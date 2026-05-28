from typing import cast

from ptcg.core.action import AttackAction, PlayPokemonAction, RetreatAction, choose_card_actions
from ptcg.core.attack import Attack
from ptcg.core.card import Card, EnergyCard, PokemonCard, StadiumCard
from ptcg.core.enums import (
    CardPosition,
    CardType,
    PokemonPosition,
    PokemonRule,
    PokemonType,
    Stage,
    SuperType,
)
from ptcg.core.reducer import (
    reduce_attack_action,
    reduce_choose_card_actions,
    reduce_play_pokemon_action,
    reduce_retreat_action,
)
from ptcg.utils.utils import (
    auto_end_turn,
    check_energy,
    current_bench,
    current_player,
    move_cards,
    next_turn,
    opponent_active,
    opponent_player,
)


class SIT138LugiaV(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SIT"
        self.number = "138"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Lugia V"
        self.hp = 220
        self.pokemonType = PokemonType.V
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.COLORLESS
        self.retreat = [CardType.COLORLESS, CardType.COLORLESS]
        self.weakness = [CardType.LIGHTNING]
        self.resistance = [CardType.FIGHTING]
        self.prize = 2

        self.energy = []
        self.attachment = []

        self.attacks = [
            Attack(
                {
                    "name": "Read Ahead",
                    "damage": 0,
                    "cost": [CardType.COLORLESS],
                    "text": "Draw cards until you have 6 cards in your hand. "
                    "If you drew any cards in this way, you may attach a Psychic Energy card "
                    "from your hand to 1 of your Benched Pokemon.",
                }
            ),
            Attack(
                {
                    "name": "Aero Dive",
                    "damage": 130,
                    "cost": [
                        CardType.COLORLESS,
                        CardType.COLORLESS,
                        CardType.COLORLESS,
                        CardType.COLORLESS,
                    ],
                    "text": "You may discard a Stadium in play.",
                }
            ),
        ]

        self.ability = []

    def get_actions(self, state):
        actions = []
        targets = opponent_active(state)
        player = current_player(state)

        if self.position == PokemonPosition.ACTIVE:
            for i, attack in enumerate(self.attacks):
                if check_energy(attack.cost, self.energy):
                    if i == 0 and attack.name == "Read Ahead":
                        actions.extend(
                            [AttackAction(state.turn, self, attack, target) for target in targets]
                        )
                    else:
                        if not player.firstTurn:
                            actions.extend(
                                [
                                    AttackAction(state.turn, self, attack, target)
                                    for target in targets
                                ]
                            )

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)

        elif isinstance(action, AttackAction):
            if action.attack == self.attacks[0]:
                yield from self._read_ahead_attack(action, state)
            elif action.attack == self.attacks[1]:
                yield from self._aero_dive_attack(action, state)
            else:
                raise ValueError(f"Invalid attack: {action.attack}")

        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)

        else:
            raise ValueError(f"Invalid action: {action}")

    def _read_ahead_attack(self, action, state):
        player = current_player(state)

        yield from reduce_attack_action(action, state, auto_end_turn=False)

        hand_count = len(player.hand)
        cards_to_draw = max(0, 6 - hand_count)

        drawn_cards = []
        if cards_to_draw > 0 and len(player.left) > 0:
            draw_count = min(cards_to_draw, len(player.left))
            drawn_cards = player.left[:draw_count]
            move_cards(
                drawn_cards,
                (player.id, CardPosition.LEFT),
                (player.id, CardPosition.HAND),
                state,
            )

        if drawn_cards:
            bench = current_bench(state)
            if bench:
                psychic_energy_cards: list[Card] = [
                    card
                    for card in player.hand
                    if isinstance(card, EnergyCard)
                    and card.superType == SuperType.ENERGY
                    and CardType.PSYCHIC in card.provides
                ]

                if psychic_energy_cards:
                    tips = (
                        "You used Read Ahead. You may choose a Psychic Energy card "
                        "from your hand to attach to 1 of your Benched Pokemon."
                    )
                    actions = choose_card_actions(
                        player.id, player.id, 0, 1, psychic_energy_cards, tips=tips, source=self
                    )
                    chosen_energy = yield from reduce_choose_card_actions(actions, state)

                    if chosen_energy:
                        energy_card = cast(EnergyCard, chosen_energy[0])

                        tips = "Choose 1 of your Benched Pokemon to attach the Psychic Energy to."
                        actions = choose_card_actions(
                            player.id, player.id, 1, 1, bench, tips=tips, source=self
                        )
                        target_pokemon = yield from reduce_choose_card_actions(actions, state)
                        target_pokemon = cast(PokemonCard, target_pokemon[0])

                        target_pokemon.energy.extend(energy_card.provides)
                        move_cards(
                            energy_card,
                            (player.id, CardPosition.HAND),
                            (player.id, CardPosition.BENCH_ATTACHMENT, target_pokemon.index),
                            state,
                        )

        if player.firstTurn:
            auto_end_turn(state)
        else:
            next_turn(state)

    def _aero_dive_attack(self, action, state):
        player = current_player(state)

        if state.stadium:
            tips = (
                "You used Aero Dive. You may discard the Stadium in play. "
                "Choose the Stadium to discard it, or choose nothing to skip."
            )
            stadium_list: list[Card] = list(state.stadium)
            actions = choose_card_actions(
                player.id, player.id, 0, 1, stadium_list, tips=tips, source=self
            )
            chosen_stadium = yield from reduce_choose_card_actions(actions, state)

            if chosen_stadium:
                stadium = cast(StadiumCard, chosen_stadium[0])
                if stadium.playedFrom == player.id:
                    move_cards(
                        stadium,
                        (None, CardPosition.STADIUM),
                        (player.id, CardPosition.DISCARD),
                        state,
                    )
                else:
                    opponent = opponent_player(state)
                    move_cards(
                        stadium,
                        (None, CardPosition.STADIUM),
                        (opponent.id, CardPosition.DISCARD),
                        state,
                    )

        yield from reduce_attack_action(action, state)
