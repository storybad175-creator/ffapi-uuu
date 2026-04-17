import asyncio
import aiohttp
import random
from typing import Any, Dict, Optional, List
from config.settings import settings
from api.errors import FFError, ErrorCode
from core.auth import jwt_manager

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

    async def post(self, url: str, data: bytes, retry_count: int = 0, host: Optional[str] = None) -> bytes:
        session = await self.get_session()
        token = await jwt_manager.get_token()

        # Production headers for OB53
        headers = {
            "User-Agent": "UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
            "Accept": "*/*",
            "Accept-Encoding": "deflate, gzip",
            "Authorization": f"Bearer {token}",
            "X-GA": "v1 1",
            "ReleaseVersion": settings.RELEASE_VERSION,
            "X-Unity-Version": settings.UNITY_VERSION,
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": host or "clientbp.ggblueshark.com",
            "Connection": "close"
        }

        # IP rotation for high availability
        ip = self._garena_ips[retry_count % len(self._garena_ips)]

        # Build direct URL
        if "api/v1/account" in url:
            region = url.split("region=")[-1] if "region=" in url else "IND"
            target_url = f"https://{ip}/api/v1/account?region={region}"
        else:
            # For specific endpoints like GetPlayerPersonalShow
            endpoint = url.split("/")[-1]
            target_url = f"https://{ip}/{endpoint}"

        try:
            async with session.post(target_url, data=data, headers=headers, timeout=5, ssl=False) as response:
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
        """Fetch from community mirror as fallback."""
        session = await self.get_session()

        # 1. Fetch Profile (Name, Level, etc)
        profile_url = f"https://freefireinfo-zy9l.onrender.com/api/v1/player-profile?uid={uid}&server={region}"
        # 2. Fetch BR Stats
        br_stats_url = f"https://freefireinfo-zy9l.onrender.com/api/v1/player-stats?uid={uid}&server={region}&gamemode=br&matchmode=CAREER"
        # 3. Fetch CS Stats
        cs_stats_url = f"https://freefireinfo-zy9l.onrender.com/api/v1/player-stats?uid={uid}&server={region}&gamemode=cs&matchmode=CAREER"

        combined_data = {}

        # Parallel fetch for speed
        async def safe_get(u):
            try:
                async with session.get(u, timeout=10) as r:
                    if r.status == 200: return await r.json()
            except: pass
            return None

        profile_json, br_json, cs_json = await asyncio.gather(
            safe_get(profile_url),
            safe_get(br_stats_url),
            safe_get(cs_stats_url)
        )

        if isinstance(profile_json, dict):
            combined_data.update(profile_json)

        combined_data["br_stats"] = br_json.get("data") if br_json and br_json.get("success") else None
        combined_data["cs_stats"] = cs_json.get("data") if cs_json and cs_json.get("success") else None

        if not combined_data:
            raise FFError(ErrorCode.PLAYER_NOT_FOUND, "Mirror failed to retrieve any data")

        return combined_data

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

transport = AsyncTransport()
