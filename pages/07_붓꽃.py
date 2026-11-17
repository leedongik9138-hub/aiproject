\
import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

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
# 2. CSV 파일 경로 설정
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
    st.write("현재 찾고 있는 위치:", FILE_PATH)
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
# 4. 실제 CSV 열 이름 확인
# --------------------------------

df.columns = df.columns.astype(str).str.strip()

REQUIRED_COLUMNS = [
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

    st.write("실제로 읽은 CSV 열 이름:", df.columns.tolist())
    st.write("읽은 파일 위치:", FILE_PATH)
    st.stop()


# --------------------------------
# 5. 데이터 전처리
# --------------------------------

df["꽃잎 길이"] = pd.to_numeric(
    df["꽃잎 길이"],
    errors="coerce"
)

df["꽃잎 너비"] = pd.to_numeric(
    df["꽃잎 너비"],
    errors="coerce"
)

df["품종"] = df["품종"].astype(str).str.strip()

df = df.dropna(
    subset=[
        "꽃잎 길이",
        "꽃잎 너비",
        "품종"
    ]
)

df = df[
    df["품종"] != ""
]

if len(df) < 2:
    st.error("분석할 데이터가 부족합니다.")
    st.stop()


# --------------------------------
# 6. 데이터 확인
# --------------------------------

st.subheader("📊 데이터 정보")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("전체 데이터 개수", len(df))

with col2:
    st.metric("붓꽃 품종 개수", df["품종"].nunique())

with col3:
    st.metric("분석에 사용하는 변수", 2)

with st.expander("CSV 데이터 확인하기"):
    st.dataframe(df, use_container_width=True)


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
# 8. 입력 범위 설정
# --------------------------------

st.subheader("🌱 꽃잎 정보 입력하기")

petal_length_min = float(df["꽃잎 길이"].min())
petal_length_max = float(df["꽃잎 길이"].max())

petal_width_min = float(df["꽃잎 너비"].min())
petal_width_max = float(df["꽃잎 너비"].max())

st.info(
    f"""
    꽃잎 길이 입력 범위:
    {petal_length_min} ~ {petal_length_max}

    꽃잎 너비 입력 범위:
    {petal_width_min} ~ {petal_width_max}
    """
)

col1, col2 = st.columns(2)

with col1:
    petal_length = st.number_input(
        "🌸 꽃잎 길이 (cm)",
        min_value=petal_length_min,
        max_value=petal_length_max,
        value=float(df["꽃잎 길이"].median()),
        step=0.1
    )

with col2:
    petal_width = st.number_input(
        "🌸 꽃잎 너비 (cm)",
        min_value=petal_width_min,
        max_value=petal_width_max,
        value=float(df["꽃잎 너비"].median()),
        step=0.1
    )


# --------------------------------
# 9. 품종 예측
# --------------------------------

if st.button("🔍 붓꽃 품종 예측하기", use_container_width=True):

    input_data = pd.DataFrame(
        [[petal_length, petal_width]],
        columns=["꽃잎 길이", "꽃잎 너비"]
    )

    input_scaled = scaler.transform(input_data)

    prediction = knn.predict(input_scaled)

    probabilities = knn.predict_proba(input_scaled)[0]

    st.success(
        f"🌸 예측된 붓꽃 품종은 **{prediction[0]}** 입니다!"
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
        probability_df.set_index("품종")
    )


# --------------------------------
# 10. 꽃잎 길이와 너비 산점도
# --------------------------------

st.divider()

st.subheader("📊 붓꽃 품종별 꽃잎 분포")

fig, ax = plt.subplots(figsize=(10, 6))

species_list = sorted(df["품종"].unique())

for species in species_list:

    species_data = df[
        df["품종"] == species
    ]

    ax.scatter(
        species_data["꽃잎 길이"],
        species_data["꽃잎 너비"],
        label=species,
        alpha=0.7,
        s=55
    )

ax.set_xlabel("Petal Length (cm)")
ax.set_ylabel("Petal Width (cm)")

ax.set_title(
    "Iris Species - Petal Length vs Petal Width"
)

ax.legend(title="Species")

ax.grid(alpha=0.3)

st.pyplot(fig)


# --------------------------------
# 11. 입력한 데이터 그래프에 표시
# --------------------------------

st.subheader("🎯 입력한 꽃잎 위치 확인하기")

fig2, ax2 = plt.subplots(figsize=(10, 6))

for species in species_list:

    species_data = df[
        df["품종"] == species
    ]

    ax2.scatter(
        species_data["꽃잎 길이"],
        species_data["꽃잎 너비"],
        label=species,
        alpha=0.5,
        s=45
    )

ax2.scatter(
    petal_length,
    petal_width,
    marker="*",
    s=300,
    color="red",
    edgecolors="black",
    label="입력한 데이터"
)

ax2.set_xlabel("Petal Length (cm)")
ax2.set_ylabel("Petal Width (cm)")

ax2.set_title("Input Data Position")

ax2.legend()

ax2.grid(alpha=0.3)

st.pyplot(fig2)


# --------------------------------
# 12. 마무리
# --------------------------------

st.divider()

st.caption(
    "🌸 KNN 알고리즘과 StandardScaler를 활용한 붓꽃 품종 예측 프로그램"
)
