from transformers import VitsModel, AutoTokenizer
import torch
from io import BytesIO
import numpy as np
import wave

# NOTE: WHY IS FLASK CLOSING THIS>!?!?!?!?
class AutoBytesIO(BytesIO):
    def close(self):
        pass

model = VitsModel.from_pretrained("facebook/mms-tts-fin")
tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-fin")

def generate_audio(text):
    text = text.replace('c', 'k').replace('w', 'v') # FOR FINNISH. TODO: generalize to any lang

    inputs = tokenizer(text, return_tensors="pt")

    # print('AUDIO GENERATING')

    with torch.no_grad():
        output = model(**inputs).waveform[0].numpy()

    # print('AUDIO GENERATED')

    output = (output*32767.0).astype(np.int16)

    buff = AutoBytesIO()
    wav = wave.open(buff, 'w')
    wav.setparams((1, 2, model.config.sampling_rate, output.shape[-1], 'NONE', 'not compressed'))
    wav.writeframes(output.tobytes())
    # buff.seek(0)

    return buff