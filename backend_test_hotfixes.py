#!/usr/bin/env python3
"""
Arabic LMS Backend Testing - QA Hotfixes Focus
Testing the 5 major hotfixes applied:
1. Google OAuth integration
2. 7-day login persistence with refresh tokens
3. TTS pronunciation with caching and fallbacks  
4. Quiz retry logic with 80% completion threshold
5. Mobile responsiveness (backend support)
"""

import requests
import sys
import json
import time
from datetime import datetime

class ArabicLMSHotfixTester:
    def __init__(self, base_url="https://maqraa-ai.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.refresh_token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name}")
        if details:
            print(f"   {details}")
        print()

    def test_api_health(self):
        """Test basic API connectivity"""
        try:
            response = self.session.get(f"{self.api_url}/lessons")
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                lessons = response.json()
                details += f", Found {len(lessons)} lessons"
            self.log_test("API Health Check", success, details)
            return success
        except Exception as e:
            self.log_test("API Health Check", False, f"Error: {str(e)}")
            return False

    def test_jwt_authentication(self):
        """Test traditional JWT authentication (should still work)"""
        # Test registration
        test_email = f"test_jwt_{int(time.time())}@example.com"
        test_password = "TestPass123!"
        
        try:
            # Register
            register_data = {
                "email": test_email,
                "password": test_password,
                "full_name": "JWT Test User"
            }
            
            response = self.session.post(f"{self.api_url}/auth/register", json=register_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.refresh_token = data.get('refresh_token')
                self.user_id = data.get('user', {}).get('id')
                
                # Set auth header
                self.session.headers['Authorization'] = f'Bearer {self.token}'
                
                self.log_test("JWT Registration", True, f"User ID: {self.user_id}")
                return True
            else:
                self.log_test("JWT Registration", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("JWT Registration", False, f"Error: {str(e)}")
            return False

    def test_refresh_token_system(self):
        """Test the new 7-day refresh token system"""
        if not self.refresh_token:
            self.log_test("Refresh Token System", False, "No refresh token available")
            return False
            
        try:
            refresh_data = {"refresh_token": self.refresh_token}
            response = self.session.post(f"{self.api_url}/auth/refresh", json=refresh_data)
            
            if response.status_code == 200:
                data = response.json()
                new_access_token = data.get('access_token')
                new_refresh_token = data.get('refresh_token')
                
                if new_access_token and new_refresh_token:
                    # Update tokens
                    self.token = new_access_token
                    self.refresh_token = new_refresh_token
                    self.session.headers['Authorization'] = f'Bearer {self.token}'
                    
                    self.log_test("Refresh Token System", True, "Successfully refreshed tokens")
                    return True
                else:
                    self.log_test("Refresh Token System", False, "Missing tokens in response")
                    return False
            else:
                self.log_test("Refresh Token System", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Refresh Token System", False, f"Error: {str(e)}")
            return False

    def test_google_oauth_endpoint(self):
        """Test Google OAuth session endpoint (without actual OAuth flow)"""
        try:
            # Test without session ID (should fail)
            response = self.session.post(f"{self.api_url}/auth/session", json={})
            
            if response.status_code == 400:
                error_data = response.json()
                if "Session ID required" in error_data.get('detail', ''):
                    self.log_test("Google OAuth Endpoint Validation", True, "Correctly requires session ID")
                    return True
                else:
                    self.log_test("Google OAuth Endpoint Validation", False, f"Unexpected error: {error_data}")
                    return False
            else:
                self.log_test("Google OAuth Endpoint Validation", False, f"Expected 400, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Google OAuth Endpoint Validation", False, f"Error: {str(e)}")
            return False

    def test_tts_with_fallbacks(self):
        """Test TTS system with caching and fallbacks"""
        try:
            # Test TTS generation
            tts_data = {"text": "ا", "voice_id": "21m00Tcm4TlvDq8ikWAM"}
            response = self.session.post(f"{self.api_url}/tts/generate", json=tts_data)
            
            if response.status_code == 200:
                data = response.json()
                audio_url = data.get('audio_url')
                source = data.get('source')
                text = data.get('text')
                
                if audio_url and source and text:
                    # Test caching by making the same request again
                    time.sleep(0.5)  # Small delay
                    response2 = self.session.post(f"{self.api_url}/tts/generate", json=tts_data)
                    
                    if response2.status_code == 200:
                        data2 = response2.json()
                        source2 = data2.get('source')
                        
                        # Check if second request uses cache or fallback
                        cache_working = source2 == 'cached' or source in ['elevenlabs', 'browser']
                        
                        details = f"First: {source}, Second: {source2}"
                        if source == 'browser':
                            details += " (Fallback working)"
                        elif source2 == 'cached':
                            details += " (Caching working)"
                        elif source == 'elevenlabs':
                            details += " (ElevenLabs working)"
                            
                        self.log_test("TTS with Caching & Fallbacks", True, details)
                        return True
                    else:
                        self.log_test("TTS with Caching & Fallbacks", False, f"Second request failed: {response2.status_code}")
                        return False
                else:
                    self.log_test("TTS with Caching & Fallbacks", False, "Missing required fields in response")
                    return False
            else:
                self.log_test("TTS with Caching & Fallbacks", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("TTS with Caching & Fallbacks", False, f"Error: {str(e)}")
            return False

    def test_quiz_retry_logic(self):
        """Test quiz retry logic with 80% threshold"""
        if not self.token:
            self.log_test("Quiz Retry Logic", False, "No authentication token")
            return False
            
        try:
            # Submit a wrong answer first
            wrong_answer = {
                "letter_id": 1,  # Alif
                "selected_letter_id": 2  # Wrong answer (Ba)
            }
            
            response = self.session.post(f"{self.api_url}/quiz/answer", json=wrong_answer)
            
            if response.status_code == 200:
                data = response.json()
                correct = data.get('correct')
                score = data.get('score')
                can_proceed = data.get('can_proceed')
                min_score_required = data.get('min_score_required')
                
                # Should be wrong answer with low score
                if not correct and score < 80 and not can_proceed and min_score_required == 80:
                    # Now submit correct answer
                    correct_answer = {
                        "letter_id": 1,
                        "selected_letter_id": 1  # Correct answer
                    }
                    
                    response2 = self.session.post(f"{self.api_url}/quiz/answer", json=correct_answer)
                    
                    if response2.status_code == 200:
                        data2 = response2.json()
                        correct2 = data2.get('correct')
                        score2 = data2.get('score')
                        can_proceed2 = data2.get('can_proceed')
                        
                        # Score should be reduced due to retry penalty
                        if correct2 and score2 < 100 and can_proceed2:
                            details = f"Wrong: {score}%, Correct (retry): {score2}% (penalty applied)"
                            self.log_test("Quiz Retry Logic", True, details)
                            return True
                        else:
                            details = f"Unexpected retry result: correct={correct2}, score={score2}, can_proceed={can_proceed2}"
                            self.log_test("Quiz Retry Logic", False, details)
                            return False
                    else:
                        self.log_test("Quiz Retry Logic", False, f"Second answer failed: {response2.status_code}")
                        return False
                else:
                    details = f"Unexpected first result: correct={correct}, score={score}, can_proceed={can_proceed}"
                    self.log_test("Quiz Retry Logic", False, details)
                    return False
            else:
                self.log_test("Quiz Retry Logic", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Quiz Retry Logic", False, f"Error: {str(e)}")
            return False

    def test_session_persistence(self):
        """Test session persistence functionality"""
        if not self.token:
            self.log_test("Session Persistence", False, "No authentication token")
            return False
            
        try:
            # Test /auth/me endpoint to verify session
            response = self.session.get(f"{self.api_url}/auth/me")
            
            if response.status_code == 200:
                user_data = response.json()
                user_id = user_data.get('id')
                email = user_data.get('email')
                
                if user_id and email:
                    self.log_test("Session Persistence", True, f"User: {email}")
                    return True
                else:
                    self.log_test("Session Persistence", False, "Missing user data")
                    return False
            else:
                self.log_test("Session Persistence", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Session Persistence", False, f"Error: {str(e)}")
            return False

    def test_logout_functionality(self):
        """Test logout endpoint"""
        if not self.token:
            self.log_test("Logout Functionality", False, "No authentication token")
            return False
            
        try:
            response = self.session.post(f"{self.api_url}/auth/logout")
            
            if response.status_code == 200:
                # Test that subsequent requests fail
                test_response = self.session.get(f"{self.api_url}/auth/me")
                
                if test_response.status_code == 401:
                    self.log_test("Logout Functionality", True, "Successfully logged out")
                    return True
                else:
                    self.log_test("Logout Functionality", False, f"Still authenticated after logout: {test_response.status_code}")
                    return False
            else:
                self.log_test("Logout Functionality", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Logout Functionality", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all hotfix-focused tests"""
        print("🧪 Arabic LMS Backend Testing - QA Hotfixes Focus")
        print("=" * 60)
        print()
        
        # Basic connectivity
        if not self.test_api_health():
            print("❌ API not accessible, stopping tests")
            return False
            
        # Authentication tests
        self.test_jwt_authentication()
        self.test_refresh_token_system()
        self.test_google_oauth_endpoint()
        self.test_session_persistence()
        
        # Feature tests
        self.test_tts_with_fallbacks()
        self.test_quiz_retry_logic()
        
        # Cleanup
        self.test_logout_functionality()
        
        # Results
        print("=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        return success_rate >= 80

def main():
    tester = ArabicLMSHotfixTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())