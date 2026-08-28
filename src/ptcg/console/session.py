"""Interactive match orchestration independent from terminal rendering."""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from functools import cache
from types import MappingProxyType
from typing import Any, Protocol

from ptcg.console.model import (
    ActionView,
    CardView,
    ChoicePromptView,
    DecisionFrame,
    PlayConfig,
    PlayerView,
    QuitGame,
    SelectAction,
    SelectCandidates,
    SessionResult,
    Terminal,
)
from ptcg.core.action import Action, ChooseCardAction, ChooseCardActionSpace
from ptcg.core.card_registry import registry
from ptcg.core.enums import ActionType, CardPosition, PlayerId
from ptcg.core.envs import DEFAULT_DECK, PokemonTCG


class MatchEnvironment(Protocol):
    winner: PlayerId | None
    recorder: Any

    def reset(self) -> tuple: ...

    def step(self, action: Action) -> tuple: ...

    def observe(self, viewer_id: PlayerId) -> dict[str, Any]: ...


_ACTION_GROUPS = {
    ActionType.PLAY_POKEMON_ACTION: "Play",
    ActionType.EVOLVE_POKEMON_ACTION: "Play",
    ActionType.USE_ITEM_ACTION: "Play",
    ActionType.USE_SUPPORTER_ACTION: "Play",
    ActionType.USE_TOOL_ACTION: "Play",
    ActionType.PUT_STADIUM_ACTION: "Play",
    ActionType.ATTACH_ENERGY_ACTION: "Attach",
    ActionType.USE_ABILITY_ACTION: "Ability",
    ActionType.ATTACK_ACTION: "Attack",
    ActionType.USE_STADIUM_ACTION: "Field",
    ActionType.EFFECT_ACTION: "Field",
    ActionType.DISCARD_STADIUM_ACTION: "Field",
    ActionType.RETREAT_ACTION: "Field",
    ActionType.PASS_TURN: "Turn",
}


def run_interactive(
    config: PlayConfig,
    terminal: Terminal,
    *,
    env: MatchEnvironment | None = None,
) -> SessionResult:
    """Run one human-vs-policy match through the terminal seam."""
    if config.opponent_policy not in {"first", "random"}:
        raise ValueError("opponent_policy must be either 'first' or 'random'")
    if config.max_steps <= 0:
        raise ValueError("max_steps must be greater than zero")

    match = env or PokemonTCG(
        seed=config.seed,
        deck1=config.deck,
        deck2=config.opponent_deck,
        verbose=config.verbose,
        record_game=config.record,
    )
    policy_rng = random.Random(config.seed)
    try:
        _observation, reward, done, info = match.reset()
    except KeyboardInterrupt:
        result = _finish_aborted(
            match,
            status="aborted",
            reason="interrupt",
            steps=0,
            reward=0,
            events=(),
        )
        terminal.show_result(result)
        return result
    steps = 0
    pending_events = list(info.get("auto_executed", []))

    while not done and steps < config.max_steps:
        actions: Sequence[Action] = info.get("raw_available_actions", [])
        if not actions:
            result = _finish_aborted(
                match,
                status="error",
                reason="no_available_actions",
                steps=steps,
                reward=reward,
                events=pending_events,
            )
            terminal.show_result(result)
            return result

        owner = actions[0].playerId
        if owner == PlayerId.PLAYER1:
            frame = build_decision_frame(
                config,
                match.observe(PlayerId.PLAYER1),
                actions,
                info,
                pending_events,
            )
            try:
                action = _read_human_action(terminal, frame, actions)
            except EOFError:
                result = _finish_aborted(
                    match,
                    status="aborted",
                    reason="eof",
                    steps=steps,
                    reward=reward,
                    events=pending_events,
                )
                terminal.show_result(result)
                return result
            except KeyboardInterrupt:
                result = _finish_aborted(
                    match,
                    status="aborted",
                    reason="interrupt",
                    steps=steps,
                    reward=reward,
                    events=pending_events,
                )
                terminal.show_result(result)
                return result

            if action is None:
                result = _finish_aborted(
                    match,
                    status="aborted",
                    reason="quit",
                    steps=steps,
                    reward=reward,
                    events=pending_events,
                )
                terminal.show_result(result)
                return result
            pending_events = []
        else:
            action = _select_policy_action(actions, config.opponent_policy, policy_rng)

        pending_events.append(describe_action(action))
        try:
            _observation, reward, done, info = match.step(action)
        except KeyboardInterrupt:
            result = _finish_aborted(
                match,
                status="aborted",
                reason="interrupt",
                steps=steps,
                reward=reward,
                events=pending_events,
            )
            terminal.show_result(result)
            return result
        pending_events.extend(info.get("auto_executed", []))
        steps += 1

    if done:
        winner = info.get("winner") or match.winner
        result = SessionResult(
            status="finished",
            steps=steps,
            reward=float(reward),
            winner=_player_name(winner),
            reason=info.get("termination_reason"),
            events=tuple(pending_events),
        )
    else:
        result = _finish_aborted(
            match,
            status="stopped",
            reason="max_steps",
            steps=steps,
            reward=reward,
            events=pending_events,
        )

    terminal.show_result(result)
    return result


def _read_human_action(
    terminal: Terminal,
    frame: DecisionFrame,
    actions: Sequence[Action],
) -> Action | None:
    while True:
        intent = terminal.choose(frame)
        if isinstance(intent, QuitGame):
            return None

        if isinstance(intent, SelectCandidates):
            if isinstance(actions, ChooseCardActionSpace):
                try:
                    return actions.action_for_candidate_indices(intent.indices)
                except (IndexError, ValueError) as exc:
                    terminal.show_error(str(exc))
                    continue

            if not isinstance(actions[0], ChooseCardAction):
                terminal.show_error("Card candidates are not expected for this decision.")
                continue
            try:
                return _listed_choice_for_candidate_indices(actions, intent.indices)
            except (IndexError, TypeError, ValueError) as exc:
                terminal.show_error(str(exc))
                continue

        if isinstance(intent, SelectAction):
            if isinstance(actions, ChooseCardActionSpace) or isinstance(
                actions[0], ChooseCardAction
            ):
                terminal.show_error("Choose candidate numbers for this card prompt.")
                continue
            if not 0 <= intent.index < len(actions):
                terminal.show_error(f"Action number must be between 1 and {len(actions)}.")
                continue
            return actions[intent.index]

        terminal.show_error("Unsupported terminal input.")


def _listed_choice_for_candidate_indices(
    actions: Sequence[Action],
    indices: Sequence[int],
) -> ChooseCardAction:
    """Find an offered choice in a small, already-materialized action list."""
    template = actions[0]
    if not isinstance(template, ChooseCardAction):
        raise TypeError("This decision does not accept card candidates")
    normalized = sorted(indices)
    if len(set(normalized)) != len(normalized):
        raise ValueError("Candidate indices must be unique")
    if any(index < 0 or index >= len(template.candidates) for index in normalized):
        raise IndexError("Candidate index out of range")

    chosen = [template.candidates[index] for index in normalized]
    for action in actions:
        if not isinstance(action, ChooseCardAction) or len(action.chosen) != len(chosen):
            continue
        if all(actual is expected for actual, expected in zip(action.chosen, chosen)):
            return action
    raise ValueError("That candidate combination is not available")


def build_decision_frame(
    config: PlayConfig,
    observation: Mapping[str, Any],
    actions: Sequence[Action],
    info: Mapping[str, Any],
    events: Sequence[str],
) -> DecisionFrame:
    """Build a detached frame containing only information safe for the human."""
    human = _player_view(observation["self"], reveal_hand=True)
    opponent = _player_view(observation["opponent"], reveal_hand=False)
    stadium = tuple(
        _card_view(f"S{index}", card_data)
        for index, card_data in enumerate(observation.get("stadium", []), start=1)
    )

    prompt_view = None
    action_views: tuple[ActionView, ...] = ()
    prompt = info.get("prompt")
    if prompt is not None:
        choice_counts = _choice_counts(actions)
        candidates = []
        for index, candidate in enumerate(prompt.candidates, start=1):
            if prompt.hidden:
                position = getattr(candidate, "cardPosition", None)
                label = "Prize" if position == CardPosition.PRIZE else "Hidden card"
                candidates.append(
                    CardView(
                        reference=f"C{index}",
                        name=f"{label} {index}",
                        set_name="",
                        number="",
                    )
                )
            else:
                candidates.append(_card_view_from_object(f"C{index}", candidate))
        prompt_view = ChoicePromptView(
            min_count=min(choice_counts),
            max_count=max(choice_counts),
            allowed_counts=choice_counts,
            tips=prompt.tips,
            candidates=tuple(candidates),
        )
    else:
        action_views = tuple(
            ActionView(
                number=index,
                group=_ACTION_GROUPS.get(action.actionType, "Other"),
                description=describe_action(action),
                card=_action_card_view(action),
            )
            for index, action in enumerate(actions, start=1)
        )

    return DecisionFrame(
        seed=config.seed,
        human_deck=config.deck or DEFAULT_DECK,
        opponent_deck=config.opponent_deck or DEFAULT_DECK,
        opponent_policy=config.opponent_policy,
        timestep=int(observation.get("timestep", 0)),
        turn_number=int(observation.get("turn_number", 0)),
        turn=observation.get("turn"),
        human=human,
        opponent=opponent,
        stadium=stadium,
        events=tuple(events),
        actions=action_views,
        prompt=prompt_view,
    )


def _choice_counts(actions: Sequence[Action]) -> tuple[int, ...]:
    if isinstance(actions, ChooseCardActionSpace):
        upper = min(actions.max_cnt, len(actions.candidates))
        return tuple(range(actions.min_cnt, upper + 1))
    counts = sorted(
        {len(action.chosen) for action in actions if isinstance(action, ChooseCardAction)}
    )
    if not counts:
        raise ValueError("A card prompt must offer at least one card choice")
    return tuple(counts)


def _player_view(data: Mapping[str, Any], *, reveal_hand: bool) -> PlayerView:
    active = tuple(
        _card_view(f"A{index}", card_data)
        for index, card_data in enumerate(data.get("active", []), start=1)
    )
    bench = tuple(
        _card_view(f"B{index}", card_data)
        for index, card_data in enumerate(data.get("bench", []), start=1)
    )
    hand_data = data.get("hand") if reveal_hand else None
    hand = tuple(
        _card_view(f"H{index}", card_data)
        for index, card_data in enumerate(hand_data or [], start=1)
    )
    return PlayerView(
        player_id=str(data.get("id", "unknown")),
        hand_count=int(data.get("hand_count", 0)),
        deck_count=int(data.get("deck_count", 0)),
        prize_count=int(data.get("prize_count", 0)),
        discard_count=len(data.get("discard", [])),
        active=active,
        bench=bench,
        hand=hand,
    )


def _card_view(reference: str, data: Mapping[str, Any]) -> CardView:
    set_name = str(data.get("set_name", ""))
    number = str(data.get("number", ""))
    details = _card_description(set_name, number) if set_name and number else None
    return CardView(
        reference=reference,
        name=str(data.get("name", "Unknown card")),
        set_name=set_name,
        number=number,
        current_hp=str(data["hp"]) if "hp" in data else None,
        maximum_hp=str(details["hp"]) if details and "hp" in details else None,
        energy=tuple(str(value) for value in data.get("energy", [])),
        tools=tuple(str(value) for value in data.get("tool", [])),
        details=details,
    )


@cache
def _card_description(set_name: str, number: str) -> Mapping[str, Any] | None:
    details = registry.describe(set_name, number)
    return _freeze(details) if details else None


def _card_view_from_object(reference: str, card: Any) -> CardView:
    return _card_view(reference, card.to_dict())


def _action_card_view(action: Action) -> CardView | None:
    for attribute in ("source", "active_pokemon", "target"):
        card = getattr(action, attribute, None)
        if hasattr(card, "set_name") and hasattr(card, "number"):
            return _card_view_from_object("", card)
    return None


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _select_policy_action(
    actions: Sequence[Action],
    policy: str,
    rng: random.Random,
) -> Action:
    if policy == "random":
        return rng.choice(actions)
    return actions[0]


def describe_action(action: Action) -> str:
    try:
        return action.to_nl()
    except Exception:  # noqa: BLE001 - card-provided renderers must not break the CLI
        return repr(action)


def _finish_aborted(
    match: MatchEnvironment,
    *,
    status: str,
    reason: str,
    steps: int,
    reward: float,
    events: Sequence[str],
) -> SessionResult:
    recorder = getattr(match, "recorder", None)
    if recorder is not None:
        recorder.record_aborted(reason)
    return SessionResult(
        status=status,
        steps=steps,
        reward=float(reward),
        reason=reason,
        events=tuple(events),
    )


def _player_name(player: Any) -> str | None:
    if player is None:
        return None
    return getattr(player, "name", str(player)).lower()
