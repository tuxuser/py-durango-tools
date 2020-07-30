"""
Test fixtures
"""

import os
import pytest
from typing import Mapping, Dict


@pytest.fixture(scope='session')
def json_testdata() -> Mapping[str, str]:
    """
    Provides json testdata to test methods

    Returns:
        A Mapping/Dictionary of (filename -> content as string).
    """
    data: Dict[str, str] = {}
    data_path = os.path.join(os.path.dirname(__file__), 'testdata', 'json')
    for f in os.listdir(data_path):
        with open(os.path.join(data_path, f), 'rt') as fh:
            data[f] = fh.read()
    return data


@pytest.fixture(scope='session')
def misc_testdata() -> Mapping[str, bytes]:
    """
    Provides misc binary testdata to test methods

    Returns:
        A Mapping/Dictionary of (filename -> content as bytes).
    """
    data: Dict[str, bytes] = {}
    data_path = os.path.join(os.path.dirname(__file__), 'testdata', 'misc')
    for f in os.listdir(data_path):
        with open(os.path.join(data_path, f), 'rb') as fh:
            data[f] = fh.read()
    return data
