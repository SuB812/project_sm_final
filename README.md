# Ad Doctor

온라인 마케팅 리스크 진단 도우미. 광고 문구의 표시광고법 위반 가능성을 AI로 진단하고, 공정거래위원회 의결서 사례를 기반으로 유사 판례를 제시합니다.

---

## 기술 스택

- **Frontend / App**: Streamlit
- **LLM**: OpenAI GPT-4o-mini
- **지식 기반**: law_graph_full.json (법령 원문), knowledge_graph.json (의결서 사례)
- **DB**: Supabase (진단 이력 저장)
- **배포**: Streamlit Cloud

---

## 파일 구조

```
├── app.py
├── requirements.txt
├── README.md
├── law_graph_full.json        ← 법령 원문 그래프 (별도 배치 필요)
├── knowledge_graph.json       ← 의결서 사례 그래프 (별도 배치 필요)
└── .streamlit/
    └── secrets.toml           ← API 키 (로컬 전용, git에 올리지 말 것)
```

---

## 로컬 실행

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. Secrets 설정

`.streamlit/secrets.toml` 파일 생성:

```toml
OPENAI_API_KEY = "sk-..."
SUPABASE_URL   = "https://xxxx.supabase.co"
SUPABASE_KEY   = "eyJ..."
```

### 3. JSON 파일 배치

`law_graph_full.json`과 `knowledge_graph.json`을 `app.py`와 같은 루트 디렉토리에 넣습니다.

### 4. 실행

```bash
streamlit run app.py
```

---

## Supabase 테이블 설정

Supabase 대시보드 → SQL Editor에서 아래 쿼리를 실행합니다.

```sql
CREATE TABLE ad_diagnoses (
  id               uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at       timestamptz DEFAULT now(),
  industry         text,
  status           text,
  is_suspended     boolean,
  ad_copy          text,
  risk_level       text,
  risk_summary     text,
  violations       jsonb,
  recommendations  jsonb
);
```

---

## Streamlit Cloud 배포

1. GitHub 레포지토리에 `app.py`, `requirements.txt`, `README.md`, 두 JSON 파일을 push합니다.
2. [Streamlit Cloud](https://streamlit.io/cloud) → New app → 레포 연결
3. **Secrets** 탭에서 아래 내용을 입력합니다:

```toml
OPENAI_API_KEY = "sk-..."
SUPABASE_URL   = "https://xxxx.supabase.co"
SUPABASE_KEY   = "eyJ..."
```

> **주의**: `.streamlit/secrets.toml`은 절대 git에 커밋하지 마세요. `.gitignore`에 추가하세요.

```
# .gitignore
.streamlit/secrets.toml
```

---

## 화면 구성

| 탭 | 설명 |
|---|---|
| 홈 | 앱 소개 및 시작 |
| 진단 | 업종 / 진행상황 / 중단여부 / 광고문구 입력 → 리스크 진단 |
| 질문 | 지식그래프 기반 자유 QnA (진단 결과 맥락 연동 가능) |
| 이력 | Supabase에 저장된 진단 이력 조회 |

---

## 데이터 구조 참고

두 JSON 파일은 구조가 다르므로 각각 전용 함수로만 접근합니다.

| 파일 | nodes 구조 | chunks |
|---|---|---|
| `law_graph_full.json` | `dict of dicts` | 있음 (RAG용 원문) |
| `knowledge_graph.json` | `dict of lists` | 없음 (사건/처분/판례 구조) |
