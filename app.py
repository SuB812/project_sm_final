import streamlit as st
import json
import re
from openai import OpenAI
from supabase import create_client
from datetime import datetime

# ──────────────────────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ad Doctor",
    page_icon="⚕",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css">
<style>
* { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'Pretendard', -apple-system, sans-serif !important;
}
.block-container {
    max-width: 420px !important;
    padding: 1.5rem 1rem 6rem !important;
    margin: 0 auto !important;
}

/* 버튼 */
.stButton > button {
    width: 100% !important;
    font-family: 'Pretendard', sans-serif !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    letter-spacing: 0.2px !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0C447C 0%, #185FA5 55%, #378ADD 100%) !important;
    border: none !important;
    color: #fff !important;
    font-size: 15px !important;
}

/* 홈 */
.home-hero {
    background: linear-gradient(160deg, #042C53 0%, #0C447C 38%, #185FA5 68%, #378ADD 100%);
    border-radius: 16px;
    padding: 52px 24px 48px;
    text-align: center;
    margin-bottom: 20px;
    overflow: hidden;
}
.home-sub {
    font-size: 12px;
    font-weight: 300;
    color: rgba(183,220,255,0.85);
    letter-spacing: 0.5px;
    margin: 0 0 10px;
}
.home-title {
    font-size: 44px;
    font-weight: 800;
    color: #fff;
    letter-spacing: -1px;
    line-height: 1.05;
    margin: 0 0 6px;
}
.home-title-light { font-weight: 300; color: rgba(183,220,255,0.8); }
.home-divider {
    width: 28px; height: 1.5px;
    background: rgba(255,255,255,0.3);
    border-radius: 2px;
    margin: 14px auto 0;
}

/* 결과 헤더 */
.risk-header {
    background: linear-gradient(135deg, #042C53 0%, #185FA5 100%);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
}
.risk-level-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255,255,255,0.15);
    border: 0.5px solid rgba(255,255,255,0.3);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 13px;
    font-weight: 700;
    font-family: 'Pretendard', sans-serif;
    color: #fff;
    margin-bottom: 8px;
}
.risk-summary {
    font-size: 13px;
    font-weight: 300;
    color: rgba(183,220,255,0.85);
    line-height: 1.6;
    font-family: 'Pretendard', sans-serif;
    margin: 0;
}

/* 리스크 카드 */
.card-high {
    border: 0.5px solid #ffd0d0; border-radius: 10px;
    padding: 12px 14px; background: #fff1f1; margin-bottom: 8px;
}
.card-mid {
    border: 0.5px solid #ffe5a0; border-radius: 10px;
    padding: 12px 14px; background: #fffbf0; margin-bottom: 8px;
}
.card-low {
    border: 0.5px solid #C0DD97; border-radius: 10px;
    padding: 12px 14px; background: #EAF3DE; margin-bottom: 8px;
}
.card-neutral {
    border: 0.5px solid rgba(24,95,165,0.12); border-radius: 10px;
    padding: 12px 14px; background: #f8faff; margin-bottom: 8px;
}
.badge-blue {
    font-size: 11px; font-weight: 600; padding: 2px 8px;
    border-radius: 20px;
    background: linear-gradient(135deg, #E6F1FB, #d0e8ff);
    color: #0C447C; display: inline-block; margin-bottom: 6px;
}

/* 채팅 말풍선 */
.bubble-user {
    background: linear-gradient(135deg, #0C447C, #185FA5);
    color: #fff; border-radius: 16px 16px 4px 16px;
    padding: 10px 14px; margin: 6px 0 6px 15%;
    font-size: 14px; font-weight: 400; line-height: 1.6;
}
.bubble-bot {
    background: #f0f4ff;
    border: 0.5px solid rgba(24,95,165,0.12);
    color: #1a2340; border-radius: 16px 16px 16px 4px;
    padding: 10px 14px; margin: 6px 15% 6px 0;
    font-size: 14px; font-weight: 300; line-height: 1.6;
}

/* 이력 헤더 */
.hist-header {
    background: linear-gradient(135deg, #0C447C, #185FA5);
    border-radius: 12px; padding: 16px; margin-bottom: 16px;
}
.hist-header-title {
    font-size: 18px; font-weight: 800; color: #fff;
    font-family: 'Pretendard', sans-serif;
}
.hist-header-sub {
    font-size: 12px; font-weight: 300;
    color: rgba(183,220,255,0.8); margin-top: 2px;
}
.hist-item {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 12px;
    border: 0.5px solid rgba(24,95,165,0.1);
    border-radius: 10px; margin-bottom: 7px; background: #f8faff;
}
.hdot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.hdot-high { background: #E24B4A; }
.hdot-mid  { background: #EF9F27; }
.hdot-ok   { background: #1D9E75; }

hr { margin: 0.5rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# Session state 초기화
# ──────────────────────────────────────────────────────
_defaults = {
    "page": "home",
    "diagnosis_result": None,
    "diagnosis_input": {},
    "chat_history": [],
    "prior_context": None,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ──────────────────────────────────────────────────────
# 상수
# ──────────────────────────────────────────────────────
INDUSTRY_OPTIONS = [
    "식품 / 건강기능식품", "화장품 / 뷰티", "금융 / 보험",
    "부동산", "의료 / 제약", "방송 / 통신",
    "의류 / 패션", "교육 / 학원", "여행 / 숙박", "기타",
]
STATUS_OPTIONS = ["기획 중", "제작 중", "집행 중", "집행 종료"]

RISK_DOT = {
    "고위험": "#E24B4A",
    "중위험": "#EF9F27",
    "저위험": "#639922",
    "적합":  "#1D9E75",
}

def dot_html(level: str, size: int = 10) -> str:
    color = RISK_DOT.get(level, "#aaa")
    return (
        f'<span style="width:{size}px;height:{size}px;border-radius:50%;'
        f'background:{color};display:inline-block;'
        f'margin-right:6px;vertical-align:middle;"></span>'
    )

# ──────────────────────────────────────────────────────
# 데이터 로드 — 두 파일을 완전히 분리해서 처리
# ──────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_graphs():
    """두 JSON 파일을 각각 독립적으로 로드. 한쪽 실패해도 앱 동작."""
    law_graph = {"nodes": {}, "edges": [], "stats": {}}
    kg = {"nodes": {}, "edges": [], "stats": {}}

    try:
        with open("law_graph_full.json", "r", encoding="utf-8") as f:
            law_graph = json.load(f)
    except FileNotFoundError:
        st.warning("law_graph_full.json 파일을 찾을 수 없습니다.")
    except json.JSONDecodeError as e:
        st.warning(f"law_graph_full.json 파싱 오류: {e}")

    try:
        with open("knowledge_graph.json", "r", encoding="utf-8") as f:
            kg = json.load(f)
    except FileNotFoundError:
        st.warning("knowledge_graph.json 파일을 찾을 수 없습니다.")
    except json.JSONDecodeError as e:
        st.warning(f"knowledge_graph.json 파싱 오류: {e}")

    return law_graph, kg

# ──────────────────────────────────────────────────────
# law_graph_full 전용 함수 (nodes = dict of dicts, chunks 있음)
# ──────────────────────────────────────────────────────
def get_law_chunks(law_graph: dict, industry: str, query: str, max_chunks: int = 20) -> list:
    """법령 원문 청크 추출. law_graph_full 전용."""
    all_chunks = []
    keywords = [w for w in (industry + " " + query).split() if len(w) > 1]

    def score(text: str) -> int:
        return sum(1 for k in keywords if k in text)

    try:
        nodes = law_graph.get("nodes", {})

        # 심사지침 — 광고법 핵심 법령이므로 전량 포함 (가중치 +10)
        for doc_id, doc in nodes.get("심사지침", {}).items():
            if not isinstance(doc, dict):
                continue
            for chunk in doc.get("chunks", []):
                content = chunk.get("content", "")
                all_chunks.append({
                    "doc": doc.get("명칭", doc_id),
                    "type": "심사지침",
                    "content": content,
                    "score": score(content) + 10,
                })

        # 나머지 법령 — 키워드 매칭이 있는 것만
        for node_type in ["법률", "시행령", "시행규칙", "행정규칙", "고시", "지침_기준"]:
            for doc_id, doc in nodes.get(node_type, {}).items():
                if not isinstance(doc, dict):
                    continue
                for chunk in doc.get("chunks", []):
                    content = chunk.get("content", "")
                    s = score(content)
                    if s > 0:
                        all_chunks.append({
                            "doc": doc.get("명칭", doc_id),
                            "type": node_type,
                            "content": content,
                            "score": s,
                        })

    except Exception as e:
        st.warning(f"[law_graph] 청크 추출 오류: {e}")

    all_chunks.sort(key=lambda x: x["score"], reverse=True)
    return all_chunks[:max_chunks]

# ──────────────────────────────────────────────────────
# knowledge_graph 전용 함수 (nodes = dict of lists, chunks 없음)
# ──────────────────────────────────────────────────────
def get_similar_cases(kg: dict, industry: str, query: str, max_cases: int = 3) -> list:
    """유사 의결서 사례 추출. knowledge_graph 전용."""
    results = []
    keywords = [w for w in (industry + " " + query).split() if len(w) > 1]

    def score(text: str) -> int:
        return sum(1 for k in keywords if k in str(text))

    try:
        nodes = kg.get("nodes", {})
        case_list      = nodes.get("사건", [])
        violation_list = nodes.get("위반행위", [])
        sanction_list  = nodes.get("처분", [])
        judgment_list  = nodes.get("법리판단", [])

        for case in case_list:
            if not isinstance(case, dict):
                continue
            case_id = case.get("id", "")

            related_violations = [
                v for v in violation_list
                if isinstance(v, dict) and case_id in v.get("id", "")
            ]
            related_sanctions = [
                s for s in sanction_list
                if isinstance(s, dict) and case_id in s.get("id", "")
            ]
            related_judgments = [
                j for j in judgment_list
                if isinstance(j, dict) and case_id in j.get("id", "")
            ]

            score_text = " ".join(
                v.get("광고문구", "") + " " + v.get("내용요약", "")
                for v in related_violations
            )
            s = score(score_text)

            results.append({
                "사건명":  case_id,
                "의결번호": case.get("의결번호", ""),
                "의결일자": case.get("의결일자", ""),
                "위반행위": related_violations[:2],
                "처분":    related_sanctions[:2],
                "법리판단": related_judgments[:1],
                "score":   s,
            })

        results.sort(key=lambda x: x["score"], reverse=True)

    except Exception as e:
        st.warning(f"[knowledge_graph] 사례 추출 오류: {e}")

    return results[:max_cases]

# ──────────────────────────────────────────────────────
# QnA 컨텍스트 빌더 — 두 그래프를 독립적으로 시도, 합산
# ──────────────────────────────────────────────────────
def build_qna_context(law_graph: dict, kg: dict, question: str) -> str:
    parts = []

    try:
        chunks = get_law_chunks(law_graph, "", question, max_chunks=15)
        if chunks:
            body = "\n\n".join(
                f"[{c['type']}] {c['doc']}\n{c['content']}" for c in chunks
            )
            parts.append(f"## 관련 법령\n{body}")
    except Exception:
        pass

    try:
        cases = get_similar_cases(kg, "", question, max_cases=4)
        if cases:
            case_texts = []
            for c in cases:
                viols = ", ".join(
                    v.get("광고문구", v.get("내용요약", ""))
                    for v in c["위반행위"] if isinstance(v, dict)
                )
                sanctions = ", ".join(
                    s.get("내용", "") for s in c["처분"] if isinstance(s, dict)
                )
                judgments = " ".join(
                    j.get("내용", "") for j in c["법리판단"] if isinstance(j, dict)
                )
                case_texts.append(
                    f"사건: {c['사건명']}\n"
                    f"의결번호: {c['의결번호']}\n"
                    f"위반 광고: {viols}\n"
                    f"처분: {sanctions}\n"
                    f"법리 판단: {judgments}"
                )
            parts.append(f"## 유사 의결서 사례\n" + "\n\n".join(case_texts))
    except Exception:
        pass

    return "\n\n".join(parts) if parts else ""

# ──────────────────────────────────────────────────────
# OpenAI API
# ──────────────────────────────────────────────────────
def get_openai_client() -> OpenAI:
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def analyze_ad(law_graph, kg, industry, status, suspended, ad_copy) -> dict:
    client = get_openai_client()

    chunks = get_law_chunks(law_graph, industry, ad_copy, max_chunks=20)
    cases  = get_similar_cases(kg, industry, ad_copy, max_cases=3)

    law_ctx = "\n\n".join(
        f"[{c['type']}] {c['doc']}\n{c['content']}" for c in chunks
    ) or "관련 법령 데이터 없음"

    case_lines = []
    for c in cases:
        viols = "\n".join(
            f"  - 광고문구: {v.get('광고문구','')}, 내용: {v.get('내용요약','')}"
            for v in c["위반행위"] if isinstance(v, dict)
        )
        sanctions = "\n".join(
            f"  - {s.get('유형','')}: {s.get('내용','')}"
            for s in c["처분"] if isinstance(s, dict)
        )
        case_lines.append(
            f"사건: {c['사건명']}\n"
            f"의결번호: {c['의결번호']}\n"
            f"위반행위:\n{viols}\n처분:\n{sanctions}"
        )
    case_ctx = "\n\n".join(case_lines) or "유사 사례 없음"

    prompt = f"""당신은 대한민국 공정거래위원회 표시광고법 전문 심사관입니다.
아래 광고 문구의 법적 리스크를 진단하고 반드시 유효한 JSON 형식으로만 응답하세요.
다른 텍스트는 절대 포함하지 마세요.

## 진단 정보
- 업종: {industry}
- 광고 진행 상황: {status}
- 광고 중단 여부: {suspended}

## 광고 문구
\"\"\"{ad_copy}\"\"\"

## 참고 법령
{law_ctx}

## 유사 의결서 사례
{case_ctx}

## 응답 JSON 스키마
{{
  "risk_level": "고위험 | 중위험 | 저위험 | 적합",
  "summary": "2~3문장 핵심 요약",
  "violations": [
    {{
      "법령": "법령명",
      "조항": "조항",
      "내용": "위반 사유 설명",
      "심각도": "높음 | 중간 | 낮음"
    }}
  ],
  "recommendations": ["개선 권고사항 문장"],
  "similar_cases": [
    {{
      "사건명": "사건명",
      "의결번호": "의결번호",
      "요약": "처분 내용 1~2문장"
    }}
  ]
}}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=1200,
    )
    return json.loads(response.choices[0].message.content)


def answer_qna(law_graph, kg, question, chat_history, prior_context=None) -> str:
    client = get_openai_client()
    context = build_qna_context(law_graph, kg, question)

    system_prompt = f"""당신은 대한민국 표시광고법 전문 AI 어시스턴트입니다.
아래 법령과 의결서 사례를 참고하여 사용자 질문에 답변하세요.

답변 규칙:
1. 법령 또는 의결서에 근거가 있을 때만 구체적으로 답변합니다.
2. 근거가 불충분하거나 사안이 복잡할 경우 "이 사안은 법률 전문가 상담을 권장합니다"라고 명시합니다.
3. 유사 의결서 사례가 있으면 사건명/의결번호와 함께 언급합니다. 없으면 솔직히 없다고 말합니다.
4. 한국어로 간결하게, 3~5문장 이내로 답변합니다.

## 참고 자료
{context if context else "현재 참고 가능한 법령/사례 데이터가 없습니다."}

{f"## 이전 진단 맥락{chr(10)}{prior_context}" if prior_context else ""}"""

    messages = [{"role": "system", "content": system_prompt}]
    # 최근 6턴만 포함해 토큰 절약
    for h in chat_history[-6:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": question})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.3,
        max_tokens=600,
    )
    return response.choices[0].message.content

# ──────────────────────────────────────────────────────
# Supabase
# ──────────────────────────────────────────────────────
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def save_diagnosis(industry, status, suspended, ad_copy, result):
    try:
        sb = get_supabase()
        sb.table("ad_diagnoses").insert({
            "industry":      industry,
            "status":        status,
            "is_suspended":  suspended == "중단",
            "ad_copy":       ad_copy,
            "risk_level":    result.get("risk_level"),
            "risk_summary":  result.get("summary"),
            "violations":    result.get("violations", []),
            "recommendations": result.get("recommendations", []),
        }).execute()
    except Exception as e:
        st.warning(f"Supabase 저장 실패: {e}")


def load_history() -> list:
    try:
        sb = get_supabase()
        res = (
            sb.table("ad_diagnoses")
            .select("*")
            .order("created_at", desc=True)
            .limit(30)
            .execute()
        )
        return res.data or []
    except Exception as e:
        st.warning(f"이력 로드 실패: {e}")
        return []

# ──────────────────────────────────────────────────────
# 하단 네비게이션
# ──────────────────────────────────────────────────────
NAV_ITEMS = [("홈", "home"), ("진단", "diagnose"), ("질문", "qna"), ("이력", "history")]

def bottom_nav():
    st.markdown("---")
    cols = st.columns(len(NAV_ITEMS))
    current = st.session_state.page
    # result 페이지는 진단 탭 active
    active_page = "diagnose" if current == "result" else current
    for col, (label, page) in zip(cols, NAV_ITEMS):
        with col:
            is_active = active_page == page
            btn_label = f"**{label}**" if is_active else label
            if st.button(btn_label, key=f"nav_{page}", use_container_width=True):
                if page != current:
                    st.session_state.page = page
                    st.rerun()

# ──────────────────────────────────────────────────────
# 화면 1 — 홈
# ──────────────────────────────────────────────────────
def page_home():
    st.markdown("""
    <div class="home-hero">
      <p class="home-sub">온라인 마케팅 리스크 진단 도우미</p>
      <h1 class="home-title">Ad<span class="home-title-light">Doctor</span></h1>
      <div class="home-divider"></div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("시작하기", type="primary", use_container_width=True):
        st.session_state.page = "diagnose"
        st.rerun()

# ──────────────────────────────────────────────────────
# 화면 2 — 진단 입력
# ──────────────────────────────────────────────────────
def page_diagnose(law_graph, kg):
    st.markdown("### 리스크 진단")

    industry  = st.selectbox("업종", INDUSTRY_OPTIONS)
    status    = st.radio("광고 진행 상황", STATUS_OPTIONS, horizontal=True)
    suspended = st.radio("광고 중단 여부", ["미중단", "중단"], horizontal=True)
    ad_copy   = st.text_area(
        "광고 문구",
        placeholder="진단할 광고 문구를 입력하세요...",
        height=130,
    )

    if st.button("리스크 진단하기", type="primary", use_container_width=True):
        if not ad_copy.strip():
            st.warning("광고 문구를 입력해주세요.")
            return
        with st.spinner("법령을 검토하는 중입니다..."):
            try:
                result = analyze_ad(law_graph, kg, industry, status, suspended, ad_copy)
                st.session_state.diagnosis_result = result
                st.session_state.diagnosis_input  = {
                    "industry": industry, "status": status,
                    "suspended": suspended, "ad_copy": ad_copy,
                }
                save_diagnosis(industry, status, suspended, ad_copy, result)
                st.session_state.page = "result"
                st.rerun()
            except json.JSONDecodeError:
                st.error("분석 결과를 파싱하지 못했습니다. 다시 시도해주세요.")
            except Exception as e:
                st.error(f"분석 중 오류가 발생했습니다: {e}")

# ──────────────────────────────────────────────────────
# 화면 3 — 진단 결과
# ──────────────────────────────────────────────────────
def page_result():
    result = st.session_state.diagnosis_result
    inp    = st.session_state.diagnosis_input

    if not result:
        st.info("진단 결과가 없습니다. 진단 탭에서 먼저 진단해주세요.")
        return

    level   = result.get("risk_level", "알 수 없음")
    summary = result.get("summary", "")

    # 리스크 레벨 헤더 (그라데이션 카드)
    st.markdown(
        f"""<div class="risk-header">
          <div class="risk-level-badge">
            {dot_html(level, 8)}{level}
          </div>
          <p class="risk-summary">{summary}</p>
        </div>""",
        unsafe_allow_html=True,
    )

    # 위반 가능 사항
    violations = result.get("violations", [])
    if violations:
        st.markdown("**위반 가능 사항**")
        for v in violations:
            sev       = v.get("심각도", "중간")
            css_class = "card-high" if sev == "높음" else "card-mid" if sev == "중간" else "card-low"
            st.markdown(
                f"""<div class="{css_class}">
                  <div style="font-size:12px;font-weight:500;margin-bottom:4px;">
                    {v.get('법령','')} {v.get('조항','')}
                    &nbsp;<span style="font-size:10px;color:#888;">({sev})</span>
                  </div>
                  <div style="font-size:13px;color:#444;line-height:1.5;">{v.get('내용','')}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    # 개선 권고사항
    recs = result.get("recommendations", [])
    if recs:
        st.markdown("**개선 권고사항**")
        for r in recs:
            st.markdown(f"- {r}")

    # 유사 의결서 사례
    similar = result.get("similar_cases", [])
    if similar:
        st.markdown(
            f"{dot_html('적합', 8)}<span style='font-size:14px;font-weight:500;'>유사 의결서 사례</span>",
            unsafe_allow_html=True,
        )
        for c in similar:
            st.markdown(
                f"""<div class="card-neutral">
                  <span class="badge-blue">{c.get('의결번호','')}</span>
                  <div style="font-size:13px;font-weight:500;margin-bottom:4px;">{c.get('사건명','')}</div>
                  <div style="font-size:12px;color:#666;line-height:1.5;">{c.get('요약','')}</div>
                </div>""",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            "<p style='font-size:13px;color:#888;'>유사 의결서 사례를 찾지 못했습니다.</p>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("추가 질문하기", use_container_width=True):
            ctx = (
                f"업종: {inp.get('industry')}\n"
                f"광고문구: {inp.get('ad_copy')}\n"
                f"진단결과: {level}\n"
                f"요약: {summary}"
            )
            st.session_state.prior_context = ctx
            st.session_state.page = "qna"
            st.rerun()
    with col2:
        if st.button("새 진단", use_container_width=True):
            st.session_state.page = "diagnose"
            st.rerun()

# ──────────────────────────────────────────────────────
# 화면 4 — QnA
# ──────────────────────────────────────────────────────
def page_qna(law_graph, kg):
    st.markdown("### 질문하기")

    if st.session_state.prior_context:
        st.info("이전 진단 결과를 바탕으로 질문할 수 있습니다.")
        if st.button("맥락 초기화", use_container_width=False):
            st.session_state.prior_context = None
            st.session_state.chat_history  = []
            st.rerun()

    # 채팅 기록 출력
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="bubble-user">{msg["content"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="bubble-bot">{msg["content"]}</div>',
                unsafe_allow_html=True,
            )

    # 입력 폼
    question = st.text_area(
        "질문",
        placeholder="예: 건강기능식품에서 '임상 검증'이라는 표현을 쓸 수 있나요?",
        height=100,
        key="qna_input",
        label_visibility="collapsed",
    )

    if st.button("질문하기", type="primary", use_container_width=True):
        if not question.strip():
            st.warning("질문을 입력해주세요.")
            return
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.spinner("답변을 생성하는 중입니다..."):
            try:
                answer = answer_qna(
                    law_graph, kg,
                    question,
                    st.session_state.chat_history[:-1],
                    st.session_state.prior_context,
                )
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                st.rerun()
            except Exception as e:
                st.session_state.chat_history.pop()
                st.error(f"답변 생성 오류: {e}")

# ──────────────────────────────────────────────────────
# 화면 5 — 이력
# ──────────────────────────────────────────────────────
def page_history():
    cnt = len(load_history())
    st.markdown(
        f"""<div class="hist-header">
          <div class="hist-header-title">진단 이력</div>
          <div class="hist-header-sub">총 {cnt}건의 진단 기록</div>
        </div>""",
        unsafe_allow_html=True,
    )

    filter_opts = ["전체", "고위험", "중위험", "저위험", "적합"]
    selected    = st.radio("필터", filter_opts, horizontal=True, label_visibility="collapsed")

    history = load_history()

    if not history:
        st.info("아직 진단 이력이 없습니다.")
        return

    for row in history:
        level = row.get("risk_level", "")
        if selected != "전체" and level != selected:
            continue

        created      = (row.get("created_at", "") or "")[:10]
        ad_copy_raw  = row.get("ad_copy", "")
        preview      = (ad_copy_raw[:38] + "...") if len(ad_copy_raw) > 38 else ad_copy_raw

        st.markdown(
            f"""<div class="card-neutral">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;">
                <div>
                  {dot_html(level)}
                  <span style="font-size:13px;font-weight:500;">{row.get('industry','')}</span>
                  &nbsp;<span style="font-size:12px;color:#888;">{level}</span>
                </div>
                <span style="font-size:11px;color:#aaa;">{created}</span>
              </div>
              <div style="font-size:12px;color:#666;">"{preview}"</div>
            </div>""",
            unsafe_allow_html=True,
        )

# ──────────────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────────────
def main():
    law_graph, kg = load_graphs()
    page          = st.session_state.page

    if page == "home":
        page_home()
    elif page == "diagnose":
        page_diagnose(law_graph, kg)
    elif page == "result":
        page_result()
    elif page == "qna":
        page_qna(law_graph, kg)
    elif page == "history":
        page_history()
    else:
        page_home()

    bottom_nav()


if __name__ == "__main__":
    main()
