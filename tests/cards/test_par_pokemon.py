import pytest

from ptcg.core.action import AttackAction, EffectAction, UseAbilityAction
from ptcg.core.effect import Effect
from ptcg.core.enums import CardType, Coin, PlayerId, PokemonPosition
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("PAR-056")
@pytest.mark.card_coverage(
    "PAR-056",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
    "damage",
    "ability",
)
def test_iron_bundle_hyper_blower_forces_opponent_to_choose_new_active():
    iron_bundle = make_card("PAR-056")
    attached_tool = make_card("PAL-173")
    iron_bundle.attachment = [attached_tool]
    opponent_active = make_card("PAF-054")
    first_bench = make_card("PAF-007")
    chosen_new_active = make_card("PAF-027")
    state = make_state(
        PlayerZones(bench=[iron_bundle]),
        PlayerZones(active=[opponent_active], bench=[first_bench, chosen_new_active]),
    )
    state.player1.onceUsedTurn["Hyper Blower"] = False

    actions = iron_bundle.get_actions(state)
    ability_actions = [action for action in actions if isinstance(action, UseAbilityAction)]
    assert len(ability_actions) == 1

    prompts = drive_choices(
        iron_bundle.reduce_action(ability_actions[0], state),
        [lambda _info: [chosen_new_active]],
    )

    assert prompts[0]["prompt"].source is iron_bundle
    assert prompts[0]["prompt"].candidates == [
        first_bench,
        chosen_new_active,
        opponent_active,
    ]
    assert state.player2.active == [chosen_new_active]
    assert state.player2.bench == [first_bench, opponent_active]
    assert chosen_new_active.position == PokemonPosition.ACTIVE
    assert opponent_active.position == PokemonPosition.BENCH
    assert iron_bundle not in state.player1.bench
    assert [card.name for card in state.player1.discard] == ["Bravery Charm", "Iron Bundle"]
    assert iron_bundle.abilityUsed is True
    assert state.player1.onceUsedTurn["Hyper Blower"] is True


def test_iron_bundle_hyper_blower_unavailable_from_active_spot():
    iron_bundle = make_card("PAR-056")
    state = make_state(
        PlayerZones(active=[iron_bundle]),
        PlayerZones(active=[make_card("PAF-054")], bench=[make_card("PAF-007")]),
    )
    state.player1.onceUsedTurn["Hyper Blower"] = False

    assert [
        action for action in iron_bundle.get_actions(state) if isinstance(action, UseAbilityAction)
    ] == []


def test_iron_bundle_hyper_blower_unavailable_without_opponents_bench():
    iron_bundle = make_card("PAR-056")
    state = make_state(PlayerZones(bench=[iron_bundle]), PlayerZones(active=[make_card("PAF-054")]))
    state.player1.onceUsedTurn["Hyper Blower"] = False

    assert [
        action for action in iron_bundle.get_actions(state) if isinstance(action, UseAbilityAction)
    ] == []


def test_iron_bundle_refrigerated_stream_damages_opponents_active_pokemon():
    iron_bundle = make_card("PAR-056")
    iron_bundle.energy = [CardType.WATER, CardType.COLORLESS, CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[iron_bundle],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )
    state.player1.onceUsedTurn["Hyper Blower"] = False

    actions = iron_bundle.get_actions(state)
    refrigerated_stream = [
        action
        for action in actions
        if isinstance(action, AttackAction) and action.attack.name == "Refrigerated Stream"
    ]
    assert len(refrigerated_stream) == 1

    list(iron_bundle.reduce_action(refrigerated_stream[0], state))

    assert defender.hp == 250
    assert state.turn == state.player2.id


def test_iron_bundle_refrigerated_stream_unavailable_without_energy():
    iron_bundle = make_card("PAR-056")
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[iron_bundle]), PlayerZones(active=[defender]))
    state.player1.onceUsedTurn["Hyper Blower"] = False

    assert [
        action for action in iron_bundle.get_actions(state) if isinstance(action, AttackAction)
    ] == []


@pytest.mark.card("PAR-086")
@pytest.mark.card_coverage(
    "PAR-086",
    "get_actions",
    "reduce_action",
    "negative_case",
    "damage",
)
def test_scream_tail_psybolt_damages_and_puts_defender_asleep_on_heads(monkeypatch):
    monkeypatch.setattr("ptcg.cards.PAR.scream_tail.flip_coin", lambda _state: Coin.HEAD)
    scream_tail = make_card("PAR-086")
    scream_tail.energy = [CardType.PSYCHIC]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[scream_tail],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )

    actions = scream_tail.get_actions(state)
    psybolt = [
        action
        for action in actions
        if isinstance(action, AttackAction) and action.attack.name == "Psybolt"
    ]
    assert len(psybolt) == 1

    list(scream_tail.reduce_action(psybolt[0], state))

    assert defender.hp == 310
    assert defender.asleep is True
    assert state.turn == state.player2.id


def test_scream_tail_psybolt_does_not_sleep_defender_on_tails(monkeypatch):
    monkeypatch.setattr("ptcg.cards.PAR.scream_tail.flip_coin", lambda _state: Coin.TAIL)
    scream_tail = make_card("PAR-086")
    scream_tail.energy = [CardType.PSYCHIC]
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[scream_tail]), PlayerZones(active=[defender]))

    list(scream_tail.reduce_action(scream_tail.get_actions(state)[0], state))

    assert defender.hp == 310
    assert getattr(defender, "asleep", False) is False


def test_scream_tail_psybolt_unavailable_without_psychic_energy():
    scream_tail = make_card("PAR-086")
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[scream_tail]), PlayerZones(active=[defender]))

    assert [
        action for action in scream_tail.get_actions(state) if isinstance(action, AttackAction)
    ] == []


@pytest.mark.card("PAR-088")
@pytest.mark.card_coverage(
    "PAR-088",
    "get_actions",
    "reduce_action",
    "negative_case",
    "damage",
)
def test_gimmighoul_continuous_coin_toss_damages_for_each_heads(monkeypatch):
    coin_results = iter([Coin.HEAD, Coin.HEAD, Coin.TAIL])
    monkeypatch.setattr("ptcg.cards.PAR.gimmighoul.flip_coin", lambda _state: next(coin_results))
    gimmighoul = make_card("PAR-088")
    gimmighoul.energy = [CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[gimmighoul],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )

    actions = gimmighoul.get_actions(state)
    continuous_coin_toss = [
        action
        for action in actions
        if isinstance(action, AttackAction) and action.attack.name == "Continuous Coin Toss"
    ]
    assert len(continuous_coin_toss) == 1

    list(gimmighoul.reduce_action(continuous_coin_toss[0], state))

    assert continuous_coin_toss[0].attack.damage == 40
    assert defender.hp == 290
    assert state.turn == state.player2.id


def test_gimmighoul_continuous_coin_toss_deals_no_damage_on_first_tails(monkeypatch):
    monkeypatch.setattr("ptcg.cards.PAR.gimmighoul.flip_coin", lambda _state: Coin.TAIL)
    gimmighoul = make_card("PAR-088")
    gimmighoul.energy = [CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[gimmighoul]), PlayerZones(active=[defender]))

    list(gimmighoul.reduce_action(gimmighoul.get_actions(state)[0], state))

    assert defender.hp == 330


def test_gimmighoul_continuous_coin_toss_unavailable_without_energy():
    gimmighoul = make_card("PAR-088")
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[gimmighoul]), PlayerZones(active=[defender]))

    assert [
        action for action in gimmighoul.get_actions(state) if isinstance(action, AttackAction)
    ] == []


@pytest.mark.card("PAR-126")
@pytest.mark.card_coverage(
    "PAR-126",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
    "ability",
)
def test_jirachi_charge_energy_puts_two_basic_energy_from_deck_into_hand(monkeypatch):
    monkeypatch.setattr("ptcg.utils.utils.random.shuffle", lambda _cards: None)
    jirachi = make_card("PAR-126")
    jirachi.energy = [CardType.COLORLESS]
    fire_energy = make_card("SVE-002")
    lightning_energy = make_card("SVE-004")
    rare_candy = make_card("PAF-089")
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[fire_energy, rare_candy, lightning_energy],
            prize=[make_card("SVE-005")],
            active=[jirachi],
        ),
        PlayerZones(
            left=[make_card("SVE-007")],
            prize=[make_card("SVE-008")],
            active=[defender],
        ),
    )

    actions = jirachi.get_actions(state)
    charge_energy = [
        action
        for action in actions
        if isinstance(action, AttackAction) and action.attack.name == "Charge Energy"
    ]
    assert len(charge_energy) == 1

    prompts = drive_choices(
        jirachi.reduce_action(charge_energy[0], state),
        [lambda _info: [fire_energy, lightning_energy]],
    )

    assert prompts[0]["prompt"].source is jirachi
    assert prompts[0]["prompt"].candidates == [fire_energy, lightning_energy]
    assert state.player1.hand == [fire_energy, lightning_energy]
    assert state.player1.left == [rare_candy]
    assert state.turn == state.player2.id


def test_jirachi_charge_energy_unavailable_without_energy():
    jirachi = make_card("PAR-126")
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[jirachi]), PlayerZones(active=[defender]))

    assert [
        action for action in jirachi.get_actions(state) if isinstance(action, AttackAction)
    ] == []


def test_jirachi_stellar_veil_prevents_damage_counters_to_own_bench_from_basic_attacker():
    jirachi = make_card("PAR-126")
    benched_target = make_card("PAF-007")
    attacker = make_card("PAR-086")
    state = make_state(
        PlayerZones(bench=[jirachi, benched_target]),
        PlayerZones(active=[attacker]),
        turn=PlayerId.PLAYER2,
    )
    effect = Effect(6)
    action = EffectAction(state.player2.id, attacker, effect, benched_target)

    jirachi.use_ability(action, state)

    assert effect.dc == 0


def test_jirachi_stellar_veil_does_not_prevent_damage_counters_from_evolution_attacker():
    jirachi = make_card("PAR-126")
    benched_target = make_card("PAF-007")
    attacker = make_card("TWM-200")
    state = make_state(
        PlayerZones(bench=[jirachi, benched_target]),
        PlayerZones(active=[attacker]),
        turn=PlayerId.PLAYER2,
    )
    effect = Effect(6)
    action = EffectAction(state.player2.id, attacker, effect, benched_target)

    jirachi.use_ability(action, state)

    assert effect.dc == 6


@pytest.mark.card("PAR-139")
@pytest.mark.card_coverage(
    "PAR-139",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
    "damage",
    "ability",
)
def test_gholdengo_ex_coin_bonus_draws_two_cards_from_active_spot():
    gholdengo = make_card("PAR-139")
    drawn_cards = [make_card("SVE-002"), make_card("SVE-004")]
    remaining_card = make_card("SVE-005")
    state = make_state(PlayerZones(left=drawn_cards + [remaining_card], active=[gholdengo]))
    state.player1.onceUsedTurn["Coin Bonus"] = False

    actions = gholdengo.get_actions(state)
    ability_actions = [action for action in actions if isinstance(action, UseAbilityAction)]
    assert len(ability_actions) == 1

    list(gholdengo.reduce_action(ability_actions[0], state))

    assert state.player1.hand == drawn_cards
    assert state.player1.left == [remaining_card]
    assert gholdengo.abilityUsed is True
    assert state.player1.onceUsedTurn["Coin Bonus"] is True


def test_gholdengo_ex_coin_bonus_draws_one_card_from_bench():
    gholdengo = make_card("PAR-139")
    drawn_card = make_card("SVE-002")
    remaining_card = make_card("SVE-004")
    state = make_state(PlayerZones(left=[drawn_card, remaining_card], bench=[gholdengo]))
    state.player1.onceUsedTurn["Coin Bonus"] = False

    ability_actions = [
        action for action in gholdengo.get_actions(state) if isinstance(action, UseAbilityAction)
    ]
    assert len(ability_actions) == 1

    list(gholdengo.reduce_action(ability_actions[0], state))

    assert state.player1.hand == [drawn_card]
    assert state.player1.left == [remaining_card]


def test_gholdengo_ex_coin_bonus_unavailable_after_use():
    gholdengo = make_card("PAR-139")
    state = make_state(PlayerZones(active=[gholdengo]))
    state.player1.onceUsedTurn["Coin Bonus"] = True

    assert [
        action for action in gholdengo.get_actions(state) if isinstance(action, UseAbilityAction)
    ] == []


def test_gholdengo_ex_make_it_rain_discards_basic_energy_for_damage():
    gholdengo = make_card("PAR-139")
    gholdengo.energy = [CardType.METAL]
    fire_energy = make_card("SVE-002")
    lightning_energy = make_card("SVE-004")
    rare_candy = make_card("PAF-089")
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            hand=[fire_energy, rare_candy, lightning_energy],
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[gholdengo],
        ),
        PlayerZones(
            left=[make_card("SVE-008")],
            prize=[make_card("PAF-084")],
            active=[defender],
        ),
    )
    state.player1.onceUsedTurn["Coin Bonus"] = False

    make_it_rain = [
        action
        for action in gholdengo.get_actions(state)
        if isinstance(action, AttackAction) and action.attack.name == "Make It Rain"
    ]
    assert len(make_it_rain) == 1

    prompts = drive_choices(
        gholdengo.reduce_action(make_it_rain[0], state),
        [lambda _info: [fire_energy, lightning_energy]],
    )

    assert prompts[0]["prompt"].source is gholdengo
    assert prompts[0]["prompt"].candidates == [fire_energy, lightning_energy]
    assert make_it_rain[0].attack.damage == 100
    assert defender.hp == 230
    assert state.player1.hand == [rare_candy]
    assert fire_energy in state.player1.discard
    assert lightning_energy in state.player1.discard
    assert state.turn == state.player2.id


def test_gholdengo_ex_make_it_rain_can_discard_no_energy_for_zero_damage():
    gholdengo = make_card("PAR-139")
    gholdengo.energy = [CardType.METAL]
    fire_energy = make_card("SVE-002")
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(hand=[fire_energy], active=[gholdengo]),
        PlayerZones(active=[defender]),
    )
    state.player1.onceUsedTurn["Coin Bonus"] = False

    make_it_rain = [
        action
        for action in gholdengo.get_actions(state)
        if isinstance(action, AttackAction) and action.attack.name == "Make It Rain"
    ]

    drive_choices(
        gholdengo.reduce_action(make_it_rain[0], state),
        [lambda _info: []],
    )

    assert make_it_rain[0].attack.damage == 0
    assert defender.hp == 330
    assert state.player1.hand == [fire_energy]


def test_gholdengo_ex_make_it_rain_unavailable_without_metal_energy():
    gholdengo = make_card("PAR-139")
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[gholdengo]), PlayerZones(active=[defender]))
    state.player1.onceUsedTurn["Coin Bonus"] = False

    assert [
        action for action in gholdengo.get_actions(state) if isinstance(action, AttackAction)
    ] == []


@pytest.mark.card("PAR-248")
@pytest.mark.card_coverage(
    "PAR-248",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
    "damage",
    "ko",
)
def test_iron_hands_ex_amp_you_very_much_takes_extra_prize_on_knockout():
    iron_hands = make_card("PAR-248")
    iron_hands.energy = [
        CardType.LIGHTNING,
        CardType.COLORLESS,
        CardType.COLORLESS,
        CardType.COLORLESS,
    ]
    prize_1 = make_card("SVE-002")
    prize_2 = make_card("SVE-004")
    remaining_prize = make_card("SVE-005")
    defender = make_card("PAF-007")
    replacement = make_card("PAF-027")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-007")],
            prize=[prize_1, prize_2, remaining_prize],
            active=[iron_hands],
        ),
        PlayerZones(
            left=[make_card("SVE-008")],
            prize=[make_card("PAF-084")],
            active=[defender],
            bench=[replacement],
        ),
    )

    amp_you_very_much = [
        action
        for action in iron_hands.get_actions(state)
        if isinstance(action, AttackAction) and action.attack.name == "Amp You Very Much"
    ]
    assert len(amp_you_very_much) == 1

    prompts = drive_choices(
        iron_hands.reduce_action(amp_you_very_much[0], state),
        [
            lambda _info: [prize_1, prize_2],
            lambda _info: [replacement],
        ],
    )

    assert prompts[0]["prompt"].source is None
    assert prompts[0]["prompt"].candidates == [prize_1, prize_2, remaining_prize]
    assert prompts[1]["prompt"].source is None
    assert prompts[1]["prompt"].candidates == [replacement]
    assert state.player1.hand == [prize_1, prize_2]
    assert state.player1.prize == [remaining_prize]
    assert [card.name for card in state.player2.discard] == ["Charmander"]
    assert state.player2.active == [replacement]
    assert state.player2.bench == []
    assert state.player2.hasPokemonDead is True
    assert state.turn == state.player2.id


def test_iron_hands_ex_arm_press_damages_opponents_active_pokemon():
    iron_hands = make_card("PAR-248")
    iron_hands.energy = [CardType.LIGHTNING, CardType.LIGHTNING, CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[iron_hands],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )

    arm_press = [
        action
        for action in iron_hands.get_actions(state)
        if isinstance(action, AttackAction) and action.attack.name == "Arm Press"
    ]
    assert len(arm_press) == 1

    list(iron_hands.reduce_action(arm_press[0], state))

    assert defender.hp == 170
    assert state.turn == state.player2.id


def test_iron_hands_ex_amp_you_very_much_unavailable_without_fourth_energy():
    iron_hands = make_card("PAR-248")
    iron_hands.energy = [CardType.LIGHTNING, CardType.COLORLESS, CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[iron_hands]), PlayerZones(active=[defender]))

    assert [
        action.attack.name
        for action in iron_hands.get_actions(state)
        if isinstance(action, AttackAction)
    ] == []
