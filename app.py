import streamlit as st
import json
import os
import glob

# --- ページ設定 ---
st.set_page_config(page_title="財務諸表論 理論学習アプリ", layout="wide")

# --- UI改善用のカスタムCSS ---
st.markdown(
    """
    <style>
    [data-testid="stSidebarResizer"] {
        width: 15px !important;
        background-color: rgba(150, 150, 150, 0.1) !important;
    }
    [data-testid="stSidebarResizer"]:hover {
        background-color: rgba(150, 150, 150, 0.4) !important;
    }
    .stMarkdown p, .stMarkdown div {
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }
    .stMarkdown strong {
        font-weight: normal !important;
        text-decoration: underline !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- データ読み込み ---
@st.cache_data
def load_data():
    data = {}
    if not os.path.exists("questions"):
        return data
        
    json_files = glob.glob("questions/*.json")
    
    for file_path in sorted(json_files):
        chapter_name = os.path.splitext(os.path.basename(file_path))[0]
        with open(file_path, "r", encoding="utf-8") as f:
            chapter_data = json.load(f)
            data[chapter_name] = chapter_data
            
    return data

data = load_data()

if not data:
    st.error("「questions」フォルダが見つからないか、中にJSONデータがありません。")
    st.stop()

chapters = list(data.keys())

# --- セッション状態の初期化 ---
if "chapter" not in st.session_state:
    st.session_state.chapter = chapters[0]
if "category" not in st.session_state:
    st.session_state.category = list(data[chapters[0]].keys())[0]
if "q_index" not in st.session_state:
    st.session_state.q_index = 0

# 【追加】誤爆防止用：前回の章・単元を記憶する変数
if "prev_chapter" not in st.session_state:
    st.session_state.prev_chapter = st.session_state.chapter
if "prev_category" not in st.session_state:
    st.session_state.prev_category = st.session_state.category

# --- ナビゲーションロジック ---
def get_next_state():
    ch_idx = chapters.index(st.session_state.chapter)
    cats = list(data[st.session_state.chapter].keys())
    cat_idx = cats.index(st.session_state.category)
    q_idx = st.session_state.q_index
    
    if q_idx < len(data[st.session_state.chapter][st.session_state.category]) - 1:
        return st.session_state.chapter, st.session_state.category, q_idx + 1
    if cat_idx < len(cats) - 1:
        return st.session_state.chapter, cats[cat_idx + 1], 0
    if ch_idx < len(chapters) - 1:
        next_ch = chapters[ch_idx + 1]
        next_cat = list(data[next_ch].keys())[0]
        return next_ch, next_cat, 0
    return None

def get_prev_state():
    ch_idx = chapters.index(st.session_state.chapter)
    cats = list(data[st.session_state.chapter].keys())
    cat_idx = cats.index(st.session_state.category)
    q_idx = st.session_state.q_index
    
    if q_idx > 0:
        return st.session_state.chapter, st.session_state.category, q_idx - 1
    if cat_idx > 0:
        prev_cat = cats[cat_idx - 1]
        last_q_idx = len(data[st.session_state.chapter][prev_cat]) - 1
        return st.session_state.chapter, prev_cat, last_q_idx
    if ch_idx > 0:
        prev_ch = chapters[ch_idx - 1]
        prev_cat = list(data[prev_ch].keys())[-1]
        last_q_idx = len(data[prev_ch][prev_cat]) - 1
        return prev_ch, prev_cat, last_q_idx
    return None

# 【修正】ボタンで移動した時は、前回記憶(prev)も一緒に更新して誤爆を防ぐ
def go_next():
    next_state = get_next_state()
    if next_state:
        st.session_state.chapter, st.session_state.category, st.session_state.q_index = next_state
        st.session_state.prev_chapter = next_state[0]
        st.session_state.prev_category = next_state[1]

def go_prev():
    prev_state = get_prev_state()
    if prev_state:
        st.session_state.chapter, st.session_state.category, st.session_state.q_index = prev_state
        st.session_state.prev_chapter = prev_state[0]
        st.session_state.prev_category = prev_state[1]

# --- UI構築 ---
st.title("財務諸表論 理論演習")

# 1. 章と単元の選択（サイドバー）
# ※ on_change コールバックを削除し、誤爆を防止
with st.sidebar:
    st.header("メニュー")
    selected_chapter = st.selectbox(
        "章を選択",
        chapters,
        key="chapter"
    )

    categories = list(data[selected_chapter].keys())
    
    # 章が切り替わった時に単元リストが矛盾しないための安全対策
    if st.session_state.category not in categories:
        st.session_state.category = categories[0]

    selected_category = st.selectbox(
        "単元を選択",
        categories,
        key="category"
    )

# 【追加】本当にユーザーが手でプルダウンを変更した時だけ、1問目(0)にリセットする
if (st.session_state.chapter != st.session_state.prev_chapter) or (st.session_state.category != st.session_state.prev_category):
    st.session_state.q_index = 0
    st.session_state.prev_chapter = st.session_state.chapter
    st.session_state.prev_category = st.session_state.category

# データ取得
questions = data[st.session_state.chapter][st.session_state.category]
total_q = len(questions)

if st.session_state.q_index >= total_q:
    st.session_state.q_index = 0

current_q = questions[st.session_state.q_index]

# 2. ナビゲーションとプログレス
disable_prev = (get_prev_state() is None)
disable_next = (get_next_state() is None)

col_prev, col_next, col_prog = st.columns([1, 1, 5])

with col_prev:
    st.button("◀ 戻る", on_click=go_prev, disabled=disable_prev, use_container_width=True)

with col_next:
    st.button("次へ ▶", on_click=go_next, disabled=disable_next, use_container_width=True)

with col_prog:
    st.markdown(
        f"<div style='text-align: right; padding-top: 10px; color: gray; font-size: 0.9em;'>"
        f"問題 {st.session_state.q_index + 1} / {total_q}</div>", 
        unsafe_allow_html=True
    )

# 3. 問題文の表示
question_text = current_q.get("question", "").replace("\n", "<br>")
st.markdown(
    f"""
    <div style="background-color: #f0f8ff; padding: 1.5rem; border-radius: 0.5rem; color: #1f2937; margin-bottom: 1rem; border-left: 5px solid #0068c9; line-height: 1.6;">
        {question_text}
    </div>
    """,
    unsafe_allow_html=True
)

# 4. 解答の目安
format_text = current_q.get("format", "")
expected_lines = current_q.get("expected_lines", 5)

if format_text.strip() != "" and "①" in format_text:
    num_blanks = sum(1 for char in format_text if char in "①②③④⑤⑥⑦⑧⑨⑩")
    guide_text = f"目安: {num_blanks}箇所の穴埋め"
elif format_text.strip() != "":
    guide_text = "目安: 穴埋め・箇条書き"
else:
    min_chars = expected_lines * 25
    max_chars = expected_lines * 35
    guide_text = f"目安: 約 {expected_lines} 行 （{min_chars}〜{max_chars} 文字程度）"

st.markdown(f"<span style='color:blue; font-weight:bold; font-size: 0.9em;'>{guide_text}</span>", unsafe_allow_html=True)

# 5. 解答欄
input_key = f"input_{st.session_state.chapter}_{st.session_state.category}_{st.session_state.q_index}"

if input_key not in st.session_state:
    st.session_state[input_key] = format_text

user_ans = st.text_area("解答を入力:", key=input_key, height=200, label_visibility="collapsed")

# 6. 解答の表示
with st.expander("💡 解答を表示する"):
    answer_text = current_q.get("answer", "解答データがありません。").replace("\n", "  \n")
    st.success(answer_text)

st.write("---")
