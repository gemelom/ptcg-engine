import pytest

from ptcg.core.action import AttackAction, UseAbilityAction
from ptcg.core.enums import CardPosition, CardType, SpecialCondition
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("SVI-165")
@pytest.mark.card_coverage(
    "SVI-165",
    "get_actions",
    "reduce_action",
    "negative_case",
    "damage",
)
def test_flamigo_nosedive_damages_opponent_and_itself():
    flamigo = make_card("SVI-165")
    flamigo.energy = [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[flamigo],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )

    attacks = [
        action
        for action in flamigo.get_actions(state)
        if isinstance(action, AttackAction) and action.attack.name == "Nosedive"
    ]
    assert len(attacks) == 1

    list(flamigo.reduce_action(attacks[0], state))

    assert defender.hp == 220  # 330 - 110
    assert flamigo.hp == 90  # 110 - 20 recoil
    assert state.turn == state.player2.id


def test_flamigo_flap_damages_without_recoil():
    flamigo = make_card("SVI-165")
    flamigo.energy = [CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(left=[make_card("SVE-002")], active=[flamigo]),
        PlayerZones(left=[make_card("SVE-005")], active=[defender]),
    )

    attacks = [action for action in flamigo.get_actions(state) if isinstance(action, AttackAction)]

    assert [action.attack.name for action in attacks] == ["Flap"]
    list(flamigo.reduce_action(attacks[0], state))
    assert defender.hp == 300
    assert flamigo.hp == 110


def test_flamigo_recoil_knockout_awards_opponent_and_replaces_active():
    flamigo = make_card("SVI-165")
    flamigo.hp = 20
    flamigo.energy = [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS]
    replacement = make_card("PAF-007")
    defender = make_card("PAF-054")
    first_prize = make_card("SVE-005")
    second_prize = make_card("SVE-007")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[flamigo],
            bench=[replacement],
        ),
        PlayerZones(
            left=[make_card("SVE-008")],
            prize=[first_prize, second_prize],
            active=[defender],
        ),
    )
    action = next(
        action
        for action in flamigo.get_actions(state)
        if isinstance(action, AttackAction) and action.attack.name == "Nosedive"
    )

    drive_choices(
        flamigo.reduce_action(action, state),
        [lambda _info: [first_prize], lambda _info: [replacement]],
    )

    assert [card.id for card in state.player1.discard] == ["SVI-165"]
    assert state.player1.active == [replacement]
    assert first_prize in state.player2.hand
    assert state.turn == state.player2.id


def test_flamigo_cannot_attack_without_energy_or_from_bench():
    flamigo = make_card("SVI-165")
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[flamigo]), PlayerZones(active=[defender]))

    assert [
        action for action in flamigo.get_actions(state) if isinstance(action, AttackAction)
    ] == []

    flamigo.energy = [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS]
    state = make_state(
        PlayerZones(active=[make_card("PAF-007")], bench=[flamigo]),
        PlayerZones(active=[defender]),
    )

    assert [
        action for action in flamigo.get_actions(state) if isinstance(action, AttackAction)
    ] == []


@pytest.mark.card("SVI-086")
@pytest.mark.card_coverage(
    "SVI-086",
    "get_actions",
    "reduce_action",
    "negative_case",
    "damage",
)
def test_gardevoir_ex_miracle_force_damages_opponent():
    gardevoir = make_card("SVI-086")
    gardevoir.energy = [CardType.PSYCHIC, CardType.PSYCHIC, CardType.COLORLESS]
    gardevoir.specialCondition = SpecialCondition.ASLEEP
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[gardevoir],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )

    attacks = [a for a in gardevoir.get_actions(state) if isinstance(a, AttackAction)]
    assert len(attacks) == 1
    assert attacks[0].attack.name == "Miracle Force"

    list(gardevoir.reduce_action(attacks[0], state))

    assert defender.hp == 140  # 330 - 190
    assert gardevoir.specialCondition == SpecialCondition.NONE
    assert state.turn == state.player2.id


def test_gardevoir_ex_miracle_force_unavailable_without_energy():
    gardevoir = make_card("SVI-086")
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[gardevoir]), PlayerZones(active=[defender]))

    assert [a for a in gardevoir.get_actions(state) if isinstance(a, AttackAction)] == []


def test_gardevoir_ex_miracle_force_unavailable_when_on_bench():
    gardevoir = make_card("SVI-086")
    gardevoir.energy = [CardType.PSYCHIC, CardType.PSYCHIC, CardType.COLORLESS]
    active = make_card("PAF-007")
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(active=[active], bench=[gardevoir]),
        PlayerZones(active=[defender]),
    )

    assert [a for a in gardevoir.get_actions(state) if isinstance(a, AttackAction)] == []


def test_gardevoir_ex_psychic_embrace_is_repeatable_and_uses_choices():
    gardevoir = make_card("SVI-086")
    kirlia = make_card("SIT-068")
    first_energy = make_card("SVE-005")
    second_energy = make_card("SVE-005")
    state = make_state(
        PlayerZones(
            discard=[first_energy, second_energy],
            active=[gardevoir],
            bench=[kirlia],
        )
    )

    first_action = next(
        action for action in gardevoir.get_actions(state) if isinstance(action, UseAbilityAction)
    )
    drive_choices(
        gardevoir.reduce_action(first_action, state),
        [lambda _info: [second_energy], lambda _info: [kirlia]],
    )

    assert second_energy in kirlia.attachment
    assert kirlia.energy == [CardType.PSYCHIC]
    assert kirlia.hp == 60
    assert second_energy.cardPosition == CardPosition.BENCH_ATTACHMENT
    assert state.player1.energyPlayedTurn is False

    second_action = next(
        action for action in gardevoir.get_actions(state) if isinstance(action, UseAbilityAction)
    )
    drive_choices(
        gardevoir.reduce_action(second_action, state),
        [lambda _info: [first_energy], lambda _info: [gardevoir]],
    )

    assert first_energy in gardevoir.attachment
    assert gardevoir.energy == [CardType.PSYCHIC]
    assert gardevoir.hp == 290
    assert state.player1.discard == []


def test_gardevoir_ex_psychic_embrace_requires_basic_psychic_energy_and_safe_target():
    gardevoir = make_card("SVI-086")
    gardevoir.hp = 30
    non_psychic = make_card("PAF-007")
    psychic_energy = make_card("SVE-005")
    mist_energy = make_card("TEF-161")
    state = make_state(
        PlayerZones(
            discard=[mist_energy],
            active=[gardevoir],
            bench=[non_psychic],
        )
    )

    assert [
        action for action in gardevoir.get_actions(state) if isinstance(action, UseAbilityAction)
    ] == []

    state.player1.discard.append(psychic_energy)
    gardevoir.hp = 20

    assert [
        action for action in gardevoir.get_actions(state) if isinstance(action, UseAbilityAction)
    ] == []


@pytest.mark.card("SVI-253")
@pytest.mark.card_coverage(
    "SVI-253",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "damage",
    "ability",
)
def test_miraidon_ex_tandem_unit_puts_lightning_pokemon_on_bench():
    miraidon = make_card("SVI-253")
    lightning1 = make_card("SVI-253")  # another Miraidon ex - Basic Lightning
    lightning2 = make_card("BRS-048")  # Raikou V - Basic Lightning
    non_lightning = make_card("PAF-007")
    state = make_state(
        PlayerZones(
            left=[lightning1, lightning2, non_lightning],
            active=[miraidon],
        )
    )
    state.player1.onceUsedTurn["Tandem Unit"] = False

    ability_actions = [a for a in miraidon.get_actions(state) if isinstance(a, UseAbilityAction)]
    assert len(ability_actions) == 1

    prompts = drive_choices(
        miraidon.reduce_action(ability_actions[0], state),
        [lambda _info: [lightning1, lightning2]],
    )

    assert prompts[0]["prompt"].source is miraidon
    assert set(prompts[0]["prompt"].candidates) == {lightning1, lightning2}
    assert len(state.player1.bench) == 2
    assert miraidon.abilityUsed is True
    assert state.player1.onceUsedTurn["Tandem Unit"] is True


def test_miraidon_ex_tandem_unit_unavailable_after_use():
    miraidon = make_card("SVI-253")
    state = make_state(PlayerZones(left=[make_card("BRS-048")], active=[miraidon]))
    state.player1.onceUsedTurn["Tandem Unit"] = True

    assert [a for a in miraidon.get_actions(state) if isinstance(a, UseAbilityAction)] == []


def test_miraidon_ex_photon_blaster_damages_opponent():
    miraidon = make_card("SVI-253")
    miraidon.energy = [CardType.LIGHTNING, CardType.LIGHTNING, CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[miraidon],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )
    state.player1.onceUsedTurn["Tandem Unit"] = False

    attacks = [a for a in miraidon.get_actions(state) if isinstance(a, AttackAction)]
    assert len(attacks) == 1

    list(miraidon.reduce_action(attacks[0], state))

    assert defender.hp == 110  # 330 - 220
    assert state.turn == state.player2.id


def test_miraidon_ex_photon_blaster_unavailable_after_use():
    miraidon = make_card("SVI-253")
    miraidon.energy = [CardType.LIGHTNING, CardType.LIGHTNING, CardType.COLORLESS]
    miraidon.useAttackLastTurn = True
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[miraidon]), PlayerZones(active=[defender]))
    state.player1.onceUsedTurn["Tandem Unit"] = False

    assert [a for a in miraidon.get_actions(state) if isinstance(a, AttackAction)] == []
