
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


# 컬럼 찾기 함수
def find_column(columns, possible_names):
    for column in columns:
        if column.strip().lower() in possible_names:
            return column
    return None


# 제목
st.title("🌍 세계 국가별 MBTI 분석")
st.write("국가를 선택하고 그 나라의 MBTI 유형별 비율을 확인해 보세요!")

# CSV 파일 확인
if not os.path.exists(FILE_PATH):
    st.error("CSV 파일을 찾을 수 없습니다.")
    st.write("파일 이름과 위치를 확인해 주세요.")
    st.code("countriesMBTI_16types.csv")
    st.stop()


# CSV 파일 읽기
try:
    with open(FILE_PATH, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        data = list(reader)
        columns = reader.fieldnames or []

except Exception as e:
    st.error(f"CSV 파일을 읽는 중 오류가 발생했습니다: {e}")
    st.stop()


if not data:
    st.warning("CSV 파일에 데이터가 없습니다.")
    st.stop()


# 컬럼 자동 탐색
country_col = find_column(columns, [
    "country", "국가", "나라", "nation", "countries"
])

mbti_col = find_column(columns, [
    "mbti", "type", "mbti_type",
    "personality", "mbti 유형", "유형"
])

value_col = find_column(columns, [
    "percentage", "percent", "ratio",
    "rate", "비율", "퍼센트",
    "value", "count", "frequency", "population"
])


# 국가 컬럼 확인
if country_col is None:
    st.error("국가 컬럼을 찾을 수 없습니다.")
    st.write("CSV 컬럼 목록:", columns)
    st.stop()


# 국가 목록 만들기
countries = sorted(set(
    row[country_col].strip()
    for row in data
    if row.get(country_col)
))


if not countries:
    st.warning("국가 데이터가 없습니다.")
    st.stop()


# 국가 선택
selected_country = st.selectbox(
    "🌎 분석할 국가를 선택하세요!",
    countries
)


# 선택한 국가의 데이터
country_rows = [
    row for row in data
    if row.get(country_col, "").strip() == selected_country
]


# MBTI별 데이터 초기화
mbti_data = {
    mbti: 0.0 for mbti in MBTI_TYPES
}


# 세로형 CSV 처리
if mbti_col and value_col:

    for row in country_rows:
        mbti = row.get(mbti_col, "").strip().upper()

        if mbti in MBTI_TYPES:
            mbti_data[mbti] += to_number(
                row.get(value_col, 0)
            )


# 가로형 CSV 처리
else:

    mbti_columns = {
        column.strip().upper(): column
        for column in columns
        if column.strip().upper() in MBTI_TYPES
    }

    if not mbti_columns:
        st.error("MBTI 유형 컬럼을 찾을 수 없습니다.")
        st.write("CSV 컬럼 목록:", columns)
        st.stop()

    for row in country_rows:
        for mbti in MBTI_TYPES:
            if mbti in mbti_columns:
                column = mbti_columns[mbti]
                mbti_data[mbti] += to_number(
                    row.get(column, 0)
                )


# 전체 합계
total = sum(mbti_data.values())

if total <= 0:
    st.warning("선택한 국가의 MBTI 데이터가 없습니다.")
    st.stop()


# 비율 계산
percentages = {
    mbti: value / total * 100
    for mbti, value in mbti_data.items()
}


# 비율이 높은 순서대로 정렬
sorted_data = sorted(
    percentages.items(),
    key=lambda item: item[1],
    reverse=True
)


# 1위 MBTI
top_mbti, top_percent = sorted_data[0]

st.divider()

st.subheader(f"📊 {selected_country} MBTI 분석 결과")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "🏆 가장 높은 MBTI",
        top_mbti
    )

with col2:
    st.metric(
        "📈 최고 비율",
        f"{top_percent:.2f}%"
    )


# 그래프
st.divider()
st.subheader("📊 MBTI 유형별 비율 그래프")

st.caption("1위부터 16위까지 비율이 높은 순서대로 표시됩니다.")

# 순위가 이미 정렬된 순서대로 데이터 생성
chart_rows = []

for rank, (mbti, percent) in enumerate(sorted_data, start=1):
    chart_rows.append({
        "순위": f"{rank}위 ({mbti})",
        "비율": round(percent, 2)
    })

# 그래프의 순서를 명시적으로 지정
ordered_labels = [
    row["순위"] for row in chart_rows
]

# Vega-Lite 그래프
chart_spec = {
    "data": {
        "values": chart_rows
    },
    "mark": {
        "type": "bar"
    },
    "encoding": {
        "x": {
            "field": "순위",
            "type": "ordinal",
            "sort": ordered_labels,
            "axis": {
                "title": "MBTI 순위",
                "labelAngle": -45
            }
        },
        "y": {
            "field": "비율",
            "type": "quantitative",
            "axis": {
                "title": "비율 (%)"
            }
        },
        "tooltip": [
            {
                "field": "순위",
                "type": "ordinal",
                "title": "순위"
            },
            {
                "field": "비율",
                "type": "quantitative",
                "title": "비율 (%)"
            }
        ]
    },
    "width": "container",
    "height": 450
}

st.vega_lite_chart(
    chart_spec,
    use_container_width=True
)


# 순위표
st.divider()
st.subheader("🏅 MBTI 순위표")

ranking_table = []

for rank, (mbti, percent) in enumerate(sorted_data, start=1):
    ranking_table.append({
        "순위": f"{rank}위",
        "MBTI 유형": mbti,
        "비율": f"{percent:.2f}%"
    })

st.table(ranking_table)


# 안내
st.divider()

st.info(
    "💡 그래프는 비율이 높은 유형부터 1위, 2위, 3위 순서로 표시됩니다."
)

st.caption(
    "※ 비율은 선택한 국가의 MBTI 데이터 합계를 기준으로 계산했습니다."
)
