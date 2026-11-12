
import streamlit as st
import csv
import os
from datetime import datetime

# --------------------------------------------------
# 1. 페이지 설정
# --------------------------------------------------
st.set_page_config(
    page_title="서울 미래 기온 예측",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 서울 월별 평균기온 및 미래 예측")
st.write("월을 선택하면 과거 평균기온을 바탕으로 선형회귀를 이용해 미래 기온을 예측합니다.")

# --------------------------------------------------
# 2. CSV 파일 경로 설정
# --------------------------------------------------
# 현재 파일은 pages 폴더 안에 있으므로
# 한 단계 위 폴더에서 temperature.csv를 찾습니다.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE_PATH = os.path.join(BASE_DIR, "temperature.csv")

if not os.path.exists(FILE_PATH):
    st.error("temperature.csv 파일을 찾을 수 없습니다.")
    st.info("temperature.csv 파일을 app.py와 같은 폴더에 넣어 주세요.")
    st.stop()


# --------------------------------------------------
# 3. CSV 파일 읽기
# --------------------------------------------------
def read_csv_file(file_path):
    encodings = ["cp949", "utf-8-sig", "euc-kr"]

    for encoding in encodings:
        try:
            with open(
                file_path,
                "r",
                encoding=encoding,
                newline=""
            ) as file:
                reader = csv.DictReader(file)
                rows = list(reader)
                columns = reader.fieldnames or []

            return rows, columns

        except UnicodeDecodeError:
            continue

    raise ValueError("CSV 파일의 인코딩을 읽을 수 없습니다.")


try:
    rows, columns = read_csv_file(FILE_PATH)

except Exception as e:
    st.error(f"CSV 파일을 읽는 중 오류가 발생했습니다: {e}")
    st.stop()


# --------------------------------------------------
# 4. 필요한 열이 있는지 확인
# --------------------------------------------------
required_columns = ["일시", "평균기온(℃)"]

missing_columns = [
    column for column in required_columns
    if column not in columns
]

if missing_columns:
    st.error(
        "CSV 파일에 필요한 열이 없습니다: "
        + ", ".join(missing_columns)
    )
    st.write("현재 CSV 파일의 열 이름:", columns)
    st.stop()


# --------------------------------------------------
# 5. 날짜와 평균기온 데이터 정리
# --------------------------------------------------
temperature_data = []

for row in rows:
    date_text = str(row.get("일시", "")).strip()
    temperature_text = str(row.get("평균기온(℃)", "")).strip()

    if not date_text or not temperature_text:
        continue

    try:
        # 예: Oct-07 → 2007년 10월
        date = datetime.strptime(date_text, "%b-%y")

        # 쉼표가 포함된 숫자도 처리
        temperature = float(
            temperature_text.replace(",", "")
        )

        temperature_data.append({
            "year": date.year,
            "month": date.month,
            "temperature": temperature
        })

    except (ValueError, TypeError):
        # 날짜나 기온을 숫자로 바꿀 수 없는 행은 제외
        continue


if not temperature_data:
    st.error("CSV 파일에서 날짜와 평균기온 데이터를 찾지 못했습니다.")
    st.stop()


# --------------------------------------------------
# 6. 월 선택
# --------------------------------------------------
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

selected_month = st.selectbox(
    "📅 예측하고 싶은 월을 선택하세요.",
    options=list(range(1, 13)),
    format_func=lambda month: month_names[month]
)


# --------------------------------------------------
# 7. 선택한 월의 데이터만 추출
# --------------------------------------------------
monthly_data = [
    item for item in temperature_data
    if item["month"] == selected_month
]

if not monthly_data:
    st.warning("선택한 월의 기온 데이터가 없습니다.")
    st.stop()


# 같은 연도에 같은 월의 데이터가 여러 개라면 평균 계산
year_temperature = {}

for item in monthly_data:
    year = item["year"]
    temperature = item["temperature"]

    if year not in year_temperature:
        year_temperature[year] = []

    year_temperature[year].append(temperature)


# --------------------------------------------------
# 8. years와 temperatures 생성
#    ※ 이 부분이 그래프보다 반드시 먼저 실행되어야 합니다.
# --------------------------------------------------
years = sorted(year_temperature.keys())

temperatures = [
    sum(year_temperature[year]) / len(year_temperature[year])
    for year in years
]

if len(years) < 2:
    st.warning("선형회귀 예측을 하려면 서로 다른 연도의 데이터가 2개 이상 필요합니다.")
    st.stop()

# 마지막 관측 연도
latest_year = max(years)

# 마지막 관측 연도의 평균기온
latest_temperature = temperatures[years.index(latest_year)]


# --------------------------------------------------
# 9. 예측 연도 선택
# --------------------------------------------------
st.subheader("🔮 미래 기온 예측")

prediction_year = st.number_input(
    "예측할 연도를 선택하세요.",
    min_value=int(latest_year + 1),
    max_value=2100,
    value=int(min(latest_year + 10, 2100)),
    step=1
)

prediction_year = int(prediction_year)


# --------------------------------------------------
# 10. 선형회귀 계산
# --------------------------------------------------
# y = ax + b
# a: 기울기
# b: y절편

mean_x = sum(years) / len(years)
mean_y = sum(temperatures) / len(temperatures)

numerator = sum(
    (year - mean_x) * (temperature - mean_y)
    for year, temperature in zip(years, temperatures)
)

denominator = sum(
    (year - mean_x) ** 2
    for year in years
)

if denominator == 0:
    st.error("선형회귀 계산에 필요한 연도 데이터가 부족합니다.")
    st.stop()

slope = numerator / denominator
intercept = mean_y - slope * mean_x


# 선형회귀 예측 함수
def predict_temperature(year):
    return slope * year + intercept


predicted_temperature = predict_temperature(prediction_year)


# --------------------------------------------------
# 11. 결정계수 R² 계산
# --------------------------------------------------
predicted_values = [
    predict_temperature(year)
    for year in years
]

ss_res = sum(
    (actual - predicted) ** 2
    for actual, predicted in zip(temperatures, predicted_values)
)

ss_tot = sum(
    (actual - mean_y) ** 2
    for actual in temperatures
)

if ss_tot == 0:
    r_squared = 0
else:
    r_squared = 1 - (ss_res / ss_tot)


# --------------------------------------------------
# 12. 예측 결과 표시
# --------------------------------------------------
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "선택한 월",
        month_names[selected_month]
    )

with col2:
    st.metric(
        f"{prediction_year}년 예측 평균기온",
        f"{predicted_temperature:.2f} ℃"
    )

with col3:
    st.metric(
        "선형회귀 결정계수 R²",
        f"{r_squared:.4f}"
    )

st.caption(
    f"분석에 사용한 실제 데이터: {min(years)}년 ~ {latest_year}년"
)


# --------------------------------------------------
# 13. 그래프 데이터 만들기
# --------------------------------------------------
# 실제 기온과 회귀 추세선을 같은 데이터에 저장합니다.
# forecast는 마지막 관측 연도부터 예측 연도까지 이어지는 선입니다.

chart_data = []

for year, temperature in zip(years, temperatures):
    chart_data.append({
        "year": int(year),
        "actual": float(temperature),
        "fitted": float(predict_temperature(year)),
        "forecast": None
    })

# 마지막 관측 연도에 예측선의 시작점을 추가
chart_data[-1]["forecast"] = float(latest_temperature)

# 미래 예측 연도 추가
chart_data.append({
    "year": prediction_year,
    "actual": None,
    "fitted": None,
    "forecast": float(predicted_temperature)
})


# --------------------------------------------------
# 14. 그래프 그리기
# --------------------------------------------------
st.subheader(
    f"📈 {month_names[selected_month]} 평균기온 및 미래 예측 그래프"
)

chart_spec = {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",

    "description": "서울의 월별 평균기온과 선형회귀 미래 예측 그래프",

    "data": {
        "values": chart_data
    },

    "width": "container",
    "height": 450,

    "layer": [

        # 실제 평균기온: 빨간색 선
        {
            "transform": [
                {"filter": "isValid(datum.actual)"}
            ],
            "mark": {
                "type": "line",
                "color": "red",
                "strokeWidth": 3
            },
            "encoding": {
                "x": {
                    "field": "year",
                    "type": "quantitative",
                    "scale": {
                        "domain": [1907, 2100],
                        "nice": False
                    },
                    "axis": {
                        "title": "연도",
                        "values": [
                            1907, 1920, 1940, 1960, 1980,
                            2000, 2020, 2040, 2060, 2080, 2100
                        ],
                        "labelAngle": -45
                    }
                },
                "y": {
                    "field": "actual",
                    "type": "quantitative",
                    "axis": {
                        "title": "평균기온 (℃)"
                    }
                },
                "order": {
                    "field": "year",
                    "type": "quantitative"
                },
                "tooltip": [
                    {"field": "year", "type": "quantitative", "title": "연도"},
                    {"field": "actual", "type": "quantitative", "title": "실제 평균기온", "format": ".2f"}
                ]
            }
        },

        # 실제 관측 데이터: 회색 점
        {
            "transform": [
                {"filter": "isValid(datum.actual)"}
            ],
            "mark": {
                "type": "point",
                "color": "gray",
                "filled": True,
                "size": 55
            },
            "encoding": {
                "x": {
                    "field": "year",
                    "type": "quantitative",
                    "scale": {
                        "domain": [1907, 2100],
                        "nice": False
                    }
                },
                "y": {
                    "field": "actual",
                    "type": "quantitative"
                },
                "tooltip": [
                    {"field": "year", "type": "quantitative", "title": "연도"},
                    {"field": "actual", "type": "quantitative", "title": "실제 평균기온", "format": ".2f"}
                ]
            }
        },

        # 선형회귀 추세선: 파란색 점선
        {
            "transform": [
                {"filter": "isValid(datum.fitted)"}
            ],
            "mark": {
                "type": "line",
                "color": "blue",
                "strokeWidth": 2,
                "strokeDash": [7, 5]
            },
            "encoding": {
                "x": {
                    "field": "year",
                    "type": "quantitative",
                    "scale": {
                        "domain": [1907, 2100],
                        "nice": False
                    }
                },
                "y": {
                    "field": "fitted",
                    "type": "quantitative"
                },
                "order": {
                    "field": "year",
                    "type": "quantitative"
                },
                "tooltip": [
                    {"field": "year", "type": "quantitative", "title": "연도"},
                    {"field": "fitted", "type": "quantitative", "title": "회귀 예측값", "format": ".2f"}
                ]
            }
        },

        # 미래 예측 구간: 주황색 선
        {
            "transform": [
                {"filter": "isValid(datum.forecast)"}
            ],
            "mark": {
                "type": "line",
                "color": "orange",
                "strokeWidth": 3
            },
            "encoding": {
                "x": {
                    "field": "year",
                    "type": "quantitative",
                    "scale": {
                        "domain": [1907, 2100],
                        "nice": False
                    }
                },
                "y": {
                    "field": "forecast",
                    "type": "quantitative"
                },
                "order": {
                    "field": "year",
                    "type": "quantitative"
                },
                "tooltip": [
                    {"field": "year", "type": "quantitative", "title": "연도"},
                    {"field": "forecast", "type": "quantitative", "title": "예측 평균기온", "format": ".2f"}
                ]
            }
        }
    ],

    "resolve": {
        "scale": {
            "y": "shared"
        }
    }
}

st.vega_lite_chart(
    chart_spec,
    use_container_width=True
)


# --------------------------------------------------
# 15. 그래프 범례 설명
# --------------------------------------------------
st.markdown("### 🎨 그래프 색상 설명")

st.markdown("""
- 🔴 **빨간색 선**: CSV에 기록된 실제 평균기온
- ⚪ **회색 점**: 실제 관측된 평균기온 데이터
- 🔵 **파란색 점선**: 과거 데이터를 바탕으로 계산한 선형회귀 추세선
- 🟠 **주황색 선**: 마지막 관측 연도부터 선택한 미래 연도까지의 예측 구간
""")


# --------------------------------------------------
# 16. 선형회귀 알고리즘 설명
# --------------------------------------------------
st.divider()

st.subheader("🧠 선형회귀 알고리즘이란?")

st.write("""
선형회귀는 과거 데이터의 전체적인 흐름을 가장 잘 나타내는
직선을 찾아 미래 값을 예측하는 알고리즘입니다.

이번 프로그램에서는 연도를 x값으로,
선택한 월의 평균기온을 y값으로 사용합니다.
""")

st.latex(r"y = ax + b")

st.write("""
- **x**: 연도
- **y**: 평균기온
- **a**: 기울기
- **b**: y절편

기울기가 양수이면 시간이 지날수록 평균기온이 높아지는 경향을,
음수이면 낮아지는 경향을 나타냅니다.
""")

st.markdown("### 📐 이번 분석에서 계산된 값")

st.write(f"- 기울기(a): **{slope:.6f}**")
st.write(f"- y절편(b): **{intercept:.4f}**")
st.write(f"- 결정계수(R²): **{r_squared:.4f}**")

st.markdown("### 🔍 선형회귀 계산 과정")

st.write("""
1. 선택한 월의 연도별 평균기온 데이터를 모읍니다.
2. 연도와 평균기온의 평균을 계산합니다.
3. 과거 데이터에 가장 잘 맞는 직선의 기울기와 y절편을 계산합니다.
4. 계산된 직선에 미래 연도를 넣어 예측 평균기온을 구합니다.
""")

st.latex(r"a = \frac{\sum (x_i-\bar{x})(y_i-\bar{y})}{\sum (x_i-\bar{x})^2}")

st.latex(r"b = \bar{y} - a\bar{x}")

st.latex(r"\hat{y} = ax+b")

st.warning(
    "주의: 이 결과는 과거 기온의 선형적인 경향이 미래에도 이어진다고 가정한 "
    "통계적 예측입니다. 실제 미래 기온을 확정적으로 알려주는 값은 아닙니다."
)

st.caption(
    "참고: 현재 CSV 데이터는 1907년부터 시작하지 않습니다. "
    "그래프의 가로축은 1907~2100년으로 표시하지만, 실제 데이터가 없는 기간에는 "
    "관측 선과 점이 나타나지 않습니다."
)
