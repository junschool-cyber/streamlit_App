import streamlit as st
from openai import OpenAI

# -----------------------------
# 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="AI 문제집 추천 서비스",
    page_icon="📚",
    layout="wide"
)

st.title("📚 AI 문제집 추천 서비스")

st.write("""
학년, 과목, 교육과정을 선택하면
AI가 학생에게 맞는 문제집과 참고서를 추천합니다.
""")

# -----------------------------
# OpenAI API
# -----------------------------
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("OPENAI_API_KEY가 설정되지 않았습니다.")
    st.stop()

# -----------------------------
# 입력
# -----------------------------
grade = st.selectbox(
    "학년",
    [
        "초1","초2","초3","초4","초5","초6",
        "중1","중2","중3",
        "고1","고2","고3"
    ]
)

subject = st.selectbox(
    "과목",
    [
        "국어",
        "수학",
        "영어",
        "사회",
        "역사",
        "과학",
        "통합과학",
        "물리",
        "화학",
        "생명과학",
        "지구과학"
    ]
)

curriculum = st.selectbox(
    "교육과정",
    [
        "2022 개정 교육과정",
        "2015 개정 교육과정"
    ]
)

level = st.selectbox(
    "학습 수준",
    [
        "기초",
        "기본",
        "중상",
        "심화",
        "최상위"
    ]
)

purpose = st.selectbox(
    "학습 목적",
    [
        "학교 시험",
        "내신 대비",
        "수능 대비",
        "선행학습",
        "복습",
        "심화학습"
    ]
)

extra = st.text_area(
    "추가 요청사항",
    placeholder="예) 계산이 약합니다. 서술형 대비를 원합니다."
)

# -----------------------------
# 추천 버튼
# -----------------------------
if st.button("📚 AI 추천받기", use_container_width=True):

    prompt = f"""
당신은 대한민국 최고의 교육 전문가입니다.

다음 정보를 참고하여 실제 시중에서 판매되는 문제집과 참고서를 추천해주세요.

[학생 정보]
학년 : {grade}
과목 : {subject}
교육과정 : {curriculum}
학습수준 : {level}
학습목표 : {purpose}

추가 요청
{extra}

반드시 아래 형식으로 작성하세요.

# 추천 문제집 (3권)

각 교재마다

- 교재명
- 출판사
- 난이도
- 특징
- 추천 이유
- 이런 학생에게 추천

---

# 추천 참고서 (2권)

---

# 가장 추천하는 교재 TOP1

왜 가장 추천하는지 자세히 설명

---

# 공부 방법

4주 학습 계획까지 작성

가능하면 표를 활용하고 보기 좋게 정리해주세요.
"""

    with st.spinner("AI가 추천 중입니다..."):

        response = client.chat.completions.create(
            model="gpt-4.1",
            temperature=0.7,
            messages=[
                {
                    "role":"system",
                    "content":"당신은 대한민국 교재 전문가입니다. 존재하지 않는 책은 추천하지 말고 실제 출판된 교재를 추천하세요."
                },
                {
                    "role":"user",
                    "content":prompt
                }
            ]
        )

        answer = response.choices[0].message.content

    st.success("추천이 완료되었습니다!")

    st.markdown(answer)

st.divider()

st.caption("Made with ❤️ using Streamlit + OpenAI")
