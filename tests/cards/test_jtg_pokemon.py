import pytest

from ptcg.core.action import AttackAction
from ptcg.core.enums import CardType
from tests.helpers.cards import make_card
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("JTG-056")
@pytest.mark.card_coverage(
    "JTG-056",
    "get_actions",
    "reduce_action",
    "negative_case",
    "zone_change",
    "damage",
)
def test_lillies_clefairy_ex_triple_dive_energy_attaches_psychic_energy_from_hand():
    clefairy = make_card("JTG-056")
    clefairy.energy = [CardType.PSYCHIC, CardType.PSYCHIC, CardType.COLORLESS]
    psychic_1 = make_card("SVE-005")
    psychic_2 = make_card("SVE-005")
    fire_energy = make_card("SVE-002")
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            hand=[psychic_1, psychic_2, fire_energy],
            left=[make_card("SVE-004")],
            prize=[make_card("SVE-007")],
            active=[clefairy],
        ),
        PlayerZones(
            left=[make_card("SVE-008")],
            prize=[make_card("PAF-007")],
            active=[defender],
        ),
    )

    actions = clefairy.get_actions(state)
    triple_dive = [
        action
        for action in actions
        if isinstance(action, AttackAction) and action.attack.name == "Triple Dive Energy"
    ]
    assert len(triple_dive) == 1

    list(clefairy.reduce_action(triple_dive[0], state))

    assert triple_dive[0].attack.damage == 160
    assert defender.hp == 170
    assert psychic_1 in clefairy.attachment
    assert psychic_2 in clefairy.attachment
    assert fire_energy in state.player1.hand
    assert clefairy.energy == [
        CardType.PSYCHIC,
        CardType.PSYCHIC,
        CardType.COLORLESS,
        CardType.PSYCHIC,
        CardType.PSYCHIC,
    ]


def test_lillies_clefairy_ex_magical_shot_requires_four_energy():
    clefairy = make_card("JTG-056")
    clefairy.energy = [CardType.PSYCHIC, CardType.PSYCHIC, CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[clefairy]), PlayerZones(active=[defender]))

    assert [
        action.attack.name
        for action in clefairy.get_actions(state)
        if isinstance(action, AttackAction)
    ] == ["Triple Dive Energy"]
