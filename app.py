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

# --- 【重要】セッション状態の初期化（ワープ対策の要） ---
if "initialized" not in st.session_state:
    first_ch = chapters[0]
    first_cat = list(data[first_ch].keys())[0]
    
    st.session_state.current_ch = first_ch
    st.session_state.current_cat = first_cat
    st.session_state.q_index = 0
    
    # 現在の問題IDと、解答を保存する辞書
    st.session_state.active_q_id = f"{first_ch}__{first_cat}__0"
    st.session_state.answers = {}
    
    # 最初の解答欄のフォーマットをセット
    fmt = data[first_ch][first_cat][0].get("format", "")
    st.session_state.user_input_area = fmt
    
    st.session_state.initialized = True

# --- 状態管理・保存ロジック ---
def save_answer():
    """現在テキストエリアに入力されている文字を保存する"""
    st.session_state.answers[st.session_state.active_q_id] = st.session_state.user_input_area

def update_active_state(ch, cat, q_idx):
    """次の問題のフォーマット（または保存された過去の解答）をテキストエリアに読み込む"""
    new_id = f"{ch}__{cat}__{q_idx}"
    st.session_state.active_q_id = new_id
    
    if new_id in st.session_state.answers:
        st.session_state.user_input_area = st.session_state.answers[new_id]
    else:
        st.session_state.user_input_area = data[ch][cat][q_idx].get("format", "")

# --- ナビゲーションロジック ---
def get_next_state():
    ch = st.session_state.current_ch
    cat = st.session_state.current_cat
    q_idx = st.session_state.q_index
    
    ch_idx = chapters.index(ch)
    cats = list(data[ch].keys())
    cat_idx = cats.index(cat)
    
    if q_idx < len(data[ch][cat]) - 1:
        return ch, cat, q_idx + 1
    if cat_idx < len(cats) - 1:
        return ch, cats[cat_idx + 1], 0
    if ch_idx < len(chapters) - 1:
        next_ch = chapters[ch_idx + 1]
        return next_ch, list(data[next_ch].keys())[0], 0
    return None

def get_prev_state():
    ch = st.session_state.current_ch
    cat = st.session_state.current_cat
    q_idx = st.session_state.q_index
    
    ch_idx = chapters.index(ch)
    cats = list(data[ch].keys())
    cat_idx = cats.index(cat)
    
    if q_idx > 0:
        return ch, cat, q_idx - 1
    if cat_idx > 0:
        prev_cat = cats[cat_idx - 1]
        last_q_idx = len(data[ch][prev_cat]) - 1
        return ch, prev_cat, last_q_idx
    if ch_idx > 0:
        prev_ch = chapters[ch_idx - 1]
        prev_cat = list(data[prev_ch].keys())[-1]
        last_q_idx = len(data[prev_ch][prev_cat]) - 1
        return prev_ch, prev_cat, last_q_idx
    return None

def go_next():
    save_answer()
    next_state = get_next_state()
    if next_state:
        st.session_state.current_ch, st.session_state.current_cat, st.session_state.q_index = next_state
        update_active_state(*next_state)

def go_prev():
    save_answer()
    prev_state = get_prev_state()
    if prev_state:
        st.session_state.current_ch, st.session_state.current_cat, st.session_state.q_index = prev_state
        update_active_state(*prev_state)

# --- UI構築 ---
st.title("財務諸表論 理論演習")

# 1. 完全に安全な手動同期サイドバー
with st.sidebar:
    st.header("メニュー")
    
    # 章の選択
    ch_idx = chapters.index(st.session_state.current_ch)
    selected_ch = st.selectbox("章を選択", chapters, index=ch_idx)
    
    if selected_ch != st.session_state.current_ch:
        save_answer()
        st.session_state.current_ch = selected_ch
        st.session_state.current_cat = list(data[selected_ch].keys())[0]
        st.session_state.q_index = 0
        update_active_state(st.session_state.current_ch, st.session_state.current_cat, 0)
        st.rerun()

    # 単元の選択
    cats = list(data[st.session_state.current_ch].keys())
    cat_idx = cats.index(st.session_state.current_cat) if st.session_state.current_cat in cats else 0
    selected_cat = st.selectbox("単元を選択", cats, index=cat_idx)
    
    if selected_cat != st.session_state.current_cat:
        save_answer()
        st.session_state.current_cat = selected_cat
        st.session_state.q_index = 0
        update_active_state(st.session_state.current_ch, st.session_state.current_cat, 0)
        st.rerun()

# 2. ナビゲーションとプログレス
questions = data[st.session_state.current_ch][st.session_state.current_cat]
total_q = len(questions)

is_first = (get_prev_state() is None)
is_last = (get_next_state() is None)

col_prev, col_next, col_prog = st.columns([1, 1, 5])

with col_prev:
    st.button("◀ 戻る", on_click=go_prev, disabled=is_first, use_container_width=True)

with col_next:
    st.button("次へ ▶", on_click=go_next, disabled=is_last, use_container_width=True)

with col_prog:
    st.markdown(
        f"<div style='text-align: right; padding-top: 10px; color: gray; font-size: 0.9em;'>"
        f"問題 {st.session_state.q_index + 1} / {total_q}</div>", 
        unsafe_allow_html=True
    )

# 3. 問題文の表示
current_q = questions[st.session_state.q_index]
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

# 5. 【究極の対策】固定IDを持つ解答欄
# keyを固定することで、Safariによる入力欄の破壊・強制リロードを完全に防ぎます
user_ans = st.text_area("解答を入力:", key="user_input_area", height=200, label_visibility="collapsed")

# 6. 解答の表示
with st.expander("💡 解答を表示する"):
    answer_text = current_q.get("answer", "解答データがありません。").replace("\n", "  \n")
    st.success(answer_text)

st.write("---")
