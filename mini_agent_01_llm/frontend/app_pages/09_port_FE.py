import base64
import binascii

import streamlit as st

from core.api_client import BackendAPIError, upload_speech_translation


LANGUAGES = {
    "en": "English (영어)",
    "ko": "Korean (한국어)",
    "ja": "Japanese (일본어)",
    "zh": "Chinese (중국어)",
}
SOURCE_LANGUAGES = {"auto": "자동 감지", **LANGUAGES}
VOICES = ["coral", "marin", "cedar", "alloy", "nova"]


st.title("1-7. 브라우저 음성 번역")
st.caption("마이크 음성을 텍스트로 인식하고 번역한 뒤 합성 음성으로 들려줍니다.")

source_language = st.selectbox(
    "말할 언어",
    list(SOURCE_LANGUAGES),
    format_func=SOURCE_LANGUAGES.get,
)
target_language = st.selectbox(
    "번역할 언어",
    list(LANGUAGES),
    format_func=LANGUAGES.get,
)
voice = st.selectbox("합성 음성", VOICES)

recorded_audio = st.audio_input(
    "마이크 버튼을 눌러 음성을 녹음하세요.",
    sample_rate=16000,
    help="브라우저에서 마이크 권한을 허용해야 합니다.",
)

if recorded_audio is None:
    st.info("녹음 대기 중입니다. 마이크 권한을 허용하고 음성을 녹음해 주세요.")
else:
    st.success("녹음이 준비되었습니다. 아래에서 원본 음성을 확인할 수 있습니다.")
    st.audio(recorded_audio.getvalue(), format="audio/wav")

if st.button(
    "음성 인식·번역·음성 생성",
    type="primary",
    disabled=recorded_audio is None,
    use_container_width=True,
):
    st.session_state.pop("speech_translation_result", None)
    try:
        with st.spinner("음성을 인식하고 번역 음성을 생성하고 있습니다."):
            result = upload_speech_translation(
                recorded_audio.name or "recording.wav",
                recorded_audio.getvalue(),
                recorded_audio.type or "audio/wav",
                target_language,
                source_language,
                voice,
            )
        st.session_state["speech_translation_result"] = result
    except BackendAPIError as error:
        st.error(str(error))

result = st.session_state.get("speech_translation_result")
if result:
    st.divider()
    st.subheader("원본 음성 인식 결과")
    st.write(result["original_text"])

    st.subheader(f"번역 결과 · {LANGUAGES.get(result['target_language'], result['target_language'])}")
    st.write(result["translated_text"])

    st.subheader("번역 음성")
    try:
        audio = base64.b64decode(result["audio_base64"], validate=True)
        st.warning("아래 음성은 AI가 생성한 합성 음성입니다.")
        st.audio(audio, format=result.get("audio_mime_type", "audio/mpeg"))
    except (KeyError, ValueError, binascii.Error):
        st.error("Backend가 반환한 음성 데이터를 재생할 수 없습니다.")

st.caption(
    "녹음 데이터는 Backend 메모리에서 처리되며 이 기능은 서버에 음성 파일을 저장하지 않습니다."
)
