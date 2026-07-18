from aiogram.fsm.state import State, StatesGroup


class SearchStates(StatesGroup):
    waiting_query = State()


class PlaylistStates(StatesGroup):
    waiting_name = State()
    waiting_rename = State()


class BroadcastStates(StatesGroup):
    waiting_message = State()
