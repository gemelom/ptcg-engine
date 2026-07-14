from ptcg.core.action import AttackAction, UseToolAction, choose_card_actions
from ptcg.core.attack import Attack
from ptcg.core.card import ToolCard
from ptcg.core.enums import CardPosition, CardType, PokemonPosition, SuperType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import (
    auto_end_turn,
    can_attach_tool,
    current_all_pokemon,
    current_player,
    move_cards,
    shuffle_cards,
)


class PAR178TechnicalMachineEvolution(ToolCard):
    def __init__(self):
        super().__init__()
        self.set_name = "PAR"
        self.number = "178"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Technical Machine: Evolution"
        self.cardType = CardType.NONE
        self.text = (
            "The Pokémon this card is attached to can use the attack on this card. "
            "(Dangerous Evolution: Search your deck for a card that evolves from this Pokémon "
            "and put it onto this Pokémon. This counts as evolving this Pokémon. Then, "
            "shuffle your deck.)"
        )
        self.hasAttached = False
        self.attachedTo = None

        self.attacks = [
            Attack(
                {
                    "name": "Dangerous Evolution",
                    "damage": 0,
                    "cost": [],
                    "text": "Search your deck for a card that evolves from this Pokémon "
                    "and put it onto this Pokémon. (This counts as evolving this Pokémon.) "
                    "Then, shuffle your deck.",
                }
            )
        ]

    def get_actions(self, state):
        actions = []
        player = current_player(state)

        if not self.hasAttached:
            for card in current_all_pokemon(state):
                if can_attach_tool(card):
                    actions.append(UseToolAction(state.turn, self, card))

        if self.hasAttached and self.attachedTo:
            pokemon = self.attachedTo[0]
            if pokemon.position == PokemonPosition.ACTIVE:
                # Check if there's an evolution card in the deck
                evolutions = [
                    c
                    for c in player.left
                    if c.superType == SuperType.POKEMON
                    and hasattr(c, "evolveFrom")
                    and pokemon.name in c.evolveFrom
                ]
                if evolutions:
                    actions.append(AttackAction(state.turn, pokemon, self.attacks[0], pokemon))

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseToolAction):
            player = current_player(state)
            target = action.target
            target_position = (
                CardPosition.ACTIVE_ATTACHMENT
                if target.cardPosition == CardPosition.ACTIVE
                else CardPosition.BENCH_ATTACHMENT
            )
            move_cards(
                self,
                (player.id, CardPosition.HAND),
                (player.id, target_position, target.index),
                state,
            )
            self.hasAttached = True
            self.attachedTo = [target]

        elif isinstance(action, AttackAction):
            if self.attachedTo:
                player = current_player(state)
                pokemon = self.attachedTo[0]

                evolutions = [
                    c
                    for c in player.left
                    if c.superType == SuperType.POKEMON
                    and hasattr(c, "evolveFrom")
                    and pokemon.name in c.evolveFrom
                ]

                if evolutions:
                    tips = (
                        f"You used Dangerous Evolution. Choose 1 card that evolves from "
                        f"{pokemon.name} to put onto it."
                    )
                    pick_actions = choose_card_actions(
                        player.id, player.id, 1, 1, evolutions, tips=tips, source=self
                    )
                    chosen = yield from reduce_choose_card_actions(pick_actions, state)

                    if chosen:
                        evolution_card = chosen[0]
                        self._evolve_from_deck(evolution_card, pokemon, player)
                        shuffle_cards(player.left)
                        auto_end_turn(state)

    def _evolve_from_deck(self, evolution_card, pokemon, player):
        evolution_card.energy = pokemon.energy.copy()
        evolution_card.attachment = pokemon.attachment.copy()
        evolution_card.position = pokemon.position
        evolution_card.cardPosition = pokemon.cardPosition
        evolution_card.index = pokemon.index

        pokemon.energy.clear()
        pokemon.attachment.clear()
        evolution_card.evolved.append(pokemon)

        if pokemon.position == PokemonPosition.ACTIVE:
            player.active[pokemon.index - 1] = evolution_card
        elif pokemon.position == PokemonPosition.BENCH:
            player.bench[pokemon.index - 1] = evolution_card

        player.left.remove(evolution_card)
        for idx, card in enumerate(player.left, start=1):
            card.index = idx
