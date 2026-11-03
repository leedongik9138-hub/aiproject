
import streamlit as st
import csv
import os

# 페이지 설정
st.set_page_config(
    page_title="국가별 MBTI 분석",
    page_icon="🌍",
    layout="wide"
)

# CSV 파일 경로
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE_PATH = os.path.join(BASE_DIR, "countriesMBTI_16types.csv")

# MBTI 16가지 유형
MBTI_TYPES = [
    "ISTJ", "ISFJ", "INFJ", "INTJ",
    "ISTP", "ISFP", "INFP", "INTP",
    "ESTP", "ESFP", "ENFP", "ENTP",
    "ESTJ", "ESFJ", "ENFJ", "ENTJ"
]


# 숫자 변환 함수
def to_number(value):
    try:
        value = str(value).replace(",", "").replace("%", "").strip()
        return float(value)
    except (ValueError, TypeError):
        return 0.0


# CSV 파일 불러오기
st.title("🌍 국가별 MBTI 분석")
st.write("나라별 MBTI 유형의 비율을 확인해 보자!")

if not os.path.exists(FILE_PATH):
    st.error("CSV 파일을 찾을 수 없어!")
    st.write("파일 위치와 이름을 확인해 줘.")
    st.code("countriesMBTI_16types.csv")

    st.stop()

try:
    with open(FILE_PATH, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        data = list(reader)
        columns = reader.fieldnames or []

except Exception as e:
    st.error(f"CSV 파일을 읽는 중 오류가 발생했어: {e}")
    st.stop()


if not data:
    st.warning("CSV 파일에 데이터가 없어!")
    st.stop()


# 컬럼 자동 찾기
def find_column(possible_names):
    for column in columns:
        if column.strip().lower() in possible_names:
            return column
    return None


country_col = find_column([
    "country", "국가", "나라", "nation", "countries"
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


# 국가 컬럼 확인
if country_col is None:
    st.error("국가를 나타내는 컬럼을 찾을 수 없어!")
    st.write("CSV 컬럼:", columns)
    st.stop()


# 국가 목록
countries = sorted(set(
    row[country_col].strip()
    for row in data
    if row.get(country_col)
))


if not countries:
    st.warning("국가 데이터가 없어!")
    st.stop()


# 국가 선택
selected_country = st.selectbox(
    "🌎 분석할 국가를 선택해 줘!",
    countries
)


# 선택한 국가 데이터
country_rows = [
    row for row in data
    if row.get(country_col, "").strip() == selected_country
]


# MBTI별 데이터 계산
mbti_data = {mbti: 0.0 for mbti in MBTI_TYPES}


# 세로형 CSV인지 확인
if mbti_col and value_col:

    for row in country_rows:
        mbti = row.get(mbti_col, "").strip().upper()

        if mbti in MBTI_TYPES:
            mbti_data[mbti] += to_number(row.get(value_col, 0))


# 가로형 CSV인지 확인
else:

    mbti_columns = {
        column.upper(): column
        for column in columns
        if column.upper() in MBTI_TYPES
    }

    if not mbti_columns:
        st.error("MBTI 유형 컬럼을 찾을 수 없어!")
        st.write("CSV 컬럼:", columns)
        st.stop()

    for row in country_rows:
        for mbti in MBTI_TYPES:
            if mbti in mbti_columns:
                column = mbti_columns[mbti]
                mbti_data[mbti] += to_number(row.get(column, 0))


# 전체 합계 계산
total = sum(mbti_data.values())

if total <= 0:
    st.warning("선택한 국가의 MBTI 데이터가 없어!")
    st.stop()


# 비율 계산
percentages = {
    mbti: value / total * 100
    for mbti, value in mbti_data.items()
}


# 높은 비율 순서로 정렬
sorted_data = sorted(
    percentages.items(),
    key=lambda item: item[1],
    reverse=True
)


# 1위 MBTI 표시
top_mbti, top_percent = sorted_data[0]

st.divider()

st.subheader(f"📊 {selected_country} MBTI 분석 결과")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="🏆 가장 높은 MBTI",
        value=top_mbti
    )

with col2:
    st.metric(
        label="📈 최고 비율",
        value=f"{top_percent:.2f}%"
    )


# 그래프
st.divider()
st.subheader("📊 MBTI 유형별 비율 그래프")
st.caption("비율이 높은 유형부터 1위, 2위, 3위 순서로 표시돼!")

chart_data = {
    "순위": [
        f"{rank}위 ({mbti})"
        for rank, (mbti, percent) in enumerate(sorted_data, start=1)
    ],
    "비율(%)": [
        round(percent, 2)
        for mbti, percent in sorted_data
    ]
}

st.bar_chart(
    chart_data,
    x="순위",
    y="비율(%)",
    height=500
)


# 순위표
st.divider()
st.subheader("🏅 MBTI 순위표")

st.table([
    {
        "순위": f"{rank}위",
        "MBTI 유형": mbti,
        "비율": f"{percent:.2f}%"
    }
    for rank, (mbti, percent) in enumerate(sorted_data, start=1)
])


# 안내 문구
st.divider()
st.info(
    "💡 MBTI 비율은 선택한 국가의 데이터 합계를 기준으로 "
    "100%가 되도록 계산했어!"
)

st.caption("※ 결과는 CSV 파일에 들어 있는 데이터에 따라 달라져.")
