import streamlit as st
import json
import os

# --- ページ設定 ---
# タブレット等の広い画面でも見やすいように設定
st.set_page_config(page_title="財務諸表論 理論学習アプリ", layout="centered")

# --- データ読み込み ---
@st.cache_data
def load_data():
    questions_file = "questions.json"
    if os.path.exists(questions_file):
        with open(questions_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

data = load_data()

if not data:
    st.error("questions.json が見つからないか、データが空です。")
    st.stop()

categories = list(data.keys())

# --- セッション状態（状態管理）の初期化 ---
if "category" not in st.session_state:
    st.session_state.category = categories[0]
if "q_index" not in st.session_state:
    st.session_state.q_index = 0

# カテゴリが変更されたときに問題番号をリセットするコールバック関数
def on_category_change():
    st.session_state.q_index = 0

# ボタン用のコールバック関数
def go_prev():
    if st.session_state.q_index > 0:
        st.session_state.q_index -= 1

def go_next(total_q):
    if st.session_state.q_index < total_q - 1:
        st.session_state.q_index += 1


# --- UI構築 ---
st.title("財務諸表論 理論演習")

# 1. カテゴリ選択（ドロップダウン）
selected_category = st.selectbox(
    "単元を選択してください",
    categories,
    key="category",
    on_change=on_category_change
)

questions = data[selected_category]
total_q = len(questions)
current_q = questions[st.session_state.q_index]

# プログレス表示
st.caption(f"問題 {st.session_state.q_index + 1} / {total_q}")

# 2. 問題文の表示
question_text = current_q.get("question", "").replace("\n", "  \n")
st.info(question_text)

# 3. 解答の目安を計算・表示
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

# 4. 解答欄（テキストエリア）
# 問題ごとに一意のキーを持たせることで、セッション中に一時的に入力を保持
input_key = f"input_{selected_category}_{st.session_state.q_index}"

# 初回表示時のみ、フォーマット（①など）を初期値としてセット
if input_key not in st.session_state:
    st.session_state[input_key] = format_text

user_ans = st.text_area("解答を入力:", key=input_key, height=200, label_visibility="collapsed")

# 5. 解答の表示（アコーディオン）
with st.expander("💡 解答を表示する"):
    st.success(current_q.get("answer", "解答データがありません。"))

st.write("---")

# 6. ナビゲーションボタン
# 端末の画面幅に合わせて均等に配置
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.button(
        "◀ 戻る",
        on_click=go_prev,
        disabled=(st.session_state.q_index == 0),
        use_container_width=True
    )

with col3:
    st.button(
        "次へ ▶",
        on_click=go_next,
        args=(total_q,),
        disabled=(st.session_state.q_index == total_q - 1),
        use_container_width=True
    )
