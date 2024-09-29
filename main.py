import asyncio
import sounddevice as sd
import wavio as wv
import speech_recognition as sr
import os
import aiohttp
import re
import json
import tkinter as tk
from dotenv import load_dotenv
from async_tkinter_loop import async_handler, async_mainloop

load_dotenv()

chat_url = os.getenv("CHAT_URL")
chat_model = os.getenv("CHAT_MODEL")

message_history = [
    {
        "role": "system",
        "content": "You are the teacher, ask me questions and correct mistakes in my responses"
    }
]

class App:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("AI exam helper")
        self.window.geometry("600x400")
        
    def create_ui(self):
        self.label = tk.Label(self.window, text="AI exam helper")
        self.record_btn = tk.Button(self.window, text="Record your question/answer", command=async_handler(self.record_file))
        self.ask_check_button = tk.Button(self.window, text="Ask/check button", command=async_handler(self.ask_check))
        
        self.label.pack()
        self.record_btn.pack()
        self.ask_check_button.pack()

    def parse_response_line(self, line):
        parsed_line = re.findall(r'\{.*\}',line)[0]
        msg = json.loads(parsed_line[parsed_line.index(":{") + 1: parsed_line.index("},") + 1].replace("\\",""))["content"]
        return(msg)

    async def record_file(self):
        freq = 44200
        duration = 5

        recording = sd.rec(int(duration * freq), 
                        samplerate=freq, channels=2)

        await asyncio.sleep(duration)

        wv.write("recording.wav", recording, freq, sampwidth=2)
        tk.messagebox.askquestion("Recording has finished")

    def convert_speech_to_text(self, path):
        r = sr.Recognizer()
        text = None
        with sr.AudioFile(path) as wav_data:
            audio_data = r.record(wav_data)
            text = r.recognize_google(audio_data)
        
        return text

    async def ask_questions(self, question):
        message_history.extend([
            {
                "role": "user",
                "content": question
            }
        ])
        
        payload = {
            "model": chat_model,
            "messages": message_history
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(chat_url, json=payload) as resp:
                msg = ""
                async for line in resp.content:
                    msg += (self.parse_response_line(str(line)))
                    print(msg)

                message_history.extend([
                    {
                        "role": "assistant",
                        "content": msg
                    }
                ])
                
    async def ask_check(self):
        txt = self.convert_speech_to_text("recording.wav")
        await self.ask_questions(txt)
        self.result_val =  message_history[-1]["content"]

    def main(self):
        self.create_ui()
        async_mainloop(self.window)

if __name__ == "__main__":
    app = App()
    asyncio.run(app.main())