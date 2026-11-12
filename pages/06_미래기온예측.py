
import streamlit as st
import csv
import os
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
# 2. CSV 파일 경로 설정
# ==========================================

# 현재 파일은 pages 폴더 안에 있으므로
# 상위 폴더에서 CSV 파일을 찾음

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
        "app.py와 같은 상위 폴더에 넣어 주세요."
    )
    st.stop()


# ==========================================
# 3. CSV 데이터 불러오기
# ==========================================

data = []

try:
    # CSV 인코딩 자동 대응
    try:
        file = open(
            FILE_PATH,
            "r",
            encoding="cp949",
            newline=""
        )

        file.read(0)

    except Exception:
        file = open(
            FILE_PATH,
            "r",
            encoding="utf-8-sig",
            newline=""
        )

    with file:
        reader = csv.DictReader(file)

        for row in reader:

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

                data.append({
                    "year": year,
                    "month": month,
                    "temperature": temperature
                })

            except (ValueError, KeyError, TypeError):
                continue

except Exception as e:
    st.error(f"CSV 파일 읽기 오류: {e}")
    st.stop()


if not data:
    st.error("분석할 수 있는 데이터가 없습니다.")
    st.stop()


# ==========================================
# 4. 월 이름 설정
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


# ==========================================
# 5. 사용자 입력
# ==========================================

st.subheader("🔍 예측 조건 선택")

col1, col2 = st.columns(2)

latest_year = max(
    item["year"] for item in data
)

with col1:

    selected_month = st.selectbox(
        "📅 분석할 월을 선택하세요.",
        list(month_names.keys()),
        format_func=lambda x: month_names[x]
    )

with col2:

    prediction_year = st.number_input(
        "🔮 예측할 연도를 입력하세요.",
        min_value=latest_year + 1,
        max_value=2100,
        value=latest_year + 1,
        step=1
    )

st.divider()


# ==========================================
# 6. 선택한 월의 기온 데이터 추출
# ==========================================

selected_data = [
    item for item in data
    if item["month"] == selected_month
]

selected_data.sort(
    key=lambda x: x["year"]
)

years = [
    item["year"] for item in selected_data
]

temperatures = [
    item["temperature"] for item in selected_data
]

if len(years) < 2:
    st.error(
        "선형회귀 분석을 위해 최소 2개의 데이터가 필요합니다."
    )
    st.stop()


# ==========================================
# 7. 선형회귀 알고리즘
# ==========================================

# X = 연도
# Y = 평균기온

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


# 기울기 계산
slope = numerator / denominator

# 절편 계산
intercept = mean_y - slope * mean_x


# 예측 함수
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
# 9. 예측 결과 출력
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
        f"{predicted_temperature:.2f} ℃"
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
# 10. 그래프 데이터 만들기
# ==========================================

chart_data = []

# 과거 실제 데이터와 회귀선
for year, actual in zip(years, temperatures):

    chart_data.append({
        "year": year,
        "actual": actual,
        "fitted": predict_temperature(year),
        "forecast": None
    })


# 미래 예측 연도까지 회귀선 연장
for year in range(
    max(years) + 1,
    int(prediction_year) + 1
):

    chart_data.append({
        "year": year,
        "actual": None,
        "fitted": predict_temperature(year),
        "forecast": (
            predicted_temperature
            if year == prediction_year
            else None
        )
    })


# ==========================================
# 11. 선형회귀 그래프
# ==========================================

st.subheader("📈 과거 기온과 미래 예측 그래프")

st.write(
    f"분석 월: {month_names[selected_month]} "
    f"| 데이터 개수: {n}개 "
    f"| 분석 기간: {min(years)}~{max(years)}년"
)

# Vega-Lite를 사용한 그래프
# matplotlib 설치 없이 Streamlit 자체 기능으로 표시

chart_spec = {

    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",

    "width": "container",

    "height": 450,

    "layer": [

        # 1. 실제 데이터와 회귀선 사이의 오차
        {
            "transform": [
                {
                    "filter": "isValid(datum.actual)"
                }
            ],

            "mark": {
                "type": "rule",
                "color": "#BDBDBD",
                "strokeDash": [3, 3],
                "strokeWidth": 1.5
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

        # 2. 선형회귀 직선
        {
            "mark": {
                "type": "line",
                "color": "#2563EB",
                "strokeWidth": 3
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

        # 3. 과거 실제 기온 점
        {
            "transform": [
                {
                    "filter": "isValid(datum.actual)"
                }
            ],

            "mark": {
                "type": "point",
                "filled": True,
                "color": "#777777",
                "size": 65
            },

            "encoding": {
                "x": {
                    "field": "year",
                    "type": "quantitative"
                },

                "y": {
                    "field": "actual",
                    "type": "quantitative"
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
                    },
                    {
                        "field": "fitted",
                        "title": "회귀선 예측값",
                        "format": ".2f"
                    }
                ]
            }
        },

        # 4. 미래 예측 지점
        {
            "transform": [
                {
                    "filter": "isValid(datum.forecast)"
                }
            ],

            "mark": {
                "type": "point",
                "shape": "star",
                "filled": True,
                "color": "#E53935",
                "size": 350
            },

            "encoding": {
                "x": {
                    "field": "year",
                    "type": "quantitative"
                },

                "y": {
                    "field": "forecast",
                    "type": "quantitative"
                },

                "tooltip": [
                    {
                        "field": "year",
                        "title": "예측 연도"
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
    chart_data,
    chart_spec,
    use_container_width=True
)


# ==========================================
# 12. 그래프 범례
# ==========================================

st.markdown("""
**📌 그래프 범례**

- ⚫ 회색 점: 과거 실제 평균기온
- 🔵 파란색 선: 선형회귀 알고리즘이 학습한 회귀선
- 🔴 빨간색 별: 미래 예측 평균기온
- 회색 세로 점선: 실제 기온과 회귀선 사이의 오차
""")


# ==========================================
# 13. 선형회귀 계산 결과
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
선형회귀는 과거 데이터를 분석하여
미래의 값을 예측하는 머신러닝 알고리즘입니다.

우리 프로그램에서는 과거 서울의 월별 평균기온을 학습하여
미래의 평균기온을 예측합니다.
""")

st.markdown("### ① 과거 데이터 학습")

st.write("""
선택한 월에 해당하는 과거 기온 데이터를 가져옵니다.

- X축: 연도
- Y축: 평균기온
- 회색 점: 실제 관측된 기온

각 점은 실제 기온 기록 하나를 의미합니다.
""")

st.markdown("### ② 가장 적합한 직선 찾기")

st.write("""
선형회귀는 실제 데이터 점들과 직선 사이의
오차 제곱의 합이 최소가 되는 직선을 찾습니다.

파란색 선이 바로 선형회귀 알고리즘이 찾은 회귀선입니다.

회색 세로 점선은 실제 기온과 회귀선이 예측한 기온의
차이를 보여 줍니다. 이것을 잔차라고 합니다.
""")

st.latex(
    r"Y = aX + b"
)

st.write("""
- Y: 예측 평균기온
- X: 연도
- a: 기울기
- b: 절편

기울기가 양수이면 과거 데이터에서 기온이 상승하는 경향,
음수이면 하락하는 경향이 있다는 뜻입니다.
""")

st.markdown("### ③ 미래 기온 예측")

st.write(f"""
과거 데이터로 학습한 회귀식에
{prediction_year}이라는 연도를 넣습니다.

그 결과 {prediction_year}년
{month_names[selected_month]}의 평균기온을 예측합니다.

그래프의 빨간색 별표가 미래 예측 위치입니다.
""")

st.markdown("### ④ 결정계수(R²)")

st.write("""
결정계수는 회귀선이 실제 데이터의 변화를
얼마나 잘 설명하는지 나타내는 수치입니다.

- 1에 가까울수록 실제 데이터의 변화를 잘 설명합니다.
- 0에 가까울수록 실제 데이터의 변화를 잘 설명하지 못합니다.

결정계수가 높더라도 미래 기온 예측이 정확하다는 보장은 없습니다.
""")

st.info(
    "💡 선형회귀는 과거의 추세가 미래에도 이어진다고 가정합니다. "
    "실제 기온은 기후변화, 자연환경 등 여러 요인의 영향을 받으므로 "
    "이 결과는 교육 및 추세 분석을 위한 참고 자료입니다."
)

st.divider()

st.caption(
    "🌡️ 서울 월별 평균기온 분석 및 미래 예측 | Linear Regression"
)
