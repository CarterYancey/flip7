from __future__ import annotations

from typing import Protocol, TYPE_CHECKING
from enum import Enum, auto

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


class HumanStrategy:
    """Interactive strategy that prompts a human for each decision."""

    def choose_action(self, player, active_opponents):
        if player.forced_flips > 0:
            return "hit"

        current_score = player.calculate_round_score()
        prompt = (
            f"\n{player.name}, it's your turn.\n"
            f"Current hand: {player.hand}\n"
            f"Current round score: {current_score}\n"
            "Choose action ([h]it/[s]tay): "
        )

        while True:
            choice = input(prompt).strip().lower()
            if choice in {"h", "hit"}:
                return "hit"
            if choice in {"s", "stay"}:
                return "stay"
            print("Please enter 'h' to hit or 's' to stay.")


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


class PerfectStrategy:
    """Card-counting strategy that maximizes expected value each turn."""

    @staticmethod
    def _simulate_score_after_hit(player, card):
        # Local import to avoid circular dependency at module load time
        from flip7 import CardType, Player

        temp_player = Player(player.name)
        temp_player.hand = list(player.hand)
        temp_player.busted = False
        temp_player.second_chance = player.second_chance

        if getattr(card.card_type, "name", None) == "NUMBER":
            existing_nums = [
                c.value for c in temp_player.hand if getattr(c.card_type, "name", None) == "NUMBER"
            ]
            if card.value in existing_nums:
                if temp_player.second_chance:
                    temp_player.second_chance = False
                else:
                    temp_player.busted = True
                    return 0
            else:
                temp_player.hand.append(card)
        elif getattr(card.card_type, "name", None) == "ACTION":
            temp_player.hand.append(card)
            if card.name == "Second Chance" and not temp_player.second_chance:
                temp_player.second_chance = True
        else:
            temp_player.hand.append(card)

        return temp_player.calculate_round_score()

    def choose_action(self, player, active_opponents):
        game = getattr(player, "game", None)
        if not game or not game.deck.draw_pile:
            return "stay"

        deck = game.deck
        remaining_cards = deck.draw_pile
        total_cards = len(remaining_cards)

        numbers_in_hand = {
            c.value for c in player.hand if getattr(c.card_type, "name", None) == "NUMBER"
        }

        if player.second_chance:
            bust_probability = 0
        else:
            bust_cards = [
                c
                for c in remaining_cards
                if getattr(c.card_type, "name", None) == "NUMBER" and c.value in numbers_in_hand
            ]
            bust_probability = len(bust_cards) / total_cards

        current_score = player.calculate_round_score()
        expected_score = sum(self._simulate_score_after_hit(player, card) for card in remaining_cards) / total_cards
        #print("current score: ", current_score)
        #print("expected score: ", expected_score)

        if expected_score > current_score and bust_probability < 1:
            return "hit"

        return "stay"
