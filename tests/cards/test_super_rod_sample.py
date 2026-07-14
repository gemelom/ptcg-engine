import pytest

from ptcg.core.action import UseItemAction
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("PAL-188")
@pytest.mark.card_coverage("PAL-188", "get_actions", "reduce_action", "choice_flow", "zone_change")
def test_super_rod_shuffles_selected_pokemon_and_basic_energy_from_discard_into_deck():
    super_rod = make_card("PAL-188")
    charmander = make_card("PAF-007")
    fire_energy = make_card("SVE-002")
    ultra_ball = make_card("PAF-091")
    state = make_state(
        PlayerZones(
            hand=[super_rod],
            discard=[charmander, fire_energy, ultra_ball],
        )
    )

    actions = super_rod.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseItemAction)

    prompts = drive_choices(
        super_rod.reduce_action(actions[0], state),
        [lambda _info: [charmander, fire_energy]],
    )

    assert prompts[0]["prompt"].source is super_rod
    assert sorted(card.name for card in prompts[0]["prompt"].candidates) == [
        "Charmander",
        "Fire Energy",
    ]
    assert super_rod in state.player1.discard
    assert ultra_ball in state.player1.discard
    assert charmander not in state.player1.discard
    assert fire_energy not in state.player1.discard
    assert sorted(card.name for card in state.player1.left) == ["Charmander", "Fire Energy"]
