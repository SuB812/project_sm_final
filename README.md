# Ad Doctor

온라인 마케팅 리스크 진단 도우미. 광고 문구의 표시광고법 위반 가능성을 AI로 진단하고, 공정거래위원회 의결서 사례 및 QA 지식그래프를 기반으로 유사 판례와 맞춤형 답변을 제시합니다.

---

## 기술 스택

- **Frontend / App**: Streamlit
- **LLM**: OpenAI GPT-4o-mini
- **지식 기반**:
  - `law_graph_full.json` — 법령 원문 그래프 (심사지침 / 법률 / 시행령 등)
  - `knowledge_graph.json` — 공정위 의결서 사례 그래프 (사건 / 위반행위 / 처분 / 법리판단)
  - `QA데이터셋__0521_.xlsx` — 페르소나 기반 QA 지식그래프 (532개 QA, 3개 페르소나)
- **DB**: Supabase (진단 이력 저장)
- **배포**: Streamlit Cloud

---

## 파일 구조

```
├── app.py
├── requirements.txt
├── README.md
├── law_graph_full.json          ← 법령 원문 그래프
├── knowledge_graph.json         ← 의결서 사례 그래프
├── QA데이터셋__0521_.xlsx       ← QA 지식그래프 (페르소나 기반)
└── .streamlit/
    └── secrets.toml             ← API 키 (로컬 전용, git에 올리지 말 것)
```

---

## 데이터 구조 참고

세 개의 지식 소스가 역할을 분담하여 동작합니다.

| 파일 | 구조 | 역할 |
|---|---|---|
| `law_graph_full.json` | `dict of dicts` + chunks | 법령 원문 RAG 검색 (대전제) |
| `knowledge_graph.json` | `dict of lists` (chunks 없음) | 유사 의결서 사례 검색 (소전제) |
| `QA데이터셋__0521_.xlsx` | 532행 × 15컬럼 | 페르소나 감지 + Few-shot 답변 스타일 |

### QA 지식그래프 구성

QA 데이터셋은 단순 FAQ가 아닌 **페르소나 기반 지식그래프**로 재구성되어 사용됩니다.

- **페르소나 3종**: 소상공인 / 행정모니터링 담당자 / 기업 컴플라이언스 담당자
- **질문유형 3종**: 실무적용 / 법령해석 / 리스크점검
- **난이도 3단계**: 기초 / 중급 / 고급

사용자 질문이 들어오면 다음 순서로 동작합니다.

```
사용자 질문
    ↓
페르소나 자동 감지 (키워드 패턴 분석)
    ↓
유사 QA 추출 (키워드 매칭 + 동일 페르소나 가중치)
    ↓
법령 원문 + 의결서 사례 + QA 예시를 통합하여 프롬프트 구성
    ↓
GPT-4o-mini → 페르소나 맞춤 답변 생성
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

### 3. 파일 배치

아래 파일을 `app.py`와 같은 루트 디렉토리에 넣습니다.

```
law_graph_full.json
knowledge_graph.json
QA데이터셋__0521_.xlsx
```

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

1. GitHub 레포지토리에 아래 파일을 push합니다.
   - `app.py`, `requirements.txt`, `README.md`
   - `law_graph_full.json`, `knowledge_graph.json`, `QA데이터셋__0521_.xlsx`

2. [Streamlit Cloud](https://streamlit.io/cloud) → New app → 레포 연결

3. **Secrets** 탭에서 아래 내용을 입력합니다.

```toml
OPENAI_API_KEY = "sk-..."
SUPABASE_URL   = "https://xxxx.supabase.co"
SUPABASE_KEY   = "eyJ..."
```

> **주의**: `.streamlit/secrets.toml`은 절대 git에 커밋하지 마세요.

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
| 질문 | 법령 + 의결서 + QA 지식그래프 기반 자유 QnA (진단 결과 맥락 연동) |
| 이력 | Supabase에 저장된 진단 이력 조회 |
