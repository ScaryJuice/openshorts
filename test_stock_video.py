#!/usr/bin/env python3
"""
Test script for stock video functionality in OpenShorts
"""
import os
import sys
import tempfile
import shutil

# Add the openshorts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openshorts import Config, get_stock_videos, find_emphasis_segments, create_stock_integration_plan

def test_stock_video_functions():
    """Test the stock video helper functions"""
    print("🧪 Testing Stock Video Functions...")
    
    # Create a temporary config
    config = Config()
    
    # Test get_stock_videos with non-existent folder
    print("\n1. Testing get_stock_videos with empty folder...")
    empty_videos = get_stock_videos("/nonexistent/path")
    print(f"   Non-existent folder result: {empty_videos}")
    assert empty_videos == [], "Should return empty list for non-existent folder"
    
    # Test emphasis detection
    print("\n2. Testing find_emphasis_segments...")
    
    # Sample transcript segments for testing
    test_segments = [
        {
            'start': 0.0,
            'end': 2.5,
            'text': 'Welcome to our amazing tutorial!',
            'words': [
                {'start': 0.0, 'end': 0.5, 'word': 'Welcome'},
                {'start': 0.5, 'end': 0.8, 'word': 'to'},
                {'start': 0.8, 'end': 1.1, 'word': 'our'},
                {'start': 1.1, 'end': 1.7, 'word': 'amazing'},
                {'start': 1.7, 'end': 2.5, 'word': 'tutorial!'}
            ]
        },
        {
            'start': 2.5,
            'end': 5.0,
            'text': 'This is incredible technology',
            'words': [
                {'start': 2.5, 'end': 2.8, 'word': 'This'},
                {'start': 2.8, 'end': 3.0, 'word': 'is'},
                {'start': 3.0, 'end': 3.8, 'word': 'incredible'},
                {'start': 3.8, 'end': 5.0, 'word': 'technology'}
            ]
        },
        {
            'start': 5.0,
            'end': 7.0,
            'text': 'And it works perfectly',
            'words': [
                {'start': 5.0, 'end': 5.3, 'word': 'And'},
                {'start': 5.3, 'end': 5.5, 'word': 'it'},
                {'start': 5.5, 'end': 5.9, 'word': 'works'},
                {'start': 5.9, 'end': 7.0, 'word': 'perfectly'}
            ]
        }
    ]
    
    emphasis_segments = find_emphasis_segments(test_segments, min_segment_duration=1.5)
    print(f"   Found {len(emphasis_segments)} emphasis segments:")
    for seg in emphasis_segments:
        print(f"     - {seg['start']:.1f}s-{seg['end']:.1f}s: '{seg['text']}' (score: {seg['emphasis_score']:.2f})")
    
    assert len(emphasis_segments) > 0, "Should find at least one emphasis segment"
    
    # Test integration plan
    print("\n3. Testing create_stock_integration_plan...")
    
    # Create dummy stock videos list
    stock_videos = [
        "/path/to/stock1.mp4",
        "/path/to/stock2.mp4", 
        "/path/to/stock3.mp4"
    ]
    
    stock_plan = create_stock_integration_plan(
        emphasis_segments, 
        stock_videos, 
        usage_percentage=50,  # 50% usage
        selection_mode="random",
        min_duration=1.0,
        max_duration=3.0
    )
    
    print(f"   Stock integration plan:")
    print(f"     - Using {len(stock_plan['segments'])} stock segments")
    print(f"     - Coverage: {stock_plan['coverage_percentage']:.1f}%")
    
    for seg in stock_plan['segments']:
        print(f"     - {seg['start']:.1f}s-{seg['end']:.1f}s: {os.path.basename(seg['stock_video'])}")
    
    print("\n✅ All stock video functions working correctly!")
    return True

def test_config_integration():
    """Test stock video config integration"""
    print("\n🔧 Testing Config Integration...")
    
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_config_path = f.name
        f.write('{}')  # Empty JSON
    
    try:
        config = Config(config_file=temp_config_path)
        
        # Test setting stock video config
        config.set("stock_video.enabled", True)
        config.set("stock_video.folder_path", "/test/stock/path")
        config.set("stock_video.usage_percentage", 60)
        config.set("stock_video.selection_mode", "sequential")
        
        # Test getting values
        enabled = config.get("stock_video.enabled", False)
        folder_path = config.get("stock_video.folder_path", "")
        usage_pct = config.get("stock_video.usage_percentage", 30)
        selection = config.get("stock_video.selection_mode", "random")
        
        print(f"   Stock video enabled: {enabled}")
        print(f"   Folder path: {folder_path}")
        print(f"   Usage percentage: {usage_pct}%")
        print(f"   Selection mode: {selection}")
        
        assert enabled == True, "Should save/load boolean correctly"
        assert folder_path == "/test/stock/path", "Should save/load path correctly"
        assert usage_pct == 60, "Should save/load percentage correctly"
        assert selection == "sequential", "Should save/load selection mode correctly"
        
        print("\n✅ Config integration working correctly!")
        return True
        
    finally:
        # Clean up temp file
        if os.path.exists(temp_config_path):
            os.unlink(temp_config_path)

if __name__ == "__main__":
    print("🚀 OpenShorts Stock Video Test Suite")
    print("=" * 50)
    
    try:
        # Test basic functions
        test_stock_video_functions()
        test_config_integration()
        
        print("\n🎉 All tests passed! Stock video system ready.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)