
import streamlit as st
import pandas as pd

# --------------------------------
# 페이지 설정
# --------------------------------
st.set_page_config(
    page_title="서울 관광지 TOP 10",
    page_icon="🗺️",
    layout="wide"
)

# --------------------------------
# 서울 주요 관광지 데이터
# --------------------------------
places = [
    {
        "rank": 1,
        "name": "명동",
        "english": "Myeong-dong",
        "lat": 37.5636,
        "lon": 126.9869,
        "area": "중구",
        "description": "화장품 매장과 패션 상점, 길거리 음식이 모여 있는 쇼핑 명소예요.",
        "tip": "다양한 한국 간식과 화장품을 구경하기 좋아요."
    },
    {
        "rank": 2,
        "name": "N서울타워",
        "english": "N Seoul Tower",
        "lat": 37.5512,
        "lon": 126.9882,
        "area": "용산구 남산",
        "description": "서울의 아름다운 풍경을 한눈에 볼 수 있는 대표 전망대예요.",
        "tip": "해 질 무렵 방문하면 멋진 야경을 볼 수 있어요."
    },
    {
        "rank": 3,
        "name": "코엑스·별마당도서관",
        "english": "COEX & Starfield Library",
        "lat": 37.5129,
        "lon": 127.0591,
        "area": "강남구",
        "description": "대형 쇼핑 공간과 높은 책장이 인상적인 도서관이 있는 곳이에요.",
        "tip": "쇼핑과 문화 공간을 함께 즐겨 보세요."
    },
    {
        "rank": 4,
        "name": "강남역 일대",
        "english": "Gangnam Station",
        "lat": 37.4979,
        "lon": 127.0276,
        "area": "강남구",
        "description": "패션 매장과 맛집, 카페가 밀집한 서울의 번화가예요.",
        "tip": "한국의 도시적인 거리 분위기를 경험해 보세요."
    },
    {
        "rank": 5,
        "name": "홍대 거리",
        "english": "Hongdae",
        "lat": 37.5563,
        "lon": 126.9236,
        "area": "마포구",
        "description": "공연과 카페, 예술 문화로 유명한 젊음의 거리예요.",
        "tip": "거리 공연과 개성 있는 상점을 구경해 보세요."
    },
    {
        "rank": 6,
        "name": "동대문디자인플라자",
        "english": "Dongdaemun Design Plaza",
        "lat": 37.5671,
        "lon": 127.0095,
        "area": "중구",
        "description": "독특한 곡선형 건축 디자인이 돋보이는 복합 문화 공간이에요.",
        "tip": "건물 외관과 주변 야경을 감상해 보세요."
    },
    {
        "rank": 7,
        "name": "광장시장",
        "english": "Gwangjang Market",
        "lat": 37.5700,
        "lon": 126.9997,
        "area": "종로구",
        "description": "빈대떡과 김밥 등 다양한 한국 음식을 맛볼 수 있는 전통시장이에요.",
        "tip": "시장 먹거리 골목을 둘러보세요."
    },
    {
        "rank": 8,
        "name": "경복궁",
        "english": "Gyeongbokgung Palace",
        "lat": 37.5796,
        "lon": 126.9770,
        "area": "종로구",
        "description": "조선 왕조의 대표 궁궐로 한국의 역사와 전통 건축을 만날 수 있어요.",
        "tip": "한복을 입고 전통 궁궐을 구경해 보세요."
    },
    {
        "rank": 9,
        "name": "북촌한옥마을",
        "english": "Bukchon Hanok Village",
        "lat": 37.5826,
        "lon": 126.9830,
        "area": "종로구",
        "description": "전통 한옥이 모여 있어 옛 서울의 분위기를 느낄 수 있는 곳이에요.",
        "tip": "주민들을 배려하여 조용히 관람해 주세요."
    },
    {
        "rank": 10,
        "name": "낙산공원",
        "english": "Naksan Park",
        "lat": 37.5803,
        "lon": 127.0074,
        "area": "종로구",
        "description": "서울 성곽길과 아름다운 도심 전망을 즐길 수 있는 공원이에요.",
        "tip": "성곽길을 걸으며 서울 풍경을 감상해 보세요."
    }
]

# --------------------------------
# 앱 제목
# --------------------------------
st.title("🗺️ 서울 외국인 인기 관광지 TOP 10")

st.write(
    "서울을 처음 방문하는 외국인 관광객을 위한 "
    "대표 관광 명소 10곳을 소개합니다! 🇰🇷"
)

st.caption(
    "서울의 대표 관광 명소를 바탕으로 구성한 추천 목록입니다. "
    "공식적인 통합 방문 순위는 아닙니다."
)

st.divider()

# --------------------------------
# 서울 지도
# --------------------------------
st.subheader("📍 서울 관광지 지도")

st.info(
    "지도 위의 점을 통해 관광지의 위치를 확인해 보세요!"
)

# 지도에 표시할 데이터 생성
map_data = pd.DataFrame([
    {
        "관광지": f'{p["rank"]}. {p["name"]}',
        "lat": p["lat"],
        "lon": p["lon"]
    }
    for p in places
])

# Streamlit 내장 지도 사용
st.map(
    map_data,
    latitude="lat",
    longitude="lon",
    color="#E64B35",
    size=180,
    zoom=10,
    use_container_width=True
)

st.caption(
    "📌 지도에 표시된 점은 각 관광지의 대표 위치입니다."
)

st.divider()

# --------------------------------
# 관광지 소개
# --------------------------------
st.subheader("⭐ 서울 관광지 TOP 10 소개")

for p in places:

    with st.container(border=True):

        col1, col2 = st.columns([1, 5])

        with col1:
            st.markdown(f"## {p['rank']:02d}")
            st.caption(p["area"])

        with col2:
            st.markdown(
                f"### {p['name']} "
                f"({p['english']})"
            )

            st.write(p["description"])

            st.caption(
                f"💡 여행 팁: {p['tip']}"
            )

            st.caption(
                f"📍 위도: {p['lat']} / 경도: {p['lon']}"
            )

st.divider()

# --------------------------------
# 마무리
# --------------------------------
st.success(
    "서울의 다양한 관광지를 즐겁게 여행해 보세요! ✈️"
)

st.markdown(
    """
    **📚 참고 자료**

    - [서울시 공식 관광 정보](https://english.visitseoul.net/)
    - [서울시 외국인 관광객 관련 자료](https://english.seoul.go.kr/)

    ※ 관광지 운영 시간과 휴무일은 방문 전에 확인해 주세요.
    """
)
