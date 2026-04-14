import time
import asyncio
from datetime import datetime, timezone
from typing import Optional

from ff_api.api.schemas import PlayerRequest, PlayerResponse, ResponseMetadata, PlayerData
from ff_api.api.errors import FFError, ErrorCode
from ff_api.config.regions import REGION_MAP
from ff_api.config.settings import settings
from ff_api.core.cache import cache
from ff_api.core.proto import proto_handler
from ff_api.core.crypto import crypto
from ff_api.core.transport import transport
from ff_api.core.decoder import decoder

async def fetch_player(uid: str, region: str) -> PlayerResponse:
    start_time = time.monotonic()

    # 1. Validate Input
    try:
        req = PlayerRequest(uid=uid, region=region)
        uid = req.uid
        region = req.region
    except Exception as e:
        raise FFError(ErrorCode.INVALID_UID, str(e))

    # 2. Check Cache
    cached_data = await cache.get(uid, region)
    if cached_data:
        return PlayerResponse(
            metadata=ResponseMetadata(
                request_uid=uid,
                request_region=region,
                fetched_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                response_time_ms=int((time.monotonic() - start_time) * 1000),
                api_version=settings.OB_VERSION,
                cache_hit=True
            ),
            data=PlayerData.model_validate(cached_data),
            error=None
        )

    # Use a per-key lock to prevent cache stampede
    key_lock = await cache.get_lock(uid, region)
    async with key_lock:
        # Check again in case another task filled the cache
        cached_data = await cache.get(uid, region)
        if cached_data:
            return PlayerResponse(
                metadata=ResponseMetadata(
                    request_uid=uid,
                    request_region=region,
                    fetched_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    response_time_ms=int((time.monotonic() - start_time) * 1000),
                    api_version=settings.OB_VERSION,
                    cache_hit=True
                ),
                data=PlayerData.model_validate(cached_data),
                error=None
            )

        try:
            # 3. Build region endpoint
            base_url = REGION_MAP.get(region)
            if not base_url:
                raise FFError(ErrorCode.INVALID_REGION, f"Region {region} is not supported")

            url = f"{base_url}/api/v1/account"

            # 4. Encode Request
            proto_bytes = proto_handler.encode_request(uid, region)

            # 5. Encrypt
            encrypted_req = crypto.encrypt(proto_bytes)

            # 6. POST to Garena
            encrypted_res = await transport.post(url, encrypted_req)

            # 7. Decode Response
            player_data = decoder.decode(encrypted_res)

            # 8. Cache result
            await cache.set(uid, region, player_data.model_dump())

            return PlayerResponse(
                metadata=ResponseMetadata(
                    request_uid=uid,
                    request_region=region,
                    fetched_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    response_time_ms=int((time.monotonic() - start_time) * 1000),
                    api_version=settings.OB_VERSION,
                    cache_hit=False
                ),
                data=player_data,
                error=None
            )

        except FFError as e:
            raise e
        except Exception as e:
            raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Orchestrator error: {str(e)}")
