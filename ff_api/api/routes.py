import asyncio
import time
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException

from ff_api.api.schemas import PlayerResponse, PlayerRequest, ResponseMetadata, ErrorDetail
from ff_api.core.fetcher import fetch_player
from ff_api.config.regions import REGION_MAP
from ff_api.config.settings import settings
from ff_api.api.errors import FFError, ErrorCode

router = APIRouter()

@router.get("/player", response_model=PlayerResponse)
async def get_player(
    uid: str = Query(..., description="Free Fire Player UID"),
    region: str = Query(..., description="Region code (e.g. IND, BR)")
):
    return await fetch_player(uid, region)

@router.get("/batch", response_model=List[PlayerResponse])
async def batch_fetch(
    uids: str = Query(..., description="Comma-separated UIDs"),
    region: str = Query(..., description="Region code")
):
    uid_list = [u.strip() for u in uids.split(",") if u.strip()][:10]

    async def safe_fetch(uid: str, region: str) -> PlayerResponse:
        try:
            return await fetch_player(uid, region)
        except FFError as e:
            return PlayerResponse(
                metadata=ResponseMetadata(
                    request_uid=uid,
                    request_region=region,
                    fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    response_time_ms=0,
                    api_version=settings.OB_VERSION,
                    cache_hit=False
                ),
                data=None,
                error=ErrorDetail(
                    code=e.code,
                    message=e.message,
                    retryable=e.retryable,
                    extra=e.extra
                )
            )
        except Exception as e:
            return PlayerResponse(
                metadata=ResponseMetadata(
                    request_uid=uid,
                    request_region=region,
                    fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    response_time_ms=0,
                    api_version=settings.OB_VERSION,
                    cache_hit=False
                ),
                data=None,
                error=ErrorDetail(
                    code=ErrorCode.SERVICE_UNAVAILABLE,
                    message=f"Batch error: {str(e)}",
                    retryable=False
                )
            )

    tasks = [safe_fetch(uid, region) for uid in uid_list]
    return await asyncio.gather(*tasks)

@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "ob_version": settings.OB_VERSION,
        "uptime": int(time.time() - getattr(router, "_start_time", time.time()))
    }

@router.get("/regions")
async def get_regions():
    return list(REGION_MAP.keys())

# Set start time on router for health check
router._start_time = time.time()
