# Free Fire UID Verification API — APEX v3.0

The definitive, production-ready Python repository for fetching Free Fire player data across all 14 regions.

## Features

- **Multi-Region Support**: All 14 Garena regions (IND, BR, SG, RU, ID, TW, US, VN, TH, ME, PK, CIS, BD, NA).
- **Secure Pipeline**: AES-CBC encryption and Protobuf v3 binary serialization.
- **Auto-Auth**: Automatic JWT lifecycle management for Garena MajorLogin.
- **Async Architecture**: Powered by `aiohttp`, `FastAPI`, and `asyncio`.
- **Advanced Caching**: TTL-based in-memory cache with LRU eviction and cache stampede protection.
- **Comprehensive Schema**: 60+ data fields including stats, ranks, guild, pet, and cosmetics.
- **Dual Interface**: RESTful API (FastAPI) and Command Line Interface (CLI).

## Installation

### Standard Setup
```bash
git clone https://github.com/your-repo/ff-api.git
cd ff-api
pip install -r requirements.txt
```

### Termux (Android)
```bash
pkg update && pkg upgrade
pkg install python rust binutils
pip install -r requirements.txt
```

## Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Fill in your Garena guest credentials and AES constants in `.env`.
   - `GARENA_GUEST_UID` / `GARENA_GUEST_TOKEN`: Extracted from Free Fire guest login.
   - `AES_KEY` / `AES_IV`: Community-extracted hex keys.

## Usage

### Starting the API Server
```bash
python -m ff_api.main --serve --port 8080
```

### API Endpoints
- `GET /player?uid={uid}&region={region}`: Fetch single player data.
- `GET /batch?uids={u1,u2}&region={region}`: Fetch up to 10 players concurrently.
- `GET /regions`: List all supported regions.
- `GET /health`: System health status.

### CLI Usage
```bash
# Single UID
python -m ff_api.cli --uid 4899748638 --region IND

# Batch Mode
python -m ff_api.cli --batch uids.txt --region BR

# Compact Output
python -m ff_api.cli --uid 4899748638 --region IND --format compact
```

## Testing
Run the full test suite using `pytest`:
```bash
pytest ff_api/tests
```

## Updating for New Versions
When Garena releases a new update (e.g., OB54), simply update the `OB_VERSION` in your `.env` file. If AES keys change, update `AES_KEY` and `AES_IV`.

## License
MIT License. For educational and research purposes only.
