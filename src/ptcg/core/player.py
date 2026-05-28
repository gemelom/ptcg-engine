import copy
import random

from ptcg.core.action import (
    AttackAction,
    EvolvePokemonAction,
    PassTurn,
    PlayPokemonAction,
    RetreatAction,
    UseAbilityAction,
)
from ptcg.core.card import ToolCard
from ptcg.core.enums import *
from ptcg.core.reducer import reduce_retreat_action
from ptcg.core.reward import Reward
from ptcg.utils.utils import *


class Player:
    id: PlayerId

    def __init__(self, deck):
        self.set_deck(deck)
        self.discard = []
        self.hand = []
        self.prize = []
        self.discard = []
        self.left = []

        self.active = []
        self.bench = []

        self.benchSize = 5

        self.lostZone = []

        self.energyPlayedTurn = False
        self.supporterPlayedTurn = True  # can't play supporter at first turn
        self.stadiumUsedTurn = False
        self.stadiumPlayedTurn = False
        self.retreatTurn = False

        self.onceUsedTurn = self.get_once_used_turn()
        self.onceUsedGame = self.get_once_used_game()

        self.firstTurn = True

        self.hasPokemonDead = False  # knocked down during opponent's last turn

        self.reward = Reward()

        # Action trajectory tracking for each turn
        self.current_turn_actions = []  # Store actions executed in current turn
        self.turn_action_history = []  # Store action trajectories for all turns

    def reset_turn_stats(self):
        """
        Reset current turn statistics for next turn
        """
        self.energyPlayedTurn = False
        self.supporterPlayedTurn = False
        self.stadiumUsedTurn = False
        self.stadiumPlayedTurn = False
        self.retreatTurn = False

        # Archive current turn actions and reset for next turn
        if self.current_turn_actions:
            self.turn_action_history.append(copy.deepcopy(self.current_turn_actions))
        self.current_turn_actions = []

    def record_action(self, action):
        """
        Record an action executed by this player in the current turn

        Args:
            action: The action object to record
        """
        # Create a record of the action with relevant information
        action_record = {
            "action_type": type(action).__name__,
            "action_nl": action.to_nl() if hasattr(action, "to_nl") else str(action),
            "player_id": action.playerId,
            "source": action.source.name if hasattr(action.source, "name") else str(action.source),
            "timestamp": len(self.current_turn_actions) + 1,  # Order in current turn
        }

        # Add specific information based on action type
        if hasattr(action, "target") and hasattr(action.target, "name"):
            action_record["target"] = action.target.name

        if isinstance(action, AttackAction):
            action_record["attack_name"] = action.attack.name
            action_record["damage"] = action.attack.damage
        elif isinstance(action, PlayPokemonAction):
            action_record["position"] = (
                action.position.name if hasattr(action.position, "name") else str(action.position)
            )
        elif isinstance(action, EvolvePokemonAction) and hasattr(action, "target"):
            action_record["evolved_from"] = action.target.name

        self.current_turn_actions.append(action_record)

    def get_current_turn_actions(self):
        """
        Get all actions executed in the current turn

        Returns:
            List of action records for current turn
        """
        return copy.deepcopy(self.current_turn_actions)

    def get_turn_action_history(self):
        """
        Get action trajectories for all completed turns

        Returns:
            List of lists, where each inner list contains action records for one turn
        """
        return copy.deepcopy(self.turn_action_history)

    def get_full_action_trajectory(self):
        """
        Get complete action trajectory including current turn

        Returns:
            Dictionary with 'completed_turns' and 'current_turn' action records
        """
        return {
            "completed_turns": self.get_turn_action_history(),
            "current_turn": self.get_current_turn_actions(),
            "total_turns": len(self.turn_action_history) + (1 if self.current_turn_actions else 0),
        }

    def shuffle(self):
        """
        shuffle when game start until hand is valid
        """
        random.shuffle(self.deck)
        self.hand = self.deck[:7]
        self.prize = self.deck[7:13]
        self.left = self.deck[13:]

        def can_play(card):
            return card.superType == SuperType.POKEMON and card.stage == Stage.BASIC

        if all(not can_play(card) for card in self.hand):
            self.shuffle()

        def set_cards_position(cards, position):
            for idx, card in enumerate(cards):
                card.cardPosition = position
                card.index = idx + 1

        set_cards_position(self.hand, CardPosition.HAND)
        set_cards_position(self.prize, CardPosition.PRIZE)
        set_cards_position(self.left, CardPosition.LEFT)

    def set_deck(self, deck):
        self.deck_composition = deck
        self.deck = copy.deepcopy(deck.cards)

    def get_actions(self, state):
        actions = []

        # use stadium
        for card in state.stadium:
            if not self.stadiumUsedTurn:
                actions.extend(card.get_actions(state))

        # use hand (Trainer & Energy)
        for card in self.hand:
            if (
                card.superType == SuperType.ENERGY
                and not self.energyPlayedTurn
                or card.superType == SuperType.TRAINER
                and card.trainerType != TrainerType.SUPPORTER
                or card.superType == SuperType.TRAINER
                and card.trainerType == TrainerType.SUPPORTER
                and not self.supporterPlayedTurn
            ):
                actions.extend(card.get_actions(state))

        # use hand (Pokemon)
        for card in self.hand:
            if card.superType == SuperType.POKEMON and card.stage == Stage.BASIC:
                if len(self.active) == 0:
                    actions.append(PlayPokemonAction(self.id, card, PokemonPosition.ACTIVE))
                if len(self.bench) < self.benchSize:
                    actions.append(PlayPokemonAction(self.id, card, PokemonPosition.BENCH))

            # evolve
            elif card.superType == SuperType.POKEMON and card.stage != Stage.BASIC:
                # can't evolve in first turn
                if self.firstTurn:
                    continue
                targets = check_evolve(card, state)
                if len(targets) != 0:
                    actions.extend(
                        [EvolvePokemonAction(self.id, card, target) for target in targets]
                    )

        # Check if active Pokémon's abilities are suppressed (e.g., by Flutter Mane's Midnight Fluttering)
        active_suppressed = is_active_ability_suppressed(self, state)

        # pokemon ability & skill
        for card in self.active + self.bench:
            card_actions = card.get_actions(state)
            # Filter out UseAbilityAction for active Pokémon if suppressed by opponent
            if card in self.active and active_suppressed:
                card_actions = [a for a in card_actions if not isinstance(a, UseAbilityAction)]
            if self.firstTurn:
                # Allow specific attacks on first turn for certain cards
                filtered_actions = []
                for action in card_actions:
                    if isinstance(action, AttackAction):
                        # Allow Fast Charge attack from Raichu V on first turn
                        if (
                            hasattr(card, "name")
                            and card.name == "Raichu V"
                            and hasattr(action.attack, "name")
                            and action.attack.name == "Fast Charge"
                        ):
                            filtered_actions.append(action)
                        # Add other exceptions here if needed
                    else:
                        filtered_actions.append(action)
                card_actions = filtered_actions
            actions.extend(card_actions)

        # item ability
        for card in self.active + self.bench:
            for item in card.attachment:
                if isinstance(item, ToolCard):
                    item_actions = item.get_actions(state)
                    actions.extend(item_actions)

        # retreat
        if not self.retreatTurn:
            for card in self.active:
                if check_energy(card.retreat, card.energy) and len(self.bench) != 0:
                    actions.append(RetreatAction(self.id, self, card))

        # end turn
        actions.append(PassTurn(self.id, self))

        return actions

    def reduce_action(self, action, state):
        # Record the action first
        if action.playerId == self.id:
            self.record_action(action)

        # retreat
        if isinstance(action, RetreatAction):
            self.retreatTurn = True
            yield from reduce_retreat_action(action, state)

        # pass turn
        elif isinstance(action, PassTurn):
            next_turn(state)

    def get_once_used_turn(self):
        onceUsedTurn = {}

        # pokemon abilities
        for card in self.deck:
            if (
                card.superType == SuperType.POKEMON
                and hasattr(card, "ability")
                and len(card.ability) != 0
                and card.ability[0].onceUsedPerTurn
            ):
                onceUsedTurn.setdefault(card.ability[0].name, False)

        return onceUsedTurn

    def get_once_used_game(self):
        onceUsedGame = {}

        # VSTAR, GX, EX
        for card in self.deck:
            if hasattr(card, "cardTag"):
                onceUsedGame.setdefault(card.cardTag, False)

        return onceUsedGame

    def get_obs(self):
        pass

    def to_dict(self):
        dict = {}
        dict["active"] = []
        dict["bench"] = []
        dict["hand"] = []
        dict["stadium"] = []
        dict["deck"] = []
        dict["discard"] = []
        dict["prize"] = []
        dict["lostZone"] = []
        dict["onceUsed"] = {
            "supporter": str(self.supporterPlayedTurn),
            "energy": str(self.energyPlayedTurn),
            "stadiumPlayed": str(self.stadiumPlayedTurn),
            "stadiumUsed": str(self.stadiumUsedTurn),
            "retreat": str(self.retreatTurn),
        }
        dict["vstar"] = str(self.onceUsedGame.get("VSTAR", False))

        for card in self.active:
            dict["active"].append(card.to_dict())
        for card in self.bench:
            dict["bench"].append(card.to_dict())
        for card in self.hand:
            dict["hand"].append(card.to_dict())
        for card in self.left:
            dict["deck"].append(card.to_dict())
        for card in self.discard:
            dict["discard"].append(card.to_dict())
        for card in self.prize:
            dict["prize"].append(card.to_dict())
        for card in self.lostZone:
            dict["lostZone"].append(card.to_dict())

        return dict
