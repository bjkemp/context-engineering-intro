#!/usr/bin/env python3
"""
Validation script to test all imports work correctly.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all main modules can be imported."""
    
    print("Testing imports...")
    
    try:
        # Test models
        from adventure_agent.models import AdventureGame, AuthorPersona, StoryRequirements
        print("✅ Models imported successfully")
        
        # Test parsers
        from adventure_agent.parsers.author_parser import parse_author_file
        from adventure_agent.parsers.story_parser import parse_story_file
        from adventure_agent.parsers.adv_generator import generate_adv_file
        print("✅ Parsers imported successfully")
        
        # Test tools (just a few key ones)
        import adventure_agent.tools.storyline_generator
        import adventure_agent.tools.adv_validator
        import adventure_agent.tools.choice_analyzer
        print("✅ Tools imported successfully")
        
        # Test main agent
        from adventure_agent.agent import generate_adventure, create_adventure_agent
        print("✅ Main agent imported successfully")
        
        # Test CLI
        from adventure_agent.cli import app
        print("✅ CLI imported successfully")
        
        print("\n🎉 All imports successful! The Adventure Generation Agent is ready to use.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)