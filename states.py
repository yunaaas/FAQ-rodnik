from aiogram.dispatcher.filters.state import State, StatesGroup

class UserStates(StatesGroup):
    asking_question = State()  # Состояние, когда пользователь задает свой вопрос
    offer_post = State() # Предложка