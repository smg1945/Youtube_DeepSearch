#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube DeepSearch API 키 테스트 스크립트
API 키가 정상적으로 작동하는지 확인하는 간단한 테스트입니다.
"""

import sys
import os

# 현재 디렉토리를 Python path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from youtube_api import YouTubeAPI
    import config
except ImportError as e:
    print(f"모듈 임포트 오류: {e}")
    print("필요한 패키지를 설치해주세요: pip install -r requirements.txt")
    sys.exit(1)


def test_api_key():
    """API 키 테스트"""
    print("YouTube DeepSearch API 키 테스트")
    print("=" * 50)
    
    # API 키 확인
    if config.YOUTUBE_API_KEY == "YOUR_YOUTUBE_API_KEY_HERE":
        print("❌ API 키가 설정되지 않았습니다.")
        print("\n설정 방법:")
        print("1. https://console.developers.google.com/apis/credentials 에서 API 키 발급")
        print("2. config.py 파일의 YOUTUBE_API_KEY 값 수정")
        print("3. 이 스크립트 재실행")
        return False
    
    print(f"API 키: {config.YOUTUBE_API_KEY[:10]}...{config.YOUTUBE_API_KEY[-5:]}")
    
    try:
        # YouTube API 초기화
        print("\n📡 YouTube API 연결 중...")
        youtube_api = YouTubeAPI()
        print("✅ YouTube API 연결 성공!")
        
        # 간단한 검색 테스트
        print("\n🔍 검색 테스트 중... (키워드: 'python')")
        videos = youtube_api.search_videos(keyword="python", max_results=5)
        
        if videos:
            print(f"✅ 검색 성공! {len(videos)}개 영상을 찾았습니다.")
            print("\n📋 검색 결과:")
            for i, video in enumerate(videos[:3], 1):
                print(f"{i}. {video['title'][:50]}...")
                print(f"   채널: {video['channel_title']}")
                print(f"   조회수: {video['view_count']:,}")
                print()
        else:
            print("⚠️ 검색 결과가 없습니다.")
        
        print("🎉 API 키 테스트 완료! YouTube DeepSearch를 사용할 수 있습니다.")
        return True
        
    except ValueError as e:
        if "YouTube API 키를 config.py 파일에 설정해주세요" in str(e):
            print(f"❌ {e}")
        else:
            print(f"❌ API 초기화 실패: {e}")
        print("\n해결 방법:")
        print("1. config.py 파일의 YOUTUBE_API_KEY 값 확인")
        print("2. API 키가 올바른지 확인")
        print("3. YouTube Data API v3가 활성화되었는지 확인")
        return False
    except Exception as e:
        print(f"❌ API 테스트 실패: {e}")
        print("\n가능한 원인:")
        print("- API 키가 올바르지 않음")
        print("- YouTube Data API v3가 활성화되지 않음")
        print("- API 할당량 초과")
        print("- 네트워크 연결 문제")
        return False


def main():
    """메인 함수"""
    success = test_api_key()
    
    if success:
        print("\n" + "=" * 50)
        print("이제 main.py를 실행하여 YouTube DeepSearch를 사용할 수 있습니다!")
        print("명령어: python main.py")
    else:
        print("\n" + "=" * 50)
        print("문제를 해결한 후 다시 시도해주세요.")
    
    input("\n아무 키나 누르면 종료됩니다...")


if __name__ == "__main__":
    main()
