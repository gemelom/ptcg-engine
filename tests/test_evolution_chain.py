from __future__ import annotations

from ptcg.core.action import AttackAction, EvolvePokemonAction, UseToolAction
from ptcg.core.enums import PlayerId
from ptcg.core.reducer import reduce_evolve_pokemon_action
from ptcg.utils.utils import discard_pokemon
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


def _zone_card_count(player) -> int:
    """Count every card held in this player's zones and Pokemon attachments."""
    return (
        len(player.active)
        + len(player.bench)
        + len(player.hand)
        + len(player.discard)
        + len(player.left)
        + len(player.prize)
        + len(player.lostZone)
        + sum(len(pokemon.attachment) for pokemon in player.active + player.bench)
    )


def test_two_stage_evolution_keeps_every_under_card():
    charmander = make_card("PAF-007")
    charmeleon = make_card("PAF-008")
    charizard_ex = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            hand=[charmeleon, charizard_ex],
            active=[charmander],
            # 57 filler cards make the starting total exactly 60.
            left=[make_card("SVE-002") for _ in range(57)],
        )
    )

    assert _zone_card_count(state.player1) == 60

    reduce_evolve_pokemon_action(
        EvolvePokemonAction(PlayerId.PLAYER1, charmeleon, charmander), state
    )
    reduce_evolve_pokemon_action(
        EvolvePokemonAction(PlayerId.PLAYER1, charizard_ex, charmeleon), state
    )

    assert state.player1.active == [charizard_ex]
    # Oldest card first, immediate pre-evolution last (physical stack order).
    assert charizard_ex.evolved == [charmander, charmeleon]

    discard_pokemon(state.player1, charizard_ex)

    assert [card.name for card in state.player1.discard] == [
        "Charmander",
        "Charmeleon",
        "Charizard ex",
    ]
    assert _zone_card_count(state.player1) == 60


def test_technical_machine_evolution_keeps_existing_under_cards(monkeypatch):
    monkeypatch.setattr("ptcg.utils.utils.random.shuffle", lambda _cards: None)
    charmander = make_card("PAF-007")
    charmeleon = make_card("PAF-008")
    charizard_ex = make_card("PAF-054")
    technical_machine = make_card("PAR-178")
    state = make_state(
        PlayerZones(
            hand=[charmeleon, technical_machine],
            active=[charmander],
            left=[charizard_ex],
            prize=[make_card("SVE-002")],
        ),
        PlayerZones(
            active=[make_card("PAF-027")],
            left=[make_card("SVE-004")],
            prize=[make_card("SVE-005")],
        ),
    )

    reduce_evolve_pokemon_action(
        EvolvePokemonAction(PlayerId.PLAYER1, charmeleon, charmander), state
    )
    attach = [
        action for action in technical_machine.get_actions(state) if isinstance(action, UseToolAction)
    ]
    assert len(attach) == 1
    list(technical_machine.reduce_action(attach[0], state))

    attack = [
        action for action in technical_machine.get_actions(state) if isinstance(action, AttackAction)
    ]
    assert len(attack) == 1
    drive_choices(
        technical_machine.reduce_action(attack[0], state),
        [lambda _info: [charizard_ex]],
    )

    assert state.player1.active == [charizard_ex]
    assert charizard_ex.evolved == [charmander, charmeleon]
