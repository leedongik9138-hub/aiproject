
import streamlit as st
import csv
import os


# ==================================================
# 1. 페이지 설정
# ==================================================
st.set_page_config(
    page_title="서울 미래 기온 예측",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 서울 월별 평균기온 및 미래 예측")
st.write(
    "1907~2026년 실제 기온 자료를 바탕으로 "
    "2027~2100년의 평균기온을 예측합니다."
)


# ==================================================
# 2. CSV 파일 경로
# ==================================================
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

FILE_PATH = os.path.join(BASE_DIR, "temperature.csv")

if not os.path.exists(FILE_PATH):
    st.error("temperature.csv 파일을 찾을 수 없습니다.")
    st.info(
        "temperature.csv 파일을 app.py와 같은 폴더에 넣어 주세요."
    )
    st.stop()


# ==================================================
# 3. CSV 파일 읽기
# ==================================================
def read_csv_file(file_path):
    encodings = ["cp949", "euc-kr", "utf-8-sig", "utf-8"]

    last_error = None

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

        except UnicodeDecodeError as error:
            last_error = error

    raise ValueError(
        f"CSV 파일의 인코딩을 읽을 수 없습니다: {last_error}"
    )


try:
    rows, columns = read_csv_file(FILE_PATH)

except Exception as error:
    st.error(f"CSV 파일 읽기 오류: {error}")
    st.stop()


# ==================================================
# 4. 필요한 열 확인
# ==================================================
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
    st.write("현재 CSV 열 이름:", columns)
    st.stop()


# ==================================================
# 5. 월 이름과 숫자 연결
# ==================================================
month_map = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12
}

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


# ==================================================
# 6. 원본 날짜를 실제 연도로 복원
# ==================================================
# 원본 날짜 형식: Oct-07, Jan-08, ... Dec-99, Jan-00
#
# 첫 번째 연도 07은 1907년으로 해석합니다.
# 99 다음에 00이 나오면 2000년대로 넘어갑니다.
# 따라서 07은 1907년, 26은 2026년이 됩니다.

temperature_data = []

century = 1900
previous_year_suffix = None

for row in rows:

    date_text = str(row.get("일시", "")).strip()
    temperature_text = str(
        row.get("평균기온(℃)", "")
    ).strip()

    if not date_text or not temperature_text:
        continue

    try:
        month_text, year_text = date_text.split("-")

        month_text = month_text.strip().title()
        year_suffix = int(year_text.strip())

        if month_text not in month_map:
            continue

        if not 0 <= year_suffix <= 99:
            continue

        # 연도 숫자가 99에서 00처럼 작아지면 세기를 올림
        if (
            previous_year_suffix is not None
            and year_suffix < previous_year_suffix
        ):
            century += 100

        actual_year = century + year_suffix
        actual_month = month_map[month_text]

        temperature = float(
            temperature_text.replace(",", "")
        )

        # 원본에서 요청한 1907~2026년 자료만 사용
        if 1907 <= actual_year <= 2026:
            temperature_data.append({
                "year": actual_year,
                "month": actual_month,
                "temperature": temperature
            })

        previous_year_suffix = year_suffix

    except (ValueError, TypeError):
        continue


if not temperature_data:
    st.error("날짜와 평균기온 데이터를 읽지 못했습니다.")
    st.stop()


# ==================================================
# 7. 실제 자료 기간 확인
# ==================================================
all_years = [
    item["year"]
    for item in temperature_data
]

actual_start_year = min(all_years)
actual_end_year = max(all_years)

st.success(
    f"✅ 원본 자료 확인 완료: "
    f"{actual_start_year}년 ~ {actual_end_year}년"
)


# ==================================================
# 8. 월 선택
# ==================================================
selected_month = st.selectbox(
    "📅 분석하고 예측할 월을 선택하세요.",
    options=list(range(1, 13)),
    format_func=lambda month: month_names[month]
)


# ==================================================
# 9. 선택한 월의 연도별 평균기온 계산
# ==================================================
monthly_data = [
    item for item in temperature_data
    if item["month"] == selected_month
]

if not monthly_data:
    st.warning("선택한 월의 기온 자료가 없습니다.")
    st.stop()


year_temperature = {}

for item in monthly_data:

    year = item["year"]
    temperature = item["temperature"]

    if year not in year_temperature:
        year_temperature[year] = []

    year_temperature[year].append(temperature)


# 연도순 정렬
years = sorted(year_temperature.keys())

# 같은 연도에 같은 월이 여러 개 있으면 평균 계산
temperatures = [
    sum(year_temperature[year]) / len(year_temperature[year])
    for year in years
]

if len(years) < 3:
    st.warning("회귀 분석에 사용할 데이터가 부족합니다.")
    st.stop()

latest_year = max(years)


# ==================================================
# 10. 예측 연도 입력
# ==================================================
st.divider()
st.subheader("🔮 미래 예측 연도 선택")

st.info(
    "실제 기온 자료는 1907~2026년이며, "
    "예측 연도는 2027~2100년 중에서 선택할 수 있습니다."
)

prediction_year = st.number_input(
    "예측할 연도를 입력하세요.",
    min_value=2027,
    max_value=2100,
    value=2027,
    step=1,
    format="%d",
    key="prediction_year_2027_to_2100",
    help="2027년부터 2100년까지 입력할 수 있습니다."
)

prediction_year = int(prediction_year)


# ==================================================
# 11. 선형회귀
# ==================================================
def fit_linear_regression(x_values, y_values):

    mean_x = sum(x_values) / len(x_values)
    mean_y = sum(y_values) / len(y_values)

    numerator = sum(
        (x - mean_x) * (y - mean_y)
        for x, y in zip(x_values, y_values)
    )

    denominator = sum(
        (x - mean_x) ** 2
        for x in x_values
    )

    if denominator == 0:
        raise ValueError("선형회귀 계산에 실패했습니다.")

    slope = numerator / denominator
    intercept = mean_y - slope * mean_x

    def predict(x):
        return slope * x + intercept

    return predict


# ==================================================
# 12. 다항 회귀 계산에 필요한 연립방정식
# ==================================================
def solve_linear_system(matrix, values):

    n = len(values)

    augmented = [
        list(matrix[i]) + [values[i]]
        for i in range(n)
    ]

    for col in range(n):

        pivot_row = max(
            range(col, n),
            key=lambda row: abs(augmented[row][col])
        )

        if abs(augmented[pivot_row][col]) < 1e-12:
            raise ValueError("다항 회귀 계산에 실패했습니다.")

        augmented[col], augmented[pivot_row] = (
            augmented[pivot_row],
            augmented[col]
        )

        pivot = augmented[col][col]

        for j in range(col, n + 1):
            augmented[col][j] /= pivot

        for row in range(n):

            if row == col:
                continue

            factor = augmented[row][col]

            for j in range(col, n + 1):
                augmented[row][j] -= (
                    factor * augmented[col][j]
                )

    return [
        augmented[i][n]
        for i in range(n)
    ]


# ==================================================
# 13. 다항 회귀 (2차)
# ==================================================
def fit_polynomial_regression(x_values, y_values):

    if len(x_values) < 3:
        raise ValueError(
            "다항 회귀에는 데이터가 3개 이상 필요합니다."
        )

    center = sum(x_values) / len(x_values)

    t_values = [
        x - center
        for x in x_values
    ]

    n = len(t_values)

    sum_t = sum(t_values)
    sum_t2 = sum(t ** 2 for t in t_values)
    sum_t3 = sum(t ** 3 for t in t_values)
    sum_t4 = sum(t ** 4 for t in t_values)

    sum_y = sum(y_values)

    sum_ty = sum(
        t * y
        for t, y in zip(t_values, y_values)
    )

    sum_t2y = sum(
        (t ** 2) * y
        for t, y in zip(t_values, y_values)
    )

    matrix = [
        [n, sum_t, sum_t2],
        [sum_t, sum_t2, sum_t3],
        [sum_t2, sum_t3, sum_t4]
    ]

    values = [
        sum_y,
        sum_ty,
        sum_t2y
    ]

    a, b, c = solve_linear_system(matrix, values)

    def predict(x):
        t = x - center
        return a + b * t + c * (t ** 2)

    return predict


# ==================================================
# 14. 의사결정나무 회귀
# ==================================================
def fit_decision_tree_regression(
    x_values,
    y_values,
    max_depth=3,
    min_leaf=2
):

    training_data = sorted(
        zip(x_values, y_values),
        key=lambda item: item[0]
    )

    def average(values):
        return sum(values) / len(values)

    def calculate_sse(values):

        mean_value = average(values)

        return sum(
            (value - mean_value) ** 2
            for value in values
        )

    def build_tree(data, depth):

        y_list = [
            item[1]
            for item in data
        ]

        node_mean = average(y_list)

        if (
            depth >= max_depth
            or len(data) < min_leaf * 2
        ):
            return {
                "type": "leaf",
                "value": node_mean
            }

        unique_x = sorted(
            set(item[0] for item in data)
        )

        if len(unique_x) < 2:
            return {
                "type": "leaf",
                "value": node_mean
            }

        best_threshold = None
        best_error = calculate_sse(y_list)
        best_left = None
        best_right = None

        thresholds = [
            (unique_x[i] + unique_x[i + 1]) / 2
            for i in range(len(unique_x) - 1)
        ]

        for threshold in thresholds:

            left_data = [
                item for item in data
                if item[0] <= threshold
            ]

            right_data = [
                item for item in data
                if item[0] > threshold
            ]

            if (
                len(left_data) < min_leaf
                or len(right_data) < min_leaf
            ):
                continue

            left_y = [
                item[1] for item in left_data
            ]

            right_y = [
                item[1] for item in right_data
            ]

            error = (
                calculate_sse(left_y)
                + calculate_sse(right_y)
            )

            if error < best_error:

                best_error = error
                best_threshold = threshold
                best_left = left_data
                best_right = right_data

        if best_threshold is None:
            return {
                "type": "leaf",
                "value": node_mean
            }

        return {
            "type": "node",
            "threshold": best_threshold,
            "left": build_tree(best_left, depth + 1),
            "right": build_tree(best_right, depth + 1)
        }

    tree = build_tree(training_data, 0)

    def predict_one(x, node):

        if node["type"] == "leaf":
            return node["value"]

        if x <= node["threshold"]:
            return predict_one(x, node["left"])

        return predict_one(x, node["right"])

    def predict(x):
        return predict_one(x, tree)

    return predict


# ==================================================
# 15. 세 가지 알고리즘 학습
# ==================================================
try:

    linear_predict = fit_linear_regression(
        years,
        temperatures
    )

    polynomial_predict = fit_polynomial_regression(
        years,
        temperatures
    )

    tree_predict = fit_decision_tree_regression(
        years,
        temperatures
    )

except Exception as error:
    st.error(f"회귀 알고리즘 계산 오류: {error}")
    st.stop()


# ==================================================
# 16. 알고리즘 선택
# ==================================================
st.divider()
st.subheader("🧠 회귀 알고리즘 선택")

algorithm_names = [
    "선형회귀",
    "다항 회귀 (2차)",
    "의사결정나무 회귀"
]

selected_algorithm = st.selectbox(
    "사용할 회귀 알고리즘을 선택하세요.",
    algorithm_names
)

predictors = {
    "선형회귀": linear_predict,
    "다항 회귀 (2차)": polynomial_predict,
    "의사결정나무 회귀": tree_predict
}

selected_predict = predictors[selected_algorithm]


# ==================================================
# 17. 예측값 계산
# ==================================================
linear_value = linear_predict(prediction_year)

polynomial_value = polynomial_predict(
    prediction_year
)

tree_value = tree_predict(prediction_year)

selected_value = selected_predict(
    prediction_year
)


# ==================================================
# 18. 예측 결과 표시
# ==================================================
st.divider()

st.subheader(
    f"📊 {prediction_year}년 {month_names[selected_month]} 예측 결과"
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "선택한 알고리즘",
        selected_algorithm
    )

with col2:
    st.metric(
        "예측 평균기온",
        f"{selected_value:.2f} ℃"
    )

with col3:
    st.metric(
        "사용한 실제 자료",
        f"{min(years)}~{latest_year}년"
    )


# ==================================================
# 19. 세 알고리즘 예측값 비교
# ==================================================
st.subheader("🔍 세 가지 알고리즘 예측값 비교")

comparison_data = [
    {
        "회귀 알고리즘": "선형회귀",
        "예측 평균기온(℃)": round(linear_value, 2)
    },
    {
        "회귀 알고리즘": "다항 회귀 (2차)",
        "예측 평균기온(℃)": round(polynomial_value, 2)
    },
    {
        "회귀 알고리즘": "의사결정나무 회귀",
        "예측 평균기온(℃)": round(tree_value, 2)
    }
]

st.table(comparison_data)


# ==================================================
# 20. 결정계수 R² 계산
# ==================================================
fitted_values = [
    selected_predict(year)
    for year in years
]

mean_temperature = (
    sum(temperatures) / len(temperatures)
)

ss_res = sum(
    (actual - predicted) ** 2
    for actual, predicted in zip(
        temperatures,
        fitted_values
    )
)

ss_tot = sum(
    (actual - mean_temperature) ** 2
    for actual in temperatures
)

if ss_tot == 0:
    r_squared = 0
else:
    r_squared = 1 - (ss_res / ss_tot)

st.metric(
    f"{selected_algorithm} 결정계수 R²",
    f"{r_squared:.4f}"
)


# ==================================================
# 21. 그래프 데이터 생성
# ==================================================
actual_by_year = {
    year: temperature
    for year, temperature in zip(
        years,
        temperatures
    )
}

chart_data = []

# 1907년부터 선택한 예측 연도까지 모델값 계산
for year in range(1907, prediction_year + 1):

    actual_value = actual_by_year.get(year)

    model_value = selected_predict(year)

    forecast_value = None

    # 마지막 실제 관측 연도
    if year == latest_year:
        forecast_value = selected_predict(year)

    # 사용자가 입력한 미래 예측 연도
    if year == prediction_year:
        forecast_value = selected_predict(year)

    chart_data.append({
        "year": year,
        "actual": actual_value,
        "model": model_value,
        "forecast": forecast_value
    })


# ==================================================
# 22. 그래프 표시
# ==================================================
st.divider()

st.subheader(
    f"📈 {month_names[selected_month]} 평균기온 그래프"
)

chart_spec = {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",

    "data": {
        "values": chart_data
    },

    "width": "container",
    "height": 450,

    "layer": [

        # 실제 평균기온 빨간 선
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
                            1907, 1920, 1940, 1960,
                            1980, 2000, 2020, 2040,
                            2060, 2080, 2100
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
                    {
                        "field": "year",
                        "type": "quantitative",
                        "title": "연도"
                    },
                    {
                        "field": "actual",
                        "type": "quantitative",
                        "title": "실제 평균기온",
                        "format": ".2f"
                    }
                ]
            }
        },

        # 실제 관측값 회색 점
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
                    {
                        "field": "year",
                        "type": "quantitative",
                        "title": "연도"
                    },
                    {
                        "field": "actual",
                        "type": "quantitative",
                        "title": "실제 평균기온",
                        "format": ".2f"
                    }
                ]
            }
        },

        # 선택한 알고리즘의 추세선
        {
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
                    "field": "model",
                    "type": "quantitative"
                },

                "order": {
                    "field": "year",
                    "type": "quantitative"
                },

                "tooltip": [
                    {
                        "field": "year",
                        "type": "quantitative",
                        "title": "연도"
                    },
                    {
                        "field": "model",
                        "type": "quantitative",
                        "title": "알고리즘 계산값",
                        "format": ".2f"
                    }
                ]
            }
        },

        # 마지막 실제 관측 연도부터 예측 연도까지 주황색 선
        {
            "transform": [
                {"filter": "isValid(datum.forecast)"}
            ],

            "mark": {
                "type": "line",
                "color": "orange",
                "strokeWidth": 4,
                "point": True
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
                    {
                        "field": "year",
                        "type": "quantitative",
                        "title": "연도"
                    },
                    {
                        "field": "forecast",
                        "type": "quantitative",
                        "title": "미래 예측 평균기온",
                        "format": ".2f"
                    }
                ]
            }
        }
    ]
}

st.vega_lite_chart(
    None,
    chart_spec,
    use_container_width=True
)


# ==================================================
# 23. 그래프 범례
# ==================================================
st.markdown("### 🎨 그래프 색상 설명")

st.markdown("""
- 🔴 **빨간색 선**: 원본 CSV의 실제 평균기온
- ⚪ **회색 점**: 실제 관측된 평균기온
- 🔵 **파란색 점선**: 선택한 알고리즘의 계산 추세
- 🟠 **주황색 선**: 마지막 실제 관측 연도부터 예측 연도까지
""")


# ==================================================
# 24. 알고리즘 설명
# ==================================================
st.divider()

st.subheader("🧠 회귀 알고리즘 설명")

st.markdown("### 1. 선형회귀")

st.write("""
과거 기온의 전체적인 흐름을 직선으로 나타내는 방법입니다.
기온이 일정한 방향으로 증가하거나 감소하는 경향을 표현합니다.
""")

st.latex(r"y = ax + b")


st.markdown("### 2. 다항 회귀 (2차)")

st.write("""
직선이 아닌 곡선으로 데이터의 흐름을 나타내는 방법입니다.
기온의 변화가 곡선 형태일 때 선형회귀와 다른 결과를 보여줄 수 있습니다.
""")

st.latex(r"y = a + bt + ct^2")


st.markdown("### 3. 의사결정나무 회귀")

st.write("""
데이터를 여러 구간으로 나누고 각 구간에 포함된 기온의 평균을 이용합니다.
구간에 따라 예측값이 달라지며 계단식 그래프가 나타날 수 있습니다.
학습 데이터의 범위를 벗어난 미래에는 마지막 구간의 평균값을 사용합니다.
""")


st.markdown("### 📌 알고리즘별 특징 비교")

st.table([
    {
        "알고리즘": "선형회귀",
        "예측 방식": "직선",
        "특징": "일정한 증가 또는 감소 경향"
    },
    {
        "알고리즘": "다항 회귀 (2차)",
        "예측 방식": "곡선",
        "특징": "휘어지는 변화 경향"
    },
    {
        "알고리즘": "의사결정나무 회귀",
        "예측 방식": "구간별 평균",
        "특징": "계단식 변화"
    }
])


# ==================================================
# 25. 주의사항
# ==================================================
st.warning("""
이 프로그램의 결과는 과거 기온 자료를 이용한 통계적 예측입니다.
실제 미래 기온을 확정적으로 알려주는 값은 아닙니다.

특히 다항 회귀는 먼 미래로 갈수록 예측 곡선이 크게 변할 수 있고,
의사결정나무 회귀는 학습 자료 범위 밖에서 마지막 구간의 평균값을 예측합니다.
""")

st.caption(
    "원본 자료의 날짜는 1907년 10월부터 2026년 10월까지입니다. "
    "따라서 2026년 11월과 12월의 실제 관측값은 원본 자료에 포함되어 있지 않습니다."
)
