# -*- coding: utf-8 -*-
from controller.utils import aio
import pytest


@pytest.fixture(scope="function", name="patch_wait_tasks_clean")
def fixture__wait_tasks_clean(mocker):
    yield mocker.patch.object(aio, "wait_tasks_clean", autospec=True, return_value=None)


@pytest.fixture(scope="function", name="patch_clean_up_tasks")
def fixture__clean_up_tasks(mocker):
    yield mocker.patch.object(aio, "clean_up_tasks", autospec=True, return_value=None)
