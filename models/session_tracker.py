import threading
import time
from typing import Dict


class SessionTracker:
    def __init__(self, ttl_seconds: int = 30):
        self.ttl_seconds = ttl_seconds
        self._sessions: Dict[str, float] = {}
        self._lock = threading.Lock()

    def heartbeat(self, client_id: str) -> int:
        now = time.time()
        with self._lock:
            self._sessions[client_id] = now
            self._cleanup(now)
            return len(self._sessions)

    def active_count(self) -> int:
        with self._lock:
            self._cleanup(time.time())
            return len(self._sessions)

    def _cleanup(self, now: float) -> None:
        expired = [client_id for client_id, ts in self._sessions.items() if now - ts > self.ttl_seconds]
        for client_id in expired:
            self._sessions.pop(client_id, None)
