import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from io import BytesIO

st.set_page_config(
    page_title="월별 기온분석",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 월별 기온분석")
st.write("원하는 월을 선택하면 연도별 기온을 비교할 수 있어요!")

# CSV 파일 경로 찾기
APP_DIR = Path(__file__).resolve().parent

CANDIDATE_PATHS = [
    APP_DIR / "temperature.csv",
    APP_DIR.parent / "temperature.csv",
    Path.cwd() / "temperature.csv"
]

CSV_PATH = next(
    (p for p in CANDIDATE_PATHS if p.is_file()),
    None
)


# 데이터 정리
def prepare_data(data):

    required = [
        "일시",
        "최고기온(℃)",
        "최저기온(℃)"
    ]

    for col in required:
        if col not in data.columns:
            raise ValueError(f"CSV에 필요한 열이 없습니다: {col}")

    dates = pd.to_datetime(
        data["일시"].astype(str).str.strip(),
        format="%b-%y",
        errors="coerce"
    )

    data["연도"] = dates.dt.year
    data["월"] = dates.dt.month

    data["최고기온(℃)"] = pd.to_numeric(
        data["최고기온(℃)"],
        errors="coerce"
    )

    data["최저기온(℃)"] = pd.to_numeric(
        data["최저기온(℃)"],
        errors="coerce"
    )

    data = data.dropna(
        subset=[
            "연도",
            "월",
            "최고기온(℃)",
            "최저기온(℃)"
        ]
    ).copy()

    data["연도"] = data["연도"].astype(int)
    data["월"] = data["월"].astype(int)

    return data


# 한글 인코딩 처리
def read_csv_with_encoding(source):

    last_error = None

    for encoding in [
        "cp949",
        "utf-8-sig",
        "euc-kr",
        "utf-8"
    ]:
        try:
            if isinstance(source, bytes):
                data = pd.read_csv(
                    BytesIO(source),
                    encoding=encoding
                )
            else:
                data = pd.read_csv(
                    source,
                    encoding=encoding
                )

            return prepare_data(data)

        except UnicodeDecodeError as error:
            last_error = error

    raise ValueError(
        f"CSV 인코딩 오류: {last_error}"
    )


# 데이터 불러오기
if CSV_PATH is not None:

    try:
        df = read_csv_with_encoding(str(CSV_PATH))
        st.caption(f"데이터 파일 위치: {CSV_PATH}")

    except Exception as error:
        st.error(f"데이터 오류: {error}")
        st.stop()

else:

    st.warning(
        "temperature.csv 파일을 자동으로 찾지 못했습니다."
    )

    st.info(
        "CSV를 app.py와 같은 폴더 또는 "
        "app.py 폴더의 상위 폴더에 넣어 주세요."
    )

    uploaded_file = st.file_uploader(
        "temperature.csv 파일 직접 업로드",
        type=["csv"]
    )

    if uploaded_file is None:
        st.stop()

    try:
        df = read_csv_with_encoding(
            uploaded_file.getvalue()
        )

    except Exception as error:
        st.error(f"CSV 오류: {error}")
        st.stop()


# 월 선택
selected_month = st.selectbox(
    "📅 분석할 월을 선택하세요.",
    options=list(range(1, 13)),
    format_func=lambda month: f"{month}월"
)


# 선택한 월의 데이터
monthly_data = df[
    df["월"] == selected_month
].copy()


# 연도별 평균 계산 및 정렬
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

    # 최고기온 핫핑크
    fig.add_trace(go.Scatter(
        x=monthly_data["연도"],
        y=monthly_data["최고기온(℃)"],
        mode="lines+markers",
        name="최고기온",
        line=dict(
            color="#FF69B4",
            width=3
        ),
        marker=dict(size=7)
    ))

    # 최저기온 파란색
    fig.add_trace(go.Scatter(
        x=monthly_data["연도"],
        y=monthly_data["최저기온(℃)"],
        mode="lines+markers",
        name="최저기온",
        line=dict(
            color="#0000FF",
            width=3
        ),
        marker=dict(size=7)
    ))

    # 그래프 설정
    fig.update_layout(
        title="월별 기온분석",
        xaxis_title="연도",
        yaxis_title="온도(℃)",
        legend_title="범례",
        hovermode="x unified",
        template="plotly_white"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.caption(
        f"선택한 월: {selected_month}월 | "
        f"분석 연도 수: {len(monthly_data)}개"
    )

    with st.expander("📋 그래프 데이터 보기"):

        st.dataframe(
            monthly_data,
            use_container_width=True,
            hide_index=True
        )
