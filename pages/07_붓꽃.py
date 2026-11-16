
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.metrics import accuracy_score


# --------------------------------
# 1. 페이지 설정
# --------------------------------

st.set_page_config(
    page_title="붓꽃 품종 예측 AI",
    page_icon="🌸",
    layout="wide"
)

st.title("🌸 인공지능 붓꽃 품종 예측 프로그램")

st.write(
    "꽃잎의 길이와 너비를 입력하면 "
    "인공지능이 붓꽃의 품종을 예측해 줍니다!"
)

st.divider()


# --------------------------------
# 2. 데이터 불러오기
# --------------------------------

@st.cache_data
def load_data():
    df = pd.read_csv("Iris.csv")
    return df


try:
    df = load_data()

except Exception:
    st.error(
        "Iris.csv 파일을 찾을 수 없습니다. "
        "app.py와 같은 폴더에 넣어 주세요."
    )
    st.stop()


# 사용할 데이터 확인
required_columns = [
    "PetalLengthCm",
    "PetalWidthCm",
    "Species"
]

if not all(col in df.columns for col in required_columns):
    st.error("CSV 파일의 열 이름을 확인해 주세요.")
    st.stop()

df = df.dropna(subset=required_columns).copy()


# --------------------------------
# 3. 학습 데이터 설정
# --------------------------------

X = df[
    ["PetalLengthCm", "PetalWidthCm"]
]

y = df["Species"]


# 학습 데이터와 테스트 데이터 분리
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)


# --------------------------------
# 4. KNN 분류 모델 생성
# --------------------------------

model = make_pipeline(
    StandardScaler(),
    KNeighborsClassifier(n_neighbors=5)
)


# 모델 학습 및 성능 평가
model.fit(X_train, y_train)

test_prediction = model.predict(X_test)

accuracy = accuracy_score(
    y_test,
    test_prediction
)


# 최종 예측을 위해 전체 데이터로 재학습
model.fit(X, y)


# --------------------------------
# 5. 데이터 입력 범위
# --------------------------------

petal_length_min = float(
    df["PetalLengthCm"].min()
)

petal_length_max = float(
    df["PetalLengthCm"].max()
)

petal_width_min = float(
    df["PetalWidthCm"].min()
)

petal_width_max = float(
    df["PetalWidthCm"].max()
)


st.subheader("📏 입력 가능한 꽃잎 크기")

col1, col2 = st.columns(2)

with col1:
    st.info(
        f"🌷 꽃잎 길이: "
        f"{petal_length_min} ~ {petal_length_max} cm"
    )

with col2:
    st.info(
        f"🌷 꽃잎 너비: "
        f"{petal_width_min} ~ {petal_width_max} cm"
    )

st.caption(
    "※ 입력 범위는 업로드한 데이터에서 관측된 "
    "최솟값과 최댓값을 기준으로 합니다."
)


# --------------------------------
# 6. 사용자 입력
# --------------------------------

st.subheader("✏️ 꽃잎 크기 입력")

col1, col2 = st.columns(2)

with col1:
    petal_length = st.number_input(
        "꽃잎 길이 (cm)",
        min_value=petal_length_min,
        max_value=petal_length_max,
        value=4.0,
        step=0.1,
        format="%.1f"
    )

with col2:
    petal_width = st.number_input(
        "꽃잎 너비 (cm)",
        min_value=petal_width_min,
        max_value=petal_width_max,
        value=1.2,
        step=0.1,
        format="%.1f"
    )


# --------------------------------
# 7. 품종 예측
# --------------------------------

if st.button("🔍 붓꽃 품종 예측하기", type="primary"):

    input_data = pd.DataFrame(
        [[petal_length, petal_width]],
        columns=[
            "PetalLengthCm",
            "PetalWidthCm"
        ]
    )

    prediction = model.predict(input_data)[0]

    species_name = prediction.replace("Iris-", "")

    st.divider()

    st.subheader("🎉 인공지능 예측 결과")

    st.success(
        f"예측된 붓꽃 품종은 **{species_name}** 입니다!"
    )

    st.write(f"🌷 꽃잎 길이: {petal_length} cm")
    st.write(f"🌷 꽃잎 너비: {petal_width} cm")

    st.metric(
        "모델 테스트 정확도",
        f"{accuracy * 100:.1f}%"
    )

    st.caption(
        "테스트 정확도는 데이터를 8:2로 나누어 "
        "평가한 결과이며, 개별 예측의 확률을 의미하지 않습니다."
    )


# --------------------------------
# 8. 품종별 꽃잎 분포 그래프
# --------------------------------

st.divider()

st.subheader("📊 붓꽃 품종별 꽃잎 크기 분포")

st.write(
    "가로축은 꽃잎 길이, 세로축은 꽃잎 너비입니다. "
    "색깔별로 붓꽃 품종을 구분합니다."
)

fig, ax = plt.subplots(figsize=(10, 6))

colors = {
    "Iris-setosa": "blue",
    "Iris-versicolor": "green",
    "Iris-virginica": "orange"
}

for species, color in colors.items():

    species_data = df[df["Species"] == species]

    if len(species_data) > 0:

        ax.scatter(
            species_data["PetalLengthCm"],
            species_data["PetalWidthCm"],
            color=color,
            label=species.replace("Iris-", ""),
            alpha=0.7,
            s=55
        )


# 사용자가 입력한 위치 표시
ax.scatter(
    petal_length,
    petal_width,
    color="red",
    marker="*",
    s=300,
    edgecolors="black",
    linewidths=1,
    label="Your Input",
    zorder=5
)

ax.set_xlabel("Petal Length (cm)")
ax.set_ylabel("Petal Width (cm)")

ax.set_title("Iris Petal Length and Width")

ax.legend()

ax.grid(alpha=0.3)

st.pyplot(fig)

plt.close(fig)


# --------------------------------
# 9. 데이터 정보
# --------------------------------

st.divider()

st.subheader("📚 데이터 정보")

col1, col2, col3 = st.columns(3)

col1.metric("전체 데이터", f"{len(df)}개")

col2.metric("붓꽃 품종", f"{df['Species'].nunique()}종")

col3.metric("사용 알고리즘", "KNN")

with st.expander("원본 데이터 확인하기"):

    st.dataframe(
        df,
        use_container_width=True
    )

st.caption(
    "본 프로그램은 Iris 데이터셋을 활용한 "
    "머신러닝 교육용 예측 프로그램입니다."
)
