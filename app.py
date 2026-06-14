import streamlit as st
import json
import pandas as pd
from openai import OpenAI
from supabase import create_client

# ──────────────────────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ad Doctor",
    page_icon="⚕",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── 폰트 (style과 반드시 분리) ──────────────────────────
st.markdown(
    '<link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" rel="stylesheet">',
    unsafe_allow_html=True,
)

# ── 전역 CSS ──────────────────────────────────────────
st.markdown("""<style>
* { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'Pretendard', -apple-system, sans-serif !important;
}
.block-container {
    max-width: 420px !important;
    padding: 1.5rem 1rem 6rem !important;
    margin: 0 auto !important;
}
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
hr { margin: 0.5rem 0 !important; }
</style>""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────
# 인라인 스타일 상수
# ──────────────────────────────────────────────────────
S = {
    "hero": (
        "background:linear-gradient(160deg,#042C53 0%,#0C447C 38%,#185FA5 68%,#378ADD 100%);"
        "border-radius:16px;padding:52px 24px 48px;text-align:center;margin-bottom:20px;"
    ),
    "hero_sub": (
        "font-size:12px;font-weight:300;color:rgba(183,220,255,0.85);"
        "letter-spacing:0.5px;margin:0 0 10px;font-family:'Pretendard',sans-serif;"
    ),
    "hero_title": (
        "font-size:44px;font-weight:800;color:#fff;letter-spacing:-1px;"
        "line-height:1.05;margin:0 0 6px;font-family:'Pretendard',sans-serif;"
    ),
    "hero_light": "font-weight:300;color:rgba(183,220,255,0.8);",
    "hero_div":   "width:28px;height:1.5px;background:rgba(255,255,255,0.3);border-radius:2px;margin:14px auto 0;",
    "risk_hdr": (
        "background:linear-gradient(135deg,#042C53 0%,#185FA5 100%);"
        "border-radius:12px;padding:16px;margin-bottom:16px;"
    ),
    "risk_badge": (
        "display:inline-flex;align-items:center;gap:6px;"
        "background:rgba(255,255,255,0.15);border:0.5px solid rgba(255,255,255,0.3);"
        "border-radius:20px;padding:4px 12px;font-size:13px;font-weight:700;"
        "font-family:'Pretendard',sans-serif;color:#fff;margin-bottom:8px;"
    ),
    "risk_sum": (
        "font-size:13px;font-weight:300;color:rgba(183,220,255,0.85);"
        "line-height:1.6;font-family:'Pretendard',sans-serif;margin:0;"
    ),
    "card_high":    "border:0.5px solid #ffd0d0;border-radius:10px;padding:12px 14px;background:#fff1f1;margin-bottom:8px;",
    "card_mid":     "border:0.5px solid #ffe5a0;border-radius:10px;padding:12px 14px;background:#fffbf0;margin-bottom:8px;",
    "card_low":     "border:0.5px solid #C0DD97;border-radius:10px;padding:12px 14px;background:#EAF3DE;margin-bottom:8px;",
    "card_neutral": "border:0.5px solid rgba(24,95,165,0.12);border-radius:10px;padding:12px 14px;background:#f8faff;margin-bottom:8px;",
    "badge_blue":   "font-size:11px;font-weight:600;padding:2px 8px;border-radius:20px;background:linear-gradient(135deg,#E6F1FB,#d0e8ff);color:#0C447C;display:inline-block;margin-bottom:6px;",
    "bubble_user":  "background:linear-gradient(135deg,#0C447C,#185FA5);color:#fff;border-radius:16px 16px 4px 16px;padding:10px 14px;margin:6px 0 6px 15%;font-size:14px;font-weight:400;line-height:1.6;font-family:'Pretendard',sans-serif;",
    "bubble_bot":   "background:#f0f4ff;border:0.5px solid rgba(24,95,165,0.12);color:#1a2340;border-radius:16px 16px 16px 4px;padding:10px 14px;margin:6px 15% 6px 0;font-size:14px;font-weight:300;line-height:1.6;font-family:'Pretendard',sans-serif;",
    "hist_hdr":     "background:linear-gradient(135deg,#0C447C,#185FA5);border-radius:12px;padding:16px;margin-bottom:16px;",
    "hist_item":    "display:flex;align-items:center;gap:10px;padding:10px 12px;border:0.5px solid rgba(24,95,165,0.1);border-radius:10px;margin-bottom:7px;background:#f8faff;",
    "persona_badge":"font-size:11px;font-weight:600;padding:3px 10px;border-radius:20px;background:linear-gradient(135deg,#E6F1FB,#d0e8ff);color:#0C447C;display:inline-block;margin-bottom:12px;",
}

RISK_COLOR = {"고위험": "#E24B4A", "중위험": "#EF9F27", "저위험": "#639922", "적합": "#1D9E75"}

def dot(level, size=10):
    c = RISK_COLOR.get(level, "#aaa")
    return (
        f'<span style="width:{size}px;height:{size}px;border-radius:50%;'
        f'background:{c};display:inline-block;vertical-align:middle;margin-right:5px;"></span>'
    )

# ──────────────────────────────────────────────────────
# Session state
# ──────────────────────────────────────────────────────
for k, v in {
    "page": "home",
    "diagnosis_result": None,
    "diagnosis_input": {},
    "chat_history": [],
    "prior_context": None,
    "detected_persona": None,
}.items():
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

VALID_PERSONAS = {"소상공인", "행정모니터링 담당자", "기업 컴플라이언스 담당자"}
VALID_TYPES    = {"실무적용", "법령해석", "리스크점검", "법령동향"}

# ──────────────────────────────────────────────────────
# 데이터 로드
# ──────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_graphs():
    """law_graph_full + knowledge_graph 각각 독립 로드"""
    law = {"nodes": {}, "edges": [], "stats": {}}
    kg  = {"nodes": {}, "edges": [], "stats": {}}
    try:
        with open("law_graph_full.json", "r", encoding="utf-8") as f:
            law = json.load(f)
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
    return law, kg


@st.cache_data(show_spinner=False)
def load_qa_dataset() -> list:
    """QA 데이터셋 로드 + 컬럼 swap 자동 수정"""
    try:
        df = pd.read_excel("QA데이터셋__0521_.xlsx")

        # 일부 행에서 페르소나↔질문유형이 뒤바뀐 경우 자동 수정
        def fix_row(row):
            p, t = row["페르소나"], row["질문유형"]
            if p in VALID_TYPES and t in VALID_PERSONAS:
                return t, p          # swap
            return p, t              # 그대로

        df[["페르소나", "질문유형"]] = df.apply(
            lambda r: pd.Series(fix_row(r)), axis=1
        )

        # 핵심 컬럼만 남겨 메모리 절약
        cols = ["ID", "페르소나", "질문유형", "난이도", "주제",
                "질문", "답변", "근거", "응답 설계 포인트", "의도된 설명 스타일"]
        return df[cols].to_dict("records")

    except FileNotFoundError:
        st.warning("QA데이터셋__0521_.xlsx 파일을 찾을 수 없습니다.")
        return []
    except Exception as e:
        st.warning(f"QA 데이터셋 로드 오류: {e}")
        return []


# ──────────────────────────────────────────────────────
# law_graph_full 전용 (dict of dicts + chunks)
# ──────────────────────────────────────────────────────
def get_law_chunks(law_graph: dict, industry: str, query: str, max_chunks: int = 20) -> list:
    all_chunks = []
    keywords = [w for w in (industry + " " + query).split() if len(w) > 1]

    def score(text):
        return sum(1 for k in keywords if k in text)

    try:
        nodes = law_graph.get("nodes", {})
        for doc_id, doc in nodes.get("심사지침", {}).items():
            if not isinstance(doc, dict):
                continue
            for chunk in doc.get("chunks", []):
                content = chunk.get("content", "")
                all_chunks.append({"doc": doc.get("명칭", doc_id), "type": "심사지침",
                                    "content": content, "score": score(content) + 10})
        for ntype in ["법률", "시행령", "시행규칙", "행정규칙", "고시", "지침_기준"]:
            for doc_id, doc in nodes.get(ntype, {}).items():
                if not isinstance(doc, dict):
                    continue
                for chunk in doc.get("chunks", []):
                    content = chunk.get("content", "")
                    s = score(content)
                    if s > 0:
                        all_chunks.append({"doc": doc.get("명칭", doc_id), "type": ntype,
                                            "content": content, "score": s})
    except Exception as e:
        st.warning(f"[law_graph] 청크 추출 오류: {e}")

    all_chunks.sort(key=lambda x: x["score"], reverse=True)
    return all_chunks[:max_chunks]


# ──────────────────────────────────────────────────────
# knowledge_graph 전용 (dict of lists, chunks 없음)
# ──────────────────────────────────────────────────────
def get_similar_cases(kg: dict, industry: str, query: str, max_cases: int = 3) -> list:
    results = []
    keywords = [w for w in (industry + " " + query).split() if len(w) > 1]

    def score(text):
        return sum(1 for k in keywords if k in str(text))

    try:
        nodes          = kg.get("nodes", {})
        case_list      = nodes.get("사건", [])
        violation_list = nodes.get("위반행위", [])
        sanction_list  = nodes.get("처분", [])
        judgment_list  = nodes.get("법리판단", [])

        for case in case_list:
            if not isinstance(case, dict):
                continue
            cid   = case.get("id", "")
            viols = [v for v in violation_list if isinstance(v, dict) and cid in v.get("id", "")]
            sancs = [s for s in sanction_list  if isinstance(s, dict) and cid in s.get("id", "")]
            judgs = [j for j in judgment_list  if isinstance(j, dict) and cid in j.get("id", "")]
            score_text = " ".join(v.get("광고문구","") + " " + v.get("내용요약","") for v in viols)
            results.append({
                "사건명": cid, "의결번호": case.get("의결번호",""),
                "위반행위": viols[:2], "처분": sancs[:2], "법리판단": judgs[:1],
                "score": score(score_text),
            })
        results.sort(key=lambda x: x["score"], reverse=True)
    except Exception as e:
        st.warning(f"[knowledge_graph] 사례 추출 오류: {e}")

    return results[:max_cases]


# ──────────────────────────────────────────────────────
# QA 데이터셋 활용 함수
# ──────────────────────────────────────────────────────
def detect_persona(question: str) -> str:
    """질문 패턴으로 페르소나 추론"""
    q = question
    소상공인_signals    = ["저희 가게", "저희 식당", "저희 매장", "운영 중인데",
                         "사용할 수", "쓸 수 있나요", "괜찮나요", "문제가 될까요",
                         "표현을 사용", "광고하려는데"]
    컴플라이언스_signals = ["저희 회사", "내부 통제", "과징금", "감경", "리스크",
                          "컴플라이언스", "산정", "부과기준", "재발 방지"]
    행정_signals        = ["판단 기준", "인정한 이유", "구체적 기준", "법령해석",
                          "의결서에서", "피심인", "공정위가"]

    s_score = sum(1 for s in 소상공인_signals    if s in q)
    c_score = sum(1 for s in 컴플라이언스_signals if s in q)
    a_score = sum(1 for s in 행정_signals        if s in q)

    if s_score >= c_score and s_score >= a_score:
        return "소상공인"
    elif c_score >= a_score:
        return "기업 컴플라이언스 담당자"
    else:
        return "행정모니터링 담당자"


def get_similar_qa(qa_list: list, question: str, persona: str, top_k: int = 3) -> list:
    """유사 QA 추출 (키워드 매칭 + 동일 페르소나 가중치)"""
    if not qa_list:
        return []
    keywords = [w for w in question.split() if len(w) > 1]

    def score(qa):
        text = str(qa.get("질문", "")) + str(qa.get("주제", ""))
        kw_score = sum(1 for k in keywords if k in text)
        persona_bonus = 3 if qa.get("페르소나") == persona else 0
        return kw_score + persona_bonus

    scored = sorted(qa_list, key=score, reverse=True)
    # 점수 0인 것 제외
    return [q for q in scored[:top_k] if score(q) > 0]


def get_style_instruction(persona: str) -> str:
    styles = {
        "소상공인":           "쉽고 직관적으로 설명하며, 대안 표현을 구체적으로 제시하세요. 법령 조문보다 실용적 조언을 우선합니다.",
        "행정모니터링 담당자": "법령 조문과 판례를 명확히 인용하고, 피심인 반박 논거와 공정위 판단 구조를 중심으로 설명하세요.",
        "기업 컴플라이언스 담당자": "리스크 수치와 내부 통제 포인트를 강조하고, 유사 의결서 과징금 금액과 감경 요인을 함께 설명하세요.",
    }
    return styles.get(persona, "명확하고 간결하게 설명하세요.")


# ──────────────────────────────────────────────────────
# QnA 컨텍스트 빌더 (법령 + 의결서 + QA 예시)
# ──────────────────────────────────────────────────────
def build_qna_context(law_graph: dict, kg: dict, question: str) -> str:
    parts = []
    try:
        chunks = get_law_chunks(law_graph, "", question, max_chunks=15)
        if chunks:
            parts.append("## 관련 법령\n" + "\n\n".join(
                f"[{c['type']}] {c['doc']}\n{c['content']}" for c in chunks))
    except Exception:
        pass
    try:
        cases = get_similar_cases(kg, "", question, max_cases=4)
        if cases:
            texts = []
            for c in cases:
                viols = ", ".join(v.get("광고문구", v.get("내용요약", "")) for v in c["위반행위"] if isinstance(v, dict))
                sancs = ", ".join(s.get("내용", "") for s in c["처분"] if isinstance(s, dict))
                judgs = " ".join(j.get("내용", "") for j in c["법리판단"] if isinstance(j, dict))
                texts.append(f"사건: {c['사건명']}\n의결번호: {c['의결번호']}\n위반 광고: {viols}\n처분: {sancs}\n법리: {judgs}")
            parts.append("## 유사 의결서 사례\n" + "\n\n".join(texts))
    except Exception:
        pass
    return "\n\n".join(parts)


# ──────────────────────────────────────────────────────
# OpenAI
# ──────────────────────────────────────────────────────
def get_client():
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def analyze_ad(law_graph, kg, industry, status, suspended, ad_copy) -> dict:
    client = get_client()
    chunks = get_law_chunks(law_graph, industry, ad_copy, 20)
    cases  = get_similar_cases(kg, industry, ad_copy, 3)

    law_ctx = "\n\n".join(f"[{c['type']}] {c['doc']}\n{c['content']}" for c in chunks) or "관련 법령 없음"

    case_lines = []
    for c in cases:
        viols = "\n".join(f"  - {v.get('광고문구','')}: {v.get('내용요약','')}"
                          for v in c["위반행위"] if isinstance(v, dict))
        sancs = "\n".join(f"  - {s.get('유형','')}: {s.get('내용','')}"
                          for s in c["처분"] if isinstance(s, dict))
        case_lines.append(f"사건: {c['사건명']}\n의결번호: {c['의결번호']}\n위반행위:\n{viols}\n처분:\n{sancs}")
    case_ctx = "\n\n".join(case_lines) or "유사 사례 없음"

    prompt = f"""당신은 대한민국 공정거래위원회 표시광고법 전문 심사관입니다.
아래 광고 문구의 법적 리스크를 진단하고 반드시 유효한 JSON 형식으로만 응답하세요.

업종: {industry} / 진행상황: {status} / 중단여부: {suspended}
광고 문구: \"\"\"{ad_copy}\"\"\"

참고 법령:
{law_ctx}

유사 의결서 사례:
{case_ctx}

응답 JSON 스키마 (다른 텍스트 없이 JSON만):
{{
  "risk_level": "고위험 | 중위험 | 저위험 | 적합",
  "summary": "2~3문장 핵심 요약",
  "violations": [{{"법령":"","조항":"","내용":"","심각도":"높음|중간|낮음"}}],
  "recommendations": ["권고사항"],
  "similar_cases": [{{"사건명":"","의결번호":"","요약":""}}]
}}"""

    res = get_client().chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1, max_tokens=1200,
    )
    return json.loads(res.choices[0].message.content)


def answer_qna(law_graph, kg, qa_list, question, history, prior_context=None) -> tuple[str, str]:
    """
    Returns: (answer_text, detected_persona)
    """
    persona   = detect_persona(question)
    style     = get_style_instruction(persona)
    similar_qa = get_similar_qa(qa_list, question, persona, top_k=3)
    context   = build_qna_context(law_graph, kg, question)

    # QA 예시 문자열 구성
    qa_examples = ""
    if similar_qa:
        examples = []
        for qa in similar_qa:
            examples.append(
                f"[예시 질문] {qa.get('질문','')}\n"
                f"[예시 답변] {qa.get('답변','')[:300]}..."
            )
        qa_examples = "\n\n## 유사 QA 예시 (이 스타일 참고)\n" + "\n\n".join(examples)

    system = f"""당신은 대한민국 표시광고법 전문 AI 어시스턴트입니다.
아래 법령, 의결서 사례, QA 예시를 참고하여 질문에 답변하세요.

감지된 사용자 유형: {persona}
답변 스타일 지침: {style}

답변 규칙:
1. 법령/의결서에 근거가 있을 때만 구체적으로 답변합니다.
2. 근거가 불충분하거나 사안이 복잡하면 반드시 "법률 전문가 상담을 권장합니다"라고 명시합니다.
3. 유사 의결서 사례가 있으면 사건명/의결번호와 함께 언급하고, 없으면 솔직히 말합니다.
4. 한국어로 간결하게 3~5문장 이내로 답변합니다.

## 참고 법령 및 사례
{context if context else "현재 참고 가능한 데이터가 없습니다."}
{qa_examples}
{f"## 이전 진단 맥락{chr(10)}{prior_context}" if prior_context else ""}"""

    messages = [{"role": "system", "content": system}]
    for h in history[-6:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": question})

    res = get_client().chat.completions.create(
        model="gpt-4o-mini", messages=messages,
        temperature=0.3, max_tokens=600,
    )
    return res.choices[0].message.content, persona


# ──────────────────────────────────────────────────────
# Supabase
# ──────────────────────────────────────────────────────
def get_sb():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def save_diagnosis(industry, status, suspended, ad_copy, result):
    try:
        get_sb().table("ad_diagnoses").insert({
            "industry": industry, "status": status,
            "is_suspended": suspended == "중단", "ad_copy": ad_copy,
            "risk_level":   result.get("risk_level"),
            "risk_summary": result.get("summary"),
            "violations":   result.get("violations", []),
            "recommendations": result.get("recommendations", []),
        }).execute()
    except Exception as e:
        st.warning(f"저장 실패: {e}")


def load_history() -> list:
    try:
        res = get_sb().table("ad_diagnoses").select("*").order("created_at", desc=True).limit(30).execute()
        return res.data or []
    except Exception as e:
        st.warning(f"이력 로드 실패: {e}")
        return []


# ──────────────────────────────────────────────────────
# 하단 네비게이션
# ──────────────────────────────────────────────────────
NAV = [("홈","home"),("진단","diagnose"),("질문","qna"),("이력","history")]

def bottom_nav():
    st.markdown("---")
    cur = st.session_state.page
    active = "diagnose" if cur == "result" else cur
    cols = st.columns(len(NAV))
    for col, (label, page) in zip(cols, NAV):
        with col:
            btn = f"**{label}**" if active == page else label
            if st.button(btn, key=f"nav_{page}", use_container_width=True):
                if page != cur:
                    st.session_state.page = page
                    st.rerun()


# ──────────────────────────────────────────────────────
# 화면 1 — 홈
# ──────────────────────────────────────────────────────
def page_home():
    st.markdown(
        f'<div style="{S["hero"]}">'
        f'<p style="{S["hero_sub"]}">온라인 마케팅 리스크 진단 도우미</p>'
        f'<h1 style="{S["hero_title"]}">Ad<span style="{S["hero_light"]}">Doctor</span></h1>'
        f'<div style="{S["hero_div"]}"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )
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
    ad_copy   = st.text_area("광고 문구", placeholder="진단할 광고 문구를 입력하세요...", height=130)

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
                st.error("분석 결과 파싱 실패. 다시 시도해주세요.")
            except Exception as e:
                st.error(f"오류: {e}")


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

    st.markdown(
        f'<div style="{S["risk_hdr"]}">'
        f'<div style="{S["risk_badge"]}">{dot(level, 8)}{level}</div>'
        f'<p style="{S["risk_sum"]}">{summary}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    violations = result.get("violations", [])
    if violations:
        st.markdown("**위반 가능 사항**")
        for v in violations:
            sev  = v.get("심각도", "중간")
            card = S["card_high"] if sev == "높음" else S["card_mid"] if sev == "중간" else S["card_low"]
            tc   = "#c0392b" if sev == "높음" else "#9a6700" if sev == "중간" else "#3b6d11"
            bc   = "#7a3030" if sev == "높음" else "#7a5500" if sev == "중간" else "#2d5016"
            st.markdown(
                f'<div style="{card}">'
                f'<div style="font-size:12px;font-weight:700;color:{tc};margin-bottom:4px;">'
                f'{v.get("법령","")} {v.get("조항","")} ({sev})</div>'
                f'<div style="font-size:13px;font-weight:300;color:{bc};line-height:1.5;">{v.get("내용","")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    recs = result.get("recommendations", [])
    if recs:
        st.markdown("**개선 권고사항**")
        for r in recs:
            st.markdown(f"- {r}")

    similar = result.get("similar_cases", [])
    st.markdown("**유사 의결서 사례**")
    if similar:
        for c in similar:
            st.markdown(
                f'<div style="{S["card_neutral"]}">'
                f'<span style="{S["badge_blue"]}">{c.get("의결번호","")}</span>'
                f'<div style="font-size:13px;font-weight:600;color:#1a2340;margin-bottom:4px;">{c.get("사건명","")}</div>'
                f'<div style="font-size:12px;font-weight:300;color:#4a5a7a;line-height:1.5;">{c.get("요약","")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown('<p style="font-size:13px;color:#888;">유사 의결서 사례를 찾지 못했습니다.</p>', unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("추가 질문하기", use_container_width=True):
            st.session_state.prior_context = (
                f"업종: {inp.get('industry')}\n"
                f"광고문구: {inp.get('ad_copy')}\n"
                f"진단결과: {level}\n요약: {summary}"
            )
            st.session_state.page = "qna"
            st.rerun()
    with col2:
        if st.button("새 진단", use_container_width=True):
            st.session_state.page = "diagnose"
            st.rerun()


# ──────────────────────────────────────────────────────
# 화면 4 — QnA (QA 데이터셋 연동)
# ──────────────────────────────────────────────────────
def page_qna(law_graph, kg, qa_list):
    st.markdown("### 질문하기")

    # 페르소나 뱃지 표시
    persona = st.session_state.get("detected_persona")
    if persona:
        persona_label = {"소상공인": "소상공인", "행정모니터링 담당자": "행정 담당자", "기업 컴플라이언스 담당자": "컴플라이언스"}.get(persona, persona)
        st.markdown(f'<span style="{S["persona_badge"]}">감지된 유형: {persona_label}</span>', unsafe_allow_html=True)

    if st.session_state.prior_context:
        st.info("이전 진단 결과를 바탕으로 질문할 수 있습니다.")
        if st.button("맥락 초기화", use_container_width=False):
            st.session_state.prior_context   = None
            st.session_state.chat_history    = []
            st.session_state.detected_persona = None
            st.rerun()

    for msg in st.session_state.chat_history:
        style = S["bubble_user"] if msg["role"] == "user" else S["bubble_bot"]
        st.markdown(f'<div style="{style}">{msg["content"]}</div>', unsafe_allow_html=True)

    question = st.text_area(
        "질문", placeholder="예: '임상 검증'이라는 표현을 건강기능식품 광고에 쓸 수 있나요?",
        height=100, key="qna_input", label_visibility="collapsed",
    )

    if st.button("질문하기", type="primary", use_container_width=True):
        if not question.strip():
            st.warning("질문을 입력해주세요.")
            return
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.spinner("답변을 생성하는 중입니다..."):
            try:
                answer, detected = answer_qna(
                    law_graph, kg, qa_list,
                    question,
                    st.session_state.chat_history[:-1],
                    st.session_state.prior_context,
                )
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                st.session_state.detected_persona = detected
                st.rerun()
            except Exception as e:
                st.session_state.chat_history.pop()
                st.error(f"답변 생성 오류: {e}")


# ──────────────────────────────────────────────────────
# 화면 5 — 이력
# ──────────────────────────────────────────────────────
def page_history():
    history = load_history()
    cnt = len(history)
    st.markdown(
        f'<div style="{S["hist_hdr"]}">'
        f'<div style="font-size:18px;font-weight:800;color:#fff;font-family:Pretendard,sans-serif;">진단 이력</div>'
        f'<div style="font-size:12px;font-weight:300;color:rgba(183,220,255,0.8);margin-top:2px;">총 {cnt}건의 진단 기록</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    opts     = ["전체", "고위험", "중위험", "저위험", "적합"]
    selected = st.radio("필터", opts, horizontal=True, label_visibility="collapsed")

    if not history:
        st.info("아직 진단 이력이 없습니다.")
        return

    for row in history:
        level = row.get("risk_level", "")
        if selected != "전체" and level != selected:
            continue
        created = (row.get("created_at", "") or "")[:10]
        raw     = row.get("ad_copy", "")
        preview = (raw[:38] + "...") if len(raw) > 38 else raw
        dc      = RISK_COLOR.get(level, "#aaa")
        st.markdown(
            f'<div style="{S["hist_item"]}">'
            f'<span style="width:8px;height:8px;border-radius:50%;background:{dc};flex-shrink:0;display:inline-block;"></span>'
            f'<div style="flex:1;min-width:0;">'
            f'<div style="font-size:13px;font-weight:600;color:#1a2340;">{row.get("industry","")}'
            f'&nbsp;<span style="font-size:11px;font-weight:300;color:#6b7a99;">{level}</span></div>'
            f'<div style="font-size:12px;font-weight:300;color:#6b7a99;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">&ldquo;{preview}&rdquo;</div>'
            f'</div>'
            f'<div style="font-size:11px;color:#aaa;white-space:nowrap;flex-shrink:0;">{created}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ──────────────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────────────
def main():
    law_graph, kg = load_graphs()
    qa_list       = load_qa_dataset()
    page          = st.session_state.page

    if page == "home":
        page_home()
    elif page == "diagnose":
        page_diagnose(law_graph, kg)
    elif page == "result":
        page_result()
    elif page == "qna":
        page_qna(law_graph, kg, qa_list)
    elif page == "history":
        page_history()
    else:
        page_home()

    bottom_nav()


if __name__ == "__main__":
    main()
