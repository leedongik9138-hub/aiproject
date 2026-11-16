
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score


# --------------------------------------------------
# 1. 페이지 설정
# --------------------------------------------------

st.set_page_config(
    page_title="붓꽃 품종 예측",
    page_icon="🌸",
    layout="wide"
)

st.title("🌸 인공지능 붓꽃 품종 예측")
st.write("꽃잎의 길이와 너비를 입력하고 어떤 붓꽃인지 예측해 보세요!")


# --------------------------------------------------
# 2. CSV 파일 경로 설정
# --------------------------------------------------

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR.parent

FILE_PATH = PROJECT_DIR / "Iris.csv"


# --------------------------------------------------
# 3. CSV 파일 불러오기
# --------------------------------------------------

@st.cache_data
def load_data(file_path):

    if not file_path.exists():
        raise FileNotFoundError(
            f"CSV 파일을 찾을 수 없습니다: {file_path}"
        )

    try:
        data = pd.read_csv(file_path, encoding="utf-8-sig")

    except UnicodeDecodeError:
        data = pd.read_csv(file_path, encoding="cp949")

    required_columns = [
        "PetalLengthCm",
        "PetalWidthCm",
        "Species"
    ]

    for column in required_columns:
        if column not in data.columns:
            raise ValueError(
                f"CSV 파일에 '{column}' 열이 없습니다."
            )

    return data


try:
    df = load_data(FILE_PATH)

except Exception as e:
    st.error("CSV 파일을 불러오는 중 오류가 발생했습니다.")
    st.error(str(e))
    st.info("Iris.csv가 requirements.txt와 같은 최상위 폴더에 있는지 확인해 주세요.")
    st.stop()


# --------------------------------------------------
# 4. 데이터 전처리
# --------------------------------------------------

df = df.copy()

df["PetalLengthCm"] = pd.to_numeric(
    df["PetalLengthCm"],
    errors="coerce"
)

df["PetalWidthCm"] = pd.to_numeric(
    df["PetalWidthCm"],
    errors="coerce"
)

df["Species"] = df["Species"].astype(str).str.strip()

df = df.dropna(
    subset=[
        "PetalLengthCm",
        "PetalWidthCm",
        "Species"
    ]
)

df = df[
    (df["Species"] != "") &
    (df["Species"] != "nan")
]

if len(df) < 5:
    st.error("예측을 학습하기 위한 데이터가 부족합니다.")
    st.stop()

if df["Species"].nunique() < 2:
    st.error("품종이 2종류 이상 있어야 분류할 수 있습니다.")
    st.stop()


# --------------------------------------------------
# 5. 학습 데이터와 정답 데이터 설정
# --------------------------------------------------

X = df[
    [
        "PetalLengthCm",
        "PetalWidthCm"
    ]
]

y = df["Species"]


# --------------------------------------------------
# 6. KNN 모델 만들기
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

knn_model = Pipeline([
    ("scaler", StandardScaler()),
    ("knn", KNeighborsClassifier(n_neighbors=5))
])

knn_model.fit(X_train, y_train)


# --------------------------------------------------
# 7. 모델 정확도 확인
# --------------------------------------------------

y_pred = knn_model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)

st.subheader("🤖 인공지능 모델 성능")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="모델 정확도",
        value=f"{accuracy * 100:.2f}%"
    )

with col2:
    st.metric(
        label="전체 데이터 개수",
        value=f"{len(df)}개"
    )


# --------------------------------------------------
# 8. 전체 데이터로 최종 모델 학습
# --------------------------------------------------

final_model = Pipeline([
    ("scaler", StandardScaler()),
    ("knn", KNeighborsClassifier(n_neighbors=5))
])

final_model.fit(X, y)


# --------------------------------------------------
# 9. 입력 범위 설정
# --------------------------------------------------

min_length = float(df["PetalLengthCm"].min())
max_length = float(df["PetalLengthCm"].max())

min_width = float(df["PetalWidthCm"].min())
max_width = float(df["PetalWidthCm"].max())


# --------------------------------------------------
# 10. 사용자 입력
# --------------------------------------------------

st.divider()

st.subheader("🌱 붓꽃 정보 입력")

st.write("꽃잎의 길이와 너비를 입력해 주세요.")

col1, col2 = st.columns(2)

with col1:
    st.write("**꽃잎 길이 (cm)**")

    petal_length = st.number_input(
        "꽃잎 길이 입력",
        min_value=min_length,
        max_value=max_length,
        value=float(np.clip(4.0, min_length, max_length)),
        step=0.1,
        key="petal_length"
    )

    st.caption(
        f"입력 가능 범위: {min_length:.1f}cm ~ {max_length:.1f}cm"
    )

with col2:
    st.write("**꽃잎 너비 (cm)**")

    petal_width = st.number_input(
        "꽃잎 너비 입력",
        min_value=min_width,
        max_value=max_width,
        value=float(np.clip(1.2, min_width, max_width)),
        step=0.1,
        key="petal_width"
    )

    st.caption(
        f"입력 가능 범위: {min_width:.1f}cm ~ {max_width:.1f}cm"
    )


# --------------------------------------------------
# 11. 품종 예측
# --------------------------------------------------

if st.button("🔍 붓꽃 품종 예측하기", use_container_width=True):

    input_data = pd.DataFrame({
        "PetalLengthCm": [petal_length],
        "PetalWidthCm": [petal_width]
    })

    prediction = final_model.predict(input_data)[0]

    st.success(f"🌸 예측 결과: **{prediction}**")

    probabilities = final_model.predict_proba(input_data)[0]

    st.subheader("📊 품종별 예측 확률")

    probability_df = pd.DataFrame({
        "품종": final_model.classes_,
        "예측 확률": probabilities
    })

    probability_df["예측 확률"] *= 100

    probability_df = probability_df.sort_values(
        by="예측 확률",
        ascending=False
    )

    st.bar_chart(
        probability_df.set_index("품종")
    )

    for _, row in probability_df.iterrows():
        st.write(
            f"{row['품종']}: {row['예측 확률']:.2f}%"
        )


# --------------------------------------------------
# 12. 품종별 산점도
# --------------------------------------------------

st.divider()

st.subheader("📈 붓꽃 품종별 산점도")

st.write("""
가로축은 꽃잎 길이, 세로축은 꽃잎 너비입니다.
각 점은 실제 붓꽃 데이터를 나타냅니다.
""")

chart_df = df[
    [
        "PetalLengthCm",
        "PetalWidthCm",
        "Species"
    ]
].copy()

chart_df = chart_df.rename(
    columns={
        "PetalLengthCm": "꽃잎 길이",
        "PetalWidthCm": "꽃잎 너비",
        "Species": "품종"
    }
)

st.scatter_chart(
    chart_df,
    x="꽃잎 길이",
    y="꽃잎 너비",
    color="품종",
    size=60
)


# --------------------------------------------------
# 13. 데이터 정보
# --------------------------------------------------

st.divider()

st.subheader("📚 붓꽃 데이터 정보")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("전체 데이터", f"{len(df)}개")

with col2:
    st.metric("붓꽃 품종 수", f"{df['Species'].nunique()}종")

with col3:
    st.metric("사용한 알고리즘", "KNN")

st.write("### 품종별 데이터 개수")

species_count = df["Species"].value_counts()

st.bar_chart(species_count)

with st.expander("📋 원본 데이터 확인하기"):
    st.dataframe(df, use_container_width=True)
