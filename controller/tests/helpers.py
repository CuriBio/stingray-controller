# -*- coding: utf-8 -*-
from random import choice
from random import randint


def random_semver():
    return f"{randint(0,1000)}.{randint(0,1000)}.{randint(0,1000)}"


def random_bool():
    return choice([True, False])
