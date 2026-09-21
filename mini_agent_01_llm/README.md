# Mini Agent 01 · LLM 판단에서 서비스 연결까지

`01_llm-to-agent`의 단위 Python 예제를 FastAPI Endpoint와 Streamlit 메뉴로
하나씩 연결합니다. 첫 단계에서는 로그인과 Agent Workflow를 넣지 않습니다.

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

## Docker Compose 실행

```powershell
cd C:\Port_수업자료\mini\mini_agent\mini_agent_01_llm
docker compose --env-file .env config --quiet
docker compose --env-file .env up -d --build
docker compose ps
```

- Frontend: `http://127.0.0.1:8501`
- Backend Health: `http://127.0.0.1:8000/health`
- Backend API 문서: `http://127.0.0.1:8000/docs`

종료할 때는 Data Volume을 사용하지 않으므로 다음 명령으로 Container만 내립니다.

```powershell
docker compose down
```

## `wk01` CI/CD

Workflow는 `.github/workflows/mini-agent-01-llm-cicd.yml`에 있습니다.

```text
Push/Pull Request
→ Backend Test
→ Compose 문법 검증
→ Backend·Frontend Image Build
→ main Push 또는 deploy=true 수동 실행
→ wk01 Environment 승인
→ EC2 Source 복사·Compose 재실행
→ Backend·Frontend Health 확인
```

GitHub Repository의 `Settings → Environments`에서 `wk01`을 만들고 다음
Environment Secret을 등록합니다.

| Secret | 내용 |
| --- | --- |
| `AWS_HOST` | EC2 Public IPv4 또는 Public DNS |
| `AWS_USER` | Ubuntu는 `ubuntu`, Amazon Linux는 `ec2-user` |
| `AWS_SSH_PRIVATE_KEY` | EC2 배포용 Private Key 전체 |
| `AWS_SSH_KNOWN_HOSTS` | 지문을 확인한 EC2 known_hosts 항목 |

EC2에서 최초 한 번 배포 폴더와 `.env`를 준비합니다.

```bash
mkdir -p ~/mini-agent-01-llm
chmod 700 ~/mini-agent-01-llm
```

`.env`는 `~/mini-agent-01-llm/.env`에 두고 `chmod 600` 권한을 적용합니다.
Workflow는 Secret 파일을 GitHub에서 전송하지 않고 EC2에 있는 `.env`를 유지합니다.

배포 후에는 EC2에서 다음을 확인합니다.

```bash
cd ~/mini-agent-01-llm
docker compose ps
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8501/_stcore/health
```

Frontend의 사이드바에 `wk01 CI/CD 배포`가 표시되면 수정 내용까지
서버에 반영된 것입니다. 실습 후에는 EC2 Security Group의 SSH `22`를
`0.0.0.0/0`으로 유지하지 말고 관리자 IP로 다시 제한합니다.
