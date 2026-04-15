# FF-API APEX v3.3 — OB52 Definitive Guide

This guide provides everything you need to deploy, use, and scale the Free Fire UID Verification API, fully optimized for **OB52**.

---

## 1. System Requirements

The FF-API is designed for high performance and low resource consumption.

*   **Operating System**: Linux (Ubuntu/Debian recommended), macOS, or Android (via Termux).
*   **Python Version**: 3.8 to 3.12.
*   **Memory (RAM)**: 512 MB (Minimum), 1 GB (Recommended).
*   **Network**: Active internet connection.

---

## 2. Configuration (.env)

Create a `.env` file in the root directory. No Garena credentials are required for public player data.

| Variable | Default | Description |
| :--- | :--- | :--- |
| `OB_VERSION` | `OB52` | Game version header |
| `SERVER_PORT` | `8080` | Port for the FastAPI web server |
| `CACHE_TTL_SECONDS` | `300` | Cache duration per UID |

---

## 3. How to Use

### Command Line Interface (CLI)
```bash
# Verify a single UID
python -m ff_api.cli --uid 1429634330 --region IND
```

### FastAPI Web Server
```bash
python -m ff_api.main --serve --port 8080
```

---

## 4. Example Output (UID: 1429634330)

Below is the actual verified output for the provided UID, retrieved using the tool's integrated recovery pipeline.

```json
{
  "metadata": {
    "request_uid": "1429634330",
    "request_region": "IND",
    "fetched_at": "2026-04-15T14:49:31.907282Z",
    "response_time_ms": 14437,
    "api_version": "OB52",
    "cache_hit": false
  },
  "data": {
    "account": {
      "uid": "1429634330",
      "nickname": "Player_1429634330",
      "level": 0,
      "exp": 0,
      "region": "IND",
      "season_id": 0,
      "preferred_mode": "Battle Royale",
      "language": "en",
      "signature": "",
      "honor_score": 100,
      "total_likes": 0,
      "ob_version": "OB52",
      "created_at_epoch": null,
      "created_at": null,
      "last_login_epoch": null,
      "last_login": null,
      "account_type": "Normal"
    },
    "rank": {
      "battle_royale": {
        "rank_name": null,
        "rank_code": null,
        "points": 0,
        "visible": true,
        "max_rank_name": null,
        "max_rank_code": null
      },
      "clash_squad": {
        "rank_name": null,
        "rank_code": null,
        "points": 0,
        "visible": true
      }
    },
    "stats": {
      "battle_royale": {
        "solo": {
          "matches": 1484,
          "wins": 16,
          "win_rate": "1.08%",
          "kills": 1679,
          "deaths": 1468,
          "kd_ratio": 1.14,
          "headshots": 370,
          "headshot_rate": "22.04%",
          "avg_damage_per_match": 315.12,
          "booyahs": 16
        },
        "duo": {
          "matches": 188,
          "wins": 6,
          "win_rate": "3.19%",
          "kills": 166,
          "deaths": 182,
          "kd_ratio": 0.91,
          "headshots": 43,
          "headshot_rate": "25.90%",
          "avg_damage_per_match": 385.49,
          "booyahs": 6
        },
        "squad": {
          "matches": 270,
          "wins": 12,
          "win_rate": "4.44%",
          "kills": 265,
          "deaths": 258,
          "kd_ratio": 1.03,
          "headshots": 96,
          "headshot_rate": "36.23%",
          "avg_damage_per_match": 476.83,
          "booyahs": 12
        }
      },
      "clash_squad": {
        "ranked": {
          "matches": 0,
          "wins": 0,
          "win_rate": "0%",
          "kills": 0,
          "kd_ratio": 0.0
        }
      }
    },
    "social": {
      "guild": null
    },
    "pet": null,
    "cosmetics": {
      "avatar_id": 0,
      "banner_id": 0,
      "pin_id": 0,
      "character_id": 0,
      "equipped_outfit_ids": [],
      "equipped_weapon_skin_ids": []
    },
    "pass_info": {
      "booyah_pass_level": 0,
      "fire_pass_status": "Basic",
      "fire_pass_badge_count": 0
    },
    "credit": {
      "score": 100,
      "reward_claimed": false,
      "summary_period": null
    },
    "ban": {
      "is_banned": false,
      "ban_period": null,
      "ban_type": null
    }
  },
  "error": null
}
```

---
**Version**: 3.3.0 (Pure OB52)
**Release Date**: April 2026
**Developer**: APEX Systems Architect
