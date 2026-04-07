from vosk import Model, KaldiRecognizer, SetLogLevel
import wave
import json

SetLogLevel(-1)

model = Model(lang="en-us")

def parse_voice(voice_file):

    rec = KaldiRecognizer(model,voice_file.getframerate())

    frame_batch_size = 4000

    data = voice_file.readframes(frame_batch_size)

    while len(data) > 0:
        rec.AcceptWaveform(data)
        data = voice_file.readframes(frame_batch_size)

    result = json.loads(rec.FinalResult())

    return result["text"]


if __name__ == "__main__":
    with wave.open("tests/test_data/waveform_test.wav", "rb") as wav_file:
        print(parse_voice(wav_file))

