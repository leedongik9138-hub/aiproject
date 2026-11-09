
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime

# =====================================
# 1. 기본 설정
# =====================================

st.set_page_config(
    page_title="서울 기온 분석",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 서울 기온 분석")
st.write("1907년부터 서울의 기온 변화를 그래프로 확인해 보세요!")

# =====================================
# 2. CSV 파일 경로 찾기
# =====================================

APP_DIR = Path(__file__).resolve().parent

CSV_PATHS = [
    APP_DIR / "temperature.csv",
    APP_DIR.parent / "temperature.csv",
    Path.cwd() / "temperature.csv"
]

CSV_PATH = next(
    (p for p in CSV_PATHS if p.exists()),
    None
)

# =====================================
# 3. CSV 한글 인코딩 처리
# =====================================

def read_csv_file(file_path):

    for encoding in [
        "cp949",
        "utf-8-sig",
        "euc-kr",
        "utf-8"
    ]:
        try:
            return pd.read_csv(
                file_path,
                encoding=encoding
            )
        except UnicodeDecodeError:
            continue

    raise ValueError("CSV 인코딩을 확인해 주세요.")


# =====================================
# 4. 데이터 분석 및 날짜 처리
# =====================================

def prepare_data(data):

    required_columns = [
        "일시",
        "평균기온(℃)",
        "최고기온(℃)",
        "최저기온(℃)"
    ]

    for col in required_columns:
        if col not in data.columns:
            raise ValueError(
                f"CSV에 {col} 열이 없습니다."
            )

    data = data.copy()

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

    # Oct-07 같은 날짜를 실제 연도로 변환
    for value in data["일시"].astype(str):

        try:
            month_text, year_text = value.strip().split("-")

            month = month_map[month_text.title()]
            year = int(year_text)

            if (
                previous_year is not None
                and year < previous_year
            ):
                century += 100

            years.append(century + year)
            months.append(month)

            previous_year = year

        except (ValueError, KeyError):
            years.append(None)
            months.append(None)

    data["연도"] = years
    data["월"] = months

    # 숫자로 변환
    for col in [
        "평균기온(℃)",
        "최고기온(℃)",
        "최저기온(℃)"
    ]:
        data[col] = pd.to_numeric(
            data[col],
            errors="coerce"
        )

    data = data.dropna(
        subset=["연도", "월"]
    )

    data["연도"] = data["연도"].astype(int)
    data["월"] = data["월"].astype(int)

    # 1907년부터 현재 연도까지만 사용
    current_year = min(datetime.now().year, 2026)

    data = data[
        (data["연도"] >= 1907) &
        (data["연도"] <= current_year)
    ]

    # 연도와 월별 평균 계산
    data = (
        data.groupby(
            ["연도", "월"],
            as_index=False
        )[
            [
                "평균기온(℃)",
                "최고기온(℃)",
                "최저기온(℃)"
            ]
        ]
        .mean()
        .sort_values(["연도", "월"])
    )

    return data


# =====================================
# 5. 데이터 불러오기
# =====================================

if CSV_PATH is not None:

    try:
        df = prepare_data(
            read_csv_file(CSV_PATH)
        )

    except Exception as e:
        st.error(f"데이터 오류: {e}")
        st.stop()

else:

    st.warning(
        "temperature.csv 파일을 찾을 수 없습니다."
    )

    uploaded_file = st.file_uploader(
        "temperature.csv 파일 업로드",
        type=["csv"]
    )

    if uploaded_file is None:
        st.stop()

    try:
        for encoding in [
            "cp949",
            "utf-8-sig",
            "euc-kr",
            "utf-8"
        ]:
            try:
                uploaded_file.seek(0)
                raw_data = pd.read_csv(
                    uploaded_file,
                    encoding=encoding
                )
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("CSV 인코딩 오류")

        df = prepare_data(raw_data)

    except Exception as e:
        st.error(f"파일 오류: {e}")
        st.stop()


if df.empty:
    st.error("분석할 데이터가 없습니다.")
    st.stop()


# =====================================
# 6. 분석 기간 표시
# =====================================

st.success(
    f"분석 기간: {df['연도'].min()}년 ~ "
    f"{df['연도'].max()}년"
)

# =====================================
# 7. 월 이름
# =====================================

month_names = [
    "1월", "2월", "3월", "4월",
    "5월", "6월", "7월", "8월",
    "9월", "10월", "11월", "12월"
]

months = list(range(1, 13))


# =====================================
# 8. 서울의 월별 평균기온 그래프
# =====================================

st.header("📊 1. 서울의 월별 평균 기온")

st.write(
    "1907년부터 최신 자료까지 "
    "각 월의 평균기온을 비교합니다."
)

monthly_avg = (
    df.groupby("월")["평균기온(℃)"]
    .mean()
    .reindex(months)
)

fig1 = go.Figure()

fig1.add_trace(
    go.Scatter(
        x=month_names,
        y=monthly_avg.values,
        mode="lines+markers",
        name="월별 평균기온",
        line=dict(
            color="#16A085",
            width=3
        ),
        marker=dict(size=8)
    )
)

fig1.update_layout(
    title="서울의 월별 평균 기온",
    xaxis_title="월",
    yaxis_title="평균 온도(℃)",
    template="plotly_white",
    hovermode="x unified"
)

st.plotly_chart(
    fig1,
    use_container_width=True
)


# =====================================
# 9. 연도 선택
# =====================================

st.header("📈 2. 연도별 최고기온과 최저기온")

available_years = sorted(
    df["연도"].unique().tolist()
)

selected_year = st.selectbox(
    "분석할 연도를 선택하세요.",
    available_years,
    index=len(available_years) - 1
)

year_data = df[
    df["연도"] == selected_year
].set_index("월").reindex(months)


# =====================================
# 10. 연도별 최고기온 최저기온 그래프
# =====================================

fig2 = go.Figure()

fig2.add_trace(
    go.Scatter(
        x=month_names,
        y=year_data["최고기온(℃)"],
        mode="lines+markers",
        name="최고기온",
        line=dict(
            color="#FF69B4",
            width=3
        )
    )
)

fig2.add_trace(
    go.Scatter(
        x=month_names,
        y=year_data["최저기온(℃)"],
        mode="lines+markers",
        name="최저기온",
        line=dict(
            color="#0000FF",
            width=3
        )
    )
)

fig2.update_layout(
    title=f"{selected_year}년 월별 최고기온과 최저기온",
    xaxis_title="월",
    yaxis_title="온도(℃)",
    legend_title="기온 구분",
    template="plotly_white",
    hovermode="x unified"
)

st.plotly_chart(
    fig2,
    use_container_width=True
)


# =====================================
# 11. 두 연도 비교
# =====================================

st.header("🔍 3. 두 연도 기온 비교")

st.write(
    "비교하고 싶은 두 연도를 선택하세요."
)

col1, col2 = st.columns(2)

with col1:

    year1 = st.selectbox(
        "첫 번째 연도",
        available_years,
        index=0,
        key="year1"
    )

with col2:

    compare_years = [
        y for y in available_years
        if y != year1
    ]

    if not compare_years:
        st.warning("비교할 수 있는 연도가 부족합니다.")
        st.stop()

    year2 = st.selectbox(
        "두 번째 연도",
        compare_years,
        index=len(compare_years) - 1,
        key="year2"
    )


# =====================================
# 12. 두 연도 비교 그래프
# =====================================

comparison_types = [
    (
        "평균기온(℃)",
        "월별 평균기온 비교",
        "#FF8C00",
        "#008B8B"
    ),
    (
        "최고기온(℃)",
        "월별 최고기온 비교",
        "#FF69B4",
        "#C2185B"
    ),
    (
        "최저기온(℃)",
        "월별 최저기온 비교",
        "#0000FF",
        "#6495ED"
    )
]

for column, title, color1, color2 in comparison_types:

    fig3 = go.Figure()

    for year, color in [
        (year1, color1),
        (year2, color2)
    ]:

        year_month_data = (
            df[df["연도"] == year]
            .set_index("월")[column]
            .reindex(months)
        )

        fig3.add_trace(
            go.Scatter(
                x=month_names,
                y=year_month_data.values,
                mode="lines+markers",
                name=f"{year}년",
                line=dict(
                    color=color,
                    width=3
                )
            )
        )

    fig3.update_layout(
        title=f"{year1}년 vs {year2}년 {title}",
        xaxis_title="월",
        yaxis_title="온도(℃)",
        legend_title="연도",
        template="plotly_white",
        hovermode="x unified"
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )


# =====================================
# 13. 데이터 확인
# =====================================

with st.expander("📋 분석 데이터 확인"):

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

st.caption(
    "※ 원본 CSV의 기록을 기준으로 연도를 복원하고 "
    "1907년부터 2026년까지의 데이터만 표시합니다."
)
