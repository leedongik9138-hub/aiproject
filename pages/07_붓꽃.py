
import streamlit as st
import pandas as pd
import os

from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


# ==========================================
# 1. 페이지 설정
# ==========================================

st.set_page_config(
    page_title="붓꽃 품종 AI 분석",
    page_icon="🌸",
    layout="wide"
)

st.title("🌸 붓꽃(Iris) 품종 AI 분석")
st.write(
    "3가지 인공지능 알고리즘으로 붓꽃의 품종을 예측하고 "
    "결과를 비교해 보세요!"
)


# ==========================================
# 2. CSV 파일 경로
# ==========================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

FILE_PATH = os.path.join(
    BASE_DIR,
    "Iris.csv"
)


# ==========================================
# 3. CSV 파일 불러오기
# ==========================================

if not os.path.exists(FILE_PATH):
    st.error("Iris.csv 파일을 찾을 수 없습니다.")
    st.write("파일 위치:", FILE_PATH)
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


# ==========================================
# 4. 열 이름 확인
# ==========================================

df.columns = (
    df.columns.astype(str)
    .str.replace("\ufeff", "", regex=False)
    .str.strip()
)

FEATURES = [
    "꽃받침 길이",
    "꽃받침 너비",
    "꽃잎 길이",
    "꽃잎 너비"
]

REQUIRED_COLUMNS = FEATURES + ["품종"]

missing_columns = [
    col for col in REQUIRED_COLUMNS
    if col not in df.columns
]

if missing_columns:

    st.error(
        f"필요한 열을 찾지 못했습니다: {missing_columns}"
    )

    st.write(
        "실제 CSV 열 이름:",
        df.columns.tolist()
    )

    st.write(
        "CSV 파일 위치:",
        FILE_PATH
    )

    st.stop()


# ==========================================
# 5. 데이터 전처리
# ==========================================

for col in FEATURES:

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

df = df[
    df["품종"] != ""
]

if len(df) < 2:
    st.error("학습할 데이터가 부족합니다.")
    st.stop()

if df["품종"].nunique() < 2:
    st.error("예측하려면 최소 2개 이상의 품종이 필요합니다.")
    st.stop()


# ==========================================
# 6. 데이터 정보
# ==========================================

st.subheader("📊 데이터 정보")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "전체 데이터",
        f"{len(df)}개"
    )

with col2:
    st.metric(
        "붓꽃 품종",
        f"{df['품종'].nunique()}종"
    )

with col3:
    st.metric(
        "사용 가능한 속성",
        "4개"
    )

with st.expander("📁 CSV 데이터 확인"):

    st.dataframe(
        df,
        use_container_width=True
    )


# ==========================================
# 7. 알고리즘 생성 함수
# ==========================================

def create_models(number_of_rows):

    neighbors = min(5, number_of_rows)

    models = {

        "KNN": Pipeline([
            ("scaler", StandardScaler()),
            ("model", KNeighborsClassifier(
                n_neighbors=neighbors
            ))
        ]),

        "Decision Tree": DecisionTreeClassifier(
            random_state=42
        ),

        "Random Forest": RandomForestClassifier(
            n_estimators=200,
            random_state=42
        )

    }

    return models


# ==========================================
# 8. 예측 및 비교 함수
# ==========================================

def predict_and_compare(selected_features, input_values):

    X = df[selected_features]
    y = df["품종"]

    models = create_models(len(df))

    input_df = pd.DataFrame(
        [input_values],
        columns=selected_features
    )

    results = []
    probability_results = []

    for model_name, model in models.items():

        # 인공지능 학습
        model.fit(X, y)

        # 품종 예측
        prediction = model.predict(input_df)[0]

        # 예측 확률 계산
        probabilities = model.predict_proba(input_df)[0]

        # 예측 결과 저장
        results.append({
            "알고리즘": model_name,
            "예측 품종": prediction,
            "예측 확률": round(
                max(probabilities) * 100, 2
            )
        })

        for species, probability in zip(
            model.classes_,
            probabilities
        ):

            probability_results.append({
                "알고리즘": model_name,
                "품종": species,
                "예측 확률 (%)": round(
                    probability * 100, 2
                )
            })

    return results, probability_results


# ==========================================
# 9. 예측 화면 함수
# ==========================================

def show_prediction_tab(tab_title, selected_features, tab_key):

    st.subheader(tab_title)

    st.write(
        "선택한 두 가지 속성의 값을 입력해 주세요."
    )

    input_values = []

    col1, col2 = st.columns(2)

    for i, feature in enumerate(selected_features):

        minimum = float(df[feature].min())
        maximum = float(df[feature].max())

        default_value = float(
            df[feature].median()
        )

        with [col1, col2][i]:

            value = st.number_input(
                f"🌱 {feature} (cm)",
                min_value=minimum,
                max_value=maximum,
                value=default_value,
                step=0.1,
                key=f"{tab_key}_{feature}"
            )

            input_values.append(value)

    st.caption(
        "입력 범위는 실제 CSV 데이터의 최솟값과 최댓값을 기준으로 합니다."
    )

    # --------------------------------------
    # 예측 버튼
    # --------------------------------------

    if st.button(
        "🔍 3가지 알고리즘으로 예측하기",
        key=f"{tab_key}_predict",
        use_container_width=True
    ):

        results, probability_results = predict_and_compare(
            selected_features,
            input_values
        )

        st.session_state[f"{tab_key}_results"] = results

        st.session_state[f"{tab_key}_probabilities"] = (
            probability_results
        )

        st.session_state[f"{tab_key}_input"] = input_values

    # --------------------------------------
    # 예측 결과 비교
    # --------------------------------------

    result_key = f"{tab_key}_results"

    if result_key in st.session_state:

        results = st.session_state[result_key]

        probability_results = st.session_state[
            f"{tab_key}_probabilities"
        ]

        saved_values = st.session_state[
            f"{tab_key}_input"
        ]

        st.divider()

        st.subheader("🏆 알고리즘별 예측 결과 비교")

        for result in results:

            with st.container(border=True):

                c1, c2, c3 = st.columns(3)

                with c1:
                    st.write(
                        f"**{result['알고리즘']}**"
                    )

                with c2:
                    st.success(
                        f"🌸 {result['예측 품종']}"
                    )

                with c3:
                    st.metric(
                        "예측 확률",
                        f"{result['예측 확률']}%"
                    )

        result_df = pd.DataFrame(results)

        st.subheader("📋 예측 결과 비교표")

        st.dataframe(
            result_df,
            hide_index=True,
            use_container_width=True
        )

        # ----------------------------------
        # 품종별 예측 확률 비교
        # ----------------------------------

        st.subheader("📈 품종별 예측 확률 비교")

        probability_df = pd.DataFrame(
            probability_results
        )

        probability_pivot = probability_df.pivot(
            index="품종",
            columns="알고리즘",
            values="예측 확률 (%)"
        )

        st.bar_chart(
            probability_pivot,
            y_label="예측 확률 (%)"
        )

        with st.expander("품종별 상세 예측 확률"):

            st.dataframe(
                probability_df,
                hide_index=True,
                use_container_width=True
            )

        # ----------------------------------
        # 예측 위치 그래프
        # ----------------------------------

        st.divider()

        st.subheader("🎯 입력한 데이터의 위치")

        plot_df = df[
            selected_features + ["품종"]
        ].copy()

        input_point = pd.DataFrame({
            selected_features[0]: [saved_values[0]],
            selected_features[1]: [saved_values[1]],
            "품종": ["입력 데이터"]
        })

        plot_df = pd.concat(
            [plot_df, input_point],
            ignore_index=True
        )

        st.scatter_chart(
            plot_df,
            x=selected_features[0],
            y=selected_features[1],
            color="품종"
        )

        st.caption(
            f"가로축: {selected_features[0]} / "
            f"세로축: {selected_features[1]}"
        )

    else:

        st.info(
            "속성을 입력한 다음 예측 버튼을 눌러 주세요."
        )

        # 예측 전에도 실제 데이터 분포 표시

        st.subheader("📊 실제 붓꽃 데이터 분포")

        st.scatter_chart(
            df,
            x=selected_features[0],
            y=selected_features[1],
            color="품종"
        )

    # ======================================
    # 10. 알고리즘 작동 원리
    # 그래프 아래에 설명
    # ======================================

    st.divider()

    st.subheader("🧠 인공지능 알고리즘 작동 원리")

    with st.expander("1️⃣ KNN - K 최근접 이웃"):

        st.write(
            """
            KNN은 새로운 데이터와 기존 데이터 사이의
            거리를 비교하는 알고리즘입니다.

            ① 새로운 붓꽃의 꽃잎 또는 꽃받침 정보를 입력합니다.

            ② 기존 데이터 중 가장 가까운 데이터 5개를 찾습니다.

            ③ 가장 많이 등장한 품종을 새로운 붓꽃의 품종으로 예측합니다.

            **핵심 원리:** 가까운 이웃들의 정보를 이용하여
            새로운 데이터의 종류를 판단합니다.
            """
        )

    with st.expander("2️⃣ Decision Tree - 의사결정나무"):

        st.write(
            """
            의사결정나무는 여러 가지 질문을 통해
            데이터를 분류하는 알고리즘입니다.

            ① 꽃잎 길이와 꽃잎 너비 등의 특징을 확인합니다.

            ② 데이터의 특징에 따라 여러 가지 조건으로 나눕니다.

            ③ 조건을 따라가면서 최종 품종을 결정합니다.

            **핵심 원리:** 질문과 조건을 단계적으로 거쳐
            최종적인 품종을 판단합니다.
            """
        )

    with st.expander("3️⃣ Random Forest - 랜덤 포레스트"):

        st.write(
            """
            랜덤 포레스트는 여러 개의 의사결정나무를
            만들어 결과를 종합하는 알고리즘입니다.

            ① 여러 개의 의사결정나무를 학습시킵니다.

            ② 각각의 나무가 붓꽃의 품종을 예측합니다.

            ③ 여러 나무의 예측 결과를 종합하여
            최종 품종을 결정합니다.

            **핵심 원리:** 여러 의사결정나무의 결과를
            종합하여 예측합니다.
            """
        )


# ==========================================
# 11. 탭 만들기
# ==========================================

st.divider()

st.header("🌸 붓꽃 품종 예측하기")

tab1, tab2 = st.tabs([
    "🌺 꽃잎 속성으로 예측",
    "🌿 원하는 속성 2개 선택"
])


# ==========================================
# 12. 탭 1 - 기존 꽃잎 속성
# ==========================================

with tab1:

    st.info(
        "기존과 동일하게 꽃잎 길이와 꽃잎 너비를 이용합니다."
    )

    show_prediction_tab(
        "🌺 꽃잎 길이와 꽃잎 너비",
        ["꽃잎 길이", "꽃잎 너비"],
        "petal"
    )


# ==========================================
# 13. 탭 2 - 원하는 속성 선택
# ==========================================

with tab2:

    st.info(
        "꽃받침과 꽃잎을 포함한 4가지 속성 중 "
        "원하는 2개를 선택할 수 있습니다."
    )

    col1, col2 = st.columns(2)

    with col1:

        feature1 = st.selectbox(
            "첫 번째 속성 선택",
            FEATURES,
            index=0,
            key="custom_feature1"
        )

    second_options = [
        feature for feature in FEATURES
        if feature != feature1
    ]

    with col2:

        feature2 = st.selectbox(
            "두 번째 속성 선택",
            second_options,
            index=0,
            key="custom_feature2"
        )

    st.write(
        f"선택한 속성: **{feature1} + {feature2}**"
    )

    show_prediction_tab(
        "🌿 선택한 속성으로 품종 예측",
        [feature1, feature2],
        "custom"
    )


# ==========================================
# 14. 마무리
# ==========================================

st.divider()

st.caption(
    "🌸 Iris AI Analysis | "
    "KNN · Decision Tree · Random Forest"
)
