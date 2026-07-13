import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px

st.set_page_config(
    page_title="서울시 공영주차장 대시보드",
    page_icon="🅿️",
    layout="wide"
)

st.title("🅿️ 서울시 공영주차장 대시보드")

uploaded = st.file_uploader(
    "서울시 공영주차장 CSV 또는 Excel 업로드",
    type=["csv", "xlsx"]
)

if uploaded is None:
    st.info("파일을 업로드해주세요.")
    st.stop()

# ------------------------
# 파일 읽기
# ------------------------

if uploaded.name.endswith(".csv"):

    df = None

    for enc in ["utf-8", "utf-8-sig", "cp949", "euc-kr"]:
        try:
            uploaded.seek(0)
            df = pd.read_csv(uploaded, encoding=enc)
            break
        except:
            continue

    if df is None:
        st.error("CSV 파일을 읽을 수 없습니다.")
        st.stop()

else:
    df = pd.read_excel(uploaded)

# ------------------------
# 컬럼 설정
# ------------------------

NAME = "주차장명"
ADDR = "주소"
LAT = "위도"
LON = "경도"

# 숫자형 변환
for col in [
    "총 주차면",
    "기본 주차 요금",
    "월 정기권 금액"
]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# ------------------------
# 자치구 추출
# ------------------------

df["자치구"] = df[ADDR].astype(str).str.extract(
    r"(강남구|강동구|강북구|강서구|관악구|광진구|구로구|금천구|노원구|도봉구|동대문구|동작구|마포구|서대문구|서초구|성동구|성북구|송파구|양천구|영등포구|용산구|은평구|종로구|중구|중랑구)"
)

# ------------------------
# 사이드바
# ------------------------

st.sidebar.header("검색 조건")

selected_gu = st.sidebar.selectbox(
    "자치구",
    ["전체"] + sorted(df["자치구"].dropna().unique().tolist())
)

keyword = st.sidebar.text_input(
    "주차장명 검색"
)

fee_type = st.sidebar.multiselect(
    "유무료",
    df["유무료구분명"].dropna().unique(),
    default=df["유무료구분명"].dropna().unique()
)

night_open = st.sidebar.multiselect(
    "야간개방",
    df["야간무료개방여부명"].dropna().unique(),
    default=df["야간무료개방여부명"].dropna().unique()
)

# ------------------------
# 필터
# ------------------------

filtered = df.copy()

if selected_gu != "전체":
    filtered = filtered[
        filtered["자치구"] == selected_gu
    ]

if keyword:
    filtered = filtered[
        filtered[NAME].astype(str).str.contains(
            keyword,
            case=False,
            na=False
        )
    ]

filtered = filtered[
    filtered["유무료구분명"].isin(fee_type)
]

filtered = filtered[
    filtered["야간무료개방여부명"].isin(night_open)
]

# ------------------------
# KPI
# ------------------------

st.subheader("📊 주요 현황")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "주차장 수",
    f"{len(filtered):,}"
)

c2.metric(
    "총 주차면",
    f"{filtered['총 주차면'].fillna(0).sum():,.0f}"
)

c3.metric(
    "평균 기본요금",
    f"{filtered['기본 주차 요금'].fillna(0).mean():.0f}원"
)

c4.metric(
    "야간 개방",
    f"{(filtered['야간무료개방여부명']=='야간 개방').sum():,}"
)

# ------------------------
# 지도
# ------------------------

st.subheader("🗺️ 주차장 위치")

map_df = filtered.dropna(
    subset=[LAT, LON]
)

if not map_df.empty:

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position="[경도, 위도]",
        get_fill_color="[255,0,0,180]",
        get_radius=40,
        pickable=True
    )

    view_state = pdk.ViewState(
        latitude=map_df[LAT].mean(),
        longitude=map_df[LON].mean(),
        zoom=11
    )

    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={
                "html": """
                <b>{주차장명}</b><br/>
                주소 : {주소}<br/>
                총 주차면 : {총 주차면}<br/>
                기본요금 : {기본 주차 요금}
                """
            }
        )
    )

else:
    st.warning("위도/경도 데이터가 없습니다.")

# ------------------------
# 차트
# ------------------------

st.subheader("📈 분석")

left, right = st.columns(2)

with left:

    gu_count = (
        filtered.groupby("자치구")
        .size()
        .reset_index(name="개수")
        .sort_values("개수", ascending=False)
    )

    fig1 = px.bar(
        gu_count,
        x="자치구",
        y="개수",
        title="자치구별 주차장 수"
    )

    st.plotly_chart(
        fig1,
        use_container_width=True
    )

with right:

    fig2 = px.histogram(
        filtered,
        x="기본 주차 요금",
        nbins=30,
        title="기본 주차요금 분포"
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

avg_fee = (
    filtered.groupby("자치구")["기본 주차 요금"]
    .mean()
    .reset_index()
    .sort_values("기본 주차 요금", ascending=False)
)

fig3 = px.bar(
    avg_fee,
    x="자치구",
    y="기본 주차 요금",
    title="자치구별 평균 기본요금"
)

st.plotly_chart(
    fig3,
    use_container_width=True
)

# ------------------------
# 데이터 테이블
# ------------------------

st.subheader("📋 데이터")

st.dataframe(
    filtered,
    use_container_width=True
)

# ------------------------
# 다운로드
# ------------------------

csv = filtered.to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    label="📥 CSV 다운로드",
    data=csv,
    file_name="seoul_parking_filtered.csv",
    mime="text/csv"
)
