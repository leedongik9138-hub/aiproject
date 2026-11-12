
import streamlit as st
import csv
import os
import io
from datetime import datetime

# ==========================================
# 1. 페이지 설정
# ==========================================

st.set_page_config(
    page_title="서울 미래 기온 예측",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 서울의 월별 평균기온 예측")

st.write(
    "과거 서울의 기온 데이터를 분석하고 "
    "선형회귀 알고리즘으로 미래 기온을 예측해 보세요!"
)

st.divider()


# ==========================================
# 2. CSV 파일 불러오기
# ==========================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

FILE_PATH = os.path.join(
    BASE_DIR,
    "temperature.csv"
)

if not os.path.exists(FILE_PATH):
    st.error(
        "temperature.csv 파일을 찾을 수 없습니다. "
        "프로젝트 상위 폴더에 넣어 주세요."
    )
    st.stop()

try:
    try:
        with open(FILE_PATH, "r", encoding="cp949") as f:
            csv_text = f.read()

    except UnicodeDecodeError:
        with open(FILE_PATH, "r", encoding="utf-8-sig") as f:
            csv_text = f.read()

    reader = csv.DictReader(io.StringIO(csv_text))

    data = list(reader)

except Exception as e:
    st.error(f"CSV 파일 읽기 오류: {e}")
    st.stop()


# ==========================================
# 3. 데이터 정리
# ==========================================

month_names = {
    1: "1월",
    2: "2월",
    3: "3월",
    4: "4월",
    5: "5월",
    6: "6월",
    7: "7월",
    8: "8월",
    9: "9월",
    10: "10월",
    11: "11월",
    12: "12월"
}

temperature_data = []

for row in data:

    try:
        date_text = row["일시"].strip()

        date = datetime.strptime(
            date_text,
            "%b-%y"
        )

        year = date.year
        month = date.month

        temperature = float(
            row["평균기온(℃)"]
        )

        if 1900 <= year <= 2026:

            temperature_data.append({
                "year": year,
                "month": month,
                "temperature": temperature
            })

    except (ValueError, KeyError, TypeError):
        continue


if not temperature_data:
    st.error("분석할 수 있는 기온 데이터가 없습니다.")
    st.stop()


# ==========================================
# 4. 월 선택
# ==========================================

st.subheader("🔍 예측 조건 선택")

selected_month = st.selectbox(
    "📅 분석할 월을 선택하세요.",
    list(month_names.keys()),
    format_func=lambda x: month_names[x]
)


# ==========================================
# 5. 선택한 월의 데이터 추출
# ==========================================

selected_data = [
    item for item in temperature_data
    if item["month"] == selected_month
]

selected_data.sort(
    key=lambda x: x["year"]
)

if len(selected_data) < 2:
    st.error("분석할 수 있는 데이터가 부족합니다.")
    st.stop()

# ★ 그래프에 필요한 변수를 먼저 생성

years = [
    item["year"] for item in selected_data
]

temperatures = [
    item["temperature"] for item in selected_data
]

latest_year = max(years)


# ==========================================
# 6. 예측 연도 입력
# ==========================================

prediction_year = st.number_input(
    "🔮 예측할 연도를 입력하세요.",
    min_value=latest_year + 1,
    max_value=2100,
    value=latest_year + 1,
    step=1
)

st.divider()


# ==========================================
# 7. 선형회귀 알고리즘
# ==========================================

n = len(years)

mean_x = sum(years) / n
mean_y = sum(temperatures) / n

numerator = sum(
    (x - mean_x) * (y - mean_y)
    for x, y in zip(years, temperatures)
)

denominator = sum(
    (x - mean_x) ** 2
    for x in years
)

if denominator == 0:
    st.error("선형회귀 계산에 실패했습니다.")
    st.stop()

# 기울기
slope = numerator / denominator

# 절편
intercept = mean_y - slope * mean_x


# 미래 예측 함수
def predict_temperature(year):

    return slope * year + intercept


# 미래 기온 예측
predicted_temperature = predict_temperature(
    prediction_year
)


# ==========================================
# 8. 결정계수 R² 계산
# ==========================================

predicted_values = [
    predict_temperature(year)
    for year in years
]

ss_total = sum(
    (actual - mean_y) ** 2
    for actual in temperatures
)

ss_residual = sum(
    (actual - predicted) ** 2
    for actual, predicted in zip(
        temperatures,
        predicted_values
    )
)

if ss_total == 0:
    r_squared = 0
else:
    r_squared = 1 - (
        ss_residual / ss_total
    )


# ==========================================
# 9. 예측 결과
# ==========================================

st.subheader("🎯 기온 예측 결과")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "예측 연도",
        f"{prediction_year}년"
    )

with col2:
    st.metric(
        "예측 평균기온",
        f"{predicted_temperature:.2f}℃"
    )

with col3:
    st.metric(
        "결정계수 R²",
        f"{r_squared:.3f}"
    )

st.success(
    f"🌤️ {prediction_year}년 "
    f"{month_names[selected_month]}의 "
    f"예측 평균기온은 "
    f"{predicted_temperature:.2f}℃입니다!"
)


# ==========================================
# 10. 그래프 데이터 생성
# ==========================================

chart_data = []

# 과거 실제 기온과 회귀선
for year in range(min(years), latest_year + 1):

    actual_temperature = None

    if year in years:
        index = years.index(year)
        actual_temperature = temperatures[index]

    chart_data.append({
        "year": year,
        "actual": actual_temperature,
        "fitted": predict_temperature(year),
        "forecast": None
    })


# 미래 예측선 시작점
chart_data.append({
    "year": latest_year,
    "actual": None,
    "fitted": None,
    "forecast": temperatures[years.index(latest_year)]
})

# 미래 예측선 끝점
chart_data.append({
    "year": int(prediction_year),
    "actual": None,
    "fitted": None,
    "forecast": predicted_temperature
})


# ==========================================
# 11. 빨간색 꺾은선 그래프
# ==========================================

st.subheader("📈 과거 기온과 미래 예측 그래프")

st.write(
    f"분석 월: {month_names[selected_month]} | "
    f"분석 기간: {min(years)}~{latest_year}년 | "
    f"데이터: {n}개"
)

chart_spec = {

    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",

    "data": {
        "values": chart_data
    },

    "width": "container",
    "height": 450,

    "layer": [

        # 실제 기온과 회귀선 사이의 오차
        {
            "transform": [
                {
                    "filter": "isValid(datum.actual)"
                }
            ],

            "mark": {
                "type": "rule",
                "color": "#BBBBBB",
                "strokeDash": [3, 3]
            },

            "encoding": {
                "x": {
                    "field": "year",
                    "type": "quantitative",
                    "title": "연도"
                },
                "y": {
                    "field": "actual",
                    "type": "quantitative",
                    "title": "평균기온 (℃)"
                },
                "y2": {
                    "field": "fitted"
                }
            }
        },

        # 과거 실제 기온: 빨간색 꺾은선
        {
            "transform": [
                {
                    "filter": "isValid(datum.actual)"
                }
            ],

            "mark": {
                "type": "line",
                "color": "#E53935",
                "strokeWidth": 3,
                "point": False
            },

            "encoding": {
                "x": {
                    "field": "year",
                    "type": "quantitative",
                    "title": "연도"
                },
                "y": {
                    "field": "actual",
                    "type": "quantitative",
                    "title": "평균기온 (℃)"
                },
                "tooltip": [
                    {
                        "field": "year",
                        "title": "연도"
                    },
                    {
                        "field": "actual",
                        "title": "실제 평균기온",
                        "format": ".2f"
                    }
                ]
            }
        },

        # 선형회귀: 파란색 점선
        {
            "transform": [
                {
                    "filter": "isValid(datum.fitted)"
                }
            ],

            "mark": {
                "type": "line",
                "color": "#2563EB",
                "strokeWidth": 3,
                "strokeDash": [7, 5]
            },

            "encoding": {
                "x": {
                    "field": "year",
                    "type": "quantitative",
                    "title": "연도"
                },
                "y": {
                    "field": "fitted",
                    "type": "quantitative",
                    "title": "평균기온 (℃)"
                },
                "tooltip": [
                    {
                        "field": "year",
                        "title": "연도"
                    },
                    {
                        "field": "fitted",
                        "title": "회귀선 기온",
                        "format": ".2f"
                    }
                ]
            }
        },

        # 미래 예측: 주황색 꺾은선
        {
            "transform": [
                {
                    "filter": "isValid(datum.forecast)"
                }
            ],

            "mark": {
                "type": "line",
                "color": "#FF9800",
                "strokeWidth": 4
            },

            "encoding": {
                "x": {
                    "field": "year",
                    "type": "quantitative",
                    "title": "연도"
                },
                "y": {
                    "field": "forecast",
                    "type": "quantitative",
                    "title": "평균기온 (℃)"
                },
                "tooltip": [
                    {
                        "field": "year",
                        "title": "연도"
                    },
                    {
                        "field": "forecast",
                        "title": "예측 평균기온",
                        "format": ".2f"
                    }
                ]
            }
        }
    ],

    "config": {
        "axis": {
            "labelFontSize": 12,
            "titleFontSize": 14,
            "grid": True
        }
    }
}

st.vega_lite_chart(
    None,
    chart_spec,
    use_container_width=True
)


# ==========================================
# 12. 그래프 범례
# ==========================================

st.markdown("""
### 📌 그래프 범례

🔴 **빨간색 꺾은선:** 과거 실제 평균기온

🔵 **파란색 점선:** 선형회귀 알고리즘의 추세선

🟠 **주황색 꺾은선:** 미래 예측 기온

회색 세로 점선: 실제 기온과 회귀선 사이의 오차
""")


# ==========================================
# 13. 선형회귀 분석 결과
# ==========================================

st.divider()

st.subheader("🧮 선형회귀 분석 결과")

col1, col2 = st.columns(2)

with col1:

    st.metric(
        "기울기",
        f"{slope:.5f}"
    )

    st.metric(
        "절편",
        f"{intercept:.3f}"
    )

with col2:

    st.metric(
        "결정계수 R²",
        f"{r_squared:.4f}"
    )

    st.metric(
        "학습 데이터 개수",
        f"{n}개"
    )

st.markdown(
    f"### 📐 회귀식: Y = {slope:.5f}X + ({intercept:.3f})"
)


# ==========================================
# 14. 선형회귀 알고리즘 설명
# ==========================================

st.divider()

st.subheader("🧠 선형회귀 알고리즘이란?")

st.write("""
선형회귀는 과거의 데이터를 분석하여
미래의 값을 예측하는 머신러닝 알고리즘입니다.

이 프로그램에서는 과거 서울의 월별 평균기온과
연도 사이의 관계를 학습합니다.
""")

st.markdown("### ① 과거 데이터 학습")

st.write("""
선택한 월의 과거 기온 데이터를 가져옵니다.

- X축: 연도
- Y축: 평균기온
- 빨간색 꺾은선: 실제 기온 변화

""")

st.markdown("### ② 가장 적합한 직선 찾기")

st.write("""
선형회귀는 실제 데이터와 직선 사이의
오차 제곱의 합이 최소가 되는 직선을 찾습니다.

파란색 점선이 바로 선형회귀 알고리즘이 찾은 회귀선입니다.

회색 세로 점선은 실제 기온과 회귀선이 예측한 기온의 차이인
잔차를 보여 줍니다.
""")

st.latex(
    r"Y = aX + b"
)

st.write("""
- Y: 예측 평균기온
- X: 연도
- a: 기울기
- b: 절편

기울기가 양수이면 과거 데이터에서 상승 경향,
음수이면 하락 경향이 있다는 뜻입니다.
""")

st.markdown("### ③ 미래 기온 예측")

st.write(
    f"""
과거 데이터로 학습한 회귀식에
{prediction_year}이라는 연도를 넣습니다.

그 결과 {prediction_year}년
{month_names[selected_month]}의 평균기온을 예측합니다.

주황색 꺾은선이 마지막 실제 관측값과 미래 예측값을 연결합니다.
"""
)

st.markdown("### ④ 결정계수(R²)")

st.write("""
결정계수는 회귀선이 실제 데이터의 변화를
얼마나 잘 설명하는지 나타내는 지표입니다.

- 1에 가까울수록 데이터의 변화를 잘 설명합니다.
- 0에 가까울수록 데이터의 변화를 잘 설명하지 못합니다.

결정계수가 높더라도 미래 예측이 반드시 정확한 것은 아닙니다.
""")

st.warning("""
⚠️ 실제 기온은 기후변화, 자연환경 등 다양한 요인의 영향을 받습니다.
이 프로그램은 연도와 기온 사이의 단순한 선형 관계를 이용한
교육용 예측 모델입니다.
""")

st.divider()

st.caption(
    "🌡️ 서울 월별 평균기온 분석 및 미래 예측 | Linear Regression"
)
