# Mini Agent 03 Docker·GitHub Actions 실습 가이드

## 1. 실습 목표

이 실습은 `mini_agent_03_tool` 프로젝트의 Frontend와 Backend를 Docker Image로 만들고,
GitHub에 코드를 Push할 때마다 GitHub Actions가 다음 항목을 자동으로 검사하게 만드는 과정입니다.

```text
Backend Test
→ Compose 설정 검사
→ Backend·Frontend Docker Image Build
→ 모두 통과하면 GitHub Actions 성공
```

이번 단계는 CI(Continuous Integration) 실습입니다. AWS나 운영 서버에 배포하는 작업은 포함하지 않습니다.

## 2. 프로젝트 구조

`mini_agent` 폴더 전체를 GitHub 저장소 루트로 사용합니다.

```text
mini_agent/                              # GitHub 저장소 루트
├─ .github/
│  └─ workflows/
│     └─ mini-agent-03-ci.yml          # GitHub Actions Workflow
└─ mini_agent_03_tool/
   ├─ requirements.txt
   ├─ backend/
   ├─ frontend/
   └─ docker/
      ├─ guide.md                       # 현재 문서
      ├─ compose.yml                    # 두 Container 연결
      ├─ backend/
      │  └─ Dockerfile                  # FastAPI Image 제작
      └─ frontend/
         └─ Dockerfile                  # Streamlit Image 제작
```

`.github/workflows` Folder는 반드시 GitHub 저장소 루트에 있어야 합니다. 현재 Workflow는
`mini_agent` 기준으로 `mini_agent_03_tool/...` 경로를 사용합니다.

## 3. 각 파일의 역할

### Backend Dockerfile

`docker/backend/Dockerfile`은 Python 3.12 환경을 준비하고 FastAPI Backend를 Uvicorn으로 실행합니다.

```text
Python 3.12
→ requirements.txt 설치
→ backend/app 복사
→ uvicorn app.main:app 실행
```

### Frontend Dockerfile

`docker/frontend/Dockerfile`은 Frontend 전체를 복사하고 Streamlit을 `8501` Port로 실행합니다.

### Compose

`docker/compose.yml`은 Frontend와 Backend Container를 하나의 Docker Network로 연결합니다.

```text
Browser
  → Frontend: http://127.0.0.1:8501
  → Backend:  http://backend:8000
```

Frontend Container 내부에서는 `127.0.0.1` 대신 Compose Service 이름인 `backend`를 사용합니다.

```yaml
BACKEND_API_URL: http://backend:8000
```

## 4. 로컬 환경 준비

PowerShell에서 `mini_agent_03_tool` Folder로 이동합니다.

```powershell
cd "C:\Port_수업자료\mini\mini_agent\mini_agent_03_tool"
```

가상 환경이 없을 때만 생성합니다.

```powershell
python -m venv .venv
```

가상 환경을 활성화하고 패키지를 설치합니다.

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r .\requirements.txt
```

`pytest`는 이 프로젝트의 `requirements.txt`에 포함되어 있으므로 별도로 설치할 필요가 없습니다.

## 5. Backend Test

테스트가 `backend/app`을 Python Package로 찾을 수 있도록 `PYTHONPATH`를 설정합니다. CI에서는
실제 LLM과 날씨 API를 호출하지 않도록 Mock Mode를 사용합니다.

```powershell
$env:PYTHONPATH = "backend"
$env:LLM_PROVIDER = "mock"
$env:WEATHER_MODE = "mock"
python -m pytest .\backend\tests -q
```

정상 기준:

```text
22 passed
```

테스트는 `backend/tests`만 명시적으로 실행합니다. `learning_unit`은 교육용 예제로 보존하지만
이 CI Test 대상에는 포함하지 않습니다.

## 6. Compose 설정 검사와 Image Build

`compose.yml`의 YAML 문법, Build Context, Dockerfile 경로를 검사합니다.

```powershell
docker compose -f .\docker\compose.yml config --quiet
```

성공하면 보통 아무 메시지도 출력되지 않습니다.

Backend와 Frontend Image를 만듭니다.

```powershell
docker compose -f .\docker\compose.yml build
```

정상 기준:

```text
Image mini-agent-03-tool-backend Built
Image mini-agent-03-tool-frontend Built
```

## 7. Container 실행과 확인

Image Build가 성공한 다음 Container를 실행합니다.

```powershell
docker compose -f .\docker\compose.yml up -d
docker compose -f .\docker\compose.yml ps
```

확인 주소:

- Streamlit: `http://127.0.0.1:8501`
- Backend Health: `http://127.0.0.1:8000/health`
- FastAPI Swagger: `http://127.0.0.1:8000/docs`

Log를 확인할 때:

```powershell
docker compose -f .\docker\compose.yml logs --tail=100 backend
docker compose -f .\docker\compose.yml logs --tail=100 frontend
```

Container를 종료할 때:

```powershell
docker compose -f .\docker\compose.yml down
```

## 8. GitHub에 올리기 전 보안 확인

이 프로젝트의 `.env`에는 API Key가 있을 수 있으므로 GitHub에 Commit하면 안 됩니다. Git에 파일을
추가하기 전에 저장소 루트의 `.gitignore`에 최소한 다음 항목이 있는지 확인합니다.

```gitignore
**/.env
**/.venv/
**/__pycache__/
**/*.pyc
**/.pytest_cache/
```

실제로 Stage된 파일을 반드시 확인합니다.

```powershell
git status --short
```

`.env`, `.venv`, `__pycache__`가 목록에 나타나면 Commit하지 말고 `.gitignore`를 먼저 수정합니다.

## 9. GitHub 저장소와 Push

PowerShell에서 GitHub 저장소 루트로 이동합니다.

```powershell
cd "C:\Port_수업자료\mini\mini_agent"
```

저장소 루트가 맞는지 확인합니다.

```powershell
git rev-parse --show-toplevel
```

정상적인 출력:

```text
C:/Port_수업자료/mini/mini_agent
```

아직 Git 저장소를 만들지 않았다면 이 폴더에서 `git init`을 실행합니다. GitHub에서 빈 저장소를
만든 후에는 해당 저장소에 표시된 원격 URL을 사용합니다.

```powershell
git init
git branch -M main
git remote add origin <GITHUB_REPOSITORY_URL>
```

`<GITHUB_REPOSITORY_URL>`은 실제 GitHub 저장소 URL로 바꾸어야 합니다.

안전하게 `.gitignore`와 `git status --short`를 확인한 뒤 Commit·Push합니다.

```powershell
git add .
git status --short
git commit -m "Add Mini Agent 03 Docker CI"
git push -u origin main
```

## 10. GitHub Actions가 실행되는 시점

`.github/workflows/mini-agent-03-ci.yml`은 다음 이벤트에서 실행됩니다.

- `mini_agent_03_tool/**` 파일을 변경하여 Push한 경우
- Pull Request에 `mini_agent_03_tool/**` 변경이 포함된 경우
- Workflow 파일 자체를 변경한 경우
- GitHub Actions 화면에서 `Run workflow` 버튼을 누른 경우

다른 Mini Agent Folder만 변경한 Push에서는 불필요한 Mini Agent 03 CI가 실행되지 않습니다.

## 11. GitHub 사이트에서 성공 여부 확인

1. GitHub 사이트에서 해당 저장소를 엽니다.
2. 상단의 **Actions** Tab을 선택합니다.
3. 왼쪽 Workflow 목록에서 **Mini Agent 03 CI**를 선택합니다.
4. 가장 최근의 Workflow Run을 선택합니다.
5. **test-and-build** Job을 열어 각 Step을 확인합니다.

다음 Step이 모두 초록색 Check로 표시되면 성공입니다.

```text
Checkout
Set up Python
Install dependencies
Test backend
Validate Compose
Build Docker images
```

### 수동 실행

Actions Tab에서 **Mini Agent 03 CI**를 선택한 후 **Run workflow** 버튼을 누르면 코드를 수정하지
않고도 Workflow를 다시 실행할 수 있습니다.

## 12. GitHub Actions 실패 확인

Workflow가 실패하면 가장 먼저 빨간색으로 표시된 Step을 엽니다. Log의 마지막 줄만 보지 말고
처음 나타난 오류를 확인합니다.

| 실패 Step | 먼저 확인할 내용 |
| --- | --- |
| Install dependencies | `requirements.txt` 경로와 Package 이름 |
| Test backend | 첫 Assertion 실패, Import 경로, Mock 설정 |
| Validate Compose | YAML 들여쓰기, Dockerfile 경로, 환경 변수 |
| Build Docker images | `COPY` 경로, Base Image, Package 설치 오류 |

오류를 수정하고 새 Commit을 Push하면 새 Workflow Run이 자동으로 생성됩니다.

## 13. CI에서 실제 API Key를 사용하지 않는 이유

Workflow는 다음 환경 변수를 사용합니다.

```yaml
LLM_PROVIDER: mock
WEATHER_MODE: mock
```

따라서 OpenAI·Gemini·Ollama나 실제 날씨 API에 의존하지 않고 Backend 계약과 Docker Build 가능 여부만
안전하게 검사합니다. Pull Request 검사에 API Key를 넘기지 않습니다.

## 14. 완료 체크

```text
[ ] mini_agent Folder가 GitHub 저장소 루트이다.
[ ] .env·.venv·__pycache__가 Commit되지 않았다.
[ ] Backend Test 22개가 통과했다.
[ ] docker compose config --quiet가 통과했다.
[ ] Backend·Frontend Docker Image Build가 성공했다.
[ ] GitHub Actions의 모든 Step이 초록색이다.
[ ] 실패한 Step의 첫 오류를 찾을 수 있다.
```
