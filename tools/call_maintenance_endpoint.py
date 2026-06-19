#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import os
from urllib import request


def main() -> None:
    site_url = os.environ.get("SCOUT_SITE_URL", "").rstrip("/")
    secret = os.environ.get("MAINTENANCE_SECRET", "")
    basic_auth = os.environ.get("SCOUT_BASIC_AUTH", "")
    if not site_url or not secret:
        print("SCOUT_SITE_URL or MAINTENANCE_SECRET is not set; skipping live maintenance endpoint.")
        return

    headers = {
        "Content-Type": "application/json",
        "X-Scout-Maintenance-Secret": secret,
    }
    if basic_auth:
        token = base64.b64encode(basic_auth.encode("utf-8")).decode("ascii")
        headers["Authorization"] = f"Basic {token}"

    req = request.Request(
        f"{site_url}/api/maintenance/enrich",
        data=b"{}",
        headers=headers,
        method="POST",
    )
    with request.urlopen(req, timeout=600) as response:
        payload = json.loads(response.read().decode("utf-8"))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
