from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import base64
import io
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from emergentintegrations.llm.chat import LlmChat, UserMessage
from elevenlabs import ElevenLabs
from elevenlabs.models import VoiceSettings

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# AI Integration
emergent_llm_key = os.environ.get('EMERGENT_LLM_KEY')
elevenlabs_api_key = os.environ.get('ELEVENLABS_API_KEY')
eleven_client = ElevenLabs(api_key=elevenlabs_api_key)

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Helper functions for MongoDB serialization
def prepare_for_mongo(data):
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, dict):
                result[key] = prepare_for_mongo(value)
            elif isinstance(value, list):
                result[key] = [prepare_for_mongo(item) if isinstance(item, dict) else item for item in value]
            else:
                result[key] = value
        return result
    return data

def parse_from_mongo(item):
    if isinstance(item, dict):
        result = {}
        for key, value in item.items():
            if key.endswith('_at') and isinstance(value, str):
                try:
                    result[key] = datetime.fromisoformat(value)
                except:
                    result[key] = value
            elif isinstance(value, dict):
                result[key] = parse_from_mongo(value)
            elif isinstance(value, list):
                result[key] = [parse_from_mongo(item) if isinstance(item, dict) else item for item in value]
            else:
                result[key] = value
        return result
    return item

# Arabic Alphabet Data
ARABIC_ALPHABET = [
    {"id": 1, "arabic": "ا", "name": "Alif", "transliteration": "A", "pronunciation": "alif", "example_word": "أسد (asad - lion)", "position": "initial"},
    {"id": 2, "arabic": "ب", "name": "Ba", "transliteration": "B", "pronunciation": "baa", "example_word": "بيت (bayt - house)", "position": "initial"},
    {"id": 3, "arabic": "ت", "name": "Ta", "transliteration": "T", "pronunciation": "taa", "example_word": "تفاح (tuffah - apple)", "position": "initial"},
    {"id": 4, "arabic": "ث", "name": "Tha", "transliteration": "TH", "pronunciation": "thaa", "example_word": "ثعلب (thalab - fox)", "position": "initial"},
    {"id": 5, "arabic": "ج", "name": "Jeem", "transliteration": "J", "pronunciation": "jeem", "example_word": "جمل (jamal - camel)", "position": "initial"},
    {"id": 6, "arabic": "ح", "name": "Ha", "transliteration": "H", "pronunciation": "haa", "example_word": "حصان (hisan - horse)", "position": "initial"},
    {"id": 7, "arabic": "خ", "name": "Kha", "transliteration": "KH", "pronunciation": "khaa", "example_word": "خروف (kharuf - sheep)", "position": "initial"},
    {"id": 8, "arabic": "د", "name": "Dal", "transliteration": "D", "pronunciation": "daal", "example_word": "دجاج (dajaj - chicken)", "position": "initial"},
    {"id": 9, "arabic": "ذ", "name": "Dhal", "transliteration": "DH", "pronunciation": "dhaal", "example_word": "ذئب (dheeb - wolf)", "position": "initial"},
    {"id": 10, "arabic": "ر", "name": "Ra", "transliteration": "R", "pronunciation": "raa", "example_word": "رجل (rajul - man)", "position": "initial"},
    {"id": 11, "arabic": "ز", "name": "Zay", "transliteration": "Z", "pronunciation": "zaay", "example_word": "زهرة (zahra - flower)", "position": "initial"},
    {"id": 12, "arabic": "س", "name": "Seen", "transliteration": "S", "pronunciation": "seen", "example_word": "سمك (samak - fish)", "position": "initial"},
    {"id": 13, "arabic": "ش", "name": "Sheen", "transliteration": "SH", "pronunciation": "sheen", "example_word": "شمس (shams - sun)", "position": "initial"},
    {"id": 14, "arabic": "ص", "name": "Sad", "transliteration": "S", "pronunciation": "saad", "example_word": "صقر (saqr - falcon)", "position": "initial"},
    {"id": 15, "arabic": "ض", "name": "Dad", "transliteration": "D", "pronunciation": "daad", "example_word": "ضفدع (difdaa - frog)", "position": "initial"},
    {"id": 16, "arabic": "ط", "name": "Ta", "transliteration": "T", "pronunciation": "taa", "example_word": "طائر (tair - bird)", "position": "initial"},
    {"id": 17, "arabic": "ظ", "name": "Dha", "transliteration": "DH", "pronunciation": "dhaa", "example_word": "ظبي (dhabi - deer)", "position": "initial"},
    {"id": 18, "arabic": "ع", "name": "Ayn", "transliteration": "A", "pronunciation": "ayn", "example_word": "عين (ayn - eye)", "position": "initial"},
    {"id": 19, "arabic": "غ", "name": "Ghayn", "transliteration": "GH", "pronunciation": "ghayn", "example_word": "غراب (ghurab - crow)", "position": "initial"},
    {"id": 20, "arabic": "ف", "name": "Fa", "transliteration": "F", "pronunciation": "faa", "example_word": "فيل (feel - elephant)", "position": "initial"},
    {"id": 21, "arabic": "ق", "name": "Qaf", "transliteration": "Q", "pronunciation": "qaaf", "example_word": "قطة (qittah - cat)", "position": "initial"},
    {"id": 22, "arabic": "ك", "name": "Kaf", "transliteration": "K", "pronunciation": "kaaf", "example_word": "كلب (kalb - dog)", "position": "initial"},
    {"id": 23, "arabic": "ل", "name": "Lam", "transliteration": "L", "pronunciation": "laam", "example_word": "ليمون (laymun - lemon)", "position": "initial"},
    {"id": 24, "arabic": "م", "name": "Meem", "transliteration": "M", "pronunciation": "meem", "example_word": "ماء (maa - water)", "position": "initial"},
    {"id": 25, "arabic": "ن", "name": "Noon", "transliteration": "N", "pronunciation": "noon", "example_word": "نار (naar - fire)", "position": "initial"},
    {"id": 26, "arabic": "ه", "name": "Ha", "transliteration": "H", "pronunciation": "haa", "example_word": "هلال (hilal - crescent)", "position": "initial"},
    {"id": 27, "arabic": "و", "name": "Waw", "transliteration": "W", "pronunciation": "waaw", "example_word": "ورد (ward - rose)", "position": "initial"},
    {"id": 28, "arabic": "ي", "name": "Ya", "transliteration": "Y", "pronunciation": "yaa", "example_word": "يد (yad - hand)", "position": "initial"}
]

# Define Models
class ArabicLetter(BaseModel):
    id: int
    arabic: str
    name: str
    transliteration: str
    pronunciation: str
    example_word: str
    position: str

class UserProgress(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    letter_id: int
    completed: bool = False
    score: int = 0
    attempts: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = "21m00Tcm4TlvDq8ikWAM"  # Default Arabic voice
    stability: Optional[float] = 0.7
    similarity_boost: Optional[float] = 0.8

class TTSResponse(BaseModel):
    audio_url: str
    text: str
    voice_id: str

class ChatMessage(BaseModel):
    message: str
    context: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

# Routes

@api_router.get("/")
async def root():
    return {"message": "Arabic LMS API is running!"}

@api_router.get("/alphabet", response_model=List[ArabicLetter])
async def get_arabic_alphabet():
    """Get the complete Arabic alphabet"""
    return [ArabicLetter(**letter) for letter in ARABIC_ALPHABET]

@api_router.get("/alphabet/{letter_id}", response_model=ArabicLetter)
async def get_arabic_letter(letter_id: int):
    """Get a specific Arabic letter by ID"""
    letter = next((l for l in ARABIC_ALPHABET if l["id"] == letter_id), None)
    if not letter:
        raise HTTPException(status_code=404, detail="Letter not found")
    return ArabicLetter(**letter)

@api_router.post("/tts/generate", response_model=TTSResponse)
async def generate_tts(request: TTSRequest):
    """Generate text-to-speech audio using ElevenLabs"""
    try:
        # Generate audio using ElevenLabs
        voice_settings = VoiceSettings(
            stability=request.stability,
            similarity_boost=request.similarity_boost,
            style=0.0,
            use_speaker_boost=True
        )
        
        audio_generator = eleven_client.text_to_speech.convert(
            text=request.text,
            voice_id=request.voice_id,
            model_id="eleven_multilingual_v2",
            voice_settings=voice_settings
        )
        
        # Collect audio data
        audio_data = b""
        for chunk in audio_generator:
            audio_data += chunk
        
        # Convert to base64 for storage/transfer
        audio_b64 = base64.b64encode(audio_data).decode()
        
        # Create response
        tts_response = TTSResponse(
            audio_url=f"data:audio/mpeg;base64,{audio_b64}",
            text=request.text,
            voice_id=request.voice_id
        )
        
        # Save to database
        tts_dict = prepare_for_mongo(tts_response.dict())
        await db.tts_generations.insert_one(tts_dict)
        
        return tts_response
        
    except Exception as e:
        logging.error(f"Error generating TTS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating TTS: {str(e)}")

@api_router.post("/progress", response_model=UserProgress)
async def save_progress(progress: UserProgress):
    """Save user progress for a letter"""
    try:
        progress.updated_at = datetime.now(timezone.utc)
        progress_dict = prepare_for_mongo(progress.dict())
        
        # Update existing progress or create new
        existing = await db.user_progress.find_one({"letter_id": progress.letter_id})
        if existing:
            await db.user_progress.update_one(
                {"letter_id": progress.letter_id},
                {"$set": progress_dict}
            )
        else:
            await db.user_progress.insert_one(progress_dict)
        
        return progress
    except Exception as e:
        logging.error(f"Error saving progress: {str(e)}")
        raise HTTPException(status_code=500, detail="Error saving progress")

@api_router.get("/progress", response_model=List[UserProgress])
async def get_progress():
    """Get all user progress"""
    try:
        progress_items = await db.user_progress.find().to_list(length=None)
        return [UserProgress(**parse_from_mongo(item)) for item in progress_items]
    except Exception as e:
        logging.error(f"Error getting progress: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting progress")

@api_router.post("/chat", response_model=ChatResponse)
async def chat_with_tutor(chat_request: ChatMessage):
    """Chat with AI Arabic tutor"""
    try:
        # Create session ID for conversation
        session_id = str(uuid.uuid4())
        
        # System message for Arabic learning context
        system_message = """You are an expert Arabic language tutor helping English-speaking Muslims learn Arabic. 
        You specialize in:
        1. Arabic alphabet and pronunciation
        2. Basic Arabic grammar for Quranic understanding
        3. Islamic context for Arabic words and phrases
        4. Encouraging and patient teaching
        
        Always provide clear, simple explanations. When discussing Arabic letters or words, 
        include both Arabic text and transliteration. Be encouraging and relate lessons to Islamic context when appropriate.
        Keep responses concise but helpful."""
        
        # Initialize chat with emergent LLM
        chat = LlmChat(
            api_key=emergent_llm_key,
            session_id=session_id,
            system_message=system_message
        ).with_model("openai", "gpt-5")
        
        # Create user message with context
        full_message = f"Context: {chat_request.context}\nUser question: {chat_request.message}" if chat_request.context else chat_request.message
        user_message = UserMessage(text=full_message)
        
        # Send message and get response
        response = await chat.send_message(user_message)
        
        # Save chat to database
        chat_record = {
            "session_id": session_id,
            "user_message": chat_request.message,
            "ai_response": response,
            "context": chat_request.context,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.chat_history.insert_one(chat_record)
        
        return ChatResponse(response=response, session_id=session_id)
        
    except Exception as e:
        logging.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()