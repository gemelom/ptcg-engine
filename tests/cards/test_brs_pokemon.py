import pytest

from ptcg.core.action import AttackAction, PlayPokemonAction, UseAbilityAction
from ptcg.core.enums import CardType, PlayerId, PokemonPosition
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("BRS-048")
@pytest.mark.card_coverage(
    "BRS-048",
    "get_actions",
    "reduce_action",
    "negative_case",
    "zone_change",
    "damage",
    "ability",
)
def test_raikou_v_fleet_footed_draws_one_card_from_active_spot():
    raikou = make_card("BRS-048")
    drawn_card = make_card("SVE-004")
    state = make_state(PlayerZones(left=[drawn_card], active=[raikou]))
    state.player1.onceUsedTurn["Fleet-Footed"] = False

    actions = raikou.get_actions(state)
    ability_actions = [action for action in actions if isinstance(action, UseAbilityAction)]
    assert len(ability_actions) == 1

    list(raikou.reduce_action(ability_actions[0], state))

    assert state.player1.hand == [drawn_card]
    assert state.player1.left == []
    assert raikou.abilityUsed is True
    assert state.player1.onceUsedTurn["Fleet-Footed"] is True


def test_raikou_v_fleet_footed_unavailable_from_bench():
    raikou = make_card("BRS-048")
    state = make_state(PlayerZones(bench=[raikou]))
    state.player1.onceUsedTurn["Fleet-Footed"] = False

    assert [action for action in raikou.get_actions(state) if isinstance(action, UseAbilityAction)] == []


def test_raikou_v_lightning_rondo_adds_damage_for_each_benched_pokemon():
    raikou = make_card("BRS-048")
    raikou.energy = [CardType.LIGHTNING, CardType.COLORLESS]
    defender = make_card("BRS-048")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[raikou],
            bench=[make_card("PAF-007"), make_card("PAF-008")],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
            bench=[make_card("PAF-027")],
        ),
    )
    state.player1.onceUsedTurn["Fleet-Footed"] = False

    actions = raikou.get_actions(state)
    attack_actions = [action for action in actions if isinstance(action, AttackAction)]
    assert len(attack_actions) == 1

    list(raikou.reduce_action(attack_actions[0], state))

    assert attack_actions[0].attack.damage == 80
    assert defender.hp == 120
    assert state.turn == state.player2.id


@pytest.mark.card("BRS-121")
@pytest.mark.card_coverage(
    "BRS-121",
    "get_actions",
    "reduce_action",
    "negative_case",
    "zone_change",
    "ability",
)
def test_bibarel_industrious_incisors_draws_until_hand_has_five_cards():
    bibarel = make_card("BRS-121")
    hand_card = make_card("SVE-002")
    drawn_cards = [
        make_card("SVE-004"),
        make_card("SVE-005"),
        make_card("SVE-007"),
        make_card("SVE-008"),
    ]
    state = make_state(PlayerZones(hand=[hand_card], left=drawn_cards, active=[bibarel]))
    state.player1.onceUsedTurn["Industrious Incisors"] = False

    actions = bibarel.get_actions(state)
    ability_actions = [action for action in actions if isinstance(action, UseAbilityAction)]
    assert len(ability_actions) == 1

    list(bibarel.reduce_action(ability_actions[0], state))

    assert state.player1.hand == [hand_card] + drawn_cards
    assert state.player1.left == []
    assert state.player1.onceUsedTurn["Industrious Incisors"] is True


def test_bibarel_industrious_incisors_does_not_draw_with_five_cards_in_hand():
    bibarel = make_card("BRS-121")
    hand = [make_card("SVE-002") for _ in range(5)]
    deck_card = make_card("SVE-004")
    state = make_state(PlayerZones(hand=hand, left=[deck_card], active=[bibarel]))
    state.player1.onceUsedTurn["Industrious Incisors"] = False

    list(bibarel.reduce_action(bibarel.get_actions(state)[0], state))

    assert state.player1.hand == hand
    assert state.player1.left == [deck_card]
    assert state.player1.onceUsedTurn["Industrious Incisors"] is True


def test_bibarel_industrious_incisors_unavailable_after_use():
    bibarel = make_card("BRS-121")
    state = make_state(PlayerZones(active=[bibarel]))
    state.player1.onceUsedTurn["Industrious Incisors"] = True

    assert [action for action in bibarel.get_actions(state) if isinstance(action, UseAbilityAction)] == []


@pytest.mark.card("BRS-041")
@pytest.mark.card_coverage(
    "BRS-041",
    "get_actions",
    "reduce_action",
    "negative_case",
    "damage",
    "ability",
)
def test_manaphy_rain_splash_damages_opponents_active_pokemon():
    manaphy = make_card("BRS-041")
    manaphy.energy = [CardType.WATER]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[manaphy],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )

    actions = manaphy.get_actions(state)
    attack_actions = [action for action in actions if isinstance(action, AttackAction)]
    assert len(attack_actions) == 1

    list(manaphy.reduce_action(attack_actions[0], state))

    assert defender.hp == 310


def test_manaphy_rain_splash_unavailable_without_water_energy():
    manaphy = make_card("BRS-041")
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[manaphy]), PlayerZones(active=[defender]))

    assert [action for action in manaphy.get_actions(state) if isinstance(action, AttackAction)] == []


def test_manaphy_wave_veil_zeroes_attack_damage_to_own_benched_pokemon():
    manaphy = make_card("BRS-041")
    attacker = make_card("ASR-046")
    benched_target = make_card("PAF-007")
    state = make_state(
        PlayerZones(bench=[manaphy, benched_target]),
        PlayerZones(active=[attacker]),
        turn=PlayerId.PLAYER2,
    )
    action = AttackAction(state.player2.id, attacker, attacker.attacks[0], benched_target)
    action.attack.damage = 90

    manaphy.use_ability(action, state)

    assert action.attack.damage == 0


@pytest.mark.card("BRS-124")
@pytest.mark.card_coverage(
    "BRS-124",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_minccino_call_for_family_puts_two_basic_pokemon_from_deck_onto_bench(monkeypatch):
    monkeypatch.setattr("ptcg.utils.utils.random.shuffle", lambda _cards: None)
    minccino = make_card("BRS-124")
    minccino.energy = [CardType.COLORLESS]
    charmander = make_card("PAF-007")
    raikou = make_card("BRS-048")
    bibarel = make_card("BRS-121")
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[charmander, raikou, bibarel],
            prize=[make_card("SVE-002")],
            active=[minccino],
        ),
        PlayerZones(
            left=[make_card("SVE-004")],
            prize=[make_card("SVE-005")],
            active=[defender],
        ),
    )

    actions = minccino.get_actions(state)
    call_for_family = [
        action
        for action in actions
        if isinstance(action, AttackAction) and action.attack.name == "Call for Family"
    ]
    assert len(call_for_family) == 1

    prompts = drive_choices(
        minccino.reduce_action(call_for_family[0], state),
        [lambda _info: [charmander, raikou]],
    )

    assert prompts[0]["prompt"].source is minccino
    assert [card.name for card in prompts[0]["prompt"].candidates] == [
        "Charmander",
        "Raikou V",
    ]
    assert state.player1.bench == [charmander, raikou]
    assert charmander not in state.player1.left
    assert raikou not in state.player1.left
    assert bibarel in state.player1.left
    assert state.turn == state.player2.id


def test_minccino_attacks_are_unavailable_without_energy():
    minccino = make_card("BRS-124")
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[minccino]), PlayerZones(active=[defender]))

    assert [action for action in minccino.get_actions(state) if isinstance(action, AttackAction)] == []


@pytest.mark.card("BRS-158")
@pytest.mark.card_coverage(
    "BRS-158",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
    "damage",
)
def test_raichu_v_fast_charge_attaches_lightning_energy_from_deck(monkeypatch):
    monkeypatch.setattr("ptcg.utils.utils.random.shuffle", lambda _cards: None)
    raichu = make_card("BRS-158")
    raichu.energy = [CardType.LIGHTNING]
    lightning_energy = make_card("SVE-004")
    fire_energy = make_card("SVE-002")
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[lightning_energy, fire_energy],
            prize=[make_card("SVE-005")],
            active=[raichu],
        ),
        PlayerZones(
            left=[make_card("SVE-007")],
            prize=[make_card("SVE-008")],
            active=[defender],
        ),
    )

    actions = raichu.get_actions(state)
    fast_charge = [
        action
        for action in actions
        if isinstance(action, AttackAction) and action.attack.name == "Fast Charge"
    ]
    assert len(fast_charge) == 1

    prompts = drive_choices(
        raichu.reduce_action(fast_charge[0], state),
        [lambda _info: [lightning_energy]],
    )

    assert prompts[0]["prompt"].source is raichu
    assert [card.name for card in prompts[0]["prompt"].candidates] == ["Lightning Energy"]
    assert lightning_energy in raichu.attachment
    assert raichu.energy == [CardType.LIGHTNING, CardType.LIGHTNING]
    assert lightning_energy not in state.player1.left
    assert fire_energy in state.player1.left
    assert raichu.fastChargeUsed is False
    assert state.turn == state.player2.id


def test_raichu_v_dynamic_spark_discards_lightning_energy_for_damage():
    raichu = make_card("BRS-158")
    active_energy = make_card("SVE-004")
    remaining_active_energy = make_card("SVE-004")
    bench_energy = make_card("SVE-004")
    raichu.attachment = [active_energy, remaining_active_energy]
    raichu.energy = [CardType.LIGHTNING, CardType.LIGHTNING]
    benched = make_card("PAF-007")
    benched.attachment = [bench_energy]
    benched.energy = [CardType.LIGHTNING]
    defender = make_card("BRS-048")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-005")],
            active=[raichu],
            bench=[benched],
        ),
        PlayerZones(
            left=[make_card("SVE-007")],
            prize=[make_card("SVE-008")],
            active=[defender],
        ),
    )
    state.player1.firstTurn = False

    actions = raichu.get_actions(state)
    dynamic_spark = [
        action
        for action in actions
        if isinstance(action, AttackAction) and action.attack.name == "Dynamic Spark"
    ]
    assert len(dynamic_spark) == 1

    drive_choices(
        raichu.reduce_action(dynamic_spark[0], state),
        [lambda _info: [active_energy, bench_energy]],
    )

    assert dynamic_spark[0].attack.damage == 120
    assert defender.hp == 80
    assert active_energy in state.player1.discard
    assert bench_energy in state.player1.discard
    assert active_energy not in raichu.attachment
    assert remaining_active_energy in raichu.attachment
    assert bench_energy not in benched.attachment
    assert raichu.energy == [CardType.LIGHTNING]
    assert benched.energy == []


def test_raichu_v_dynamic_spark_unavailable_on_first_turn():
    raichu = make_card("BRS-158")
    raichu.energy = [CardType.LIGHTNING, CardType.LIGHTNING]
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[raichu]), PlayerZones(active=[defender]))

    assert [
        action.attack.name
        for action in raichu.get_actions(state)
        if isinstance(action, AttackAction)
    ] == ["Fast Charge"]


@pytest.mark.card("BRS-040")
@pytest.mark.card_coverage(
    "BRS-040",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
    "ability",
)
def test_lumineon_v_luminous_sign_searches_supporter_when_played_to_bench(monkeypatch):
    monkeypatch.setattr("ptcg.utils.utils.random.shuffle", lambda _cards: None)
    lumineon = make_card("BRS-040")
    supporter = make_card("PAF-087")
    item = make_card("PAF-084")
    state = make_state(PlayerZones(hand=[lumineon], left=[supporter, item]))
    action = PlayPokemonAction(state.player1.id, lumineon, PokemonPosition.BENCH)

    prompts = drive_choices(
        lumineon.reduce_action(action, state),
        [lambda _info: [supporter]],
    )

    assert prompts[0]["prompt"].source is lumineon
    assert [card.name for card in prompts[0]["prompt"].candidates] == ["Professor's Research"]
    assert lumineon in state.player1.bench
    assert lumineon not in state.player1.hand
    assert supporter in state.player1.hand
    assert item in state.player1.left


def test_lumineon_v_aqua_return_action_requires_energy_and_benched_pokemon():
    lumineon = make_card("BRS-040")
    lumineon.energy = [CardType.WATER, CardType.COLORLESS, CardType.COLORLESS]
    defender = make_card("PAF-054")
    bench_pokemon = make_card("PAF-007")
    state = make_state(PlayerZones(active=[lumineon], bench=[bench_pokemon]), PlayerZones(active=[defender]))

    actions = lumineon.get_actions(state)

    assert [action.attack.name for action in actions if isinstance(action, AttackAction)] == [
        "Aqua Return"
    ]


def test_lumineon_v_aqua_return_unavailable_without_benched_pokemon():
    lumineon = make_card("BRS-040")
    lumineon.energy = [CardType.WATER, CardType.COLORLESS, CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[lumineon]), PlayerZones(active=[defender]))

    assert [action for action in lumineon.get_actions(state) if isinstance(action, AttackAction)] == []
