
import streamlit as st
import pandas as pd
import os
import re
import heapq
from collections import defaultdict

# --------------------------------------------------
# 1. 페이지 설정
# --------------------------------------------------
st.set_page_config(
    page_title="서울 지하철 최적 경로 찾기",
    page_icon="🚇",
    layout="wide"
)

st.title("🚇 서울 지하철 최적 경로 찾기")
st.write("출발역과 도착역을 선택하면 가장 빠른 이동 경로를 찾아줍니다.")

# --------------------------------------------------
# 2. 파일 경로 설정
# pages 폴더의 상위 폴더가 프로젝트 최상위 폴더
# --------------------------------------------------
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

COORD_FILE = os.path.join(
    BASE_DIR,
    "지하철역_GEOM (역사마스터) (1).csv"
)

DISTANCE_FILE = os.path.join(
    BASE_DIR,
    "서울교통공사 역간거리 및 소요시간_240810(1).csv"
)

TRANSFER_FILE = os.path.join(
    BASE_DIR,
    "서울교통공사_환승역거리 소요시간 정보_20250331.csv"
)

# --------------------------------------------------
# 3. 공통 함수
# --------------------------------------------------
def normalize_station(name):
    """역 이름의 공백과 괄호 등을 정리한다."""
    name = str(name).strip()
    name = re.sub(r"\([^)]*\)", "", name)
    name = name.replace(" ", "")

    if name.endswith("역"):
        name = name[:-1]

    return name


def time_to_seconds(value):
    """시간을 초 단위로 변환한다."""
    value = str(value).strip()

    if not value or value.lower() == "nan":
        return 0

    try:
        parts = value.split(":")

        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])

        if len(parts) == 3:
            return (
                int(parts[0]) * 3600
                + int(parts[1]) * 60
                + int(parts[2])
            )

        return int(float(value))

    except (ValueError, TypeError):
        return 0


def seconds_to_text(seconds):
    """초를 분과 초로 표시한다."""
    seconds = int(round(seconds))
    minutes = seconds // 60
    remain = seconds % 60

    if remain == 0:
        return f"{minutes}분"

    return f"{minutes}분 {remain}초"


def get_line_number(value):
    """1호선, 2호선 등의 숫자를 가져온다."""
    match = re.search(r"\d+", str(value))

    if match:
        return match.group()

    return None


# --------------------------------------------------
# 4. CSV 인코딩 자동 확인 함수
# --------------------------------------------------
def read_csv_auto(file_path, sep=","):
    """
    CSV 파일의 인코딩을 자동으로 확인한다.
    파일마다 다른 인코딩을 사용해도 읽을 수 있도록 한다.
    """

    encodings = [
        "utf-8-sig",
        "utf-8",
        "cp949",
        "euc-kr"
    ]

    errors = []

    for encoding in encodings:
        try:
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                sep=sep,
                low_memory=False
            )

            # 열 이름 앞뒤 공백 제거
            df.columns = [
                str(col).strip()
                for col in df.columns
            ]

            return df

        except UnicodeDecodeError as e:
            errors.append(
                f"{encoding}: {str(e)}"
            )

        except Exception as e:
            errors.append(
                f"{encoding}: {str(e)}"
            )

    raise ValueError(
        f"CSV 파일을 읽을 수 없습니다: {os.path.basename(file_path)}\n"
        + "\n".join(errors)
    )


# --------------------------------------------------
# 5. CSV 파일 불러오기
# --------------------------------------------------
@st.cache_data
def load_csv_files():

    missing = []

    for file_path in [
        COORD_FILE,
        DISTANCE_FILE,
        TRANSFER_FILE
    ]:
        if not os.path.exists(file_path):
            missing.append(
                os.path.basename(file_path)
            )

    if missing:
        raise FileNotFoundError(
            "다음 파일을 찾을 수 없습니다.\n\n"
            + "\n".join(missing)
            + "\n\nCSV 파일 3개가 GitHub 저장소의 최상위 폴더에 있는지 확인해 주세요."
        )

    # 역 좌표 파일은 탭으로 구분
    coord_df = read_csv_auto(
        COORD_FILE,
        sep="\t"
    )

    # 역간 거리 파일
    distance_df = read_csv_auto(
        DISTANCE_FILE
    )

    # 환승역 거리 파일
    transfer_df = read_csv_auto(
        TRANSFER_FILE
    )

    required_coord = {
        "역한글명칭",
        "호선명칭",
        "환승역X좌표",
        "환승역Y좌표"
    }

    required_distance = {
        "호선",
        "역명",
        "소요시간",
        "역간거리(km)"
    }

    required_transfer = {
        "호선",
        "환승역명",
        "환승노선",
        "환승거리",
        "환승소요시간"
    }

    if not required_coord.issubset(coord_df.columns):
        raise ValueError(
            "역 좌표 CSV의 열 이름이 예상과 다릅니다.\n"
            f"현재 열: {list(coord_df.columns)}"
        )

    if not required_distance.issubset(distance_df.columns):
        raise ValueError(
            "역간 거리 CSV의 열 이름이 예상과 다릅니다.\n"
            f"현재 열: {list(distance_df.columns)}"
        )

    if not required_transfer.issubset(transfer_df.columns):
        raise ValueError(
            "환승역 CSV의 열 이름이 예상과 다릅니다.\n"
            f"현재 열: {list(transfer_df.columns)}"
        )

    return coord_df, distance_df, transfer_df


# --------------------------------------------------
# 6. 지하철 그래프 만들기
# --------------------------------------------------
def build_graph(coord_df, distance_df, transfer_df):

    graph = defaultdict(list)
    station_info = {}
    coordinate_lookup = defaultdict(list)

    # ----------------------------------------------
    # 역 좌표 정리
    # ----------------------------------------------
    for _, row in coord_df.iterrows():

        station_name = str(row["역한글명칭"]).strip()
        line_name = str(row["호선명칭"]).strip()

        try:
            longitude = float(row["환승역X좌표"])
            latitude = float(row["환승역Y좌표"])

        except (ValueError, TypeError):
            continue

        key = normalize_station(station_name)

        coordinate_lookup[key].append({
            "line": line_name,
            "longitude": longitude,
            "latitude": latitude
        })

    # ----------------------------------------------
    # 역간 이동 연결
    # ----------------------------------------------
    for line, group in distance_df.groupby("호선"):

        line = str(line).strip()

        group = group.copy()

        if "연번" in group.columns:
            group = group.sort_values("연번")

        rows = group.to_dict("records")

        previous_node = None

        for row in rows:

            station_name = str(row["역명"]).strip()
            station_key = normalize_station(station_name)

            node = (line, station_key)

            station_info[node] = {
                "name": station_name,
                "line": line
            }

            if previous_node is not None:

                travel_seconds = time_to_seconds(
                    row["소요시간"]
                )

                try:
                    distance_km = float(
                        row["역간거리(km)"]
                    )

                except (ValueError, TypeError):
                    distance_km = 0.0

                if travel_seconds > 0:

                    graph[previous_node].append({
                        "to": node,
                        "time": travel_seconds,
                        "distance": distance_km,
                        "type": "일반 이동"
                    })

                    graph[node].append({
                        "to": previous_node,
                        "time": travel_seconds,
                        "distance": distance_km,
                        "type": "일반 이동"
                    })

            previous_node = node

    # ----------------------------------------------
    # 환승 이동 연결
    # ----------------------------------------------
    for _, row in transfer_df.iterrows():

        source_line = get_line_number(row["호선"])
        target_line = get_line_number(row["환승노선"])

        station_name = str(row["환승역명"]).strip()
        station_key = normalize_station(station_name)

        if source_line is None or target_line is None:
            continue

        source_node = (source_line, station_key)
        target_node = (target_line, station_key)

        if (
            source_node not in station_info
            or target_node not in station_info
        ):
            continue

        transfer_seconds = time_to_seconds(
            row["환승소요시간"]
        )

        try:
            transfer_distance = float(
                row["환승거리"]
            )

        except (ValueError, TypeError):
            transfer_distance = 0.0

        if transfer_seconds <= 0:
            continue

        graph[source_node].append({
            "to": target_node,
            "time": transfer_seconds,
            "distance": transfer_distance / 1000,
            "type": "환승"
        })

        graph[target_node].append({
            "to": source_node,
            "time": transfer_seconds,
            "distance": transfer_distance / 1000,
            "type": "환승"
        })

    return graph, station_info, coordinate_lookup


# --------------------------------------------------
# 7. 다익스트라 최단 경로 알고리즘
# --------------------------------------------------
def dijkstra(graph, start, end):

    distances = {start: 0}
    previous = {}

    queue = [(0, start)]

    while queue:

        current_time, current_node = heapq.heappop(queue)

        if current_time > distances.get(
            current_node,
            float("inf")
        ):
            continue

        if current_node == end:
            break

        for edge in graph.get(current_node, []):

            next_node = edge["to"]
            new_time = current_time + edge["time"]

            if new_time < distances.get(
                next_node,
                float("inf")
            ):

                distances[next_node] = new_time

                previous[next_node] = (
                    current_node,
                    edge
                )

                heapq.heappush(
                    queue,
                    (new_time, next_node)
                )

    if end not in distances:
        return None, None

    path = []
    edges = []

    current = end

    while current != start:

        path.append(current)

        previous_node, edge = previous[current]

        edges.append(edge)

        current = previous_node

    path.append(start)

    path.reverse()
    edges.reverse()

    return path, edges


# --------------------------------------------------
# 8. 좌표 찾기
# --------------------------------------------------
def find_coordinate(
    node,
    station_info,
    coordinate_lookup
):

    station_name = station_info[node]["name"]
    station_key = normalize_station(station_name)
    line = node[0]

    candidates = coordinate_lookup.get(
        station_key,
        []
    )

    if not candidates:
        return None

    for item in candidates:

        if get_line_number(item["line"]) == line:
            return item

    return candidates[0]


# --------------------------------------------------
# 9. 데이터 로딩 및 그래프 생성
# --------------------------------------------------
try:

    coord_df, distance_df, transfer_df = load_csv_files()

    graph, station_info, coordinate_lookup = build_graph(
        coord_df,
        distance_df,
        transfer_df
    )

    if not station_info:
        st.error("지하철 역 정보를 불러오지 못했습니다.")
        st.stop()

except Exception as e:

    st.error("데이터를 불러오는 중 오류가 발생했습니다.")
    st.exception(e)
    st.stop()


# --------------------------------------------------
# 10. 출발역과 도착역 선택
# --------------------------------------------------
st.subheader("📍 출발역과 도착역 선택")

station_options = sorted(
    station_info.keys(),
    key=lambda x: (
        station_info[x]["name"],
        int(x[0])
    )
)

display_names = {}

for node in station_options:

    info = station_info[node]

    display_names[node] = (
        f"{info['name']} ({info['line']}호선)"
    )

col1, col2 = st.columns(2)

with col1:

    start = st.selectbox(
        "🚉 출발역",
        station_options,
        format_func=lambda x: display_names[x],
        key="start_station"
    )

with col2:

    end = st.selectbox(
        "🏁 도착역",
        station_options,
        format_func=lambda x: display_names[x],
        index=min(1, len(station_options) - 1),
        key="end_station"
    )


# --------------------------------------------------
# 11. 경로 검색
# --------------------------------------------------
if st.button(
    "🚇 최적 경로 검색",
    type="primary"
):

    if start == end:

        st.warning("출발역과 도착역이 같습니다.")

    else:

        path, edges = dijkstra(
            graph,
            start,
            end
        )

        if path is None:

            st.error(
                "선택한 두 역 사이의 경로를 찾을 수 없습니다. "
                "현재 데이터에 연결 정보가 없는 노선일 수 있습니다."
            )

        else:

            total_seconds = sum(
                edge["time"] for edge in edges
            )

            total_distance = sum(
                edge["distance"] for edge in edges
            )

            transfer_count = sum(
                1 for edge in edges
                if edge["type"] == "환승"
            )

            # --------------------------------------
            # 결과 요약
            # --------------------------------------
            st.divider()
            st.subheader("🎯 최적 경로 결과")

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "예상 소요 시간",
                seconds_to_text(total_seconds)
            )

            c2.metric(
                "환승 횟수",
                f"{transfer_count}회"
            )

            c3.metric(
                "총 이동 거리",
                f"{total_distance:.1f} km"
            )

            # --------------------------------------
            # 이동 경로 표시
            # --------------------------------------
            st.subheader("🚉 이동 경로")

            for i, node in enumerate(path):

                info = station_info[node]

                if i == 0:

                    st.markdown(
                        f"🟢 **출발: {info['name']} ({info['line']}호선)**"
                    )

                elif i == len(path) - 1:

                    st.markdown(
                        f"🏁 **도착: {info['name']} ({info['line']}호선)**"
                    )

                else:

                    previous_edge = edges[i - 1]

                    if previous_edge["type"] == "환승":

                        st.markdown(
                            f"🔄 **{info['name']}역에서 "
                            f"{info['line']}호선으로 환승**"
                        )

                    else:

                        st.markdown(
                            f"⬇️ {info['name']} ({info['line']}호선)"
                        )

            # --------------------------------------
            # 환승역 목록
            # --------------------------------------
            st.subheader("🔄 환승역")

            transfer_stations = []

            for i, edge in enumerate(edges):

                if edge["type"] == "환승":

                    transfer_node = path[i]

                    transfer_name = station_info[
                        transfer_node
                    ]["name"]

                    from_line = station_info[
                        path[i]
                    ]["line"]

                    to_line = station_info[
                        path[i + 1]
                    ]["line"]

                    transfer_stations.append(
                        f"{transfer_name}역: "
                        f"{from_line}호선 → {to_line}호선"
                    )

            if transfer_stations:

                for item in transfer_stations:
                    st.write("•", item)

            else:

                st.info("환승 없이 이동하는 경로입니다.")

            # --------------------------------------
            # 상세 이동 정보
            # --------------------------------------
            st.subheader("📋 구간별 이동 정보")

            detail_rows = []

            for i, edge in enumerate(edges):

                from_name = station_info[
                    path[i]
                ]["name"]

                to_name = station_info[
                    path[i + 1]
                ]["name"]

                from_line = station_info[
                    path[i]
                ]["line"]

                to_line = station_info[
                    path[i + 1]
                ]["line"]

                detail_rows.append({

                    "출발역": from_name,

                    "도착역": to_name,

                    "이동 구분": edge["type"],

                    "노선": (
                        f"{from_line}호선 → {to_line}호선"
                        if edge["type"] == "환승"
                        else f"{from_line}호선"
                    ),

                    "소요 시간": seconds_to_text(
                        edge["time"]
                    ),

                    "거리(km)": round(
                        edge["distance"],
                        2
                    )

                })

            detail_df = pd.DataFrame(detail_rows)

            st.dataframe(
                detail_df,
                use_container_width=True,
                hide_index=True
            )

            # --------------------------------------
            # 지도 표시
            # --------------------------------------
            st.subheader("🗺️ 경로 지도")

            map_rows = []

            for node in path:

                coordinate = find_coordinate(
                    node,
                    station_info,
                    coordinate_lookup
                )

                if coordinate is None:
                    continue

                map_rows.append({

                    "latitude": coordinate["latitude"],

                    "longitude": coordinate["longitude"]

                })

            if map_rows:

                map_df = pd.DataFrame(map_rows)

                map_df = map_df.drop_duplicates()

                st.map(
                    map_df,
                    latitude="latitude",
                    longitude="longitude",
                    zoom=10
                )

                st.caption(
                    "지도에는 좌표 파일에서 찾을 수 있는 역만 표시됩니다."
                )

            else:

                st.warning(
                    "선택한 경로의 역 좌표를 찾지 못했습니다."
                )

            # --------------------------------------
            # 데이터 안내
            # --------------------------------------
            st.divider()

            st.caption(
                "※ 소요 시간은 제공된 역간 소요시간과 환승 소요시간의 합계입니다. "
                "실제 열차 운행 상황, 대기 시간, 혼잡도는 반영하지 않습니다."
            )

            st.caption(
                "※ 역간 이동 자료는 1~8호선이며, "
                "해당 자료에서 이동 시간이 0으로 기록된 역간 연결은 "
                "제외했습니다."
            )

else:

    st.info(
        "출발역과 도착역을 선택한 뒤 "
        "'최적 경로 검색' 버튼을 눌러 주세요."
    )
