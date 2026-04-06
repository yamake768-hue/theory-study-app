import streamlit as st
import json
import os
import glob

# --- ページ設定 ---
st.set_page_config(page_title="財務諸表論 理論学習アプリ", layout="centered")

# --- データ読み込み（複数ファイル対応） ---
@st.cache_data
def load_data():
    data = {}
    # questionsフォルダ内の全JSONファイルを取得
    # クラウド環境等でフォルダがない場合は空の辞書を返す
    if not os.path.exists("questions"):
        return data
        
    json_files = glob.glob("questions/*.json")
    
    # ファイル名でソートして読み込む（第1章、第2章...と順番に並べるため）
    for file_path in sorted(json_files):
        # ファイル名（拡張子なし）を章のタイトルとして取得
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

# --- セッション状態（状態管理）の初期化 ---
if "chapter" not in st.session_state:
    st.session_state.chapter = chapters[0]
if "category" not in st.session_state:
    st.session_state.category = list(data[chapters[0]].keys())[0]
if "q_index" not in st.session_state:
    st.session_state.q_index = 0

# ドロップダウン変更時のリセット処理
def on_dropdown_change():
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

# 1. 章と単元の選択（サイドバーに移動してスマホ最適化）
with st.sidebar:
    st.header("メニュー")
    selected_chapter = st.selectbox(
        "章を選択",
        chapters,
        key="chapter",
        on_change=on_dropdown_change
    )

    # 選択された章に属する単元リストを取得
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

# プログレス表示
st.caption(f"問題 {st.session_state.q_index + 1} / {total_q}")

# 2. 問題文の表示（Markdown仕様に合わせて改行コードの前に半角スペース2つを付与）
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
input_key = f"input_{selected_chapter}_{selected_category}_{st.session_state.q_index}"

if input_key not in st.session_state:
    st.session_state[input_key] = format_text

user_ans = st.text_area("解答を入力:", key=input_key, height=200, label_visibility="collapsed")

# 5. 解答の表示（アコーディオン）
with st.expander("💡 解答を表示する"):
    # 解答のテキストもMarkdownの改行仕様（半角スペース2つ追加）に変換して縦並びに
    answer_text = current_q.get("answer", "解答データがありません。").replace("\n", "  \n")
    st.success(answer_text)

st.write("---")

# 6. ナビゲーションボタン
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
