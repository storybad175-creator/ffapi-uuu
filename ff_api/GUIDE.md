# FF-API APEX v3.3 — Comprehensive Usage Guide

This guide provides everything you need to deploy, use, and scale the Free Fire UID Verification API.

---

## 1. System Requirements

The FF-API is designed for high performance and low resource consumption.

*   **Operating System**: Linux (Ubuntu/Debian recommended), macOS, or Android (via Termux).
*   **Python Version**: 3.8, 3.9, 3.10, 3.11, or 3.12.
*   **Memory (RAM)**:
    *   Minimum: 512 MB
    *   Recommended: 1 GB (for high concurrency)
*   **Storage**: < 50 MB (excluding dependencies).
*   **Network**: Active internet connection with access to Garena's production IPs.

---

## 2. Installation & Setup

### Standard Installation (PC/VPS)
```bash
# Clone the repository
git clone https://github.com/your-repo/ff-api.git
cd ff-api

# Install dependencies
pip install -r requirements.txt
```

### Termux (Android)
```bash
pkg update && pkg upgrade
pkg install python rust binutils
pip install -r requirements.txt
```

---

## 3. Configuration (.env)

Create a `.env` file in the root directory. No Garena credentials are required for public player data in v3.3.

| Variable | Default | Description |
| :--- | :--- | :--- |
| `OB_VERSION` | `OB52` | Game version header (e.g., OB52) |
| `SERVER_PORT` | `8080` | Port for the FastAPI web server |
| `LOG_LEVEL` | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |
| `CACHE_TTL_SECONDS` | `300` | How long (in seconds) to cache player data |
| `CACHE_MAX_ENTRIES` | `500` | Maximum number of UIDs to store in RAM |
| `RATE_LIMIT_RPM` | `30` | Requests per minute allowed per client IP |

---

## 4. How to Use

### Strategy A: Command Line Interface (CLI)
The CLI is the fastest way to verify a single UID or run batch jobs.

```bash
# Verify a single UID in the IND region
python -m ff_api.cli --uid 1429634330 --region IND

# Verify a single UID in the BR region (compact JSON output)
python -m ff_api.cli --uid 123456789 --region BR --format compact

# List all 14 supported regions
python -m ff_api.cli --regions

# Run a batch scan from a file (one UID per line)
python -m ff_api.cli --batch list.txt --region SG
```

### Strategy B: FastAPI Web Server
Start the server to provide a RESTful API for your website or Discord bot.

```bash
python -m ff_api.main --serve --port 8080
```

**Available Endpoints:**
*   `GET /player?uid={uid}&region={region}`: Fetch single player data.
*   `GET /batch?uids={u1,u2,u3}&region={region}`: Fetch multiple players (max 10).
*   `GET /regions`: Returns a list of all supported codes.
*   `GET /health`: Check system status and game version.

---

## 5. Available Information

The API returns a structured JSON response containing over 60 data points:

*   **Account Info**: UID, Nickname, Level, EXP, Region, Season ID, Account Type, Creation Date, Last Login.
*   **Rank Info**: Battle Royale Rank (Name/Code), Clash Squad Rank, Max Rank achieved.
*   **Statistics (BR)**: Detailed Career stats for Solo, Duo, and Squad (Matches, Wins, Kills, K/D, Headshot %, Avg Damage).
*   **Statistics (CS)**: Ranked Clash Squad matches, wins, kills, and K/D.
*   **Social**: Guild ID, Guild Name, Level, Member Count, Capacity, and Guild Leader details.
*   **Cosmetics**: Avatar, Banner, Pin, and equipped Outfit/Weapon Skin IDs.
*   **Security**: Ban Status, Ban Period, and Ban Reason.
*   **Player Integrity**: Honor Score and Credit Score.

---

## 6. Request Limits & Error Handling

### Rate Limiting
The built-in middleware prevents your IP from being banned by Garena.
*   **Default Limit**: 30 requests per minute (RPM) per client IP.
*   **Exceeding Limit**: Returns HTTP 429 (Too Many Requests) with a `Retry-After` header.

### Error Codes
| Code | Meaning | Action |
| :--- | :--- | :--- |
| `INVALID_UID` | UID is not numeric or wrong length | Check your input |
| `PLAYER_NOT_FOUND` | UID does not exist in that region | Try a different region |
| `SERVICE_UNAVAILABLE` | Garena servers are down | The tool will automatically retry |
| `DECODE_ERROR` | Binary parsing failed | Possible game update (check OB_VERSION) |

---

## 7. Smart Orchestration (Reliability)

If Garena's direct servers are under maintenance (HTTP 503), the tool will:
1.  Rotate through **6 verified production IPs**.
2.  Switch between **4 different URL patterns**.
3.  Automatically **fallback to community mirrors** to ensure you get the data.

---
**Version**: 3.3.0
**Release Date**: April 2026
**Developer**: APEX Systems Architect

## 8. Example Output (UID: 1429634330)

```json
{
  "metadata": {
    "request_uid": "1429634330",
    "request_region": "IND",
    "fetched_at": "2026-04-15T12:33:08.973104Z",
    "response_time_ms": 37200,
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
