import os
import re
from collections import Counter

import pandas as pd
import plotly.express as px
import streamlit as st
from googleapiclient.discovery import build

# matplotlib / wordcloud
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from wordcloud import WordCloud
    WC_AVAILABLE = True
except Exception:
    WC_AVAILABLE = False


# --------------------------------------------------
# 페이지 설정
# --------------------------------------------------
st.set_page_config(
    page_title="YouTube 댓글 분석기",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 YouTube 댓글 분석기")
st.write("YouTube API Key와 영상 링크를 입력하면 댓글을 분석합니다.")


# --------------------------------------------------
# 입력 UI
# --------------------------------------------------
api_key = st.text_input("YouTube API Key", type="password")

url = st.text_input("YouTube 영상 URL")

max_comments = st.slider(
    "가져올 댓글 수",
    min_value=100,
    max_value=1000,
    value=300,
    step=100
)


# --------------------------------------------------
# 영상 ID 추출
# --------------------------------------------------
def extract_video_id(url):
    patterns = [
        r"v=([^&]+)",
        r"youtu\\.be/([^?]+)"
    ]

    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)

    return None


# --------------------------------------------------
# 영상 정보 가져오기
# --------------------------------------------------
def get_video_info(api_key, video_id):
    youtube = build("youtube", "v3", developerKey=api_key)

    req = youtube.videos().list(
        part="snippet,statistics",
        id=video_id
    )

    res = req.execute()

    if not res["items"]:
        return None

    item = res["items"][0]

    return {
        "title": item["snippet"]["title"],
        "channel": item["snippet"]["channelTitle"],
        "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
        "views": int(item["statistics"].get("viewCount", 0)),
        "likes": int(item["statistics"].get("likeCount", 0)),
        "comments": int(item["statistics"].get("commentCount", 0)),
    }


# --------------------------------------------------
# 댓글 수집
# --------------------------------------------------
def get_comments(api_key, video_id, max_comments):
    youtube = build("youtube", "v3", developerKey=api_key)

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


# --------------------------------------------------
# 단어 추출
# --------------------------------------------------
def make_word_counter(texts):
    text = " ".join(texts.astype(str))

    text = re.sub(r"[^가-힣A-Za-z ]", " ", text)

    stopwords = {
        "그리고", "정말", "너무", "진짜",
        "영상", "이번", "그냥", "있는",
        "합니다", "입니다", "같아요", "좋아요"
    }

    words = [
        w for w in text.split()
        if len(w) >= 2 and w not in stopwords
    ]

    return Counter(words)


# --------------------------------------------------
# 워드클라우드 생성
# --------------------------------------------------
def show_wordcloud(counter):
    if not WC_AVAILABLE:
        st.warning("wordcloud 또는 matplotlib를 사용할 수 없습니다.")
        return

    font_path = None

    if os.path.exists("NanumGothic.ttf"):
        font_path = "NanumGothic.ttf"
    elif os.path.exists("fonts/NanumGothic.ttf"):
        font_path = "fonts/NanumGothic.ttf"

    if font_path is None:
        st.warning("NanumGothic.ttf 파일이 없어 워드클라우드를 표시하지 않습니다.")
        return

    wc = WordCloud(
        width=1000,
        height=500,
        background_color="white",
        font_path=font_path
    ).generate_from_frequencies(counter)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.imshow(wc)
    ax.axis("off")
    st.pyplot(fig)


# --------------------------------------------------
# 메인 실행
# --------------------------------------------------
if st.button("댓글 분석 시작"):

    if api_key.strip() == "":
        st.error("API Key를 입력하세요.")
        st.stop()

    video_id = extract_video_id(url)

    if video_id is None:
        st.error("유튜브 URL이 올바르지 않습니다.")
        st.stop()

    # 영상 정보
    try:
        info = get_video_info(api_key, video_id)
    except Exception as e:
        st.error(f"영상 정보를 가져오지 못했습니다: {e}")
        st.stop()

    if info:
        col1, col2 = st.columns([1, 3])

        with col1:
            st.image(info["thumbnail"], use_container_width=True)

        with col2:
            st.subheader(info["title"])
            st.write(f"📺 채널: {info['channel']}")

            c1, c2, c3 = st.columns(3)
            c1.metric("조회수", f"{info['views']:,}")
            c2.metric("좋아요", f"{info['likes']:,}")
            c3.metric("댓글수", f"{info['comments']:,}")

    st.divider()

    # 댓글 수집
    with st.spinner("댓글 수집 중..."):
        try:
            df = get_comments(api_key, video_id, max_comments)
        except Exception as e:
            st.error(f"댓글을 가져오는 중 오류 발생: {e}")
            st.stop()

    st.success(f"총 {len(df)}개의 댓글을 가져왔습니다.")

    # 시간 변환
    df["시간"] = pd.to_datetime(df["시간"])
    df["Hour"] = df["시간"].dt.hour

    # --------------------------------------------------
    # 시간대별 댓글 추이
    # --------------------------------------------------
    st.subheader("⏰ 시간대별 댓글 작성 추이")

    hour_df = (
        df.groupby("Hour")
        .size()
        .reset_index(name="댓글수")
    )

    fig_hour = px.bar(
        hour_df,
        x="Hour",
        y="댓글수",
        text="댓글수",
        title="시간대별 댓글 수"
    )

    fig_hour.update_traces(textposition="outside")

    st.plotly_chart(fig_hour, use_container_width=True)

    st.divider()

    # --------------------------------------------------
    # 워드클라우드
    # --------------------------------------------------
    st.subheader("☁️ 워드클라우드")

    counter = make_word_counter(df["댓글"])

    if len(counter) > 0:
        show_wordcloud(counter)
    else:
        st.info("워드클라우드를 생성할 단어가 없습니다.")

    st.divider()

    # --------------------------------------------------
    # TOP 20 단어
    # --------------------------------------------------
    st.subheader("🔥 자주 등장한 단어 TOP 20")

    top_df = pd.DataFrame(
        counter.most_common(20),
        columns=["단어", "빈도"]
    )

    if not top_df.empty:
        fig_top = px.bar(
            top_df,
            x="단어",
            y="빈도",
            text="빈도",
            title="TOP 20 단어"
        )

        fig_top.update_traces(textposition="outside")

        st.plotly_chart(fig_top, use_container_width=True)

    st.divider()

    # --------------------------------------------------
    # 댓글 데이터
    # --------------------------------------------------
    st.subheader("📝 댓글 데이터")

    st.dataframe(df, use_container_width=True)

    # CSV 다운로드
    csv = df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="📥 댓글 CSV 다운로드",
        data=csv,
        file_name="youtube_comments.csv",
        mime="text/csv"
    )
    )
