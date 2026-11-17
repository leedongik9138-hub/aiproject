
import streamlit as st
import pandas as pd
import os

from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler


# --------------------------------
# 1. 페이지 설정
# --------------------------------

st.set_page_config(
    page_title="붓꽃 품종 예측",
    page_icon="🌸",
    layout="wide"
)

st.title("🌸 붓꽃(Iris) 품종 예측 프로그램")

st.write(
    "꽃잎의 길이와 너비를 입력하면 "
    "인공지능이 붓꽃의 품종을 예측해 줍니다!"
)


# --------------------------------
# 2. CSV 파일 경로
# --------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

FILE_PATH = os.path.join(
    BASE_DIR,
    "Iris.csv"
)


# --------------------------------
# 3. CSV 파일 불러오기
# --------------------------------

if not os.path.exists(FILE_PATH):
    st.error("Iris.csv 파일을 찾을 수 없습니다.")
    st.write("찾는 파일 위치:", FILE_PATH)
    st.stop()

try:
    try:
        df = pd.read_csv(
            FILE_PATH,
            encoding="utf-8-sig"
        )
    except UnicodeDecodeError:
        df = pd.read_csv(
            FILE_PATH,
            encoding="cp949"
        )

except Exception as e:
    st.error(f"CSV 파일 읽기 오류: {e}")
    st.stop()


# --------------------------------
# 4. CSV 열 이름 확인
# --------------------------------

df.columns = (
    df.columns.astype(str)
    .str.replace("\ufeff", "", regex=False)
    .str.strip()
)

REQUIRED_COLUMNS = [
    "꽃받침 길이",
    "꽃받침 너비",
    "꽃잎 길이",
    "꽃잎 너비",
    "품종"
]

missing_columns = [
    col for col in REQUIRED_COLUMNS
    if col not in df.columns
]

if missing_columns:
    st.error(
        f"필요한 열을 찾지 못했습니다: {missing_columns}"
    )

    st.write("실제 CSV 열 이름:", df.columns.tolist())
    st.write("CSV 파일 위치:", FILE_PATH)
    st.stop()


# --------------------------------
# 5. 데이터 전처리
# --------------------------------

NUMERIC_COLUMNS = [
    "꽃받침 길이",
    "꽃받침 너비",
    "꽃잎 길이",
    "꽃잎 너비"
]

for col in NUMERIC_COLUMNS:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

df["품종"] = df["품종"].astype(str).str.strip()

df = df.replace(
    [float("inf"), float("-inf")],
    float("nan")
)

df = df.dropna(
    subset=REQUIRED_COLUMNS
)

df = df[df["품종"] != ""]

if len(df) < 2:
    st.error("학습할 데이터가 부족합니다.")
    st.stop()


# --------------------------------
# 6. 데이터 정보
# --------------------------------

st.subheader("📊 데이터 정보")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "전체 데이터 개수",
        len(df)
    )

with col2:
    st.metric(
        "붓꽃 품종 개수",
        df["품종"].nunique()
    )

with col3:
    st.metric(
        "사용하는 특징",
        "2개"
    )

with st.expander("CSV 데이터 확인하기"):
    st.dataframe(
        df,
        use_container_width=True
    )


# --------------------------------
# 7. 인공지능 학습
# --------------------------------

X = df[
    ["꽃잎 길이", "꽃잎 너비"]
]

y = df["품종"]

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)

knn = KNeighborsClassifier(
    n_neighbors=min(5, len(df))
)

knn.fit(X_scaled, y)


# --------------------------------
# 8. 꽃잎 입력
# --------------------------------

st.divider()

st.subheader("🌱 꽃잎 정보 입력하기")

length_min = float(df["꽃잎 길이"].min())
length_max = float(df["꽃잎 길이"].max())

width_min = float(df["꽃잎 너비"].min())
width_max = float(df["꽃잎 너비"].max())

st.info(
    f"""
    꽃잎 길이 범위: {length_min} ~ {length_max} cm

    꽃잎 너비 범위: {width_min} ~ {width_max} cm
    """
)

col1, col2 = st.columns(2)

with col1:
    petal_length = st.number_input(
        "🌸 꽃잎 길이 (cm)",
        min_value=length_min,
        max_value=length_max,
        value=float(df["꽃잎 길이"].median()),
        step=0.1
    )

with col2:
    petal_width = st.number_input(
        "🌸 꽃잎 너비 (cm)",
        min_value=width_min,
        max_value=width_max,
        value=float(df["꽃잎 너비"].median()),
        step=0.1
    )


# --------------------------------
# 9. 품종 예측
# --------------------------------

if st.button(
    "🔍 붓꽃 품종 예측하기",
    use_container_width=True
):

    input_data = pd.DataFrame(
        [[petal_length, petal_width]],
        columns=["꽃잎 길이", "꽃잎 너비"]
    )

    input_scaled = scaler.transform(input_data)

    prediction = knn.predict(input_scaled)

    probabilities = knn.predict_proba(
        input_scaled
    )[0]

    st.success(
        f"🌸 예측 결과: {prediction[0]}"
    )

    st.subheader("📈 품종별 예측 확률")

    probability_df = pd.DataFrame({
        "품종": knn.classes_,
        "예측 확률 (%)": probabilities * 100
    })

    probability_df = probability_df.sort_values(
        "예측 확률 (%)",
        ascending=False
    )

    st.bar_chart(
        probability_df,
        x="품종",
        y="예측 확률 (%)"
    )

    st.dataframe(
        probability_df,
        hide_index=True,
        use_container_width=True
    )


# --------------------------------
# 10. 품종별 꽃잎 분포 그래프
# --------------------------------

st.divider()

st.subheader("📊 붓꽃 품종별 꽃잎 분포")

st.write(
    "가로축은 꽃잎 길이, 세로축은 꽃잎 너비입니다."
)

st.scatter_chart(
    df,
    x="꽃잎 길이",
    y="꽃잎 너비",
    color="품종"
)


# --------------------------------
# 11. 입력한 꽃잎 위치 확인
# --------------------------------

st.divider()

st.subheader("🎯 입력한 꽃잎 위치 확인하기")

input_point = pd.DataFrame({
    "꽃잎 길이": [petal_length],
    "꽃잎 너비": [petal_width],
    "품종": ["입력한 데이터"]
})

plot_df = pd.concat(
    [df, input_point],
    ignore_index=True
)

st.scatter_chart(
    plot_df,
    x="꽃잎 길이",
    y="꽃잎 너비",
    color="품종"
)

st.caption(
    "⭐ 입력한 데이터는 '입력한 데이터' 항목으로 표시됩니다."
)


# --------------------------------
# 12. 마무리
# --------------------------------

st.divider()

st.success(
    "🌸 붓꽃 품종 분석이 준비되었습니다!"
)

st.caption(
    "KNN 알고리즘과 StandardScaler를 활용한 "
    "붓꽃 품종 예측 프로그램"
)
