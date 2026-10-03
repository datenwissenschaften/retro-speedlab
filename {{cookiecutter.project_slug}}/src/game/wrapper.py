from datenwissenschaften.environment.wrapper import StateMachineGymWrapper

from src.game.actions import ACTION_DESCRIPTIONS, ACTION_TABLE
from src.ram.game import GameRam
from src.states.play import Play


class GameWrapper(StateMachineGymWrapper[GameRam]):
    start_state_cls = Play
    state_classes = (Play,)
    ram_info_cls = GameRam
    action_table = ACTION_TABLE
    action_descriptions = ACTION_DESCRIPTIONS
