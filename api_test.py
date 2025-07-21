#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 현재 디렉토리를 Python path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("YouTube API Test")
print("=" * 50)

try:
    from youtube_api import YouTubeAPI
    import config
    
    print(f"API Key: {config.YOUTUBE_API_KEY[:10]}...{config.YOUTUBE_API_KEY[-5:]}")
    
    print("\nInitializing YouTube API...")
    youtube_api = YouTubeAPI()
    print("SUCCESS: YouTube API connected!")
    
    print("\nTesting search (keyword: 'python programming')...")
    videos = youtube_api.search_videos(keyword="python programming", max_results=3)
    
    if videos:
        print(f"SUCCESS: Found {len(videos)} videos!")
        print("\nSearch Results:")
        for i, video in enumerate(videos, 1):
            print(f"{i}. {video['title'][:60]}...")
            print(f"   Channel: {video['channel_title']}")
            print(f"   Views: {video['view_count']:,}")
            print(f"   Duration: {video['duration_seconds']}s")
            print(f"   URL: {video['url']}")
            print()
    else:
        print("WARNING: No search results found")
    
    print("=" * 50)
    print("API Test Completed Successfully!")
    print("You can now run: python main.py")
    print("=" * 50)

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    print("\nPossible solutions:")
    print("1. Check API key in config.py")
    print("2. Verify YouTube Data API v3 is enabled")
    print("3. Check network connection")

print("\nPress Enter to continue...")
input()
