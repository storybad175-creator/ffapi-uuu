import pytest
from unittest.mock import AsyncMock, patch
from ff_api.core.auth import JWTManager
from ff_api.api.errors import FFError

@pytest.mark.asyncio
async def test_token_fetch(mock_settings):
    manager = JWTManager()

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_res = AsyncMock()
        mock_res.status = 200
        mock_res.json.return_value = {"jwt": "fake_token", "expires_in": 3600}
        mock_post.return_value.__aenter__.return_value = mock_res

        token = await manager.get_token()
        assert token == "fake_token"
        assert manager._token == "fake_token"

@pytest.mark.asyncio
async def test_token_refresh_on_expiry(mock_settings):
    manager = JWTManager()
    manager._token = "old_token"
    manager._expires_at = 0 # Expired

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_res = AsyncMock()
        mock_res.status = 200
        mock_res.json.return_value = {"jwt": "new_token", "expires_in": 3600}
        mock_post.return_value.__aenter__.return_value = mock_res

        token = await manager.get_token()
        assert token == "new_token"
