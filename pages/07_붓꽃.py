
import streamlit as st
import pandas as pd
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score


# =========================================
# 1. 페이지 설정
# =========================================

st.set_page_config(
    page_title="붓꽃 품종 예측 AI",
    page_icon="🌸",
    layout="wide"
)

st.title("🌸 인공지능 붓꽃 품종 예측")
st.write(
    "꽃잎 길이와 너비를 입력하면 "
    "인공지능이 붓꽃 품종을 예측해 줍니다!"
)

st.divider()


# =========================================
# 2. CSV 파일 위치 설정
# =========================================

# 현재 파이썬 파일이 있는 pages 폴더
CURRENT_DIR = Path(__file__).resolve().parent

# pages 폴더의 상위 프로젝트 폴더
PROJECT_DIR = CURRENT_DIR.parent

# CSV 파일이 있을 수 있는 위치
possible_paths = [
    PROJECT_DIR / "iris" / "Iris.csv",
    CURRENT_DIR / "iris" / "Iris.csv",
    PROJECT_DIR / "Iris.csv",
    CURRENT_DIR / "Iris.csv",
    PROJECT_DIR / "iris" / "iris.csv",
    CURRENT_DIR / "iris" / "iris.csv"
]

FILE_PATH = None

for path in possible_paths:
    if path.is_file():
        FILE_PATH = path
        break


# =========================================
# 3. 데이터 불러오기
# =========================================

if FILE_PATH is None:
    st.error("Iris.csv 파일을 찾을 수 없습니다.")

    st.write("확인한 위치:")

    for path in possible_paths:
        st.write(str(path))

    st.info(
        "GitHub에서 iris 폴더 안에 "
        "Iris.csv 파일이 있는지 확인해 주세요."
    )

    st.stop()


@st.cache_data
def load_data(file_path):
    return pd.read_csv(
        file_path,
        encoding="utf-8-sig"
    )


try:
    df = load_data(str(FILE_PATH))

except Exception as e:
    st.error(f"CSV 파일 읽기 오류: {e}")
    st.stop()


# =========================================
# 4. 데이터 확인
# =========================================

required_columns = [
    "PetalLengthCm",
    "PetalWidthCm",
    "Species"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    st.error(
        f"CSV 파일의 열 이름이 올바르지 않습니다: "
        f"{missing_columns}"
    )
    st.write("현재 CSV 열 이름:", list(df.columns))
    st.stop()


df = df[required_columns].copy()

df["PetalLengthCm"] = pd.to_numeric(
    df["PetalLengthCm"],
    errors="coerce"
)

df["PetalWidthCm"] = pd.to_numeric(
    df["PetalWidthCm"],
    errors="coerce"
)

df = df.dropna()

df["Species"] = df["Species"].astype(str).str.strip()

df = df[df["Species"] != ""]

if df.empty:
    st.error("분석할 데이터가 없습니다.")
    st.stop()

if df["Species"].nunique() < 2:
    st.error("품종이 2종류 이상 있어야 학습할 수 있습니다.")
    st.stop()

species_counts = df["Species"].value_counts()

if species_counts.min() < 2:
    st.error("각 품종에 최소 2개 이상의 데이터가 필요합니다.")
    st.stop()


# =========================================
# 5. 학습 데이터와 테스트 데이터 분리
# =========================================

X = df[
    ["PetalLengthCm", "PetalWidthCm"]
]

y = df["Species"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)


# =========================================
# 6. KNN 알고리즘
# =========================================

model = Pipeline([
    ("scaler", StandardScaler()),
    ("knn", KNeighborsClassifier(n_neighbors=5))
])

model.fit(X_train, y_train)

test_prediction = model.predict(X_test)

accuracy = accuracy_score(
    y_test,
    test_prediction
)

# 최종 모델은 전체 데이터로 다시 학습
model.fit(X, y)


# =========================================
# 7. 입력 가능한 범위
# =========================================

length_min = float(df["PetalLengthCm"].min())
length_max = float(df["PetalLengthCm"].max())

width_min = float(df["PetalWidthCm"].min())
width_max = float(df["PetalWidthCm"].max())

st.subheader("📏 입력 가능한 꽃잎 크기")

col1, col2 = st.columns(2)

with col1:
    st.info(
        f"🌷 꽃잎 길이: {length_min} ~ {length_max} cm"
    )

with col2:
    st.info(
        f"🌷 꽃잎 너비: {width_min} ~ {width_max} cm"
    )

st.caption(
    "위 범위는 실제 Iris.csv 데이터의 "
    "최솟값과 최댓값입니다."
)


# =========================================
# 8. 사용자 입력
# =========================================

st.subheader("✏️ 꽃잎 크기 입력")

col1, col2 = st.columns(2)

with col1:
    petal_length = st.number_input(
        "꽃잎 길이 (cm)",
        min_value=length_min,
        max_value=length_max,
        value=min(max(4.0, length_min), length_max),
        step=0.1,
        format="%.1f"
    )

with col2:
    petal_width = st.number_input(
        "꽃잎 너비 (cm)",
        min_value=width_min,
        max_value=width_max,
        value=min(max(1.2, width_min), width_max),
        step=0.1,
        format="%.1f"
    )


# =========================================
# 9. 품종 예측
# =========================================

if st.button("🔍 붓꽃 품종 예측하기", type="primary"):

    input_data = pd.DataFrame({
        "PetalLengthCm": [petal_length],
        "PetalWidthCm": [petal_width]
    })

    prediction = model.predict(input_data)[0]

    species_name = prediction.replace("Iris-", "")

    st.success(
        f"🎉 예측된 붓꽃 품종은 {species_name}입니다!"
    )

    st.write(f"꽃잎 길이: {petal_length} cm")
    st.write(f"꽃잎 너비: {petal_width} cm")

    st.metric(
        "모델 테스트 정확도",
        f"{accuracy * 100:.1f}%"
    )


# =========================================
# 10. 산점도 그래프
# =========================================

st.divider()

st.subheader("📊 붓꽃 품종별 꽃잎 크기 그래프")

st.write(
    "가로축: 꽃잎 길이(cm) / "
    "세로축: 꽃잎 너비(cm)"
)

# 그래프용 데이터
chart_df = df.copy()

chart_df["품종"] = chart_df["Species"].str.replace(
    "Iris-", "",
    regex=False
)

# 사용자 입력값을 그래프에 추가
input_df = pd.DataFrame({
    "PetalLengthCm": [petal_length],
    "PetalWidthCm": [petal_width],
    "품종": ["사용자 입력"]
})

chart_df = pd.concat(
    [
        chart_df[
            ["PetalLengthCm", "PetalWidthCm", "품종"]
        ],
        input_df
    ],
    ignore_index=True
)

st.scatter_chart(
    chart_df,
    x="PetalLengthCm",
    y="PetalWidthCm",
    color="품종",
    x_label="꽃잎 길이 (cm)",
    y_label="꽃잎 너비 (cm)"
)


# =========================================
# 11. 데이터 정보
# =========================================

st.divider()

st.subheader("📚 데이터 분석 정보")

col1, col2, col3 = st.columns(3)

col1.metric(
    "전체 데이터",
    f"{len(df)}개"
)

col2.metric(
    "붓꽃 품종",
    f"{df['Species'].nunique()}종"
)

col3.metric(
    "사용 알고리즘",
    "KNN"
)

with st.expander("원본 데이터 확인하기"):
    st.dataframe(
        df,
        use_container_width=True
    )

st.caption(
    "Iris 데이터셋을 활용한 머신러닝 교육용 프로그램입니다."
)
