from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile

from app.config import settings
from app.schemas import (
    SourceLanguage,
    SpeechTranslationResult,
    TargetLanguage,
    TtsRequest,
    VoiceName,
)
from app.services.media_service import analyze_image, create_speech, translate_speech


media_router = APIRouter(prefix="/api/media", tags=["Multimodal"])


@media_router.post("/image-analysis")
async def image_analysis(
    image: UploadFile = File(...),
    question: str = Form("여행자가 알아야 할 정보와 주의점을 알려주세요."),
) -> dict:
    try:
        result = analyze_image(image.content_type or "", await image.read(), question)
        return result.model_dump()
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"이미지 분석 실패: {error}") from error


@media_router.post("/tts")
def text_to_speech(payload: TtsRequest) -> Response:
    try:
        audio = create_speech(payload.text, payload.voice, payload.instructions)
        return Response(
            content=audio,
            media_type="audio/mpeg",
            headers={"X-Synthetic-Voice": "true"},
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"TTS 생성 실패: {error}") from error


@media_router.post(
    "/speech-translation",
    response_model=SpeechTranslationResult,
)
async def speech_translation(
    audio: UploadFile = File(...),
    target_language: TargetLanguage = Form(...),
    source_language: SourceLanguage = Form("auto"),
    voice: VoiceName | None = Form(None),
) -> SpeechTranslationResult:
    try:
        content = await audio.read(settings.max_audio_size_mb * 1024 * 1024 + 1)
        return translate_speech(
            audio.content_type,
            content,
            target_language,
            source_language,
            voice,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"음성 번역 실패: {error}") from error
