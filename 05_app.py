import random
import requests
import streamlit as st

st.set_page_config(page_title="🎲 여행 룰렛", page_icon="🎲")

st.title("🎲 국내 여행 룰렛")
st.write("버튼을 눌러 랜덤 여행지를 추천받아 보세요!")

API_KEY = st.secrets["2de74b9ba4e5495f2e373ebf99ca0f8732e82a4998a091f1c7120a2c620e035f"]

@st.cache_data
def get_places():
    url = "https://apis.data.go.kr/B551011/KorService1/areaBasedList1"

    params = {
        "serviceKey": API_KEY,
        "MobileOS": "ETC",
        "MobileApp": "TripRoulette",
        "_type": "json",
        "numOfRows": 100,
        "pageNo": 1,
        "contentTypeId": 12
    }

    r = requests.get(url, params=params, timeout=10)
    data = r.json()

    return data["response"]["body"]["items"]["item"]

comments = [
    "🌿 오늘은 새로운 풍경을 만나러 떠나보세요!",
    "📸 인생 사진을 남기기 좋은 여행지입니다.",
    "☕ 여유롭게 힐링하기 좋은 곳입니다.",
    "🚗 가볍게 드라이브 다녀오기 좋습니다.",
    "🎒 지금 떠나면 좋은 하루 여행지입니다."
]

if st.button("🎲 여행지 추천"):

    try:
        places = get_places()
        place = random.choice(places)

        st.subheader(place.get("title", "이름 없음"))

        if place.get("firstimage"):
            st.image(place["firstimage"], use_container_width=True)

        st.write("📍", place.get("addr1", "주소 정보 없음"))
        st.success(random.choice(comments))

        if place.get("mapx") and place.get("mapy"):
            url = (
                f"https://www.google.com/maps/search/?api=1&query="
                f"{place['mapy']},{place['mapx']}"
            )
            st.markdown(f"[📍 Google 지도 보기]({url})")

    except Exception:
        st.error("관광 정보를 불러오지 못했습니다.")
