import requests
import json

def test_backend():
    """Test the backend API endpoints"""
    base_url = "http://localhost:5000/api"
    
    print("Testing Video Downloader Backend...")
    print("=" * 40)
    
    # Test health check
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print("❌ Health check failed")
    except requests.exceptions.ConnectionError:
        print("❌ Backend server is not running")
        print("Please start the backend server first: python app.py")
        return
    
    # Test video info endpoint with a sample YouTube URL
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll for testing
    
    print(f"\nTesting video info extraction with: {test_url}")
    
    try:
        response = requests.post(
            f"{base_url}/info",
            json={"url": test_url},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Video info extraction successful")
            print(f"   Title: {data.get('title', 'Unknown')}")
            print(f"   Duration: {data.get('duration', 0)} seconds")
            print(f"   Available formats: {len(data.get('formats', []))}")
        else:
            print(f"❌ Video info extraction failed: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    
    print("\nBackend test completed!")

if __name__ == "__main__":
    test_backend() 