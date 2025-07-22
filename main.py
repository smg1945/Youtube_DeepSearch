import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import webbrowser
import os
from datetime import datetime
from PIL import Image, ImageTk
import requests
from io import BytesIO

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Environment variables loaded from .env file")
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")

import config
from youtube_api import YouTubeAPI


class CheckboxTreeview(ttk.Frame):
    """체크박스가 있는 트리뷰 위젯"""
    def __init__(self, parent, columns, column_widths, **kwargs):
        super().__init__(parent)
        
        # 체크박스 상태 저장
        self.checked_items = set()
        
        # 체크박스 컬럼을 추가한 컬럼 리스트
        all_columns = ["☐"] + list(columns)
        all_widths = [30] + list(column_widths)
        
        # 트리뷰 생성
        self.tree = ttk.Treeview(self, columns=all_columns, show='headings', **kwargs)
        
        # 컬럼 설정
        for i, (col, width) in enumerate(zip(all_columns, all_widths)):
            if col == "☐":
                self.tree.heading(col, text="☐", command=self.toggle_all)
                self.tree.column(col, width=width, minwidth=30, anchor='center')
            else:
                self.tree.heading(col, text=col, command=lambda c=col: self.sort_callback(c))
                self.tree.column(col, width=width, minwidth=50)
        
        # 스크롤바
        v_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 그리드 배치
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # 그리드 가중치
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # 이벤트 바인딩
        self.tree.bind('<Button-1>', self.on_click)
        self.tree.bind('<Double-1>', self.on_double_click)
        
        # 콜백 함수들
        self.sort_callback = lambda x: None
        self.double_click_callback = lambda: None
        self.selection_change_callback = lambda: None
    
    def on_click(self, event):
        """클릭 이벤트 처리"""
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify("column", event.x, event.y)
            if column == '#1':  # 체크박스 컬럼
                item = self.tree.identify("item", event.x, event.y)
                if item:
                    self.toggle_item(item)
                    return "break"  # 기본 선택 동작 방지
        
        # 체크박스 컬럼이 아닌 경우에만 선택 변경 콜백 호출
        if region == "cell":
            column = self.tree.identify("column", event.x, event.y)
            if column != '#1':  # 체크박스 컬럼이 아닌 경우에만
                self.after(10, self.selection_change_callback)
    
    def on_double_click(self, event):
        """더블클릭 이벤트 처리"""
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify("column", event.x, event.y)
            if column != '#1':  # 체크박스 컬럼이 아닌 경우만
                item = self.tree.identify("item", event.x, event.y)
                if item:
                    self.double_click_callback()
    
    def toggle_item(self, item):
        """개별 항목 체크박스 토글"""
        if item in self.checked_items:
            self.checked_items.remove(item)
            checkbox_state = "☐"
        else:
            self.checked_items.add(item)
            checkbox_state = "☑"
        
        # 첫 번째 컬럼(체크박스) 업데이트
        values = list(self.tree.item(item)['values'])
        values[0] = checkbox_state
        self.tree.item(item, values=values)
        
        self.selection_change_callback()
    
    def toggle_all(self):
        """전체 선택/해제 토글"""
        all_items = self.tree.get_children()
        if len(self.checked_items) == len(all_items):
            # 전체 해제
            self.checked_items.clear()
            checkbox_state = "☐"
        else:
            # 전체 선택
            self.checked_items = set(all_items)
            checkbox_state = "☑"
        
        # 모든 항목의 체크박스 상태 업데이트
        for item in all_items:
            values = list(self.tree.item(item)['values'])
            values[0] = checkbox_state
            self.tree.item(item, values=values)
        
        self.selection_change_callback()
    
    def insert(self, parent, index, **kwargs):
        """항목 삽입"""
        values = kwargs.get('values', [])
        # 체크박스 컬럼 추가
        values = ["☐"] + list(values)
        kwargs['values'] = values
        return self.tree.insert(parent, index, **kwargs)
    
    def get_children(self):
        """자식 항목들 반환"""
        return self.tree.get_children()
    
    def delete(self, *items):
        """항목 삭제"""
        for item in items:
            self.checked_items.discard(item)
        return self.tree.delete(*items)
    
    def get_checked_items(self):
        """체크된 항목들 반환"""
        return list(self.checked_items)
    
    def select_all(self):
        """전체 선택"""
        all_items = self.tree.get_children()
        self.checked_items = set(all_items)
        for item in all_items:
            values = list(self.tree.item(item)['values'])
            values[0] = "☑"
            self.tree.item(item, values=values)
        self.selection_change_callback()
    
    def deselect_all(self):
        """전체 해제"""
        all_items = self.tree.get_children()
        self.checked_items.clear()
        for item in all_items:
            values = list(self.tree.item(item)['values'])
            values[0] = "☐"
            self.tree.item(item, values=values)
        self.selection_change_callback()
    
    def move(self, item, parent, index):
        """항목 이동"""
        return self.tree.move(item, parent, index)
    
    def item(self, item, option=None, **kwargs):
        """항목 정보 가져오기/설정"""
        return self.tree.item(item, option, **kwargs)


class YouTubeDeepSearch:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube DeepSearch")
        self.root.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        
        # YouTube API 초기화
        try:
            self.youtube_api = YouTubeAPI()
        except ValueError as e:
            messagebox.showerror("API 키 오류", str(e))
            self.root.destroy()
            return
        
        # 데이터 저장 변수
        self.current_videos = []
        self.selected_video = None
        
        # GUI 구성
        self.setup_ui()
    
    def setup_ui(self):
        """UI 구성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 검색 프레임
        self.setup_search_frame(main_frame)
        
        # 결과 프레임
        self.setup_result_frame(main_frame)
        
        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
    
    def setup_search_frame(self, parent):
        """검색 프레임 구성"""
        search_frame = ttk.LabelFrame(parent, text="검색 조건", padding="10")
        search_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 키워드 입력
        ttk.Label(search_frame, text="키워드:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.keyword_var = tk.StringVar()
        keyword_entry = ttk.Entry(search_frame, textvariable=self.keyword_var, width=30)
        keyword_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 영상 유형
        ttk.Label(search_frame, text="영상 유형:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.video_type_var = tk.StringVar(value="전체")
        video_type_combo = ttk.Combobox(search_frame, textvariable=self.video_type_var,
                                       values=["전체", "쇼츠", "20분 초과"], 
                                       state="readonly", width=10)
        video_type_combo.grid(row=0, column=3, padx=(0, 10))
        
        # 최소 조회수
        ttk.Label(search_frame, text="최소 조회수:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0), padx=(0, 5))
        self.min_views_var = tk.StringVar(value="제한 없음")
        min_views_combo = ttk.Combobox(search_frame, textvariable=self.min_views_var,
                                      values=["제한 없음", "1,000", "10,000", "50,000", "100,000", "500,000", "1,000,000"], 
                                      state="readonly", width=12)
        min_views_combo.grid(row=1, column=1, sticky=tk.W, pady=(5, 0), padx=(0, 10))
        
        # 최대 구독자 수
        ttk.Label(search_frame, text="최대 구독자 수:").grid(row=1, column=2, sticky=tk.W, pady=(5, 0), padx=(0, 5))
        self.max_subscribers_var = tk.StringVar(value="제한 없음")
        max_subscribers_combo = ttk.Combobox(search_frame, textvariable=self.max_subscribers_var,
                                           values=["제한 없음", "1,000", "10,000", "50,000", "100,000", "500,000", "1,000,000", "10,000,000"], 
                                           state="readonly", width=12)
        max_subscribers_combo.grid(row=1, column=3, sticky=tk.W, pady=(5, 0), padx=(0, 10))
        
        # 업로드 기간
        ttk.Label(search_frame, text="업로드 기간:").grid(row=2, column=0, sticky=tk.W, pady=(5, 0), padx=(0, 5))
        self.upload_period_var = tk.StringVar(value="전체")
        upload_period_combo = ttk.Combobox(search_frame, textvariable=self.upload_period_var,
                                          values=["전체", "1일", "1주일", "1개월", "3개월", "1년"], 
                                          state="readonly", width=10)
        upload_period_combo.grid(row=2, column=1, sticky=tk.W, pady=(5, 0), padx=(0, 10))
        
        # 최대 결과 수
        ttk.Label(search_frame, text="최대 결과 수:").grid(row=2, column=2, sticky=tk.W, pady=(5, 0), padx=(0, 5))
        self.max_results_var = tk.StringVar(value="100")
        max_results_entry = ttk.Entry(search_frame, textvariable=self.max_results_var, width=10)
        max_results_entry.grid(row=2, column=3, sticky=tk.W, pady=(5, 0), padx=(0, 10))
        
        # 검색 버튼
        search_button = ttk.Button(search_frame, text="검색", command=self.search_videos)
        search_button.grid(row=0, column=4, rowspan=3, padx=(10, 0), pady=5)
        
        # 그리드 가중치 설정
        search_frame.columnconfigure(1, weight=1)
        search_frame.columnconfigure(3, weight=1)
    
    def show_progress(self, text="처리 중..."):
        """프로그레스 바 표시"""
        self.progress_text.config(text=text)
        self.progress_text.pack(side=tk.TOP, anchor=tk.E, pady=(2, 0))
        self.progress_bar.pack(side=tk.TOP, fill=tk.X, pady=(2, 0))
        self.progress_bar.start(10)
        self.root.update()
    
    def hide_progress(self):
        """프로그레스 바 숨김"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.progress_text.pack_forget()
        self.root.update()
    
    def setup_result_frame(self, parent):
        """결과 프레임 구성"""
        result_frame = ttk.LabelFrame(parent, text="검색 결과", padding="5")
        result_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 트리뷰 설정
        self.tree = ttk.Treeview(result_frame, columns=config.MAIN_COLUMNS, show='headings', height=20)
        
        # 컬럼 설정
        for i, (col, width) in enumerate(zip(config.MAIN_COLUMNS, config.MAIN_COLUMN_WIDTHS)):
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(c))
            self.tree.column(col, width=width, minwidth=50)
        
        # 스크롤바
        v_scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(result_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 그리드 배치
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # 버튼 프레임
        button_frame = ttk.Frame(result_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # 채널 분석 버튼
        channel_analysis_button = ttk.Button(button_frame, text="채널 분석", 
                                           command=self.open_channel_analysis)
        channel_analysis_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # 선택된 영상 정보 레이블
        self.selected_info_label = ttk.Label(button_frame, text="영상을 선택해주세요")
        self.selected_info_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 상태 레이블과 프로그레스 바
        status_frame = ttk.Frame(button_frame)
        status_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        self.status_label = ttk.Label(status_frame, text="검색 결과가 없습니다.")
        self.status_label.pack(side=tk.TOP, anchor=tk.E)
        
        # 프로그레스 바 (처음에는 숨김)
        self.progress_bar = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress_text = ttk.Label(status_frame, text="", font=('Arial', 8))
        
        # 이벤트 바인딩
        self.tree.bind('<Double-1>', self.on_video_double_click)
        self.tree.bind('<ButtonRelease-1>', self.on_video_select)
        
        # 그리드 가중치 설정
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
    
    def search_videos(self):
        """영상 검색"""
        keyword = self.keyword_var.get().strip()
        if not keyword:
            messagebox.showwarning("입력 오류", "키워드를 입력해주세요.")
            return
        
        # 검색 조건 가져오기
        video_type = self.video_type_var.get()
        if video_type == "전체":
            video_type = "all"
        
        try:
            # 최소 조회수 처리
            min_views_str = self.min_views_var.get()
            if min_views_str == "제한 없음":
                min_views = 0
            else:
                min_views = int(min_views_str.replace(",", ""))
            
            # 최대 구독자 수 처리
            max_subscribers_str = self.max_subscribers_var.get()
            if max_subscribers_str == "제한 없음":
                max_subscribers = None
            else:
                max_subscribers = int(max_subscribers_str.replace(",", ""))
            
            max_results = int(self.max_results_var.get() or 100)
        except ValueError:
            messagebox.showerror("입력 오류", "숫자 입력 항목을 확인해주세요.")
            return
        
        upload_period = self.upload_period_var.get()
        if upload_period == "전체":
            upload_period = None
        
        # 상태 업데이트
        self.status_label.config(text="검색 준비 중...")
        self.show_progress("영상 검색 중...")
        
        # 별도 스레드에서 검색 실행
        def search_thread():
            try:
                videos = self.youtube_api.search_videos(
                    keyword=keyword,
                    video_type=video_type,
                    min_views=min_views,
                    max_subscribers=max_subscribers,
                    upload_period=upload_period,
                    max_results=max_results,
                    progress_callback=self.update_search_progress
                )
                
                # UI 업데이트는 메인 스레드에서
                self.root.after(0, lambda: self.update_search_results(videos))
                
            except Exception as e:
                self.root.after(0, lambda: self.show_search_error(str(e)))
        
        threading.Thread(target=search_thread, daemon=True).start()
    
    def update_search_progress(self, message):
        """검색 진행 상황 업데이트"""
        def update_ui():
            self.progress_text.config(text=message)
            self.root.update()
        self.root.after(0, update_ui)
    
    def update_search_results(self, videos):
        """검색 결과 업데이트"""
        self.hide_progress()  # 프로그레스 바 숨김
        self.current_videos = videos
        
        # 기존 항목 삭제
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 새 항목 추가
        for video in videos:
            # 지속 시간 포맷팅
            duration = self.format_duration(video['duration_seconds'])
            
            # 조회수 포맷팅
            views = self.format_number(video['view_count'])
            
            # 구독자 수 포맷팅
            subscribers = self.format_number(video['subscriber_count'])
            
            # 트리뷰에 추가
            self.tree.insert('', 'end', values=(
                video['title'][:50] + "..." if len(video['title']) > 50 else video['title'],
                views,
                video['outlier_score'],
                duration,
                subscribers,
                video['channel_title'][:20] + "..." if len(video['channel_title']) > 20 else video['channel_title']
            ))
        
        # 상태 업데이트
        self.status_label.config(text=f"총 {len(videos)}개 영상을 찾았습니다.")
        
        # 선택 상태 초기화
        self.selected_video = None
        self.selected_info_label.config(text="영상을 선택해주세요")
    
    def show_search_error(self, error_msg):
        """검색 오류 표시"""
        self.hide_progress()  # 프로그레스 바 숨김
        self.status_label.config(text="검색 실패")
        messagebox.showerror("검색 오류", f"검색 중 오류가 발생했습니다:\n{error_msg}")
    
    def format_duration(self, seconds):
        """초를 분:초 형식으로 변환"""
        if seconds < 60:
            return f"{seconds}초"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}:{secs:02d}"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours}:{minutes:02d}:{secs:02d}"
    
    def format_number(self, number):
        """숫자를 K, M 형식으로 포맷팅"""
        if number >= 1000000:
            return f"{number/1000000:.1f}M"
        elif number >= 1000:
            return f"{number/1000:.1f}K"
        else:
            return str(number)
    
    def sort_treeview(self, column):
        """트리뷰 정렬"""
        # 현재 정렬 상태 확인
        current_sort = getattr(self, f'sort_{column}', 'asc')
        reverse = current_sort == 'desc'
        
        # 트리뷰의 모든 항목과 해당하는 비디오 데이터 가져오기
        items_data = []
        for i, child in enumerate(self.tree.get_children()):
            if i < len(self.current_videos):
                video_data = self.current_videos[i]
                items_data.append((child, video_data))
        
        # 컬럼별 정렬 키 함수
        def sort_key(item):
            video = item[1]  # video_data
            
            if column == 'Title':
                return video['title'].lower()
            elif column == 'Views':
                return video['view_count']
            elif column == 'Outlier Score':
                return video['outlier_score']
            elif column == 'Duration':
                return video['duration_seconds']
            elif column == 'Subscribers':
                return video['subscriber_count']
            elif column == 'Channel':
                return video['channel_title'].lower()
            else:
                return 0
        
        # 정렬 실행
        items_data.sort(key=sort_key, reverse=reverse)
        
        # 트리뷰와 current_videos 동시에 재정렬
        sorted_videos = []
        for i, (child, video_data) in enumerate(items_data):
            self.tree.move(child, '', i)
            sorted_videos.append(video_data)
        
        # current_videos 업데이트
        self.current_videos = sorted_videos
        
        # 정렬 상태 업데이트
        setattr(self, f'sort_{column}', 'desc' if current_sort == 'asc' else 'asc')
    
    def on_video_double_click(self, event):
        """영상 더블클릭 이벤트"""
        selection = self.tree.selection()
        if selection:
            index = self.tree.get_children().index(selection[0])
            if index < len(self.current_videos):
                video = self.current_videos[index]
                webbrowser.open(video['url'])
    
    def on_video_select(self, event):
        """영상 선택 이벤트"""
        selection = self.tree.selection()
        if selection:
            index = self.tree.get_children().index(selection[0])
            if index < len(self.current_videos):
                self.selected_video = self.current_videos[index]
                # 선택된 영상 정보 표시
                title = self.selected_video['title']
                if len(title) > 30:
                    title = title[:30] + "..."
                self.selected_info_label.config(
                    text=f"선택: {title} (채널: {self.selected_video['channel_title']})"
                )
        else:
            self.selected_video = None
            self.selected_info_label.config(text="영상을 선택해주세요")
    
    def open_channel_analysis(self):
        """채널 분석 창 열기"""
        if not self.selected_video:
            messagebox.showwarning("선택 오류", "분석할 영상을 선택해주세요.")
            return
        
        # 채널 분석 창 생성
        analysis_window = ChannelAnalysisWindow(self.root, self.youtube_api, self.selected_video)


class ChannelAnalysisWindow:
    def __init__(self, parent, youtube_api, video):
        self.youtube_api = youtube_api
        self.video = video
        self.channel_videos = []
        self.selected_videos = []
        
        # 창 생성
        self.window = tk.Toplevel(parent)
        self.window.title(f"채널 분석 - {video['channel_title']}")
        self.window.geometry(f"{config.ANALYSIS_WINDOW_WIDTH}x{config.ANALYSIS_WINDOW_HEIGHT}")
        
        # UI 구성
        self.setup_ui()
        
        # 채널 영상 로드
        self.load_channel_videos()
    
    def setup_ui(self):
        """UI 구성"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 채널 정보 프레임
        info_frame = ttk.LabelFrame(main_frame, text="채널 정보", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text=f"채널명: {self.video['channel_title']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"구독자 수: {self.format_number(self.video['subscriber_count'])}").pack(anchor=tk.W)
        
        # 영상 목록 프레임
        videos_frame = ttk.LabelFrame(main_frame, text="채널 영상 목록", padding="5")
        videos_frame.pack(fill=tk.BOTH, expand=True)
        
        # 트리뷰 설정
        self.tree = CheckboxTreeview(videos_frame, config.CHANNEL_COLUMNS, config.CHANNEL_COLUMN_WIDTHS, height=15)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 콜백 함수 설정
        self.tree.sort_callback = self.sort_treeview
        self.tree.double_click_callback = self.on_video_double_click
        self.tree.selection_change_callback = self.update_selection_status
        
        # 추가 이벤트 바인딩 (더블클릭)
        self.tree.tree.bind('<Double-1>', lambda event: self.on_video_double_click())
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 전체 선택/해제 버튼
        ttk.Button(button_frame, text="전체 선택", command=self.tree.select_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="선택 해제", command=self.tree.deselect_all).pack(side=tk.LEFT, padx=(0, 10))
        
        # 추출 버튼들
        ttk.Button(button_frame, text="제목 추출", command=self.extract_titles).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="썸네일 추출", command=self.extract_thumbnails).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="대본 추출", command=self.extract_transcripts).pack(side=tk.LEFT, padx=(0, 5))
        
        # 상태 레이블
        self.status_label = ttk.Label(button_frame, text="채널 영상을 로드하는 중...")
        self.status_label.pack(side=tk.RIGHT)
    
    def on_video_select(self, event):
        """영상 선택 이벤트"""
        # 약간의 지연 후 선택 상태 업데이트 (GUI 업데이트 후)
        self.window.after(100, self.update_selection_status)
    
    def update_selection_status(self):
        """선택 상태 업데이트"""
        checked_count = len(self.tree.get_checked_items())
        total_count = len(self.channel_videos)
        
        if checked_count == 0:
            self.status_label.config(text=f"총 {total_count}개 영상")
        else:
            self.status_label.config(text=f"총 {total_count}개 영상 (선택: {checked_count}개)")
    
    def format_number(self, number):
        """숫자를 K, M 형식으로 포맷팅"""
        if number >= 1000000:
            return f"{number/1000000:.1f}M"
        elif number >= 1000:
            return f"{number/1000:.1f}K"
        else:
            return str(number)
    
    def load_channel_videos(self):
        """채널 영상 로드"""
        def load_thread():
            try:
                videos = self.youtube_api.get_channel_videos(self.video['channel_id'], max_results=200)
                self.window.after(0, lambda: self.update_video_list(videos))
            except Exception as e:
                self.window.after(0, lambda: self.show_load_error(str(e)))
        
        threading.Thread(target=load_thread, daemon=True).start()
    
    def update_video_list(self, videos):
        """영상 목록 업데이트"""
        self.channel_videos = videos
        
        # 기존 항목 삭제
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 새 항목 추가
        for video in videos:
            # 날짜 포맷팅
            published_date = datetime.strptime(video['published_at'][:10], '%Y-%m-%d').strftime('%Y-%m-%d')
            
            # 지속 시간 포맷팅
            duration = self.format_duration(video['duration_seconds'])
            
            # 조회수 포맷팅
            views = self.format_number(video['view_count'])
            
            # 트리뷰에 추가
            self.tree.insert('', 'end', values=(
                video['title'][:50] + "..." if len(video['title']) > 50 else video['title'],
                views,
                video['outlier_score'],
                duration,
                published_date
            ))
        
        # 상태 업데이트
        self.status_label.config(text=f"총 {len(videos)}개 영상")
        
        # 초기 선택 상태 업데이트
        self.update_selection_status()
    
    def show_load_error(self, error_msg):
        """로드 오류 표시"""
        self.status_label.config(text="로드 실패")
        messagebox.showerror("로드 오류", f"채널 영상 로드 중 오류가 발생했습니다:\n{error_msg}")
    
    def format_duration(self, seconds):
        """초를 분:초 형식으로 변환"""
        if seconds < 60:
            return f"{seconds}초"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}:{secs:02d}"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours}:{minutes:02d}:{secs:02d}"
    
    def sort_treeview(self, column):
        """트리뷰 정렬"""
        # 현재 정렬 상태 확인
        current_sort = getattr(self, f'sort_{column}', 'asc')
        reverse = current_sort == 'desc'
        
        # 트리뷰의 모든 항목과 해당하는 비디오 데이터 가져오기
        items_data = []
        for i, child in enumerate(self.tree.get_children()):
            if i < len(self.channel_videos):
                video_data = self.channel_videos[i]
                items_data.append((child, video_data))
        
        # 컬럼별 정렬 키 함수
        def sort_key(item):
            video = item[1]  # video_data
            
            if column == 'Title':
                return video['title'].lower()
            elif column == 'Views':
                return video['view_count']
            elif column == 'Outlier Score':
                return video['outlier_score']
            elif column == 'Duration':
                return video['duration_seconds']
            elif column == 'Published':
                try:
                    return datetime.strptime(video['published_at'][:10], '%Y-%m-%d')
                except:
                    return datetime.min
            else:
                return 0
        
        # 정렬 실행
        items_data.sort(key=sort_key, reverse=reverse)
        
        # 트리뷰와 channel_videos 동시에 재정렬
        sorted_videos = []
        for i, (child, video_data) in enumerate(items_data):
            self.tree.move(child, '', i)
            sorted_videos.append(video_data)
        
        # channel_videos 업데이트
        self.channel_videos = sorted_videos
        
        # 정렬 상태 업데이트
        setattr(self, f'sort_{column}', 'desc' if current_sort == 'asc' else 'asc')
    
    def select_all(self):
        """전체 선택"""
        children = self.tree.get_children()
        self.tree.selection_set(children)
    
    def deselect_all(self):
        """선택 해제"""
        self.tree.selection_remove(self.tree.selection())
    
    def get_selected_videos(self):
        """선택된 영상들 가져오기"""
        selected_videos = []
        checked_items = self.tree.get_checked_items()
        
        for item in checked_items:
            index = self.tree.get_children().index(item)
            if index < len(self.channel_videos):
                selected_videos.append(self.channel_videos[index])
        
        return selected_videos
    
    def extract_titles(self):
        """선택된 영상들의 제목 추출"""
        selected_videos = self.get_selected_videos()
        
        if not selected_videos:
            messagebox.showwarning("선택 오류", "추출할 영상을 선택해주세요.")
            return
        
        # 파일 저장 대화상자
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="제목 목록 저장"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for i, video in enumerate(selected_videos, 1):
                        f.write(f"{i}. {video['title']}\n")
                        f.write(f"   URL: {video['url']}\n")
                        f.write(f"   조회수: {self.format_number(video['view_count'])}\n")
                        f.write(f"   게시일: {video['published_at'][:10]}\n\n")
                
                messagebox.showinfo("완료", f"제목 목록이 저장되었습니다.\n({len(selected_videos)}개 영상)")
                
            except Exception as e:
                messagebox.showerror("저장 오류", f"파일 저장 중 오류가 발생했습니다:\n{e}")
    
    def extract_thumbnails(self):
        """선택된 영상들의 썸네일 추출"""
        selected_videos = self.get_selected_videos()
        
        if not selected_videos:
            messagebox.showwarning("선택 오류", "추출할 영상을 선택해주세요.")
            return
        
        # 폴더 선택 대화상자
        folder_path = filedialog.askdirectory(title="썸네일 저장 폴더 선택")
        
        if folder_path:
            self.status_label.config(text="썸네일 다운로드 중...")
            self.window.update()
            
            def download_thread():
                success_count = 0
                for i, video in enumerate(selected_videos):
                    try:
                        # 안전한 파일명 생성
                        safe_title = "".join(c for c in video['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                        safe_title = safe_title[:50]  # 길이 제한
                        
                        file_name = f"{i+1:03d}_{safe_title}_{video['video_id']}.jpg"
                        file_path = os.path.join(folder_path, file_name)
                        
                        if self.youtube_api.download_thumbnail(video['thumbnail_url'], file_path):
                            success_count += 1
                        
                        # 진행상황 업데이트
                        progress = f"썸네일 다운로드 중... ({i+1}/{len(selected_videos)})"
                        self.window.after(0, lambda p=progress: self.status_label.config(text=p))
                        
                    except Exception as e:
                        print(f"썸네일 다운로드 오류 ({video['title']}): {e}")
                
                # 완료 메시지
                message = f"썸네일 다운로드 완료!\n성공: {success_count}/{len(selected_videos)}"
                self.window.after(0, lambda: messagebox.showinfo("완료", message))
                self.window.after(0, lambda: self.status_label.config(text=f"총 {len(self.channel_videos)}개 영상"))
            
            threading.Thread(target=download_thread, daemon=True).start()
    
    def extract_transcripts(self):
        """선택된 영상들의 대본 추출"""
        selected_videos = self.get_selected_videos()
        
        if not selected_videos:
            messagebox.showwarning("선택 오류", "추출할 영상을 선택해주세요.")
            return
        
        # 폴더 선택 대화상자로 변경 (개별 파일로 저장)
        folder_path = filedialog.askdirectory(title="대본 저장 폴더 선택")
        
        if folder_path:
            self.status_label.config(text="대본 추출 중...")
            self.window.update()
            
            def extract_thread():
                extracted_count = 0
                
                try:
                    for i, video in enumerate(selected_videos):
                        try:
                            # 진행상황 업데이트
                            progress = f"대본 추출 중... ({i+1}/{len(selected_videos)})"
                            def update_progress(text=progress):
                                self.status_label.config(text=text)
                            self.window.after(0, update_progress)
                            
                            # 안전한 파일명 생성: "채널명 : 영상제목" (Windows에서는 콜론을 언더스코어로 변경)
                            channel_name = "".join(c for c in video['channel_title'] if c.isalnum() or c in (' ', '-', '_')).strip()
                            video_title = "".join(c for c in video['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
                            
                            # 파일명 길이 제한
                            channel_name = channel_name[:30]
                            video_title = video_title[:50]
                            
                            filename = f"{channel_name} _ {video_title}.txt"
                            file_path = os.path.join(folder_path, filename)
                            
                            # 중복 파일명 처리
                            counter = 1
                            original_path = file_path
                            while os.path.exists(file_path):
                                name, ext = os.path.splitext(original_path)
                                file_path = f"{name}_{counter}{ext}"
                                counter += 1
                            
                            # 대본 가져오기 (개선된 오류 처리)
                            try:
                                # 진행상황 표시
                                def update_detailed_progress(text=f"대본 추출 중... ({video['title'][:30]}...)"):
                                    self.status_label.config(text=text)
                                self.window.after(0, update_detailed_progress)
                                
                                transcript = self.youtube_api.get_video_transcript(video['video_id'], use_whisper=True)
                                
                                if transcript and transcript.strip():
                                    # 성공적으로 추출된 경우
                                    if "오류가 발생했습니다" in transcript or "추출할 수 없습니다" in transcript or "자막이 없는 영상입니다" in transcript:
                                        # 오류 메시지인 경우 - 오류 로그에만 기록
                                        print(f"대본 추출 실패: {video['title'][:50]}... - {transcript}")
                                        # 오류인 경우 파일을 생성하지 않고 다음 영상으로
                                    else:
                                        # 정상적인 대본인 경우 - 대본 내용만 저장
                                        with open(file_path, 'w', encoding='utf-8') as f:
                                            f.write(transcript)
                                        extracted_count += 1
                                        print(f"대본 추출 성공: {video['title'][:50]}...")
                                else:
                                    print(f"대본 추출 실패: {video['title'][:50]}... - 대본이 없거나 비공개 영상")
                                    # 실패한 경우 파일을 생성하지 않음
                                    
                            except Exception as transcript_error:
                                print(f"대본 추출 오류: {video['title'][:50]}... - {str(transcript_error)[:100]}...")
                                # 오류인 경우 파일을 생성하지 않음
                                
                                # 요청 간격 조정 (API 제한 방지)
                                import time
                                time.sleep(0.5)
                                
                        except Exception as e:
                            error_msg = f"파일 생성 오류: {e}"
                            print(f"파일 생성 오류 ({video['title']}): {e}")
                            
                            # 상세 오류 로그 파일 생성
                            try:
                                error_file = os.path.join(folder_path, "오류_로그.txt")
                                with open(error_file, 'a', encoding='utf-8') as ef:
                                    ef.write(f"{'='*80}\n")
                                    ef.write(f"오류 발생 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                                    ef.write(f"영상 제목: {video['title']}\n")
                                    ef.write(f"영상 ID: {video['video_id']}\n")
                                    ef.write(f"채널명: {video['channel_title']}\n")
                                    ef.write(f"오류 내용: {error_msg}\n")
                                    ef.write(f"영상 URL: {video['url']}\n")
                                    ef.write(f"{'='*80}\n\n")
                            except Exception as log_error:
                                print(f"오류 로그 작성 실패: {log_error}")
                    
                    # 완료 메시지
                    message = f"대본 추출 완료!\n\n"
                    message += f"결과 요약:\n"
                    message += f"• 성공: {extracted_count}/{len(selected_videos)}\n"
                    message += f"• 실패: {len(selected_videos) - extracted_count}/{len(selected_videos)}\n"
                    message += f"• 저장 위치: {folder_path}\n\n"
                    message += f"참고사항:\n"
                    message += f"• YouTube 자막이 있는 영상만 추출됩니다\n"
                    message += f"• 자막이 없는 영상은 건너뜁니다\n"
                    message += f"• 대본 내용만 깔끔하게 저장됩니다"
                    def show_complete():
                        messagebox.showinfo("대본 추출 완료", message)
                    self.window.after(0, show_complete)
                    
                except Exception as e:
                    def show_error():
                        messagebox.showerror("저장 오류", f"대본 추출 중 오류가 발생했습니다:\n{e}")
                    self.window.after(0, show_error)
                
                def reset_status():
                    self.status_label.config(text=f"총 {len(self.channel_videos)}개 영상")
                self.window.after(0, reset_status)
            
            threading.Thread(target=extract_thread, daemon=True).start()
    
    def on_video_double_click(self):
        """영상 더블클릭 이벤트"""
        try:
            selection = self.tree.tree.selection()
            if selection:
                index = list(self.tree.tree.get_children()).index(selection[0])
                if 0 <= index < len(self.channel_videos):
                    video = self.channel_videos[index]
                    webbrowser.open(video['url'])
        except Exception as e:
            print(f"더블클릭 이벤트 오류: {e}")
            # 오류가 발생해도 계속 진행


def main():
    """메인 함수"""
    # API 키 확인
    if config.YOUTUBE_API_KEY == "YOUR_YOUTUBE_API_KEY_HERE":
        root = tk.Tk()
        root.withdraw()  # 메인 창 숨기기
        messagebox.showerror(
            "API 키 설정 필요", 
            "YouTube Data API 키를 설정해주세요.\n\n"
            "1. https://console.developers.google.com/apis/credentials 에서 API 키 발급\n"
            "2. config.py 파일의 YOUTUBE_API_KEY 값 수정\n"
            "3. 프로그램 재실행"
        )
        return
    
    # GUI 시작
    root = tk.Tk()
    app = YouTubeDeepSearch(root)
    root.mainloop()


if __name__ == "__main__":
    main()
