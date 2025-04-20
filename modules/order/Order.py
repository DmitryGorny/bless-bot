from abc import ABC, abstractmethod


class Order:
    def __init__(self):
        self._positions = []
        self._photo = []

    @property
    def positions(self) -> list:
        return self._positions

    def add_position(self, position:str) -> None:
        self._positions.append(position)

    @property
    def photo(self) -> list:
        return self._photo

    def add_photo(self, photo:str):
        self._photo.append(photo)


class IOrderBuilder(ABC):
    @abstractmethod
    def add_position(self, position:str) -> None:
        pass

    @abstractmethod
    def add_photo(self, photo) -> None:
        pass

class OrderBuilder(IOrderBuilder):
    def __init__(self):
        self._order = Order()

    @property
    def order(self) -> Order:
        return self._order

    @order.setter
    def order(self, orderObj:Order) -> None:
        self._order = orderObj

    def add_position(self, position:str) -> None:
        self._order.add_position(position)
    @property
    def photo(self) -> list:
        return self.photo
    def add_photo(self, photo:str) -> None:
        self._order.add_photo(photo)
