import streamlit as st
import json
import os
import glob

# --- ページ設定（wideに変更して画面を広く使う） ---
st.set_page_config(page_title="財務諸表論 理論学習アプリ", layout="wide")

# --- UI改善用のカスタムCSSの注入 ---
st.markdown(
    """
    <style>
    /* 1. サイドバーのリサイズ枠を太くして掴みやすくする */
    [data-testid="stSidebarResizer"] {
        width: 15px !important;
        background-color: rgba(150, 150, 150, 0.1) !important;
    }
    [data-testid="stSidebarResizer"]:hover {
        background-color: rgba(150, 150, 150, 0.4) !important;
    }
    
    /* 2. サイドバー表示時にテキストが裏に隠れないよう強制的に折り返す */
    .stMarkdown p {
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
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

# --- ナビゲーションロジック（章や単元をまたいで移動する機能） ---
def get_next_state():
    """次の問題のインデックス、単元、章を計算する"""
    ch_idx = chapters.index(st.session_state.chapter)
    cats = list(data[st.session_state.chapter].keys())
    cat_idx = cats.index(st.session_state.category)
    q_idx = st.session_state.q_index
    
    # 同じ単元内にまだ次の問題がある場合
    if q_idx < len(data[st.session_state.chapter][st.session_state.category]) - 1:
        return st.session_state.chapter, st.session_state.category, q_idx + 1
    # 単元の最後の場合 -> 次の単元の1問目へ
    if cat_idx < len(cats) - 1:
        return st.session_state.chapter, cats[cat_idx + 1], 0
    # 章の最後の場合 -> 次の章の最初の単元の1問目へ
    if ch_idx < len(chapters) - 1:
        next_ch = chapters[ch_idx + 1]
        next_cat = list(data[next_ch].keys())[0]
        return next_ch, next_cat, 0
    # 全問題の最後
    return None

def get_prev_state():
    """前の問題のインデックス、単元、章を計算する"""
    ch_idx = chapters.index(st.session_state.chapter)
    cats = list(data[st.session_state.chapter].keys())
    cat_idx = cats.index(st.session_state.category)
    q_idx = st.session_state.q_index
    
    # 同じ単元内に前の問題がある場合
    if q_idx > 0:
        return st.session_state.chapter, st.session_state.category, q_idx - 1
    # 単元の最初の場合 -> 前の単元の最後の問題へ
    if cat_idx > 0:
        prev_cat = cats[cat_idx - 1]
        last_q_idx = len(data[st.session_state.chapter][prev_cat]) - 1
        return st.session_state.chapter, prev_cat, last_q_idx
    # 章の最初の場合 -> 前の章の最後の単元の最後の問題へ
    if ch_idx > 0:
        prev_ch = chapters[ch_idx - 1]
        prev_cat = list(data[prev_ch].keys())[-1]
        last_q_idx = len(data[prev_ch][prev_cat]) - 1
        return prev_ch, prev_cat, last_q_idx
    # 全問題の最初
    return None

def go_next():
    next_state = get_next_state()
    if next_state:
        st.session_state.chapter, st.session_state.category, st.session_state.q_index = next_state

def go_prev():
    prev_state = get_prev_state()
    if prev_state:
        st.session_state.chapter, st.session_state.category, st.session_state.q_index = prev_state

# ドロップダウンを手動で操作した時のリセット処理
def on_dropdown_change():
    st.session_state.q_index = 0

# --- UI構築 ---
st.title("財務諸表論 理論演習")

# 1. 章と単元の選択（サイドバー）
with st.sidebar:
    st.header("メニュー")
    selected_chapter = st.selectbox(
        "章を選択",
        chapters,
        key="chapter",
        on_change=on_dropdown_change
    )

    categories = list(data[selected_chapter].keys())

    selected_category = st.selectbox(
        "単元を選択",
        categories,
        key="category",
        on_change=on_dropdown_change
    )

questions = data[selected_chapter][selected_category]
total_q = len(questions)

# q_indexが範囲外になった場合の安全対策
if st.session_state.q_index >= total_q:
    st.session_state.q_index = 0

current_q = questions[st.session_state.q_index]

# 2. ナビゲーションとプログレス（問題文の上部にコンパクトに配置）
disable_prev = (get_prev_state() is None)
disable_next = (get_next_state() is None)

# カラムの幅を [1 : 1 : 5] の比率で分割し、ボタンを左に寄せて小さくする
col_prev, col_next, col_prog = st.columns([1, 1, 5])

with col_prev:
    st.button("◀ 戻る", on_click=go_prev, disabled=disable_prev, use_container_width=True)

with col_next:
    st.button("次へ ▶", on_click=go_next, disabled=disable_next, use_container_width=True)

with col_prog:
    # 右寄せで問題の進捗を表示し、ボタンの高さと合うように余白を調整
    st.markdown(
        f"<div style='text-align: right; padding-top: 10px; color: gray; font-size: 0.9em;'>"
        f"問題 {st.session_state.q_index + 1} / {total_q}</div>", 
        unsafe_allow_html=True
    )

# 3. 問題文の表示
question_text = current_q.get("question", "").replace("\n", "  \n")
st.info(question_text)

# 4. 解答の目安を計算・表示
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

# 5. 解答欄（テキストエリア）
input_key = f"input_{selected_chapter}_{selected_category}_{st.session_state.q_index}"

if input_key not in st.session_state:
    st.session_state[input_key] = format_text

user_ans = st.text_area("解答を入力:", key=input_key, height=200, label_visibility="collapsed")

# 6. 解答の表示（アコーディオン）
with st.expander("💡 解答を表示する"):
    answer_text = current_q.get("answer", "解答データがありません。").replace("\n", "  \n")
    st.success(answer_text)

st.write("---")
