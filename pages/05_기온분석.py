import os
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(
    page_title="월별 기온분석",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 월별 기온분석")
st.write("원하는 월을 선택하면 연도별 최고기온과 최저기온을 비교할 수 있어요!")

FILE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "temperature.csv"
)

@st.cache_data
def load_data(file_path):
    data = None

    for encoding in ["cp949", "utf-8-sig", "euc-kr", "utf-8"]:
        try:
            data = pd.read_csv(file_path, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue

    if data is None:
        raise ValueError("CSV 인코딩을 확인해 주세요.")

    required = ["일시", "최고기온(℃)", "최저기온(℃)"]

    for col in required:
        if col not in data.columns:
            raise ValueError(f"필요한 열이 없습니다: {col}")

    month_map = {
        "Jan": 1, "Feb": 2, "Mar": 3,
        "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9,
        "Oct": 10, "Nov": 11, "Dec": 12
    }

    years = []
    months = []
    century = 1900
    previous_year = None

    for value in data["일시"].astype(str):
        try:
            month_text, year_text = value.strip().split("-")
            month = month_map[month_text]
            year = int(year_text)

            if previous_year is not None and year < previous_year:
                century += 100

            years.append(century + year)
            months.append(month)
            previous_year = year

        except (ValueError, KeyError):
            years.append(None)
            months.append(None)

    data["연도"] = years
    data["월"] = months

    data["최고기온(℃)"] = pd.to_numeric(
        data["최고기온(℃)"], errors="coerce"
    )

    data["최저기온(℃)"] = pd.to_numeric(
        data["최저기온(℃)"], errors="coerce"
    )

    data = data.dropna(
        subset=["연도", "월", "최고기온(℃)", "최저기온(℃)"]
    )

    data["연도"] = data["연도"].astype(int)
    data["월"] = data["월"].astype(int)

    return data


if not os.path.exists(FILE_PATH):
    st.error("temperature.csv 파일을 app.py와 같은 폴더에 넣어 주세요.")
    st.stop()

try:
    df = load_data(FILE_PATH)
except Exception as error:
    st.error(f"데이터를 불러오는 중 문제가 발생했습니다: {error}")
    st.stop()


# 월 선택
selected_month = st.selectbox(
    "📅 분석할 월을 선택하세요.",
    options=list(range(1, 13)),
    format_func=lambda month: f"{month}월"
)


# 선택한 월의 데이터 추출
monthly_data = df[df["월"] == selected_month].copy()

monthly_data = monthly_data.sort_values("연도")

# 같은 연도에 여러 데이터가 있다면 평균 계산
monthly_data = (
    monthly_data.groupby("연도", as_index=False)[
        ["최고기온(℃)", "최저기온(℃)"]
    ]
    .mean()
    .sort_values("연도")
)


if monthly_data.empty:
    st.warning("선택한 월의 데이터가 없습니다.")

else:
    fig = go.Figure()

    # 최고기온: 핫핑크
    fig.add_trace(go.Scatter(
        x=monthly_data["연도"],
        y=monthly_data["최고기온(℃)"],
        mode="lines+markers",
        name="최고기온",
        line=dict(color="#FF69B4", width=3),
        marker=dict(size=6)
    ))

    # 최저기온: 파란색
    fig.add_trace(go.Scatter(
        x=monthly_data["연도"],
        y=monthly_data["최저기온(℃)"],
        mode="lines+markers",
        name="최저기온",
        line=dict(color="#0000FF", width=3),
        marker=dict(size=6)
    ))

    # 그래프 설정
    fig.update_layout(
        title="월별 기온분석",
        xaxis_title="연도",
        yaxis_title="온도(℃)",
        legend_title="기온 구분",
        hovermode="x unified",
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        f"선택한 월: {selected_month}월 | "
        f"분석 연도 수: {len(monthly_data)}개"
    )

    with st.expander("📋 그래프에 사용된 데이터 보기"):
        st.dataframe(
            monthly_data,
            use_container_width=True,
            hide_index=True
        )
