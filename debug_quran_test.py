#!/usr/bin/env python3

import requests
import json

def test_quran_endpoints():
    base_url = "https://maqraa-ai.preview.emergentagent.com/api"
    
    print("=== Testing Quran API Endpoints ===\n")
    
    # Test tafsir endpoint
    print("1. Testing tafsir endpoint...")
    try:
        response = requests.get(f"{base_url}/quran/tafsir/1/ayah/2:255", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test audio endpoint
    print("2. Testing audio endpoint...")
    try:
        response = requests.get(f"{base_url}/quran/chapters/1/audio?reciter_id=7", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            print(f"Full response: {json.dumps(data, indent=2)}")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test TTS endpoint
    print("3. Testing TTS endpoint...")
    try:
        response = requests.post(f"{base_url}/tts/generate", 
                               json={"text": "الف", "voice_id": "21m00Tcm4TlvDq8ikWAM"}, 
                               timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            print(f"Audio URL type: {type(data.get('audio_url'))}")
            audio_url = data.get('audio_url', '')
            if audio_url.startswith('data:audio/mpeg;base64,'):
                print("✅ Valid base64 audio URL")
            elif audio_url.startswith('browser_speech:'):
                print("✅ Valid browser speech URL")
            else:
                print(f"❌ Unexpected audio URL format: {audio_url[:100]}...")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_quran_endpoints()