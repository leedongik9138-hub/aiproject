
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import re

# ---------------------------------
# 1. 페이지 설정
# ---------------------------------

st.set_page_config(
    page_title="서울시 연령별 인구 분석",
    page_icon="🏙️",
    layout="wide"
)

# ---------------------------------
# 2. 제목
# ---------------------------------

st.title("🏙️ 서울시 연령별 인구 분석")
st.write(
    "행정구역, 성별, 연도를 선택하여 "
    "연령대별 인구 분포를 확인해 보세요!"
)

st.divider()

# ---------------------------------
# 3. CSV 파일 불러오기
# ---------------------------------

FILE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "population.csv"
)

if not os.path.exists(FILE_PATH):
    st.error(
        "population.csv 파일을 app.py와 "
        "같은 폴더에 넣어 주세요."
    )
    st.stop()

try:
    df = pd.read_csv(
        FILE_PATH,
        encoding="cp949",
        thousands=","
    )

except UnicodeDecodeError:
    st.error(
        "CSV 파일의 인코딩을 확인해 주세요. "
        "현재 코드는 CP949 인코딩을 사용합니다."
    )
    st.stop()

except Exception as e:
    st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
    st.stop()

# ---------------------------------
# 4. 행정구역 이름 정리
# ---------------------------------

def clean_district(name):
    name = str(name).strip()

    # 행정구역 코드 제거
    name = re.sub(r"\s*\(\d+\)\s*$", "", name)

    # 서울특별시 글자 정리
    name = name.replace("서울특별시 ", "")

    if name == "서울특별시":
        return "서울특별시 전체"

    return name


df["행정구역명"] = df["행정구역"].apply(
    clean_district
)

district_list = df["행정구역명"].tolist()

# ---------------------------------
# 5. 사용자 선택 메뉴
# ---------------------------------

st.subheader("🔎 분석 조건 선택")

col1, col2, col3 = st.columns(3)

with col1:
    selected_district = st.selectbox(
        "📍 행정구역 선택",
        district_list
    )

with col2:
    selected_gender = st.selectbox(
        "👥 성별 선택",
        ["전체", "남성", "여성"]
    )

with col3:
    selected_year = st.selectbox(
        "📅 연도 선택",
        [2020, 2021, 2022, 2023, 2024, 2025],
        index=5
    )

# ---------------------------------
# 6. 성별에 따른 데이터 구분
# ---------------------------------

gender_dict = {
    "전체": "",
    "남성": "남",
    "여성": "여"
}

gender_code = gender_dict[selected_gender]

# ---------------------------------
# 7. 연령대 설정
# ---------------------------------

age_groups = [
    "0~9세",
    "10~19세",
    "20~29세",
    "30~39세",
    "40~49세",
    "50~59세",
    "60~69세",
    "70~79세",
    "80~89세",
    "90~99세",
    "100세 이상"
]

# ---------------------------------
# 8. 선택한 지역 데이터 찾기
# ---------------------------------

selected_data = df[
    df["행정구역명"] == selected_district
]

if selected_data.empty:
    st.error("선택한 행정구역의 데이터가 없습니다.")
    st.stop()

selected_data = selected_data.iloc[0]

# ---------------------------------
# 9. 연령별 인구 데이터 추출
# ---------------------------------

population = []

for age in age_groups:

    if gender_code == "":
        column_name = (
            f"{selected_year}년_거주자_{age}"
        )

    else:
        column_name = (
            f"{selected_year}년_{gender_code}_거주자_{age}"
        )

    if column_name not in df.columns:
        st.error(
            f"데이터 열을 찾을 수 없습니다: {column_name}"
        )
        st.stop()

    value = pd.to_numeric(
        selected_data[column_name],
        errors="coerce"
    )

    population.append(
        0 if pd.isna(value) else int(value)
    )

# ---------------------------------
# 10. 그래프용 데이터 만들기
# ---------------------------------

chart_df = pd.DataFrame({
    "나이": age_groups,
    "인구 수": population
})

# ---------------------------------
# 11. 인구 정보 표시
# ---------------------------------

total_population = sum(population)

st.divider()

st.subheader("📊 분석 결과")

metric1, metric2, metric3 = st.columns(3)

with metric1:
    st.metric(
        "선택한 행정구역",
        selected_district
    )

with metric2:
    st.metric(
        "선택한 연도",
        f"{selected_year}년"
    )

with metric3:
    st.metric(
        "전체 연령 인구",
        f"{total_population:,}명"
    )

# ---------------------------------
# 12. 민트색 꺾은선 그래프
# ---------------------------------

st.subheader("📈 연령대별 인구 분포")

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=chart_df["나이"],
        y=chart_df["인구 수"],
        mode="lines+markers",
        name="인구 수",

        line=dict(
            color="#65D6C0",
            width=4
        ),

        marker=dict(
            color="#65D6C0",
            size=9,
            line=dict(
                color="#FFFFFF",
                width=1
            )
        ),

        hovertemplate=(
            "나이: %{x}<br>"
            "인구 수: %{y:,}명"
            "<extra></extra>"
        )
    )
)

# ---------------------------------
# 13. 그래프 디자인
# ---------------------------------

fig.update_layout(
    title=dict(
        text=(
            f"{selected_district} "
            f"{selected_gender} "
            f"{selected_year}년 연령별 인구"
        ),
        x=0.5,
        xanchor="center"
    ),

    xaxis=dict(
        title="나이",
        type="category",
        categoryorder="array",
        categoryarray=age_groups,
        tickmode="array",
        tickvals=age_groups,
        showgrid=True,
        gridcolor="#D9E8E4",
        gridwidth=1
    ),

    yaxis=dict(
        title="인구 수 (명)",
        rangemode="tozero",
        dtick=100,
        tickformat=",d",
        showgrid=True,
        gridcolor="#D9E8E4",
        gridwidth=1
    ),

    font=dict(
        family="Malgun Gothic, Apple SD Gothic Neo, sans-serif",
        size=13,
        color="#333333"
    ),

    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",

    hovermode="x unified",

    height=600,

    margin=dict(
        l=60,
        r=30,
        t=80,
        b=80
    )
)

# ---------------------------------
# 14. 스트림릿에 그래프 출력
# ---------------------------------

st.plotly_chart(
    fig,
    use_container_width=True
)

# ---------------------------------
# 15. 데이터 표 출력
# ---------------------------------

with st.expander("📋 연령대별 인구 데이터 확인하기"):

    display_df = chart_df.copy()

    display_df["인구 수"] = display_df[
        "인구 수"
    ].apply(lambda x: f"{x:,}명")

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

# ---------------------------------
# 16. 안내 문구
# ---------------------------------

st.divider()

st.caption(
    "📌 데이터 출처: 제공된 population.csv 파일"
)

st.caption(
    "한글 인코딩: CP949 | 그래프 색상: Mint"
)

st.success("인구 분석이 완료되었습니다! 😊")
