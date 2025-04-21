from pydub import AudioSegment
import logging
import speech_recognition as sr
import openai
import requests
from PIL import Image
from dotenv import load_dotenv
from io import BytesIO
import os


logging.basicConfig(level=logging.INFO)


### TRANSCRIBING

def convert_mp3_to_wav(mp3_path, wav_path):
    audio = AudioSegment.from_mp3(mp3_path)
    audio.export(wav_path, format="wav")
    logging.info(f"Converted MP3 to WAV : {wav_path}")
    
    
def split_media(wav_path, check_lenght_ms=60000):
    
    audio = AudioSegment.from_wav
    chunks = [audio[i:i+ check_lenght_ms] for i in range[0, len(audio), check_lenght_ms]]
    
    return chunks    
    

def transcribe_audio_chunks(chunk, chunk_index):
    chunk_path = f"chunk_{chunk_index}.wav"
    chunk.export(chunk_path, format="wav")
    
    try:
        with open(chunk_path, 'rb') as audio_file:
            response = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file
            )
    
    except Exception as e:
        logging.error("An error has occured with chunk {chunk_index}: {e}")
        text = ""
        
    finally: 
        os.remove(chunk_path)
    return text
    

def transcribe_wav_to_text(wav_path):
    chunks = split_media(wav_path)
    full_text = ""
    
    for i, chunk in enumerate(chunks):
        chunk_text = transcribe_audio_chunks(chunk, i)
        full_text += chunk_text + " "
        
    logging.info("Transcribed Text: {full_text.strip()}")
    return full_text.strip()
    
    
async def summerize_text(text):
    try:
        response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            messages = [
                {"role": "system", "content": "You are helpful assistant."},
                {"role": "user", "content": f"Summerize the following text in one sentence: {text}"}
            ]
        )
        summary = response.choices[0].message['content'].strip()
        logging.info(f"Generated summary: {summary}")
        return summary
        
    except Exception as e:
        logging.error(f"An error occured during text summerization: {e}")
        return "Summary generation failed"    

    

    
    