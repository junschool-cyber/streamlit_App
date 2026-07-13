import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px

st.set_page_config(
    page_title="서울시 공영주차장",
    page_icon="🅿️",
    layout="wide"
)

st.title("🅿️ 서울시 공영주차장 정보")

uploaded = st.file_uploader(
    "CSV 또는 Excel 파일 업로드",
    type=["csv", "xlsx"]
)

if uploaded is None:
    st.info("공영주차장 데이터를 업로드하세요.")
    st.stop()

# -----------------------
# 데이터 읽기 (인코딩 자동 처리)
# -----------------------

if uploaded.name.endswith(".csv"):

    df = None

    encodings = [
        "utf-8",
        "utf-8-sig",
        "cp949",
        "euc-kr"
    ]

    separators = [
        ",",
        ";",
        "\t"
    ]

    for enc in encodings:
        for sep in separators:
            try:
                uploaded.seek(0)
                df = pd.read_csv(
                    uploaded,
                    encoding=enc,
                    sep=sep
                )
                break
            except:
                continue

        if df is not None:
            break

    if df is None:
        st.error("CSV 파일을 읽을 수 없습니다.")
        st.stop()

else:
    df = pd.read_excel(uploaded)

st.success(f"{len(df):,}개의 데이터를 불러왔습니다.")

# -----------------------
# 컬럼명
# -----------------------

NAME = "주차장명"
ADDR = "주소"
GU = "자치구"
LAT = "위도"
LON = "경도"
SPACE = "주차면수"
FEE = "기본요금"

# -----------------------
# 사이드바
# -----------------------

st.sidebar.header("검색")

gu = st.sidebar.selectbox(
    "자치구",
    ["전체"] + sorted(df[GU].dropna().unique().tolist())
)

keyword = st.sidebar.text_input(
    "주차장 검색"
)

# -----------------------
# 필터
# -----------------------

filtered = df.copy()

if gu != "전체":
    filtered = filtered[
        filtered[GU] == gu
    ]

if keyword:
    filtered = filtered[
        filtered[NAME].str.contains(
            keyword,
            case=False,
            na=False
        )
    ]

# -----------------------
# KPI
# -----------------------

c1, c2, c3 = st.columns(3)

c1.metric(
    "주차장 수",
    len(filtered)
)

if SPACE in filtered.columns:
    c2.metric(
        "총 주차면",
        int(filtered[SPACE].fillna(0).sum())
    )

if FEE in filtered.columns:
    c3.metric(
        "평균 기본요금",
        f"{filtered[FEE].fillna(0).mean():.0f}원"
    )

# -----------------------
# 지도
# -----------------------

st.subheader("🗺️ 지도")

map_df = filtered.dropna(
    subset=[LAT, LON]
)

layer = pdk.Layer(
    "ScatterplotLayer",
    data=map_df,
    get_position="[경도, 위도]",
    get_radius=50,
    get_fill_color=[255, 0, 0, 160],
    pickable=True,
)

view = pdk.ViewState(
    latitude=map_df[LAT].mean(),
    longitude=map_df[LON].mean(),
    zoom=11
)

tooltip = {
    "html":
    "<b>{주차장명}</b><br/>"
    "{주소}<br/>"
    "주차면수 : {주차면수}",
    "style": {
        "backgroundColor": "steelblue"
    }
}

st.pydeck_chart(
    pdk.Deck(
        layers=[layer],
        initial_view_state=view,
        tooltip=tooltip
    )
)

# -----------------------
# Plotly
# -----------------------

left, right = st.columns(2)

with left:

    count_df = (
        filtered
        .groupby(GU)
        .size()
        .reset_index(name="개수")
    )

    fig = px.bar(
        count_df,
        x=GU,
        y="개수",
        title="자치구별 주차장 개수"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

with right:

    if FEE in filtered.columns:

        fig2 = px.histogram(
            filtered,
            x=FEE,
            nbins=20,
            title="기본요금 분포"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

# -----------------------
# 데이터
# -----------------------

st.subheader("데이터")

st.dataframe(
    filtered,
    use_container_width=True
)

# -----------------------
# 다운로드
# -----------------------

csv = filtered.to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    "CSV 다운로드",
    csv,
    "parking.csv",
    "text/csv"
)
