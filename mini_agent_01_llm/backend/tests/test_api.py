import base64
from dataclasses import replace

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.schemas import SpeechTranslationResult, TravelImageAnalysis
from app.services.media_service import translate_speech, validate_audio


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["stage"] == "mini_agent_01_llm"


def test_provider_list_does_not_expose_keys() -> None:
    response = client.get("/api/providers")
    assert response.status_code == 200
    body = response.json()
    assert {item["provider"] for item in body["providers"]} == {
        "mock",
        "openai",
        "gemini",
        "ollama",
    }
    assert "api_key" not in response.text.lower()


def test_concept_compare_shows_rule_and_semantic_difference() -> None:
    response = client.post(
        "/api/concepts/compare",
        json={"message": "내일 비가 올까요?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["workflow"]["route"] == "general"
    assert body["semantic_router"]["route"] == "weather"


def test_travel_classifier_asks_for_missing_destination() -> None:
    response = client.post(
        "/api/travel/classify",
        json={"message": "여행을 준비해 줘."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "travel_plan"
    assert body["next_action"] == "ask_user"
    assert "destination" in body["missing_information"]


def test_low_confidence_requests_clarification() -> None:
    response = client.post(
        "/api/travel/classify",
        json={"message": "도와주세요."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "needs_clarification"
    assert body["next_action"] == "ask_user"


def test_mock_provider_generate() -> None:
    response = client.post(
        "/api/generate",
        json={"provider": "mock", "message": "부산 여행"},
    )
    assert response.status_code == 200
    assert response.json()["provider"] == "mock"


def test_provider_compare_preserves_each_result() -> None:
    response = client.post(
        "/api/providers/compare",
        json={"providers": ["mock"], "message": "부산 여행"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["request_count"] == 1
    assert body["results"][0]["status"] == "success"


def test_missing_openai_key_is_explicit(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.providers.settings",
        replace(settings, openai_api_key=""),
    )
    response = client.post(
        "/api/generate",
        json={"provider": "openai", "message": "부산 여행을 추천해 주세요."},
    )
    assert response.status_code == 422
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_image_analysis_returns_structured_result(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.routers.media_router.analyze_image",
        lambda *_: TravelImageAnalysis(
            scene_type="landmark",
            summary="부산의 해변입니다.",
            travel_tips=["운영 시간을 확인하세요."],
        ),
    )
    response = client.post(
        "/api/media/image-analysis",
        files={"image": ("travel.png", b"fake", "image/png")},
    )
    assert response.status_code == 200
    assert response.json()["scene_type"] == "landmark"


def test_tts_marks_synthetic_audio(monkeypatch) -> None:
    monkeypatch.setattr("app.routers.media_router.create_speech", lambda *_: b"mp3")
    response = client.post("/api/media/tts", json={"text": "안녕하세요.", "voice": "coral"})
    assert response.status_code == 200
    assert response.headers["x-synthetic-voice"] == "true"


def test_speech_translation_returns_text_and_audio(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.routers.media_router.translate_speech",
        lambda *_: SpeechTranslationResult(
            original_text="안녕하세요.",
            translated_text="Hello.",
            target_language="en",
            audio_base64=base64.b64encode(b"mp3").decode("ascii"),
        ),
    )
    response = client.post(
        "/api/media/speech-translation",
        files={"audio": ("recording.wav", b"fake", "audio/wav")},
        data={
            "target_language": "en",
            "source_language": "ko",
            "voice": "coral",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["original_text"] == "안녕하세요."
    assert body["translated_text"] == "Hello."
    assert base64.b64decode(body["audio_base64"]) == b"mp3"
    assert body["synthetic_voice"] is True


def test_speech_translation_rejects_unsupported_language() -> None:
    response = client.post(
        "/api/media/speech-translation",
        files={"audio": ("recording.wav", b"fake", "audio/wav")},
        data={"target_language": "fr"},
    )
    assert response.status_code == 422


def test_audio_validation_accepts_browser_wav() -> None:
    wav = b"RIFF" + (37).to_bytes(4, "little") + b"WAVE" + (b"\x00" * 33)
    validate_audio("audio/wav", wav)


def test_audio_validation_rejects_fake_wav() -> None:
    try:
        validate_audio("audio/wav", b"not a wav file")
    except ValueError as error:
        assert "WAV 형식" in str(error)
    else:
        raise AssertionError("가짜 WAV 파일이 허용되었습니다.")


def test_translate_speech_combines_all_steps(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.media_service.transcribe_audio",
        lambda *_: "안녕하세요.",
    )
    monkeypatch.setattr(
        "app.services.media_service.translate_text",
        lambda *_: "Hello.",
    )
    monkeypatch.setattr(
        "app.services.media_service.create_speech",
        lambda *_: b"mp3",
    )
    wav = b"RIFF" + (37).to_bytes(4, "little") + b"WAVE" + (b"\x00" * 33)

    result = translate_speech("audio/wav", wav, "en", "ko", "coral")

    assert result.original_text == "안녕하세요."
    assert result.translated_text == "Hello."
    assert base64.b64decode(result.audio_base64) == b"mp3"
