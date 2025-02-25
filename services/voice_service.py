import os
import json
import speech_recognition as sr
import pyttsx3
import numpy as np
import sounddevice as sd
import wave
from tempfile import NamedTemporaryFile
from services.ai_service import analyze_spending_patterns, generate_saving_tip, analyze_expense_cause
import logging

class VoiceAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 0.9)

    def listen(self, audio_data):
        """Convert audio data to text using speech recognition"""
        try:
            # Convert numpy array to audio file
            with NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                with wave.open(temp_file.name, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(44100)
                    wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())

                # Use speech recognition
                with sr.AudioFile(temp_file.name) as source:
                    audio = self.recognizer.record(source)
                    text = self.recognizer.recognize_google(audio)

                # Clean up temp file
                os.unlink(temp_file.name)
                return text.lower()
        except sr.UnknownValueError:
            return "Sorry, I couldn't understand what you said."
        except sr.RequestError:
            return "Sorry, there was an error with the speech recognition service."
        except Exception as e:
            return f"Error processing audio: {str(e)}"

    def generate_response(self, text, user):
        """Generate appropriate response based on user input"""
        if text.startswith("Sorry") or text.startswith("Error"):
            return text

        if any(word in text for word in ['spending', 'expenses', 'budget', 'cost']):
            response = analyze_spending_patterns(user)
        elif any(word in text for word in ['save', 'saving', 'savings', 'money']):
            response = generate_saving_tip()
        elif any(word in text for word in ['why', 'how come', 'reason', 'explain']):
            response = analyze_expense_cause(user)
        elif any(word in text for word in ['help', 'assist', 'what can you do']):
            response = """I can help you with:
            1. Analyzing your spending patterns
            2. Providing saving tips
            3. Explaining your expenses
            Just ask me about any of these topics!"""
        else:
            response = "I can help you with your spending analysis, saving tips, and budget management. What would you like to know?"

        return self._clean_response(response)

    def _clean_response(self, text):
        """Clean up response text"""
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
        """Convert text to speech"""
        try:
            with NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                self.engine.save_to_file(text, temp_file.name)
                self.engine.runAndWait()

                with wave.open(temp_file.name, 'rb') as wf:
                    audio_data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
                    audio_data = audio_data.astype(np.float32) / 32767.0

                    # Clean up temp file
                    os.unlink(temp_file.name)

                    return {
                        'audio': audio_data.tolist(),
                        'sample_rate': wf.getframerate(),
                        'duration': len(audio_data) / wf.getframerate()
                    }
        except Exception as e:
            return {'error': str(e)}

voice_assistant = VoiceAssistant()