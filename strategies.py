from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from typing import Iterable
    from flip7 import Player


class Strategy(Protocol):
    """Protocol for player decision logic."""

    def choose_action(self, player: "Player", active_opponents: "Iterable[Player]") -> str:
        """Return "hit" or "stay" for the given player."""
        ...


class AggressiveStrategy:
    """Always hit, regardless of score or opponents."""

    def choose_action(self, player, active_opponents):
        return "hit"


class ConservativeStrategy:
    """Stay once the player reaches a configurable score threshold."""

    def __init__(self, stay_threshold: int = 40):
        self.stay_threshold = stay_threshold

    def choose_action(self, player, active_opponents):
        if player.forced_flips > 0:
            return "hit"

        current_score = player.calculate_round_score()
        if current_score >= self.stay_threshold:
            return "stay"
        return "hit"


class Flip7ChaserStrategy:
    """Keep drawing to chase Flip 7 unless the score is already comfortable."""

    def __init__(self, safe_score: int = 50):
        self.safe_score = safe_score

    @staticmethod
    def _unique_number_count(player) -> int:
        return len({c.value for c in player.hand if getattr(c.card_type, "name", None) == "NUMBER"})

    def choose_action(self, player, active_opponents):
        if player.forced_flips > 0:
            return "hit"

        unique_numbers = self._unique_number_count(player)
        current_score = player.calculate_round_score()

        if player.has_flip_seven():
            return "stay"

        if unique_numbers >= 5:
            return "hit"

        if current_score >= self.safe_score:
            return "stay"

        return "hit"
