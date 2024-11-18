from gtts import gTTS
import os

class Text2Audio:
    def __init__(self):
        self.tts = None
        self.idx = 0

    def gen_audio(self, text):
        self.tts = gTTS(text, lang='yue')
        self.idx += 1
        
    def save_audio(self, path):
        assert self.tts is not None, 'self.tts is None. Run self.get_audio() first.'
        self.tts.save(path)


if __name__ == '__main__':
    print("Running text2audio.py")

    text = "美國大選進入衝刺階段, 比特幣暴升7%, 站上7.3萬美元上方, 期權定價顯示明日波動幅度達8%"
    sentences = text.split(', ')

    text_2_audio = Text2Audio()

    for i in range(len(sentences)-2):
        sentence =', '.join(sentences[i:i+3])
        text_2_audio.gen_audio(sentence)
        text_2_audio.save_audio(f'outputs/{i}_{sentence}.mp3')
