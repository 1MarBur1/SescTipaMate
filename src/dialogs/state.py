from aiogram.dispatcher.filters.state import StatesGroup, State


class MutableStatesGroupMeta(type(StatesGroup)):
    def __new__(cls, name, bases, namespace, **kwargs):
        cls = super().__new__(cls, name, bases, namespace)

        cls._states = list(cls._states)

        # Not necessary as long as it is redundant variable
        # cls._state_names = list(cls._state_names)

        return cls


class MutableStatesGroup(StatesGroup, metaclass=MutableStatesGroupMeta):
    @classmethod
    def register(cls, state: State):
        cls.states.append(state)
        state.set_parent(cls)
        return state

