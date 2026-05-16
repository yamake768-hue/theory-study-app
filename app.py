import streamlit as st
import streamlit.components.v1 as components
import json
import os
import glob
import requests

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

# --- GitHub Gistを利用したクラウド保存ロジック（チェック状態のみ） ---
def load_bookmarks():
    if "GITHUB_TOKEN" in st.secrets and "GIST_ID" in st.secrets:
        headers = {
            "Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
            "Accept": "application/vnd.github.v3+json"
        }
        try:
            res = requests.get(f"https://api.github.com/gists/{st.secrets['GIST_ID']}", headers=headers)
            if res.status_code == 200:
                files = res.json().get("files", {})
                if "bookmarks.json" in files:
                    content = files["bookmarks.json"]["content"]
                    return set(json.loads(content))
        except Exception:
            pass
    return set()

def save_bookmarks_to_server():
    if "GITHUB_TOKEN" not in st.secrets or "GIST_ID" not in st.secrets:
        return False, "Secrets未設定"

    headers = {
        "Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "files": {
            "bookmarks.json": {
                "content": json.dumps(list(st.session_state.bookmarks))
            }
        }
    }
    try:
        res = requests.patch(f"https://api.github.com/gists/{st.secrets['GIST_ID']}", headers=headers, json=payload)
        if res.status_code == 200:
            return True, ""
        else:
            return False, f"APIエラー ({res.status_code})"
    except Exception as e:
        return False, f"通信エラー: {str(e)}"

if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = load_bookmarks()


# --- URLパラメータによる状態の復元 ---
if "initialized" not in st.session_state:
    params = st.query_params
    url_ch = params.get("ch", chapters[0])
    url_cat = params.get("cat", "")
    try:
        url_q = int(params.get("q", 0))
    except ValueError:
        url_q = 0
        
    st.session_state.current_ch = url_ch if url_ch in data else chapters[0]
    valid_cats = list(data[st.session_state.current_ch].keys())
    st.session_state.current_cat = url_cat if url_cat in valid_cats else valid_cats[0]
    
    valid_q_len = len(data[st.session_state.current_ch][st.session_state.current_cat])
    st.session_state.q_index = url_q if 0 <= url_q < valid_q_len else 0
    
    st.session_state.active_q_id = f"{st.session_state.current_ch}__{st.session_state.current_cat}__{st.session_state.q_index}"
    st.session_state.answers = {} 
    
    fmt = data[st.session_state.current_ch][st.session_state.current_cat][st.session_state.q_index].get("format", "")
    st.session_state.user_input_area = fmt
    
    st.session_state.initialized = True
    st.session_state.filter_mode = False

def save_answer():
    st.session_state.answers[st.session_state.active_q_id] = st.session_state.user_input_area

def update_active_state(ch, cat, q_idx):
    new_id = f"{ch}__{cat}__{q_idx}"
    st.session_state.active_q_id = new_id
    
    if new_id in st.session_state.answers:
        st.session_state.user_input_area = st.session_state.answers[new_id]
    else:
        st.session_state.user_input_area = data[ch][cat][q_idx].get("format", "")
        
    st.query_params["ch"] = ch
    st.query_params["cat"] = cat
    st.query_params["q"] = str(q_idx)

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

# --- UI構築 ---
st.title("財務諸表論 理論演習")

with st.sidebar:
    st.header("メニュー")
    new_filter_mode = st.checkbox("☑ チェックした問題のみ表示", value=st.session_state.filter_mode)
    if new_filter_mode != st.session_state.filter_mode:
        st.session_state.filter_mode = new_filter_mode
        st.session_state.q_index = 0
        st.rerun()

    st.write("---")

    if st.session_state.filter_mode:
        st.success("復習モード作動中")
        st.markdown("<p style='font-size:0.8em; color:gray;'>チェックされた問題のみを順番に表示しています。章や単元の選択は現在無効です。</p>", unsafe_allow_html=True)
    else:
        with st.form("nav_form"):
            ch_idx = chapters.index(st.session_state.current_ch)
            selected_ch = st.selectbox("章を選択", chapters, index=ch_idx)
            
            cats = list(data[selected_ch].keys())
            cat_idx = cats.index(st.session_state.current_cat) if (selected_ch == st.session_state.current_ch and st.session_state.current_cat in cats) else 0
            selected_cat = st.selectbox("単元を選択", cats, index=cat_idx)
            
            submitted = st.form_submit_button("この単元を解く", type="primary", use_container_width=True)
            if submitted:
                save_answer()
                st.session_state.current_ch = selected_ch
                st.session_state.current_cat = selected_cat
                st.session_state.q_index = 0
                update_active_state(selected_ch, selected_cat, 0)
                st.rerun()

# --- モードに応じた問題データの抽出 ---
if st.session_state.filter_mode:
    active_list = []
    for ch in chapters:
        for cat in data[ch].keys():
            for i, q in enumerate(data[ch][cat]):
                temp_id = f"{ch}____{cat}____{i}"
                if temp_id in st.session_state.bookmarks:
                    active_list.append((ch, cat, i, q, temp_id))
    
    total_q = len(active_list)
    if total_q == 0:
        st.warning("チェックされた問題がありません。左のメニューからチェックを外し、通常モードで問題にチェックを入れてください。")
        st.stop()
        
    if st.session_state.q_index >= total_q:
        st.session_state.q_index = total_q - 1
        
    current_ch, current_cat, original_idx, current_q, q_id = active_list[st.session_state.q_index]
    
    if st.session_state.active_q_id != q_id:
        update_active_state(current_ch, current_cat, original_idx)
        
    is_first = (st.session_state.q_index == 0)
    is_last = (st.session_state.q_index == total_q - 1)
    
    def go_next():
        save_answer()
        st.session_state.q_index += 1
        n_ch, n_cat, n_idx, _, _ = active_list[st.session_state.q_index]
        update_active_state(n_ch, n_cat, n_idx)

    def go_prev():
        save_answer()
        st.session_state.q_index -= 1
        p_ch, p_cat, p_idx, _, _ = active_list[st.session_state.q_index]
        update_active_state(p_ch, p_cat, p_idx)
        
    display_ch = current_ch
    display_cat = current_cat

else:
    questions = data[st.session_state.current_ch][st.session_state.current_cat]
    total_q = len(questions)
    
    if st.session_state.q_index >= total_q:
        st.session_state.q_index = 0
        
    current_q = questions[st.session_state.q_index]
    current_ch = st.session_state.current_ch
    current_cat = st.session_state.current_cat
    original_idx = st.session_state.q_index
    q_id = f"{current_ch}____{current_cat}____{original_idx}"
    
    is_first = (get_prev_state() is None)
    is_last = (get_next_state() is None)
    
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
            
    display_ch = current_ch
    display_cat = current_cat

# --- メイン画面描画 ---
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

st.markdown(f"<span style='color:gray; font-size: 0.9em;'>【{display_ch}：{display_cat}】</span>", unsafe_allow_html=True)

# チェックボックスと保存処理
is_checked = q_id in st.session_state.bookmarks
chk_key = f"chk_{q_id}"
new_is_checked = st.checkbox("✅ この問題をチェックする（弱点・復習用）", value=is_checked, key=chk_key)

if new_is_checked != is_checked:
    if new_is_checked:
        st.session_state.bookmarks.add(q_id)
    else:
        st.session_state.bookmarks.discard(q_id)
        
    success, msg = save_bookmarks_to_server()
    if success:
        st.toast("✅ クラウドにチェックを保存しました", icon="☁️")
    else:
        st.error(f"❌ 保存に失敗しました: {msg}")
    st.rerun()

# 問題文の表示
question_text = current_q.get("question", "").replace("\n", "<br>")
st.markdown(
    f"""
    <div style="background-color: #f0f8ff; padding: 1.5rem; border-radius: 0.5rem; color: #1f2937; margin-bottom: 1rem; border-left: 5px solid #0068c9; line-height: 1.6;">
        {question_text}
    </div>
    """,
    unsafe_allow_html=True
)

# 解答の目安
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

# --- タブによる入力方式の切り替え ---
tab1, tab2 = st.tabs(["✍️ 解答入力（テキスト）", "📝 計算用紙（手書き）"])

with tab1:
    user_ans = st.text_area("解答を入力:", key="user_input_area", height=200, label_visibility="collapsed")

with tab2:
    # --- 超軽量HTML5ネイティブキャンバス（ラグ・滲み解消版） ---
    # Streamlitのシステムを介さず、iPadのブラウザ上で直接高速描画処理を行います。
    # Retinaディスプレイ（高DPI）に対応し、滲みを防ぐスケーリング処理を実装。
    
    canvas_html = f"""
    <div style="position: relative; width: 100%; height: 400px; border: 1px solid #ccc; border-radius: 5px; background: #ffffff;">
      <button onclick="clearCanvas()" style="position: absolute; top: 10px; right: 10px; z-index: 10; padding: 5px 15px; border-radius: 5px; border: 1px solid #ccc; background: #f8f9fa; cursor: pointer;">🗑️ 全消去</button>
      <canvas id="scratchpad" style="width: 100%; height: 100%; touch-action: none;"></canvas>
    </div>
    
    <script>
      const canvas = document.getElementById('scratchpad');
      const ctx = canvas.getContext('2d');
      
      // Retinaディスプレイ等の高画質画面での滲みを防ぐ処理
      function resizeCanvas() {{
          const rect = canvas.getBoundingClientRect();
          const dpr = window.devicePixelRatio || 1;
          canvas.width = rect.width * dpr;
          canvas.height = rect.height * dpr;
          ctx.scale(dpr, dpr);
          ctx.lineWidth = 1; // ペンの太さ固定
          ctx.lineCap = 'round';
          ctx.lineJoin = 'round';
          ctx.strokeStyle = '#000000';
      }}
      
      // 初期化
      resizeCanvas();
      
      let drawing = false;
      
      function getPos(e) {{
          const rect = canvas.getBoundingClientRect();
          return {{
              x: e.clientX - rect.left,
              y: e.clientY - rect.top
          }};
      }}
      
      // Apple Pencilのタッチイベント（ラグなし）
      canvas.addEventListener('pointerdown', (e) => {{
          drawing = true;
          const pos = getPos(e);
          ctx.beginPath();
          ctx.moveTo(pos.x, pos.y);
          e.preventDefault();
      }});
      
      canvas.addEventListener('pointermove', (e) => {{
          if (!drawing) return;
          const pos = getPos(e);
          ctx.lineTo(pos.x, pos.y);
          ctx.stroke();
          e.preventDefault();
      }});
      
      window.addEventListener('pointerup', () => {{
          drawing = false;
      }});
      
      // 全消去機能
      function clearCanvas() {{
          const rect = canvas.getBoundingClientRect();
          ctx.clearRect(0, 0, rect.width, rect.height);
      }}
    </script>
    """
    
    # HTMLをそのまま埋め込む（StreamlitのReactシステムを完全にバイパスします）
    components.html(canvas_html, height=420)

# 解答の表示
with st.expander("💡 解答を表示する"):
    answer_text = current_q.get("answer", "解答データがありません。").replace("\n", "  \n")
    st.success(answer_text)

st.write("---")
