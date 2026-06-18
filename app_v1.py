"""
AI Agent Chat - Version 3
LangChain + Streamlit 기반 Chat UI
+ MES / ERM / Edit 3개 탭 분리
+ 각 탭별 독립적 대화 히스토리
+ Edit 탭: 파일 업로드/수정/다운로드
"""

import os
import openai
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import json
import csv
import io
import xlwings as xw
import tempfile
import os as os_module

# ─────────────────────────────────────────
# 환경변수 로드
# ─────────────────────────────────────────
load_dotenv(override=True)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ─────────────────────────────────────────
# 설정
# ─────────────────────────────────────────
def get_system_prompt(model_name: str) -> str:
    return f"당신은 친절한 AI 어시스턴트입니다. 한국어로 답변해 주세요. 당신이 사용 중인 모델은 {model_name}입니다."

st.set_page_config(
    page_title="AI Agent Chat",
    page_icon="🤖",
    layout="wide",
)

# ─────────────────────────────────────────
# 사용 가능한 모델 목록 조회
# ─────────────────────────────────────────
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

# ─────────────────────────────────────────
# 모델 초기화
# ─────────────────────────────────────────
@st.cache_resource
def get_model(model_name: str):
    return ChatOpenAI(
        model=model_name,
        temperature=0.7,
        api_key=OPENAI_API_KEY,
    )

# ─────────────────────────────────────────
# 세션 상태 초기화
# ─────────────────────────────────────────
if "mes_messages" not in st.session_state:
    st.session_state.mes_messages = []

if "erm_messages" not in st.session_state:
    st.session_state.erm_messages = []

if "general_messages" not in st.session_state:
    st.session_state.general_messages = []

if "edit_messages" not in st.session_state:
    st.session_state.edit_messages = []

if "current_tab" not in st.session_state:
    st.session_state.current_tab = "PIS"

if "uploaded_file_content" not in st.session_state:
    st.session_state.uploaded_file_content = None

if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None

# ─────────────────────────────────────────
# 헬퍼 함수
# ─────────────────────────────────────────
def get_current_messages():
    """현재 탭의 메시지 리스트 반환"""
    if st.session_state.current_tab == "PIS":
        return st.session_state.mes_messages
    elif st.session_state.current_tab == "ERM":
        return st.session_state.erm_messages
    elif st.session_state.current_tab == "일반":
        return st.session_state.general_messages
    else:  # Edit
        return st.session_state.edit_messages

def read_excel_with_xlwings(file_path: str) -> str:
    """xlwings로 DRM 보안 엑셀 파일 읽기"""
    try:
        wb = xw.Book(file_path)
        content = "# Excel 파일 내용\n\n"
        
        for sheet_idx, sheet in enumerate(wb.sheets):
            content += f"## Sheet: {sheet.name}\n"
            
            # 사용된 범위 찾기
            used_range = sheet.used_range
            if used_range:
                data = used_range.value
                content += f"```\n{data}\n```\n\n"
        
        wb.close()
        return content
    except Exception as e:
        return f"⚠️ xlwings로 엑셀 읽기 실패: {str(e)}"

def read_file_content(file_path: str, file_name: str) -> str:
    """파일 타입별 콘텐츠 읽기"""
    file_ext = file_name.split('.')[-1].lower()
    
    if file_ext in ['xlsx', 'xls']:
        return read_excel_with_xlwings(file_path)
    elif file_ext == 'pdf':
        return "⚠️ PDF 처리는 향후 지원 예정입니다."
    elif file_ext == 'csv':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f"# CSV 파일 내용\n```\n{f.read()}\n```"
    elif file_ext == 'txt':
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f"# 텍스트 파일 내용\n```\n{f.read()}\n```"
    else:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f"# 파일 내용\n```\n{f.read()}\n```"

# ─────────────────────────────────────────
# 사이드바 — 탭 선택
# ─────────────────────────────────────────
with st.sidebar:
    st.title("📋 채팅 도메인")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏭 PIS", use_container_width=True, 
                     type="primary" if st.session_state.current_tab == "PIS" else "secondary"):
            st.session_state.current_tab = "PIS"
            st.rerun()
    
    with col2:
        if st.button("⚙️ ERM", use_container_width=True,
                     type="primary" if st.session_state.current_tab == "ERM" else "secondary"):
            st.session_state.current_tab = "ERM"
            st.rerun()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🟢 일반", use_container_width=True,
                     type="primary" if st.session_state.current_tab == "일반" else "secondary"):
            st.session_state.current_tab = "일반"
            st.rerun()
    
    with col2:
        if st.button("✏️ Edit", use_container_width=True,
                     type="primary" if st.session_state.current_tab == "Edit" else "secondary"):
            st.session_state.current_tab = "Edit"
            st.rerun()

# ─────────────────────────────────────────
# 메인 — 타이틀 + 모델 선택 (Edit 탭 제외)
# ─────────────────────────────────────────
if st.session_state.current_tab != "Edit":
    st.title(f"🤖 AI Agent Chat - [{st.session_state.current_tab}]")

    available_models = fetch_available_models()

    col1, col2 = st.columns([3, 1])
    with col1:
        selected_model = st.selectbox(
            label="모델 선택",
            label_visibility="collapsed",
            options=available_models,
            index=available_models.index("gpt-4o-mini") if "gpt-4o-mini" in available_models else 0,
        )
    with col2:
        if st.button("🗑️ 초기화", use_container_width=True):
            current_messages = get_current_messages()
            current_messages.clear()
            st.rerun()

    st.divider()

    model = get_model(selected_model)

    # 현재 탭의 메시지 가져오기
    current_messages = get_current_messages()

    # ─────────────────────────────────────────
    # 메인 — 채팅 메시지 표시
    # ─────────────────────────────────────────
    for msg in current_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # ─────────────────────────────────────────
    # 메인 — 채팅 입력
    # ─────────────────────────────────────────
    if prompt := st.chat_input("메시지를 입력하세요..."):

        with st.chat_message("user"):
            st.write(prompt)
        current_messages.append({"role": "user", "content": prompt})

        lc_messages = [SystemMessage(content=get_system_prompt(selected_model))]

        for msg in current_messages:
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            else:
                lc_messages.append(AIMessage(content=msg["content"]))

        with st.chat_message("assistant"):
            with st.spinner("생각 중..."):
                response = model.invoke(lc_messages)
                answer = response.content
            st.write(answer)

        current_messages.append({"role": "assistant", "content": answer})
        st.rerun()

else:  # Edit 탭
    st.title("✏️ 파일 수정 & 분석")
    
    st.subheader("파일 업로드")
    st.info("지원 형식: Excel (.xlsx, .xls - DRM 보안 처리), CSV, TXT, PDF (향후 지원)")
    uploaded_file = st.file_uploader("파일을 선택하세요", type=None)
    
    if uploaded_file is not None:
        st.session_state.uploaded_file_name = uploaded_file.name
        file_ext = uploaded_file.name.split('.')[-1].lower()
        
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            tmp_path = tmp_file.name
        
        try:
            # 파일 타입별 처리
            if file_ext in ['xlsx', 'xls']:
                st.success(f"✅ Excel 파일 업로드: {uploaded_file.name}")
                with st.spinner("xlwings로 DRM 보안 엑셀 파일을 읽는 중..."):
                    st.session_state.uploaded_file_content = read_excel_with_xlwings(tmp_path)
            elif file_ext == 'pdf':
                st.warning(f"⚠️ PDF 처리는 향후 지원 예정입니다: {uploaded_file.name}")
                st.session_state.uploaded_file_content = None
            elif file_ext in ['csv', 'txt']:
                st.success(f"✅ 파일 업로드: {uploaded_file.name}")
                st.session_state.uploaded_file_content = read_file_content(tmp_path, uploaded_file.name)
            else:
                st.success(f"✅ 파일 업로드: {uploaded_file.name}")
                st.session_state.uploaded_file_content = read_file_content(tmp_path, uploaded_file.name)
            
            if st.session_state.uploaded_file_content:
                st.text_area("파일 내용 미리보기", st.session_state.uploaded_file_content, height=250, disabled=True)
        
        finally:
            # 임시 파일 삭제
            try:
                os_module.remove(tmp_path)
            except:
                pass
    
    st.divider()
    
    if st.session_state.uploaded_file_content and "향후 지원" not in st.session_state.uploaded_file_content:
        available_models = fetch_available_models()
        selected_model = st.selectbox(
            label="모델 선택",
            label_visibility="collapsed",
            options=available_models,
            index=available_models.index("gpt-4o-mini") if "gpt-4o-mini" in available_models else 0,
            key="edit_model"
        )
        
        model = get_model(selected_model)
        
        st.subheader("파일 분석 & 요청")
        
        current_messages = get_current_messages()
        
        for msg in current_messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        
        edit_prompt = st.chat_input("파일을 어떻게 수정/분석할까요?")
        
        if edit_prompt:
            with st.chat_message("user"):
                st.write(edit_prompt)
            current_messages.append({"role": "user", "content": edit_prompt})
            
            file_context = f"""
업로드된 파일: {st.session_state.uploaded_file_name}
파일 내용:
{st.session_state.uploaded_file_content}

사용자 요청: {edit_prompt}
"""
            
            lc_messages = [
                SystemMessage(content=f"당신은 파일 수정 및 분석 전문가입니다. 파일을 수정하거나 분석하고 결과를 명확하게 제시해주세요. 수정된 코드나 데이터는 코드 블록으로 감싸서 보여주세요. 한국어로 답변해주세요."),
                HumanMessage(content=file_context)
            ]
            
            with st.chat_message("assistant"):
                with st.spinner("분석 중..."):
                    response = model.invoke(lc_messages)
                    answer = response.content
                st.write(answer)
            
            current_messages.append({"role": "assistant", "content": answer})
            st.rerun()