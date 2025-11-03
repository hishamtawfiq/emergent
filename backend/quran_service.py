import os
import time
import logging
import httpx
from typing import Any, Dict, List, Optional, Tuple

QURAN_API_BASE = os.environ.get("QURAN_API_BASE", "https://api.quran.com/api/v4")
CACHE_TTL = int(os.environ.get("QURAN_CACHE_TTL", "1800"))  # seconds (default 30 mins)

_logger = logging.getLogger(__name__)

# In-memory TTL cache: key -> (expires_at, value)
_cache: Dict[str, Tuple[float, Any]] = {}


def _cache_get(key: str):
    now = time.time()
    if key in _cache:
        exp, val = _cache[key]
        if now < exp:
            return val
        # expired
        try:
            del _cache[key]
        except Exception:
            pass
    return None


def _cache_set(key: str, value: Any, ttl: Optional[int] = None):
    exp = time.time() + (ttl if ttl is not None else CACHE_TTL)
    _cache[key] = (exp, value)


async def fetch_json(path: str, params: Optional[Dict[str, Any]] = None, retries: int = 2, timeout: float = 15.0) -> Any:
    url = f"{QURAN_API_BASE}{path}"
    attempt = 0
    last_exc: Optional[Exception] = None
    backoff = 1.5
    async with httpx.AsyncClient(timeout=timeout) as client:
        while attempt <= retries:
            try:
                resp = await client.get(url, params=params)
                if resp.status_code == 429:
                    # too many requests: exponential backoff
                    wait_for = min(5.0, backoff * (attempt + 1))
                    await _async_sleep(wait_for)
                    attempt += 1
                    continue
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                last_exc = e
                attempt += 1
                if attempt > retries:
                    break
                await _async_sleep(backoff * attempt)
    _logger.error(f"Quran API fetch failed for {url}: {last_exc}")
    raise last_exc if last_exc else RuntimeError("Quran API fetch failed")


async def _async_sleep(seconds: float):
    # small helper to avoid importing asyncio at top-level
    import asyncio
    await asyncio.sleep(seconds)


# Service functions
async def list_chapters() -> List[Dict[str, Any]]:
    cache_key = "chapters_list"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    data = await fetch_json("/chapters")
    chapters = []
    for c in data.get("chapters", []):
        chapters.append({
            "id": c.get("id"),
            "name_ar": c.get("name_arabic"),
            "name_en": (c.get("translated_name") or {}).get("name"),
            "revelation_place": c.get("revelation_place"),
            "verses_count": c.get("verses_count"),
            "bismillah_pre": c.get("bismillah_pre"),
            "name_simple": c.get("name_simple"),
        })
    _cache_set(cache_key, chapters)
    return chapters


async def list_tafsirs() -> List[Dict[str, Any]]:
    cache_key = "tafsirs_list"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    data = await fetch_json("/resources/tafsirs")
    tafsirs: List[Dict[str, Any]] = []
    for t in data.get("tafsirs", []):
        tafsirs.append({
            "id": t.get("id"),
            "slug": t.get("slug"),
            "language": t.get("language_name") or t.get("language"),
            "author": t.get("author_name") or t.get("author"),
            "translated_name": (t.get("translated_name") or {}).get("name"),
            "name": t.get("name"),
        })
    _cache_set(cache_key, tafsirs)
    return tafsirs


async def verses_by_chapter(chapter: int, translation_id: Optional[int] = None, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
    # Quran.com API uses `translations` as comma-separated list of IDs
    params: Dict[str, Any] = {
        "page": page,
        "per_page": per_page,
        "words": False,
    }
    if translation_id:
        params["translations"] = str(translation_id)

    data = await fetch_json(f"/verses/by_chapter/{chapter}", params=params)

    verses_out: List[Dict[str, Any]] = []
    for v in data.get("verses", []):
        # translations field is a list; pick first when present
        tr_text: Optional[str] = None
        translations = v.get("translations") or []
        if translations:
            tr_text = translations[0].get("text")
        verses_out.append({
            "id": v.get("id"),
            "verse_key": v.get("verse_key"),
            "text_uthmani": v.get("text_uthmani") or v.get("text_imlaei"),
            "translation": tr_text,
        })

    pagination = data.get("pagination") or {}
    return {
        "chapter": chapter,
        "page": pagination.get("current_page", page),
        "per_page": pagination.get("per_page", per_page),
        "total_pages": pagination.get("total_pages"),
        "verses": verses_out,
    }


async def tafsir_for_surah(tafsir_id: int, chapter: int) -> Dict[str, Any]:
    data = await fetch_json(f"/tafsirs/by_chapter/{tafsir_id}/{chapter}")
    out: List[Dict[str, Any]] = []
    for t in data.get("tafsirs", []):
        out.append({
            "verse_key": t.get("verse_key"),
            "text": t.get("text"),
            "resource_id": t.get("resource_id") or tafsir_id,
            "resource_name": t.get("resource_name"),
        })
    return {"chapter": chapter, "tafsir_id": tafsir_id, "items": out}


async def tafsir_for_ayah(tafsir_id: int, ayah_key: str) -> Dict[str, Any]:
    data = await fetch_json(f"/tafsirs/{tafsir_id}/by_ayah/{ayah_key}")
    tafsir = data.get("tafsir") or {}
    return {
        "verse_key": tafsir.get("verse_key") or ayah_key,
        "text": tafsir.get("text"),
        "resource_id": tafsir.get("resource_id") or tafsir_id,
        "resource_name": tafsir.get("resource_name"),
    }


async def audio_for_chapter(chapter: int, reciter_id: int) -> Dict[str, Any]:
    # Quran.com v4: /chapter_recitations/{reciter_id}/{chapter}
    data = await fetch_json(f"/chapter_recitations/{reciter_id}/{chapter}")
    audio = data.get("audio_file") or {}
    return {
        "chapter": chapter,
        "reciter_id": reciter_id,
        "audio_url": audio.get("url"),
        "format": audio.get("format"),
        "duration": audio.get("duration"),
        "audio_file": audio,
    }
