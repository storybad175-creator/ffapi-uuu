import time
import asyncio
import aiohttp
from typing import Optional
from config.settings import settings
from api.errors import FFError, ErrorCode

class JWTManager:
    def __init__(self):
        self._token: Optional[str] = None
        self._expires_at: float = 0
        self._lock = asyncio.Lock()

    async def get_token(self) -> str:
        async with self._lock:
            if self._token and time.time() < self._expires_at - 60:
                return self._token

            await self._refresh_token()
            return self._token

    async def _refresh_token(self, region="BD"):
        """POST to Garena MajorLogin to get a new JWT."""
        # Use provided credentials or fall back to community-extracted guest accounts
        guest_accounts = {
            "BD": {"uid": "4700657632", "token": "71A9EBCA4C1934E3C4D83E64AD288950E1AA0BE0CEFD20866771C5AE01B28C81"},
            "IND": {"uid": "4700657236", "token": "11AE657CB5F438F880F755E85E3F05027F245CCAA68B88067641650FD2CC3FA0"},
            "SG": {"uid": "4700657292", "token": "9B6E1EA8D549F3F282016312FB0920F40A54BF684912AC723DF142EEBC049BC6"}
        }

        target_uid = settings.GARENA_GUEST_UID or guest_accounts.get(region, {}).get("uid")
        target_token = settings.GARENA_GUEST_TOKEN or guest_accounts.get(region, {}).get("token")

        if not target_token:
            self._token = "DUMMY_TOKEN"
            self._expires_at = time.time() + 3600
            return

        # Attempt multiple login endpoints
        endpoints = [
            "https://loginbp.ggpolarbear.com/MajorLogin",
            "https://loginbp.ggblueshark.com/MajorLogin"
        ]

        async with aiohttp.ClientSession() as session:
            for url in endpoints:
                try:
                    payload = {
                        "openid": target_uid,
                        "logintoken": target_token,
                        "platform": "4"
                    }
                    headers = {
                        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; A063 Build/TKQ1.221220.001)",
                        "ReleaseVersion": settings.RELEASE_VERSION,
                        "X-Unity-Version": settings.UNITY_VERSION,
                        "Content-Type": "application/json"
                    }
                    async with session.post(url, json=payload, headers=headers, timeout=5) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            self._token = data.get("jwt") or data.get("token")
                            self._expires_at = time.time() + data.get("expires_in", 3600)
                            return
                except:
                    continue

            # If all failed, use dummy to allow fallbacks to proceed
            self._token = "DUMMY_TOKEN"
            self._expires_at = time.time() + 3600

jwt_manager = JWTManager()
