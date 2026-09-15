# Mini Agent 01 Docker 직접 실습 가이드

`mini_agent_01_llm`을 Backend와 Frontend 두 Container로 실행하고, 생성한
Image를 Docker Hub에 올리는 실습입니다. Database와 Redis는 사용하지 않습니다.

## 1. Docker Desktop 확인

Docker Desktop을 먼저 실행한 뒤 PowerShell에서 확인합니다.

```powershell
docker version
docker compose version
```

기존 Container를 내리고 처음부터 다시 실습하려면 다음을 실행합니다.

```powershell
cd C:\Port_수업자료\mini\mini_agent\mini_agent_01_docker
docker compose down
```

## 2. 환경 설정 파일 만들기

```powershell
Copy-Item .env.example .env
Copy-Item .\backend\.env.example .\backend\.env
Copy-Item .\frontend\.env.example .\frontend\.env
```

각 환경설정 파일의 역할은 다음과 같습니다.

| 파일 | 역할 |
| --- | --- |
| `.env` | Docker Hub 사용자명과 Image Version |
| `backend/.env` | LLM API Key, Model, Backend 설정 |
| `frontend/.env` | Backend API 주소 |

처음에는 `backend/.env`에서 API Key 없이 Mock Provider로 실습할 수 있습니다.

```ini
LLM_PROVIDER=mock
```

OpenAI를 사용하려면 실제 `backend/.env`에 다음과 같이 설정합니다.

```ini
LLM_PROVIDER=openai
OPENAI_API_KEY=본인의_API_KEY
```

> 실제 `backend/.env`에는 API Key가 들어갈 수 있으므로 Docker Image, Docker Hub,
> Git 저장소에 포함하지 않습니다.

## 3. Dockerfile 이해하기

### Backend

`backend/Dockerfile`은 다음 작업을 합니다.

1. Python 3.12 Image를 사용합니다.
2. Backend Library를 설치합니다.
3. `backend/app` 코드를 Image에 복사합니다.
4. FastAPI를 8000번 Port로 실행합니다.

핵심 실행 명령:

```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend

`frontend/Dockerfile`은 Streamlit을 8501번 Port로 실행합니다.

```dockerfile
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
```

## 4. Compose 구성 확인

`compose.yml`에는 Backend와 Frontend 두 Service만 있습니다.

```text
Frontend :8501
    ↓
Backend  :8000
```

Frontend Container가 Backend Container를 호출할 때는 `localhost`가 아니라
Compose Service 이름을 사용합니다.

```yaml
BACKEND_API_URL: http://backend:8000
```

Database와 Redis는 사용하지 않으므로 Compose에 추가하지 않습니다.

Compose 파일의 문법을 먼저 확인합니다.

```powershell
docker compose config --quiet
```

아무 메시지도 나오지 않으면 정상입니다.

## 5. Image Build 및 Container 실행

Backend와 Frontend Image를 만듭니다.

```powershell
docker compose build backend frontend
```

Container를 백그라운드에서 실행하고 상태를 확인합니다.

```powershell
docker compose up -d
docker compose ps
```

다음과 같이 나오면 정상입니다.

```text
backend    Up (healthy)
frontend   Up
```

문제가 있다면 Service별 로그를 확인합니다.

```powershell
docker compose logs backend
docker compose logs frontend
```

Browser에서 다음 주소를 확인합니다.

| 확인 대상 | 주소 |
| --- | --- |
| Streamlit Frontend | `http://127.0.0.1:8501` |
| FastAPI 문서 | `http://127.0.0.1:8000/docs` |
| Backend 상태 | `http://127.0.0.1:8000/health` |

코드나 환경 설정을 수정했다면 Image를 다시 Build하고 Container를 새로 만듭니다.

```powershell
docker compose up -d --build --force-recreate backend frontend
```

## 6. Docker Hub에 Image 올리기

최상위 `.env`에는 Docker Hub 사용자명과 Image Version만 설정합니다.

```ini
DOCKER_HUB_USERNAME=본인의_도커허브_아이디
IMAGE_TAG=1.0.0
```

Docker Hub에 로그인하고 사용자명이 반영된 Image를 다시 Build합니다.

```powershell
docker login
docker compose build backend frontend
docker image ls
```

Backend와 Frontend Image를 Docker Hub에 올립니다.

```powershell
docker compose push backend frontend
```

Docker Hub에서 다음 두 저장소가 생성됐는지 확인합니다.

```text
본인아이디/mini-agent-01-backend
본인아이디/mini-agent-01-frontend
```

## 7. Docker Hub Image로 실행하기

다른 PC에서는 `compose.release.yml`을 사용합니다. 세 개의 `.env.example`을 각각
복사한 뒤 최상위 파일에는 Docker Hub 사용자명, Backend 파일에는 필요한 API Key를
입력합니다.

```powershell
Copy-Item .env.example .env
Copy-Item .\backend\.env.example .\backend\.env
Copy-Item .\frontend\.env.example .\frontend\.env
docker compose -f .\compose.release.yml pull
docker compose -f .\compose.release.yml up -d
docker compose -f .\compose.release.yml ps
```

## 8. 종료

기본 Compose Container를 종료합니다.

```powershell
docker compose down
```

배포용 Compose를 사용했다면 다음과 같이 종료합니다.

```powershell
docker compose -f .\compose.release.yml down
```

## 핵심 주의사항

- 실제 `.env` 파일들과 API Key는 Docker Hub나 Git에 올리지 않습니다.
- Database와 Redis Service는 추가하지 않습니다.
- Frontend에서 Backend로의 주소는 `http://backend:8000`입니다.
- Host에서 실행 중인 Ollama는 Container 안에서
  `http://host.docker.internal:11434`로 접근합니다.
