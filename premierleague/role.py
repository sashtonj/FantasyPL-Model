from enum import Enum


class Role(Enum):
    GK = 1
    DF = 2
    MF = 3
    FW = 4

    def __lt__(self, other):
        return self.value < other.value
