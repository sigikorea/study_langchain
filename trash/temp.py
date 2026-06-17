import os
import sys
from dotenv import load_dotenv
import openai


def list_models():
    load_dotenv(override=True)  # .env 파일에서 환경변수 로드
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # API 키 가져오기

    if not OPENAI_API_KEY:
        print("환경변수 OPENAI_API_KEY가 설정되어 있지 않습니다. .env 또는 환경변수를 확인하세요.")
        sys.exit(1)

    openai.api_key = OPENAI_API_KEY

    try:
        resp = openai.Model.list()
        models = resp.get("data", [])
        if not models:
            print("사용 가능한 모델이 없습니다.")
            return

        print(f"총 {len(models)}개 모델 발견:")
        for m in models:
            mid = m.get("id", "<no-id>")
            owned = m.get("owned_by", "")
            desc = m.get("description") or m.get("permission", "") or ""
            print(f"- {mid}  (owned_by={owned})")
    except Exception as e:
        print("모델 조회 중 오류가 발생했습니다:", str(e))
        sys.exit(2)


if __name__ == "__main__":
    list_models()
