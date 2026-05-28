import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Type

from ptcg.core.card import Card

CARDS_DIR = Path(__file__).parent.parent / "cards"


class CardRegistry:
    _instance: Optional["CardRegistry"] = None
    _cards: Dict[str, Type[Card]]
    _loaded: bool

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cards = {}
            cls._instance._loaded = False
        return cls._instance

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self._scan_card_implementations()
            self._loaded = True

    def _scan_card_implementations(self) -> None:
        for py_file in sorted(CARDS_DIR.rglob("*.py")):
            if py_file.name == "__init__.py":
                continue
            rel = py_file.relative_to(CARDS_DIR)
            module_name = "ptcg.cards." + str(rel.with_suffix("")).replace("/", ".")

            try:
                module = importlib.import_module(module_name)
            except Exception as e:
                print(f"Warning: Could not import {module_name}: {e}")
                continue

            for _attr_name, obj in inspect.getmembers(module, inspect.isclass):
                if not issubclass(obj, Card) or obj is Card:
                    continue
                # Only register classes defined in this module (not re-exported)
                if obj.__module__ != module_name:
                    continue
                try:
                    instance = obj()
                    card_id = instance.id
                    if card_id:
                        self._cards[card_id] = obj
                except Exception as e:
                    print(f"Warning: Could not instantiate {obj.__name__}: {e}")

    def get(self, card_id: str) -> Optional[Type[Card]]:
        self._ensure_loaded()
        return self._cards.get(card_id)

    def get_by_set_and_number(self, set_name: str, number: str) -> Optional[Type[Card]]:
        self._ensure_loaded()
        return self._cards.get(f"{set_name}-{number}")

    def list_all(self) -> List[str]:
        self._ensure_loaded()
        return list(self._cards.keys())


registry = CardRegistry()


def _build_card_list() -> Dict[str, Optional[Type[Card]]]:
    card_list: Dict[str, Optional[Type[Card]]] = {"NONE": None}
    for card_id, card_class in registry._cards.items():
        card_list[card_id] = card_class
    return card_list


class _CardListProxy:
    def __init__(self):
        self._cached: Optional[Dict[str, Optional[Type[Card]]]] = None

    def __getitem__(self, key: str) -> Optional[Type[Card]]:
        if self._cached is None:
            registry._ensure_loaded()
            self._cached = _build_card_list()
        return self._cached[key]

    def get(self, key: str, default: Optional[Type[Card]] = None) -> Optional[Type[Card]]:
        if self._cached is None:
            registry._ensure_loaded()
            self._cached = _build_card_list()
        return self._cached.get(key, default)


CardList: Dict[str, Optional[Type[Card]]] = _CardListProxy()  # type: ignore
