from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import base64
import jwt
import httpx
from datetime import datetime, timezone, timedelta
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
import bcrypt
from emergentintegrations.llm.chat import LlmChat, UserMessage
from elevenlabs import ElevenLabs, VoiceSettings
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
security = HTTPBearer(auto_error=False)
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 7

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')

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

# AI Integration
emergent_llm_key = os.environ.get('EMERGENT_LLM_KEY')
elevenlabs_api_key = os.environ.get('ELEVENLABS_API_KEY')
eleven_client = ElevenLabs(api_key=elevenlabs_api_key) if elevenlabs_api_key else None

# Create the main app
app = FastAPI(title="Arabic LMS API", description="Learn Arabic for the Quran")
api_router = APIRouter(prefix="/api")

# Arabic Alphabet Data (Complete 28 letters)
ARABIC_ALPHABET = [
    {"id": 1, "arabic": "ا", "name": "Alif", "transliteration": "A", "pronunciation": "alif", "example_word": "أسد", "example_meaning": "lion"},
    {"id": 2, "arabic": "ب", "name": "Ba", "transliteration": "B", "pronunciation": "baa", "example_word": "بيت", "example_meaning": "house"},
    {"id": 3, "arabic": "ت", "name": "Ta", "transliteration": "T", "pronunciation": "taa", "example_word": "تفاح", "example_meaning": "apple"},
    {"id": 4, "arabic": "ث", "name": "Tha", "transliteration": "TH", "pronunciation": "thaa", "example_word": "ثعلب", "example_meaning": "fox"},
    {"id": 5, "arabic": "ج", "name": "Jeem", "transliteration": "J", "pronunciation": "jeem", "example_word": "جمل", "example_meaning": "camel"},
    {"id": 6, "arabic": "ح", "name": "Ha", "transliteration": "H", "pronunciation": "haa", "example_word": "حصان", "example_meaning": "horse"},
    {"id": 7, "arabic": "خ", "name": "Kha", "transliteration": "KH", "pronunciation": "khaa", "example_word": "خروف", "example_meaning": "sheep"},
    {"id": 8, "arabic": "د", "name": "Dal", "transliteration": "D", "pronunciation": "daal", "example_word": "دجاج", "example_meaning": "chicken"},
    {"id": 9, "arabic": "ذ", "name": "Dhal", "transliteration": "DH", "pronunciation": "dhaal", "example_word": "ذئب", "example_meaning": "wolf"},
    {"id": 10, "arabic": "ر", "name": "Ra", "transliteration": "R", "pronunciation": "raa", "example_word": "رجل", "example_meaning": "man"},
    {"id": 11, "arabic": "ز", "name": "Zay", "transliteration": "Z", "pronunciation": "zaay", "example_word": "زهرة", "example_meaning": "flower"},
    {"id": 12, "arabic": "س", "name": "Seen", "transliteration": "S", "pronunciation": "seen", "example_word": "سمك", "example_meaning": "fish"},
    {"id": 13, "arabic": "ش", "name": "Sheen", "transliteration": "SH", "pronunciation": "sheen", "example_word": "شمس", "example_meaning": "sun"},
    {"id": 14, "arabic": "ص", "name": "Sad", "transliteration": "S", "pronunciation": "saad", "example_word": "صقر", "example_meaning": "falcon"},
    {"id": 15, "arabic": "ض", "name": "Dad", "transliteration": "D", "pronunciation": "daad", "example_word": "ضفدع", "example_meaning": "frog"},
    {"id": 16, "arabic": "ط", "name": "Ta", "transliteration": "T", "pronunciation": "taa", "example_word": "طائر", "example_meaning": "bird"},
    {"id": 17, "arabic": "ظ", "name": "Dha", "transliteration": "DH", "pronunciation": "dhaa", "example_word": "ظبي", "example_meaning": "deer"},
    {"id": 18, "arabic": "ع", "name": "Ayn", "transliteration": "A", "pronunciation": "ayn", "example_word": "عين", "example_meaning": "eye"},
    {"id": 19, "arabic": "غ", "name": "Ghayn", "transliteration": "GH", "pronunciation": "ghayn", "example_word": "غراب", "example_meaning": "crow"},
    {"id": 20, "arabic": "ف", "name": "Fa", "transliteration": "F", "pronunciation": "faa", "example_word": "فيل", "example_meaning": "elephant"},
    {"id": 21, "arabic": "ق", "name": "Qaf", "transliteration": "Q", "pronunciation": "qaaf", "example_word": "قطة", "example_meaning": "cat"},
    {"id": 22, "arabic": "ك", "name": "Kaf", "transliteration": "K", "pronunciation": "kaaf", "example_word": "كلب", "example_meaning": "dog"},
    {"id": 23, "arabic": "ل", "name": "Lam", "transliteration": "L", "pronunciation": "laam", "example_word": "ليمون", "example_meaning": "lemon"},
    {"id": 24, "arabic": "م", "name": "Meem", "transliteration": "M", "pronunciation": "meem", "example_word": "ماء", "example_meaning": "water"},
    {"id": 25, "arabic": "ن", "name": "Noon", "transliteration": "N", "pronunciation": "noon", "example_word": "نار", "example_meaning": "fire"},
    {"id": 26, "arabic": "ه", "name": "Ha", "transliteration": "H", "pronunciation": "haa", "example_word": "هلال", "example_meaning": "crescent"},
    {"id": 27, "arabic": "و", "name": "Waw", "transliteration": "W", "pronunciation": "waaw", "example_word": "ورد", "example_meaning": "rose"},
    {"id": 28, "arabic": "ي", "name": "Ya", "transliteration": "Y", "pronunciation": "yaa", "example_word": "يد", "example_meaning": "hand"}
]

# Enhanced JWT token functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=JWT_EXPIRY_DAYS)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(user_id: str):
    return create_access_token({"sub": user_id, "type": "refresh"}, timedelta(days=30))

async def get_current_user(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    token = None
    
    # Check session_token cookie first (for Google OAuth)
    if "session_token" in request.cookies:
        session_token = request.cookies["session_token"]
        session = await db.sessions.find_one({"session_token": session_token})
        if session and session.get("expires_at") and datetime.fromisoformat(session["expires_at"]) > datetime.now(timezone.utc):
            user = await db.users.find_one({"email": session["email"]})
            if user:
                return user
    
    # Fallback to JWT token
    if credentials:
        token = credentials.credentials
    
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email = payload.get("sub")
        if email is None or payload.get("type") == "refresh":
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"email": email})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    picture: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_xp: int = 0
    current_level: int = 1
    completed_letters: List[int] = []

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: User

class SessionDataRequest(BaseModel):
    pass

class ArabicLetter(BaseModel):
    id: int
    arabic: str
    name: str
    transliteration: str
    pronunciation: str
    example_word: str
    example_meaning: str

class UserProgress(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    letter_id: int
    completed: bool = False
    score: int = 0
    attempts: int = 0
    xp_earned: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProgressRequest(BaseModel):
    letter_id: int
    completed: bool = False
    score: int = 0
    attempts: int = 0
    xp_earned: int = 0

class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = "21m00Tcm4TlvDq8ikWAM"

class TTSResponse(BaseModel):
    audio_url: str
    text: str
    source: str  # 'elevenlabs', 'browser', or 'cached'

class QuizAnswer(BaseModel):
    letter_id: int
    selected_letter_id: int

class QuizResult(BaseModel):
    correct: bool
    xp_earned: int
    message: str
    score: int
    can_proceed: bool
    min_score_required: int = 80

# Audio caching
audio_cache = {}

def generate_browser_speech(text: str) -> str:
    """Generate a data URL for browser speech synthesis as fallback"""
    # Return an instruction for the frontend to use speechSynthesis
    return f"browser_speech:{text}"

async def get_cached_audio(text: str) -> Optional[str]:
    """Get cached audio URL"""
    return audio_cache.get(text)

async def cache_audio(text: str, audio_url: str):
    """Cache audio URL"""
    audio_cache[text] = audio_url

# Auth Routes
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate, response: Response):
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_data.password)
    user = User(email=user_data.email, full_name=user_data.full_name)
    
    user_dict = prepare_for_mongo(user.dict())
    user_dict["hashed_password"] = hashed_password
    
    await db.users.insert_one(user_dict)
    
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(user.email)
    
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer", user=user)

@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    user = await db.users.find_one({"email": user_credentials.email})
    if not user or not verify_password(user_credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user["email"]})
    refresh_token = create_refresh_token(user["email"])
    
    user_obj = User(**{k: v for k, v in user.items() if k != "hashed_password"})
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer", user=user_obj)

@api_router.post("/auth/refresh", response_model=Token)
async def refresh_token(refresh_data: RefreshTokenRequest):
    try:
        payload = jwt.decode(refresh_data.refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email = payload.get("sub")
        if email is None or payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        user = await db.users.find_one({"email": email})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        access_token = create_access_token(data={"sub": email})
        new_refresh_token = create_refresh_token(email)
        
        user_obj = User(**{k: v for k, v in user.items() if k != "hashed_password"})
        return Token(access_token=access_token, refresh_token=new_refresh_token, token_type="bearer", user=user_obj)
        
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@api_router.post("/auth/session")
async def process_session(request: Request, response: Response):
    """Process Google OAuth session_id"""
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    try:
        # Call Emergent auth service
        async with httpx.AsyncClient() as client:
            auth_response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id},
                timeout=10.0
            )
            
            if auth_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Invalid session")
                
            auth_data = auth_response.json()
        
        # Check if user exists
        existing_user = await db.users.find_one({"email": auth_data["email"]})
        
        if not existing_user:
            # Create new user
            user = User(
                email=auth_data["email"],
                full_name=auth_data["name"],
                picture=auth_data.get("picture")
            )
            user_dict = prepare_for_mongo(user.dict())
            await db.users.insert_one(user_dict)
        else:
            user = User(**{k: v for k, v in existing_user.items() if k != "hashed_password"})
        
        # Store session in database
        session_token = auth_data["session_token"]
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        await db.sessions.update_one(
            {"email": auth_data["email"]},
            {"$set": {
                "session_token": session_token,
                "expires_at": expires_at.isoformat(),
                "user_id": user.id
            }},
            upsert=True
        )
        
        # Set httpOnly cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=7 * 24 * 60 * 60,  # 7 days
            httponly=True,
            secure=True,
            samesite="none",
            path="/"
        )
        
        return {"user": user, "session_token": session_token}
        
    except Exception as e:
        logging.error(f"OAuth session error: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication failed")

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response, current_user: dict = Depends(get_current_user)):
    """Logout user and clear session"""
    # Clear session from database
    await db.sessions.delete_many({"user_id": current_user["id"]})
    
    # Clear cookie
    response.delete_cookie("session_token", path="/")
    
    return {"message": "Logged out successfully"}

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return User(**{k: v for k, v in current_user.items() if k != "hashed_password"})

# Lesson Routes
@api_router.get("/lessons", response_model=List[ArabicLetter])
async def get_lessons():
    """Get all Arabic alphabet letters"""
    return [ArabicLetter(**letter) for letter in ARABIC_ALPHABET]

@api_router.get("/lessons/{letter_id}", response_model=ArabicLetter)
async def get_lesson(letter_id: int):
    """Get specific letter lesson"""
    letter = next((l for l in ARABIC_ALPHABET if l["id"] == letter_id), None)
    if not letter:
        raise HTTPException(status_code=404, detail="Letter not found")
    return ArabicLetter(**letter)

@api_router.post("/tts/generate", response_model=TTSResponse)
async def generate_tts(request: TTSRequest):
    """Generate Arabic pronunciation audio with caching and fallbacks"""
    # Check cache first
    cached_audio = await get_cached_audio(request.text)
    if cached_audio:
        return TTSResponse(
            audio_url=cached_audio,
            text=request.text,
            source="cached"
        )
    
    # Try ElevenLabs
    if eleven_client:
        try:
            voice_settings = VoiceSettings(
                stability=0.7,
                similarity_boost=0.8,
                style=0.0,
                use_speaker_boost=True
            )
            
            audio_generator = eleven_client.text_to_speech.convert(
                text=request.text,
                voice_id=request.voice_id,
                model_id="eleven_multilingual_v2",
                voice_settings=voice_settings
            )
            
            audio_data = b""
            for chunk in audio_generator:
                audio_data += chunk
            
            audio_b64 = base64.b64encode(audio_data).decode()
            audio_url = f"data:audio/mpeg;base64,{audio_b64}"
            
            # Cache the result
            await cache_audio(request.text, audio_url)
            
            return TTSResponse(
                audio_url=audio_url,
                text=request.text,
                source="elevenlabs"
            )
            
        except Exception as e:
            logging.error(f"ElevenLabs TTS Error: {str(e)}")
    
    # Fallback to browser speech synthesis
    browser_speech_url = generate_browser_speech(request.text)
    return TTSResponse(
        audio_url=browser_speech_url,
        text=request.text,
        source="browser"
    )

# Progress Routes
@api_router.post("/progress", response_model=UserProgress)
async def save_progress(progress_request: ProgressRequest, current_user: dict = Depends(get_current_user)):
    """Save lesson progress"""
    progress = UserProgress(
        user_id=current_user["id"],
        letter_id=progress_request.letter_id,
        completed=progress_request.completed,
        score=progress_request.score,
        attempts=progress_request.attempts,
        xp_earned=progress_request.xp_earned,
        updated_at=datetime.now(timezone.utc)
    )
    
    progress_dict = prepare_for_mongo(progress.dict())
    
    existing = await db.progress.find_one({
        "user_id": current_user["id"], 
        "letter_id": progress_request.letter_id
    })
    
    if existing:
        await db.progress.update_one(
            {"user_id": current_user["id"], "letter_id": progress_request.letter_id},
            {"$set": progress_dict}
        )
    else:
        await db.progress.insert_one(progress_dict)
    
    # Update user XP and completed letters
    if progress.completed and progress_request.letter_id not in current_user.get("completed_letters", []):
        new_xp = current_user.get("total_xp", 0) + progress.xp_earned
        new_level = (new_xp // 100) + 1
        completed_letters = current_user.get("completed_letters", [])
        completed_letters.append(progress_request.letter_id)
        
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": {
                "total_xp": new_xp,
                "current_level": new_level,
                "completed_letters": completed_letters
            }}
        )
    
    return progress

@api_router.get("/progress", response_model=List[UserProgress])
async def get_progress(current_user: dict = Depends(get_current_user)):
    """Get user's learning progress"""
    progress_items = await db.progress.find({"user_id": current_user["id"]}).to_list(length=None)
    return [UserProgress(**item) for item in progress_items]

@api_router.post("/quiz/answer", response_model=QuizResult)
async def submit_quiz_answer(answer: QuizAnswer, current_user: dict = Depends(get_current_user)):
    """Submit quiz answer and get result with completion gating"""
    correct = answer.letter_id == answer.selected_letter_id
    xp_earned = 20 if correct else 5
    
    # Get current attempts for this letter
    existing_progress = await db.progress.find_one({
        "user_id": current_user["id"],
        "letter_id": answer.letter_id
    })
    
    attempts = (existing_progress.get("attempts", 0) if existing_progress else 0) + 1
    previous_score = existing_progress.get("score", 0) if existing_progress else 0
    
    # Calculate score based on attempts (first try = 100, decreases with retries)
    base_score = 100 if correct else 0
    attempt_penalty = max(0, (attempts - 1) * 10)  # -10 points per retry
    current_score = max(0, base_score - attempt_penalty)
    
    # Use highest score achieved
    final_score = max(previous_score, current_score)
    
    # Check if score meets threshold (80%)
    min_score_required = 80
    can_proceed = final_score >= min_score_required
    
    # Save quiz attempt
    quiz_attempt = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "letter_id": answer.letter_id,
        "selected_letter_id": answer.selected_letter_id,
        "correct": correct,
        "xp_earned": xp_earned,
        "score": current_score,
        "attempts": attempts,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.quiz_attempts.insert_one(quiz_attempt)
    
    # Update progress
    await db.progress.update_one(
        {"user_id": current_user["id"], "letter_id": answer.letter_id},
        {"$set": {
            "score": final_score,
            "attempts": attempts,
            "completed": can_proceed,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    # Update user XP only if they can proceed
    if can_proceed:
        new_xp = current_user.get("total_xp", 0) + xp_earned
        new_level = (new_xp // 100) + 1
        
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": {"total_xp": new_xp, "current_level": new_level}}
        )
    
    if correct and can_proceed:
        message = f"Excellent! Letter completed with {final_score}% score!"
    elif correct and not can_proceed:
        message = f"Correct! But score is {final_score}%. Need {min_score_required}% to proceed."
    else:
        message = f"Try again! Current score: {final_score}%"
    
    return QuizResult(
        correct=correct,
        xp_earned=xp_earned if can_proceed else 0,
        message=message,
        score=final_score,
        can_proceed=can_proceed,
        min_score_required=min_score_required
    )

# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Seed data on startup
@app.on_event("startup")
async def seed_database():
    """Seed the database with initial data"""
    lesson_count = await db.lessons.count_documents({})
    if lesson_count == 0:
        lesson_documents = [prepare_for_mongo(letter) for letter in ARABIC_ALPHABET]
        await db.lessons.insert_many(lesson_documents)
        logger.info("Seeded Arabic alphabet lessons")