#!/usr/bin/env python3
"""
Backend API Testing for Nirman LLM Keys Feature
Tests all LLM Keys endpoints and user authentication
"""

import requests
import sys
import json
from datetime import datetime

class NirmanAPITester:
    def __init__(self, base_url="https://c7aa30db-9fa8-4862-9acc-e279703c4bf6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make API request with error handling"""
        url = f"{self.api_base}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
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
            else:
                return False, {}, f"Unsupported method: {method}"

            success = response.status_code == expected_status
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = {"raw_response": response.text}

            if not success:
                details = f"Expected {expected_status}, got {response.status_code}. Response: {response_data}"
                return False, response_data, details

            return True, response_data, ""

        except requests.exceptions.RequestException as e:
            return False, {}, f"Request failed: {str(e)}"

    def test_user_registration(self):
        """Test user registration"""
        test_email = f"test@nirman.tech"
        test_password = "test123"
        
        success, response, details = self.make_request(
            'POST', 'auth/register', 
            {
                "email": test_email,
                "name": "Test User",
                "password": test_password
            },
            expected_status=201
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response.get('user', {}).get('id')
            self.log_test("User Registration", True)
            return True
        else:
            # Try login if user already exists
            return self.test_user_login()

    def test_user_login(self):
        """Test user login"""
        success, response, details = self.make_request(
            'POST', 'auth/login',
            {
                "email": "test@nirman.tech",
                "password": "test123"
            }
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response.get('user', {}).get('id')
            self.log_test("User Login", True)
            return True
        else:
            self.log_test("User Login", False, details)
            return False

    def test_llm_keys_pricing_info(self):
        """Test GET /api/llm-keys/pricing/info"""
        success, response, details = self.make_request('GET', 'llm-keys/pricing/info')
        
        if success:
            required_fields = ['currency', 'pricing_per_1k_tokens', 'credit_packages', 'free_tier']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                self.log_test("LLM Keys Pricing Info", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("LLM Keys Pricing Info", True)
                return True
        else:
            self.log_test("LLM Keys Pricing Info", False, details)
        return False

    def test_llm_keys_overview_stats(self):
        """Test GET /api/llm-keys/overview/stats"""
        success, response, details = self.make_request('GET', 'llm-keys/overview/stats')
        
        if success:
            required_fields = ['total_keys', 'active_keys', 'total_credits_balance', 'supported_providers']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                self.log_test("LLM Keys Overview Stats", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("LLM Keys Overview Stats", True)
                return True
        else:
            self.log_test("LLM Keys Overview Stats", False, details)
        return False

    def test_llm_keys_list_empty(self):
        """Test GET /api/llm-keys (should be empty initially)"""
        success, response, details = self.make_request('GET', 'llm-keys')
        
        if success and isinstance(response, list):
            self.log_test("LLM Keys List (Empty)", True)
            return True
        else:
            self.log_test("LLM Keys List (Empty)", False, details)
        return False

    def test_llm_keys_create(self):
        """Test POST /api/llm-keys"""
        success, response, details = self.make_request(
            'POST', 'llm-keys',
            {
                "name": "Test Key",
                "allowed_providers": ["openai", "gemini", "claude"]
            },
            expected_status=200
        )
        
        if success and 'key' in response and 'key_id' in response:
            self.test_key_id = response['key_id']
            self.test_key = response['key']
            self.log_test("LLM Keys Create", True)
            return True
        else:
            self.log_test("LLM Keys Create", False, details)
        return False

    def test_llm_keys_list_with_data(self):
        """Test GET /api/llm-keys (should have data after creation)"""
        success, response, details = self.make_request('GET', 'llm-keys')
        
        if success and isinstance(response, list) and len(response) > 0:
            key = response[0]
            required_fields = ['id', 'name', 'key_preview', 'is_active', 'credits_balance']
            missing_fields = [field for field in required_fields if field not in key]
            
            if missing_fields:
                self.log_test("LLM Keys List (With Data)", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("LLM Keys List (With Data)", True)
                return True
        else:
            self.log_test("LLM Keys List (With Data)", False, details)
        return False

    def test_llm_keys_get_specific(self):
        """Test GET /api/llm-keys/{key_id}"""
        if not hasattr(self, 'test_key_id'):
            self.log_test("LLM Keys Get Specific", False, "No test key ID available")
            return False
            
        success, response, details = self.make_request('GET', f'llm-keys/{self.test_key_id}')
        
        if success and 'id' in response:
            self.log_test("LLM Keys Get Specific", True)
            return True
        else:
            self.log_test("LLM Keys Get Specific", False, details)
        return False

    def test_llm_keys_update(self):
        """Test PUT /api/llm-keys/{key_id}"""
        if not hasattr(self, 'test_key_id'):
            self.log_test("LLM Keys Update", False, "No test key ID available")
            return False
            
        success, response, details = self.make_request(
            'PUT', f'llm-keys/{self.test_key_id}',
            {
                "name": "Updated Test Key",
                "is_active": True
            }
        )
        
        if success:
            self.log_test("LLM Keys Update", True)
            return True
        else:
            self.log_test("LLM Keys Update", False, details)
        return False

    def test_llm_keys_regenerate(self):
        """Test POST /api/llm-keys/{key_id}/regenerate"""
        if not hasattr(self, 'test_key_id'):
            self.log_test("LLM Keys Regenerate", False, "No test key ID available")
            return False
            
        success, response, details = self.make_request(
            'POST', f'llm-keys/{self.test_key_id}/regenerate'
        )
        
        if success and 'key' in response:
            self.log_test("LLM Keys Regenerate", True)
            return True
        else:
            self.log_test("LLM Keys Regenerate", False, details)
        return False

    def test_llm_keys_usage(self):
        """Test GET /api/llm-keys/{key_id}/usage"""
        if not hasattr(self, 'test_key_id'):
            self.log_test("LLM Keys Usage", False, "No test key ID available")
            return False
            
        success, response, details = self.make_request('GET', f'llm-keys/{self.test_key_id}/usage?days=30')
        
        if success and 'total_requests' in response:
            self.log_test("LLM Keys Usage", True)
            return True
        else:
            self.log_test("LLM Keys Usage", False, details)
        return False

    def test_llm_keys_credits_history(self):
        """Test GET /api/llm-keys/{key_id}/credits-history"""
        if not hasattr(self, 'test_key_id'):
            self.log_test("LLM Keys Credits History", False, "No test key ID available")
            return False
            
        success, response, details = self.make_request('GET', f'llm-keys/{self.test_key_id}/credits-history')
        
        if success and 'transactions' in response and 'current_balance' in response:
            self.log_test("LLM Keys Credits History", True)
            return True
        else:
            self.log_test("LLM Keys Credits History", False, details)
        return False

    def test_llm_keys_delete(self):
        """Test DELETE /api/llm-keys/{key_id}"""
        if not hasattr(self, 'test_key_id'):
            self.log_test("LLM Keys Delete", False, "No test key ID available")
            return False
            
        success, response, details = self.make_request('DELETE', f'llm-keys/{self.test_key_id}')
        
        if success:
            self.log_test("LLM Keys Delete", True)
            return True
        else:
            self.log_test("LLM Keys Delete", False, details)
        return False

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Nirman Backend API Tests")
        print("=" * 50)
        
        # Authentication tests
        print("\n📝 Authentication Tests")
        if not self.test_user_registration():
            print("❌ Authentication failed, stopping tests")
            return False
        
        # LLM Keys API tests
        print("\n🔑 LLM Keys API Tests")
        self.test_llm_keys_pricing_info()
        self.test_llm_keys_overview_stats()
        self.test_llm_keys_list_empty()
        
        # Create a test key for further testing
        if self.test_llm_keys_create():
            self.test_llm_keys_list_with_data()
            self.test_llm_keys_get_specific()
            self.test_llm_keys_update()
            self.test_llm_keys_regenerate()
            self.test_llm_keys_usage()
            self.test_llm_keys_credits_history()
            self.test_llm_keys_delete()
        
        # Print results
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

    def get_test_summary(self):
        """Get test summary for reporting"""
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0,
            "test_results": self.test_results
        }

def main():
    tester = NirmanAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    summary = tester.get_test_summary()
    with open('/app/test_reports/backend_test_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())