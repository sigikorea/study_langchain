import os
import shutil
import streamlit as st
from pathlib import Path

def render_file_sorter():
    st.title("📁 파일 정리 프로그램")

    st.write("파일을 확장자별로 정리하는 예시입니다.")

    source_dir = st.text_input("정리할 폴더 경로를 입력하세요")
    target_dir = st.text_input("정리된 파일을 저장할 폴더 경로를 입력하세요")

    if st.button("파일 정리 시작"):
        if not source_dir or not target_dir:
            st.error("폴더 경로를 모두 입력하세요.")
            return

        source_path = Path(source_dir)
        target_path = Path(target_dir)

        if not source_path.exists():
            st.error("원본 폴더가 존재하지 않습니다.")
            return

        target_path.mkdir(parents=True, exist_ok=True)

        count = 0
        for file in source_path.iterdir():
            if file.is_file():
                ext = file.suffix[1:] if file.suffix else "no_extension"
                folder = target_path / ext
                folder.mkdir(exist_ok=True)
                shutil.move(str(file), str(folder / file.name))
                count += 1

        st.success(f"{count}개의 파일을 정리했습니다.")