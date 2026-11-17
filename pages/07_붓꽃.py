
import streamlit as st
import pandas as pd
import os
import html

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
    st.write("실제 CSV 열 이름:", df.columns.tolist())
    st.write("CSV 파일 위치:", FILE_PATH)
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

df = df[df["품종"] != ""]

if len(df) < 2:
    st.error("학습할 데이터가 부족합니다.")
    st.stop()

if df["품종"].nunique() < 2:
    st.error("최소 2개 이상의 품종이 필요합니다.")
    st.stop()


# ==========================================
# 6. 데이터 정보
# ==========================================

st.subheader("📊 데이터 정보")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("전체 데이터", f"{len(df)}개")

with col2:
    st.metric("붓꽃 품종", f"{df['품종'].nunique()}종")

with col3:
    st.metric("사용 가능한 속성", "4개")

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
# 8. 예측 함수
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

        model.fit(X, y)

        prediction = model.predict(input_df)[0]

        probabilities = model.predict_proba(input_df)[0]

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
# 9. 검정색 큰 동그라미 그래프 함수
# ==========================================

def show_custom_graph(
    selected_features,
    input_values,
    graph_key
):

    x_col = selected_features[0]
    y_col = selected_features[1]

    x_min = float(df[x_col].min())
    x_max = float(df[x_col].max())

    y_min = float(df[y_col].min())
    y_max = float(df[y_col].max())

    x_range = max(x_max - x_min, 0.1)
    y_range = max(y_max - y_min, 0.1)

    x_padding = x_range * 0.08
    y_padding = y_range * 0.08

    graph_width = 800
    graph_height = 440

    left = 75
    right = 25
    top = 25
    bottom = 65

    inner_width = graph_width - left - right
    inner_height = graph_height - top - bottom

    def get_x(value):
        return (
            left +
            (value - x_min + x_padding) /
            (x_range + 2 * x_padding) *
            inner_width
        )

    def get_y(value):
        return (
            top +
            (y_max + y_padding - value) /
            (y_range + 2 * y_padding) *
            inner_height
        )

    colors = [
        "#3182CE",
        "#E53E3E",
        "#38A169",
        "#805AD5",
        "#D69E2E"
    ]

    svg_parts = []

    svg_parts.append(
        f'<svg viewBox="0 0 {graph_width} {graph_height}" '
        'width="100%" xmlns="http://www.w3.org/2000/svg">'
    )

    # 배경
    svg_parts.append(
        f'<rect width="{graph_width}" height="{graph_height}" '
        'fill="white" rx="8"/>'
    )

    # 가로 격자와 세로 격자
    for i in range(6):

        x = left + inner_width * i / 5
        y = top + inner_height * i / 5

        x_value = x_min - x_padding + (
            (x_max - x_min + 2 * x_padding) * i / 5
        )

        y_value = y_max + y_padding - (
            (y_max - y_min + 2 * y_padding) * i / 5
        )

        svg_parts.append(
            f'<line x1="{x}" y1="{top}" '
            f'x2="{x}" y2="{top + inner_height}" '
            'stroke="#E2E8F0" stroke-width="1"/>'
        )

        svg_parts.append(
            f'<line x1="{left}" y1="{y}" '
            f'x2="{left + inner_width}" y2="{y}" '
            'stroke="#E2E8F0" stroke-width="1"/>'
        )

        svg_parts.append(
            f'<text x="{x}" y="{top + inner_height + 23}" '
            'font-size="12" text-anchor="middle" fill="#333">'
            f'{x_value:.2f}</text>'
        )

        svg_parts.append(
            f'<text x="{left - 12}" y="{y + 4}" '
            'font-size="12" text-anchor="end" fill="#333">'
            f'{y_value:.2f}</text>'
        )

    # 축
    svg_parts.append(
        f'<line x1="{left}" y1="{top}" '
        f'x2="{left}" y2="{top + inner_height}" '
        'stroke="#333" stroke-width="2"/>'
    )

    svg_parts.append(
        f'<line x1="{left}" y1="{top + inner_height}" '
        f'x2="{left + inner_width}" y2="{top + inner_height}" '
        'stroke="#333" stroke-width="2"/>'
    )

    # 기존 데이터 점
    species_list = sorted(df["품종"].unique())

    for index, species in enumerate(species_list):

        color = colors[index % len(colors)]

        species_data = df[df["품종"] == species]

        for _, row in species_data.iterrows():

            cx = get_x(float(row[x_col]))
            cy = get_y(float(row[y_col]))

            svg_parts.append(
                f'<circle cx="{cx:.2f}" cy="{cy:.2f}" '
                f'r="5" fill="{color}" fill-opacity="0.7"/>'
            )

    # 입력한 데이터: 검정색 큰 원
    input_x = get_x(input_values[0])
    input_y = get_y(input_values[1])

    svg_parts.append(
        f'<circle cx="{input_x:.2f}" cy="{input_y:.2f}" '
        'r="11" fill="black" stroke="white" '
        'stroke-width="2"/>'
    )

    # 검정색 원 설명
    svg_parts.append(
        f'<text x="{input_x + 15}" y="{input_y - 14}" '
        'font-size="13" font-weight="bold" fill="black">'
        '입력 데이터</text>'
    )

    # 축 이름
    svg_parts.append(
        f'<text x="{left + inner_width / 2}" '
        f'y="{graph_height - 12}" '
        'font-size="14" text-anchor="middle" fill="#222">'
        f'{html.escape(x_col)} (cm)</text>'
    )

    svg_parts.append(
        f'<text x="18" y="{top + inner_height / 2}" '
        'font-size="14" text-anchor="middle" fill="#222" '
        f'transform="rotate(-90 18 {top + inner_height / 2})">'
        f'{html.escape(y_col)} (cm)</text>'
    )

    svg_parts.append('</svg>')

    # 범례
    legend = '<div style="display:flex; flex-wrap:wrap; gap:15px; margin-top:8px;">'

    for index, species in enumerate(species_list):

        color = colors[index % len(colors)]

        legend += (
            '<span style="display:flex;align-items:center;gap:5px;">'
            f'<span style="width:11px;height:11px;border-radius:50%;'
            f'background:{color};display:inline-block;"></span>'
            f'{html.escape(species)}</span>'
        )

    legend += (
        '<span style="display:flex;align-items:center;gap:5px;">'
        '<span style="width:15px;height:15px;border-radius:50%;'
        'background:black;display:inline-block;"></span>'
        '<b>입력 데이터</b></span>'
    )

    legend += '</div>'

    st.html(
        '<div style="width:100%;overflow:hidden;">'
        + ''.join(svg_parts)
        + legend
        + '</div>'
    )


# ==========================================
# 10. 예측 화면 함수
# ==========================================

def show_prediction_tab(
    tab_title,
    selected_features,
    tab_key
):

    st.subheader(tab_title)

    st.write("선택한 두 가지 속성의 값을 입력해 주세요.")

    input_values = []

    col1, col2 = st.columns(2)

    for i, feature in enumerate(selected_features):

        minimum = float(df[feature].min())
        maximum = float(df[feature].max())

        default_value = float(df[feature].median())

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
        "입력 범위는 실제 CSV 데이터의 최솟값과 최댓값입니다."
    )

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

        st.session_state[f"{tab_key}_features"] = (
            selected_features
        )

    result_key = f"{tab_key}_results"

    if result_key in st.session_state:

        results = st.session_state[result_key]

        probability_results = st.session_state[
            f"{tab_key}_probabilities"
        ]

        saved_values = st.session_state[
            f"{tab_key}_input"
        ]

        saved_features = st.session_state[
            f"{tab_key}_features"
        ]

        st.divider()

        st.subheader("🏆 알고리즘별 예측 결과 비교")

        for result in results:

            with st.container(border=True):

                c1, c2, c3 = st.columns(3)

                with c1:
                    st.write(f"**{result['알고리즘']}**")

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

        st.divider()

        st.subheader("🎯 입력한 꽃의 위치")

        show_custom_graph(
            saved_features,
            saved_values,
            tab_key
        )

    else:

        st.info(
            "속성을 입력한 다음 예측 버튼을 눌러 주세요."
        )

        st.subheader("📊 실제 붓꽃 데이터 분포")

        st.scatter_chart(
            df,
            x=selected_features[0],
            y=selected_features[1],
            color="품종"
        )

    # ======================================
    # 알고리즘 작동 원리
    # ======================================

    st.divider()

    st.subheader("🧠 인공지능 알고리즘 작동 원리")

    with st.expander("1️⃣ KNN - K 최근접 이웃"):

        st.write(
            """
            ① 새로운 붓꽃의 속성값을 입력합니다.

            ② 기존 데이터 중 가장 가까운 데이터 5개를 찾습니다.

            ③ 가장 많이 등장한 품종을 예측합니다.

            **핵심 원리:** 가까운 이웃들의 정보를 이용합니다.
            """
        )

    with st.expander("2️⃣ Decision Tree - 의사결정나무"):

        st.write(
            """
            ① 꽃잎과 꽃받침의 특징을 확인합니다.

            ② 특징에 따라 데이터를 여러 조건으로 나눕니다.

            ③ 조건을 따라가며 최종 품종을 결정합니다.

            **핵심 원리:** 질문과 조건을 단계적으로 거칩니다.
            """
        )

    with st.expander("3️⃣ Random Forest - 랜덤 포레스트"):

        st.write(
            """
            ① 여러 개의 의사결정나무를 학습시킵니다.

            ② 각각의 나무가 품종을 예측합니다.

            ③ 여러 나무의 예측 결과를 종합합니다.

            **핵심 원리:** 여러 의사결정나무의 결과를 종합합니다.
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
# 12. 탭 1
# ==========================================

with tab1:

    st.info(
        "꽃잎 길이와 꽃잎 너비를 이용합니다."
    )

    show_prediction_tab(
        "🌺 꽃잎 길이와 꽃잎 너비",
        ["꽃잎 길이", "꽃잎 너비"],
        "petal"
    )


# ==========================================
# 13. 탭 2
# ==========================================

with tab2:

    st.info(
        "4가지 속성 중 원하는 2개를 선택하세요."
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
