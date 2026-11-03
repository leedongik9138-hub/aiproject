
import streamlit as st
import csv
import os
import html

# =====================================
# 1. 페이지 설정
# =====================================
st.set_page_config(
    page_title="국가별 MBTI 분석",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 세계 국가별 MBTI 분석")
st.write("국가를 선택하고 그 나라의 MBTI 유형별 비율을 확인해 보세요!")
st.divider()

# =====================================
# 2. CSV 파일 경로 설정
# =====================================

# 현재 app.py가 있는 pages 폴더의 상위 폴더
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

# 상위 폴더에 있는 CSV 파일
FILE_PATH = os.path.join(
    BASE_DIR,
    "countriesMBTI_16types.csv"
)

# CSV 파일 확인
if not os.path.isfile(FILE_PATH):
    st.error("CSV 파일을 찾을 수 없습니다.")
    st.write("찾으려는 경로:")
    st.code(FILE_PATH)
    st.stop()

# CSV 파일 읽기
try:
    with open(
        FILE_PATH,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)
        data = list(reader)
        columns = reader.fieldnames or []

except Exception as e:
    st.error("CSV 파일을 읽는 중 오류가 발생했습니다.")
    st.code(str(e))
    st.stop()

if not data or not columns:
    st.error("CSV 파일에 데이터 또는 컬럼명이 없습니다.")
    st.stop()

# =====================================
# 3. 컬럼 자동 확인
# =====================================

column_map = {
    str(col).strip().lower(): col
    for col in columns
    if col
}

def find_column(names):
    for name in names:
        if name.lower() in column_map:
            return column_map[name.lower()]
    return None

country_col = find_column([
    "country", "국가", "나라",
    "nation", "countries"
])

mbti_col = find_column([
    "mbti", "type", "mbti_type",
    "personality", "mbti 유형", "유형"
])

value_col = find_column([
    "percentage", "percent", "ratio",
    "rate", "비율", "퍼센트",
    "value", "count", "frequency", "population"
])

if country_col is None:
    st.error("국가 컬럼을 찾을 수 없습니다.")
    st.write("CSV 컬럼명:", columns)
    st.stop()

# =====================================
# 4. MBTI 16개 유형
# =====================================

MBTI_TYPES = [
    "ISTJ", "ISFJ", "INFJ", "INTJ",
    "ISTP", "ISFP", "INFP", "INTP",
    "ESTP", "ESFP", "ENFP", "ENTP",
    "ESTJ", "ESFJ", "ENFJ", "ENTJ"
]

# =====================================
# 5. 숫자 변환
# =====================================

def to_number(value):
    try:
        if value is None:
            return None

        value = str(value).strip()
        value = value.replace(",", "").replace("%", "")

        if value == "":
            return None

        number = float(value)

        if number < 0:
            return None

        return number

    except (ValueError, TypeError):
        return None

# =====================================
# 6. 국가 목록 만들기
# =====================================

countries = sorted(set(
    str(row.get(country_col, "")).strip()
    for row in data
    if row.get(country_col)
    and str(row.get(country_col)).strip()
))

if not countries:
    st.error("국가 데이터가 없습니다.")
    st.stop()

# =====================================
# 7. 국가 선택
# =====================================

st.subheader("🔎 분석할 국가 선택")

selected_country = st.selectbox(
    "국가를 선택하세요!",
    countries
)

# =====================================
# 8. 선택한 국가의 데이터 정리
# =====================================

mbti_data = {
    mbti: 0.0
    for mbti in MBTI_TYPES
}

country_rows = [
    row for row in data
    if str(row.get(country_col, "")).strip()
    == selected_country
]

# 세로형 CSV
if mbti_col and value_col:

    for row in country_rows:

        mbti = str(
            row.get(mbti_col, "")
        ).strip().upper()

        value = to_number(
            row.get(value_col)
        )

        if mbti in mbti_data and value is not None:
            mbti_data[mbti] += value

# 가로형 CSV
else:

    matching_columns = {}

    for column in columns:

        name = str(column).strip().upper()

        if name in MBTI_TYPES:
            matching_columns[name] = column

    if not matching_columns:
        st.error("MBTI 유형 컬럼을 찾지 못했습니다.")
        st.write("CSV 컬럼명:", columns)
        st.stop()

    for row in country_rows:

        for mbti, column in matching_columns.items():

            value = to_number(
                row.get(column)
            )

            if value is not None:
                mbti_data[mbti] += value

# =====================================
# 9. 비율 계산
# =====================================

total = sum(mbti_data.values())

if total <= 0:
    st.warning("선택한 국가의 MBTI 데이터가 없습니다.")
    st.stop()

percentages = {
    mbti: value / total * 100
    for mbti, value in mbti_data.items()
}

sorted_data = sorted(
    percentages.items(),
    key=lambda item: item[1],
    reverse=True
)

# =====================================
# 10. 요약 정보
# =====================================

top_mbti, top_percent = sorted_data[0]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("🌍 선택 국가", selected_country)

with col2:
    st.metric("🏆 가장 높은 MBTI", top_mbti)

with col3:
    st.metric("📊 최고 비율", f"{top_percent:.2f}%")

st.divider()

# =====================================
# 11. 막대그래프 색상
# =====================================

st.subheader(f"📊 {selected_country}의 MBTI 비율")

st.caption(
    "1위는 파란색, 나머지는 검정색에서 "
    "회색으로 점점 밝아집니다."
)

def get_color(rank, total_types):

    if rank == 0:
        return "#1677FF"

    if total_types <= 1:
        return "#222222"

    gray = int(
        25 + (210 - 25) * (rank - 1)
        / max(total_types - 2, 1)
    )

    return f"rgb({gray}, {gray}, {gray})"

# =====================================
# 12. HTML 그래프 만들기
# =====================================

chart_html = """
<div style="
    width:100%;
    padding:20px;
    background:#FFFFFF;
    border-radius:12px;
    border:1px solid #E5E7EB;
    box-sizing:border-box;
">
"""

for rank, (mbti, percent) in enumerate(sorted_data):

    color = get_color(rank, len(sorted_data))
    width = min(max(percent, 0), 100)

    chart_html += f"""
    <div style="margin-bottom:17px;">

        <div style="
            display:flex;
            justify-content:space-between;
            margin-bottom:6px;
            font-size:14px;
            font-weight:600;
            color:#222222;
        ">
            <span>{rank + 1}위 · {html.escape(mbti)}</span>
            <span>{percent:.2f}%</span>
        </div>

        <div style="
            width:100%;
            height:19px;
            background:#EEEEEE;
            border-radius:5px;
            overflow:hidden;
        ">
            <div style="
                width:{width:.4f}%;
                height:100%;
                background:{color};
                border-radius:5px;
            "></div>
        </div>

    </div>
    """

chart_html += "</div>"

st.markdown(
    chart_html,
    unsafe_allow_html=True
)

# =====================================
# 13. MBTI 순위표
# =====================================

st.divider()
st.subheader("🏅 MBTI 순위표")

for rank, (mbti, percent) in enumerate(sorted_data):

    if rank == 0:

        st.success(
            f"🥇 {rank + 1}위 {mbti} | {percent:.2f}%"
        )

    else:

        st.write(
            f"**{rank + 1}위. {mbti}** — {percent:.2f}%"
        )

# =====================================
# 14. 안내
# =====================================

st.divider()

st.info(
    "💡 MBTI 비율은 제공된 CSV 데이터를 기준으로 계산합니다. "
    "실제 국가 전체 인구의 성격 유형을 대표한다고 단정할 수는 없습니다."
)

st.caption("🌍 국가별 MBTI 분석 앱 | Streamlit")
