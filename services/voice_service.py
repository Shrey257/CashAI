import os
import json
import speech_recognition as sr
import pyttsx3
import numpy as np
import sounddevice as sd
from tempfile import NamedTemporaryFile
from services.ai_service import analyze_spending_patterns, generate_saving_tip, analyze_expense_cause


class VoiceAssistant:

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        # Configure voice settings
        self.engine.setProperty('rate', 150)  # Speed of speech
        self.engine.setProperty('volume', 0.9)  # Volume level

    def listen(self, audio_data):
        """Convert audio data to text using speech recognition"""
        try:
            # Save the audio data to a temporary file
            with NamedTemporaryFile(suffix=".wav", delete=True) as temp_file:
                # Convert float32 audio data to int16
                audio_int16 = (audio_data * 32767).astype(np.int16)
                import wave
                with wave.open(temp_file.name, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(44100)
                    wf.writeframes(audio_int16.tobytes())

                # Use the temporary file for speech recognition
                with sr.AudioFile(temp_file.name) as source:
                    audio = self.recognizer.record(source)
                    text = self.recognizer.recognize_google(audio)
                    return text.lower()
        except Exception as e:
            return f"Error processing audio: {str(e)}"

    def generate_response(self, text, user):
        """Generate a response based on the recognized text"""
        # Determine the type of query and generate appropriate response
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
        """Clean the response for speech synthesis"""
        # Remove markdown formatting
        text = text.replace('**', '')
        # Replace emojis with their descriptions
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
            # Create a temporary file for the audio
            with NamedTemporaryFile(suffix=".wav", delete=True) as temp_file:
                self.engine.save_to_file(text, temp_file.name)
                self.engine.runAndWait()

                # Read the audio file
                with wave.open(temp_file.name, 'rb') as wf:
                    # Get audio data
                    audio_data = np.frombuffer(wf.readframes(wf.getnframes()),
                                               dtype=np.int16)
                    audio_data = audio_data.astype(np.float32) / 32767.0

                    return {
                        'audio': audio_data.tolist(),
                        'sample_rate': wf.getframerate(),
                        'duration': len(audio_data) / wf.getframerate()
                    }
        except Exception as e:
            return {'error': str(e)}


voice_assistant = VoiceAssistant()
