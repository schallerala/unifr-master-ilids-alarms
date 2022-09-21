"""From Stackoverflow answer: https://stackoverflow.com/a/54919285/3771148"""
from enum import Enum


class ExtendedEnum(Enum):
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))
