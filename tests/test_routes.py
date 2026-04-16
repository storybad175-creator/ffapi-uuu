import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from main import app
from api.schemas import PlayerResponse

client = TestClient(app)

@pytest.mark.asyncio
async def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_regions_endpoint():
    response = client.get("/regions")
    assert response.status_code == 200
    assert "IND" in response.json()

@pytest.mark.asyncio
async def test_player_endpoint_invalid_uid():
    response = client.get("/player?uid=abc&region=IND")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_UID"

@patch("api.routes.fetch_player")
def test_player_endpoint_valid(mock_fetch):
    mock_fetch.return_value = AsyncMock() # Should return a PlayerResponse
    # Integration testing with real models
    from api.schemas import PlayerResponse, ResponseMetadata
    from datetime import datetime

    mock_res = PlayerResponse(
        metadata=ResponseMetadata(
            request_uid="12345678",
            request_region="IND",
            fetched_at=datetime.now().isoformat(),
            response_time_ms=100,
            api_version="OB52",
            cache_hit=False
        ),
        data=None, # Simplified
        error=None
    )
    mock_fetch.return_value = mock_res

    response = client.get("/player?uid=12345678&region=IND")
    assert response.status_code == 200
    assert response.json()["metadata"]["request_uid"] == "12345678"
