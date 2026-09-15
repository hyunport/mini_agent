"""8020 포트에서 실행되는 네이버 주요 지수 Streamable HTTP MCP Server입니다."""

import json
import os
import urllib.request
from pathlib import Path
from urllib.error import HTTPError, URLError

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Referer": "https://m.stock.naver.com/",
    "Accept": "application/json",
}

DOMESTIC_URL = "https://polling.finance.naver.com/api/realtime/domestic/index/{code}"
WORLD_URL = "https://api.stock.naver.com/index/{code}/basic"

TARGETS = [
    ("코스피", "domestic", "KOSPI"),
    ("코스닥", "domestic", "KOSDAQ"),
    ("S&P 500", "world", ".INX"),
    ("나스닥", "world", ".IXIC"),
]

TIMEOUT_SECONDS = 10

INDEX_HOST = os.getenv("INDEX_HOST", "0.0.0.0")
INDEX_PORT = int(os.getenv("INDEX_PORT", "8020"))

mcp = FastMCP(
    "mini-agent-naver-index",
    instructions=(
        "네이버 증권에서 코스피, 코스닥, S&P 500, 나스닥 지수를 "
        "조회합니다."
    ),
    host=INDEX_HOST,
    port=INDEX_PORT,
    stateless_http=True,
    json_response=True,
)


def _get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def _sign(raw: str | int) -> str:
    """네이버 전일 대비 코드를 등락률에 표시할 부호로 변환합니다."""
    return "-" if str(raw) in ("4", "5") else ""


def _pack(
    name: str,
    code: str,
    price: str,
    diff: str,
    ratio: str,
    updown_code: str | int,
    updated_at: str | None,
) -> dict:
    sign = _sign(updown_code)
    normalized_diff = str(diff).lstrip("+-")
    normalized_ratio = str(ratio).lstrip("+-")
    direction = {
        "1": "상승",
        "2": "상승",
        "3": "보합",
        "4": "하락",
        "5": "하락",
    }.get(str(updown_code), "-")

    return {
        "name": name,
        "code": code,
        "price": price,
        "change": f"{sign}{normalized_diff}",
        "change_pct": f"{sign}{normalized_ratio}",
        "direction": direction,
        "updated_at": updated_at,
    }


def _fetch_domestic(name: str, code: str) -> dict:
    data = _get_json(DOMESTIC_URL.format(code=code))
    index = data["datas"][0]
    return _pack(
        name=name,
        code=code,
        price=index["closePrice"],
        diff=index["compareToPreviousClosePrice"],
        ratio=index["fluctuationsRatio"],
        updown_code=index["compareToPreviousPrice"]["code"],
        updated_at=index.get("localTradedAt") or index.get("tradeTime"),
    )


def _fetch_world(name: str, code: str) -> dict:
    index = _get_json(WORLD_URL.format(code=code))
    return _pack(
        name=name,
        code=code,
        price=index["closePrice"],
        diff=index["compareToPreviousClosePrice"],
        ratio=index["fluctuationsRatio"],
        updown_code=index["compareToPreviousPrice"]["code"],
        updated_at=index.get("localTradedAt"),
    )


@mcp.tool()
def get_market_indices() -> dict:
    """네이버 증권에서 코스피, 코스닥, S&P 500, 나스닥 지수를 조회합니다."""
    items = []

    for name, market_type, code in TARGETS:
        try:
            if market_type == "domestic":
                items.append(_fetch_domestic(name, code))
            else:
                items.append(_fetch_world(name, code))
        except (
            HTTPError,
            URLError,
            TimeoutError,
            KeyError,
            IndexError,
            ValueError,
        ) as error:
            items.append({
                "name": name,
                "code": code,
                "error": f"{type(error).__name__}: {error}",
            })

    return {
        "items": items,
        "total": len(items),
        "source": "naver-finance",
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
