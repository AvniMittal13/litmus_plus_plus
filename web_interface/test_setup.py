"""
Test script to verify the hierarchical MainAgent web interface setup
"""

import sys
import os

# Add paths for testing
web_interface_path = os.path.dirname(__file__)
sys.path.append(web_interface_path)
sys.path.append(os.path.join(web_interface_path, 'agents_enhanced'))
sys.path.append(os.path.join(web_interface_path, 'services'))

def test_imports():
    """Test that all necessary imports work"""
    print("Testing imports...")
    
    try:
        from enhanced_main_agent import EnhancedMainAgent
        print("✓ EnhancedMainAgent import successful")
    except ImportError as e:
        print(f"✗ EnhancedMainAgent import failed: {e}")
        return False
    
    try:
        from main_agent_service import MainAgentService
        print("✓ MainAgentService import successful")
    except ImportError as e:
        print(f"✗ MainAgentService import failed: {e}")
        return False
    
    try:
        from session_manager import SessionManager
        print("✓ SessionManager import successful")
    except ImportError as e:
        print(f"✗ SessionManager import failed: {e}")
        return False
    
    return True

def test_file_structure():
    """Test that all necessary files exist"""
    print("\nTesting file structure...")
    
    files_to_check = [
        "app.py",
        "services/main_agent_service.py",
        "services/session_manager.py",
        "agents_enhanced/enhanced_main_agent.py",
        "agents_enhanced/enhanced_thought_agent.py",
        "static/js/thinking-panel.js",
        "static/css/style.css",
        "templates/index.html"
    ]
    
    all_exist = True
    for file_path in files_to_check:
        full_path = os.path.join(web_interface_path, file_path)
        if os.path.exists(full_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} (missing)")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print("=== Hierarchical MainAgent Web Interface Test ===")
    
    imports_ok = test_imports()
    files_ok = test_file_structure()
    
    print(f"\n=== Test Results ===")
    print(f"Imports: {'PASS' if imports_ok else 'FAIL'}")
    print(f"File Structure: {'PASS' if files_ok else 'FAIL'}")
    
    if imports_ok and files_ok:
        print("\n🎉 All tests passed! The web interface should be ready to run.")
        print("\nTo start the interface:")
        print("1. cd web_interface")
        print("2. python app.py")
        print("3. Open http://localhost:5000")
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")

if __name__ == "__main__":
    main()
