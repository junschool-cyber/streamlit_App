import re
import streamlit as st
import pandas as pd
import plotly.express as px
from googleapiclient.discovery import build

st.set_page_config(page_title="YouTube 댓글 분석기", layout="wide")

st.title("🎬 YouTube 댓글 분석기")

api_key = st.text_input("YouTube API Key", type="password")
url = st.text_input("YouTube URL")
max_comments = st.slider("댓글 개수", 100, 500, 200, 100)


def get_video_id(url):
    patterns = [
        r"v=([^&]+)",
        r"youtu\.be/([^?]+)"
    ]

    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)

    return None


def get_comments(api_key, video_id, limit):

    youtube = build(
        "youtube",
        "v3",
        developerKey=api_key
    )

    comments = []

    next_page = None

    while len(comments) < limit:

        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            pageToken=next_page,
            textFormat="plainText"
        )

        response = request.execute()

        for item in response["items"]:

            c = item["snippet"]["topLevelComment"]["snippet"]

            comments.append({
                "작성자": c["authorDisplayName"],
                "댓글": c["textDisplay"],
                "좋아요": c["likeCount"],
                "시간": c["publishedAt"]
            })

            if len(comments) >= limit:
                break

        next_page = response.get("nextPageToken")

        if not next_page:
            break

    return pd.DataFrame(comments)


if st.button("댓글 분석"):

    if api_key == "":
        st.error("API Key를 입력하세요.")
        st.stop()

    video_id = get_video_id(url)

    if video_id is None:
        st.error("유튜브 URL이 올바르지 않습니다.")
        st.stop()

    with st.spinner("댓글 가져오는 중..."):

        df = get_comments(
            api_key,
            video_id,
            max_comments
        )

    if len(df) == 0:
        st.warning("댓글이 없습니다.")
        st.stop()

    st.success(f"{len(df)}개의 댓글을 가져왔습니다.")

    df["시간"] = pd.to_datetime(df["시간"])

    df["시간대"] = df["시간"].dt.hour

    chart = (
        df.groupby("시간대")
        .size()
        .reset_index(name="댓글수")
    )

    fig = px.bar(
        chart,
        x="시간대",
        y="댓글수",
        title="시간대별 댓글 작성 수"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.subheader("댓글 목록")

    st.dataframe(df)

    csv = df.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        "CSV 다운로드",
        csv,
        "youtube_comments.csv",
        "text/csv"
    )
