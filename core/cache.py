import time
import asyncio
from typing import Dict, Optional, Any, Tuple
from config.settings import settings

class TTLCache:
    def __init__(self):
        self._store: Dict[Tuple[str, str], Tuple[Dict[str, Any], float]] = {}
        self._lock = asyncio.Lock()
        self._key_locks: Dict[Tuple[str, str], asyncio.Lock] = {}

    async def get_lock(self, uid: str, region: str) -> asyncio.Lock:
        async with self._lock:
            key = (uid, region)
            if key not in self._key_locks:
                self._key_locks[key] = asyncio.Lock()
            return self._key_locks[key]

    async def get(self, uid: str, region: str) -> Optional[Dict[str, Any]]:
        key = (uid, region)
        async with self._lock:
            if key in self._store:
                data, expires_at = self._store[key]
                if time.time() < expires_at:
                    return data
                else:
                    del self._store[key]
        return None

    async def set(self, uid: str, region: str, data: Dict[str, Any]):
        key = (uid, region)
        async with self._lock:
            # Eviction logic
            if len(self._store) >= settings.CACHE_MAX_ENTRIES:
                # Remove 50 oldest entries
                sorted_entries = sorted(self._store.items(), key=lambda item: item[1][1])
                for k, _ in sorted_entries[:50]:
                    del self._store[k]
                    if k in self._key_locks:
                        del self._key_locks[k]

            self._store[key] = (data, time.time() + settings.CACHE_TTL_SECONDS)

cache = TTLCache()
