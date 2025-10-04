import os
from typing import Dict, Generator, Iterable

import requests
import streamlit as st

BASE_URL = "https://api.app.legis365.com/public/v1.0"


def has_api_key() -> bool:
    return bool(st.secrets.get("LEGIS_API_KEY", "") or os.getenv("LEGIS_API_KEY", ""))


def get_headers() -> Dict[str, str]:
    key = st.secrets.get("LEGIS_API_KEY", "") or os.getenv("LEGIS_API_KEY", "")
    return {"Accept": "application/json", "X-API-Key": key}


def paged(path: str, page_size: int = 500) -> Iterable[dict]:
    page = 1
    while True:
        response = requests.get(
            f"{BASE_URL}{path}",
            headers=get_headers(),
            params={"page": page, "pageSize": page_size},
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        items = payload.get("results") or []
        if not items:
            break
        for item in items:
            yield item
        if len(items) < page_size:
            break
        page += 1
