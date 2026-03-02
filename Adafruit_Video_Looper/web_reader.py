import os

class WebReader:
    """File reader that watches a local directory for videos that have been
    uploaded via the web interface.  Detects additions and deletions so the
    VideoLooper rebuilds its playlist automatically.
    """

    def __init__(self, config):
        self._load_config(config)
        os.makedirs(self._path, exist_ok=True)
        self._state = self._snapshot()

    def _load_config(self, config):
        self._path = config.get('web_reader', 'path')

    def _snapshot(self):
        """Return a sorted list of filenames currently in the directory."""
        try:
            return sorted(os.listdir(self._path))
        except FileNotFoundError:
            return []

    def search_paths(self):
        """Return the list of directories to search for video files."""
        return [self._path]

    def is_changed(self):
        """Return True if files in the directory have been added or removed
        since the last call to this method.
        """
        current = self._snapshot()
        if current != self._state:
            self._state = current
            return True
        return False

    def idle_message(self):
        """Message shown when no videos are in the upload directory."""
        return 'No videos uploaded. Please use the web interface at port 5000.'


def create_file_reader(config, screen):
    """Factory function required by the VideoLooper plugin architecture."""
    return WebReader(config)
