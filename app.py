import html
import re
import uuid
from datetime import datetime

import streamlit as st

import storage

NAME_MAX = 50
MEMO_MAX = 100
QTY_MIN, QTY_MAX = 1, 999

st.set_page_config(page_title="쇼핑 리스트", page_icon="🛒", layout="centered")

# 아이템 행(st-key-row-*)은 모바일에서도 한 줄로 유지되도록 Streamlit 기본 컬럼 스택을 덮어쓴다.
st.markdown(
    """
<style>
.block-container { max-width: 640px; padding-top: 2.5rem; }

[class*="st-key-row-"] {
    border-bottom: 1px solid rgba(128, 128, 128, 0.2);
    padding: 0.2rem 0;
}
[class*="st-key-row-"] [data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    align-items: center;
    gap: 0.4rem;
}
[class*="st-key-row-"] [data-testid="stColumn"] {
    min-width: 0 !important;
    width: auto !important;
}
[class*="st-key-row-"] [data-testid="stColumn"]:nth-child(1) { flex: 0 0 1.6rem !important; }
[class*="st-key-row-"] [data-testid="stColumn"]:nth-child(2) { flex: 1 1 auto !important; }
[class*="st-key-row-"] [data-testid="stColumn"]:nth-child(n+3) { flex: 0 0 2.6rem !important; }
[class*="st-key-row-"] button {
    min-width: 2.6rem;
    min-height: 2.6rem;
    padding: 0;
}
[class*="st-key-row-"] [data-testid="stMarkdownContainer"] { margin-bottom: 0; }

/* 입력 폼·편집 박스의 [이름 | 수량]도 모바일에서 한 줄 유지 */
:is([data-testid="stForm"], [class*="st-key-editbox-"]) [data-testid="stHorizontalBlock"]:has(input[type="number"]) {
    flex-wrap: nowrap !important;
}
:is([data-testid="stForm"], [class*="st-key-editbox-"]) [data-testid="stHorizontalBlock"]:has(input[type="number"]) > [data-testid="stColumn"] {
    min-width: 0 !important;
    width: auto !important;
}
:is([data-testid="stForm"], [class*="st-key-editbox-"]) [data-testid="stHorizontalBlock"]:has(input[type="number"]) > [data-testid="stColumn"]:first-child { flex: 1 1 auto !important; }
:is([data-testid="stForm"], [class*="st-key-editbox-"]) [data-testid="stHorizontalBlock"]:has(input[type="number"]) > [data-testid="stColumn"]:last-child { flex: 0 0 7.5rem !important; }

@media (max-width: 640px) {
    .block-container { padding-top: 1.5rem; }
    h1 { font-size: 1.9rem !important; }
}

.item { line-height: 1.35; overflow-wrap: anywhere; }
.item-name { font-weight: 500; }
.item-qty {
    display: inline-block;
    margin-left: 0.4rem;
    padding: 0 0.5rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    background: rgba(128, 128, 128, 0.18);
    vertical-align: 0.1em;
}
.item-memo { font-size: 0.8rem; opacity: 0.6; margin-top: 0.1rem; }
.item.done { opacity: 0.45; }
.item.done .item-name { text-decoration: line-through; }
</style>
""",
    unsafe_allow_html=True,
)

st.session_state.setdefault("editing_id", None)
st.session_state.setdefault("confirm_clear", False)
st.session_state.setdefault("new_qty", 1)

# 세션마다 목록 사본을 들고 있으면 다른 탭/사용자의 변경을 덮어쓰므로,
# 매 실행과 매 콜백에서 파일을 다시 읽고(load → 변경 → save) 파일만 기준으로 삼는다.


def _find(items, item_id):
    return next((i for i in items if i["id"] == item_id), None)


def _md_escape(text):
    # 사용자 입력이 Markdown 서식으로 해석되지 않도록 특수문자 이스케이프
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|~<>:$])", r"\\\1", text)


def _toast(msg, icon):
    # 이전 토스트가 떠 있는 동안 새 토스트는 무시되므로(Streamlit 동작) 표시 시간을 짧게 둔다.
    st.toast(msg, icon=icon, duration=2)


def _item_html(item):
    memo = f'<div class="item-memo">{html.escape(item["memo"])}</div>' if item["memo"] else ""
    return (
        f'<div class="item{" done" if item["checked"] else ""}">'
        f'<span class="item-name">{html.escape(item["name"])}</span>'
        f'<span class="item-qty">x{item["quantity"]}</span>{memo}</div>'
    )


# ---------- 콜백 ----------

def add_item():
    name = st.session_state.new_name.strip()
    if not name:
        st.session_state.flash_warning = "아이템 이름을 입력해 주세요."
        return
    items = storage.load_items()
    items.append({
        "id": str(uuid.uuid4()),
        "name": name[:NAME_MAX],
        "quantity": int(st.session_state.new_qty),
        "memo": st.session_state.new_memo.strip()[:MEMO_MAX],
        "checked": False,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    })
    storage.save_items(items)
    _toast(f"'{_md_escape(name[:NAME_MAX])}' 추가했어요", "✅")
    st.session_state.new_name = ""
    st.session_state.new_qty = 1
    st.session_state.new_memo = ""


def toggle_item(item_id):
    items = storage.load_items()
    item = _find(items, item_id)
    if item:
        item["checked"] = st.session_state[f"chk_{item_id}"]
        storage.save_items(items)


def start_edit(item_id):
    item = _find(storage.load_items(), item_id)
    if not item:
        return
    st.session_state.editing_id = item_id
    st.session_state[f"edit_name_{item_id}"] = item["name"]
    st.session_state[f"edit_qty_{item_id}"] = item["quantity"]
    st.session_state[f"edit_memo_{item_id}"] = item["memo"]


def save_edit(item_id):
    items = storage.load_items()
    item = _find(items, item_id)
    if not item:
        st.session_state.editing_id = None
        return
    name = st.session_state[f"edit_name_{item_id}"].strip()
    if not name:
        st.session_state.flash_warning = "아이템 이름은 비워 둘 수 없어요."
        return
    item["name"] = name[:NAME_MAX]
    item["quantity"] = int(st.session_state[f"edit_qty_{item_id}"])
    item["memo"] = st.session_state[f"edit_memo_{item_id}"].strip()[:MEMO_MAX]
    st.session_state.editing_id = None
    storage.save_items(items)


def cancel_edit():
    st.session_state.editing_id = None


def delete_item(item_id):
    items = storage.load_items()
    item = _find(items, item_id)
    if st.session_state.editing_id == item_id:
        st.session_state.editing_id = None
    if item:
        items.remove(item)
        storage.save_items(items)
        _toast(f"'{_md_escape(item['name'])}' 삭제했어요", "🗑️")


def delete_checked():
    items = storage.load_items()
    kept = [i for i in items if not i["checked"]]
    if _find(kept, st.session_state.editing_id) is None:
        st.session_state.editing_id = None
    storage.save_items(kept)
    _toast(f"체크된 항목 {len(items) - len(kept)}개를 삭제했어요", "🗑️")


def ask_clear(flag):
    st.session_state.confirm_clear = flag


def clear_all():
    st.session_state.editing_id = None
    st.session_state.confirm_clear = False
    storage.save_items([])
    _toast("전체 삭제했어요", "🗑️")


# ---------- 헤더 + F6. 진행 현황 ----------

st.title("🛒 쇼핑 리스트")

items = storage.load_items()
if st.session_state.editing_id and _find(items, st.session_state.editing_id) is None:
    st.session_state.editing_id = None  # 다른 탭에서 삭제된 경우

total = len(items)
remaining = sum(1 for i in items if not i["checked"])
if total:
    st.markdown(f"남은 아이템 **{remaining}개** / 전체 {total}개")
    st.progress((total - remaining) / total)

# ---------- F1. 추가 ----------

with st.form("add_form"):
    c_name, c_qty = st.columns([3, 1])
    c_name.text_input("아이템 이름", key="new_name", max_chars=NAME_MAX, placeholder="예: 우유")
    c_qty.number_input("수량", key="new_qty", min_value=QTY_MIN, max_value=QTY_MAX, step=1)
    st.text_input("메모 (선택)", key="new_memo", max_chars=MEMO_MAX, placeholder="예: 저지방")
    st.form_submit_button("추가", type="primary", width="stretch", on_click=add_item)

if msg := st.session_state.pop("flash_warning", None):
    st.warning(msg)

# ---------- 아이템 목록 (F2~F4) ----------

if not items:
    st.info("쇼핑 리스트가 비어 있어요. 아이템을 추가해 보세요!")
else:
    for item in sorted(items, key=lambda i: (i["checked"], i["created_at"])):
        iid = item["id"]

        if st.session_state.editing_id == iid:
            with st.container(border=True, key=f"editbox-{iid}"):
                e_name, e_qty = st.columns([3, 1])
                e_name.text_input("이름", key=f"edit_name_{iid}", max_chars=NAME_MAX)
                e_qty.number_input("수량", key=f"edit_qty_{iid}", min_value=QTY_MIN, max_value=QTY_MAX, step=1)
                st.text_input("메모", key=f"edit_memo_{iid}", max_chars=MEMO_MAX)
                b_save, b_cancel = st.columns(2)
                b_save.button("저장", key=f"save_{iid}", on_click=save_edit, args=(iid,), type="primary", width="stretch")
                b_cancel.button("취소", key=f"cancel_{iid}", on_click=cancel_edit, width="stretch")
            continue

        with st.container(key=f"row-{iid}"):
            c_chk, c_text, c_edit, c_del = st.columns(4, vertical_alignment="center")
            st.session_state[f"chk_{iid}"] = item["checked"]
            c_chk.checkbox(
                "구매 완료", key=f"chk_{iid}",
                on_change=toggle_item, args=(iid,), label_visibility="collapsed",
            )
            c_text.markdown(_item_html(item), unsafe_allow_html=True)
            c_edit.button("✏️", key=f"edit_{iid}", on_click=start_edit, args=(iid,), help="수정", type="tertiary")
            c_del.button("🗑️", key=f"del_{iid}", on_click=delete_item, args=(iid,), help="삭제", type="tertiary")

    # ---------- 일괄 삭제 ----------
    st.write("")
    if not st.session_state.confirm_clear:
        b_checked, b_all = st.columns(2)
        b_checked.button(
            "체크된 항목 삭제", on_click=delete_checked, width="stretch",
            disabled=not any(i["checked"] for i in items),
        )
        b_all.button("전체 삭제", on_click=ask_clear, args=(True,), width="stretch")
    else:
        st.warning("정말 전체 삭제할까요? 되돌릴 수 없어요.")
        y, n = st.columns(2)
        y.button("삭제", key="clear_yes", on_click=clear_all, type="primary", width="stretch")
        n.button("취소", key="clear_no", on_click=ask_clear, args=(False,), width="stretch")
