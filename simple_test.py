#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 테스트 스크립트
"""

print("=" * 50)
print("YouTube DeepSearch 환경 테스트")
print("=" * 50)

try:
    import sys
    print(f"✅ Python 버전: {sys.version}")
    
    import tkinter
    print("✅ tkinter 모듈 OK")
    
    import requests
    print("✅ requests 모듈 OK")
    
    try:
        import googleapiclient
        print("✅ googleapiclient 모듈 OK")
    except ImportError:
        print("❌ googleapiclient 모듈 없음 - pip install google-api-python-client 필요")
    
    try:
        import youtube_transcript_api
        print("✅ youtube_transcript_api 모듈 OK")
    except ImportError:
        print("❌ youtube_transcript_api 모듈 없음 - pip install youtube-transcript-api 필요")
    
    try:
        from PIL import Image
        print("✅ PIL/Pillow 모듈 OK")
    except ImportError:
        print("❌ PIL/Pillow 모듈 없음 - pip install Pillow 필요")
    
    # config 파일 확인
    try:
        import config
        if hasattr(config, 'YOUTUBE_API_KEY'):
            if config.YOUTUBE_API_KEY == "YOUR_YOUTUBE_API_KEY_HERE":
                print("⚠️ API 키가 설정되지 않음")
            else:
                key_preview = config.YOUTUBE_API_KEY[:10] + "..." + config.YOUTUBE_API_KEY[-5:]
                print(f"✅ API 키 설정됨: {key_preview}")
        else:
            print("❌ API 키 설정 없음")
    except ImportError:
        print("❌ config.py 파일 없음")
    
    print("\n" + "=" * 50)
    print("환경 테스트 완료!")
    print("=" * 50)

except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()

input("\n아무 키나 누르면 종료됩니다...")
