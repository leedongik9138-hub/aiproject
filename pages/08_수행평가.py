
import streamlit as st
import csv
import os
import re
import math
import heapq

# ==========================================
# 1. 페이지 설정
# ==========================================

st.set_page_config(
    page_title="서울 지하철 길찾기",
    page_icon="🚇",
    layout="wide"
)

st.title("🚇 서울 지하철 길찾기")
st.write("출발역과 도착역을 선택하고 지하철 이동 경로를 확인해 보세요!")

# 현재 파일은 pages 폴더 안에 있으므로
# 한 단계 위의 프로젝트 폴더를 기준으로 CSV를 찾음
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

STATION_FILE = os.path.join(
    BASE_DIR,
    "subway_station_coordinates.csv"
)

TRANSFER_FILE = os.path.join(
    BASE_DIR,
    "SeoulMetro_TransferDistance_Time_20250331.csv"
)

DISTANCE_FILE = os.path.join(
    BASE_DIR,
    "subway_transfer_distance.csv"
)


# ==========================================
# 2. CSV 읽기
# ==========================================

def read_csv_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"파일을 찾을 수 없습니다: {os.path.basename(path)}"
        )

    for encoding in ["utf-8-sig", "cp949", "euc-kr", "utf-8"]:
        try:
            with open(
                path,
                "r",
                encoding=encoding,
                newline=""
            ) as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                if not rows:
                    raise ValueError(
                        f"{os.path.basename(path)} 파일에 데이터가 없습니다."
                    )

                return rows, reader.fieldnames or []

        except UnicodeDecodeError:
            continue

    raise ValueError(
        f"{os.path.basename(path)} 파일 인코딩을 읽을 수 없습니다."
    )


# ==========================================
# 3. 열 이름 찾기
# ==========================================

def normalize(value):
    return re.sub(
        r"[\s_\-()（）\[\]]+",
        "",
        str(value)
    ).lower()


def find_column(columns, candidates):
    normalized = {
        normalize(col): col
        for col in columns
    }

    # 이름이 정확히 일치하는 열 먼저 찾기
    for candidate in candidates:
        key = normalize(candidate)

        if key in normalized:
            return normalized[key]

    # 이름이 포함되어 있는 열 찾기
    for candidate in candidates:
        key = normalize(candidate)

        for norm_col, original_col in normalized.items():
            if key and key in norm_col:
                return original_col

    return None


def clean_station_name(value):
    if value is None:
        return ""

    text = str(value).strip()
    text = re.sub(r"\s+", "", text)

    # "서울역"과 "서울"을 같은 역 이름으로 처리
    if text.endswith("역"):
        text = text[:-1]

    return text


def number(value):
    if value is None:
        return None

    text = str(value).strip()
    text = text.replace(",", "")
    text = text.replace("분", "")
    text = text.replace("미터", "")
    text = text.replace("m", "")

    if not text:
        return None

    try:
        result = float(text)

        if math.isfinite(result) and result >= 0:
            return result

    except ValueError:
        pass

    return None


# ==========================================
# 4. 지하철역 좌표 데이터 정리
# ==========================================

def prepare_stations(rows, columns):
    name_col = find_column(columns, [
        "역명",
        "역이름",
        "역명칭",
        "station_name",
        "station",
        "name"
    ])

    lat_col = find_column(columns, [
        "위도",
        "latitude",
        "lat"
    ])

    lon_col = find_column(columns, [
        "경도",
        "longitude",
        "lon",
        "lng"
    ])

    line_col = find_column(columns, [
        "호선",
        "노선명",
        "노선",
        "line_name",
        "line"
    ])

    if not name_col or not lat_col or not lon_col:
        raise ValueError(
            "역 좌표 CSV에서 역명, 위도, 경도 열을 찾지 못했습니다."
        )

    stations = []
    station_lines = {}
    station_coords = {}

    for row in rows:
        name = clean_station_name(row.get(name_col))
        lat = number(row.get(lat_col))
        lon = number(row.get(lon_col))

        line = (
            str(row.get(line_col, "")).strip()
            if line_col else ""
        )

        if not name or lat is None or lon is None:
            continue

        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue

        stations.append({
            "역": name,
            "호선": line,
            "위도": lat,
            "경도": lon
        })

        station_lines.setdefault(name, set())

        if line:
            station_lines[name].add(line)

        # 같은 역의 여러 호선 좌표는 평균으로 저장
        station_coords.setdefault(name, []).append(
            (lat, lon)
        )

    # 역별 대표 좌표 계산
    final_coords = {}

    for name, coord_list in station_coords.items():
        avg_lat = sum(x[0] for x in coord_list) / len(coord_list)
        avg_lon = sum(x[1] for x in coord_list) / len(coord_list)

        final_coords[name] = {
            "위도": avg_lat,
            "경도": avg_lon
        }

    return stations, station_lines, final_coords


# ==========================================
# 5. 역 연결 그래프 만들기
# ==========================================

def prepare_graph(distance_rows, distance_columns,
                  transfer_rows, transfer_columns):

    graph = {}

    # 역 이름 열 후보
    from_candidates = [
        "출발역",
        "출발역명",
        "시작역",
        "역명1",
        "역1",
        "from_station",
        "from"
    ]

    to_candidates = [
        "도착역",
        "도착역명",
        "종착역",
        "역명2",
        "역2",
        "to_station",
        "to"
    ]

    time_candidates = [
        "소요시간",
        "이동시간",
        "소요시간분",
        "시간(분)",
        "분",
        "time",
        "minutes",
        "transfer_time"
    ]

    distance_candidates = [
        "거리",
        "이동거리",
        "환승거리",
        "거리(m)",
        "distance",
        "meters"
    ]

    line_candidates = [
        "호선",
        "노선명",
        "노선",
        "line",
        "line_name"
    ]

    type_candidates = [
        "구분",
        "연결구분",
        "유형",
        "type",
        "kind"
    ]

    total_added = 0

    # 두 파일 모두 역-역 연결 형태라면 읽어서 그래프에 추가
    all_sources = [
        (distance_rows, distance_columns, "역간"),
        (transfer_rows, transfer_columns, "환승")
    ]

    for rows, columns, source_type in all_sources:

        from_col = find_column(columns, from_candidates)
        to_col = find_column(columns, to_candidates)

        time_col = find_column(columns, time_candidates)
        distance_col = find_column(columns, distance_candidates)
        line_col = find_column(columns, line_candidates)
        type_col = find_column(columns, type_candidates)

        # 출발역과 도착역이 없으면 이 파일은
        # 다른 형태일 수 있으므로 연결 데이터로 사용하지 않음
        if not from_col or not to_col:
            continue

        for row in rows:
            start = clean_station_name(row.get(from_col))
            end = clean_station_name(row.get(to_col))

            if not start or not end or start == end:
                continue

            minutes = number(row.get(time_col)) if time_col else None
            distance = number(row.get(distance_col)) if distance_col else None

            line = (
                str(row.get(line_col, "")).strip()
                if line_col else ""
            )

            edge_type = (
                str(row.get(type_col, "")).strip()
                if type_col else source_type
            )

            edge = {
                "역": end,
                "시간": minutes,
                "거리": distance,
                "호선": line,
                "구분": edge_type
            }

            reverse_edge = {
                "역": start,
                "시간": minutes,
                "거리": distance,
                "호선": line,
                "구분": edge_type
            }

            graph.setdefault(start, []).append(edge)
            graph.setdefault(end, []).append(reverse_edge)

            total_added += 1

    return graph, total_added


# ==========================================
# 6. 최단 경로 찾기
# ==========================================

def find_route(graph, start, end):
    if start == end:
        return {
            "역목록": [start],
            "구간목록": [],
            "비용": 0,
            "기준": "시간"
        }

    if start not in graph or end not in graph:
        return None

    # 모든 연결에 시간이 있으면 시간 기준
    all_have_time = all(
        edge["시간"] is not None
        for edges in graph.values()
        for edge in edges
    )

    # 시간이 없으면 거리 기준
    all_have_distance = all(
        edge["거리"] is not None
        for edges in graph.values()
        for edge in edges
    )

    if all_have_time:
        weight_key = "시간"
    elif all_have_distance:
        weight_key = "거리"
    else:
        return None

    queue = [(0, start)]
    costs = {start: 0}
    previous = {}
    previous_edge = {}

    while queue:
        current_cost, current = heapq.heappop(queue)

        if current_cost > costs.get(current, float("inf")):
            continue

        if current == end:
            break

        for edge in graph.get(current, []):
            next_station = edge["역"]
            weight = edge[weight_key]

            if weight is None:
                continue

            new_cost = current_cost + weight

            if new_cost < costs.get(next_station, float("inf")):
                costs[next_station] = new_cost
                previous[next_station] = current
                previous_edge[next_station] = edge

                heapq.heappush(
                    queue,
                    (new_cost, next_station)
                )

    if end not in costs:
        return None

    route = []
    route_edges = []

    current = end

    while current != start:
        route.append(current)

        if current not in previous:
            return None

        route_edges.append(previous_edge[current])
        current = previous[current]

    route.append(start)

    route.reverse()
    route_edges.reverse()

    return {
        "역목록": route,
        "구간목록": route_edges,
        "비용": costs[end],
        "기준": weight_key
    }


# ==========================================
# 7. 데이터 불러오기
# ==========================================

@st.cache_data
def load_data():
    station_rows, station_columns = read_csv_file(STATION_FILE)

    transfer_rows, transfer_columns = read_csv_file(TRANSFER_FILE)

    distance_rows, distance_columns = read_csv_file(DISTANCE_FILE)

    stations, station_lines, station_coords = prepare_stations(
        station_rows,
        station_columns
    )

    graph, edge_count = prepare_graph(
        distance_rows,
        distance_columns,
        transfer_rows,
        transfer_columns
    )

    return (
        stations,
        station_lines,
        station_coords,
        graph,
        edge_count,
        station_columns,
        transfer_columns,
        distance_columns
    )


try:
    (
        stations,
        station_lines,
        station_coords,
        graph,
        edge_count,
        station_columns,
        transfer_columns,
        distance_columns
    ) = load_data()

except Exception as e:
    st.error("CSV 파일을 불러오는 중 오류가 발생했습니다.")
    st.code(str(e))
    st.info(
        "CSV 파일이 프로젝트 최상위 폴더에 있는지, "
        "파일 이름이 정확한지 확인해 주세요."
    )
    st.stop()


# ==========================================
# 8. 데이터 상태
# ==========================================

with st.expander("📂 불러온 데이터 확인"):
    st.write(f"지하철역 좌표 데이터: {len(stations):,}개")
    st.write(f"역 연결 정보: {edge_count:,}개")
    st.write(f"그래프에 등록된 역: {len(graph):,}개")

    st.write("역 좌표 CSV 열 이름")
    st.write(station_columns)

    st.write("환승 CSV 열 이름")
    st.write(transfer_columns)

    st.write("역 간 거리 CSV 열 이름")
    st.write(distance_columns)


# ==========================================
# 9. 출발역 / 도착역 선택
# ==========================================

st.header("🗺️ 출발역과 도착역 선택")

station_names = sorted(
    set(
        station["역"]
        for station in stations
    )
)

col1, col2 = st.columns(2)

with col1:
    start_station = st.selectbox(
        "🚉 출발역",
        station_names,
        index=0
    )

with col2:
    destination_options = [
        name for name in station_names
        if name != start_station
    ]

    end_station = st.selectbox(
        "🏁 도착역",
        destination_options
    )


# ==========================================
# 10. 경로 검색
# ==========================================

if st.button("🔍 경로 검색하기", type="primary", use_container_width=True):

    result = find_route(
        graph,
        start_station,
        end_station
    )

    if result is None:
        st.error(
            "두 역 사이의 경로를 찾지 못했습니다."
        )

        st.warning(
            "CSV의 출발역·도착역 열 이름 또는 연결 데이터 형식을 "
            "확인해야 합니다."
        )

    else:
        route = result["역목록"]
        route_edges = result["구간목록"]

        st.success("경로를 찾았습니다! 🎉")

        # --------------------------------------
        # 경로 요약
        # --------------------------------------

        st.subheader("📍 이동 경로")

        st.write(
            " → ".join(
                f"{station}역"
                for station in route
            )
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "출발역",
                start_station + "역"
            )

        with col2:
            st.metric(
                "도착역",
                end_station + "역"
            )

        with col3:
            st.metric(
                "이동 구간",
                f"{len(route) - 1}개"
            )

        # --------------------------------------
        # 이동 시간 또는 거리
        # --------------------------------------

        st.subheader("⏱️ 예상 이동 정보")

        if result["기준"] == "시간":
            st.metric(
                "CSV 구간 시간 합계",
                f'{result["비용"]:.1f}분'
            )

            st.caption(
                "CSV에 기록된 구간 시간을 합산한 값이며, "
                "열차 대기 시간이나 실제 시간표와 다를 수 있습니다."
            )

        else:
            st.metric(
                "CSV 거리 합계",
                f'{result["비용"]:.1f}'
            )

            st.caption(
                "시간 정보가 충분하지 않아 거리 기준으로 경로를 찾았습니다."
            )

        # --------------------------------------
        # 환승역 추정
        # --------------------------------------

        st.subheader("🔄 환승 정보")

        transfer_stations = []

        for index, edge in enumerate(route_edges):
            edge_type = str(edge.get("구분", "")).lower()

            # 데이터에 환승이라고 표시된 구간
            if "환승" in edge_type or "transfer" in edge_type:
                transfer_stations.append(route[index])

        if transfer_stations:
            st.write(
                "환승 관련 역: "
                + ", ".join(
                    station + "역"
                    for station in transfer_stations
                )
            )
        else:
            st.info(
                "CSV에서 환승 구간을 명확히 구분하지 못했습니다. "
                "환승역을 정확히 표시하려면 호선별 연결 정보가 필요합니다."
            )

        # --------------------------------------
        # 역별 순서
        # --------------------------------------

        st.subheader("🚇 역별 이동 순서")

        for index, station in enumerate(route):
            if index == 0:
                st.write(f"🟢 출발: **{station}역**")

            elif index == len(route) - 1:
                st.write(f"🔴 도착: **{station}역**")

            else:
                st.write(f"⬇️ {station}역")

        # --------------------------------------
        # 지도 표시
        # --------------------------------------

        st.subheader("🗺️ 경로 지도")

        map_data = []

        for station in route:
            if station in station_coords:
                map_data.append({
                    "lat": station_coords[station]["위도"],
                    "lon": station_coords[station]["경도"],
                    "역": station
                })

        if map_data:
            st.map(
                map_data,
                latitude="lat",
                longitude="lon",
                size=15
            )

            st.caption(
                "지도에는 경로에 포함된 역의 위치가 표시됩니다. "
                "역 사이의 실제 선로를 그린 지도는 아닙니다."
            )
        else:
            st.warning(
                "경로에 포함된 역의 좌표를 찾지 못했습니다."
            )


# ==========================================
# 11. 안내
# ==========================================

st.divider()

st.caption(
    "이 앱은 제공된 CSV 자료를 이용해 경로를 계산합니다. "
    "실시간 열차 운행, 현재 열차 위치, 실제 운행 방향, "
    "열차 대기 시간은 별도 데이터가 필요합니다."
)
