#!/usr/bin/env python3
"""
YouTube 대본 전용 추출기 - API 할당량 없이 사용 가능
youtube-transcript-api만 사용하여 API 한도와 무관하게 대본 추출
"""
import os
import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter


class TranscriptOnlyExtractor:
    """YouTube 대본 전용 추출기 - API 할당량 사용 안 함"""
    
    def __init__(self):
        self.formatter = TextFormatter()
        
    def extract_video_id_from_url(self, url):
        """URL에서 비디오 ID 추출"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
            r'youtube\.com/watch\?.*v=([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_transcript(self, video_id_or_url, languages=['ko', 'en']):
        """
        비디오 ID 또는 URL로 대본 추출
        
        Args:
            video_id_or_url (str): YouTube 비디오 ID 또는 전체 URL
            languages (list): 우선 언어 목록
            
        Returns:
            str: 추출된 대본 텍스트 또는 None
        """
        try:
            # URL인 경우 비디오 ID 추출
            if 'youtube.com' in video_id_or_url or 'youtu.be' in video_id_or_url:
                video_id = self.extract_video_id_from_url(video_id_or_url)
                if not video_id:
                    return None
            else:
                video_id = video_id_or_url
            
            print(f"대본 추출 시도: {video_id}")
            
            # 사용 가능한 자막 목록 가져오기
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # 우선 언어별로 시도
            for lang in languages:
                try:
                    transcript = transcript_list.find_transcript([lang])
                    transcript_data = transcript.fetch()
                    
                    # 텍스트만 추출
                    text_content = self.formatter.format_transcript(transcript_data)
                    
                    if text_content.strip():
                        print(f"✅ {lang} 자막으로 대본 추출 성공")
                        return text_content.strip()
                        
                except Exception as lang_error:
                    continue
            
            # 자동 생성 자막 시도
            try:
                for lang in languages:
                    try:
                        transcript = transcript_list.find_generated_transcript([lang])
                        transcript_data = transcript.fetch()
                        
                        text_content = self.formatter.format_transcript(transcript_data)
                        
                        if text_content.strip():
                            print(f"✅ {lang} 자동생성 자막으로 대본 추출 성공")
                            return text_content.strip()
                            
                    except Exception:
                        continue
                        
            except Exception as auto_error:
                pass
            
            print(f"❌ 사용 가능한 자막이 없습니다: {video_id}")
            return None
            
        except Exception as e:
            print(f"❌ 대본 추출 오류 ({video_id}): {e}")
            return None
    
    def get_multiple_transcripts(self, video_list, progress_callback=None):
        """
        여러 비디오의 대본을 한 번에 추출
        
        Args:
            video_list (list): 비디오 ID 또는 URL 목록
            progress_callback (function): 진행상황 콜백 함수
            
        Returns:
            dict: {video_id: transcript_text} 형태의 결과
        """
        results = {}
        total = len(video_list)
        
        for i, video in enumerate(video_list):
            if progress_callback:
                progress_callback(f"대본 추출 중... ({i+1}/{total})")
            
            transcript = self.get_transcript(video)
            if transcript:
                video_id = self.extract_video_id_from_url(video) if 'youtube.com' in video else video
                results[video_id] = transcript
                
            # 요청 간격 조정
            import time
            time.sleep(0.5)
        
        return results
    
    def save_transcript(self, video_id_or_url, output_file, languages=['ko', 'en']):
        """
        대본을 파일로 저장
        
        Args:
            video_id_or_url (str): YouTube 비디오 ID 또는 URL
            output_file (str): 저장할 파일 경로
            languages (list): 우선 언어 목록
            
        Returns:
            bool: 저장 성공 여부
        """
        transcript = self.get_transcript(video_id_or_url, languages)
        
        if transcript:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(transcript)
                print(f"✅ 대본 저장 완료: {output_file}")
                return True
            except Exception as e:
                print(f"❌ 파일 저장 오류: {e}")
                return False
        else:
            print(f"❌ 추출할 대본이 없습니다")
            return False


def main():
    """테스트 및 사용 예시"""
    extractor = TranscriptOnlyExtractor()
    
    print("=== YouTube 대본 전용 추출기 ===")
    print("API 할당량을 사용하지 않는 대본 추출 도구")
    print()
    
    # 사용 예시
    video_url = input("YouTube URL 또는 비디오 ID를 입력하세요: ").strip()
    
    if video_url:
        transcript = extractor.get_transcript(video_url)
        
        if transcript:
            print("\n=== 추출된 대본 ===")
            print(transcript[:500] + "..." if len(transcript) > 500 else transcript)
            
            # 파일로 저장할지 물어보기
            save_option = input("\n파일로 저장하시겠습니까? (y/n): ").lower()
            if save_option == 'y':
                filename = f"transcript_{extractor.extract_video_id_from_url(video_url) or 'unknown'}.txt"
                extractor.save_transcript(video_url, filename)
        else:
            print("대본을 추출할 수 없습니다.")


if __name__ == "__main__":
    main()
