import time
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any

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

    key_lock = await cache.get_lock(uid, region)
    async with key_lock:
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

        # 3. DIRECT GARENA ATTEMPT
        try:
            # Try multiple protobuf structures
            for struct_type in ["standard", "nested", "integer"]:
                try:
                    proto_bytes = proto_handler.encode_request(uid, region, structure=struct_type)
                    encrypted_req = crypto.encrypt(proto_bytes)

                    # Try current known region URL
                    base_url = REGION_MAP.get(region)
                    url = f"{base_url}/api/v1/account?region={region}"

                    encrypted_res = await transport.post(url, encrypted_req)
                    player_data = decoder.decode(encrypted_res)

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
                except:
                    continue # Try next structure
        except:
            pass

        # 4. FALLBACK TO MIRROR
        try:
            raw_data = await transport.fetch_fallback(uid, region)
            # Map fallback data to PlayerData (Simplified Mapping)
            # Note: Fallback data might be from /player-stats, so we populate what we can

            # Helper to safely build StatLine from fallback
            def sl(src):
                if not src: return {"matches":0,"wins":0,"win_rate":"0%","kills":0,"deaths":0,"kd_ratio":0,"headshots":0,"headshot_rate":"0%","avg_damage_per_match":0,"booyahs":0}
                det = src.get("detailedstats", {})
                m = src.get("gamesplayed", 0)
                w = src.get("wins", 0)
                k = src.get("kills", 0)
                return {
                    "matches": m,
                    "wins": w,
                    "win_rate": f"{(w/m*100):.2f}%" if m else "0%",
                    "kills": k,
                    "deaths": det.get("deaths", 0),
                    "kd_ratio": round(k/max(det.get("deaths", 1), 1), 2),
                    "headshots": det.get("headshots", 0),
                    "headshot_rate": f"{(det.get('headshots', 0)/max(k, 1)*100):.2f}%" if k else "0%",
                    "avg_damage_per_match": round(det.get("damage", 0)/max(m, 1), 2),
                    "booyahs": w
                }

            mapped_data = {
                "account": {
                    "uid": uid,
                    "nickname": "Player_" + uid, # Fallback doesn't always provide name
                    "level": 0, "exp": 0, "region": region, "season_id": 0,
                    "preferred_mode": "Battle Royale", "language": "en",
                    "signature": "", "honor_score": 100, "total_likes": 0,
                    "ob_version": settings.OB_VERSION, "account_type": "Normal"
                },
                "rank": {
                    "battle_royale": {"points": 0, "visible": True},
                    "clash_squad": {"points": 0, "visible": True}
                },
                "stats": {
                    "battle_royale": {
                        "solo": sl(raw_data.get("solostats")),
                        "duo": sl(raw_data.get("duostats")),
                        "squad": sl(raw_data.get("quadstats"))
                    },
                    "clash_squad": {"ranked": {"matches":0,"wins":0,"win_rate":"0%","kills":0,"kd_ratio":0}}
                },
                "social": {"guild": None},
                "pet": None,
                "cosmetics": {"avatar_id": 0, "banner_id": 0, "pin_id": 0, "character_id": 0, "equipped_outfit_ids": [], "equipped_weapon_skin_ids": []},
                "pass": {"booyah_pass_level": 0, "fire_pass_status": "Basic", "fire_pass_badge_count": 0},
                "credit": {"score": 100, "reward_claimed": False},
                "ban": {"is_banned": False}
            }

            player_data = PlayerData.model_validate(mapped_data)
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
        except Exception as e:
            raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"All retrieval methods failed: {str(e)}")
