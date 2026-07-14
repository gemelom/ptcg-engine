import pytest

from ptcg.core.action import UseItemAction
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("SVI-170")
@pytest.mark.card_coverage(
    "SVI-170",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_electric_generator_attaches_lightning_energy_to_benched_lightning_pokemon():
    card = make_card("SVI-170")
    lightning_energy = make_card("SVE-004")   # Lightning Energy
    other_card = make_card("PAF-007")
    miraidon = make_card("SVI-253")           # Lightning type benched Pokemon
    state = make_state(
        PlayerZones(
            hand=[card],
            left=[lightning_energy, other_card],
            active=[make_card("PAF-007")],
            bench=[miraidon],
        )
    )

    actions = card.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseItemAction)

    drive_choices(
        card.reduce_action(actions[0], state),
        [lambda _info: [lightning_energy], lambda _info: [miraidon]],
    )

    assert lightning_energy in miraidon.attachment
    assert card in state.player1.discard


def test_electric_generator_unavailable_without_lightning_bench_pokemon():
    card = make_card("SVI-170")
    state = make_state(
        PlayerZones(
            hand=[card],
            left=[make_card("SVE-004")],
            active=[make_card("PAF-007")],
        )
    )

    assert card.get_actions(state) == []


def test_electric_generator_unavailable_with_empty_deck():
    card = make_card("SVI-170")
    miraidon = make_card("SVI-253")
    state = make_state(PlayerZones(hand=[card], bench=[miraidon]))

    assert card.get_actions(state) == []
