import streamlit as st
import pandas as pd
import re
from collections import Counter
from io import BytesIO

from googleapiclient.discovery import build

import plotly.express as px

import matplotlib.pyplot as plt
from wordcloud import WordCloud

# -----------------------------
# 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="YouTube 댓글 분석기",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 YouTube 댓글 분석기")
st.write("API Key와 유튜브 링크를 입력하면 댓글을 분석합니다.")

# -----------------------------
# 입력
# -----------------------------
api_key = st.text_input("YouTube API Key", type="password")

url = st.text_input("YouTube URL")

max_comments = st.slider(
    "가져올 댓글 수",
    100,
    1000,
    300,
    step=100
)

# -----------------------------
# 영상 ID 추출
# -----------------------------
def extract_video_id(url):

    patterns = [
        r"v=([^&]+)",
        r"youtu\.be/([^?]+)"
    ]

    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)

    return None


# -----------------------------
# 댓글 가져오기
# -----------------------------
def get_comments(api_key, video_id, max_comments):

    youtube = build(
        "youtube",
        "v3",
        developerKey=api_key
    )

    comments = []

    next_page = None

    while len(comments) < max_comments:

        req = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            pageToken=next_page,
            textFormat="plainText"
        )

        res = req.execute()

        for item in res["items"]:

            c = item["snippet"]["topLevelComment"]["snippet"]

            comments.append({

                "작성자": c["authorDisplayName"],
                "댓글": c["textDisplay"],
                "좋아요": c["likeCount"],
                "시간": c["publishedAt"]

            })

            if len(comments) >= max_comments:
                break

        next_page = res.get("nextPageToken")

        if not next_page:
            break

    return pd.DataFrame(comments)


# -----------------------------
# 워드 추출
# -----------------------------
def make_words(texts):

    text = " ".join(texts)

    text = re.sub("[^가-힣a-zA-Z ]", " ", text)

    words = text.split()

    stop = {

        "그리고",
        "입니다",
        "정말",
        "너무",
        "진짜",
        "영상",
        "이번",
        "그냥",
        "있는",
        "합니다"

    }

    words = [

        w

        for w in words

        if len(w) >= 2 and w not in stop

    ]

    return Counter(words)


# -----------------------------
# 메인
# -----------------------------
if st.button("댓글 분석 시작"):

    if api_key == "":
        st.error("API Key를 입력하세요.")
        st.stop()

    video_id = extract_video_id(url)

    if video_id is None:
        st.error("유튜브 URL이 올바르지 않습니다.")
        st.stop()

    with st.spinner("댓글 가져오는 중..."):

        df = get_comments(
            api_key,
            video_id,
            max_comments
        )

    st.success(f"{len(df)}개의 댓글을 가져왔습니다.")

    st.dataframe(df)

    # -------------------------
    # 시간 변환
    # -------------------------

    df["시간"] = pd.to_datetime(df["시간"])

    df["Hour"] = df["시간"].dt.hour

    hour = (
        df.groupby("Hour")
        .size()
        .reset_index(name="댓글수")
    )

    fig = px.bar(

        hour,

        x="Hour",

        y="댓글수",

        title="시간대별 댓글 작성"

    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # -------------------------
    # 워드클라우드
    # -------------------------

    st.subheader("워드클라우드")

    counter = make_words(df["댓글"])

    if len(counter) > 0:

        wc = WordCloud(

            width=1000,
            height=500,

            background_color="white",

            font_path="NanumGothic.ttf"

        ).generate_from_frequencies(counter)

        fig2, ax = plt.subplots(figsize=(12,6))

        ax.imshow(wc)

        ax.axis("off")

        st.pyplot(fig2)

    # -------------------------
    # TOP20
    # -------------------------

    st.subheader("TOP20 단어")

    top = pd.DataFrame(

        counter.most_common(20),

        columns=["단어","빈도"]

    )

    fig3 = px.bar(

        top,

        x="단어",

        y="빈도",

        text="빈도"

    )

    st.plotly_chart(

        fig3,

        use_container_width=True

    )

    # -------------------------
    # 다운로드
    # -------------------------

    csv = df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(

        "CSV 다운로드",

        csv,

        file_name="youtube_comments.csv",

        mime="text/csv"

    )
