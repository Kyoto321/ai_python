from pydantic import BaseModel

# class
class LyricsPayload(BaseModel):
    lyrics: str

