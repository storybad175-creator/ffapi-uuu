import asyncio
import aiohttp
from typing import Any, Dict, Optional
from ff_api.config.settings import settings
from ff_api.api.errors import FFError, ErrorCode
from ff_api.core.auth import jwt_manager

class AsyncTransport:
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()

    async def get_session(self) -> aiohttp.ClientSession:
        async with self._lock:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession(
                    headers={
                        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12; Pixel 6 Build/SD1A.210817.036)",
                        "X-Unity-Version": "2021.3.11f1",
                        "Accept-Encoding": "gzip",
                        "Connection": "Keep-Alive"
                    }
                )
            return self._session

    async def post(self, url: str, data: bytes, retry_count: int = 0) -> bytes:
        session = await self.get_session()
        token = await jwt_manager.get_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-protobuf",
            "X-GA-Version": settings.OB_VERSION
        }

        try:
            async with session.post(url, data=data, headers=headers, timeout=12) as response:
                if response.status == 200:
                    return await response.read()

                if response.status == 401 and retry_count < 1:
                    await jwt_manager.refresh()
                    return await self.post(url, data, retry_count + 1)

                if response.status == 429:
                    retry_after = int(response.headers.get("Retry-After", 10))
                    if retry_count < 2:
                        await asyncio.sleep(retry_after)
                        return await self.post(url, data, retry_count + 1)
                    raise FFError(ErrorCode.RATE_LIMITED, "Rate limit exceeded", extra={"retry_after": retry_after})

                if response.status == 404:
                    raise FFError(ErrorCode.PLAYER_NOT_FOUND, "Player not found in this region")

                if response.status >= 500 and retry_count < 3:
                    backoff = [1, 3, 7][retry_count]
                    await asyncio.sleep(backoff)
                    return await self.post(url, data, retry_count + 1)

                raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Garena API returned status {response.status}")

        except asyncio.TimeoutError:
            if retry_count < 3:
                backoff = [1, 3, 7][retry_count]
                await asyncio.sleep(backoff)
                return await self.post(url, data, retry_count + 1)
            raise FFError(ErrorCode.TIMEOUT, "Request timed out after multiple retries")
        except aiohttp.ClientError as e:
            raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Network error: {str(e)}")
        except Exception as e:
            if isinstance(e, FFError):
                raise e
            raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Unexpected transport error: {str(e)}")

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

transport = AsyncTransport()
