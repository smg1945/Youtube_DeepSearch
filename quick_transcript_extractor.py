#!/usr/bin/env python3
"""
빠른 대본 추출기 - API 할당량 없이 대본만 빠르게 추출
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from youtube_transcript_api import YouTubeTranscriptApi


class QuickTranscriptExtractor:
    """API 할당량을 사용하지 않는 빠른 대본 추출기"""
    
    def __init__(self, parent_window):
        self.parent = parent_window
        self.create_window()
    
    def create_window(self):
        """빠른 대본 추출 창 생성"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("🚀 빠른 대본 추출기 (API 할당량 무관)")
        self.window.geometry("800x600")
        self.window.configure(bg='#f5f5f7')
        
        # 중앙 정렬
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.window.winfo_screenheight() // 2) - (600 // 2)
        self.window.geometry(f'800x600+{x}+{y}')
        
        self.setup_ui()
    
    def setup_ui(self):
        """UI 구성"""
        main_frame = tk.Frame(self.window, bg='#f5f5f7')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 제목
        title_label = tk.Label(
            main_frame, 
            text="🚀 빠른 대본 추출기",
            font=('Arial', 16, 'bold'),
            bg='#f5f5f7'
        )
        title_label.pack(pady=(0, 10))
        
        # 설명
        desc_label = tk.Label(
            main_frame,
            text="API 할당량을 사용하지 않고 YouTube 자막만으로 빠르게 대본을 추출합니다.",
            font=('Arial', 10),
            bg='#f5f5f7',
            fg='#666'
        )
        desc_label.pack(pady=(0, 20))
        
        # 입력 프레임
        input_frame = tk.LabelFrame(main_frame, text="YouTube URL 또는 비디오 ID 입력", bg='#f5f5f7', padx=10, pady=10)
        input_frame.pack(fill='x', pady=(0, 20))
        
        # URL 입력
        tk.Label(input_frame, text="URL/ID:", bg='#f5f5f7').pack(anchor='w')
        self.url_entry = tk.Text(input_frame, height=5, wrap='word')
        self.url_entry.pack(fill='x', pady=(5, 0))
        
        # 도움말
        help_text = "• 한 줄에 하나씩 입력하세요\n• YouTube URL 또는 비디오 ID 모두 지원\n• 예: https://www.youtube.com/watch?v=VIDEO_ID"
        tk.Label(input_frame, text=help_text, bg='#f5f5f7', fg='#666', font=('Arial', 9)).pack(anchor='w', pady=(5, 0))
        
        # 버튼 프레임
        button_frame = tk.Frame(main_frame, bg='#f5f5f7')
        button_frame.pack(fill='x', pady=(0, 20))
        
        # 추출 버튼
        extract_button = tk.Button(
            button_frame,
            text="🎯 대본 추출 시작",
            command=self.start_extraction,
            bg='#007aff',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10,
            cursor='hand2'
        )
        extract_button.pack(side='left', padx=(0, 10))
        
        # 폴더 선택 버튼
        folder_button = tk.Button(
            button_frame,
            text="📁 저장 폴더 선택",
            command=self.select_folder,
            bg='#34c759',
            fg='white',
            font=('Arial', 10),
            padx=15,
            pady=10,
            cursor='hand2'
        )
        folder_button.pack(side='left')
        
        # 상태 프레임
        status_frame = tk.LabelFrame(main_frame, text="진행 상황", bg='#f5f5f7', padx=10, pady=10)
        status_frame.pack(fill='both', expand=True)
        
        # 진행 상황 텍스트
        self.status_text = tk.Text(status_frame, height=15, wrap='word', state='disabled')
        self.status_text.pack(fill='both', expand=True)
        
        # 스크롤바
        scrollbar = tk.Scrollbar(status_frame, command=self.status_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        # 하단 상태
        self.bottom_status = tk.Label(main_frame, text="저장 폴더를 선택하고 URL을 입력한 후 추출을 시작하세요.", bg='#f5f5f7', fg='#666')
        self.bottom_status.pack(pady=(10, 0))
        
        # 기본값
        self.save_folder = None
    
    def log_message(self, message):
        """상태 텍스트에 메시지 추가"""
        self.status_text.configure(state='normal')
        self.status_text.insert('end', f"{message}\n")
        self.status_text.configure(state='disabled')
        self.status_text.see('end')
        self.window.update()
    
    def select_folder(self):
        """저장 폴더 선택"""
        folder = filedialog.askdirectory(title="대본 저장 폴더 선택")
        if folder:
            self.save_folder = folder
            self.bottom_status.config(text=f"저장 폴더: {folder}")
            self.log_message(f"📁 저장 폴더 선택됨: {folder}")
    
    def extract_video_id(self, url_or_id):
        """URL에서 비디오 ID 추출"""
        import re
        if 'youtube.com' in url_or_id or 'youtu.be' in url_or_id:
            patterns = [
                r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
                r'youtube\.com/watch\?.*v=([^&\n?#]+)',
            ]
            for pattern in patterns:
                match = re.search(pattern, url_or_id)
                if match:
                    return match.group(1)
        return url_or_id.strip()
    
    def get_transcript(self, video_id):
        """비디오 ID로 대본 추출"""
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # 우선 언어별로 시도
            for lang in ['ko', 'en']:
                try:
                    transcript = transcript_list.find_transcript([lang])
                    transcript_data = transcript.fetch()
                    
                    # 텍스트만 추출
                    text_content = ' '.join([item.get('text', '') for item in transcript_data])
                    
                    if text_content.strip():
                        return text_content.strip(), f"{lang} 자막"
                        
                except Exception:
                    continue
            
            # 자동 생성 자막 시도
            for lang in ['ko', 'en']:
                try:
                    transcript = transcript_list.find_generated_transcript([lang])
                    transcript_data = transcript.fetch()
                    
                    text_content = ' '.join([item.get('text', '') for item in transcript_data])
                    
                    if text_content.strip():
                        return text_content.strip(), f"{lang} 자동생성 자막"
                        
                except Exception:
                    continue
            
            return None, "사용 가능한 자막 없음"
            
        except Exception as e:
            return None, f"오류: {str(e)}"
    
    def start_extraction(self):
        """대본 추출 시작"""
        if not self.save_folder:
            messagebox.showwarning("폴더 선택", "저장 폴더를 먼저 선택해주세요.")
            return
        
        urls = self.url_entry.get('1.0', 'end').strip()
        if not urls:
            messagebox.showwarning("URL 입력", "YouTube URL 또는 비디오 ID를 입력해주세요.")
            return
        
        url_list = [url.strip() for url in urls.split('\n') if url.strip()]
        
        if not url_list:
            messagebox.showwarning("URL 입력", "유효한 URL을 입력해주세요.")
            return
        
        # 기존 로그 클리어
        self.status_text.configure(state='normal')
        self.status_text.delete('1.0', 'end')
        self.status_text.configure(state='disabled')
        
        def extraction_thread():
            success_count = 0
            total = len(url_list)
            
            self.log_message(f"🚀 빠른 대본 추출 시작: {total}개 항목")
            self.log_message("=" * 50)
            
            for i, url in enumerate(url_list, 1):
                try:
                    video_id = self.extract_video_id(url)
                    
                    self.log_message(f"[{i}/{total}] 처리 중: {video_id}")
                    self.bottom_status.config(text=f"진행 중... ({i}/{total})")
                    
                    transcript, source = self.get_transcript(video_id)
                    
                    if transcript:
                        # 파일 저장
                        filename = f"transcript_{video_id}.txt"
                        filepath = os.path.join(self.save_folder, filename)
                        
                        # 중복 파일명 처리
                        counter = 1
                        original_path = filepath
                        while os.path.exists(filepath):
                            name, ext = os.path.splitext(original_path)
                            filepath = f"{name}_{counter}{ext}"
                            counter += 1
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(transcript)
                        
                        success_count += 1
                        self.log_message(f"✅ 성공: {source} → {filename}")
                    else:
                        self.log_message(f"❌ 실패: {source}")
                    
                except Exception as e:
                    self.log_message(f"❌ 오류: {str(e)}")
                
                # 요청 간격
                import time
                time.sleep(0.5)
            
            # 완료 메시지
            self.log_message("=" * 50)
            self.log_message(f"🎉 추출 완료: {success_count}/{total}개 성공")
            self.bottom_status.config(text=f"완료: {success_count}/{total}개 성공")
            
            messagebox.showinfo(
                "추출 완료",
                f"빠른 대본 추출이 완료되었습니다!\n\n"
                f"성공: {success_count}/{total}개\n"
                f"저장 위치: {self.save_folder}\n\n"
                f"💡 API 할당량을 전혀 사용하지 않았습니다!"
            )
        
        threading.Thread(target=extraction_thread, daemon=True).start()


# 메인 애플리케이션에 버튼 추가용 함수
def add_quick_extract_button(parent_window, button_frame):
    """메인 창에 빠른 추출 버튼 추가"""
    quick_button = tk.Button(
        button_frame,
        text="🚀 빠른 대본 추출",
        command=lambda: QuickTranscriptExtractor(parent_window),
        bg='#ff9500',
        fg='white',
        font=('Arial', 10, 'bold'),
        padx=15,
        pady=5,
        cursor='hand2'
    )
    quick_button.pack(side='left', padx=(10, 0))


if __name__ == "__main__":
    # 단독 실행 테스트
    root = tk.Tk()
    root.withdraw()  # 메인 창 숨기기
    
    app = QuickTranscriptExtractor(root)
    root.mainloop()
