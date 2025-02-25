
import os
import json
import speech_recognition as sr
import pyttsx3
import numpy as np
import sounddevice as sd
import wave
from tempfile import NamedTemporaryFile
from services.ai_service import analyze_spending_patterns, generate_saving_tip, analyze_expense_cause

class VoiceAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 0.9)

    def listen(self, audio_data):
        """Convert audio data to text using speech recognition"""
        try:
            # Convert the audio data to WAV format
            with NamedTemporaryFile(suffix=".wav", delete=True) as temp_file:
                with wave.open(temp_file.name, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(44100)
                    wf.writeframes(audio_data.tobytes())

                # Use speech recognition on the WAV file
                with sr.AudioFile(temp_file.name) as source:
                    audio = self.recognizer.record(source)
                    text = self.recognizer.recognize_google(audio)
                    return text.lower()
        except sr.UnknownValueError:
            return "Sorry, I couldn't understand what you said."
        except sr.RequestError:
            return "Sorry, there was an error with the speech recognition service."
        except Exception as e:
            return f"Error processing audio: {str(e)}"

    def generate_response(self, text, user):
        if text.startswith("Sorry") or text.startswith("Error"):
            return text
            
        if any(word in text for word in ['spending', 'expenses', 'budget']):
            response = analyze_spending_patterns(user)
        elif any(word in text for word in ['save', 'saving', 'savings']):
            response = generate_saving_tip()
        elif any(word in text for word in ['why', 'how come', 'reason']):
            response = analyze_expense_cause(user)
        else:
            response = "I can help you with your spending analysis, saving tips, and budget management. What would you like to know?"

        return self._clean_response(response)

    def _clean_response(self, text):
        text = text.replace('**', '')
        emoji_map = {
            '💰': 'money',
            '📊': 'chart',
            '💡': 'tip',
            '🍽️': 'food',
            '🚌': 'transport',
            '📚': 'education',
            '🎮': 'entertainment',
            '🏠': 'home'
        }
        for emoji, description in emoji_map.items():
            text = text.replace(emoji, description)
        return text

    def speak(self, text):
        try:
            with NamedTemporaryFile(suffix=".wav", delete=True) as temp_file:
                self.engine.save_to_file(text, temp_file.name)
                self.engine.runAndWait()

                with wave.open(temp_file.name, 'rb') as wf:
                    audio_data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
                    audio_data = audio_data.astype(np.float32) / 32767.0

                    return {
                        'audio': audio_data.tolist(),
                        'sample_rate': wf.getframerate(),
                        'duration': len(audio_data) / wf.getframerate()
                    }
        except Exception as e:
            return {'error': str(e)}

voice_assistant = VoiceAssistant()
