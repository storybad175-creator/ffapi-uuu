import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from ff_api.config.settings import settings
from ff_api.api.schemas import PlayerData

@pytest.fixture
def mock_settings():
    with patch("ff_api.config.settings.settings") as mocked:
        mocked.CACHE_TTL_SECONDS = 300
        mocked.CACHE_MAX_ENTRIES = 10
        mocked.OB_VERSION = "OB53"
        yield mocked

@pytest.fixture
def sample_uid():
    return "4899748638"

@pytest.fixture
def sample_region():
    return "IND"

@pytest.fixture
def mock_player_data():
    return {
        "account": {
            "uid": "4899748638",
            "nickname": "Ƭɴɪᴛᴀᴄʜɪ",
            "level": 60,
            "exp": 964636,
            "region": "IND",
            "season_id": 38,
            "preferred_mode": "Battle Royale",
            "language": "English",
            "signature": "CHANDRU HERE...!!!",
            "honor_score": 100,
            "total_likes": 5817,
            "ob_version": "OB53",
            "created_at_epoch": 1641513600,
            "created_at": "2022-01-07T00:00:00Z",
            "last_login_epoch": 1735862400,
            "last_login": "2025-01-03T00:00:00Z",
            "account_type": "Normal"
        },
        "rank": {
            "battle_royale": {
                "rank_name": "Platinum IV",
                "rank_code": 114,
                "points": 2541,
                "max_rank_name": "Diamond I",
                "max_rank_code": 115,
                "visible": True
            },
            "clash_squad": {
                "rank_name": "Gold III",
                "rank_code": 209,
                "points": 261,
                "visible": True
            }
        },
        "stats": {
            "battle_royale": {
                "solo": {"matches": 10, "wins": 1, "win_rate": "10.00%", "kills": 20, "deaths": 9, "kd_ratio": 2.22, "headshots": 5, "headshot_rate": "25.00%", "avg_damage_per_match": 500.0, "booyahs": 1},
                "duo": {"matches": 10, "wins": 1, "win_rate": "10.00%", "kills": 20, "deaths": 9, "kd_ratio": 2.22, "headshots": 5, "headshot_rate": "25.00%", "avg_damage_per_match": 500.0, "booyahs": 1},
                "squad": {"matches": 10, "wins": 1, "win_rate": "10.00%", "kills": 20, "deaths": 9, "kd_ratio": 2.22, "headshots": 5, "headshot_rate": "25.00%", "avg_damage_per_match": 500.0, "booyahs": 1}
            },
            "clash_squad": {
                "ranked": {"matches": 10, "wins": 5, "win_rate": "50.00%", "kills": 30, "kd_ratio": 3.0}
            }
        },
        "social": {"guild": None},
        "pet": None,
        "cosmetics": {
            "avatar_id": 0, "banner_id": 0, "pin_id": 0, "character_id": 0,
            "equipped_outfit_ids": [], "equipped_weapon_skin_ids": []
        },
        "pass": {"booyah_pass_level": 0, "fire_pass_status": "Basic", "fire_pass_badge_count": 0},
        "credit": {"score": 100, "reward_claimed": False, "summary_period": None},
        "ban": {"is_banned": False, "ban_period": None, "ban_type": None}
    }
