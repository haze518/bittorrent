import tracker
from torrentfile import parse_torrent_file


def test_get_peers(torrent_file_path, tracker_response_path, monkeypatch):
    
    def mock_request_data_from_tracker(*args, **kwargs):
        with open(tracker_response_path, 'rb') as file:
            return file.read()

    torrent_file = parse_torrent_file(torrent_file_path)
    with monkeypatch.context() as m:
        m.setattr(tracker, '_request_data_from_tracker', mock_request_data_from_tracker)
        data = tracker.get_peers(torrent_file)
        assert len(data) == 50
        assert isinstance(data[0], tracker.Peer)
