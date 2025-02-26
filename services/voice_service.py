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
import re

class Expense: # Placeholder class
    def __init__(self, amount, category_id, user_id):
        self.amount = amount
        self.category_id = category_id
        self.user_id = user_id

def get_category_id(category): # Placeholder function
    # Replace with actual database query to get category ID
    category_map = {"food": 1, "transport": 2, "education": 3, "entertainment": 4, "utilities": 5}
    return category_map.get(category)

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
        """Enhanced voice command processing with natural language understanding"""
        text = text.lower()

        # Command patterns
        if "add expense" in text:
            # Extract amount and category using regex
            amount_match = re.search(r'\d+(\.\d{1,2})?', text)
            amount = float(amount_match.group()) if amount_match else None

            categories = ["food", "transport", "education", "entertainment", "utilities"]
            category = next((cat for cat in categories if cat in text), None)

            if amount and category:
                # Add expense through voice - Placeholder
                expense = Expense(amount=amount, category_id=get_category_id(category), user_id=user.id) # Placeholder
                #db.session.add(expense) # Placeholder database interaction
                #db.session.commit() # Placeholder database interaction
                return f"Added ${amount} expense for {category}"

        elif "budget summary" in text:
            # Placeholder for fetching expenses
            user_expenses = user.expenses if hasattr(user, 'expenses') else [] # Placeholder for user object
            total_spent = sum(e.amount for e in user_expenses)
            return f"Your total spending is ${total_spent:.2f}. Would you like a detailed breakdown?"

        elif "financial advice" in text:
            return analyze_spending_patterns(user)

        return "I'm sorry, I didn't understand that command. Try saying 'add expense', 'budget summary', or 'financial advice'"


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