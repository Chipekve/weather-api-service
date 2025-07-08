from aiogram.fsm.state import State, StatesGroup
 
class CitySelectStates(StatesGroup):
    waiting_for_city_name = State()
    waiting_for_city_choice = State() 