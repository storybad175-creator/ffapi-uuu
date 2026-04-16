from datetime import datetime, timezone
from typing import Any, Dict, Optional
from core.crypto import crypto
from core.proto import proto_handler
from api.schemas import PlayerData
from config.ranks import RANK_MAP
from api.errors import FFError, ErrorCode

class ResponseDecoder:
    @staticmethod
    def decode(raw_data: bytes) -> PlayerData:
        try:
            # Step 1: AES Decrypt
            decrypted_data = crypto.decrypt(raw_data)
        except Exception as e:
            raise FFError(ErrorCode.DECODE_ERROR, f"AES decryption failed: {str(e)}")

        try:
            # Step 2: Protobuf Decode
            raw_dict = proto_handler.decode_response(decrypted_data)
        except Exception as e:
            raise FFError(
                ErrorCode.DECODE_ERROR,
                "Protobuf decoding failed. Possible AES key rotation?",
                extra={"possible_key_rotation": True}
            )

        # Step 3: Map to Pydantic Model
        return ResponseDecoder.map_to_model(raw_dict)

    @staticmethod
    def map_to_model(d: Dict[str, Any]) -> PlayerData:
        acc = d.get("account_info", {})
        rank = d.get("rank_info", {})
        br_rank = rank.get("br_rank", {})
        cs_rank = rank.get("cs_rank", {})
        stats = d.get("stats_info", {})
        br_stats = stats.get("br_stats", {})
        cs_stats = stats.get("cs_stats", {}).get("ranked", {}) # Simplified mapping
        social = d.get("social_info", {})
        guild = social.get("guild", {})
        leader = guild.get("leader", {})
        pet = d.get("pet_info", {})
        cosm = d.get("cosmetics_info", {})
        pass_inf = d.get("pass_info", {})
        credit = d.get("credit_info", {})
        ban = d.get("ban_info", {})

        def get_rank_name(code: Optional[int]) -> Optional[str]:
            return RANK_MAP.get(code) if code else None

        def calc_win_rate(wins: int, matches: int) -> str:
            if not matches: return "0.00%"
            return f"{(wins / matches) * 100:.2f}%"

        def calc_kd(kills: int, deaths: int) -> float:
            return round(kills / max(deaths, 1), 2)

        def calc_hs_rate(hs: int, kills: int) -> str:
            if not kills: return "0.00%"
            return f"{(hs / kills) * 100:.2f}%"

        def format_stat_line(sl: Dict[str, Any]) -> Dict[str, Any]:
            m = sl.get("matches", 0)
            w = sl.get("wins", 0)
            k = sl.get("kills", 0)
            d = sl.get("deaths", 0)
            h = sl.get("headshots", 0)
            return {
                "matches": m,
                "wins": w,
                "win_rate": calc_win_rate(w, m),
                "kills": k,
                "deaths": d,
                "kd_ratio": calc_kd(k, d),
                "headshots": h,
                "headshot_rate": calc_hs_rate(h, k),
                "avg_damage_per_match": round(sl.get("avg_damage", 0), 2),
                "booyahs": w
            }

        def format_epoch(epoch: Optional[int]) -> Optional[str]:
            if not epoch: return None
            return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat().replace("+00:00", "Z")

        # Construct PlayerData compatible dict
        data_dict = {
            "account": {
                "uid": str(acc.get("uid", "")),
                "nickname": acc.get("nickname", ""),
                "level": acc.get("level", 0),
                "exp": acc.get("exp", 0),
                "region": acc.get("region", ""),
                "season_id": acc.get("season_id", 0),
                "preferred_mode": acc.get("preferred_mode", "Battle Royale"),
                "language": acc.get("language", "English"),
                "signature": acc.get("signature", ""),
                "honor_score": acc.get("honor_score", 100),
                "total_likes": acc.get("total_likes", 0),
                "ob_version": acc.get("ob_version", ""),
                "created_at_epoch": acc.get("created_at_epoch"),
                "created_at": format_epoch(acc.get("created_at_epoch")),
                "last_login_epoch": acc.get("last_login_epoch"),
                "last_login": format_epoch(acc.get("last_login_epoch")),
                "account_type": acc.get("account_type", "Normal")
            },
            "rank": {
                "battle_royale": {
                    "rank_name": get_rank_name(br_rank.get("rank_code")),
                    "rank_code": br_rank.get("rank_code"),
                    "points": br_rank.get("points", 0),
                    "max_rank_name": get_rank_name(br_rank.get("max_rank_code")),
                    "max_rank_code": br_rank.get("max_rank_code"),
                    "visible": bool(br_rank.get("visible", True))
                },
                "clash_squad": {
                    "rank_name": get_rank_name(cs_rank.get("rank_code")),
                    "rank_code": cs_rank.get("rank_code"),
                    "points": cs_rank.get("points", 0),
                    "visible": bool(cs_rank.get("visible", True))
                }
            },
            "stats": {
                "battle_royale": {
                    "solo": format_stat_line(br_stats.get("solo", {})),
                    "duo": format_stat_line(br_stats.get("duo", {})),
                    "squad": format_stat_line(br_stats.get("squad", {}))
                },
                "clash_squad": {
                    "ranked": {
                        "matches": cs_stats.get("matches", 0),
                        "wins": cs_stats.get("wins", 0),
                        "win_rate": calc_win_rate(cs_stats.get("wins", 0), cs_stats.get("matches", 0)),
                        "kills": cs_stats.get("kills", 0),
                        "kd_ratio": calc_kd(cs_stats.get("kills", 0), cs_stats.get("deaths", 0))
                    }
                }
            },
            "social": {
                "guild": {
                    "id": str(guild.get("id", "")),
                    "name": guild.get("name", ""),
                    "level": guild.get("level", 0),
                    "member_count": guild.get("member_count", 0),
                    "capacity": guild.get("capacity", 0),
                    "leader": {
                        "uid": str(leader.get("uid", "")),
                        "nickname": leader.get("nickname", ""),
                        "level": leader.get("level", 0),
                        "rank_name": get_rank_name(leader.get("rank_code"))
                    }
                } if guild.get("id") else None
            },
            "pet": {
                "name": pet.get("name"),
                "level": pet.get("level", 0),
                "exp": pet.get("exp", 0),
                "active_skill": pet.get("active_skill"),
                "skin_id": pet.get("skin_id", 0),
                "is_selected": bool(pet.get("is_selected"))
            } if pet.get("name") else None,
            "cosmetics": {
                "avatar_id": cosm.get("avatar_id", 0),
                "banner_id": cosm.get("banner_id", 0),
                "pin_id": cosm.get("pin_id", 0),
                "character_id": cosm.get("character_id", 0),
                "equipped_outfit_ids": cosm.get("outfit_ids", []),
                "equipped_weapon_skin_ids": cosm.get("weapon_skin_ids", [])
            },
            "pass": {
                "booyah_pass_level": pass_inf.get("booyah_pass_level", 0),
                "fire_pass_status": pass_inf.get("fire_pass_status", "Basic"),
                "fire_pass_badge_count": pass_inf.get("fire_pass_badge_count", 0)
            },
            "credit": {
                "score": credit.get("score", 100),
                "reward_claimed": bool(credit.get("reward_claimed")),
                "summary_period": credit.get("summary_period")
            },
            "ban": {
                "is_banned": bool(ban.get("is_banned")),
                "ban_period": ban.get("ban_period"),
                "ban_type": ban.get("ban_type")
            }
        }

        return PlayerData.model_validate(data_dict)

decoder = ResponseDecoder()
