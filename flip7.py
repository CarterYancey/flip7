import random
from enum import Enum, auto
from typing import Iterable, Optional

from strategies import (
    AggressiveStrategy,
    ConservativeStrategy,
    Flip7ChaserStrategy,
    Strategy,
)

class CardType(Enum):
    NUMBER = auto()
    ACTION = auto()
    MODIFIER = auto()

class Card:
    def __init__(self, name, card_type, value=0, count=1):
        self.name = name
        self.card_type = card_type
        self.value = value
        self.count = count # For deck generation

    def __repr__(self):
        return f"[{self.name}]"

class Deck:
    def __init__(self):
        self.draw_pile = []
        self.discard_pile = []
        self.build_deck()

    def build_deck(self):
        # Number Cards: One 0, One 1, Two 2s ... Twelve 12s [cite: 13, 14, 52]
        cards = [Card("0", CardType.NUMBER, 0, 1)]
        for i in range(1, 13):
            cards.append(Card(str(i), CardType.NUMBER, i, i))
        
        # Action Cards [cite: 14, 34, 39]
        # Counts are estimated based on visual "x3" cues in the document
        cards.append(Card("Flip Three", CardType.ACTION, 0, 3))
        cards.append(Card("Freeze", CardType.ACTION, 0, 3))
        cards.append(Card("Second Chance", CardType.ACTION, 0, 3))

        # Modifier Cards [cite: 40, 114, 118, 119]
        # Estimated remaining counts to reach ~94 cards
        cards.append(Card("+2 Points", CardType.MODIFIER, 2, 1))
        cards.append(Card("+4 Points", CardType.MODIFIER, 4, 1))
        cards.append(Card("+8 Points", CardType.MODIFIER, 8, 1)) # Inferred from image
        cards.append(Card("+10 Points", CardType.MODIFIER, 10, 1))
        cards.append(Card("x2 Multiplier", CardType.MODIFIER, 0, 1))

        final_deck = []
        for c in cards:
            for _ in range(c.count):
                final_deck.append(Card(c.name, c.card_type, c.value))
        
        self.draw_pile = final_deck
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.draw_pile)

    def draw(self):
        if not self.draw_pile:
            # Reshuffle discard into draw if empty [cite: 185]
            if not self.discard_pile:
                return None # Truly out of cards
            self.draw_pile = self.discard_pile[:]
            self.discard_pile = []
            self.shuffle()
            print("--- Deck Reshuffled ---")
        
        return self.draw_pile.pop()

class Player:
    def __init__(self, name: str, strategy: Optional[Strategy] = None):
        self.name = name
        self.total_game_score = 0
        self.hand = [] # Current round cards
        self.active = True # False if Stayed, Busted, or Frozen
        self.busted = False
        self.frozen = False
        self.second_chance = False
        self.forced_flips = 0 # For 'Flip Three' action
        self.strategy = strategy or Flip7ChaserStrategy()

    def reset_round(self):
        self.hand = []
        self.active = True
        self.busted = False
        self.frozen = False
        self.second_chance = False
        self.forced_flips = 0

    def calculate_round_score(self):
        # [cite: 147-170]
        if self.busted:
            return 0
        
        number_sum = sum(c.value for c in self.hand if c.card_type == CardType.NUMBER)
        
        # Apply Multiplier First [cite: 122]
        has_multiplier = any(c.name == "x2 Multiplier" for c in self.hand)
        if has_multiplier:
            number_sum *= 2
            
        # Add Bonus Points [cite: 161]
        modifier_sum = sum(c.value for c in self.hand if c.card_type == CardType.MODIFIER and c.name != "x2 Multiplier")
        
        total = number_sum + modifier_sum
        
        # Check Flip 7 Bonus [cite: 170]
        unique_nums = {c.value for c in self.hand if c.card_type == CardType.NUMBER}
        if len(unique_nums) >= 7:
            total += 15
            
        return total

    def has_flip_seven(self):
        # [cite: 9]
        unique_nums = {c.value for c in self.hand if c.card_type == CardType.NUMBER}
        return len(unique_nums) >= 7

    def decide_action(self, active_opponents: Iterable["Player"]):
        # Always hit if forced
        if self.forced_flips > 0:
            return "hit"

        return self.strategy.choose_action(self, active_opponents)

class Game:
    def __init__(self, player_names, strategies=None):
        self.players = []
        for idx, name in enumerate(player_names):
            strategy = None
            if strategies and idx < len(strategies):
                strategy = strategies[idx]
            self.players.append(Player(name, strategy=strategy))
        self.deck = Deck()
        self.dealer_index = 0
        self.round_num = 1
        self.winning_score = 200 # [cite: 5]

    def play_game(self):
        print(f"Starting Flip 7! Goal: {self.winning_score} points.\n")
        
        while all(p.total_game_score < self.winning_score for p in self.players):
            self.play_round()
            self.round_num += 1
            
            # Check for winner [cite: 188]
            leaders = sorted(self.players, key=lambda x: x.total_game_score, reverse=True)
            if leaders[0].total_game_score >= self.winning_score:
                print(f"\nGame Over! {leaders[0].name} wins with {leaders[0].total_game_score} points!")
                return
                
    def get_active_players(self):
        return [p for p in self.players if p.active]

    def resolve_action_card(self, card, drawer, players):
        # [cite: 86] Action cards target active players
        #TODO Improve target logic. Sometimes a player may want to target their self.
        targets = [p for p in players if p.active and p != drawer]
        if not targets:
            target = drawer # Targets self if only one active [cite: 87]
        else:
            target = random.choice(targets)

        #print(f"  > Action! {drawer.name} plays {card.name} on {target.name}")

        if card.name == "Freeze":
            # [cite: 93] Target banks points and is out
            target.frozen = True
            target.active = False
            print(f"  > {target.name} is Frozen! They bank their current score and exit the round.")

        elif card.name == "Flip Three":
            # [cite: 95] Target must accept next 3 cards
            target.forced_flips += 3
            print(f"  > {target.name} must Flip Three cards!")

        elif card.name == "Second Chance":
            # [cite: 104] Keep this card. Protects against bust.
            # Max 1 per player [cite: 105]
            if not drawer.second_chance:
                drawer.second_chance = True
                drawer.hand.append(card)
                print(f"  > {drawer.name} gains a Second Chance!")
            else:
                # Pass to another player if already have one [cite: 106]
                if targets: #TODO: This is just giving it to a specific player without checking to see if that player already has one (they might).
                    targets[0].second_chance = True
                    targets[0].hand.append(card)
                    print(f"  > {drawer.name} already has one. Passed Second Chance to {targets[0].name}.")
                else:
                    print(f"  > Everyone has Second Chance. Card discarded.") #TODO `else` here does not mean everyone has a second chance...

    def deal_card_to_player(self, player):
        card = self.deck.draw()
        if not card: 
            return # Deck empty edge case
        
        print(f"    {player.name} drew: {card}")

        if card.card_type == CardType.ACTION:
            # Action cards are resolved immediately (unless dealt during setup, handled separately)
            # In regular play, they are placed above rows[cite: 88], but effect triggers
            self.resolve_action_card(card, player, self.players)
            # Actions don't count for Flip 7 or Busts (except forcing logic)
            player.hand.append(card)

        elif card.card_type == CardType.MODIFIER:
            # [cite: 112] Modifiers don't cause bust
            player.hand.append(card)

        elif card.card_type == CardType.NUMBER:
            # Check for Bust [cite: 10]
            existing_nums = [c.value for c in player.hand if c.card_type == CardType.NUMBER]
            
            if card.value in existing_nums:
                if player.second_chance:
                    # [cite: 104] Discard duplicate and Second Chance
                    print(f"    ! SAVED BY SECOND CHANCE ! Discarding {card} and Second Chance token.")
                    player.second_chance = False
                    # Card is effectively discarded, not added to hand
                    #TODO: Is the second_chance card placed into the discard pile now? It should be.
                else:
                    print(f"    ! BUST ! {player.name} drew a duplicate {card.value}.")
                    player.busted = True
                    player.active = False
            else:
                player.hand.append(card)
                # Check Flip 7 Victory [cite: 9]
                if player.has_flip_seven():
                    return "FLIP7"

        return "OK"

    def play_round(self):
        print(f"\n--- Round {self.round_num} ---")
        for p in self.players:
            p.reset_round()
        
        # 1. Initial Deal (1 card each) [cite: 60]
        print("Dealing initial cards...")
        for i in range(len(self.players)):
            # Dealing order starting from dealer
            p_idx = (self.dealer_index + i) % len(self.players)
            player = self.players[p_idx]
            
            card = self.deck.draw()
            print(f"{player.name} starts with {card}")
            
            # If Action comes up in dealing, resolve immediately [cite: 61]
            if card.card_type == CardType.ACTION:
                self.resolve_action_card(card, player, self.players)
                player.hand.append(card)
            else:
                player.hand.append(card)

        # 2. Turns
        round_over = False
        winner_flip7 = None

        while not round_over:
            active_players = self.get_active_players()
            if not active_players:
                break # Everyone stayed or busted [cite: 127]

            for player in active_players:
                if not player.active: continue # Might have been frozen by previous player this loop

                # Check forced flips (Flip Three)
                action = "stay"
                if player.forced_flips > 0:
                    action = "hit"
                    player.forced_flips -= 1
                    print(f"{player.name} is forced to hit! ({player.forced_flips} remaining)")
                else:
                    opponents = [p for p in active_players if p != player]
                    action = player.decide_action(opponents)

                if action == "hit":
                    print(f"{player.name} HITS.")
                    result = self.deal_card_to_player(player)
                    
                    if result == "FLIP7":
                        # [cite: 135] Round ends immediately
                        print(f"!!! {player.name} ACHIEVED FLIP 7 !!!")
                        winner_flip7 = player
                        round_over = True
                        break
                else:
                    print(f"{player.name} STAYS.")
                    player.active = False # Safe for round

        # 3. End of Round Scoring
        print("\n--- Round Scores ---")
        
        # [cite: 183] Discard all cards at end of round
        current_round_cards = []
        
        for p in self.players:
            score = p.calculate_round_score()
            
            # If someone got Flip 7, they are the only ones getting that bonus
            # but everyone else keeps their points unless they busted?
            # Rule [cite: 9] says "automatically end the round for everyone".
            # Rule [cite: 135] says "One player can Flip 7... ending round immediately."
            # It implies others score what they have banked/on table.
            
            if p == winner_flip7:
                # Bonus already calculated in calculate_round_score if logic holds, 
                # but let's ensure the +15 is highlighted
                pass 

            p.total_game_score += score
            print(f"{p.name}: +{score} (Total: {p.total_game_score}) | Hand: {p.hand}")
            
            # Collect cards for discard
            current_round_cards.extend(p.hand)
        
        self.deck.discard_pile.extend(current_round_cards)
        
        # Rotate Dealer [cite: 184]
        self.dealer_index = (self.dealer_index + 1) % len(self.players)

# --- Run Simulation ---
if __name__ == "__main__":
    strategies = [
        Flip7ChaserStrategy(),
        ConservativeStrategy(stay_threshold=35),
        AggressiveStrategy(),
        Flip7ChaserStrategy(safe_score=45),
    ]
    game = Game(["Alice", "Bob", "Charlie", "Diana"], strategies=strategies)
    game.play_game()
