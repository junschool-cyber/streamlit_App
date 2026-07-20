import random
import requests
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="AI 여행 룰렛", page_icon="🎲")

st.title("🎲 AI 국내여행 룰렛")
st.write("버튼을 눌러 오늘의 여행지를 추천받아보세요!")

tour_key = st.secrets["TOUR_API_KEY"]
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

styles = ["힐링", "데이트", "가족", "먹방", "자연", "랜덤"]
style = st.selectbox("여행 스타일", styles)

areas = {
    "전국": 0,
    "서울": 1,
    "인천": 2,
    "대전": 3,
    "대구": 4,
    "광주": 5,
    "부산": 6,
    "울산": 7,
    "세종": 8,
    "경기": 31,
    "강원": 32,
    "충북": 33,
    "충남": 34,
    "경북": 35,
    "경남": 36,
    "전북": 37,
    "전남": 38,
    "제주": 39
}

area = st.selectbox("지역", list(areas.keys()))


def get_places(area_code):
    url = "https://apis.data.go.kr/B551011/KorService1/areaBasedList1"

    params = {
        "serviceKey": tour_key,
        "MobileOS": "ETC",
        "MobileApp": "Trip",
        "_type": "json",
        "numOfRows": 50,
        "pageNo": 1,
        "contentTypeId": 12
    }

    if area_code != 0:
        params["areaCode"] = area_code

    r = requests.get(url, params=params, timeout=10)
    data = r.json()

    return data["response"]["body"]["items"]["item"]


def ai_comment(name, style):
    try:
        res = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "user",
                    "content": f"{style} 여행으로 {name}을 추천하는 한 문장만 작성해줘."
                }
            ]
        )
        return res.choices[0].message.content
    except:
        return "오늘 꼭 한 번 떠나보세요! 😊"


if st.button("🎲 룰렛 돌리기"):

    try:
        places = get_places(areas[area])

        if not places:
            st.warning("관광지가 없습니다.")
            st.stop()

        place = random.choice(places)

        st.success("오늘의 여행지")

        st.header(place.get("title", "-"))

        if place.get("firstimage"):
            st.image(place["firstimage"], use_container_width=True)

        st.write("📍", place.get("addr1", "주소 없음"))

        overview = place.get("overview")
        if overview:
            st.write(overview)

        st.info(ai_comment(place.get("title", ""), style))

        map_url = (
            "https://www.google.com/maps/search/?api=1&query="
            + str(place.get("mapy", ""))
            + ","
            + str(place.get("mapx", ""))
        )

        st.markdown(f"[📍 Google 지도에서 보기]({map_url})")

    except Exception as e:
        st.error("관광정보를 불러오지 못했습니다.")
        st.code(str(e))
