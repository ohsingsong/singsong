"""쇼핑 리스트 데이터 로드/저장 (JSON 파일)."""

import json
import os
import threading
from pathlib import Path

# 테스트 등에서 다른 파일을 쓰도록 환경변수로 경로를 바꿀 수 있다.
DATA_FILE = Path(
    os.environ.get("SHOPPING_LIST_FILE", Path(__file__).parent / "data" / "shopping_list.json")
)

# Streamlit 세션들은 한 프로세스의 스레드이므로, 동시 읽기/쓰기(임시 파일 충돌,
# Windows에서 읽는 중인 파일 교체 시 PermissionError)를 막기 위해 잠근다.
_lock = threading.Lock()


def load_items() -> list[dict]:
    """저장된 아이템 목록을 반환한다. 파일이 없거나 손상되었으면 빈 리스트."""
    try:
        with _lock, DATA_FILE.open(encoding="utf-8") as f:
            items = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        return []
    return items if isinstance(items, list) else []


def save_items(items: list[dict]) -> None:
    """아이템 목록을 JSON 파일로 저장한다."""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA_FILE.with_suffix(".tmp")
    with _lock:
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        tmp.replace(DATA_FILE)
