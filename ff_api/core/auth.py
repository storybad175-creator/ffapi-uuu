import time
import asyncio
import aiohttp
from typing import Optional
from ff_api.config.settings import settings
from ff_api.api.errors import FFError, ErrorCode

class JWTManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JWTManager, cls).__new__(cls)
            cls._instance._token = None
            cls._instance._expires_at = 0
            cls._instance._lock = asyncio.Lock()
        return cls._instance

    async def get_token(self) -> str:
        async with self._lock:
            if self._token and time.time() < self._expires_at - 60:
                return self._token

            await self.refresh()
            return self._token

    async def refresh(self):
        url = "https://loginbp.ggblueshark.com/MajorLogin"
        payload = {
            "uid": settings.GARENA_GUEST_UID,
            "token": settings.GARENA_GUEST_TOKEN,
            "login_type": "guest"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as response:
                    if response.status != 200:
                        raise FFError(
                            ErrorCode.AUTH_FAILED,
                            "Failed to authenticate with Garena MajorLogin"
                        )

                    data = await response.json()
                    self._token = data.get("jwt")
                    # Assume token is valid for 1 hour if expiry not provided
                    expires_in = data.get("expires_in", 3600)
                    self._expires_at = time.time() + expires_in

                    if not self._token:
                        raise FFError(
                            ErrorCode.AUTH_FAILED,
                            "Garena MajorLogin response missing JWT"
                        )
        except Exception as e:
            if isinstance(e, FFError):
                raise e
            raise FFError(
                ErrorCode.AUTH_FAILED,
                f"Authentication request failed: {str(e)}"
            )

jwt_manager = JWTManager()
