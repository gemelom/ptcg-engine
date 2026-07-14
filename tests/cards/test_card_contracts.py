import pytest

from ptcg.core.card import EnergyCard, PokemonCard, TrainerCard
from ptcg.core.card_registry import registry


@pytest.mark.card_coverage("ALL", "metadata")
def test_all_registered_cards_have_metadata_contracts():
    for card_id in registry.list_all():
        card_class = registry.get(card_id)
        assert card_class is not None

        card = card_class()
        assert card.id == f"{card.set_name}-{card.number}"
        assert card.id == card_id
        assert card.name
        assert card.set_name
        assert card.number
        assert card.superType is not None
        assert card.cardType is not None
        assert card.get_info()["name"] == card.name

        if isinstance(card, PokemonCard):
            assert card.hp > 0
            assert card.stage is not None
            assert isinstance(card.retreat, list)
            assert isinstance(card.weakness, list)
            assert isinstance(card.resistance, list)
            assert card.prize >= 1
            if hasattr(card, "attacks"):
                assert isinstance(card.attacks, list)
            if hasattr(card, "ability"):
                assert isinstance(card.ability, list)
        elif isinstance(card, EnergyCard):
            assert card.energyType is not None
            assert card.provides
        elif isinstance(card, TrainerCard):
            assert card.trainerType is not None
            assert hasattr(card, "text")
