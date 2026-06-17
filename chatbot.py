import os
import openai
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

load_dotenv(override=True)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def get_system_prompt(model_name: str) -> str:
    return f"당신은 친절한 AI 어시스턴트입니다. 한국어로 답변해 주세요. 당신이 사용 중인 모델은 {model_name}입니다."

@st.cache_data
def fetch_available_models():
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        resp = client.models.list()
        models = [m.id for m in resp.data if "gpt" in m.id]
        models.sort()
        return models
    except Exception as e:
        st.warning(f"모델 목록 조회 실패: {e}")
        return ["gpt-4o-mini"]

@st.cache_resource
def get_model(model_name: str):
    return ChatOpenAI(
        model=model_name,
        temperature=0.7,
        api_key=OPENAI_API_KEY,
    )

def init_chat_state():
    if "conversations" not in st.session_state:
        st.session_state.conversations = []

    if "current_id" not in st.session_state:
        st.session_state.current_id = None

    if not st.session_state.conversations:
        new_conversation()

def new_conversation():
    conv_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.conversations.append({
        "id": conv_id,
        "title": "새 대화",
        "messages": [],
        "created_at": datetime.now().strftime("%m/%d %H:%M"),
    })
    st.session_state.current_id = conv_id

def get_current_conv():
    for conv in st.session_state.conversations:
        if conv["id"] == st.session_state.current_id:
            return conv
    return None

def update_title(conv, first_message: str):
    if conv["title"] == "새 대화":
        conv["title"] = first_message[:20] + ("..." if len(first_message) > 20 else "")

def render_chatbot():
    init_chat_state()
    current_conv = get_current_conv()

    with st.sidebar:
        st.title("💬 대화 목록")

        if st.button("➕ 새 대화", use_container_width=True):
            new_conversation()
            st.rerun()

        st.divider()

        for conv in reversed(st.session_state.conversations):
            is_active = conv["id"] == st.session_state.current_id
            col_btn, col_del = st.columns([5, 1])
            with col_btn:
                if st.button(
                    f"{'▶ ' if is_active else ''}{conv['title']}",
                    key=f"conv_{conv['id']}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    st.session_state.current_id = conv["id"]
                    st.rerun()
            with col_del:
                if st.button("🗑", key=f"del_{conv['id']}"):
                    st.session_state.conversations = [
                        c for c in st.session_state.conversations if c["id"] != conv["id"]
                    ]
                    if st.session_state.conversations:
                        st.session_state.current_id = st.session_state.conversations[-1]["id"]
                    else:
                        new_conversation()
                    st.rerun()

    st.title("🤖 AI Agent Chat")

    available_models = fetch_available_models()

    col1, col2 = st.columns([3, 1])
    with col1:
        selected_model = st.selectbox(
            label="모델 선택",
            label_visibility="collapsed",
            options=available_models,
            index=available_models.index("gpt-4o-mini") if "gpt-4o-mini" in available_models else 0,
            key="selected_model",
        )
    with col2:
        if st.button("🗑️ 초기화", use_container_width=True):
            current_conv["messages"] = []
            current_conv["title"] = "새 대화"
            st.rerun()

    st.divider()

    model = get_model(selected_model)

    for msg in current_conv["messages"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("메시지를 입력하세요..."):
        with st.chat_message("user"):
            st.write(prompt)
        current_conv["messages"].append({"role": "user", "content": prompt})
        update_title(current_conv, prompt)

        lc_messages = [SystemMessage(content=get_system_prompt(selected_model))]
        for msg in current_conv["messages"]:
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            else:
                lc_messages.append(AIMessage(content=msg["content"]))

        with st.chat_message("assistant"):
            with st.spinner("생각 중..."):
                response = model.invoke(lc_messages)
                answer = response.content
            st.write(answer)

        current_conv["messages"].append({"role": "assistant", "content": answer})
        st.rerun()