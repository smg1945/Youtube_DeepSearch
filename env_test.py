#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 현재 디렉토리를 Python path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("YouTube DeepSearch Environment Test")
print("=" * 50)

try:
    print(f"Python version: {sys.version}")
    
    print("Testing modules...")
    
    try:
        import tkinter
        print("OK: tkinter module")
    except ImportError:
        print("MISSING: tkinter module")
    
    try:
        import requests
        print("OK: requests module")
    except ImportError:
        print("MISSING: requests module - pip install requests")
    
    try:
        import googleapiclient
        print("OK: googleapiclient module")
    except ImportError:
        print("MISSING: googleapiclient - pip install google-api-python-client")
    
    try:
        import youtube_transcript_api
        print("OK: youtube_transcript_api module")
    except ImportError:
        print("MISSING: youtube_transcript_api - pip install youtube-transcript-api")
    
    try:
        from PIL import Image
        print("OK: PIL/Pillow module")
    except ImportError:
        print("MISSING: PIL/Pillow - pip install Pillow")
    
    # config 파일 확인
    try:
        import config
        if hasattr(config, 'YOUTUBE_API_KEY'):
            if config.YOUTUBE_API_KEY == "YOUR_YOUTUBE_API_KEY_HERE":
                print("WARNING: API key not set")
            else:
                key_preview = config.YOUTUBE_API_KEY[:10] + "..." + config.YOUTUBE_API_KEY[-5:]
                print(f"OK: API key configured: {key_preview}")
        else:
            print("MISSING: No API key found in config")
    except ImportError as e:
        print(f"MISSING: config.py file - {e}")
    
    print("\n" + "=" * 50)
    print("Environment test completed!")
    print("=" * 50)

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\nPress Enter to continue...")
input()
