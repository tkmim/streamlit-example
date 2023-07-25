from pathlib import Path
import pickle


class Cache:
    def __init__(self, file_path: Path):
        self.file_path: Path = file_path
        if self.file_path.exists():
            self.from_file()
        else:
            self.raw_data = {}
            self.probabilities = {}
            self.figures = {}

    def from_file(self):
        with self.file_path.open("rb") as f:
            _cache: Cache
            _cache = pickle.load(f)
            self.raw_data = _cache.raw_data
            self.probabilities = _cache.probabilities
            self.figures = _cache.figures

    def save_cache(self):
        with self.file_path.open("wb") as f:
            pickle.dump(self, f)
