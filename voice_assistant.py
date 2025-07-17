"""
Voice Assistant Module
Provides text-to-speech and speech-to-text capabilities for Siri/Alexa integration
"""

import os
import logging
import pyttsx3
import speech_recognition as sr
from typing import Optional, Dict, Any
from flask import request, jsonify
import time

logger = logging.getLogger(__name__)

class VoiceAssistant:
    """Voice Assistant for Siri/Alexa integration"""
    
    def __init__(self):
        self.enable_voice = os.environ.get("ENABLE_VOICE_ASSISTANT", "False").lower() == "true"
        self.voice_language = os.environ.get("VOICE_LANGUAGE", "en-US")
        self.voice_rate = int(os.environ.get("VOICE_RATE", "150"))
        
        if self.enable_voice:
            self._initialize_tts()
            self._initialize_stt()
    
    def _initialize_tts(self):
        """Initialize text-to-speech engine"""
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', self.voice_rate)
            
            # Set voice based on language
            voices = self.tts_engine.getProperty('voices')
            for voice in voices:
                if self.voice_language in voice.id:
                    self.tts_engine.setProperty('voice', voice.id)
                    break
            
            logger.info("Text-to-speech engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            self.tts_engine = None
    
    def _initialize_stt(self):
        """Initialize speech-to-text recognizer"""
        try:
            self.stt_recognizer = sr.Recognizer()
            self.stt_recognizer.energy_threshold = 4000
            self.stt_recognizer.dynamic_energy_threshold = True
            
            logger.info("Speech-to-text recognizer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize STT recognizer: {e}")
            self.stt_recognizer = None
    
    def text_to_speech(self, text: str, save_to_file: bool = False, filename: str = None) -> Dict[str, Any]:
        """
        Convert text to speech
        
        Args:
            text: Text to convert to speech
            save_to_file: Whether to save audio to file
            filename: Optional filename for saved audio
            
        Returns:
            Dict with success status and file path if saved
        """
        if not self.enable_voice or not self.tts_engine:
            return {
                "success": False,
                "error": "Voice assistant not enabled or TTS not initialized"
            }
        
        try:
            if save_to_file:
                if not filename:
                    filename = f"response_{int(time.time())}.mp3"
                
                # Save to file
                self.tts_engine.save_to_file(text, filename)
                self.tts_engine.runAndWait()
                
                return {
                    "success": True,
                    "file_path": filename,
                    "text": text
                }
            else:
                # Speak directly
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                
                return {
                    "success": True,
                    "text": text
                }
                
        except Exception as e:
            logger.error(f"Text-to-speech error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def speech_to_text(self, audio_file_path: str = None) -> Dict[str, Any]:
        """
        Convert speech to text
        
        Args:
            audio_file_path: Path to audio file (optional, uses microphone if not provided)
            
        Returns:
            Dict with success status and transcribed text
        """
        if not self.enable_voice or not self.stt_recognizer:
            return {
                "success": False,
                "error": "Voice assistant not enabled or STT not initialized"
            }
        
        try:
            if audio_file_path:
                # Process audio file
                with sr.AudioFile(audio_file_path) as source:
                    audio = self.stt_recognizer.record(source)
            else:
                # Use microphone
                with sr.Microphone() as source:
                    logger.info("Listening...")
                    audio = self.stt_recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            # Recognize speech
            text = self.stt_recognizer.recognize_google(audio, language=self.voice_language)
            
            return {
                "success": True,
                "text": text
            }
            
        except sr.WaitTimeoutError:
            return {
                "success": False,
                "error": "No speech detected within timeout"
            }
        except sr.UnknownValueError:
            return {
                "success": False,
                "error": "Could not understand audio"
            }
        except sr.RequestError as e:
            return {
                "success": False,
                "error": f"Speech recognition service error: {e}"
            }
        except Exception as e:
            logger.error(f"Speech-to-text error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_voice_response(self, text: str) -> Dict[str, Any]:
        """
        Create a voice response suitable for Siri/Alexa
        
        Args:
            text: Text to convert to voice response
            
        Returns:
            Dict with audio file path and metadata
        """
        if not self.enable_voice:
            return {
                "success": False,
                "error": "Voice assistant not enabled"
            }
        
        try:
            # Create a voice-friendly version of the text
            voice_text = self._optimize_for_voice(text)
            
            # Generate audio file
            filename = f"voice_response_{int(time.time())}.mp3"
            result = self.text_to_speech(voice_text, save_to_file=True, filename=filename)
            
            if result["success"]:
                return {
                    "success": True,
                    "audio_file": filename,
                    "original_text": text,
                    "voice_text": voice_text,
                    "duration": self._estimate_duration(voice_text)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error creating voice response: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _optimize_for_voice(self, text: str) -> str:
        """Optimize text for voice output"""
        # Remove code blocks and technical formatting
        import re
        
        # Remove markdown code blocks
        text = re.sub(r'```[\s\S]*?```', '[Code block]', text)
        
        # Remove inline code
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # Replace technical terms with voice-friendly versions
        replacements = {
            'API': 'A P I',
            'URL': 'U R L',
            'HTTP': 'H T T P',
            'JSON': 'J S O N',
            'HTML': 'H T M L',
            'CSS': 'C S S',
            'JS': 'JavaScript',
            'SQL': 'S Q L',
            'Git': 'Git',
            'npm': 'N P M',
            'yarn': 'Yarn',
            'Docker': 'Docker',
            'AWS': 'A W S',
            'API key': 'A P I key',
            'CLI': 'C L I',
            'GUI': 'G U I',
            'IDE': 'I D E',
            'SDK': 'S D K',
            'REST': 'REST',
            'GraphQL': 'Graph Q L'
        }
        
        for tech_term, voice_term in replacements.items():
            text = text.replace(tech_term, voice_term)
        
        # Add pauses for better comprehension
        text = text.replace('. ', '. ... ')
        text = text.replace('! ', '! ... ')
        text = text.replace('? ', '? ... ')
        
        return text
    
    def _estimate_duration(self, text: str) -> int:
        """Estimate speech duration in seconds"""
        # Rough estimate: 150 words per minute
        words = len(text.split())
        return max(1, int(words * 60 / 150)) 