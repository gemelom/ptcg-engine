REWARD_WEIGHTS = {
    "energy_attached": 0.01,  # per energy attached
    "damage_dealt": 0.0005,  # per damage point
    "prize_cards_taken": 0.1,  # per prize card
    "pokemon_evolved": 0.05,  # per evolution
}


class Reward:
    """
    A class to handle per step reward-related logic for the Pokemon TCG environment.
    This centralizes reward calculation and tracking.
    """

    def __init__(self):
        self.weight = REWARD_WEIGHTS

        # Turn statistics for reward calculation
        self.energy_attached_count = 0
        self.damage_dealt = 0
        self.prize_cards_taken = 0
        self.pokemon_evolved_count = 0

    def clear(self):
        self.energy_attached_count = 0
        self.damage_dealt = 0
        self.prize_cards_taken = 0
        self.pokemon_evolved_count = 0

    def apply_energy_attached_reward(self, count):
        self.energy_attached_count += count

    def apply_damage_dealt_reward(self, damage):
        self.damage_dealt += damage

    def apply_prize_card_reward(self, count):
        self.prize_cards_taken += count

    def apply_pokemon_evolved_reward(self, count):
        self.pokemon_evolved_count += count

    def apply_penalty(self, penalty_value):
        """Apply a penalty for invalid actions"""
        self.penalty_reward = penalty_value
        return penalty_value

    def calculate_step_reward(self):
        """
        Calculate the reward for the current step based on actions taken
        and the game state.
        """
        reward = (
            self.weight["prize_cards_taken"] * self.prize_cards_taken
            + self.weight["damage_dealt"] * self.damage_dealt
            + self.weight["energy_attached"] * self.energy_attached_count
            + self.weight["pokemon_evolved"] * self.pokemon_evolved_count
        )

        return reward


penalty_reward = 0
