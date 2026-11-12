
import streamlit as st
import csv
import os
import matplotlib.pyplot as plt

# ---------------------------------
# 1. 페이지 설정
# ---------------------------------

st.set_page_config(
    page_title="서울 기온 예측",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 서울의 월별 평균기온 예측")
st.write(
    "과거 서울의 기온 데이터를 분석하고 "
    "선형회귀 알고리즘으로 미래의 기온을 예측해 보세요!"
)

st.divider()


# ---------------------------------
# 2. CSV 파일 불러오기
# ---------------------------------

FILE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "temperature.csv"
)

if not os.path.exists(FILE_PATH):
    st.error("temperature.csv 파일을 app.py와 같은 폴더에 넣어 주세요.")
    st.stop()

try:
    with open(
        FILE_PATH,
        "r",
        encoding="cp949",
        newline=""
    ) as file:

        reader = csv.DictReader(file)
        data = list(reader)

except Exception as e:
    st.error(f"CSV 파일을 읽을 수 없습니다: {e}")
    st.stop()


# ---------------------------------
# 3. 데이터 정리
# ---------------------------------

month_names = {
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

korean_months = {
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

        month_text, year_text = date_text.split("-")

        month = month_names[month_text]

        year = 2000 + int(year_text)

        temperature = float(row["평균기온(℃)"])

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


# ---------------------------------
# 4. 사용자 입력
# ---------------------------------

st.subheader("🔍 예측 조건 선택")

col1, col2 = st.columns(2)

with col1:
    selected_month = st.selectbox(
        "📅 분석할 월을 선택하세요.",
        list(korean_months.keys()),
        format_func=lambda x: korean_months[x]
    )

with col2:
    latest_year = max(
        item["year"] for item in temperature_data
    )

    prediction_year = st.number_input(
        "🔮 예측할 연도를 입력하세요.",
        min_value=latest_year + 1,
        max_value=2100,
        value=latest_year + 1,
        step=1
    )

st.divider()


# ---------------------------------
# 5. 선택한 월의 데이터 추출
# ---------------------------------

selected_data = [
    item for item in temperature_data
    if item["month"] == selected_month
]

selected_data.sort(key=lambda x: x["year"])

years = [
    item["year"] for item in selected_data
]

temperatures = [
    item["temperature"] for item in selected_data
]

if len(years) < 2:
    st.error("선형회귀 분석을 위해서는 최소 2개의 데이터가 필요합니다.")
    st.stop()


# ---------------------------------
# 6. 선형회귀 알고리즘 구현
# ---------------------------------

# X: 연도
# Y: 평균기온

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
    st.error("회귀선을 계산할 수 없습니다.")
    st.stop()

# 기울기
slope = numerator / denominator

# 절편
intercept = mean_y - slope * mean_x

# 예측 함수
def predict_temperature(year):
    return slope * year + intercept


# 미래 기온 예측
predicted_temperature = predict_temperature(
    prediction_year
)


# ---------------------------------
# 7. 결정계수 R² 계산
# ---------------------------------

predicted_values = [
    predict_temperature(year)
    for year in years
]

ss_total = sum(
    (y - mean_y) ** 2
    for y in temperatures
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
    r_squared = 1 - (ss_residual / ss_total)


# ---------------------------------
# 8. 예측 결과 표시
# ---------------------------------

st.subheader("🎯 기온 예측 결과")

result_col1, result_col2, result_col3 = st.columns(3)

with result_col1:
    st.metric(
        "예측 연도",
        f"{prediction_year}년"
    )

with result_col2:
    st.metric(
        "예측 평균기온",
        f"{predicted_temperature:.2f} ℃"
    )

with result_col3:
    st.metric(
        "결정계수 R²",
        f"{r_squared:.3f}"
    )

st.info(
    f"🌤️ {prediction_year}년 "
    f"{korean_months[selected_month]}의 "
    f"예측 평균기온은 "
    f"**{predicted_temperature:.2f}℃** 입니다."
)


# ---------------------------------
# 9. 선형회귀 그래프
# ---------------------------------

st.subheader("📈 과거 기온과 미래 예측 그래프")

fig, ax = plt.subplots(figsize=(12, 6))

# 실제 기온 데이터
ax.plot(
    years,
    temperatures,
    color="gray",
    marker="o",
    markersize=6,
    linewidth=1.5,
    label="Actual Temperature"
)

# 회귀선에 사용할 연도
regression_years = list(
    range(min(years), int(prediction_year) + 1)
)

regression_temperatures = [
    predict_temperature(year)
    for year in regression_years
]

# 선형회귀 직선
ax.plot(
    regression_years,
    regression_temperatures,
    color="blue",
    linestyle="--",
    linewidth=2.5,
    label="Linear Regression"
)

# 실제 데이터와 회귀선 사이의 오차 표시
for year, actual, fitted in zip(
    years,
    temperatures,
    predicted_values
):
    ax.plot(
        [year, year],
        [actual, fitted],
        color="lightgray",
        linestyle=":",
        linewidth=1
    )

# 미래 예측 지점
ax.scatter(
    prediction_year,
    predicted_temperature,
    color="red",
    marker="*",
    s=250,
    zorder=5,
    label="Predicted Temperature"
)

# 예측 지점에 설명 추가
ax.annotate(
    f"{prediction_year}년 예측\n{predicted_temperature:.2f}℃",
    xy=(prediction_year, predicted_temperature),
    xytext=(10, 15),
    textcoords="offset points",
    color="red",
    fontsize=11,
    fontweight="bold"
)

ax.set_title(
    f"Seoul {korean_months[selected_month]} Average Temperature Prediction",
    fontsize=14
)

ax.set_xlabel("Year", fontsize=12)
ax.set_ylabel("Average Temperature (℃)", fontsize=12)

ax.grid(
    True,
    linestyle="--",
    alpha=0.4
)

ax.legend()

ax.set_xlim(
    min(years) - 0.5,
    prediction_year + 2
)

plt.tight_layout()

st.pyplot(fig)

plt.close(fig)


# ---------------------------------
# 10. 선형회귀 분석 정보
# ---------------------------------

st.subheader("📊 선형회귀 분석 정보")

st.write(
    f"**분석에 사용된 데이터:** {n}개"
)

st.write(
    f"**기울기:** {slope:.4f}"
)

st.write(
    f"**절편:** {intercept:.4f}"
)

st.write(
    f"**회귀식:** Y = {slope:.4f}X + ({intercept:.4f})"
)

st.write(
    f"**결정계수(R²):** {r_squared:.4f}"
)

st.divider()


# ---------------------------------
# 11. 선형회귀 알고리즘 설명
# ---------------------------------

st.subheader("🧠 선형회귀 알고리즘이란?")

st.write("""
선형회귀는 과거의 데이터를 분석하여
미래의 값을 예측하는 머신러닝 알고리즘입니다.

이번 프로그램에서는 과거 서울의 월별 평균기온과
연도 사이의 관계를 분석합니다.
""")

st.markdown("### ① 데이터 학습")

st.write("""
선택한 월의 과거 기온 데이터를 모두 가져옵니다.

- X축: 연도
- Y축: 해당 월의 평균기온

그래프의 회색 점 하나하나가 실제 관측된 기온입니다.
""")

st.markdown("### ② 가장 적합한 직선 찾기")

st.write("""
선형회귀는 실제 데이터 점들과 직선 사이의
오차 제곱의 합이 가장 작아지는 직선을 찾습니다.

그래프의 파란색 점선이 바로 이 회귀선입니다.

회색 점과 파란색 선 사이의 세로 간격은
예측값과 실제값의 차이인 잔차를 나타냅니다.
""")

st.latex(
    r"Y = aX + b"
)

st.write("""
- Y: 예측할 평균기온
- X: 연도
- a: 기울기
- b: 절편

기울기가 양수이면 장기적으로 기온이 상승하는 경향,
음수이면 하락하는 경향을 나타냅니다.
""")

st.markdown("### ③ 미래 기온 예측")

st.write(f"""
과거 데이터로 구한 직선을 사용하여
**{prediction_year}년 {korean_months[selected_month]}**의
평균기온을 예측합니다.

그래프의 빨간색 별표가 미래 예측 지점입니다.
파란색 회귀선을 미래 연도까지 연장한 위치에 표시됩니다.
""")

st.markdown("### ④ 결정계수(R²)란?")

st.write("""
결정계수는 회귀선이 실제 데이터의 변화를
얼마나 잘 설명하는지 나타내는 지표입니다.

- 1에 가까울수록 데이터의 변화와 회귀선이 잘 맞습니다.
- 0에 가까울수록 회귀선이 데이터를 잘 설명하지 못합니다.

단, 결정계수가 높다고 미래 예측이 반드시 정확한 것은 아닙니다.
""")

st.warning(
    "⚠️ 주의: 기온은 기후변화, 자연환경 등 다양한 요인의 영향을 받습니다. "
    "이 프로그램은 과거 기온과 연도 사이의 단순한 선형 관계만을 "
    "이용하므로 실제 미래 기온과 차이가 발생할 수 있습니다."
)

st.divider()

st.caption(
    "🌡️ 서울 기온 예측 프로그램 | 선형회귀 알고리즘 활용"
)
