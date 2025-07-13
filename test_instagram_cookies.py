#!/usr/bin/env python3
"""
Instagram Cookie Tester
Tests if the current Instagram cookies are valid
"""

import requests
import json
from pathlib import Path

def load_cookies_from_file(cookie_file):
    """Load cookies from Netscape format file"""
    cookies = {}
    if not Path(cookie_file).exists():
        print(f"Cookie file {cookie_file} not found!")
        return cookies
    
    with open(cookie_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            parts = line.split('\t')
            if len(parts) >= 7:
                domain, _, path, secure, expiry, name, value = parts[:7]
                if domain == '.instagram.com' or domain == '#HttpOnly_.instagram.com':
                    # Handle HttpOnly cookies (remove #HttpOnly_ prefix if present)
                    if name.startswith('#HttpOnly_'):
                        name = name[10:]  # Remove '#HttpOnly_' prefix
                    cookies[name] = value
    
    return cookies

def test_instagram_session(cookies):
    """Test if Instagram session is valid"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # Test 1: Check if we can access Instagram API
    try:
        response = requests.get(
            'https://www.instagram.com/api/v1/users/web_profile_info/',
            headers=headers,
            cookies=cookies,
            timeout=10
        )
        
        print(f"API Test Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Instagram API accessible")
            return True
        elif response.status_code == 401:
            print("❌ Unauthorized - Session expired")
            return False
        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Instagram API: {e}")
        return False

def main():
    print("🔍 Instagram Cookie Tester")
    print("=" * 40)
    
    # Test Instagram cookies
    insta_cookies = load_cookies_from_file('backend/cookies_insta.txt')
    
    if not insta_cookies:
        print("❌ No Instagram cookies found!")
        return
    
    print(f"📋 Found {len(insta_cookies)} Instagram cookies:")
    for name, value in insta_cookies.items():
        if name == 'sessionid':
            # Truncate sessionid for security
            display_value = value[:20] + "..." if len(value) > 20 else value
        else:
            display_value = value
        print(f"  {name}: {display_value}")
    
    print("\n🧪 Testing Instagram session...")
    is_valid = test_instagram_session(insta_cookies)
    
    if is_valid:
        print("\n✅ Instagram cookies are valid!")
    else:
        print("\n❌ Instagram cookies are invalid or expired!")
        print("\n📝 To fix this:")
        print("1. Go to Instagram.com and log in")
        print("2. Open Developer Tools (F12)")
        print("3. Go to Application/Storage → Cookies")
        print("4. Copy the sessionid and other cookies")
        print("5. Update backend/cookies_insta.txt")

if __name__ == "__main__":
    main() 