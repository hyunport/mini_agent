# Mini Agent 01 · Docker Compose 배포

`01_llm-to-agent`의 단위 Python 예제를 FastAPI Endpoint와 Streamlit 메뉴로
하나씩 연결합니다. 첫 단계에서는 로그인과 Agent Workflow를 넣지 않습니다.

이 폴더는 `mini_agent_01_llm`을 Backend와 Frontend 두 Container로 실행하는
Docker 실습용입니다. PostgreSQL과 Redis는 사용하지 않습니다.

## Docker Compose 실행

```powershell
cd C:\Port_수업자료\mini\mini_agent\mini_agent_01_docker
Copy-Item .env.example .env
Copy-Item .\backend\.env.example .\backend\.env
Copy-Item .\frontend\.env.example .\frontend\.env
docker compose config --quiet
docker compose up --build -d
docker compose ps
```

OpenAI나 Gemini를 사용하려면 실제 `backend/.env`에 API Key를 설정합니다. Frontend의
Backend 주소는 `frontend/.env`에서 관리합니다. 호스트에서
실행 중인 Ollama는 Container 안에서 `host.docker.internal:11434`로 접근합니다.

| 확인 대상 | 주소 |
| --- | --- |
| Streamlit | `http://127.0.0.1:8501` |
| FastAPI 문서 | `http://127.0.0.1:8000/docs` |
| Backend 상태 | `http://127.0.0.1:8000/health` |

## Docker Hub 업로드

최상위 `.env`의 `DOCKER_HUB_USERNAME`을 Docker Hub 사용자명으로 설정한 뒤 실행합니다.
이 파일은 Compose Image 이름과 Version만 관리하며 LLM API Key를 보관하지 않습니다.

```powershell
docker login
docker compose build backend frontend
docker compose push backend frontend
```

다른 PC에서는 `.env.example`로 `.env`를 만든 뒤 Registry Image를 내려받아
실행합니다.

```powershell
docker compose -f .\compose.release.yml pull
docker compose -f .\compose.release.yml up -d
```

`backend/.env` 등 실제 `.env` 파일은 Docker Image나 Docker Hub에 포함하지 않습니다.

```text
Python 판단 함수
→ FastAPI
→ Streamlit 메뉴
→ Mock
→ Gemini
→ OpenAI GPT
→ Docker Ollama/Llama
→ 이미지 분석
→ 음성 생성
```

## 이번 단계에서 구현

- LLM·Workflow·Agent 비교
- 여행 요청 분류
- 낮은 confidence와 추가 질문
- Mock Provider로 연결 확인
- Gemini·GPT·Ollama/Llama 선택
- 동일 Prompt의 모델·응답 시간·실패 비교
- GPT 이미지 분석과 업로드 검증
- 여행 안내문 MP3 합성 음성 생성

## 아직 구현하지 않음

- Structured Output
- LangChain
- Tool
- RAG와 Memory
- Agent Workflow와 LangGraph
- 로그인

## 실행

```powershell
cd C:\mini_agent_st\mini_agent_01_llm
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

터미널 1:

```powershell
cd backend
uvicorn app.main:app --reload --port 8000
```

터미널 2:

```powershell
cd C:\mini_agent_st\mini_agent_01_llm
streamlit run .\frontend\app.py
```

Ollama는 `C:\mini_agent_st\infra`에서 먼저 실행하고 모델을 내려받아야 합니다.
Cloud Provider는 `.env`에 해당 API Key와 모델을 설정한 경우에만 호출합니다.

## 확인 순서

1. LLM·Workflow·Agent 메뉴에서 두 판단 결과를 비교합니다.
2. 여행 요청 분류에서 `confidence`와 추가 질문을 확인합니다.
3. 환경 상태에서 Backend와 Provider 설정을 확인합니다.
4. 기본 Provider인 Mock으로 Frontend·Backend 연결을 확인합니다.
5. 이전 과정에서 사용한 Gemini를 연결합니다.
6. GPT와 Ollama/Llama를 추가해 같은 질문을 비교합니다.
7. Ollama Container를 중지하고 실패가 비교 결과에 남는지 확인합니다.
8. 이미지 분석에서 업로드 형식과 구조화된 결과를 확인합니다.
9. 음성 생성에서 안내문을 MP3로 변환하고 합성 음성 고지를 확인합니다.

Provider 비교는 `Gemini → GPT → Ollama/Llama` 순서로 진행합니다. Cloud Provider는
호출량과 비용을 확인하고, Ollama는 Docker와 모델 준비 상태를 먼저 확인합니다.

이미지 분석과 음성 생성은 01 단원의 `1-5`, `1-6` 메뉴에서 진행합니다.
