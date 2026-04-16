import asyncio
import argparse
import json
import sys
from typing import List

from core.fetcher import fetch_player
from config.regions import REGION_MAP
from api.errors import FFError

from core.transport import transport

async def run_fetch(uid: str, region: str, compact: bool = False):
    try:
        response = await fetch_player(uid, region)
        indent = None if compact else 2
        print(json.dumps(response.model_dump(by_alias=True), indent=indent))
    except FFError as e:
        error_res = {
            "error": {
                "code": e.code,
                "message": e.message,
                "extra": e.extra
            }
        }
        print(json.dumps(error_res, indent=2), file=sys.stderr)
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
    finally:
        await transport.close()

async def run_batch(file_path: str, region: str):
    try:
        with open(file_path, 'r') as f:
            uids = [line.strip() for line in f if line.strip()]

        tasks = [fetch_player(uid, region) for uid in uids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, Exception):
                print(json.dumps({"error": str(res)}))
            else:
                print(json.dumps(res.model_dump(by_alias=True)))
    except Exception as e:
        print(f"Batch Error: {str(e)}", file=sys.stderr)
    finally:
        await transport.close()

def main():
    parser = argparse.ArgumentParser(description="Free Fire API CLI")
    parser.add_argument("--uid", type=str, help="Player UID")
    parser.add_argument("--region", type=str, help="Region code (IND, BR, etc.)")
    parser.add_argument("--batch", type=str, help="Path to file containing UIDs (one per line)")
    parser.add_argument("--format", choices=["pretty", "compact"], default="pretty", help="Output format")
    parser.add_argument("--regions", action="store_true", help="List all supported regions")
    parser.add_argument("--health", action="store_true", help="Check API status")

    args = parser.parse_args()

    if args.regions:
        print("Supported Regions:", ", ".join(REGION_MAP.keys()))
        return

    if args.health:
        print("FF-API v3.0: Status OK")
        return

    if args.batch:
        if not args.region:
            print("Error: --region is required for batch mode", file=sys.stderr)
            sys.exit(1)
        asyncio.run(run_batch(args.batch, args.region))
    elif args.uid:
        asyncio.run(run_fetch(args.uid, args.region, compact=(args.format == "compact")))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
