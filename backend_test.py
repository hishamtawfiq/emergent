#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import time

class ArabicLMSAPITester:
    def __init__(self, base_url="https://maqraa-ai.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test user data
        self.test_user = {
            "full_name": f"Test User {datetime.now().strftime('%H%M%S')}",
            "email": f"test_{datetime.now().strftime('%H%M%S')}@example.com",
            "password": "TestPass123!"
        }

    def log_test(self, name, success, status_code=None, error=None, response_data=None):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED (Status: {status_code})")
        else:
            print(f"❌ {name} - FAILED (Status: {status_code}, Error: {error})")
        
        self.test_results.append({
            "test_name": name,
            "success": success,
            "status_code": status_code,
            "error": error,
            "response_data": response_data
        })

    def make_request(self, method, endpoint, data=None, auth_required=False):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if auth_required and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            
            return response
        except requests.exceptions.RequestException as e:
            return None

    def test_health_check(self):
        """Test basic API connectivity"""
        print("\n🔍 Testing API Health Check...")
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            success = response.status_code == 200
            self.log_test("API Health Check", success, response.status_code)
            return success
        except Exception as e:
            self.log_test("API Health Check", False, error=str(e))
            return False

    def test_user_registration(self):
        """Test user registration endpoint"""
        print("\n🔍 Testing User Registration...")
        response = self.make_request('POST', 'auth/register', self.test_user)
        
        if response is None:
            self.log_test("User Registration", False, error="Request failed")
            return False
        
        success = response.status_code == 200
        if success:
            try:
                data = response.json()
                self.token = data.get('access_token')
                self.user_data = data.get('user')
                self.log_test("User Registration", True, response.status_code, response_data=data)
            except Exception as e:
                self.log_test("User Registration", False, response.status_code, f"JSON parse error: {e}")
                return False
        else:
            try:
                error_detail = response.json().get('detail', 'Unknown error')
            except:
                error_detail = response.text
            self.log_test("User Registration", False, response.status_code, error_detail)
        
        return success

    def test_user_login(self):
        """Test user login endpoint"""
        print("\n🔍 Testing User Login...")
        login_data = {
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        }
        
        response = self.make_request('POST', 'auth/login', login_data)
        
        if response is None:
            self.log_test("User Login", False, error="Request failed")
            return False
        
        success = response.status_code == 200
        if success:
            try:
                data = response.json()
                self.token = data.get('access_token')
                self.user_data = data.get('user')
                self.log_test("User Login", True, response.status_code, response_data=data)
            except Exception as e:
                self.log_test("User Login", False, response.status_code, f"JSON parse error: {e}")
                return False
        else:
            try:
                error_detail = response.json().get('detail', 'Unknown error')
            except:
                error_detail = response.text
            self.log_test("User Login", False, response.status_code, error_detail)
        
        return success

    def test_get_current_user(self):
        """Test get current user endpoint"""
        print("\n🔍 Testing Get Current User...")
        response = self.make_request('GET', 'auth/me', auth_required=True)
        
        if response is None:
            self.log_test("Get Current User", False, error="Request failed")
            return False
        
        success = response.status_code == 200
        if success:
            try:
                data = response.json()
                self.log_test("Get Current User", True, response.status_code, response_data=data)
            except Exception as e:
                self.log_test("Get Current User", False, response.status_code, f"JSON parse error: {e}")
                return False
        else:
            try:
                error_detail = response.json().get('detail', 'Unknown error')
            except:
                error_detail = response.text
            self.log_test("Get Current User", False, response.status_code, error_detail)
        
        return success

    def test_get_lessons(self):
        """Test get all lessons endpoint"""
        print("\n🔍 Testing Get All Lessons...")
        response = self.make_request('GET', 'lessons')
        
        if response is None:
            self.log_test("Get All Lessons", False, error="Request failed")
            return False
        
        success = response.status_code == 200
        if success:
            try:
                data = response.json()
                lesson_count = len(data)
                expected_count = 28  # 28 Arabic letters
                if lesson_count == expected_count:
                    self.log_test("Get All Lessons", True, response.status_code, 
                                response_data=f"Found {lesson_count} lessons")
                else:
                    self.log_test("Get All Lessons", False, response.status_code, 
                                f"Expected {expected_count} lessons, got {lesson_count}")
                    return False
            except Exception as e:
                self.log_test("Get All Lessons", False, response.status_code, f"JSON parse error: {e}")
                return False
        else:
            try:
                error_detail = response.json().get('detail', 'Unknown error')
            except:
                error_detail = response.text
            self.log_test("Get All Lessons", False, response.status_code, error_detail)
        
        return success

    def test_get_specific_lesson(self):
        """Test get specific lesson endpoint"""
        print("\n🔍 Testing Get Specific Lesson...")
        letter_id = 1  # Test with first letter (Alif)
        response = self.make_request('GET', f'lessons/{letter_id}')
        
        if response is None:
            self.log_test("Get Specific Lesson", False, error="Request failed")
            return False
        
        success = response.status_code == 200
        if success:
            try:
                data = response.json()
                required_fields = ['id', 'arabic', 'name', 'transliteration', 'pronunciation', 'example_word', 'example_meaning']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test("Get Specific Lesson", True, response.status_code, 
                                response_data=f"Letter: {data.get('arabic')} - {data.get('name')}")
                else:
                    self.log_test("Get Specific Lesson", False, response.status_code, 
                                f"Missing fields: {missing_fields}")
                    return False
            except Exception as e:
                self.log_test("Get Specific Lesson", False, response.status_code, f"JSON parse error: {e}")
                return False
        else:
            try:
                error_detail = response.json().get('detail', 'Unknown error')
            except:
                error_detail = response.text
            self.log_test("Get Specific Lesson", False, response.status_code, error_detail)
        
        return success

    def test_tts_generation(self):
        """Test TTS generation endpoint"""
        print("\n🔍 Testing TTS Generation...")
        tts_data = {
            "text": "الف",  # Arabic letter Alif
            "voice_id": "21m00Tcm4TlvDq8ikWAM"
        }
        
        response = self.make_request('POST', 'tts/generate', tts_data)
        
        if response is None:
            self.log_test("TTS Generation", False, error="Request failed")
            return False
        
        success = response.status_code == 200
        if success:
            try:
                data = response.json()
                audio_url = data.get('audio_url', '')
                # Accept both ElevenLabs base64 and browser speech fallback
                if (audio_url.startswith('data:audio/mpeg;base64,') or 
                    audio_url.startswith('browser_speech:')):
                    self.log_test("TTS Generation", True, response.status_code, 
                                response_data=f"Audio generated successfully ({data.get('source', 'unknown')})")
                else:
                    self.log_test("TTS Generation", False, response.status_code, 
                                f"Invalid audio URL format: {audio_url[:50]}...")
                    return False
            except Exception as e:
                self.log_test("TTS Generation", False, response.status_code, f"JSON parse error: {e}")
                return False
        else:
            try:
                error_detail = response.json().get('detail', 'Unknown error')
            except:
                error_detail = response.text
            self.log_test("TTS Generation", False, response.status_code, error_detail)
        
        return success

    def test_save_progress(self):
        """Test save progress endpoint"""
        print("\n🔍 Testing Save Progress...")
        if not self.token:
            self.log_test("Save Progress", False, error="No authentication token")
            return False
        
        progress_data = {
            "letter_id": 1,
            "completed": True,
            "score": 95,
            "attempts": 1,
            "xp_earned": 50
        }
        
        response = self.make_request('POST', 'progress', progress_data, auth_required=True)
        
        if response is None:
            self.log_test("Save Progress", False, error="Request failed")
            return False
        
        success = response.status_code == 200
        if success:
            try:
                data = response.json()
                self.log_test("Save Progress", True, response.status_code, 
                            response_data=f"Progress saved for letter {data.get('letter_id')}")
            except Exception as e:
                self.log_test("Save Progress", False, response.status_code, f"JSON parse error: {e}")
                return False
        else:
            try:
                error_detail = response.json().get('detail', 'Unknown error')
            except:
                error_detail = response.text
            self.log_test("Save Progress", False, response.status_code, error_detail)
        
        return success

    def test_get_progress(self):
        """Test get progress endpoint"""
        print("\n🔍 Testing Get Progress...")
        if not self.token:
            self.log_test("Get Progress", False, error="No authentication token")
            return False
        
        response = self.make_request('GET', 'progress', auth_required=True)
        
        if response is None:
            self.log_test("Get Progress", False, error="Request failed")
            return False
        
        success = response.status_code == 200
        if success:
            try:
                data = response.json()
                self.log_test("Get Progress", True, response.status_code, 
                            response_data=f"Found {len(data)} progress records")
            except Exception as e:
                self.log_test("Get Progress", False, response.status_code, f"JSON parse error: {e}")
                return False
        else:
            try:
                error_detail = response.json().get('detail', 'Unknown error')
            except:
                error_detail = response.text
            self.log_test("Get Progress", False, response.status_code, error_detail)
        
        return success

    def test_quiz_answer(self):
        """Test quiz answer endpoint"""
        print("\n🔍 Testing Quiz Answer...")
        if not self.token:
            self.log_test("Quiz Answer", False, error="No authentication token")
            return False
        
        quiz_data = {
            "letter_id": 1,
            "selected_letter_id": 1  # Correct answer
        }
        
        response = self.make_request('POST', 'quiz/answer', quiz_data, auth_required=True)
        
        if response is None:
            self.log_test("Quiz Answer", False, error="Request failed")
            return False
        
        success = response.status_code == 200
        if success:
            try:
                data = response.json()
                required_fields = ['correct', 'xp_earned', 'message']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test("Quiz Answer", True, response.status_code, 
                                response_data=f"Correct: {data.get('correct')}, XP: {data.get('xp_earned')}")
                else:
                    self.log_test("Quiz Answer", False, response.status_code, 
                                f"Missing fields: {missing_fields}")
                    return False
            except Exception as e:
                self.log_test("Quiz Answer", False, response.status_code, f"JSON parse error: {e}")
                return False
        else:
            try:
                error_detail = response.json().get('detail', 'Unknown error')
            except:
                error_detail = response.text
            self.log_test("Quiz Answer", False, response.status_code, error_detail)
        
        return success

    def test_quran_chapters(self):
        """Test Quran chapters endpoint"""
        print("\n🔍 Testing Quran Chapters...")
        response = self.make_request('GET', 'quran/chapters')
        
        if response is None:
            self.log_test("Quran Chapters", False, error="Request failed")
            return False
        
        success = response.status_code == 200
        if success:
            try:
                data = response.json()
                chapters = data.get('chapters', [])
                
                # Expect 114 chapters
                if len(chapters) == 114:
                    # Check required fields in first chapter
                    if chapters:
                        first_chapter = chapters[0]
                        required_fields = ['id', 'name_ar', 'name_en']
                        missing_fields = [field for field in required_fields if field not in first_chapter]
                        
                        if not missing_fields:
                            self.log_test("Quran Chapters", True, response.status_code, 
                                        response_data=f"Found {len(chapters)} chapters with required fields")
                        else:
                            self.log_test("Quran Chapters", False, response.status_code, 
                                        f"Missing fields in chapters: {missing_fields}")
                            return False
                    else:
                        self.log_test("Quran Chapters", False, response.status_code, "Empty chapters array")
                        return False
                else:
                    self.log_test("Quran Chapters", False, response.status_code, 
                                f"Expected 114 chapters, got {len(chapters)}")
                    return False
            except Exception as e:
                self.log_test("Quran Chapters", False, response.status_code, f"JSON parse error: {e}")
                return False
        else:
            try:
                error_detail = response.json().get('detail', 'Unknown error')
            except:
                error_detail = response.text
            self.log_test("Quran Chapters", False, response.status_code, error_detail)
        
        return success

    def test_quran_verses(self):
        """Test Quran verses endpoint"""
        print("\n🔍 Testing Quran Verses...")
        response = self.make_request('GET', 'quran/chapters/1/verses?per_page=7')
        
        if response is None:
            self.log_test("Quran Verses", False, error="Request failed")
            return False
        
        success = response.status_code == 200
        if success:
            try:
                data = response.json()
                verses = data.get('verses', [])
                
                # Expect 7 verses
                if len(verses) == 7:
                    # Check required fields in first verse
                    if verses:
                        first_verse = verses[0]
                        required_fields = ['verse_key', 'text_uthmani']
                        missing_fields = [field for field in required_fields if field not in first_verse]
                        
                        if not missing_fields:
                            # Check if translation is present (should be Saheeh Intl, id=20 default)
                            has_translation = first_verse.get('translation') is not None
                            if has_translation:
                                self.log_test("Quran Verses", True, response.status_code, 
                                            response_data=f"Found {len(verses)} verses with translation")
                            else:
                                self.log_test("Quran Verses", False, response.status_code, 
                                            "Translation not present in verses")
                                return False
                        else:
                            self.log_test("Quran Verses", False, response.status_code, 
                                        f"Missing fields in verses: {missing_fields}")
                            return False
                    else:
                        self.log_test("Quran Verses", False, response.status_code, "Empty verses array")
                        return False
                else:
                    self.log_test("Quran Verses", False, response.status_code, 
                                f"Expected 7 verses, got {len(verses)}")
                    return False
            except Exception as e:
                self.log_test("Quran Verses", False, response.status_code, f"JSON parse error: {e}")
                return False
        else:
            try:
                error_detail = response.json().get('detail', 'Unknown error')
            except:
                error_detail = response.text
            self.log_test("Quran Verses", False, response.status_code, error_detail)
        
        return success

    def test_quran_tafsirs(self):
        """Test Quran tafsirs endpoint"""
        print("\n🔍 Testing Quran Tafsirs...")
        response = self.make_request('GET', 'quran/resources/tafsirs')
        
        if response is None:
            self.log_test("Quran Tafsirs", False, error="Request failed")
            return False
        
        success = response.status_code == 200
        if success:
            try:
                data = response.json()
                tafsirs = data.get('tafsirs', [])
                
                # Expect non-empty tafsirs array
                if len(tafsirs) > 0:
                    # Check required fields in first tafsir
                    first_tafsir = tafsirs[0]
                    required_fields = ['id']
                    missing_fields = [field for field in required_fields if field not in first_tafsir]
                    
                    if not missing_fields:
                        # Check if slug or language is present
                        has_slug_or_lang = first_tafsir.get('slug') or first_tafsir.get('language')
                        if has_slug_or_lang:
                            self.log_test("Quran Tafsirs", True, response.status_code, 
                                        response_data=f"Found {len(tafsirs)} tafsirs")
                        else:
                            self.log_test("Quran Tafsirs", False, response.status_code, 
                                        "No slug or language field in tafsirs")
                            return False
                    else:
                        self.log_test("Quran Tafsirs", False, response.status_code, 
                                    f"Missing fields in tafsirs: {missing_fields}")
                        return False
                else:
                    self.log_test("Quran Tafsirs", False, response.status_code, "Empty tafsirs array")
                    return False
            except Exception as e:
                self.log_test("Quran Tafsirs", False, response.status_code, f"JSON parse error: {e}")
                return False
        else:
            try:
                error_detail = response.json().get('detail', 'Unknown error')
            except:
                error_detail = response.text
            self.log_test("Quran Tafsirs", False, response.status_code, error_detail)
        
        return success

    def test_quran_tafsir_ayah(self):
        """Test Quran tafsir for specific ayah endpoint"""
        print("\n🔍 Testing Quran Tafsir for Ayah...")
        # Test Ayat al-Kursi (2:255) with resource 1
        response = self.make_request('GET', 'quran/tafsir/1/ayah/2:255')
        
        if response is None:
            self.log_test("Quran Tafsir Ayah", False, error="Request failed")
            return False
        
        success = response.status_code == 200
        if success:
            try:
                data = response.json()
                
                # Check if tafsir text is present
                tafsir_text = data.get('text')
                if tafsir_text and len(tafsir_text.strip()) > 0:
                    self.log_test("Quran Tafsir Ayah", True, response.status_code, 
                                response_data=f"Tafsir text present for 2:255")
                else:
                    self.log_test("Quran Tafsir Ayah", False, response.status_code, 
                                "No tafsir text found for ayah 2:255")
                    return False
            except Exception as e:
                self.log_test("Quran Tafsir Ayah", False, response.status_code, f"JSON parse error: {e}")
                return False
        else:
            try:
                error_detail = response.json().get('detail', 'Unknown error')
            except:
                error_detail = response.text
            self.log_test("Quran Tafsir Ayah", False, response.status_code, error_detail)
        
        return success

    def test_quran_audio_no_reciter(self):
        """Test Quran audio endpoint without reciter_id (should return 400)"""
        print("\n🔍 Testing Quran Audio without reciter_id...")
        response = self.make_request('GET', 'quran/chapters/1/audio')
        
        if response is None:
            self.log_test("Quran Audio No Reciter", False, error="Request failed")
            return False
        
        # Expect 400 Bad Request
        success = response.status_code == 400
        if success:
            self.log_test("Quran Audio No Reciter", True, response.status_code, 
                        response_data="Correctly returned 400 for missing reciter_id")
        else:
            try:
                error_detail = response.json().get('detail', 'Unknown error')
            except:
                error_detail = response.text
            self.log_test("Quran Audio No Reciter", False, response.status_code, 
                        f"Expected 400, got {response.status_code}: {error_detail}")
        
        return success

    def test_quran_audio_with_reciter(self):
        """Test Quran audio endpoint with reciter_id"""
        print("\n🔍 Testing Quran Audio with reciter_id...")
        # Try with reciter_id 7
        response = self.make_request('GET', 'quran/chapters/1/audio?reciter_id=7')
        
        if response is None:
            self.log_test("Quran Audio With Reciter", False, error="Request failed")
            return False
        
        success = response.status_code == 200
        if success:
            try:
                data = response.json()
                
                # Check if audio URL is present in audio_file.audio_url
                audio_file = data.get('audio_file', {})
                audio_url = audio_file.get('audio_url') or data.get('audio_url')
                
                if audio_url and len(audio_url.strip()) > 0:
                    self.log_test("Quran Audio With Reciter", True, response.status_code, 
                                response_data=f"Audio URL present for reciter 7: {audio_url[:50]}...")
                else:
                    self.log_test("Quran Audio With Reciter", False, response.status_code, 
                                f"No audio URL found in response: {list(data.keys())}")
                    return False
            except Exception as e:
                self.log_test("Quran Audio With Reciter", False, response.status_code, f"JSON parse error: {e}")
                return False
        else:
            try:
                error_detail = response.json().get('detail', 'Unknown error')
            except:
                error_detail = response.text
            self.log_test("Quran Audio With Reciter", False, response.status_code, error_detail)
        
        return success

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Arabic LMS API Testing...")
        print(f"Base URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        print("=" * 60)
        
        # Test sequence
        tests = [
            self.test_health_check,
            self.test_get_lessons,
            self.test_get_specific_lesson,
            self.test_user_registration,
            self.test_user_login,
            self.test_get_current_user,
            self.test_tts_generation,
            self.test_save_progress,
            self.test_get_progress,
            self.test_quiz_answer,
            # Quran API tests
            self.test_quran_chapters,
            self.test_quran_verses,
            self.test_quran_tafsirs,
            self.test_quran_tafsir_ayah,
            self.test_quran_audio_no_reciter,
            self.test_quran_audio_with_reciter
        ]
        
        for test in tests:
            try:
                test()
                time.sleep(0.5)  # Small delay between tests
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {str(e)}")
                self.log_test(test.__name__, False, error=f"Test crashed: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%" if self.tests_run > 0 else "0%")
        
        # Print failed tests
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test_name']}: {test['error']}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = ArabicLMSAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_tests': tester.tests_run,
            'passed_tests': tester.tests_passed,
            'success_rate': (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0,
            'test_results': tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())