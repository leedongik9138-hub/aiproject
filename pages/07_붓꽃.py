
import streamlit as st
import pandas as pd
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score


# =====================================
# 1. 페이지 설정
# =====================================

st.set_page_config(
    page_title="붓꽃 품종 예측 AI",
    page_icon="🌸",
    layout="wide"
)

st.title("🌸 인공지능 붓꽃 품종 예측")
st.write(
    "꽃잎 길이와 너비를 입력하면 "
    "인공지능이 붓꽃의 품종을 예측합니다!"
)

st.divider()


# =====================================
# 2. CSV 파일 불러오기
# =====================================

FILE_PATH = Path(__file__).parent / "Iris.csv"


@st.cache_data
def load_data(file_path):
    data = pd.read_csv(file_path, encoding="utf-8-sig")
    return data


if not FILE_PATH.exists():
    st.error(
        "Iris.csv 파일을 찾을 수 없습니다.\n\n"
        "app.py와 Iris.csv를 같은 폴더에 넣어 주세요."
    )
    st.stop()


try:
    df = load_data(str(FILE_PATH))

except Exception as e:
    st.error(f"CSV 파일을 읽는 중 오류가 발생했습니다: {e}")
    st.stop()


# =====================================
# 3. 데이터 확인 및 정리
# =====================================

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
        f"CSV 파일에 필요한 열이 없습니다: {missing_columns}"
    )
    st.stop()


df = df[required_columns].copy()

df["PetalLengthCm"] = pd.to_numeric(
    df["PetalLengthCm"], errors="coerce"
)

df["PetalWidthCm"] = pd.to_numeric(
    df["PetalWidthCm"], errors="coerce"
)

df = df.dropna()

df["Species"] = df["Species"].astype(str)

if df.empty or df["Species"].nunique() < 2:
    st.error("분류 학습에 필요한 데이터가 부족합니다.")
    st.stop()


# =====================================
# 4. 학습 데이터와 테스트 데이터 분리
# =====================================

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


# =====================================
# 5. KNN 모델 생성 및 학습
# =====================================

model = Pipeline([
    ("scaler", StandardScaler()),
    ("knn", KNeighborsClassifier(n_neighbors=5))
])


model.fit(X_train, y_train)


# 테스트 데이터 정확도
test_pred = model.predict(X_test)

accuracy = accuracy_score(
    y_test,
    test_pred
)


# 최종 예측을 위해 전체 데이터로 학습
model.fit(X, y)


# =====================================
# 6. 입력 범위 계산
# =====================================

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
    "입력 범위는 Iris.csv에 기록된 실제 관측값의 "
    "최솟값과 최댓값입니다."
)


# =====================================
# 7. 사용자 입력
# =====================================

st.subheader("✏️ 꽃잎 크기 입력")

col1, col2 = st.columns(2)

with col1:
    petal_length = st.number_input(
        "꽃잎 길이 (cm)",
        min_value=length_min,
        max_value=length_max,
        value=4.0,
        step=0.1,
        format="%.1f"
    )

with col2:
    petal_width = st.number_input(
        "꽃잎 너비 (cm)",
        min_value=width_min,
        max_value=width_max,
        value=1.2,
        step=0.1,
        format="%.1f"
    )


# =====================================
# 8. 품종 예측
# =====================================

st.subheader("🔍 붓꽃 품종 예측")

if st.button("🌸 품종 예측하기", type="primary"):

    input_data = pd.DataFrame({
        "PetalLengthCm": [petal_length],
        "PetalWidthCm": [petal_width]
    })

    prediction = model.predict(input_data)[0]

    species_name = prediction.replace("Iris-", "")

    st.success(
        f"🎉 예측 결과: {species_name}"
    )

    st.write(f"꽃잎 길이: {petal_length} cm")
    st.write(f"꽃잎 너비: {petal_width} cm")

    st.metric(
        "모델 테스트 정확도",
        f"{accuracy * 100:.1f}%"
    )

    st.caption(
        "정확도는 테스트 데이터에 대한 평가 결과이며, "
        "개별 예측의 확률은 아닙니다."
    )


# =====================================
# 9. 품종별 산점도 그래프
# =====================================

st.divider()

st.subheader("📊 붓꽃 품종별 꽃잎 크기 그래프")

st.write(
    "가로축은 꽃잎 길이, 세로축은 꽃잎 너비입니다."
)

# 그래프용 데이터 생성
chart_df = df.copy()

chart_df["품종"] = chart_df["Species"].str.replace(
    "Iris-", "", regex=False
)

chart_df["표시 크기"] = 50


# 사용자 입력 위치 추가
input_row = pd.DataFrame({
    "PetalLengthCm": [petal_length],
    "PetalWidthCm": [petal_width],
    "Species": ["사용자 입력"],
    "품종": ["⭐ 사용자 입력"],
    "표시 크기": [250]
})

chart_df = pd.concat(
    [chart_df, input_row],
    ignore_index=True
)


# Streamlit 기본 산점도 그래프
st.scatter_chart(
    chart_df,
    x="PetalLengthCm",
    y="PetalWidthCm",
    color="품종",
    size="표시 크기",
    size_max=250,
    x_label="꽃잎 길이 (cm)",
    y_label="꽃잎 너비 (cm)"
)


# =====================================
# 10. 데이터 정보
# =====================================

st.divider()

st.subheader("📚 데이터 분석 정보")

col1, col2, col3 = st.columns(3)

col1.metric("전체 데이터", f"{len(df)}개")

col2.metric("붓꽃 품종", f"{df['Species'].nunique()}종")

col3.metric("분류 알고리즘", "KNN")

with st.expander("원본 데이터 확인하기"):
    st.dataframe(
        df,
        use_container_width=True
    )

st.caption(
    "Iris 데이터셋을 활용한 머신러닝 교육용 프로그램입니다."
)
