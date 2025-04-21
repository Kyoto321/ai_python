from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os
from io import BytesIO
from pydub import AudioSegment
from PIL import Image
from dotenv import load_dotenv
import logging
import speech_recognition as sc
import openai
import requests
from schemas import LyricsPayload
from utility import convert_mp3_to_wav, split_media, transcribe_audio_chunks, transcribe_wav_to_text, summerize_text

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

logging.basicConfig(level=logging.INFO)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # allow all origins
    allow_credentials=True,
    allow_methods=["*"],    # allows all methods
    allow_headers=["*"],    # allow all headers
);

if not os.path.exists('converted_files'):
    os.makedirs('converted_files')


@app.get('/', response_class=HTMLResponse)
async def read_root():
    return templates.TemplateResponse("index.html", {"request": {}})


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile=File(...), language: str = Form(...)):
    if not os.path.exists('uploads'):
        os.makedirs('uploads')

    file_location = f"uploads/{file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())
        
    # AUDIO PROCESSING
    wav_file_location = f"converted_files/{file.filename.replace(".mp3", ".wav")}"
    
    # TODO -> CONVERT TO MP3
    convert_mp3_to_wav(file_location, wav_file_location)
    
    lyrics = transcribe_wav_to_text(wav_file_location)
    
    os.remove(file_location)
    
    summary = await summerize_text(lyrics)

    return {"lyrics": lyrics, "summary": summary}


@app.post("/generate_image/")
async def generate_image(payload: LyricsPayload):
    try:
        api_key = os.getenv("OPEN_API_KEY")
        if not api_key:
            logging.error("API KEY NOT FOUND")
            raise HTTPException(status_code=200, detail="API KEY NOT FOUND")
        
        dalle_url = "https://api.openai.com/images/generations"
        
        headers = {
            "Authentication": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"Generate an image based on the summary of song. {payload.lyrics}"
        
        if len(prompt) > 100:
            prompt = prompt[:1000]
            
        data = {
            "prompt": prompt,
            "size": "1024x1024",
            "m": 1
        }
        
        logging.info(f"Sending request to OpenAI API with: {data}")
        response = requests.post(dalle_url, headers=headers, json=data)
        
        logging.info(f"OpenAI API response status: {response.status_code}")
        logging.info(f"OpenAI API response status: {response.text}")
        
        response.raise_for_status()
        
        image_url = response.json()['data'][0]['url']
        
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        
        image = Image.open(BytesIO(image_response.content))
        
        if not os.path.exists("media"):
            os.makedirs("media")
        image_path = os.path.join("media", "generated_image.png")
        image.save(image_path)
        
        logging.info(f"Image saved at: {image_path}")
        return {"image_path": image_path}
         
    except requests.exceptions.RequestException as e:
        logging.error(f"Request exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
        

@app.get("/media/generated_image.png")
async def get_generated_image():
    return FileResponse("media/generated_image.png")



