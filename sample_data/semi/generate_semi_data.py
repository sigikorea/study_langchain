"""
반도체 공정 합성데이터 생성 스크립트
- semi_yield.xlsx (3 sheets)
- semi.db (SQLite, 4 tables)
seed: 42
"""

import sqlite3
import random
from pathlib import Path
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
random.seed(42)

BASE = Path(__file__).parent
DB_PATH = BASE / "semi.db"
XL_PATH = BASE / "semi_yield.xlsx"

# ── 공통 풀 ──────────────────────────────────────────────────────────────────
PRODUCTS = ["HBM3E", "DDR5", "LPDDR5X", "NAND-V9"]
FABS = ["FAB-M16", "FAB-M17", "FAB-C1"]
PROCESS_STEPS = ["Etch", "Deposition", "CMP", "Lithography", "Implant"]
DEFECT_TYPES = ["Particle", "Scratch", "Pattern Defect", "Void", "Bridge"]
SEVERITIES = ["Critical", "Major", "Minor"]
EQUIPMENT_TYPES = ["Etcher", "CVD", "PVD", "CMP", "Stepper"]
PM_STATUSES = ["Normal", "PM예정", "PM진행중"]
MAINT_TYPES = ["PM", "BM", "교체"]

START_DATE = date(2025, 1, 1)
END_DATE = date(2025, 4, 30)

ENGINEERS = [
    "김민준", "이서연", "박지호", "최수빈", "정현우",
    "강지은", "조태양", "윤하은", "장준서", "임예린",
    "홍동현", "신미래", "오성민", "한유나", "권재원",
]

EQUIPMENT_MODELS = {
    "Etcher": ["LAM Versys", "AMAT Centris", "TEL Tactras"],
    "CVD": ["AMAT Producer", "Novellus Concept", "TEL Trias"],
    "PVD": ["AMAT Endura", "Ulvac Entron", "Canon Anelva"],
    "CMP": ["AMAT Reflexion", "Ebara F-REX", "Speedfam SFT"],
    "Stepper": ["ASML NXT1980", "ASML NXT2000", "Canon FPA-8300"],
}


def rand_date(start: date, end: date) -> str:
    delta = (end - start).days
    return (start + timedelta(days=int(rng.integers(0, delta + 1)))).strftime("%Y-%m-%d")


def rand_datetime(start: date, end: date) -> str:
    """Datetime with minute precision."""
    delta_days = (end - start).days
    base = datetime(start.year, start.month, start.day)
    minutes_total = delta_days * 24 * 60
    offset_min = int(rng.integers(0, minutes_total + 1))
    dt = base + timedelta(minutes=offset_min)
    return dt.strftime("%Y-%m-%d %H:%M")


def make_lot_id(d: date, seq: int) -> str:
    return f"LOT-{d.strftime('%Y%m%d')}-{seq:03d}"


# ════════════════════════════════════════════════════════════════════════════
# 1. Excel 데이터
# ════════════════════════════════════════════════════════════════════════════

# ── 시트1: Lot별수율 (100 rows) ──────────────────────────────────────────────
n_lots = 100
lot_dates = [
    date(2025, 1, 1) + timedelta(days=int(rng.integers(0, 119)))
    for _ in range(n_lots)
]
lot_seqs = list(range(1, n_lots + 1))
lot_ids = [make_lot_id(lot_dates[i], lot_seqs[i]) for i in range(n_lots)]

wafer_counts = rng.integers(20, 26, n_lots).tolist()
total_die_counts = rng.integers(1000, 1301, n_lots).tolist()
good_die_counts = [
    int(rng.integers(800, min(1201, total_die_counts[i] + 1)))
    for i in range(n_lots)
]
yield_pcts = [round(good_die_counts[i] / total_die_counts[i] * 100, 2) for i in range(n_lots)]
# Clamp to 75~98 range as specified
yield_pcts = [min(98.0, max(75.0, y)) for y in yield_pcts]

df_yield = pd.DataFrame({
    "lot_id": lot_ids,
    "product": rng.choice(PRODUCTS, n_lots).tolist(),
    "fab": rng.choice(FABS, n_lots).tolist(),
    "process_step": rng.choice(PROCESS_STEPS, n_lots).tolist(),
    "wafer_count": wafer_counts,
    "good_die_count": good_die_counts,
    "total_die_count": total_die_counts,
    "yield_pct": yield_pcts,
    "date": [d.strftime("%Y-%m-%d") for d in lot_dates],
})

# ── 시트2: 공정별불량 (200 rows) ─────────────────────────────────────────────
n_defect = 200
defect_lot_indices = rng.integers(0, n_lots, n_defect).tolist()
defect_rows = []
for i, li in enumerate(defect_lot_indices):
    defect_rows.append({
        "lot_id": lot_ids[li],
        "process_step": rng.choice(PROCESS_STEPS),
        "defect_type": rng.choice(DEFECT_TYPES),
        "defect_count": int(rng.integers(0, 51)),
        "severity": rng.choice(SEVERITIES),
        "date": lot_dates[li].strftime("%Y-%m-%d"),
    })
df_defect = pd.DataFrame(defect_rows)

# ── 시트3: 장비가동률 (150 rows) ─────────────────────────────────────────────
# Build equipment ID pool: 8 per type = 40 total
eq_pool = []
type_abbr = {"Etcher": "ETCH", "CVD": "CVD", "PVD": "PVD", "CMP": "CMP", "Stepper": "STEP"}
for eq_type in EQUIPMENT_TYPES:
    for j in range(1, 9):
        eq_pool.append((f"EQ-{type_abbr[eq_type]}-{j:03d}", eq_type))

n_util = 150
util_rows = []
for i in range(n_util):
    eq_id, eq_type = eq_pool[int(rng.integers(0, len(eq_pool)))]
    uptime = round(float(rng.uniform(16, 23.5)), 1)
    downtime = round(24.0 - uptime, 1)
    utilization = round(uptime / 24.0 * 100, 1)
    util_rows.append({
        "equipment_id": eq_id,
        "equipment_type": eq_type,
        "fab": rng.choice(FABS),
        "date": rand_date(START_DATE, END_DATE),
        "uptime_hours": uptime,
        "downtime_hours": downtime,
        "utilization_pct": utilization,
        "pm_status": rng.choice(PM_STATUSES),
    })
df_util = pd.DataFrame(util_rows)

# ── Excel 저장 ────────────────────────────────────────────────────────────
with pd.ExcelWriter(XL_PATH, engine="openpyxl") as writer:
    df_yield.to_excel(writer, sheet_name="Lot별수율", index=False)
    df_defect.to_excel(writer, sheet_name="공정별불량", index=False)
    df_util.to_excel(writer, sheet_name="장비가동률", index=False)

print(f"[OK] Excel saved → {XL_PATH}")
print(f"     Lot별수율:   {len(df_yield)} rows")
print(f"     공정별불량:  {len(df_defect)} rows")
print(f"     장비가동률:  {len(df_util)} rows")


# ════════════════════════════════════════════════════════════════════════════
# 2. SQLite 데이터
# ════════════════════════════════════════════════════════════════════════════
if DB_PATH.exists():
    DB_PATH.unlink()

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ── equipment (40 rows) ──────────────────────────────────────────────────────
cur.execute("""
    CREATE TABLE equipment (
        equipment_id   TEXT PRIMARY KEY,
        type           TEXT,
        fab            TEXT,
        model          TEXT,
        install_date   TEXT,
        status         TEXT
    )
""")

STATUSES = ["가동중", "점검중", "대기중", "정지"]
eq_rows = []
for eq_id, eq_type in eq_pool:
    fab = rng.choice(FABS)
    model = rng.choice(EQUIPMENT_MODELS[eq_type])
    install_d = rand_date(date(2018, 1, 1), date(2024, 12, 31))
    status = rng.choice(STATUSES, p=[0.7, 0.1, 0.15, 0.05])
    eq_rows.append((eq_id, eq_type, fab, model, install_d, status))

cur.executemany("INSERT INTO equipment VALUES (?,?,?,?,?,?)", eq_rows)

# ── sensors (500 rows) ───────────────────────────────────────────────────────
cur.execute("""
    CREATE TABLE sensors (
        sensor_id      TEXT PRIMARY KEY,
        equipment_id   TEXT,
        timestamp      TEXT,
        temperature    REAL,
        pressure       REAL,
        gas_flow       REAL,
        humidity       REAL
    )
""")

sensor_rows = []
for i in range(500):
    eq_id, eq_type = eq_pool[int(rng.integers(0, len(eq_pool)))]
    ts = rand_datetime(START_DATE, END_DATE)
    # Sensor ranges by equipment type
    if eq_type == "Etcher":
        temp = round(float(rng.uniform(20, 80)), 2)
        pressure = round(float(rng.uniform(1e-3, 5e-1)), 4)
        gas_flow = round(float(rng.uniform(50, 500)), 1)
    elif eq_type in ("CVD", "PVD"):
        temp = round(float(rng.uniform(200, 600)), 2)
        pressure = round(float(rng.uniform(1e-6, 1e-2)), 6)
        gas_flow = round(float(rng.uniform(10, 200)), 1)
    elif eq_type == "CMP":
        temp = round(float(rng.uniform(20, 40)), 2)
        pressure = round(float(rng.uniform(1, 6)), 2)
        gas_flow = round(float(rng.uniform(100, 400)), 1)
    else:  # Stepper
        temp = round(float(rng.uniform(21, 23)), 2)
        pressure = round(float(rng.uniform(0.95, 1.05)), 4)
        gas_flow = round(float(rng.uniform(5, 20)), 1)
    humidity = round(float(rng.uniform(30, 60)), 1)
    sensor_rows.append((f"SEN-{i+1:05d}", eq_id, ts, temp, pressure, gas_flow, humidity))

cur.executemany("INSERT INTO sensors VALUES (?,?,?,?,?,?,?)", sensor_rows)

# ── maintenance (100 rows) ───────────────────────────────────────────────────
cur.execute("""
    CREATE TABLE maintenance (
        maint_id        TEXT PRIMARY KEY,
        equipment_id    TEXT,
        type            TEXT,
        date            TEXT,
        duration_hours  REAL,
        engineer        TEXT,
        description     TEXT
    )
""")

MAINT_DESCRIPTIONS = {
    "PM": [
        "정기 예방정비 - 내부 부품 점검 및 세정",
        "분기 PM - 챔버 세정 및 소모품 교체",
        "월간 PM - 진공 펌프 오일 교환 및 필터 교체",
        "연간 PM - 전체 기계 점검 및 캘리브레이션",
        "챔버 라이너 교체 및 세정 작업",
    ],
    "BM": [
        "챔버 진공 리크 수리",
        "RF 전원 공급 장치 고장 수리",
        "가스 라인 막힘 제거",
        "모터 베어링 교체",
        "냉각수 누수 긴급 수리",
        "컨트롤러 보드 교체",
    ],
    "교체": [
        "히터 블록 교체",
        "매스 플로우 컨트롤러(MFC) 교체",
        "O-ring 세트 교체",
        "터보 펌프 교체",
        "세라믹 샤워헤드 교체",
        "엔드포인트 검출기 교체",
    ],
}

maint_rows = []
for i in range(100):
    eq_id, eq_type = eq_pool[int(rng.integers(0, len(eq_pool)))]
    m_type = rng.choice(MAINT_TYPES)
    m_date = rand_date(START_DATE, END_DATE)
    duration = round(float(rng.uniform(1, 16)), 1)
    engineer = rng.choice(ENGINEERS)
    desc = rng.choice(MAINT_DESCRIPTIONS[m_type])
    maint_rows.append((f"MNT-{i+1:04d}", eq_id, m_type, m_date, duration, engineer, desc))

cur.executemany("INSERT INTO maintenance VALUES (?,?,?,?,?,?,?)", maint_rows)

# ── alarms (150 rows) ────────────────────────────────────────────────────────
cur.execute("""
    CREATE TABLE alarms (
        alarm_id       TEXT PRIMARY KEY,
        equipment_id   TEXT,
        timestamp      TEXT,
        alarm_code     TEXT,
        severity       TEXT,
        message        TEXT,
        resolved       INTEGER
    )
""")

ALARM_MESSAGES = {
    "ETCH": [
        "챔버 압력 상한 초과 경보",
        "RF 전력 불일치 경보",
        "가스 유량 편차 경보",
        "엔드포인트 미검출 경보",
        "챔버 온도 이상 경보",
    ],
    "CVD": [
        "소스 가스 공급 이상 경보",
        "챔버 온도 편차 과대 경보",
        "진공도 불량 경보",
        "박막 두께 이상 경보",
        "플라즈마 이그니션 실패",
    ],
    "PVD": [
        "타겟 전력 이상 경보",
        "기판 온도 초과 경보",
        "진공 리크 감지 경보",
        "아르곤 유량 편차 경보",
        "접착력 불량 경보",
    ],
    "CMP": [
        "연마 압력 이상 경보",
        "슬러리 공급 중단 경보",
        "연마율 편차 경보",
        "패드 수명 한계 경보",
        "웨이퍼 척 진공 이상 경보",
    ],
    "STEP": [
        "포커스 편차 경보",
        "얼라인먼트 오류 경보",
        "조도 불균일 경보",
        "레티클 위치 이상 경보",
        "웨이퍼 스테이지 오류 경보",
    ],
}

alarm_rows = []
for i in range(150):
    eq_id, eq_type = eq_pool[int(rng.integers(0, len(eq_pool)))]
    abbr = type_abbr[eq_type]
    ts = rand_datetime(START_DATE, END_DATE)
    alarm_code = f"ALM-{abbr}-{int(rng.integers(1, 100)):03d}"
    sev = rng.choice(["Critical", "Major", "Minor", "Warning"], p=[0.1, 0.25, 0.4, 0.25])
    msg = rng.choice(ALARM_MESSAGES[abbr])
    resolved = int(rng.choice([0, 1], p=[0.2, 0.8]))
    alarm_rows.append((f"ALM-{i+1:05d}", eq_id, ts, alarm_code, sev, msg, resolved))

cur.executemany("INSERT INTO alarms VALUES (?,?,?,?,?,?,?)", alarm_rows)

conn.commit()
conn.close()

print(f"\n[OK] SQLite saved → {DB_PATH}")
print(f"     equipment:   {len(eq_rows)} rows")
print(f"     sensors:     {len(sensor_rows)} rows")
print(f"     maintenance: {len(maint_rows)} rows")
print(f"     alarms:      {len(alarm_rows)} rows")


# ════════════════════════════════════════════════════════════════════════════
# 3. Verification
# ════════════════════════════════════════════════════════════════════════════
conn2 = sqlite3.connect(DB_PATH)
for tbl in ["equipment", "sensors", "maintenance", "alarms"]:
    cnt = conn2.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    print(f"     [verify] {tbl}: {cnt} rows")
conn2.close()

xl = pd.ExcelFile(XL_PATH)
for sh in xl.sheet_names:
    df_tmp = xl.parse(sh)
    print(f"     [verify] sheet '{sh}': {len(df_tmp)} rows")

print("\n[완료] 반도체 공정 합성데이터 생성 완료")
