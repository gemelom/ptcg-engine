# PTCG Core — Game Engine Internals

**Purpose:** Low-level game abstractions (state, actions, reducers, abilities)

## Files

| File | Purpose |
|------|---------|
| `envs.py` | `PokemonTCG` environment class with generator-based game loop |
| `state.py` | `State` container (players, turn, stadium, action buffer) |
| `player.py` | `Player` class with zones, restrictions, action tracking |
| `action.py` | 15 action types with serialization (to_nl, to_dict) |
| `reducer.py` | State transition generators (attack, retreat, evolve, etc.) |
| `card.py` | Card hierarchy (Pokemon, Energy, Trainer) with metadata |
| `attack.py` | Attack definition (name, cost, damage, text) |
| `ability.py` | Ability system (Active, Passive, Instant) with triggers |
| `enums.py` | Domain enums (CardType, ActionType, PlayerId, etc.) |
| `reward.py` | Weighted reward components and calculation |
| `effect.py` | Effect definitions (damage counters, etc.) |
| `deck.py` | Deck composition structure |
| `card_registry.py` | Card registry for loading and accessing cards |
| `ability_handler.py` | Unified passive ability triggering |
| `recorder.py` | JSONL game recording (GameRecorder) |
| `exceptions.py` | Custom exceptions (PTCGError, GameTermination, etc.) |

## State Flow

```
env.reset()
  → create Player1, Player2
  → shuffle decks, deal 7 cards, set 6 prize cards
  → start_stage: choose active Pokémon
  → determine first player (coin flip)
  → return (obs, info)

env.step(action)
  → validate action
  → reducer.send(action)
  → reduce_action(action, state)
    → card.reduce_action() or player.reduce_action()
    → may yield for sub-actions (card selection)
  → calculate reward
  → check termination
  → record state
  → return (obs, reward, done, info)
```

## Generator Pattern

Reducers use Python generators for async-like sub-actions:

```python
def reduce_attack_action(action, state):
    # Handle damage, weakness/resistance
    trigger_attack_abilities(action, state)
    # May yield for knockout handling, prize selection
    yield from _handle_knockout(target, player, opponent, state)
    # Turn management
    if auto_end_turn:
        next_turn(state)
```

### Generator Protocol

```python
# Create generator
gen = reduce_attack_action(action, state)

# Get first yield
result = gen.send(None)  # Returns (obs, reward, done, info)

# Send action to resume
result = gen.send(choose_card_action)

# Or delegate to sub-generator
yield from sub_generator()
```

## Action Types

| Action | Description | Reducer |
|--------|-------------|----------|
| `AttackAction` | Attack with active Pokémon | `reduce_attack_action` |
| `EffectAction` | Apply card effect | `reduce_effect_action` |
| `UseAbilityAction` | Activate Pokémon ability | `reduce_use_ability_action` (NYI) |
| `UseStadiumAction` | Use stadium effect | `reduce_use_stadium_action` (NYI) |
| `RetreatAction` | Swap active Pokémon | `reduce_retreat_action` |
| `PlayPokemonAction` | Put basic Pokémon to active/bench | `reduce_play_pokemon_action` |
| `EvolvePokemonAction` | Evolve Pokémon | `reduce_evolve_pokemon_action` |
| `AttachEnergyAction` | Attach energy to Pokémon | `reduce_attach_energy_action` |
| `ChooseCardAction` | Select cards from prompt | `reduce_choose_card_actions` |
| Other actions | Handled by card/player directly | N/A |

## Reducer Functions

### Attack Handling

```python
def reduce_attack_action(action, state, auto_end_turn=True):
    1. Trigger attack abilities (ATTACKING, ATTACKED)
    2. Calculate damage with weakness/resistance
    3. Apply damage or handle knockout
    4. If knockout:
       - Discard knocked out Pokémon
       - Attacker takes prize cards
       - If active was knocked out, force replacement
    5. End turn (if auto_end_turn)
```

### Retreat Handling

```python
def reduce_retreat_action(action, state):
    1. Choose replacement from bench (card selection prompt)
    2. Trigger retreat abilities (RETREAT)
    3. Discard retreat cost energy (card selection prompt)
    4. Switch active and bench positions
```

### Card Selection Pattern

```python
def reduce_choose_card_actions(actions, state):
    1. Set state.is_choosing_card = True
    2. Yield (obs, reward, done, info) with prompt
    3. Receive ChooseCardAction from player
    4. Validate action (fallback to random if invalid)
    5. Return chosen cards
```

## Ability System

### Ability Types

```python
class AbilityType(Enum):
    ACTIVE = "Active"     # Manual activation
    PASSIVE = "Passive"   # Automatic on trigger
    INSTANT = "Instant"    # One-time automatic
```

### Passive Ability Triggers

```python
class AbilityTrigger(Enum):
    ATTACKING = "ATTACKING"   # When attacking
    ATTACKED = "ATTACKED"     # When being attacked
    RETREAT = "RETREAT"       # When retreating
    # Add more triggers as needed
```

### Ability Handler

`ability_handler.py` provides unified triggering:

```python
def trigger_attack_abilities(action, state):
    # Trigger source's ATTACKING ability
    trigger_passive_ability(action.source, action, state, AbilityTrigger.ATTACKING)

    # Trigger source's attachments' ATTACKING abilities
    for card in action.source.attachment:
        trigger_passive_ability(card, action, state, AbilityTrigger.ATTACKING)

    # Trigger target's attachments' ATTACKED abilities
    if hasattr(action, "target"):
        for card in action.target.attachment:
            trigger_passive_ability(card, action, state, AbilityTrigger.ATTACKED)

    # Trigger opponent Pokemon's ATTACKED abilities
    for card in opponent_all_pokemon(state):
        trigger_passive_ability(card, action, state, AbilityTrigger.ATTACKED)

    # Trigger stadium's ATTACKING abilities
    for card in state.stadium:
        trigger_passive_ability(card, action, state, AbilityTrigger.ATTACKING)
```

## Reward Weights

```python
REWARD_WEIGHTS = {
    "energy_attached": 0.01,
    "damage_dealt": 0.0005,
    "prize_cards_taken": 0.1,
    "pokemon_evolved": 0.05,
}
# Terminal: +1 for win, -1 for loss
```

Reward calculation:

```python
class Reward:
    def calculate_step_reward(self):
        total = 0
        total += self.energy_attached_count * REWARD_WEIGHTS["energy_attached"]
        total += self.damage_dealt * REWARD_WEIGHTS["damage_dealt"]
        total += self.prize_cards_taken * REWARD_WEIGHTS["prize_cards_taken"]
        total += self.pokemon_evolved_count * REWARD_WEIGHTS["pokemon_evolved"]
        return total
```

## Termination Conditions

Game ends when:

1. **All prizes taken** — Player takes all 6 prize cards
2. **No Pokémon in play** — Player has no active or benched Pokémon
3. **Deck empty at draw** — Player cannot draw from empty deck

```python
def judge_termination(state):
    if len(state.player1.prize) == 0 or len(state.player2.prize) == 0:
        return True, determine_winner(state)

    if len(state.player1.active + state.player1.bench) == 0:
        return True, PlayerId.PLAYER2

    if len(state.player2.active + state.player2.bench) == 0:
        return True, PlayerId.PLAYER1

    return False, None
```

## State Components

### State Class

```python
@dataclass
class State:
    player1: Player
    player2: Player
    turn: Optional[PlayerId] = None
    timestep: int = 0
    is_choosing_card: bool = False
    end_turn: bool = False
    stadium: List[StadiumCard] = []
    choose_card_list: List[Card] = []
    actions_buffer: List[Action] = []

    def get_area(self, area: Tuple[PlayerId, CardPosition, Optional[int]]) -> Sequence[Card]:
        # Return cards from specified area

    def get_obs(self) -> State:
        return self

    def get_opponent_actions_buffer(self) -> List[Action]:
        # Return actions from opponent's last turn
```

### Player Class

```python
class Player:
    id: PlayerId

    # Zones
    active: List[PokemonCard]      # Active Pokémon
    bench: List[PokemonCard]       # Benched Pokémon
    hand: List[Card]              # Current hand
    deck: List[Card]              # Draw pile
    discard: List[Card]            # Discard pile
    prize: List[Card]              # Prize cards
    lostZone: List[Card]          # Lost zone

    # Restrictions
    energyPlayedTurn: bool
    supporterPlayedTurn: bool       # True on first turn
    stadiumUsedTurn: bool
    stadiumPlayedTurn: bool
    retreatTurn: bool
    firstTurn: bool
    hasPokemonDead: bool           # Knocked out during opponent's turn

    # Action tracking
    current_turn_actions: List[Dict]      # Actions in current turn
    turn_action_history: List[List[Dict]]   # All past turns

    # Methods
    def get_actions(self, state) -> List[Action]:
        # Return all legal actions for this player

    def reduce_action(self, action, state):
        # Handle retreat and pass turn (generator)
```

## Damage Calculation

```python
def _calculate_damage(source: PokemonCard, target: PokemonCard, base_damage: int) -> int:
    """Calculate damage after applying weakness and resistance."""
    if source.cardType in target.weakness:
        return base_damage * 2
    elif source.cardType in target.resistance:
        return max(0, base_damage - RESISTANCE_VALUE)  # 30
    return base_damage
```

## Constants

```python
RESISTANCE_VALUE = 30
DAMAGE_COUNTER_MULTIPLIER = 10  # 1 damage counter = 10 HP
BENCH_SIZE = 5
PRIZE_COUNT = 6
HAND_SIZE = 7
```

## Custom Exceptions

```python
class PTCGError(Exception):
    """Base exception for all PTCG errors."""

class GameError(PTCGError):
    """Game state errors."""

class GameTermination(PTCGError):
    """Normal game end (raised, not caught)."""

class ActionError(PTCGError):
    """Action-related errors."""

class InvalidCardPositionError(PTCGError):
    """Invalid card position specified."""

class InvalidAreaError(PTCGError):
    """Invalid area specified."""
```

## Game Recorder

JSONL format for game replay:

```python
class GameRecorder:
    def __init__(self, seed: int, output_dir: str = "./battle_log"):
        # Initialize recorder with seed

    def record_game_start(self, first_player: str, state: State):
        # Record game initialization

    def record_action(self, action: Action):
        # Record action execution

    def record_state(self, state: State):
        # Record state snapshot

    def record_choose_card_prompt(self, min_cnt, max_cnt, candidates, tips):
        # Record card selection prompt

    def record_termination(self, winner: Optional[PlayerId]):
        # Record game end

    def save(self) -> str:
        # Save to ./battle_log/seed_{seed}.jsonl
```

## Card Registry

```python
# Registry pattern for card loading
CARD_REGISTRY: Dict[int, Card] = {}

def get_card(card_id: int) -> Card:
    """Get card by ID."""

def get_cards_by_set(set_name: str) -> List[Card]:
    """Get all cards from a set."""
```

## Deck Loading

```python
def load_deck(deck_path: str) -> Deck:
    """
    Load deck from text file.

    Format:
        CardName SetCode Quantity
        Charmander PAF 4
        Charmeleon PAF 3
        ...
    """
```

## Key Design Patterns

1. **Generator-Based State Machine**: Multi-step actions use generators for async-like control flow
2. **Action-Reducer Pattern**: Actions describe what happened, reducers describe how state changes
3. **Card-Source Pattern**: Actions have a `source` (card or player) that handles reduction
4. **Passive Ability System**: Centralized ability triggering eliminates code duplication
5. **Immutable State**: State is updated in-place but conceptually treated as immutable snapshots
6. **Action Buffer**: Tracks all actions for game replay and analysis
