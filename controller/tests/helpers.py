# -*- coding: utf-8 -*-
from random import choice
from random import randint

from controller.constants import NUM_WELLS

TEST_PLATE_BARCODE = "ML22001000-2"
TEST_STIM_BARCODE = "MS22001000-2"


def random_semver():
    return f"{randint(0,1000)}.{randint(0,1000)}.{randint(0,1000)}"


def random_bool():
    return choice([True, False])


def random_well_idx():
    return randint(0, NUM_WELLS - 1)
