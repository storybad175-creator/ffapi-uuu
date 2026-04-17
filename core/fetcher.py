import time
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from api.schemas import PlayerRequest, PlayerResponse, ResponseMetadata, PlayerData
from api.errors import FFError, ErrorCode
from config.regions import REGION_MAP
from config.settings import settings
from core.cache import cache
from core.proto import proto_handler
from core.crypto import crypto
from core.transport import transport
from core.decoder import decoder

async def fetch_player(uid: str, region: Optional[str] = None) -> PlayerResponse:
    start_time = time.monotonic()

    # Priority regions for auto-detection
    # User is BD, so we prioritize BD then SG (same infrastructure)
    if region and region.upper() == "BD":
        regions_to_check = ["BD", "SG", "IND"]
    elif region:
        regions_to_check = [region.upper()]
    else:
        # Bangladesh is priority 1
        regions_to_check = ["BD", "IND", "SG", "BR", "ID", "US", "RU", "TH", "VN"]

    for current_region in regions_to_check:
        # Check Cache (only if not forcing deep search)
        cached_data = await cache.get(uid, current_region) if region else None
        if cached_data:
            return PlayerResponse(
                metadata=ResponseMetadata(
                    request_uid=uid, request_region=current_region,
                    fetched_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    response_time_ms=int((time.monotonic() - start_time) * 1000),
                    api_version=settings.OB_VERSION, cache_hit=True
                ),
                data=PlayerData.model_validate(cached_data),
                error=None
            )

        key_lock = await cache.get_lock(uid, current_region)
        async with key_lock:
            # 1. DIRECT GARENA ATTEMPT (Production Endpoints)
            direct_success = False

            # Map region to specific production hostnames
            host_map = {
                "IND": "client.ind.freefiremobile.com",
                "BD": "client.ind.freefiremobile.com", # BD often uses IND infrastructure
                "SG": "client.sg.freefiremobile.com",
            }
            target_host = host_map.get(current_region, "clientbp.ggblueshark.com")

            # Try GetPlayerPersonalShow (Detailed) and GetPlayerStats
            variants = ["production", "standard", "nested", "legacy", "extended"]
            cmd_ids = [1001, 2001, 3001]

            for variant in variants:
                for cmd_id in (cmd_ids if variant == "nested" else [None]):
                    try:
                        proto_bytes = proto_handler.encode_request(uid, current_region, variant=variant, cmd_id=cmd_id)
                        encrypted_req = crypto.encrypt(proto_bytes)

                        # Try GetPlayerPersonalShow for profile info
                        endpoint = "GetPlayerPersonalShow" if variant == "production" else "api/v1/account"
                        url = f"https://{target_host}/{endpoint}"
                        encrypted_res = await transport.post(url, encrypted_req, host=target_host)
                        player_data = decoder.decode(encrypted_res)

                        # Verify "live" data
                        if player_data.account.level >= 55:
                            direct_success = True
                            break
                    except Exception:
                        continue
                if direct_success:
                    break

            if direct_success:
                await cache.set(uid, current_region, player_data.model_dump())
                return PlayerResponse(
                    metadata=ResponseMetadata(
                        request_uid=uid, request_region=current_region,
                        fetched_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                        response_time_ms=int((time.monotonic() - start_time) * 1000),
                        api_version=settings.OB_VERSION, cache_hit=False
                    ),
                    data=player_data,
                    error=None
                )

            # 2. SMART FALLBACK (Mirror Recovery)
            try:
                raw_data = await transport.fetch_fallback(uid, current_region)

                profile = raw_data.get("basicinfo", {})
                br_stats = raw_data.get("br_stats", {})
                cs_stats = raw_data.get("cs_stats", {})
                social = raw_data.get("socialinfo", {})
                clan = raw_data.get("clanbasicinfo", {})
                pet = raw_data.get("petinfo", {})

                # Check if we got any real stats or a real profile
                has_stats = any(s.get("gamesplayed", 0) > 0 for s in [
                    br_stats.get("solostats", {}),
                    br_stats.get("duostats", {}),
                    br_stats.get("quadstats", {}),
                    cs_stats.get("csstats", {})
                ])
                has_profile = bool(profile.get("nickname"))

                # If we got shallow/empty data, try the next region in the detection loop
                if not has_stats and not has_profile:
                    continue

                # Check for "live" indicators if user requested
                # If level is lower than known (59), we might want to keep searching other mirrors
                # but for now we accept the best available.

                def format_epoch(epoch: Optional[int]) -> Optional[str]:
                    if not epoch: return None
                    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat().replace("+00:00", "Z")

                def sl(src):
                    if not src: return {"matches":0,"wins":0,"win_rate":"0%","kills":0,"deaths":0,"kd_ratio":0,"headshots":0,"headshot_rate":"0%","avg_damage_per_match":0,"booyahs":0}
                    det = src.get("detailedstats", {})
                    m = src.get("gamesplayed", 0)
                    w = src.get("wins", 0)
                    k = src.get("kills", 0)
                    d = det.get("deaths", 0)
                    return {
                        "matches": m, "wins": w,
                        "win_rate": f"{(w/max(m,1)*100):.2f}%",
                        "kills": k, "deaths": d,
                        "kd_ratio": round(k/max(d, 1), 2),
                        "headshots": det.get("headshots", 0),
                        "headshot_rate": f"{(det.get('headshots', 0)/max(k, 1)*100):.2f}%",
                        "avg_damage_per_match": round(det.get("damage", 0)/max(m, 1), 2),
                        "booyahs": w
                    }

                nickname = profile.get("nickname") or f"Player_{uid}"
                level = profile.get("level") or 0
                exp = profile.get("exp") or 0

                mapped_data = {
                    "account": {
                        "uid": uid, "nickname": nickname, "level": level, "exp": exp,
                        "region": profile.get("region", current_region),
                        "season_id": profile.get("seasonid", 0),
                        "preferred_mode": "Battle Royale", "language": social.get("language", "English"),
                        "signature": social.get("signature", ""),
                        "honor_score": 100,
                        "total_likes": profile.get("liked", 0),
                        "ob_version": settings.OB_VERSION, "account_type": "Normal",
                        "created_at_epoch": int(profile.get("createat", 0)) if profile.get("createat") else None,
                        "created_at": format_epoch(int(profile.get("createat"))) if profile.get("createat") else None,
                        "last_login_epoch": int(profile.get("lastloginat", 0)) if profile.get("lastloginat") else None,
                        "last_login": format_epoch(int(profile.get("lastloginat"))) if profile.get("lastloginat") else None,
                    },
                    "rank": {
                        "battle_royale": {
                            "points": profile.get("rankingpoints", 0),
                            "rank_code": profile.get("rank", 0),
                            "max_rank_code": profile.get("maxrank", 0),
                            "visible": True
                        },
                        "clash_squad": {
                            "points": profile.get("csrankingpoints", 0),
                            "rank_code": profile.get("csrank", 0),
                            "visible": True
                        }
                    },
                    "stats": {
                        "battle_royale": {
                            "solo": sl(br_stats.get("solostats")),
                            "duo": sl(br_stats.get("duostats")),
                            "squad": sl(br_stats.get("quadstats"))
                        },
                        "clash_squad": {
                            "ranked": {
                                "matches": cs_stats.get("csstats", {}).get("gamesplayed", 0),
                                "wins": cs_stats.get("csstats", {}).get("wins", 0),
                                "win_rate": f"{(cs_stats.get('csstats', {}).get('wins', 0)/max(cs_stats.get('csstats', {}).get('gamesplayed', 1), 1)*100):.2f}%",
                                "kills": cs_stats.get("csstats", {}).get("kills", 0),
                                "kd_ratio": round(cs_stats.get("csstats", {}).get("kills", 0)/max(cs_stats.get("csstats", {}).get("detailedstats", {}).get("deaths", 1), 1), 2)
                            }
                        }
                    },
                    "social": {
                        "guild": {
                            "id": clan.get("clanid"),
                            "name": clan.get("clanname"),
                            "level": clan.get("clanlevel", 0),
                            "member_count": clan.get("membernum", 0),
                            "capacity": clan.get("capacity", 0),
                            "leader": {
                                "uid": clan.get("captainid") or "0",
                                "nickname": "Leader",
                                "level": 0
                            }
                        } if clan.get("clanid") else None
                    },
                    "pet": {
                        "name": str(pet.get("id", "Pet")),
                        "level": pet.get("level", 0),
                        "exp": pet.get("exp", 0),
                        "skin_id": pet.get("skinid", 0),
                        "is_selected": pet.get("isselected", False)
                    } if pet.get("id") else None,
                    "cosmetics": {"avatar_id": 0, "banner_id": 0, "pin_id": 0, "character_id": 0, "equipped_outfit_ids": [], "equipped_weapon_skin_ids": []},
                    "pass_info": {"booyah_pass_level": 0, "fire_pass_status": "Basic", "fire_pass_badge_count": 0},
                    "credit": {"score": 100, "reward_claimed": False},
                    "ban": {"is_banned": False}
                }

                # Add human readable ranks
                from config.ranks import RANK_MAP
                br_code = mapped_data["rank"]["battle_royale"]["rank_code"]
                br_max_code = mapped_data["rank"]["battle_royale"]["max_rank_code"]
                cs_code = mapped_data["rank"]["clash_squad"]["rank_code"]

                mapped_data["rank"]["battle_royale"]["rank_name"] = RANK_MAP.get(br_code) or (f"Rank {br_code}" if br_code else None)
                mapped_data["rank"]["battle_royale"]["max_rank_name"] = RANK_MAP.get(br_max_code) or (f"Rank {br_max_code}" if br_max_code else None)
                mapped_data["rank"]["clash_squad"]["rank_name"] = RANK_MAP.get(cs_code) or (f"Rank {cs_code}" if cs_code else None)

                player_data = PlayerData.model_validate(mapped_data)
                await cache.set(uid, current_region, player_data.model_dump())

                return PlayerResponse(
                    metadata=ResponseMetadata(
                        request_uid=uid, request_region=current_region,
                        fetched_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                        response_time_ms=int((time.monotonic() - start_time) * 1000),
                        api_version=settings.OB_VERSION, cache_hit=False
                    ),
                    data=player_data,
                    error=None
                )
            except:
                continue

    raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Auto-detection failed for UID {uid}. All regions checked.")
