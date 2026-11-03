
import streamlit as st
import csv
import os

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
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

FILE_PATH = os.path.join(
    BASE_DIR,
    "countriesMBTI_16types(1).csv"
)

if not os.path.isfile(FILE_PATH):
    st.error("CSV 파일을 찾을 수 없습니다.")
    st.code(FILE_PATH)
    st.stop()

# =====================================
# 3. CSV 파일 읽기
# =====================================
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
    st.error("CSV 파일 읽기 오류")
    st.code(str(e))
    st.stop()

if not data or not columns:
    st.error("CSV 파일에 데이터가 없습니다.")
    st.stop()

# =====================================
# 4. 컬럼 확인
# =====================================
def find_column(names):
    for column in columns:
        if str(column).strip().lower() in names:
            return column
    return None

country_col = find_column({
    "country", "국가", "나라",
    "nation", "countries"
})

mbti_col = find_column({
    "mbti", "type", "mbti_type",
    "personality", "mbti 유형", "유형"
})

value_col = find_column({
    "percentage", "percent", "ratio",
    "rate", "비율", "퍼센트",
    "value", "count", "frequency", "population"
})

if country_col is None:
    st.error("국가 컬럼을 찾지 못했습니다.")
    st.write("현재 CSV 컬럼:", columns)
    st.stop()

# =====================================
# 5. MBTI 유형
# =====================================
MBTI_TYPES = [
    "ISTJ", "ISFJ", "INFJ", "INTJ",
    "ISTP", "ISFP", "INFP", "INTP",
    "ESTP", "ESFP", "ENFP", "ENTP",
    "ESTJ", "ESFJ", "ENFJ", "ENTJ"
]

# =====================================
# 6. 숫자 변환 함수
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
# 7. 국가 목록
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
# 8. 국가 선택
# =====================================
st.subheader("🔎 국가 선택")

selected_country = st.selectbox(
    "분석할 국가를 선택하세요!",
    countries
)

# =====================================
# 9. 국가별 MBTI 데이터 정리
# =====================================
mbti_data = {
    mbti: 0.0 for mbti in MBTI_TYPES
}

country_rows = [
    row for row in data
    if str(row.get(country_col, "")).strip()
    == selected_country
]

# 세로형 데이터
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

# 가로형 데이터
else:

    matching_columns = {}

    for column in columns:
        name = str(column).strip().upper()

        if name in MBTI_TYPES:
            matching_columns[name] = column

    if not matching_columns:
        st.error("MBTI 컬럼을 찾지 못했습니다.")
        st.write("CSV 컬럼:", columns)
        st.stop()

    for row in country_rows:

        for mbti, column in matching_columns.items():

            value = to_number(row.get(column))

            if value is not None:
                mbti_data[mbti] += value

# =====================================
# 10. 비율 계산
# =====================================
total = sum(mbti_data.values())

if total <= 0:
    st.warning("선택한 국가의 데이터가 없습니다.")
    st.stop()

percentages = {
    mbti: value / total * 100
    for mbti, value in mbti_data.items()
}

# 높은 비율부터 정렬
sorted_data = sorted(
    percentages.items(),
    key=lambda x: x[1],
    reverse=True
)

# =====================================
# 11. 요약 정보
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
# 12. 실제 막대그래프 만들기
# =====================================
st.subheader(
    f"📊 {selected_country}의 MBTI 비율"
)

st.caption(
    "국가별 MBTI 유형의 비율을 막대그래프로 확인해 보세요!"
)

# Streamlit 그래프에 전달할 데이터
chart_data = {
    "MBTI": [item[0] for item in sorted_data],
    "비율(%)": [round(item[1], 2) for item in sorted_data]
}

# 실제 그래프 출력
st.bar_chart(
    chart_data,
    x="MBTI",
    y="비율(%)",
    height=500
)

st.divider()

# =====================================
# 13. MBTI 순위표
# =====================================
st.subheader("🏅 MBTI 순위표")

for rank, (mbti, percent) in enumerate(sorted_data):

    if rank == 0:
        st.success(
            f"🥇 {rank + 1}위 | {mbti} | {percent:.2f}%"
        )

    elif rank == 1:
        st.info(
            f"🥈 {rank + 1}위 | {mbti} | {percent:.2f}%"
        )

    elif rank == 2:
        st.warning(
            f"🥉 {rank + 1}위 | {mbti} | {percent:.2f}%"
        )

    else:
        st.write(
            f"{rank + 1}위 | {mbti} | {percent:.2f}%"
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
