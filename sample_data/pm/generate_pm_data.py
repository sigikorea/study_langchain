"""
PM 합성데이터 생성 스크립트
- pm_projects.xlsx (3 sheets)
- pm.db (SQLite, 4 tables)
seed: 42
"""

import sqlite3
import random
from pathlib import Path
from datetime import date, timedelta

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
random.seed(42)

BASE = Path(__file__).parent
DB_PATH = BASE / "pm.db"
XL_PATH = BASE / "pm_projects.xlsx"

# ── 공통 풀 ──────────────────────────────────────────────────────────────────
DEPARTMENTS = ["IT개발팀", "경영지원팀", "품질관리팀", "데이터팀", "인프라팀"]
PROJECT_STATUSES = ["진행중", "완료", "지연", "보류"]
RISK_LEVELS = ["낮음", "중간", "높음"]
ROLES = ["PM", "개발자", "디자이너", "QA엔지니어", "데이터분석가", "인프라엔지니어", "기획자"]
POSITIONS = ["사원", "대리", "과장", "차장", "부장"]
SKILL_SETS = [
    "Python, SQL, LangChain",
    "Java, Spring, Kubernetes",
    "React, TypeScript, Figma",
    "Selenium, JUnit, Pytest",
    "Spark, Airflow, dbt",
    "Terraform, AWS, Linux",
    "기획, PPT, Notion",
]

START_DATE = date(2025, 1, 1)
END_DATE_MAX = date(2025, 4, 30)


def rand_date(start: date, end: date) -> str:
    delta = (end - start).days
    return (start + timedelta(days=int(rng.integers(0, delta + 1)))).strftime(
        "%Y-%m-%d"
    )


def rand_date_after(d_str: str, max_date: date) -> str:
    d = date.fromisoformat(d_str)
    if d >= max_date:
        return max_date.strftime("%Y-%m-%d")
    return rand_date(d, max_date)


# ── 한국어 이름 풀 ────────────────────────────────────────────────────────────
SURNAMES = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임"]
GIVEN = [
    "민준", "서연", "지호", "수빈", "현우", "지은", "태양", "하은", "준서", "예린",
    "동현", "미래", "성민", "유나", "재원", "소희", "진우", "아름", "승현", "나영",
    "경훈", "지수", "민혁", "채원", "건우", "혜진", "우진", "수연", "태민", "보라",
    "혁준", "서현", "지원", "민지", "준혁", "다연", "시우", "은지", "재현", "하늘",
]


def make_name(idx: int) -> str:
    return SURNAMES[idx % len(SURNAMES)] + GIVEN[idx % len(GIVEN)]


MEMBER_NAMES = [make_name(i) for i in range(50)]

PROJECT_NAMES = [
    "ERP 시스템 고도화", "AI 챗봇 플랫폼 구축", "데이터 레이크 구성", "보안 취약점 점검",
    "클라우드 마이그레이션", "고객 포털 리뉴얼", "HR 자동화 시스템", "품질 모니터링 대시보드",
    "DevOps 파이프라인 구축", "디지털 전환 로드맵", "모바일 앱 개발", "재고 관리 최적화",
    "인프라 비용 절감", "API 게이트웨이 구축", "MLOps 플랫폼 도입", "내부 감사 시스템",
    "공급망 가시화", "RPA 도입 프로젝트", "사용자 경험 개선", "데이터 거버넌스 수립",
    "마케팅 분석 플랫폼", "컴플라이언스 관리", "지식 관리 시스템", "스마트 오피스 구축",
    "성과 관리 시스템", "AI 기반 수요 예측", "네트워크 보안 강화", "셀프서비스 BI 도입",
    "레거시 시스템 교체", "통합 알림 시스템",
]


# ════════════════════════════════════════════════════════════════════════════
# 1. Excel 데이터
# ════════════════════════════════════════════════════════════════════════════

# ── 시트1: 프로젝트현황 (30 rows) ──────────────────────────────────────────
n_proj = 30
project_ids = [f"PRJ-{i+1:03d}" for i in range(n_proj)]

proj_status_vals = (
    ["진행중"] * 14 + ["완료"] * 8 + ["지연"] * 5 + ["보류"] * 3
)
rng.shuffle(proj_status_vals)

start_dates = [rand_date(START_DATE, date(2025, 3, 31)) for _ in range(n_proj)]
end_dates = [rand_date_after(sd, END_DATE_MAX) for sd in start_dates]

df_projects = pd.DataFrame(
    {
        "project_id": project_ids,
        "project_name": PROJECT_NAMES,
        "department": rng.choice(DEPARTMENTS, n_proj).tolist(),
        "manager": [MEMBER_NAMES[i] for i in range(n_proj)],
        "start_date": start_dates,
        "end_date": end_dates,
        "budget_million": rng.integers(50, 500, n_proj).tolist(),
        "spent_million": rng.integers(10, 450, n_proj).tolist(),
        "progress_pct": rng.integers(0, 101, n_proj).tolist(),
        "status": proj_status_vals,
        "risk_level": rng.choice(RISK_LEVELS, n_proj).tolist(),
    }
)
# 완료 프로젝트는 progress 100%
df_projects.loc[df_projects["status"] == "완료", "progress_pct"] = 100

# ── 시트2: 월별실적 (120 rows = 30 × 4) ──────────────────────────────────
months = ["2025-01", "2025-02", "2025-03", "2025-04"]
monthly_rows = []
for pid in project_ids:
    for m in months:
        planned = int(rng.integers(5, 25))
        completed = int(rng.integers(0, planned + 1))
        monthly_rows.append(
            {
                "project_id": pid,
                "month": m,
                "planned_tasks": planned,
                "completed_tasks": completed,
                "issues_count": int(rng.integers(0, 10)),
                "man_hours": int(rng.integers(40, 320)),
            }
        )
df_monthly = pd.DataFrame(monthly_rows)

# ── 시트3: 리소스배분 (50 rows) ───────────────────────────────────────────
resource_rows = []
used_project_ids = rng.choice(project_ids, 50).tolist()
for i, pid in enumerate(used_project_ids):
    resource_rows.append(
        {
            "project_id": pid,
            "member_name": MEMBER_NAMES[(i + 5) % len(MEMBER_NAMES)],
            "role": rng.choice(ROLES),
            "allocation_pct": int(rng.integers(20, 101, dtype=int)),
            "skill_set": rng.choice(SKILL_SETS),
        }
    )
df_resources = pd.DataFrame(resource_rows)

# ── Excel 저장 ────────────────────────────────────────────────────────────
with pd.ExcelWriter(XL_PATH, engine="openpyxl") as writer:
    df_projects.to_excel(writer, sheet_name="프로젝트현황", index=False)
    df_monthly.to_excel(writer, sheet_name="월별실적", index=False)
    df_resources.to_excel(writer, sheet_name="리소스배분", index=False)

print(f"[OK] Excel saved → {XL_PATH}")
print(f"     프로젝트현황: {len(df_projects)} rows")
print(f"     월별실적:     {len(df_monthly)} rows")
print(f"     리소스배분:   {len(df_resources)} rows")


# ════════════════════════════════════════════════════════════════════════════
# 2. SQLite 데이터
# ════════════════════════════════════════════════════════════════════════════
if DB_PATH.exists():
    DB_PATH.unlink()

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ── members (30 rows) ─────────────────────────────────────────────────────
cur.execute(
    """
    CREATE TABLE members (
        member_id   TEXT PRIMARY KEY,
        name        TEXT,
        department  TEXT,
        position    TEXT,
        email       TEXT,
        join_date   TEXT
    )
"""
)
member_rows = []
for i in range(30):
    name = MEMBER_NAMES[i]
    dept = DEPARTMENTS[i % len(DEPARTMENTS)]
    pos = POSITIONS[i % len(POSITIONS)]
    email = f"user{i+1:02d}@sk.com"
    join_d = rand_date(date(2015, 1, 1), date(2024, 12, 31))
    member_rows.append((f"MBR-{i+1:03d}", name, dept, pos, email, join_d))
cur.executemany("INSERT INTO members VALUES (?,?,?,?,?,?)", member_rows)

# ── tasks (200 rows) ──────────────────────────────────────────────────────
TASK_TITLES = [
    "요구사항 분석", "설계 문서 작성", "DB 스키마 설계", "API 개발",
    "프론트엔드 개발", "단위 테스트", "통합 테스트", "배포 준비",
    "성능 최적화", "보안 검토", "코드 리뷰", "사용자 교육",
    "운영 이관", "버그 수정", "문서화",
]
TASK_STATUSES = ["할일", "진행중", "완료", "보류"]
PRIORITIES = ["낮음", "중간", "높음", "긴급"]

cur.execute(
    """
    CREATE TABLE tasks (
        task_id         TEXT PRIMARY KEY,
        project_id      TEXT,
        title           TEXT,
        assignee        TEXT,
        status          TEXT,
        priority        TEXT,
        created_date    TEXT,
        due_date        TEXT,
        completed_date  TEXT
    )
"""
)
task_rows = []
for i in range(200):
    pid = rng.choice(project_ids)
    created = rand_date(START_DATE, date(2025, 4, 15))
    due = rand_date_after(created, END_DATE_MAX)
    t_status = rng.choice(TASK_STATUSES)
    completed = rand_date_after(created, date.fromisoformat(due)) if t_status == "완료" else None
    task_rows.append(
        (
            f"TSK-{i+1:04d}",
            pid,
            rng.choice(TASK_TITLES),
            MEMBER_NAMES[int(rng.integers(0, 30))],
            t_status,
            rng.choice(PRIORITIES),
            created,
            due,
            completed,
        )
    )
cur.executemany("INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?)", task_rows)

# ── issues (80 rows) ──────────────────────────────────────────────────────
ISSUE_TITLES = [
    "배포 후 오류 발생", "성능 저하 문제", "보안 취약점 발견", "데이터 정합성 오류",
    "UI 렌더링 버그", "API 응답 지연", "인증 오류", "데이터 누락",
    "통합 테스트 실패", "환경 설정 오류", "메모리 누수", "로그인 불가",
    "파일 업로드 실패", "권한 설정 오류", "배치 작업 실패",
]
SEVERITIES = ["낮음", "중간", "높음", "긴급"]
ISSUE_STATUSES = ["미처리", "처리중", "완료", "보류"]

cur.execute(
    """
    CREATE TABLE issues (
        issue_id        TEXT PRIMARY KEY,
        project_id      TEXT,
        title           TEXT,
        reporter        TEXT,
        severity        TEXT,
        status          TEXT,
        created_date    TEXT,
        resolved_date   TEXT
    )
"""
)
issue_rows = []
for i in range(80):
    pid = rng.choice(project_ids)
    created = rand_date(START_DATE, date(2025, 4, 20))
    i_status = rng.choice(ISSUE_STATUSES)
    resolved = rand_date_after(created, END_DATE_MAX) if i_status == "완료" else None
    issue_rows.append(
        (
            f"ISS-{i+1:04d}",
            pid,
            rng.choice(ISSUE_TITLES),
            MEMBER_NAMES[int(rng.integers(0, 30))],
            rng.choice(SEVERITIES),
            i_status,
            created,
            resolved,
        )
    )
cur.executemany("INSERT INTO issues VALUES (?,?,?,?,?,?,?,?)", issue_rows)

# ── meetings (60 rows) ────────────────────────────────────────────────────
MEETING_TITLES = [
    "주간 현황 보고", "스프린트 플래닝", "스프린트 리뷰", "회고 미팅",
    "리스크 검토 회의", "이해관계자 보고", "설계 검토 회의", "배포 승인 회의",
    "요구사항 확인 회의", "킥오프 미팅",
]
DECISIONS_POOL = [
    "다음 주까지 API 설계 완료 예정",
    "테스트 커버리지 80% 이상 확보 필요",
    "보안 검토 일정 2주 앞당기기로 결정",
    "추가 인력 투입 검토 중",
    "배포 일정 1주 연기",
    "요구사항 재검토 필요",
    "QA 환경 별도 구성 결정",
    "주간 보고 양식 변경 합의",
    "위험 항목 에스컬레이션 절차 수립",
    "스프린트 길이 2주로 고정",
]

cur.execute(
    """
    CREATE TABLE meetings (
        meeting_id      TEXT PRIMARY KEY,
        project_id      TEXT,
        title           TEXT,
        date            TEXT,
        duration_min    INTEGER,
        attendees       TEXT,
        decisions       TEXT
    )
"""
)
meeting_rows = []
for i in range(60):
    pid = rng.choice(project_ids)
    attendee_count = int(rng.integers(3, 9))
    attendees = ", ".join(
        MEMBER_NAMES[j % len(MEMBER_NAMES)]
        for j in rng.integers(0, 30, attendee_count).tolist()
    )
    meeting_rows.append(
        (
            f"MTG-{i+1:04d}",
            pid,
            rng.choice(MEETING_TITLES),
            rand_date(START_DATE, END_DATE_MAX),
            int(rng.choice([30, 60, 90, 120])),
            attendees,
            rng.choice(DECISIONS_POOL),
        )
    )
cur.executemany("INSERT INTO meetings VALUES (?,?,?,?,?,?,?)", meeting_rows)

conn.commit()
conn.close()

print(f"\n[OK] SQLite saved → {DB_PATH}")
print(f"     members:  {len(member_rows)} rows")
print(f"     tasks:    {len(task_rows)} rows")
print(f"     issues:   {len(issue_rows)} rows")
print(f"     meetings: {len(meeting_rows)} rows")


# ════════════════════════════════════════════════════════════════════════════
# 3. Verification
# ════════════════════════════════════════════════════════════════════════════
conn2 = sqlite3.connect(DB_PATH)
for tbl in ["members", "tasks", "issues", "meetings"]:
    cnt = conn2.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    print(f"     [verify] {tbl}: {cnt} rows")
conn2.close()

xl = pd.ExcelFile(XL_PATH)
for sh in xl.sheet_names:
    df_tmp = xl.parse(sh)
    print(f"     [verify] sheet '{sh}': {len(df_tmp)} rows")
