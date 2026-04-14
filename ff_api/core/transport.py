import asyncio
import aiohttp
from typing import Any, Dict, Optional, List
from ff_api.config.settings import settings
from ff_api.api.errors import FFError, ErrorCode

class AsyncTransport:
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()
        # Direct IP fallbacks for clientbp.ggblueshark.com
        self._ip_fallbacks = [
            "202.81.99.11", "202.81.99.12", "202.81.99.6", "202.81.99.15",
            "202.81.97.159", "202.81.97.165" # Also try loginbp IPs as sometimes they are co-located
        ]

    async def get_session(self) -> aiohttp.ClientSession:
        async with self._lock:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession(
                    headers={
                        "User-Agent": "Dalvik/2.1.0 (Linux; Android 9; SM-G960F Build/PPR1.180610.011)",
                        "X-Unity-Version": "2018.4.11f1",
                        "Accept-Encoding": "gzip",
                        "Connection": "Keep-Alive"
                    }
                )
            return self._session

    async def post(self, url: str, data: bytes, retry_count: int = 0) -> bytes:
        session = await self.get_session()

        # Aggressive headers for OB52
        headers = {
            "Content-Type": "application/octet-stream",
            "X-Release-Version": settings.OB_VERSION,
            "X-GA-Version": settings.OB_VERSION,
            "X-Unity-Version": "2018.4.11f1",
            "Host": "clientbp.ggblueshark.com"
        }

        current_url = url
        if retry_count > 0:
            # Alternate between URL patterns
            patterns = [
                "/api/v1/account",
                "/api/v1/account/info",
                "/api/v1/profile",
                "/api/v1/info"
            ]
            pattern = patterns[retry_count % len(patterns)]

            # Try IP fallback if DNS continues to fail or we get 503
            ip = self._ip_fallbacks[retry_count % len(self._ip_fallbacks)]
            base = f"https://{ip}"
            current_url = f"{base}{pattern}?region={url.split('region=')[-1] if 'region=' in url else 'IND'}"

        try:
            async with session.post(current_url, data=data, headers=headers, timeout=15, ssl=False) as response:
                if response.status == 200:
                    return await response.read()

                # If we get 503, it might be the wrong endpoint on the right server
                if response.status == 503 and retry_count < 8:
                    await asyncio.sleep(1)
                    return await self.post(url, data, retry_count + 1)

                if response.status == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    await asyncio.sleep(retry_after)
                    return await self.post(url, data, retry_count + 1)

                if response.status == 404:
                    # Maybe the endpoint path is wrong, try another pattern
                    if retry_count < len(patterns):
                        return await self.post(url, data, retry_count + 1)
                    raise FFError(ErrorCode.PLAYER_NOT_FOUND, "Player not found or endpoint invalid")

                if response.status >= 500 and retry_count < 10:
                    await asyncio.sleep(2)
                    return await self.post(url, data, retry_count + 1)

                raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Garena API returned status {response.status} at {current_url}")

        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            if retry_count < 10:
                await asyncio.sleep(1)
                return await self.post(url, data, retry_count + 1)
            raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Network error: {str(e)}")
        except Exception as e:
            if isinstance(e, FFError):
                raise e
            raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Unexpected error: {str(e)}")

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

transport = AsyncTransport()
