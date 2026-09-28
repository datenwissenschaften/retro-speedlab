from datenwissenschaften.environment.wrapper import StateMachineGymWrapper

from src.game.actions import ACTION_DESCRIPTIONS, ACTION_TABLE
from src.ram.airstriker import AirstrikerRam
from src.states.survive import SurviveAndScore


class AirstrikerWrapper(StateMachineGymWrapper[AirstrikerRam]):
    start_state_cls = SurviveAndScore
    state_classes = (SurviveAndScore,)
    ram_info_cls = AirstrikerRam
    action_table = ACTION_TABLE
    action_descriptions = ACTION_DESCRIPTIONS
