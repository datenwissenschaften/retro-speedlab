from datenwissenschaften.states.state import State

from src.ram.airstriker import AirstrikerRam


class SurviveAndScore(State[AirstrikerRam]):
    """Reward scoring, survival, and preserving lives during an Airstriker run."""

    description = "Survive for as long as possible while increasing the score."
    progress = 0

    maximum_episode_steps = 18_000
    survival_reward = 0.01
    lost_life_penalty = 100.0
    game_over_penalty = 500.0

    previous_score: int
    previous_lives: int
    elapsed_steps: int
    life_lost: bool

    def _on_reset(self) -> None:
        self.previous_score = self.ram.score
        self.previous_lives = self.ram.lives
        self.elapsed_steps = 0
        self.life_lost = False

    def _reward(self) -> float:
        self.elapsed_steps += 1

        score_delta = max(0, self.ram.score - self.previous_score)
        lives_lost = max(0, self.previous_lives - self.ram.lives)
        self.life_lost = lives_lost > 0

        reward = float(score_delta) + self.survival_reward
        reward -= lives_lost * self.lost_life_penalty
        if self.ram.game_over:
            reward -= self.game_over_penalty

        self.previous_score = self.ram.score
        self.previous_lives = self.ram.lives
        return reward

    def _terminated(self) -> bool:
        return self.ram.game_over or self.life_lost

    def _truncated(self) -> bool:
        return self.elapsed_steps >= self.maximum_episode_steps

    def _won(self) -> bool:
        return self.ram.score >= 1000
