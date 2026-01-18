from threading import Lock

class CountryConfig:
    def __init__(self):
        self._lock = Lock()
        self._country = "IN"

    def set(self, code: str):
        with self._lock:
            self._country = code.upper()

    def get(self) -> str:
        with self._lock:
            return self._country


COUNTRY_CONFIG = CountryConfig()
