from ptcg.core.action import UseToolAction, choose_card_actions
from ptcg.core.card import ToolCard
from ptcg.core.enums import CardPosition, CardType, EnergyType, SuperType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import can_attach_tool, current_all_pokemon, current_player, move_cards


class TEF151HeavyBaton(ToolCard):
    def __init__(self):
        super().__init__()
        self.set_name = "TEF"
        self.number = "151"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Heavy Baton"
        self.cardType = CardType.NONE
        self.text = (
            "If the Pokémon this card is attached to has a Retreat Cost of exactly 4, "
            "is in the Active Spot, and is Knocked Out by damage from an attack from your "
            "opponent's Pokémon, move up to 3 Basic Energy cards from that Pokémon to your "
            "Benched Pokémon in any way you like."
        )
        self.hasAttached = False
        self.attachedTo = None

    def get_actions(self, state):
        if self.hasAttached:
            return []
        return [
            UseToolAction(state.turn, self, card)
            for card in current_all_pokemon(state)
            if can_attach_tool(card)
        ]

    def on_knocked_out(self, target, is_active_dead, attacker, opponent, state):
        """Called from _handle_knockout before discard if conditions are met."""
        if not is_active_dead or len(target.retreat) != 4:
            return
        if not opponent.bench:
            return

        basic_energy = [
            card
            for card in target.attachment
            if card.superType == SuperType.ENERGY
            and hasattr(card, "energyType")
            and card.energyType == EnergyType.BASIC
        ]
        if not basic_energy:
            return

        max_count = min(3, len(basic_energy))
        tips = (
            f"Heavy Baton: Choose up to {max_count} Basic Energy card(s) from "
            f"{target.name} to move to your Benched Pokémon."
        )
        actions = choose_card_actions(
            opponent.id, opponent.id, 0, max_count, basic_energy, tips=tips, source=self
        )
        chosen_energy = yield from reduce_choose_card_actions(actions, state)

        for energy_card in chosen_energy:
            if energy_card not in target.attachment:
                continue

            tips = f"Choose a Benched Pokémon to move {energy_card.name} to."
            bench_actions = choose_card_actions(
                opponent.id, opponent.id, 1, 1, opponent.bench, tips=tips, source=self
            )
            bench_target_list = yield from reduce_choose_card_actions(bench_actions, state)
            if not bench_target_list:
                continue
            bench_pokemon = bench_target_list[0]

            # Move energy from KO'd pokemon to bench pokemon
            target.attachment.remove(energy_card)
            for energy_type in energy_card.provides:
                if energy_type in target.energy:
                    target.energy.remove(energy_type)

            bench_pokemon.attachment.append(energy_card)
            bench_pokemon.energy.extend(energy_card.provides)
            energy_card.cardPosition = CardPosition.BENCH_ATTACHMENT

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
