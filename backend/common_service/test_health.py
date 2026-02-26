"""Quick test to verify common_service health endpoint."""
import sys
sys.path.insert(0, '.')

from common_service.main import app

def test_app_import():
    """Test that app can be imported."""
    assert app is not None
    assert app.title == "HQKV8 Common Service"
    print("✓ App import test passed")

def test_health_route():
    """Test that health route is registered."""
    routes = [route.path for route in app.routes]
    assert "/health" in routes
    print("✓ Health route registered")

if __name__ == "__main__":
    test_app_import()
    test_health_route()
    print("\n✓ All health checks passed!")
