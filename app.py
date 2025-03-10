import streamlit as st
from google.cloud import speech
from pydub import AudioSegment
import os
import tempfile
import json

# הגדרת הרשאות Google Cloud
st.title("🎙️ תמלול וחיתוך אודיו")

uploaded_auth_file = st.file_uploader("📂 העלה קובץ JSON של הרשאות Google", type=["json"])
if uploaded_auth_file:
    with open("service_account.json", "wb") as f:
        f.write(uploaded_auth_file.read())
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"
    st.success("✅ הרשאות נטענו בהצלחה!")

# העלאת קובץ אודיו
uploaded_file = st.file_uploader("📂 העלה קובץ MP3", type=["mp3"])

if uploaded_file:
    # שמירת הקובץ שהועלה זמנית
    temp_dir = tempfile.mkdtemp()
    input_audio_path = os.path.join(temp_dir, "uploaded.mp3")

    with open(input_audio_path, "wb") as f:
        f.write(uploaded_file.read())

    st.success("✅ קובץ הועלה בהצלחה!")

    # תמלול ההקלטה
    def transcribe_audio(file_path):
        client = speech.SpeechClient()
        with open(file_path, "rb") as audio_file:
            audio_content = audio_file.read()

        audio = speech.RecognitionAudio(content=audio_content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.MP3,
            sample_rate_hertz=16000,
            language_code="en-US",
            enable_word_time_offsets=True  # זמני תחילת מילים
        )

        response = client.recognize(config=config, audio=audio)

        transcribed_text = []
        for result in response.results:
            for word_info in result.alternatives[0].words:
                word = word_info.word
                start_time = word_info.start_time.total_seconds()
                transcribed_text.append(f"{start_time:.2f} sec: {word}")

        return "\n".join(transcribed_text)

    # הרצת התמלול
    with st.spinner("⏳ מתמלל את ההקלטה..."):
        transcript = transcribe_audio(input_audio_path)

    st.subheader("📜 תמלול עם זמנים:")
    st.text_area("📖 תמלול:", transcript, height=300)

    # בחירת טווח לחיתוך
    st.subheader("✂️ חיתוך קובץ אודיו:")
    start_time = st.number_input("⏳ זמן התחלה (שניות)", min_value=0.0, step=0.1)
    end_time = st.number_input("⏳ זמן סיום (שניות)", min_value=0.0, step=0.1)

    # חיתוך האודיו
    if st.button("✂️ חתוך ושמור"):
        if end_time > start_time:
            cut_audio_path = os.path.join(temp_dir, "trimmed_audio.mp3")

            audio = AudioSegment.from_mp3(input_audio_path)
            cut_audio = audio[start_time * 1000:end_time * 1000]
            cut_audio.export(cut_audio_path, format="mp3")

            st.success("✅ החיתוך בוצע בהצלחה!")

            # הצגת נגן אודיו
            st.audio(cut_audio_path, format="audio/mp3")

            # קישור להורדת הקובץ
            with open(cut_audio_path, "rb") as f:
                st.download_button(label="📥 הורד את האודיו החתוך", data=f, file_name="trimmed_audio.mp3", mime="audio/mp3")
        else:
            st.error("❌ זמן הסיום חייב להיות גדול מזמן ההתחלה!")
