
import streamlit as st
import pandas as pd
import re
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR.parent

FILE_PATH = PROJECT_DIR / "Iris.csv"


@st.cache_data
def load_data(file_path):

    if not file_path.exists():
        raise FileNotFoundError(
            f"CSV 파일을 찾을 수 없습니다.\n경로: {file_path}"
        )

    data = None
    errors = []

    # 여러 인코딩을 시도하고 구분 기호 자동 감지
    for encoding in ["utf-8-sig", "utf-8", "cp949"]:

        try:
            data = pd.read_csv(
                file_path,
                encoding=encoding,
                sep=None,
                engine="python",
                skipinitialspace=True
            )
            break

        except Exception as e:
            errors.append(f"{encoding}: {e}")

    if data is None:
        raise ValueError(
            "CSV 파일을 읽지 못했습니다.\n" + "\n".join(errors)
        )

    # 열 이름 정리
    def normalize(name):
        return re.sub(
            r"[^a-z0-9]",
            "",
            str(name).replace("\ufeff", "").strip().lower()
        )

    # 실제 CSV 열 이름을 확인
    column_map = {}

    aliases = {
        "petallengthcm": "PetalLengthCm",
        "petallength": "PetalLengthCm",
        "petalwidthcm": "PetalWidthCm",
        "petalwidth": "PetalWidthCm",
        "species": "Species",
        "class": "Species",
        "variety": "Species"
    }

    for column in data.columns:
        key = normalize(column)

        if key in aliases:
            column_map[column] = aliases[key]

    data = data.rename(columns=column_map)

    required = [
        "PetalLengthCm",
        "PetalWidthCm",
        "Species"
    ]

    missing = [
        column for column in required
        if column not in data.columns
    ]

    if missing:
        raise ValueError(
            f"필요한 열을 찾지 못했습니다: {missing}\n"
            f"실제로 읽은 CSV 열 이름: {list(data.columns)}\n"
            f"읽은 파일 위치: {file_path}"
        )

    return data


try:
    df = load_data(FILE_PATH)

    st.success("CSV 파일을 정상적으로 불러왔습니다.")
    st.caption(f"불러온 파일: {FILE_PATH}")

except Exception as e:
    st.error("CSV 파일을 불러오는 중 오류가 발생했습니다.")
    st.code(str(e))
    st.stop()
