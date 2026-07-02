from datenwissenschaften.gym import StateMachineGymWrapper

from src.game.actions import ACTION_TABLE
from src.ram.airstriker import AirstrikerRam
from src.states.survive import SurviveAndScore


class AirstrikerWrapper(StateMachineGymWrapper[AirstrikerRam]):
    ram_info_cls = AirstrikerRam
    start_state_cls = SurviveAndScore
    training_state_classes = (SurviveAndScore,)

    def __init__(self, env):
        super().__init__(env, obs_size=(96, 96), action_table=ACTION_TABLE)
