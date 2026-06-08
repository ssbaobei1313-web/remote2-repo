# Minimal, well-documented ProxyPool implementation for unit testing.
# Place at src/proxy_pool/proxy_pool.py

from collections import deque
from typing import Deque, Dict, Optional, Iterable


class ProxyPool:
    """
    Simple proxy pool with round-robin retrieval and basic bad-proxy handling.
    - add(proxy: str): add a proxy string (e.g., "http://1.2.3.4:8080")
    - get() -> Optional[str]: get next healthy proxy or None if none available
    - mark_bad(proxy: str): mark a proxy as bad (removed from rotation)
    - remove(proxy: str): remove proxy if present
    - size() -> int: number of healthy proxies
    - all_proxies() -> list[str]: list of all healthy proxies in rotation order
    """

    def __init__(self, proxies: Optional[Iterable[str]] = None):
        self._queue: Deque[str] = deque()
        self._bad: Dict[str, bool] = {}
        if proxies:
            for p in proxies:
                self.add(p)

    def add(self, proxy: str) -> None:
        if proxy in self._bad:
            # previously marked bad; unmark and re-add
            del self._bad[proxy]
        if proxy not in self._queue:
            self._queue.append(proxy)

    def get(self) -> Optional[str]:
        if not self._queue:
            return None
        # round-robin: pop left, append right, return value
        proxy = self._queue.popleft()
        self._queue.append(proxy)
        return proxy

    def mark_bad(self, proxy: str) -> None:
        # mark as bad and remove from queue if present
        self._bad[proxy] = True
        try:
            self._queue.remove(proxy)
        except ValueError:
            pass

    def remove(self, proxy: str) -> None:
        try:
            self._queue.remove(proxy)
        except ValueError:
            pass
        self._bad.pop(proxy, None)

    def size(self) -> int:
        return len(self._queue)

    def all_proxies(self) -> list:
        return list(self._queue)

    def clear(self) -> None:
        self._queue.clear()
        self._bad.clear()
