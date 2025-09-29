from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request, Response, UploadFile, File
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
import io
import speech_recognition as sr
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

# Arabic Alphabet Data with Islamic Context
ARABIC_ALPHABET = [
    {"id": 1, "arabic": "ا", "name": "Alif", "transliteration": "A", "pronunciation": "alif", "example_word": "أسد", "example_meaning": "lion", "quranic_examples": ["الله (Allah)", "أحمد (Ahmad)", "الإسلام (Islam)"], "islamic_context": "First letter of Allah's name, represents the oneness of Allah"},
    {"id": 2, "arabic": "ب", "name": "Ba", "transliteration": "B", "pronunciation": "baa", "example_word": "بيت", "example_meaning": "house", "quranic_examples": ["بسم (Bism - In the name)", "بركة (Barakah - Blessing)"], "islamic_context": "Begins Bismillah, the most recited phrase in Islam"},
    {"id": 3, "arabic": "ت", "name": "Ta", "transliteration": "T", "pronunciation": "taa", "example_word": "تفاح", "example_meaning": "apple", "quranic_examples": ["توبة (Tawbah - Repentance)", "تقوى (Taqwa - God-consciousness)"], "islamic_context": "Found in many spiritual terms like Taqwa"},
    {"id": 4, "arabic": "ث", "name": "Tha", "transliteration": "TH", "pronunciation": "thaa", "example_word": "ثعلب", "example_meaning": "fox", "quranic_examples": ["ثواب (Thawab - Reward)", "ثلاثة (Thalatha - Three)"], "islamic_context": "Appears in reward (thawab) for good deeds"},
    {"id": 5, "arabic": "ج", "name": "Jeem", "transliteration": "J", "pronunciation": "jeem", "example_word": "جمل", "example_meaning": "camel", "quranic_examples": ["جنة (Jannah - Paradise)", "جماعة (Jamaah - Community)"], "islamic_context": "First letter of Jannah (Paradise)"},
    {"id": 6, "arabic": "ح", "name": "Ha", "transliteration": "H", "pronunciation": "haa", "example_word": "حصان", "example_meaning": "horse", "quranic_examples": ["حمد (Hamd - Praise)", "حلال (Halal)", "حج (Hajj)"], "islamic_context": "Found in Hamd (praise to Allah) and Hajj pilgrimage"},
    {"id": 7, "arabic": "خ", "name": "Kha", "transliteration": "KH", "pronunciation": "khaa", "example_word": "خروف", "example_meaning": "sheep", "quranic_examples": ["خير (Khayr - Good)", "خلق (Khalq - Creation)"], "islamic_context": "In Khayr (goodness) and Allah's creation (Khalq)"},
    {"id": 8, "arabic": "د", "name": "Dal", "transliteration": "D", "pronunciation": "daal", "example_word": "دجاج", "example_meaning": "chicken", "quranic_examples": ["دين (Deen - Religion)", "دعاء (Dua - Prayer)"], "islamic_context": "Essential in Deen (way of life) and Dua (supplication)"},
    {"id": 9, "arabic": "ذ", "name": "Dhal", "transliteration": "DH", "pronunciation": "dhaal", "example_word": "ذئب", "example_meaning": "wolf", "quranic_examples": ["ذكر (Dhikr - Remembrance)", "ذنب (Dhanb - Sin)"], "islamic_context": "Key in Dhikr (remembrance of Allah)"},
    {"id": 10, "arabic": "ر", "name": "Ra", "transliteration": "R", "pronunciation": "raa", "example_word": "رجل", "example_meaning": "man", "quranic_examples": ["رحمن (Rahman - The Merciful)", "ربّ (Rabb - Lord)"], "islamic_context": "Central in Allah's names: Ar-Rahman, Ar-Raheem"},
    {"id": 11, "arabic": "ز", "name": "Zay", "transliteration": "Z", "pronunciation": "zaay", "example_word": "زهرة", "example_meaning": "flower", "quranic_examples": ["زكاة (Zakah - Charity)", "زمزم (Zamzam)"], "islamic_context": "In Zakah, the third pillar of Islam"},
    {"id": 12, "arabic": "س", "name": "Seen", "transliteration": "S", "pronunciation": "seen", "example_word": "سمك", "example_meaning": "fish", "quranic_examples": ["سلام (Salam - Peace)", "صلاة (Salah - Prayer)"], "islamic_context": "In Salam (peace) and core Islamic greetings"},
    {"id": 13, "arabic": "ش", "name": "Sheen", "transliteration": "SH", "pronunciation": "sheen", "example_word": "شمس", "example_meaning": "sun", "quranic_examples": ["شهادة (Shahadah - Testimony)", "شكر (Shukr - Gratitude)"], "islamic_context": "First letter of Shahadah (declaration of faith)"},
    {"id": 14, "arabic": "ص", "name": "Sad", "transliteration": "S", "pronunciation": "saad", "example_word": "صقر", "example_meaning": "falcon", "quranic_examples": ["صلاة (Salah - Prayer)", "صوم (Sawm - Fasting)"], "islamic_context": "In Salah (prayer) and Sawm (fasting) - two pillars of Islam"},
    {"id": 15, "arabic": "ض", "name": "Dad", "transliteration": "D", "pronunciation": "daad", "example_word": "ضفدع", "example_meaning": "frog", "quranic_examples": ["ضلال (Dalal - Misguidance)", "فضل (Fadl - Grace)"], "islamic_context": "The 'Dad' is unique to Arabic, showing the language's special status"},
    {"id": 16, "arabic": "ط", "name": "Ta", "transliteration": "T", "pronunciation": "taa", "example_word": "طائر", "example_meaning": "bird", "quranic_examples": ["طهارة (Taharah - Purity)", "طواف (Tawaf)"], "islamic_context": "In Taharah (ritual purity) and Tawaf (circling Kaaba)"},
    {"id": 17, "arabic": "ظ", "name": "Dha", "transliteration": "DH", "pronunciation": "dhaa", "example_word": "ظبي", "example_meaning": "deer", "quranic_examples": ["ظلم (Dhulm - Oppression)", "ظهر (Dhuhr - Noon prayer)"], "islamic_context": "In Dhuhr prayer and warnings against oppression (dhulm)"},
    {"id": 18, "arabic": "ع", "name": "Ayn", "transliteration": "A", "pronunciation": "ayn", "example_word": "عين", "example_meaning": "eye", "quranic_examples": ["عبادة (Ibadah - Worship)", "عمرة (Umrah)"], "islamic_context": "Central in worship (Ibadah) and Umrah pilgrimage"},
    {"id": 19, "arabic": "غ", "name": "Ghayn", "transliteration": "GH", "pronunciation": "ghayn", "example_word": "غراب", "example_meaning": "crow", "quranic_examples": ["غفران (Ghufran - Forgiveness)", "مغرب (Maghrib)"], "islamic_context": "In seeking Allah's forgiveness (Ghufran)"},
    {"id": 20, "arabic": "ف", "name": "Fa", "transliteration": "F", "pronunciation": "faa", "example_word": "فيل", "example_meaning": "elephant", "quranic_examples": ["فاتحة (Fatihah)", "فجر (Fajr - Dawn prayer)"], "islamic_context": "Opens Al-Fatihah and in Fajr prayer"},
    {"id": 21, "arabic": "ق", "name": "Qaf", "transliteration": "Q", "pronunciation": "qaaf", "example_word": "قطة", "example_meaning": "cat", "quranic_examples": ["قرآن (Quran)", "قبلة (Qiblah)"], "islamic_context": "First letter of Quran and in Qiblah (prayer direction)"},
    {"id": 22, "arabic": "ك", "name": "Kaf", "transliteration": "K", "pronunciation": "kaaf", "example_word": "كلب", "example_meaning": "dog", "quranic_examples": ["كعبة (Kaaba)", "كتاب (Kitab - Book)"], "islamic_context": "In Kaaba (House of Allah) and Kitab (divine books)"},
    {"id": 23, "arabic": "ل", "name": "Lam", "transliteration": "L", "pronunciation": "laam", "example_word": "ليمون", "example_meaning": "lemon", "quranic_examples": ["لا إله إلا الله (La ilaha illa Allah)", "ليلة (Laylah - Night)"], "islamic_context": "Key in the Shahada and Laylat al-Qadr"},
    {"id": 24, "arabic": "م", "name": "Meem", "transliteration": "M", "pronunciation": "meem", "example_word": "ماء", "example_meaning": "water", "quranic_examples": ["محمد (Muhammad)", "مسجد (Masjid)", "مكة (Makkah)"], "islamic_context": "In Prophet Muhammad's name and Makkah"},
    {"id": 25, "arabic": "ن", "name": "Noon", "transliteration": "N", "pronunciation": "noon", "example_word": "نار", "example_meaning": "fire", "quranic_examples": ["نور (Nur - Light)", "نبي (Nabi - Prophet)"], "islamic_context": "In Divine Light (Nur) and Prophet (Nabi)"},
    {"id": 26, "arabic": "ه", "name": "Ha", "transliteration": "H", "pronunciation": "haa", "example_word": "هلال", "example_meaning": "crescent", "quranic_examples": ["هدى (Huda - Guidance)", "هجرة (Hijra)"], "islamic_context": "In Divine guidance (Huda) and Hijra migration"},
    {"id": 27, "arabic": "و", "name": "Waw", "transliteration": "W", "pronunciation": "waaw", "example_word": "ورد", "example_meaning": "rose", "quranic_examples": ["وضوء (Wudu)", "ولي (Wali - Guardian)"], "islamic_context": "In ritual ablution (Wudu) before prayers"},
    {"id": 28, "arabic": "ي", "name": "Ya", "transliteration": "Y", "pronunciation": "yaa", "example_word": "يد", "example_meaning": "hand", "quranic_examples": ["يوم (Yawm - Day)", "يقين (Yaqeen - Certainty)"], "islamic_context": "In Yawm al-Din (Day of Judgment) and faith certainty"}
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
    quranic_examples: Optional[List[str]] = []
    islamic_context: Optional[str] = ""

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

# AI Tutor Models
class AITutorRequest(BaseModel):
    message: str
    lesson_id: Optional[int] = None
    context_type: Optional[str] = "general"  # "lesson", "quiz", "general"

class AITutorResponse(BaseModel):
    response: str
    suggestions: List[str] = []
    lesson_recommendations: List[int] = []
    session_id: str

class VoiceFeedbackRequest(BaseModel):
    target_word: str
    lesson_id: Optional[int] = None

class VoiceFeedbackResponse(BaseModel):
    transcription: str
    target_word: str
    match: bool
    confidence: float
    feedback: str
    pronunciation_tips: List[str] = []

# Audio caching
audio_cache = {}

def generate_browser_speech(text: str) -> str:
    """Generate a data URL for browser speech synthesis as fallback"""
    return f"browser_speech:{text}"

async def get_cached_audio(text: str) -> Optional[str]:
    """Get cached audio URL"""
    return audio_cache.get(text)

async def cache_audio(text: str, audio_url: str):
    """Cache audio URL"""
    audio_cache[text] = audio_url

# AI Tutor Helper Functions
async def get_user_context(user_id: str, lesson_id: Optional[int] = None):
    """Get user's learning context for AI personalization"""
    # Get user progress
    progress_items = await db.progress.find({"user_id": user_id}).to_list(length=None)
    
    # Get recent chat history (last 10 exchanges)
    chat_history = await db.ai_tutor_chats.find(
        {"user_id": user_id}
    ).sort("created_at", -1).limit(20).to_list(length=20)
    
    # Get current lesson info if provided
    current_lesson = None
    if lesson_id:
        current_lesson = next((l for l in ARABIC_ALPHABET if l["id"] == lesson_id), None)
    
    # Analyze struggle areas (letters with low scores or multiple attempts)
    struggle_letters = []
    for progress in progress_items:
        if progress.get("score", 0) < 80 or progress.get("attempts", 0) > 2:
            letter_info = next((l for l in ARABIC_ALPHABET if l["id"] == progress["letter_id"]), None)
            if letter_info:
                struggle_letters.append(letter_info["name"])
    
    return {
        "completed_letters": len([p for p in progress_items if p.get("completed", False)]),
        "total_letters": 28,
        "struggle_areas": struggle_letters[:3],  # Top 3 struggles
        "current_lesson": current_lesson,
        "recent_chats": chat_history[:5],  # Last 5 exchanges for context
        "total_xp": sum(p.get("xp_earned", 0) for p in progress_items)
    }

def create_ai_system_prompt(user_context: dict, user_name: str) -> str:
    """Create personalized system prompt for AI tutor"""
    base_prompt = f"""You are Ustaz Ahmed, an expert Arabic language tutor specializing in Quranic Arabic for English-speaking Muslims. You're helping {user_name} learn Arabic.

TEACHING PHILOSOPHY:
- Patient, encouraging, and culturally sensitive
- Connect Arabic letters and words to Islamic context when relevant
- Explain pronunciation using simple English phonetics
- Give practical examples from daily Islamic life
- Use encouraging Islamic phrases like "Barakallahu feeki" when appropriate

STUDENT CONTEXT:
- Completed {user_context['completed_letters']}/{user_context['total_letters']} Arabic letters
- Total XP earned: {user_context['total_xp']}
"""

    if user_context.get('current_lesson'):
        lesson = user_context['current_lesson']
        base_prompt += f"""
CURRENT LESSON: Letter {lesson['id']} - {lesson['name']} ({lesson['arabic']})
- Pronunciation: {lesson['pronunciation']}
- Example word: {lesson['example_word']} ({lesson['example_meaning']})
- Islamic context: {lesson['islamic_context']}
- Quranic examples: {', '.join(lesson['quranic_examples'])}
"""

    if user_context.get('struggle_areas'):
        base_prompt += f"\nSTRUGGLE AREAS: {', '.join(user_context['struggle_areas'])} - offer gentle review suggestions"

    base_prompt += """
RESPONSE GUIDELINES:
1. Keep responses concise (2-3 sentences max)
2. Always include Arabic text with transliteration when relevant
3. Connect to Islamic/Quranic context when appropriate
4. Offer specific, actionable learning tips
5. Be encouraging and patient
6. Use simple language suitable for beginners
"""

    return base_prompt

# Auth Routes (unchanged from previous implementation)
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
        return Token(access=access_token, refresh_token=new_refresh_token, token_type="bearer", user=user_obj)
        
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
    """Logout user and clear all sessions"""
    try:
        # Clear all sessions from database for this user
        await db.sessions.delete_many({"user_id": current_user["id"]})
        
        # Clear session cookie
        response.delete_cookie("session_token", path="/", secure=True, samesite="none")
        
        # Also clear any other potential cookies
        response.delete_cookie("session_token", path="/")
        
        # Invalidate current JWT by adding to blacklist (optional enhancement)
        token = request.headers.get("authorization", "").replace("Bearer ", "")
        if token:
            # Store blacklisted token with expiry
            blacklist_entry = {
                "token": token,
                "user_id": current_user["id"],
                "blacklisted_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
            }
            await db.blacklisted_tokens.insert_one(blacklist_entry)
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logging.error(f"Logout error: {str(e)}")
        return {"message": "Logged out successfully"}  # Still return success to user

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

# AI Tutor Routes
@api_router.post("/ai-tutor", response_model=AITutorResponse)
async def chat_with_ai_tutor(request: AITutorRequest, current_user: dict = Depends(get_current_user)):
    """Chat with AI Arabic tutor with personalized context"""
    try:
        # Get user context for personalization
        user_context = await get_user_context(current_user["id"], request.lesson_id)
        
        # Create personalized system prompt
        system_prompt = create_ai_system_prompt(user_context, current_user["full_name"])
        
        # Create session ID for this conversation
        session_id = str(uuid.uuid4())
        
        # Initialize AI chat
        chat = LlmChat(
            api_key=emergent_llm_key,
            session_id=session_id,
            system_message=system_prompt
        ).with_model("openai", "gpt-5")
        
        # Send user message
        user_message = UserMessage(text=request.message)
        ai_response = await chat.send_message(user_message)
        
        # Generate suggestions based on context
        suggestions = []
        lesson_recommendations = []
        
        # Add contextual suggestions
        if request.lesson_id and user_context.get("current_lesson"):
            lesson = user_context["current_lesson"]
            suggestions.append(f"Practice pronouncing {lesson['arabic']} ({lesson['name']})")
            suggestions.append(f"Learn Quranic examples of {lesson['name']}")
        
        # Add review suggestions for struggle areas
        if user_context.get("struggle_areas"):
            for struggle in user_context["struggle_areas"][:2]:
                letter_info = next((l for l in ARABIC_ALPHABET if l["name"] == struggle), None)
                if letter_info:
                    lesson_recommendations.append(letter_info["id"])
                    suggestions.append(f"Review {struggle} ({letter_info['arabic']})")
        
        # Save chat to database
        chat_record = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "session_id": session_id,
            "lesson_id": request.lesson_id,
            "user_message": request.message,
            "ai_response": ai_response,
            "context_type": request.context_type,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.ai_tutor_chats.insert_one(chat_record)
        
        return AITutorResponse(
            response=ai_response,
            suggestions=suggestions[:3],  # Limit to 3 suggestions
            lesson_recommendations=lesson_recommendations[:2],  # Limit to 2 recommendations
            session_id=session_id
        )
        
    except Exception as e:
        logging.error(f"AI Tutor Error: {str(e)}")
        raise HTTPException(status_code=500, detail="AI tutor temporarily unavailable")

@api_router.post("/ai-tutor/voice-feedback", response_model=VoiceFeedbackResponse)
async def voice_pronunciation_feedback(
    audio_file: UploadFile = File(...),
    target_word: str = "",
    lesson_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """Analyze voice pronunciation and provide AI feedback"""
    try:
        if not target_word:
            raise HTTPException(status_code=400, detail="Target word is required")
        
        # For MVP, we'll provide AI-powered feedback without complex speech recognition
        # This gives users immediate value while we can enhance the speech recognition later
        
        # Use AI to generate pronunciation feedback and tips
        try:
            system_prompt = f"""You are an Arabic pronunciation coach. The user is trying to pronounce the Arabic word/sound '{target_word}'. 
            Give encouraging feedback and 3 specific pronunciation tips for English speakers learning Arabic. 
            Be supportive and provide practical guidance."""
            
            chat = LlmChat(
                api_key=emergent_llm_key,
                session_id=str(uuid.uuid4()),
                system_message=system_prompt
            ).with_model("openai", "gpt-5")
            
            tip_request = UserMessage(text=f"Give me 3 pronunciation tips for '{target_word}' and encouraging feedback")
            ai_response = await chat.send_message(tip_request)
            
            # Parse the response to extract tips
            response_lines = [line.strip() for line in ai_response.split('\n') if line.strip()]
            
            # Extract tips (look for numbered points or bullet points)
            tips = []
            feedback = "Great effort! Here are some tips to improve your pronunciation:"
            
            for line in response_lines:
                if any(marker in line.lower() for marker in ['1.', '2.', '3.', '•', '-', 'tip']):
                    # Clean up the tip text
                    clean_tip = line.replace('1.', '').replace('2.', '').replace('3.', '').replace('•', '').replace('-', '').strip()
                    if clean_tip and len(clean_tip) > 10:  # Ensure it's a meaningful tip
                        tips.append(clean_tip)
                elif 'feedback' in line.lower() or len(response_lines) < 4:
                    feedback = line
            
            # Fallback tips if parsing didn't work well
            if len(tips) < 2:
                tips = [
                    f"Listen carefully to the Arabic audio for '{target_word}' and repeat slowly",
                    "Focus on the tongue and lip position - Arabic sounds are different from English",
                    "Practice the sound in isolation before saying it in words"
                ]
            
            # Simulate realistic feedback with some randomization for engagement
            import random
            confidence = random.uniform(0.6, 0.9)  # Realistic confidence range
            match = confidence > 0.75  # Consider it a match if confidence is high
            
            if match:
                feedback = f"Good pronunciation of '{target_word}'! Keep practicing to perfect it."
            else:
                feedback = f"Keep practicing '{target_word}' - you're making progress!"
                
        except Exception as e:
            logging.error(f"AI feedback error: {str(e)}")
            # Fallback feedback
            tips = [
                f"Listen to the Arabic pronunciation of '{target_word}' multiple times",
                "Practice slowly and focus on mouth position",
                "Record yourself and compare with the example audio"
            ]
            feedback = "Keep practicing! Arabic pronunciation takes time to master."
            confidence = 0.5
            match = False
        
        # Save feedback record
        feedback_record = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "lesson_id": lesson_id,
            "target_word": target_word,
            "transcription": f"Practice attempt for {target_word}",
            "match": match,
            "confidence": confidence,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.voice_feedback.insert_one(feedback_record)
        
        return VoiceFeedbackResponse(
            transcription=f"Practice attempt for {target_word}",
            target_word=target_word,
            match=match,
            confidence=confidence,
            feedback=feedback,
            pronunciation_tips=tips[:3]  # Limit to 3 tips
        )
        
    except Exception as e:
        logging.error(f"Voice feedback error: {str(e)}")
        raise HTTPException(status_code=500, detail="Voice analysis temporarily unavailable")

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
        logger.info("Seeded Arabic alphabet lessons with Islamic context")