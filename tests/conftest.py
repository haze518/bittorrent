import pytest
import os


@pytest.fixture
def torrent_file_path():
    return os.getcwd() + '/tests/data/debian-10.9.0-amd64-netinst.iso.torrent'


@pytest.fixture
def tracker_response_path():
    return os.getcwd() + '/tests/data/tracker_response.txt'
