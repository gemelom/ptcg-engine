"""
Common utility functions for agent action filtering.
"""

from ptcg.core.action import ChooseCardAction


def filter_actions(legal_actions):
    """
    Filter legal actions to remove duplicates based on card name combinations.

    For ChooseCardAction with indexed=True, keeps only unique card name combinations.
    For other action types (or indexed=False), returns the original list unchanged.

    Args:
        legal_actions: List of legal actions to filter

    Returns:
        Filtered list of unique actions
    """
    if not legal_actions:
        return legal_actions

    if isinstance(legal_actions[0], ChooseCardAction) and legal_actions[0].indexed:
        # Keep only unique card name combinations
        seen_combinations = set()
        filtered_actions = []

        for action in legal_actions:
            # Convert cards list to tuple of card names for hashing
            cards_name_tuple = tuple(sorted(card.name for card in action.chosen))
            if cards_name_tuple not in seen_combinations:
                seen_combinations.add(cards_name_tuple)
                filtered_actions.append(action)

        return filtered_actions
    else:
        return legal_actions
