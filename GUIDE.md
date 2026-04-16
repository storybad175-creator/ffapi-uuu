# Free Fire UID Verification API v3.0 - OB52 (April 2026)

## Overview
This repository provides a production-grade API for fetching Free Fire player data using only a UID. It supports all 14 regions and includes a multi-layer retrieval strategy:
1. **Direct Garena IP Rotation:** Attempts to connect directly to production servers using Protobuf v3.
2. **Mirror Recovery:** Automatically falls back to high-uptime community mirrors if Garena returns 503 errors.
3. **Auto-Detection:** Scans multiple regions automatically if the player's server is unknown.

## Verified Example (UID: 1429634330)

Below is the real-time JSON response for a verified player.

```json
{
  "metadata": {
    "request_uid": "1429634330",
    "request_region": "IND",
    "fetched_at": "2026-04-16T03:20:25.374486Z",
    "response_time_ms": 20254,
    "api_version": "OB52",
    "cache_hit": false
  },
  "data": {
    "account": {
      "uid": "1429634330",
      "nickname": "Dk᭄RAFAY༒★",
      "level": 55,
      "exp": 506858,
      "region": "BD",
      "season_id": 50,
      "preferred_mode": "Battle Royale",
      "language": "LANGUAGEEN",
      "signature": "[B][c] [520017]Legends never die",
      "honor_score": 100,
      "total_likes": 1466,
      "ob_version": "OB52",
      "created_at_epoch": 1568561094,
      "created_at": "2019-09-15T15:24:54Z",
      "last_login_epoch": 1647943420,
      "last_login": "2022-03-22T10:03:40Z",
      "account_type": "Normal"
    },
    "rank": {
      "battle_royale": {
        "rank_name": "Platinum III",
        "rank_code": 113,
        "points": 1000,
        "visible": true
      },
      "clash_squad": {
        "rank_name": "Gold II",
        "rank_code": 208,
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
          "matches": 1760,
          "wins": 767,
          "win_rate": "43.58%",
          "kills": 5126,
          "kd_ratio": 0.89
        }
      }
    },
    "social": {
      "guild": {
        "id": "3007862528",
        "name": "I'M_CRIMINAL",
        "level": 1,
        "member_count": 39,
        "capacity": 40,
        "leader": {
          "uid": "2349742356",
          "nickname": "Leader",
          "level": 0
        }
      }
    },
    "pet": {
      "name": "Night Panther",
      "level": 7,
      "exp": 6018,
      "is_selected": true
    }
  }
}
```

## Key Fields
| Field | Description |
| :--- | :--- |
| `nickname` | The player's current in-game name (supports Unicode/Symbols). |
| `level` | Current account level. |
| `rank` | BR and CS Ranks with points and human-readable names. |
| `win_rate` | Computed percentage across solo, duo, and squad modes. |
| `kd_ratio` | Calculated Kills/Deaths (minimum 1 death to avoid division by zero). |
| `created_at` | ISO-8601 timestamp of account creation. |

## Troubleshooting
- **PLAYER_NOT_FOUND**: The UID does not exist or Garena has throttled the region.
- **SERVICE_UNAVAILABLE**: All mirrors and direct IPs are currently unreachable.
- **DECODE_ERROR**: Protobuf mapping failed (likely due to an unannounced OB update).
