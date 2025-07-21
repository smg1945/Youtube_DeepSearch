import os
import re
import json
import requests
import tempfile
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import config
import statistics

try:
    import yt_dlp
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("Warning: yt-dlp or whisper not installed. Audio transcription will not be available.")


class YouTubeAPI:
    def __init__(self):
        self.api_key = config.YOUTUBE_API_KEY
        if self.api_key == "YOUR_YOUTUBE_API_KEY_HERE":
            raise ValueError("YouTube API 키를 config.py 파일에 설정해주세요.")
        
        # Whisper 모델을 클래스 변수로 저장 (한 번만 로드)
        self.whisper_model = None
        
        try:
            self.youtube = build(
                config.YOUTUBE_API_SERVICE_NAME,
                config.YOUTUBE_API_VERSION,
                developerKey=self.api_key,
                cache_discovery=False  # 캐시 비활성화로 인증 문제 방지
            )
        except Exception as e:
            raise ValueError(f"YouTube API 초기화 실패: {e}\nAPI 키가 올바른지 확인해주세요.")
    
    def search_videos(self, keyword, video_type="all", min_views=0, max_subscribers=None, 
                     upload_period=None, max_results=100, progress_callback=None):
        """
        키워드로 영상 검색
        """
        try:
            if progress_callback:
                progress_callback("검색 조건 설정 중...")
            
            # 날짜 범위 설정
            published_after = None
            if upload_period:
                if upload_period == "1일":
                    published_after = (datetime.now() - timedelta(days=1)).isoformat() + 'Z'
                elif upload_period == "1주일":
                    published_after = (datetime.now() - timedelta(weeks=1)).isoformat() + 'Z'
                elif upload_period == "1개월":
                    published_after = (datetime.now() - timedelta(days=30)).isoformat() + 'Z'
                elif upload_period == "3개월":
                    published_after = (datetime.now() - timedelta(days=90)).isoformat() + 'Z'
                elif upload_period == "1년":
                    published_after = (datetime.now() - timedelta(days=365)).isoformat() + 'Z'
            
            # 검색 수행
            all_videos = []
            next_page_token = None
            page_count = 0
            
            while len(all_videos) < max_results:
                page_count += 1
                if progress_callback:
                    progress_callback(f"검색 중... 페이지 {page_count} ({len(all_videos)}/{max_results})")
                
                # 한 번에 가져올 결과 수 계산
                remaining = max_results - len(all_videos)
                results_per_request = min(config.MAX_RESULTS_PER_REQUEST, remaining)
                
                # 검색 요청 파라미터
                search_params = {
                    'part': 'snippet',
                    'q': keyword,
                    'type': 'video',
                    'maxResults': results_per_request,
                    'order': 'relevance'
                }
                
                if published_after:
                    search_params['publishedAfter'] = published_after
                
                if next_page_token:
                    search_params['pageToken'] = next_page_token
                
                # 검색 실행
                search_response = self.youtube.search().list(**search_params).execute()
                
                if not search_response.get('items'):
                    break
                
                # 비디오 ID 추출
                video_ids = [item['id']['videoId'] for item in search_response['items']]
                
                if progress_callback:
                    progress_callback(f"영상 정보 분석 중... ({len(video_ids)}개 영상)")
                
                # 비디오 상세 정보 가져오기
                videos_detail = self._get_videos_detail(video_ids)
                
                # 필터링 및 추가
                for video in videos_detail:
                    if self._filter_video(video, video_type, min_views, max_subscribers):
                        all_videos.append(video)
                
                # 다음 페이지 토큰 확인
                next_page_token = search_response.get('nextPageToken')
                if not next_page_token:
                    break
            
            if progress_callback:
                progress_callback("영상 품질 점수 계산 중...")
            
            # Outlier score 계산
            self._calculate_outlier_scores(all_videos)
            
            if progress_callback:
                progress_callback("검색 완료!")
            
            return all_videos[:max_results]
            
        except Exception as e:
            print(f"검색 중 오류 발생: {e}")
            return []
    
    def _get_videos_detail(self, video_ids):
        """비디오 상세 정보 가져오기"""
        try:
            videos_response = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=','.join(video_ids)
            ).execute()
            
            detailed_videos = []
            
            for item in videos_response['items']:
                # 채널 정보 가져오기
                channel_info = self._get_channel_info(item['snippet']['channelId'])
                
                video_data = {
                    'video_id': item['id'],
                    'title': item['snippet']['title'],
                    'channel_id': item['snippet']['channelId'],
                    'channel_title': item['snippet']['channelTitle'],
                    'published_at': item['snippet']['publishedAt'],
                    'view_count': int(item['statistics'].get('viewCount', 0)),
                    'like_count': int(item['statistics'].get('likeCount', 0)),
                    'comment_count': int(item['statistics'].get('commentCount', 0)),
                    'duration': item['contentDetails']['duration'],
                    'duration_seconds': self._parse_duration(item['contentDetails']['duration']),
                    'subscriber_count': channel_info.get('subscriber_count', 0),
                    'thumbnail_url': item['snippet']['thumbnails'].get('high', {}).get('url', ''),
                    'description': item['snippet'].get('description', ''),
                    'url': f"https://www.youtube.com/watch?v={item['id']}"
                }
                
                detailed_videos.append(video_data)
            
            return detailed_videos
            
        except Exception as e:
            print(f"비디오 상세 정보 가져오기 오류: {e}")
            return []
    
    def _get_channel_info(self, channel_id):
        """채널 정보 가져오기"""
        try:
            channel_response = self.youtube.channels().list(
                part='statistics',
                id=channel_id
            ).execute()
            
            if channel_response['items']:
                stats = channel_response['items'][0]['statistics']
                return {
                    'subscriber_count': int(stats.get('subscriberCount', 0))
                }
            
            return {'subscriber_count': 0}
            
        except Exception as e:
            print(f"채널 정보 가져오기 오류: {e}")
            return {'subscriber_count': 0}
    
    def _parse_duration(self, duration):
        """YouTube duration 형식(PT15M33S)을 초로 변환"""
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
    
    def _filter_video(self, video, video_type, min_views, max_subscribers):
        """비디오 필터링"""
        # 조회수 필터
        if video['view_count'] < min_views:
            return False
        
        # 구독자 수 필터
        if max_subscribers and video['subscriber_count'] > max_subscribers:
            return False
        
        # 비디오 타입 필터
        duration_seconds = video['duration_seconds']
        
        if video_type == "쇼츠" and duration_seconds > config.SHORTS_MAX_DURATION:
            return False
        elif video_type == "롱폼" and duration_seconds <= config.SHORTS_MAX_DURATION:
            return False
        elif video_type == "20분 초과":
            if duration_seconds <= 1200:  # 20분 이하
                return False
        
        return True
    
    def _calculate_outlier_scores(self, videos):
        """Outlier score 계산 (조회수 대비 구독자 수 비율)"""
        if not videos:
            return
        
        # 비율 계산 (조회수 / 구독자 수)
        ratios = []
        for video in videos:
            if video['subscriber_count'] > 0:
                ratio = video['view_count'] / video['subscriber_count']
                ratios.append(ratio)
            else:
                ratios.append(0)
        
        if not ratios:
            return
        
        # Z-score 계산
        mean_ratio = statistics.mean(ratios)
        stdev_ratio = statistics.stdev(ratios) if len(ratios) > 1 else 1
        
        for i, video in enumerate(videos):
            if stdev_ratio > 0:
                z_score = (ratios[i] - mean_ratio) / stdev_ratio
                video['outlier_score'] = round(abs(z_score), 2)
            else:
                video['outlier_score'] = 0
    
    def get_channel_videos(self, channel_id, max_results=50):
        """채널의 모든 영상 가져오기"""
        try:
            # 채널의 업로드 재생목록 ID 가져오기
            channel_response = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            ).execute()
            
            if not channel_response['items']:
                return []
            
            uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # 재생목록의 영상들 가져오기
            all_videos = []
            next_page_token = None
            
            while len(all_videos) < max_results:
                remaining = max_results - len(all_videos)
                results_per_request = min(config.MAX_RESULTS_PER_REQUEST, remaining)
                
                playlist_params = {
                    'part': 'snippet',
                    'playlistId': uploads_playlist_id,
                    'maxResults': results_per_request
                }
                
                if next_page_token:
                    playlist_params['pageToken'] = next_page_token
                
                playlist_response = self.youtube.playlistItems().list(**playlist_params).execute()
                
                if not playlist_response.get('items'):
                    break
                
                # 비디오 ID 추출
                video_ids = [item['snippet']['resourceId']['videoId'] for item in playlist_response['items']]
                
                # 비디오 상세 정보 가져오기
                videos_detail = self._get_videos_detail(video_ids)
                all_videos.extend(videos_detail)
                
                next_page_token = playlist_response.get('nextPageToken')
                if not next_page_token:
                    break
            
            # Outlier score 계산
            self._calculate_outlier_scores(all_videos)
            
            return all_videos[:max_results]
            
        except Exception as e:
            print(f"채널 영상 가져오기 오류: {e}")
            return []
    
    def get_video_transcript(self, video_id, use_whisper=True):
        """영상 대본 가져오기 (YouTube 자막 우선, 없으면 Whisper로 추출)"""
        import time
        
        try:
            # 1단계: YouTube 자막 시도
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            transcript = None
            try:
                # 한국어 자막 시도
                transcript = transcript_list.find_transcript(['ko'])
            except:
                try:
                    # 영어 자막 시도
                    transcript = transcript_list.find_transcript(['en'])
                except:
                    try:
                        # 자동생성 자막 시도
                        transcript = transcript_list.find_generated_transcript(['ko'])
                    except:
                        try:
                            transcript = transcript_list.find_generated_transcript(['en'])
                        except:
                            transcript = None
            
            if transcript:
                transcript_data = transcript.fetch()
                # 안전한 텍스트 추출
                try:
                    if isinstance(transcript_data, list):
                        full_text = ' '.join([
                            item.get('text', '') if isinstance(item, dict) else str(item) 
                            for item in transcript_data
                        ])
                    else:
                        full_text = str(transcript_data)
                    
                    if full_text.strip():
                        print(f"YouTube 자막으로 대본 추출 성공: {video_id}")
                        return full_text.strip()
                except Exception as text_error:
                    print(f"자막 텍스트 처리 오류 ({video_id}): {text_error}")
            
            # API 제한을 피하기 위한 대기
            time.sleep(1)
            
            # 2단계: Whisper로 오디오 추출 후 대본 생성
            if use_whisper and WHISPER_AVAILABLE:
                print(f"YouTube 자막이 없어 Whisper로 대본 추출 시도: {video_id}")
                return self._extract_transcript_with_whisper_improved(video_id)
            
            return None
            
        except Exception as e:
            print(f"대본 가져오기 오류 (Video ID: {video_id}): {e}")
            if use_whisper and WHISPER_AVAILABLE:
                print(f"오류 발생, Whisper로 재시도: {video_id}")
                return self._extract_transcript_with_whisper_improved(video_id)
            else:
                return None
    
    def _extract_transcript_with_whisper_improved(self, video_id):
        """개선된 yt-dlp와 Whisper를 사용한 대본 추출"""
        if not WHISPER_AVAILABLE:
            return None
        
        # Whisper 모델 로드 (한 번만 로드)
        if self.whisper_model is None:
            try:
                print("Whisper 모델 로드 중...")
                self.whisper_model = whisper.load_model("base")
                print("Whisper 모델 로드 완료")
            except Exception as e:
                print(f"Whisper 모델 로드 실패: {e}")
                return None
        
        temp_dir = None
        try:
            import time
            
            # 요청 간격 조정 (403 오류 방지)
            time.sleep(2)
            
            # 임시 디렉토리 생성
            temp_dir = tempfile.mkdtemp()
            audio_path = os.path.join(temp_dir, f"{video_id}")
            
            # 개선된 yt-dlp 설정
            ydl_opts = {
                'format': 'bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio',
                'outtmpl': audio_path + '.%(ext)s',
                'no_warnings': True,
                'quiet': True,
                'ignoreerrors': True,
                'extract_flat': False,
                'writesubtitles': False,
                'writeautomaticsub': False,
                'retries': 3,
                'fragment_retries': 3,
                'skip_unavailable_fragments': True,
                # User-Agent와 헤더 설정
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                },
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
            }
            
            # 오디오 다운로드 시도
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    info = ydl.extract_info(video_url, download=False)
                    
                    # 짧은 영상만 처리 (10분 이하)
                    duration = info.get('duration', 0)
                    if duration > 600:  # 10분 초과
                        print(f"영상이 너무 김 (Whisper 스킵): {video_id} - {duration}초")
                        return "영상이 너무 길어 Whisper 처리를 건너뜁니다. (10분 초과)"
                    
                    # 실제 다운로드
                    ydl.download([video_url])
                    
            except Exception as download_error:
                if "403" in str(download_error) or "Forbidden" in str(download_error):
                    return "해당 영상은 다운로드가 제한되어 있어 대본을 추출할 수 없습니다."
                else:
                    print(f"yt-dlp 다운로드 오류: {download_error}")
                    return None
            
            # 다운로드된 오디오 파일 찾기
            actual_audio_path = None
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    if video_id in file and file.endswith('.wav'):
                        actual_audio_path = os.path.join(temp_dir, file)
                        break
            
            if not actual_audio_path or not os.path.exists(actual_audio_path):
                return "오디오 파일 추출에 실패했습니다."
            
            # Whisper로 텍스트 추출
            try:
                result = self.whisper_model.transcribe(
                    actual_audio_path, 
                    language="ko",
                    task="transcribe",
                    fp16=False  # 호환성 향상
                )
                
                if result and result.get('text'):
                    transcript_text = result['text'].strip()
                    if len(transcript_text) > 10:  # 의미있는 텍스트인지 확인
                        print(f"Whisper로 대본 추출 성공: {video_id}")
                        return transcript_text
                    else:
                        return "추출된 대본이 너무 짧습니다."
                else:
                    return "Whisper가 텍스트를 추출하지 못했습니다."
                    
            except Exception as whisper_error:
                print(f"Whisper 처리 오류: {whisper_error}")
                return f"음성 인식 처리 중 오류가 발생했습니다: {str(whisper_error)}"
                
        except Exception as e:
            print(f"대본 추출 전체 오류 (Video ID: {video_id}): {e}")
            return f"대본 추출 중 오류가 발생했습니다: {str(e)}"
        finally:
            # 임시 파일 정리
            if temp_dir and os.path.exists(temp_dir):
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception as cleanup_error:
                    print(f"임시 파일 정리 오류: {cleanup_error}")
                    pass
        """yt-dlp와 Whisper를 사용한 대본 추출"""
        if not WHISPER_AVAILABLE:
            return None
        
        # Whisper 모델 로드 (한 번만 로드)
        if self.whisper_model is None:
            try:
                print("Whisper 모델 로드 중...")
                self.whisper_model = whisper.load_model("base")
                print("Whisper 모델 로드 완료")
            except Exception as e:
                print(f"Whisper 모델 로드 실패: {e}")
                return None
        
        temp_dir = None
        try:
            # 임시 디렉토리 생성
            temp_dir = tempfile.mkdtemp()
            audio_path = os.path.join(temp_dir, f"{video_id}.wav")
            
            # yt-dlp 설정
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': audio_path[:-4] + '.%(ext)s',
                'extractaudio': True,
                'audioformat': 'wav',
                'audioquality': '192K',
                'no_warnings': True,
                'quiet': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
            }
            
            # 오디오 다운로드
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                ydl.download([video_url])
            
            # 실제 오디오 파일 경로 찾기
            actual_audio_path = None
            for file in os.listdir(temp_dir):
                if file.startswith(video_id) and file.endswith('.wav'):
                    actual_audio_path = os.path.join(temp_dir, file)
                    break
            
            if not actual_audio_path or not os.path.exists(actual_audio_path):
                print(f"오디오 파일을 찾을 수 없음: {video_id}")
                return None
            
            # 오디오에서 텍스트 추출
            result = self.whisper_model.transcribe(actual_audio_path, language="ko")
            
            if result and result.get('text'):
                transcript_text = result['text'].strip()
                print(f"Whisper로 대본 추출 성공: {video_id}")
                return transcript_text
            else:
                print(f"Whisper 추출 결과가 비어있음: {video_id}")
                return None
                
        except Exception as e:
            print(f"Whisper 대본 추출 오류 (Video ID: {video_id}): {e}")
            return None
        finally:
            # 임시 파일 정리
            if temp_dir and os.path.exists(temp_dir):
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except:
                    pass
    
    def download_thumbnail(self, thumbnail_url, save_path):
        """썸네일 다운로드"""
        try:
            response = requests.get(thumbnail_url)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
            return False
        except Exception as e:
            print(f"썸네일 다운로드 오류: {e}")
            return False
