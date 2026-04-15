import asyncio
import aiohttp
import random
from typing import Any, Dict, Optional, List
from ff_api.config.settings import settings
from ff_api.api.errors import FFError, ErrorCode

class AsyncTransport:
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()
        self._garena_ips = ["202.81.109.65", "202.81.99.11", "202.81.97.159"]

    async def get_session(self) -> aiohttp.ClientSession:
        async with self._lock:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession()
            return self._session

    async def post(self, url: str, data: bytes, retry_count: int = 0) -> bytes:
        session = await self.get_session()
        headers = {
            "Content-Type": "application/x-protobuf",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11) GarenaFreeFire/1.103.1",
            "X-GA-Version": settings.OB_VERSION,
            "Host": "clientbp.ggblueshark.com",
            "Connection": "close"
        }

        ip = self._garena_ips[retry_count % len(self._garena_ips)]
        region = url.split("region=")[-1] if "region=" in url else "IND"
        current_url = f"https://{ip}/api/v1/account?region={region}"

        try:
            async with session.post(current_url, data=data, headers=headers, timeout=5, ssl=False) as response:
                if response.status == 200:
                    return await response.read()
                if retry_count < 3:
                    return await self.post(url, data, retry_count + 1)
                raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Direct failed: {response.status}")
        except:
            if retry_count < 3:
                return await self.post(url, data, retry_count + 1)
            raise FFError(ErrorCode.SERVICE_UNAVAILABLE, "Direct failed")

    async def fetch_fallback(self, uid: str, region: str) -> Dict[str, Any]:
        session = await self.get_session()
        url = f"https://freefireinfo-zy9l.onrender.com/api/v1/player-stats?uid={uid}&server={region}&gamemode=br&matchmode=CAREER"
        async with session.get(url, timeout=10) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("success"):
                    return data.get("data")
        raise FFError(ErrorCode.PLAYER_NOT_FOUND, "Mirror failed")

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

transport = AsyncTransport()
