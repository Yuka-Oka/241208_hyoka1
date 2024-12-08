# 2024/12/08
# ログイン機能もつけたい
# streamlit_page_change使ってみる

import openai
import os
import streamlit as st
import subprocess
from io import StringIO
import tempfile
import requests
import re
from datetime import datetime
import pytz


# 背景色を指定
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f9f4ff;
    }
    [data-testid="stSidebar"] {
        background-color: #eaeaff;
    }
    </style>
    """,
    unsafe_allow_html=True
)

if "user_id" not in st.session_state:
    st.session_state.user_id = None

def main():
    # １ページ目表示
    st.markdown(
    """
    <h1 style="font-size: 38px;">プログラミング学習者支援システム</h1>
    """,
    unsafe_allow_html=True
    )

    st.markdown(
    """
    <h1 style="font-size: 20px;">IDを入力してください</h1>
    """,
    unsafe_allow_html=True
    )

    st.session_state.user_id = st.text_input(" ", key="login_input")
    st.button("ログイン", on_click=change_page)

def change_page():
    # ページ切り替えボタンコールバック
    st.session_state["page_control"]=1

def next_page():
    # ２ページ目表示
    
    st.markdown(
    """
    <h1 style="font-size: 38px;">プログラミング学習者支援システム</h1>
    """,
    unsafe_allow_html=True
    )

    st.write(f"使用中のID: {st.session_state.user_id}")

    ############ github用 ############
    JDoodle_Client_ID = st.secrets["client_id"]
    JDoodle_Client_Secret = st.secrets["client_secret"]
    openai.api_key = st.secrets["api_key"]
    ##################################

    # session_satte "openai_model"：gptモデル設定
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4"

    # session_satte'chat_history'：会話履歴を保存
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []

    # session_satte "input_history"：入力履歴保存
    if 'input_history' not in st.session_state:
        st.session_state.input_history = []

    # session_satte "down_log"：ダウンロードする内容入れる用
    if "down_log" not in st.session_state:
        st.session_state.down_log = []

    # コード＋コンパイル結果を格納用
    if "code_compile" not in st.session_state:
        st.session_state.code_compile = []

    # 辞書my_dict: プロンプトを格納
    my_dict = {
        "簡潔に教えて": "最初に直す箇所を１つだけあげてください",
        "もう少し教えて": "プログラムのエラーを解説してください。コードは含めないでください",
        "色々知りたい": "プログラムのエラーを解説してください。必要ならば、部分的にコードを提示してください。"
    }

    # 解説のレベルをラジオボタンで選択
    self_sys_prompt = "プログラムのエラーを解説してください。必要ならば、部分的にコードを提示してください。"

    # テキストを表示（サイドバー）
    st.sidebar.markdown("<h2 style='font-size: 22px;'>① 解説のレベルを選択</h2>", unsafe_allow_html=True)

    # ラジオボタン（サイドバー）
    action = st.sidebar.radio(" ", ("簡潔に教えて", "もう少し教えて", "色々知りたい"))

    if action == list(my_dict.keys())[0]:
        self_sys_prompt = my_dict[list(my_dict.keys())[0]]

    if action == list(my_dict.keys())[1]:
        self_sys_prompt = my_dict[list(my_dict.keys())[1]]

    if action == list(my_dict.keys())[2]:
        self_sys_prompt = my_dict[list(my_dict.keys())[2]]

    # サイドバー：テキスト表示
    st.sidebar.markdown("<h2 style='font-size: 22px;'>② ファイルアップロード</h2>", unsafe_allow_html=True)

    # サイドバー：ファイルアップロード
    uploaded_file = st.sidebar.file_uploader(" ", type=["java"])

    # サイドバー：テキスト表示
    st.sidebar.markdown("<h2 style='font-size: 22px;'>③ 解説生成</h2>", unsafe_allow_html=True)

    # 関数response_generation：OpenAI APIを用いて応答生成
    # 引数error_code: コード＋エラー文
    # 引数prom: システムへのプロンプト
    # 返り値　full_response: 生成した解説
    def response_generation(error_code, prom):
        print("response_generation")

        # systemプロンプト
        print("self_sys_prompt:")
        print(prom)

        # 応答格納用変数
        full_response = ""
        message_placeholder = st.empty()

        error_code += "プログラムのエラーを説明してください"
        print(error_code)

        for response in openai.ChatCompletion.create(
            model = st.session_state["openai_model"],
            messages = [
                {"role": "system", "content": prom},
                {"role": "user", "content": error_code}
            ],
            stream = True,
        ):
            full_response += response.choices[0].delta.get("content", "")
            # message_placeholder.markdown(full_response + " ")
        # message_placeholder.markdown(full_response)
        return full_response

    # 関数response_generation_dummy：解説生成なし、api使用なし
    # 引数error_code: コード＋エラー文
    # 引数prom: システムへのプロンプト
    # 返り値　full_response: 決めうちの解説
    def response_generation_dummy(error_code, prom):
        print("response_generation_dummy")
        error_code += "\nプログラムのエラーを説明してください"
        print(error_code)

        full_response = "APIを節約中です。self_sys_promptは「"
        full_response += prom
        full_response += "」です。"
        return full_response

    # 関数append_to_file：指定したファイルに書き込む
    # 引数text:書き込む内容
    # 引数file_path:書き込むファイルのパス
    def append_to_file(text, file_path):
        # 'a'モードはファイルが存在する場合に追記し、存在しない場合は新しいファイルを作成
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(str(text) + '\n')

    # 関数file_jdoo：アップロードしたファイルをjavacし、関数response_generationを呼び出す
    # 引数java_code_d:ファイルの中身そのまま
    # 引数string_data_d_j:ファイルの中身string化
    # 返り値string_data_d_j:コード＋エラー文
    # 返り値sys_response_d:コンパイル結果を元にした解説結果
    def file_jdoo(java_code_d, string_data_d_j):
        print("JDoodle")

        # 応答履歴格納用変数
        sys_response_d = ""

        # JDoodle APIにリクエストを送信
        api_url = "https://api.jdoodle.com/v1/execute"
        data = {
            "script": string_data_d_j,
            "language": "java",
            "versionIndex": "3",  # Javaバージョン（3 = JDK 1.8.0_66）
            "clientId": JDoodle_Client_ID,
            "clientSecret": JDoodle_Client_Secret
        }
        
        # Jdoodle結果
        response = requests.post(api_url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            output = result.get("output", "No output")
            # st.code(output, language="text")

            # コンパイルエラーのチェック
            if "error" in result['output'].lower():
                # st.write("コンパイルエラー発生！")
                string_data_d_j += result['output']

                # gptへの入力格納用変数
                java_code_d += result['output']
                java_code_d += "\n"

                # user_prompt
                # java_code_d += "プログラムのエラーを説明してください"
                sys_response_d = response_generation(java_code_d, self_sys_prompt)
            else:
                sys_response_d += "❤️コンパイル成功❤️\n"
                sys_response_d += result['output']
            
        else:
            st.write(f"Error: {response.status_code}")
            sys_response_d += "何らかのトラブルが発生しました"

        return string_data_d_j, sys_response_d

    # 関数file_jdoo_dummy：アップロードしたファイルをjavacわざとしない
    # 引数java_code_d:ファイルの中身
    # 引数string_data_d_j:ファイルの中身string化
    # 返り値nyuryoku:ファイルの中身＋ダミー結果
    # 返り値sys_response_d:コンパイル結果を元にした解説結果、ではなくダミーの文言
    def file_jdoo_dummy(java_code_d, string_data_d_j):
        print("file_jdoo_dummy")
        # 応答履歴格納用変数
        sys_response_d = "\njdoodle節約したいからコンパイルしませんの"
        java_code_d += sys_response_d

        sys_response_d = response_generation_dummy(java_code_d, self_sys_prompt)

        nyuryoku = java_code_d
        return nyuryoku, sys_response_d

    # 関数file_check: ファイルの中身をチェック、同じだったら警告
    # 引数java_code_d:ファイルの中身
    # 返り値tf:True or false
    def file_check(java_code_d):
        if java_code_d in st.session_state.input_history:
            tf = True
            # st.warning("過去にも同じファイルが入力されましたよ")
        else:
            tf = False
            # st.success("新しいファイルがアップロードされました")

        st.session_state.input_history.append(java_code_d)

        return tf

    # 関数prom_hyouzi: 選択したプロンプトに対応するボタン名を取得
    # 引数self_sys_prompt_d: その時のself_sys_prompt_d
    # 返り値ppp_d:簡潔に教えて", "もう少し教えて", "色々知りたい"のどれか
    def prom_hyouzi(self_sys_prompt_d):
        ppp_d = ""
        if self_sys_prompt_d == my_dict[list(my_dict.keys())[0]]:
            ppp_d = list(my_dict.keys())[0]
        elif self_sys_prompt_d == my_dict[list(my_dict.keys())[1]]:
            ppp_d = list(my_dict.keys())[1]
        else:
            ppp_d = list(my_dict.keys())[2]
        return ppp_d

    # 関数safe_filename: ファイル名として安全な文字列に変換する関数
    # 引数input_string: ファイル名にしたい変数
    # 返り値: 最終的なファイル名
    def safe_filename(input_string):
        # 使用できない文字を置換（例：スラッシュやコロンをアンダースコアに置換）
        # None の場合は明示的にエラーを発生させる
        if input_string is None:
            raise ValueError("input_string に None が渡されました。値を確認してください。")
        # 文字列に変換して不正な文字を置換
        return re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', str(input_string))

    # アップロードされたファイルをjdoodleでjavac
    # if uploaded_file:

    # 実行ボタン
    if st.sidebar.button("解説生成"):
        # 日本のタイムゾーンを取得
        japan_timezone = pytz.timezone('Asia/Tokyo')
        japan_time = datetime.now(japan_timezone)
        japan_time_str = japan_time.strftime('%Y-%m-%d %H:%M:%S')

        if uploaded_file is not None:
            
            java_code = uploaded_file.read().decode("utf-8")

            # ファイルの中身をチェック
            che = file_check(java_code)

            if (che):
                # print("お　な　じ　フ　ァ　イ　ル")

                stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
                string_data = stringio.read()

                # プロンプトに対応するボタン名取得
                ppp = prom_hyouzi(self_sys_prompt)

                user_nyuryoku = st.session_state.code_compile

                # ここを変更
                # sys_response = response_generation_dummy(user_nyuryoku, self_sys_prompt)
                sys_response = response_generation(user_nyuryoku, self_sys_prompt)

                
            else:

                stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
                string_data = stringio.read()

                # プロンプトに対応するボタン名取得
                ppp = prom_hyouzi(self_sys_prompt)

                # 応答履歴格納用変数
                sys_response = ""

                # ユーザーの入力格納
                user_nyuryoku = ""

                # ここを変更

                # javacして、解説生成
                user_nyuryoku, sys_response = file_jdoo(java_code, string_data)

                # javacしない、解説も生成しない
                # user_nyuryoku, sys_response = file_jdoo_dummy(java_code, string_data)

                st.session_state.code_compile = user_nyuryoku

        else:
            st.warning("ファイルをアップロードしてください。")
            
        temp = "使用ID   : " + st.session_state.user_id + "\n使用日時　: " + japan_time_str + "\n使用ボタン: " + ppp + "\nファイル名: " + uploaded_file.name +"\n"
        temp += "------------------------------------------------------------\n"
        user_nyuryoku =  temp + user_nyuryoku

        st.session_state.chat_history.append({"role": "assistant", "content": sys_response})
        st.session_state.chat_history.append({"role": "user", "content": user_nyuryoku})

        # ダウンロードファイル書き込み
        st.session_state.down_log.append("")
        st.session_state.down_log.append(user_nyuryoku)
        st.session_state.down_log.append("")
        st.session_state.down_log.append("解説：")
        st.session_state.down_log.append(sys_response)
        st.session_state.down_log.append("")
        st.session_state.down_log.append("#############################################################")
        st.session_state.down_log.append("#############################################################")

    # 入力内容をテキスト形式に変換
    down_log = "\n".join(st.session_state.down_log)
    filename = safe_filename(st.session_state.user_id) + ".txt"

    st.sidebar.write("· · • • • ✤ • • • · ·· · • • • ✤ • • • · ·· · • • • ✤ • • •  ")

    st.sidebar.download_button(
        label="履歴ダウンロード",
        data = down_log,
        file_name = filename
    )

    # 最新のメッセージを取得
    last_user_message = None
    last_assistant_message = None

    for message in reversed(st.session_state.chat_history):

        if message["role"] == "assistant" and last_assistant_message is None:
            last_assistant_message = message
        elif message["role"] == "user" and last_user_message is None:
            last_user_message = message
        
        if last_user_message and last_assistant_message:
            break

    # 会話履歴を新しい順に表示
    for message in reversed(st.session_state.chat_history):
        
        if message["role"] == "user":
            if message == last_user_message:
                # st.image("./images/44ki3.png", width = 170)
                st.code(message["content"], language='java')
                last_user_message = None
            else:
                st.code(message["content"], language='java')
                
        if message["role"] == "assistant":
            if message == last_assistant_message:
                st.write(message["content"])
                st.write("----------------------------")
                
                last_assistant_message = None
            else:
                st.write(message["content"])
                st.write("----------------------------")

# 状態保持する変数を作成して確認
if ("page_control" in st.session_state and
   st.session_state["page_control"] == 1):
    next_page()
else:
    st.session_state["page_control"] = 0
    main()
