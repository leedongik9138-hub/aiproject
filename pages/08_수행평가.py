
import streamlit as st
import csv
import os
import math
import heapq
import re
from difflib import get_close_matches

# ==========================================
# 1. 기본 설정
# ==========================================

st.set_page_config(
    page_title="서울 지하철 길찾기",
    page_icon="🚇",
    layout="wide"
)

st.title("🚇 서울 지하철 길찾기")
st.write("우리 동네에서 가까운 지하철역을 찾고, 목적지까지 가는 경로를 확인해 보세요!")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FILES = {
    "station": os.path.join(BASE_DIR, "subway_station_coordinates.csv"),
    "transfer": os.path.join(BASE_DIR, "SeoulMetro_TransferDistance_Time_20250331.csv"),
    "distance": os.path.join(BASE_DIR, "subway_transfer_distance.csv"),
    "dong": os.path.join(BASE_DIR, "dong_coordinates.csv")
}


# ==========================================
# 2. CSV 파일 읽기
# ==========================================

def read_csv_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"파일을 찾을 수 없습니다: {os.path.basename(file_path)}"
        )

    encodings = ["utf-8-sig", "cp949", "euc-kr", "utf-8"]

    for encoding in encodings:
        try:
            with open(
                file_path,
                "r",
                encoding=encoding,
                newline=""
            ) as file:
                reader = csv.DictReader(file)
                data = list(reader)

                if not data:
                    raise ValueError(
                        f"{os.path.basename(file_path)} 파일에 데이터가 없습니다."
                    )

                return data

        except UnicodeDecodeError:
            continue

    raise ValueError(
        f"{os.path.basename(file_path)} 파일의 인코딩을 확인해 주세요."
    )


# ==========================================
# 3. 열 이름 자동 찾기
# ==========================================

def normalize(text):
    return re.sub(r"[\s_\-()（）]+", "", str(text)).lower()


def find_column(data, candidates):
    if not data:
        return None

    columns = list(data[0].keys())

    normalized_columns = {
        normalize(column): column
        for column in columns
    }

    # 정확하게 일치하는 열 찾기
    for candidate in candidates:
        key = normalize(candidate)

        if key in normalized_columns:
            return normalized_columns[key]

    # 일부 이름이 포함된 열 찾기
    for candidate in candidates:
        key = normalize(candidate)

        for normalized, original in normalized_columns.items():
            if key and key in normalized:
                return original

    return None


def get_value(row, column):
    if column is None:
        return ""

    return str(row.get(column, "")).strip()


def to_number(value):
    if value is None:
        return None

    text = str(value).strip()
    text = text.replace(",", "")
    text = text.replace("분", "")
    text = text.replace("m", "")
    text = text.replace("km", "")

    if not text:
        return None

    try:
        return float(text)
    except ValueError:
        return None


# ==========================================
# 4. 행정동 데이터 정리
# ==========================================

def prepare_dong_data(data):
    gu_col = find_column(data, [
        "구", "구명", "시군구명", "자치구명",
        "시군구", "자치구"
    ])

    dong_col = find_column(data, [
        "행정동명", "동명", "동", "행정동",
        "읍면동명", "읍면동"
    ])

    lat_col = find_column(data, [
        "위도", "latitude", "lat"
    ])

    lon_col = find_column(data, [
        "경도", "longitude", "lon", "lng"
    ])

    if not gu_col or not dong_col or not lat_col or not lon_col:
        raise ValueError(
            "행정동 CSV에서 구 이름, 동 이름, 위도, 경도 열을 찾지 못했습니다."
        )

    result = []

    for row in data:
        gu = get_value(row, gu_col)
        dong = get_value(row, dong_col)

        lat = to_number(get_value(row, lat_col))
        lon = to_number(get_value(row, lon_col))

        if not gu or not dong or lat is None or lon is None:
            continue

        # 위도와 경도 범위 확인
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue

        result.append({
            "구": gu,
            "동": dong,
            "위도": lat,
            "경도": lon
        })

    if not result:
        raise ValueError("사용할 수 있는 행정동 좌표 데이터가 없습니다.")

    return result


# ==========================================
# 5. 지하철역 데이터 정리
# ==========================================

def prepare_station_data(data):
    name_col = find_column(data, [
        "역명", "역이름", "역명칭", "station_name",
        "station", "역"
    ])

    lat_col = find_column(data, [
        "위도", "latitude", "lat"
    ])

    lon_col = find_column(data, [
        "경도", "longitude", "lon", "lng"
    ])

    line_col = find_column(data, [
        "호선", "노선명", "노선", "line", "line_name"
    ])

    if not name_col or not lat_col or not lon_col:
        raise ValueError(
            "지하철역 CSV에서 역명, 위도, 경도 열을 찾지 못했습니다."
        )

    result = []

    for row in data:
        name = get_value(row, name_col)
        lat = to_number(get_value(row, lat_col))
        lon = to_number(get_value(row, lon_col))
        line = get_value(row, line_col) if line_col else ""

        if not name or lat is None or lon is None:
            continue

        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue

        result.append({
            "역": name,
            "호선": line,
            "위도": lat,
            "경도": lon
        })

    if not result:
        raise ValueError("사용할 수 있는 지하철역 좌표가 없습니다.")

    return result


# ==========================================
# 6. 두 지점 사이 거리 계산
# ==========================================

def calculate_distance(lat1, lon1, lat2, lon2):
    earth_radius = 6371

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius * c


# ==========================================
# 7. 가까운 지하철역 찾기
# ==========================================

def find_nearest_stations(dong, stations, count=5):
    distances = []

    for station in stations:
        distance = calculate_distance(
            dong["위도"],
            dong["경도"],
            station["위도"],
            station["경도"]
        )

        distances.append({
            "역": station["역"],
            "호선": station["호선"],
            "거리": distance,
            "위도": station["위도"],
            "경도": station["경도"]
        })

    distances.sort(key=lambda x: x["거리"])

    # 같은 역이 여러 호선으로 중복된 경우에도
    # 역 이름이 같은 결과는 하나만 표시
    unique = []
    seen = set()

    for item in distances:
        key = item["역"]

        if key not in seen:
            seen.add(key)
            unique.append(item)

        if len(unique) >= count:
            break

    return unique


# ==========================================
# 8. 역 이름 정리
# ==========================================

def clean_station_name(name):
    name = str(name).strip()

    name = re.sub(r"\s+", "", name)

    name = name.replace("역", "")

    return name


def find_station_name(user_input, stations):
    target = clean_station_name(user_input)

    station_names = list(set(
        clean_station_name(s["역"])
        for s in stations
    ))

    if target in station_names:
        return target

    matches = get_close_matches(
        target,
        station_names,
        n=1,
        cutoff=0.65
    )

    if matches:
        return matches[0]

    return None


# ==========================================
# 9. 역 간 이동 그래프 만들기
# ==========================================

def add_edges_from_csv(graph, data):
    from_col = find_column(data, [
        "출발역", "출발역명", "시작역", "역명1",
        "역명A", "역1", "from_station", "from"
    ])

    to_col = find_column(data, [
        "도착역", "도착역명", "종착역", "역명2",
        "역명B", "역2", "to_station", "to"
    ])

    time_col = find_column(data, [
        "소요시간", "이동시간", "소요시간분",
        "시간(분)", "분", "time", "minutes",
        "transfer_time"
    ])

    distance_col = find_column(data, [
        "거리", "이동거리", "환승거리",
        "거리(m)", "distance", "meters"
    ])

    if not from_col or not to_col:
        return 0

    added = 0

    for row in data:
        start = clean_station_name(get_value(row, from_col))
        end = clean_station_name(get_value(row, to_col))

        if not start or not end or start == end:
            continue

        minutes = to_number(get_value(row, time_col))
        distance = to_number(get_value(row, distance_col))

        # 소요 시간이 없는 경우 시간은 알 수 없는 것으로 처리
        edge = {
            "역": end,
            "시간": minutes,
            "거리": distance
        }

        reverse_edge = {
            "역": start,
            "시간": minutes,
            "거리": distance
        }

        graph.setdefault(start, []).append(edge)
        graph.setdefault(end, []).append(reverse_edge)

        added += 1

    return added


def build_graph(transfer_data, distance_data):
    graph = {}

    count1 = add_edges_from_csv(graph, transfer_data)
    count2 = add_edges_from_csv(graph, distance_data)

    return graph, count1 + count2


# ==========================================
# 10. 최단 경로 계산
# ==========================================

def dijkstra(graph, start, end):
    if start not in graph or end not in graph:
        return None

    # 모든 연결 구간에 시간이 있어야 시간 기준 계산 가능
    all_edges_have_time = True

    for edges in graph.values():
        for edge in edges:
            if edge["시간"] is None:
                all_edges_have_time = False
                break

    if all_edges_have_time:
        weight_key = "시간"
    else:
        # 시간이 없으면 거리 기준 경로만 계산
        all_edges_have_distance = True

        for edges in graph.values():
            for edge in edges:
                if edge["거리"] is None:
                    all_edges_have_distance = False
                    break

        if not all_edges_have_distance:
            return None

        weight_key = "거리"

    queue = [(0, start)]
    costs = {start: 0}
    previous = {}

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

                heapq.heappush(
                    queue,
                    (new_cost, next_station)
                )

    if end not in costs:
        return None

    path = []
    current = end

    while current != start:
        path.append(current)

        if current not in previous:
            return None

        current = previous[current]

    path.append(start)
    path.reverse()

    return {
        "경로": path,
        "비용": costs[end],
        "기준": weight_key
    }


# ==========================================
# 11. 데이터 불러오기
# ==========================================

@st.cache_data
def load_all_data():
    dong_raw = read_csv_file(FILES["dong"])
    station_raw = read_csv_file(FILES["station"])
    transfer_raw = read_csv_file(FILES["transfer"])
    distance_raw = read_csv_file(FILES["distance"])

    dong_data = prepare_dong_data(dong_raw)
    station_data = prepare_station_data(station_raw)

    graph, edge_count = build_graph(
        transfer_raw,
        distance_raw
    )

    return dong_data, station_data, graph, edge_count


try:
    dong_data, station_data, graph, edge_count = load_all_data()

except Exception as error:
    st.error("CSV 파일을 불러오는 중 문제가 발생했습니다.")
    st.write(error)

    st.info(
        "파일 이름과 CSV의 열 이름을 확인해 주세요. "
        "행정동 좌표 파일에는 구, 동, 위도, 경도 정보가 필요합니다."
    )

    st.stop()


# ==========================================
# 12. 사이드바
# ==========================================

st.sidebar.header("📂 데이터 확인")

st.sidebar.write(
    f"행정동 데이터: {len(dong_data):,}개"
)

st.sidebar.write(
    f"지하철역 데이터: {len(station_data):,}개"
)

st.sidebar.write(
    f"역 연결 정보: {edge_count:,}개"
)


# ==========================================
# 13. 출발 지역 선택
# ==========================================

st.header("📍 1. 현재 사는 지역 선택")

gu_list = sorted(set(
    item["구"] for item in dong_data
))

selected_gu = st.selectbox(
    "서울시 어느 구에 살고 있나요?",
    gu_list
)

dong_list = sorted(set(
    item["동"]
    for item in dong_data
    if item["구"] == selected_gu
))

selected_dong = st.selectbox(
    "어느 동에 살고 있나요?",
    dong_list
)

selected_location = next(
    (
        item for item in dong_data
        if item["구"] == selected_gu
        and item["동"] == selected_dong
    ),
    None
)

if selected_location:
    st.success(
        f"선택한 지역: 서울특별시 {selected_gu} {selected_dong}"
    )

    st.caption(
        "행정동 중심 좌표를 이용해 가까운 역을 계산합니다."
    )


# ==========================================
# 14. 가까운 역 검색
# ==========================================

st.divider()

st.header("🚉 2. 가까운 지하철역 찾기")

nearest = find_nearest_stations(
    selected_location,
    station_data,
    count=5
)

if nearest:
    first_station = nearest[0]

    st.subheader("가장 가까운 지하철역")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "가까운 역",
            first_station["역"]
        )

    with col2:
        st.metric(
            "호선",
            first_station["호선"] or "정보 없음"
        )

    with col3:
        st.metric(
            "직선거리",
            f'{first_station["거리"]:.2f} km'
        )

    st.subheader("주변 지하철역 TOP 5")

    for index, station in enumerate(nearest):
        st.write(
            f'{index + 1}위. 🚇 {station["역"]} '
            f'({station["호선"] or "호선 정보 없음"})'
            f' - 약 {station["거리"]:.2f}km'
        )

else:
    st.warning("주변 지하철역을 찾지 못했습니다.")


# ==========================================
# 15. 도착역 입력
# ==========================================

st.divider()

st.header("🧭 3. 목적지 입력")

st.write(
    "이동하고 싶은 지하철역 이름을 입력해 주세요."
)

destination_input = st.text_input(
    "도착역",
    placeholder="예: 강남역, 서울역, 잠실역"
)

if st.button("🔍 지하철 경로 검색", type="primary"):

    if not destination_input.strip():
        st.warning("도착역을 입력해 주세요.")

    elif not nearest:
        st.warning("출발역을 찾을 수 없습니다.")

    else:
        start_station = clean_station_name(
            nearest[0]["역"]
        )

        end_station = find_station_name(
            destination_input,
            station_data
        )

        if end_station is None:
            st.error(
                "입력한 역을 찾을 수 없습니다. "
                "역 이름을 다시 확인해 주세요."
            )

        elif start_station == end_station:
            st.success("현재 선택한 지역에서 가장 가까운 역이 목적지입니다.")

        else:
            result = dijkstra(
                graph,
                start_station,
                end_station
            )

            if result is None:
                st.error(
                    "두 역을 연결하는 경로를 계산하지 못했습니다."
                )

                st.warning(
                    "역 연결 CSV에 출발역과 도착역 정보가 있는지, "
                    "두 역이 같은 연결 그래프에 포함되어 있는지 확인해 주세요."
                )

            else:
                route = result["경로"]

                st.success("경로를 찾았습니다! 🎉")

                st.subheader("🚇 이동 경로")

                st.write(
                    f"출발역: **{start_station}역**"
                )

                st.write(
                    f"도착역: **{end_station}역**"
                )

                st.markdown("### 이동 순서")

                for index, station in enumerate(route):
                    if index == 0:
                        st.write(f"🟢 **출발** → {station}역")

                    elif index == len(route) - 1:
                        st.write(f"🔴 **도착** → {station}역")

                    else:
                        st.write(f"⬇️ {station}역")

                st.divider()

                st.subheader("📊 경로 분석")

                if result["기준"] == "시간":
                    st.metric(
                        "CSV 연결 정보 기준 이동 시간",
                        f'{result["비용"]:.1f}분'
                    )

                else:
                    st.metric(
                        "CSV 연결 정보 기준 총 거리",
                        f'{result["비용"]:.1f}'
                    )

                    st.info(
                        "시간 정보가 충분하지 않아 거리 기준으로 경로를 계산했습니다."
                    )

                st.metric(
                    "이동 구간 수",
                    f"{len(route) - 1}개"
                )

                st.metric(
                    "경유하는 중간 역 수",
                    f"{max(0, len(route) - 2)}개"
                )

                st.subheader("🔄 환승 정보")

                st.info(
                    "현재 코드는 역 사이의 연결 경로를 계산합니다. "
                    "호선별 운행 방향과 환승 통로를 구분하려면 "
                    "호선별 구간 및 환승 연결 정보가 추가로 필요합니다."
                )

                st.write(
                    "계산된 역 순서: "
                    + " → ".join(route)
                )


# ==========================================
# 16. 데이터 안내
# ==========================================

st.divider()

with st.expander("📌 데이터와 계산 방식 안내"):
    st.write("""
    **가까운 역 계산**

    - 선택한 행정동의 위도와 경도를 사용합니다.
    - 각 지하철역의 좌표와 직선거리를 비교합니다.
    - 가장 가까운 역부터 표시합니다.
    - 실제 도보 거리나 도보 시간과는 다를 수 있습니다.

    **지하철 경로 계산**

    - 두 역을 연결하는 CSV 데이터를 이용합니다.
    - 연결 정보에 시간이 있으면 시간 기준으로 계산합니다.
    - 시간이 없고 거리가 있으면 거리 기준으로 계산합니다.
    - CSV에 없는 역 연결이나 운행 정보는 만들어 내지 않습니다.

    **주의**

    - 실제 열차 운행 방향과 시간표는 별도 정보가 필요합니다.
    - 실제 환승역과 환승 통로를 정확하게 구분하려면
      호선별 역 연결 및 환승 데이터가 필요합니다.
    - 실제 집 주소에서 역까지의 도보 경로를 제공하려면
      별도의 도보 길찾기 서비스가 필요합니다.
    """)

