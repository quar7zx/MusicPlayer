import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import pygame
import os
import json
import random
import time
from mutagen.mp3 import MP3
from tkinter import font as tkfont
from collections import deque

class ModernMusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Music")
        self.root.geometry("1200x800")
        self.root.configure(bg='#000000')
        
        # Пути для хранения данных
        self.data_dir = "music_player_data"
        self.playlists_file = os.path.join(self.data_dir, "playlists.json")
        
        # Создаем директорию для данных если ее нет
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Инициализация pygame mixer
        pygame.mixer.init()
        
        # Переменные
        self.playlist = []
        self.current_song_index = 0
        self.paused = False
        self.playing = False
        self.volume = 0.7
        self.song_length = 0
        self.current_time = 0
        pygame.mixer.music.set_volume(self.volume)
        
        # Плейлисты
        self.user_playlists = {}
        self.current_playlist = "main"
        
        # История прослушивания
        self.recently_played = deque(maxlen=10)
        
        # Словарь для хранения треков в интерфейсе
        self.track_frames = {}
        
        # Загружаем плейлисты
        self.load_playlists()
        
        # Кастомные шрифты
        self.setup_fonts()
        
        # Создание интерфейса
        self.create_widgets()
        
        # Загрузка тестовых треков (опционально)
        self.load_sample_tracks()
        
        # Обновление времени
        self.update_time()
        
        # Анимация
        self.animate_visualizer()
        
        # Привязка горячих клавиш
        self.bind_hotkeys()
        
        # Микширование
        self.mix_mode = False
        self.mix_interval = 3000  # 3 секунды между треками в режиме микса
        self.mix_timer = None
    
    def load_playlists(self):
        """Загружает плейлисты из файла"""
        if os.path.exists(self.playlists_file):
            try:
                with open(self.playlists_file, 'r', encoding='utf-8') as f:
                    self.user_playlists = json.load(f)
            except:
                self.user_playlists = {"main": [], "избранное": []}
        else:
            self.user_playlists = {"main": [], "избранное": []}
        
        # Загружаем текущий плейлист
        self.playlist = self.user_playlists.get(self.current_playlist, [])
    
    def save_playlists(self):
        """Сохраняет плейлисты в файл"""
        with open(self.playlists_file, 'w', encoding='utf-8') as f:
            json.dump(self.user_playlists, f, ensure_ascii=False, indent=2)
    
    def setup_fonts(self):
        self.title_font = ('Segoe UI', 24, 'bold')
        self.subtitle_font = ('Segoe UI', 14)
        self.button_font = ('Segoe UI', 11, 'bold')
        self.song_font = ('Segoe UI', 12)
        self.time_font = ('Segoe UI', 10)
        
        available_fonts = ['Segoe UI', 'Helvetica', 'Arial', 'Montserrat']
        for font_name in available_fonts:
            try:
                test_font = tkfont.Font(family=font_name, size=12)
                self.title_font = (font_name, 24, 'bold')
                break
            except:
                continue
    
    def bind_hotkeys(self):
        """Привязка горячих клавиш"""
        self.root.bind('<space>', lambda e: self.play_pause())
        self.root.bind('<Right>', lambda e: self.next_song())
        self.root.bind('<Left>', lambda e: self.prev_song())
        self.root.bind('<Up>', lambda e: self.volume_up())
        self.root.bind('<Down>', lambda e: self.volume_down())
        self.root.bind('<Escape>', lambda e: self.root.quit())
        self.root.bind('<m>', lambda e: self.toggle_mix())
    
    def volume_up(self):
        """Увеличить громкость"""
        current_vol = self.volume_slider.get()
        if current_vol < 100:
            new_vol = min(100, current_vol + 10)
            self.volume_slider.set(new_vol)
            self.set_volume(new_vol)
    
    def volume_down(self):
        """Уменьшить громкость"""
        current_vol = self.volume_slider.get()
        if current_vol > 0:
            new_vol = max(0, current_vol - 10)
            self.volume_slider.set(new_vol)
            self.set_volume(new_vol)
    
    def create_widgets(self):
        # Главный контейнер
        main_container = tk.Frame(self.root, bg='#000000')
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Боковая панель (навигация)
        self.create_sidebar(main_container)
        
        # Основная область
        main_area = tk.Frame(main_container, bg='#000000')
        main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Верхняя панель
        self.create_top_bar(main_area)
        
        # Контент
        self.content_frame = tk.Frame(main_area, bg='#121212')
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 100))
        
        # Заголовок
        title_frame = tk.Frame(self.content_frame, bg='#121212')
        title_frame.pack(fill=tk.X, pady=(20, 10))
        
        self.welcome_label = tk.Label(title_frame, 
                                    text=f"Music Player - {self.current_playlist}", 
                                    font=self.title_font,
                                    bg='#121212',
                                    fg='white')
        self.welcome_label.pack(side=tk.LEFT)
        
        # Быстрые действия
        quick_actions = tk.Frame(self.content_frame, bg='#121212')
        quick_actions.pack(fill=tk.X, pady=(0, 20))
        
        action_btn = tk.Button(quick_actions,
                             text="🎵 Добавить музыку",
                             command=self.add_songs,
                             bg='#1DB954',
                             fg='white',
                             font=self.button_font,
                             relief='flat',
                             padx=20,
                             pady=10,
                             cursor='hand2',
                             activebackground='#1ED760')
        action_btn.pack(side=tk.LEFT)
        
        # Кнопка очистки плейлиста
        clear_btn = tk.Button(quick_actions,
                            text="🗑️ Очистить плейлист",
                            command=self.clear_playlist,
                            bg='#E22134',
                            fg='white',
                            font=self.button_font,
                            relief='flat',
                            padx=20,
                            pady=10,
                            cursor='hand2',
                            activebackground='#FF3B30')
        clear_btn.pack(side=tk.LEFT, padx=10)
        
        # Кнопка создания микса
        mix_btn = tk.Button(quick_actions,
                          text="🔀 Создать микс",
                          command=self.create_mix,
                          bg='#9C27B0',
                          fg='white',
                          font=self.button_font,
                          relief='flat',
                          padx=20,
                          pady=10,
                          cursor='hand2',
                          activebackground='#BA68C8')
        mix_btn.pack(side=tk.LEFT, padx=10)
        
        # Визуализатор и плейлист
        visualizer_frame = tk.Frame(self.content_frame, bg='#181818')
        visualizer_frame.pack(fill=tk.BOTH, expand=True)
        
        # Визуализатор
        viz_container = tk.Frame(visualizer_frame, bg='#181818')
        viz_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Визуализатор барами
        self.viz_canvas = tk.Canvas(viz_container, bg='#181818', 
                                   highlightthickness=0, height=200)
        self.viz_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Плейлист
        playlist_container = tk.Frame(visualizer_frame, bg='#181818', width=400)
        playlist_container.pack(side=tk.RIGHT, fill=tk.BOTH)
        playlist_container.pack_propagate(False)
        
        playlist_header = tk.Frame(playlist_container, bg='#181818')
        playlist_header.pack(fill=tk.X, pady=(10, 5))
        
        self.playlist_title = tk.Label(playlist_header,
                                     text=f"Плейлист: {self.current_playlist}",
                                     font=('Segoe UI', 16, 'bold'),
                                     bg='#181818',
                                     fg='white')
        self.playlist_title.pack(side=tk.LEFT)
        
        # Счетчик треков
        self.track_count_label = tk.Label(playlist_header,
                                        text=f"{len(self.playlist)} треков",
                                        font=self.time_font,
                                        bg='#181818',
                                        fg='#b3b3b3')
        self.track_count_label.pack(side=tk.RIGHT, padx=20)
        
        # Список песен с прокруткой
        playlist_scroll = tk.Frame(playlist_container, bg='#181818')
        playlist_scroll.pack(fill=tk.BOTH, expand=True)
        
        # Canvas для скроллинга
        self.playlist_canvas = tk.Canvas(playlist_scroll, bg='#181818', 
                                        highlightthickness=0)
        scrollbar = ttk.Scrollbar(playlist_scroll, orient="vertical", 
                                 command=self.playlist_canvas.yview)
        self.scrollable_frame = tk.Frame(self.playlist_canvas, bg='#181818')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.playlist_canvas.configure(
                scrollregion=self.playlist_canvas.bbox("all")
            )
        )
        
        self.playlist_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.playlist_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.playlist_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.playlist_frame = self.scrollable_frame
        
        # Загружаем треки текущего плейлиста
        self.refresh_playlist_display()
        
        # Нижняя панель управления
        self.create_player_bar(main_area)
    
    def create_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg='#000000', width=250)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        # Логотип
        logo_frame = tk.Frame(sidebar, bg='#000000', height=100)
        logo_frame.pack(fill=tk.X)
        logo_frame.pack_propagate(False)
        
        logo = tk.Label(logo_frame,
                       text="🎵 Music",
                       font=('Segoe UI', 24, 'bold'),
                       bg='#000000',
                       fg='#1DB954')
        logo.pack(pady=30)
        
        # Меню навигации
        nav_items = [
            ("🏠", "Главная", self.show_home),
            ("🔍", "Поиск", self.show_search),
            ("📚", "Библиотека", self.show_library),
            ("⭐", "Избранное", self.show_favorites),
            ("➕", "Создать плейлист", self.create_new_playlist_dialog),
        ]
        
        self.nav_buttons = {}
        
        for icon, text, command in nav_items:
            btn = tk.Button(sidebar,
                          text=f"   {icon}  {text}",
                          font=self.button_font,
                          bg='#000000',
                          fg='#b3b3b3',
                          anchor='w',
                          relief='flat',
                          padx=20,
                          pady=15,
                          cursor='hand2',
                          command=command)
            btn.pack(fill=tk.X)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg='#282828'))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg='#000000'))
            self.nav_buttons[text] = btn
        
        # Активируем главную страницу
        self.activate_nav_button("Главная")
        
        # Разделитель
        separator = tk.Frame(sidebar, height=2, bg='#282828')
        separator.pack(fill=tk.X, pady=20, padx=20)
        
        # Плейлисты пользователя
        playlists_label = tk.Label(sidebar,
                                 text="МОИ ПЛЕЙЛИСТЫ",
                                 font=('Segoe UI', 10, 'bold'),
                                 bg='#000000',
                                 fg='#b3b3b3')
        playlists_label.pack(anchor='w', padx=20, pady=(0, 10))
        
        # Контейнер для плейлистов
        self.playlists_container = tk.Frame(sidebar, bg='#000000')
        self.playlists_container.pack(fill=tk.BOTH, expand=True, padx=10)
        
        # Загружаем плейлисты пользователя
        self.load_user_playlists()
    
    def load_user_playlists(self):
        """Загружает плейлисты пользователя в боковую панель"""
        # Очищаем контейнер
        for widget in self.playlists_container.winfo_children():
            widget.destroy()
        
        # Добавляем кнопки для каждого плейлиста
        for playlist_name in self.user_playlists.keys():
            btn = tk.Button(self.playlists_container,
                          text=f"   📁  {playlist_name}",
                          font=('Segoe UI', 11),
                          bg='#000000',
                          fg='#b3b3b3',
                          anchor='w',
                          relief='flat',
                          padx=10,
                          pady=8,
                          cursor='hand2',
                          command=lambda name=playlist_name: self.switch_playlist(name))
            btn.pack(fill=tk.X)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg='#282828'))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg='#000000'))
    
    def switch_playlist(self, playlist_name):
        """Переключается на указанный плейлист"""
        if playlist_name in self.user_playlists:
            self.current_playlist = playlist_name
            self.playlist = self.user_playlists[playlist_name]
            
            # Обновляем отображение
            self.refresh_playlist_display()
            
            # Обновляем заголовки
            self.welcome_label.config(text=f"Music Player - {playlist_name}")
            self.playlist_title.config(text=f"Плейлист: {playlist_name}")
            
            # Обновляем счетчик
            self.update_track_count()
            
            print(f"Переключен на плейлист: {playlist_name}")
    
    def activate_nav_button(self, button_name):
        """Активирует кнопку навигации (меняет цвет)"""
        for name, btn in self.nav_buttons.items():
            if name == button_name:
                btn.config(fg='white', bg='#282828')
            else:
                btn.config(fg='#b3b3b3', bg='#000000')
    
    def show_home(self):
        """Показать главную страницу"""
        self.activate_nav_button("Главная")
        self.show_home_content()
    
    def show_home_content(self):
        """Показывает содержимое главной страницы"""
        # Очищаем контент
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Заголовок
        title_frame = tk.Frame(self.content_frame, bg='#121212')
        title_frame.pack(fill=tk.X, pady=(20, 10))
        
        self.welcome_label = tk.Label(title_frame, 
                                    text=f"Music Player - {self.current_playlist}", 
                                    font=self.title_font,
                                    bg='#121212',
                                    fg='white')
        self.welcome_label.pack(side=tk.LEFT)
        
        # Быстрые действия
        quick_actions = tk.Frame(self.content_frame, bg='#121212')
        quick_actions.pack(fill=tk.X, pady=(0, 20))
        
        action_btn = tk.Button(quick_actions,
                             text="🎵 Добавить музыку",
                             command=self.add_songs,
                             bg='#1DB954',
                             fg='white',
                             font=self.button_font,
                             relief='flat',
                             padx=20,
                             pady=10,
                             cursor='hand2',
                             activebackground='#1ED760')
        action_btn.pack(side=tk.LEFT)
        
        # Кнопка очистки плейлиста
        clear_btn = tk.Button(quick_actions,
                            text="🗑️ Очистить плейлист",
                            command=self.clear_playlist,
                            bg='#E22134',
                            fg='white',
                            font=self.button_font,
                            relief='flat',
                            padx=20,
                            pady=10,
                            cursor='hand2',
                            activebackground='#FF3B30')
        clear_btn.pack(side=tk.LEFT, padx=10)
        
        # Кнопка создания микса
        mix_btn = tk.Button(quick_actions,
                          text="🔀 Создать микс",
                          command=self.create_mix,
                          bg='#9C27B0',
                          fg='white',
                          font=self.button_font,
                          relief='flat',
                          padx=20,
                          pady=10,
                          cursor='hand2',
                          activebackground='#BA68C8')
        mix_btn.pack(side=tk.LEFT, padx=10)
        
        # Статистика
        stats_frame = tk.Frame(self.content_frame, bg='#181818')
        stats_frame.pack(fill=tk.X, pady=(0, 20))
        
        total_tracks = sum(len(tracks) for tracks in self.user_playlists.values())
        
        stats = [
            (f"{len(self.playlist)}", f"Треков в {self.current_playlist}"),
            (f"{len(self.user_playlists)}", "Плейлистов"),
            (f"{total_tracks}", "Всего треков")
        ]
        
        for value, label in stats:
            stat_frame = tk.Frame(stats_frame, bg='#181818')
            stat_frame.pack(side=tk.LEFT, expand=True, padx=10, pady=10)
            
            value_label = tk.Label(stat_frame,
                                 text=value,
                                 font=('Segoe UI', 24, 'bold'),
                                 bg='#181818',
                                 fg='#1DB954')
            value_label.pack()
            
            label_label = tk.Label(stat_frame,
                                 text=label,
                                 font=self.time_font,
                                 bg='#181818',
                                 fg='#b3b3b3')
            label_label.pack()
        
        # Визуализатор и плейлист
        visualizer_frame = tk.Frame(self.content_frame, bg='#181818')
        visualizer_frame.pack(fill=tk.BOTH, expand=True)
        
        # Визуализатор
        viz_container = tk.Frame(visualizer_frame, bg='#181818')
        viz_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Визуализатор барами
        self.viz_canvas = tk.Canvas(viz_container, bg='#181818', 
                                   highlightthickness=0, height=200)
        self.viz_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Плейлист
        playlist_container = tk.Frame(visualizer_frame, bg='#181818', width=400)
        playlist_container.pack(side=tk.RIGHT, fill=tk.BOTH)
        playlist_container.pack_propagate(False)
        
        playlist_header = tk.Frame(playlist_container, bg='#181818')
        playlist_header.pack(fill=tk.X, pady=(10, 5))
        
        self.playlist_title = tk.Label(playlist_header,
                                     text=f"Плейлист: {self.current_playlist}",
                                     font=('Segoe UI', 16, 'bold'),
                                     bg='#181818',
                                     fg='white')
        self.playlist_title.pack(side=tk.LEFT)
        
        # Счетчик треков
        self.track_count_label = tk.Label(playlist_header,
                                        text=f"{len(self.playlist)} треков",
                                        font=self.time_font,
                                        bg='#181818',
                                        fg='#b3b3b3')
        self.track_count_label.pack(side=tk.RIGHT, padx=20)
        
        # Список песен с прокруткой
        playlist_scroll = tk.Frame(playlist_container, bg='#181818')
        playlist_scroll.pack(fill=tk.BOTH, expand=True)
        
        # Canvas для скроллинга
        self.playlist_canvas = tk.Canvas(playlist_scroll, bg='#181818', 
                                        highlightthickness=0)
        scrollbar = ttk.Scrollbar(playlist_scroll, orient="vertical", 
                                 command=self.playlist_canvas.yview)
        self.scrollable_frame = tk.Frame(self.playlist_canvas, bg='#181818')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.playlist_canvas.configure(
                scrollregion=self.playlist_canvas.bbox("all")
            )
        )
        
        self.playlist_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.playlist_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.playlist_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.playlist_frame = self.scrollable_frame
        
        # Загружаем треки текущего плейлиста
        self.refresh_playlist_display()
    
    def refresh_playlist_display(self):
        """Обновляет отображение плейлиста"""
        # Очищаем текущий плейлист
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.track_frames = {}
        
        # Добавляем треки из текущего плейлиста
        for i, song_path in enumerate(self.playlist):
            if os.path.exists(song_path):
                self.add_track_to_display(i, song_path)
        
        # Обновляем счетчик
        self.update_track_count()
    
    def show_search(self):
        """Показать страницу поиска"""
        self.activate_nav_button("Поиск")
        print("Переход на страницу поиска")
    
    def show_library(self):
        """Показать библиотеку"""
        self.activate_nav_button("Библиотека")
        self.show_library_content()
    
    def show_library_content(self):
        """Показывает содержимое библиотеки"""
        # Очищаем контент
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        title_frame = tk.Frame(self.content_frame, bg='#121212')
        title_frame.pack(fill=tk.X, pady=(20, 10))
        
        title_label = tk.Label(title_frame, 
                             text="📚 Моя библиотека",
                             font=self.title_font,
                             bg='#121212',
                             fg='white')
        title_label.pack(side=tk.LEFT)
        
        # Статистика библиотеки
        stats_frame = tk.Frame(self.content_frame, bg='#181818', padx=20, pady=20)
        stats_frame.pack(fill=tk.X, pady=20)
        
        total_tracks = sum(len(tracks) for tracks in self.user_playlists.values())
        
        stats = [
            (f"{total_tracks}", "Всего треков"),
            (f"{len(self.user_playlists)}", "Плейлистов"),
            (f"{len(self.recently_played)}", "В истории прослушивания")
        ]
        
        for value, label in stats:
            stat_frame = tk.Frame(stats_frame, bg='#181818')
            stat_frame.pack(side=tk.LEFT, expand=True, padx=10)
            
            value_label = tk.Label(stat_frame,
                                 text=value,
                                 font=('Segoe UI', 28, 'bold'),
                                 bg='#181818',
                                 fg='#1DB954')
            value_label.pack()
            
            label_label = tk.Label(stat_frame,
                                 text=label,
                                 font=self.time_font,
                                 bg='#181818',
                                 fg='#b3b3b3')
            label_label.pack()
        
        # Список плейлистов
        playlists_frame = tk.Frame(self.content_frame, bg='#121212')
        playlists_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        playlists_label = tk.Label(playlists_frame,
                                 text="МОИ ПЛЕЙЛИСТЫ",
                                 font=('Segoe UI', 12, 'bold'),
                                 bg='#121212',
                                 fg='white')
        playlists_label.pack(anchor='w', pady=(0, 10))
        
        # Отображаем все плейлисты
        for playlist_name, tracks in self.user_playlists.items():
            playlist_card = tk.Frame(playlists_frame, bg='#181818')
            playlist_card.pack(fill=tk.X, pady=5)
            
            # Информация о плейлисте
            info_frame = tk.Frame(playlist_card, bg='#181818')
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=15, pady=10)
            
            name_label = tk.Label(info_frame,
                                text=playlist_name,
                                font=self.song_font,
                                bg='#181818',
                                fg='white',
                                anchor='w')
            name_label.pack(fill=tk.X)
            
            count_label = tk.Label(info_frame,
                                 text=f"{len(tracks)} треков",
                                 font=self.time_font,
                                 bg='#181818',
                                 fg='#b3b3b3',
                                 anchor='w')
            count_label.pack(fill=tk.X)
            
            # Кнопки управления
            btn_frame = tk.Frame(playlist_card, bg='#181818')
            btn_frame.pack(side=tk.RIGHT, padx=10)
            
            play_btn = tk.Button(btn_frame,
                               text="▶ Воспроизвести",
                               command=lambda name=playlist_name: self.play_playlist(name),
                               bg='#1DB954',
                               fg='white',
                               font=self.time_font,
                               relief='flat',
                               padx=10,
                               pady=5,
                               cursor='hand2')
            play_btn.pack(side=tk.LEFT, padx=2)
            
            delete_btn = tk.Button(btn_frame,
                                 text="🗑️",
                                 command=lambda name=playlist_name: self.delete_playlist(name),
                                 bg='#E22134',
                                 fg='white',
                                 font=('Arial', 10),
                                 relief='flat',
                                 width=3,
                                 cursor='hand2')
            delete_btn.pack(side=tk.LEFT, padx=2)
    
    def play_playlist(self, playlist_name):
        """Начинает воспроизведение плейлиста"""
        if playlist_name in self.user_playlists:
            self.current_playlist = playlist_name
            self.playlist = self.user_playlists[playlist_name]
            
            if self.playlist:
                self.current_song_index = 0
                self.play_song()
                self.show_home()  # Возвращаемся на главную
            else:
                messagebox.showinfo("Плейлист пуст", f"Плейлист '{playlist_name}' пуст.")
    
    def delete_playlist(self, playlist_name):
        """Удаляет плейлист"""
        if playlist_name in ["main", "избранное"]:
            messagebox.showwarning("Нельзя удалить", "Этот плейлист нельзя удалить.")
            return
        
        if messagebox.askyesno("Удалить плейлист", 
                             f"Вы уверены, что хотите удалить плейлист '{playlist_name}'?"):
            del self.user_playlists[playlist_name]
            self.save_playlists()
            
            # Если удалили текущий плейлист, переключаемся на main
            if self.current_playlist == playlist_name:
                self.current_playlist = "main"
                self.playlist = self.user_playlists.get("main", [])
            
            # Обновляем интерфейс
            self.load_user_playlists()
            self.show_library_content()
            
            messagebox.showinfo("Успешно", f"Плейлист '{playlist_name}' удален.")
    
    def show_favorites(self):
        """Показать избранное"""
        self.activate_nav_button("Избранное")
        self.switch_playlist("избранное")
        self.show_home()
    
    def create_new_playlist_dialog(self):
        """Диалог создания нового плейлиста"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Создать новый плейлист")
        dialog.geometry("400x200")
        dialog.configure(bg='#121212')
        dialog.resizable(False, False)
        
        # Делаем окно модальным
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Центрируем окно
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        # Заголовок
        tk.Label(dialog,
                text="Название плейлиста",
                font=('Segoe UI', 14, 'bold'),
                bg='#121212',
                fg='white').pack(pady=20)
        
        # Поле ввода
        playlist_name_entry = tk.Entry(dialog,
                                     font=('Segoe UI', 12),
                                     bg='white',
                                     fg='black',
                                     relief='flat')
        playlist_name_entry.pack(pady=10, padx=40, fill=tk.X)
        playlist_name_entry.focus()
        
        # Кнопки
        button_frame = tk.Frame(dialog, bg='#121212')
        button_frame.pack(pady=20)
        
        def create_playlist():
            name = playlist_name_entry.get().strip()
            if not name:
                messagebox.showerror("Ошибка", "Введите название плейлиста")
                return
            
            if name in self.user_playlists:
                messagebox.showerror("Ошибка", "Плейлист с таким названием уже существует")
                return
            
            # Создаем новый плейлист
            self.user_playlists[name] = []
            self.save_playlists()
            
            # Обновляем интерфейс
            self.load_user_playlists()
            dialog.destroy()
            
            messagebox.showinfo("Успешно", f"Плейлист '{name}' создан!")
        
        create_btn = tk.Button(button_frame,
                             text="Создать",
                             command=create_playlist,
                             bg='#1DB954',
                             fg='white',
                             font=self.button_font,
                             relief='flat',
                             padx=30,
                             pady=8,
                             cursor='hand2')
        create_btn.pack(side=tk.LEFT, padx=10)
        
        cancel_btn = tk.Button(button_frame,
                             text="Отмена",
                             command=dialog.destroy,
                             bg='#535353',
                             fg='white',
                             font=self.button_font,
                             relief='flat',
                             padx=30,
                             pady=8,
                             cursor='hand2')
        cancel_btn.pack(side=tk.LEFT, padx=10)
    
    def create_top_bar(self, parent):
        top_bar = tk.Frame(parent, bg='#121212', height=70)
        top_bar.pack(fill=tk.X)
        top_bar.pack_propagate(False)
        
        # Поле поиска
        search_frame = tk.Frame(top_bar, bg='white', height=40)
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=20)
        search_frame.pack_propagate(False)
        
        self.search_entry = tk.Entry(search_frame,
                                   font=('Segoe UI', 12),
                                   bg='white',
                                   fg='black',
                                   relief='flat')
        self.search_entry.pack(fill=tk.BOTH, expand=True, padx=10)
        self.search_entry.insert(0, "Поиск музыки...")
        
        # События для поля поиска
        self.search_entry.bind('<FocusIn>', self.on_search_focus_in)
        self.search_entry.bind('<FocusOut>', self.on_search_focus_out)
        self.search_entry.bind('<Return>', self.on_search_enter)
    
    def on_search_focus_in(self, event):
        if self.search_entry.get() == "Поиск музыки...":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg='black')
    
    def on_search_focus_out(self, event):
        if not self.search_entry.get():
            self.search_entry.insert(0, "Поиск музыки...")
            self.search_entry.config(fg='gray')
    
    def on_search_enter(self, event):
        query = self.search_entry.get()
        if query and query != "Поиск музыки...":
            print(f"Поиск: {query}")
    
    def create_player_bar(self, parent):
        player_bar = tk.Frame(parent, bg='#181818', height=100)
        player_bar.pack(side=tk.BOTTOM, fill=tk.X)
        player_bar.pack_propagate(False)
        
        # Информация о текущем треке
        current_track_frame = tk.Frame(player_bar, bg='#181818', width=300)
        current_track_frame.pack(side=tk.LEFT, fill=tk.Y)
        current_track_frame.pack_propagate(False)
        
        self.current_track_label = tk.Label(current_track_frame,
                                          text="Не воспроизводится",
                                          font=self.song_font,
                                          bg='#181818',
                                          fg='white')
        self.current_track_label.pack(anchor='w', padx=20, pady=10)
        
        self.current_artist_label = tk.Label(current_track_frame,
                                           text="Выберите трек для воспроизведения",
                                           font=self.time_font,
                                           bg='#181818',
                                           fg='#b3b3b3')
        self.current_artist_label.pack(anchor='w', padx=20)
        
        # Элементы управления
        control_frame = tk.Frame(player_bar, bg='#181818')
        control_frame.pack(expand=True, fill=tk.BOTH)
        
        # Кнопки управления
        buttons_frame = tk.Frame(control_frame, bg='#181818')
        buttons_frame.pack(pady=10)
        
        # Стилизованные кнопки
        button_style = {
            'bg': '#181818',
            'fg': 'white',
            'relief': 'flat',
            'cursor': 'hand2',
            'activebackground': '#282828',
            'borderwidth': 0
        }
        
        self.prev_btn = tk.Button(buttons_frame,
                                text="⏮",
                                font=('Arial', 20),
                                command=self.prev_song,
                                **button_style)
        self.prev_btn.pack(side=tk.LEFT, padx=10)
        
        self.play_btn = tk.Button(buttons_frame,
                                text="▶",
                                font=('Arial', 24),
                                command=self.play_pause,
                                bg='white',
                                fg='black',
                                relief='flat',
                                width=3,
                                cursor='hand2',
                                activebackground='#f0f0f0')
        self.play_btn.pack(side=tk.LEFT, padx=10)
        
        self.next_btn = tk.Button(buttons_frame,
                                text="⏭",
                                font=('Arial', 20),
                                command=self.next_song,
                                **button_style)
        self.next_btn.pack(side=tk.LEFT, padx=10)
        
        # Кнопка случайного воспроизведения
        self.shuffle_btn = tk.Button(buttons_frame,
                                   text="🔀",
                                   font=('Arial', 14),
                                   command=self.toggle_shuffle,
                                   **button_style)
        self.shuffle_btn.pack(side=tk.LEFT, padx=20)
        self.shuffle_mode = False
        
        # Кнопка повтора
        self.repeat_btn = tk.Button(buttons_frame,
                                  text="🔁",
                                  font=('Arial', 14),
                                  command=self.toggle_repeat,
                                  **button_style)
        self.repeat_btn.pack(side=tk.LEFT, padx=5)
        self.repeat_mode = False
        
        # Кнопка микширования
        self.mix_btn = tk.Button(buttons_frame,
                               text="🎚️",
                               font=('Arial', 14),
                               command=self.toggle_mix,
                               **button_style)
        self.mix_btn.pack(side=tk.LEFT, padx=20)
        
        # Прогресс бар
        progress_frame = tk.Frame(control_frame, bg='#181818')
        progress_frame.pack(fill=tk.X, padx=50, pady=5)
        
        self.time_current = tk.Label(progress_frame,
                                   text="0:00",
                                   font=self.time_font,
                                   bg='#181818',
                                   fg='#b3b3b3')
        self.time_current.pack(side=tk.LEFT)
        
        # Кастомный прогресс-бар
        self.progress_canvas = tk.Canvas(progress_frame, 
                                        bg='#181818',
                                        height=4,
                                        highlightthickness=0)
        self.progress_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        self.progress_bg = self.progress_canvas.create_rectangle(0, 0, 400, 4, 
                                                                fill='#404040', outline='')
        self.progress_fg = self.progress_canvas.create_rectangle(0, 0, 0, 4, 
                                                                fill='#1DB954', outline='')
        
        self.progress_canvas.bind("<Button-1>", self.on_progress_click)
        self.progress_canvas.bind("<B1-Motion>", self.on_progress_drag)
        
        self.time_total = tk.Label(progress_frame,
                                 text="0:00",
                                 font=self.time_font,
                                 bg='#181818',
                                 fg='#b3b3b3')
        self.time_total.pack(side=tk.LEFT)
        
        # Громкость и доп. кнопки
        volume_frame = tk.Frame(player_bar, bg='#181818', width=200)
        volume_frame.pack(side=tk.RIGHT, fill=tk.Y)
        volume_frame.pack_propagate(False)
        
        # Ползунок громкости
        vol_btn = tk.Button(volume_frame,
                          text="🔊",
                          font=('Arial', 12),
                          bg='#181818',
                          fg='white',
                          relief='flat',
                          cursor='hand2',
                          command=self.toggle_mute)
        vol_btn.pack(side=tk.LEFT, padx=5)
        self.is_muted = False
        
        self.volume_slider = ttk.Scale(volume_frame,
                                     from_=0,
                                     to=100,
                                     orient=tk.HORIZONTAL,
                                     value=self.volume*100,
                                     command=self.set_volume)
        
        # Стиль для ползунка
        style = ttk.Style()
        style.configure('Volume.Horizontal.TScale', 
                       background='#181818',
                       troughcolor='#404040',
                       bordercolor='#181818')
        
        self.volume_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
    
    def toggle_shuffle(self):
        """Включить/выключить случайное воспроизведение"""
        self.shuffle_mode = not self.shuffle_mode
        if self.shuffle_mode:
            self.shuffle_btn.config(fg='#1DB954')
            print("Случайное воспроизведение включено")
        else:
            self.shuffle_btn.config(fg='white')
            print("Случайное воспроизведение выключено")
    
    def toggle_repeat(self):
        """Включить/выключить повтор"""
        self.repeat_mode = not self.repeat_mode
        if self.repeat_mode:
            self.repeat_btn.config(fg='#1DB954')
            print("Повтор включен")
        else:
            self.repeat_btn.config(fg='white')
            print("Повтор выключен")
    
    def toggle_mix(self):
        """Включить/выключить режим микширования"""
        self.mix_mode = not self.mix_mode
        if self.mix_mode:
            self.mix_btn.config(fg='#9C27B0')
            print("Режим микширования включен")
            self.start_mix_mode()
        else:
            self.mix_btn.config(fg='white')
            print("Режим микширования выключен")
            self.stop_mix_mode()
    
    def start_mix_mode(self):
        """Запускает режим микширования"""
        if self.mix_mode and self.playlist:
            # Останавливаем текущее воспроизведение
            if self.playing:
                pygame.mixer.music.stop()
            
            # Запускаем микс
            self.play_mix()
    
    def stop_mix_mode(self):
        """Останавливает режим микширования"""
        if self.mix_timer:
            self.root.after_cancel(self.mix_timer)
            self.mix_timer = None
    
    def play_mix(self):
        """Воспроизводит микс (перемешанные треки)"""
        if not self.mix_mode or not self.playlist:
            return
        
        # Выбираем случайный трек
        self.current_song_index = random.randint(0, len(self.playlist) - 1)
        
        # Воспроизводим трек
        self.play_song()
        
        # Устанавливаем таймер для следующего трека
        if self.mix_mode:
            # Используем короткий интервал для микса (3-10 секунд)
            mix_interval = random.randint(3000, 10000)
            self.mix_timer = self.root.after(mix_interval, self.play_mix)
    
    def create_mix(self):
        """Создает новый микс из случайных треков"""
        if len(self.playlist) < 3:
            messagebox.showwarning("Недостаточно треков", 
                                 "Для создания микса нужно хотя бы 3 трека в плейлисте.")
            return
        
        # Спрашиваем пользователя о длительности микса
        dialog = tk.Toplevel(self.root)
        dialog.title("Создать микс")
        dialog.geometry("400x250")
        dialog.configure(bg='#121212')
        dialog.resizable(False, False)
        
        # Делаем окно модальным
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Центрируем окно
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        # Заголовок
        tk.Label(dialog,
                text="Создание микса",
                font=('Segoe UI', 16, 'bold'),
                bg='#121212',
                fg='white').pack(pady=20)
        
        # Количество треков в миксе
        tk.Label(dialog,
                text="Количество треков:",
                font=('Segoe UI', 12),
                bg='#121212',
                fg='white').pack(pady=5)
        
        track_count_var = tk.StringVar(value=str(min(10, len(self.playlist))))
        track_count_spin = tk.Spinbox(dialog,
                                    from_=3,
                                    to=min(20, len(self.playlist)),
                                    textvariable=track_count_var,
                                    font=('Segoe UI', 12),
                                    width=10)
        track_count_spin.pack(pady=5)
        
        # Название микса
        tk.Label(dialog,
                text="Название микса:",
                font=('Segoe UI', 12),
                bg='#121212',
                fg='white').pack(pady=5)
        
        mix_name_entry = tk.Entry(dialog,
                                font=('Segoe UI', 12),
                                bg='white',
                                fg='black',
                                relief='flat')
        mix_name_entry.pack(pady=5, padx=40, fill=tk.X)
        mix_name_entry.insert(0, f"Микс {time.strftime('%d.%m.%Y')}")
        
        # Кнопки
        button_frame = tk.Frame(dialog, bg='#121212')
        button_frame.pack(pady=20)
        
        def create_mix_playlist():
            track_count = int(track_count_var.get())
            mix_name = mix_name_entry.get().strip()
            
            if not mix_name:
                messagebox.showerror("Ошибка", "Введите название микса")
                return
            
            # Выбираем случайные треки
            if track_count > len(self.playlist):
                track_count = len(self.playlist)
            
            mix_tracks = random.sample(self.playlist, track_count)
            
            # Создаем новый плейлист с миксом
            self.user_playlists[mix_name] = mix_tracks
            self.save_playlists()
            
            # Обновляем интерфейс
            self.load_user_playlists()
            dialog.destroy()
            
            # Переключаемся на новый микс
            self.switch_playlist(mix_name)
            
            # Запускаем воспроизведение
            self.toggle_mix()  # Включаем режим микширования
            
            messagebox.showinfo("Успешно", f"Микс '{mix_name}' создан из {track_count} треков!")
        
        create_btn = tk.Button(button_frame,
                             text="Создать микс",
                             command=create_mix_playlist,
                             bg='#9C27B0',
                             fg='white',
                             font=self.button_font,
                             relief='flat',
                             padx=30,
                             pady=8,
                             cursor='hand2')
        create_btn.pack(side=tk.LEFT, padx=10)
        
        cancel_btn = tk.Button(button_frame,
                             text="Отмена",
                             command=dialog.destroy,
                             bg='#535353',
                             fg='white',
                             font=self.button_font,
                             relief='flat',
                             padx=30,
                             pady=8,
                             cursor='hand2')
        cancel_btn.pack(side=tk.LEFT, padx=10)
    
    def toggle_mute(self):
        """Включить/выключить беззвучный режим"""
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.old_volume = self.volume
            pygame.mixer.music.set_volume(0)
            self.volume_slider.set(0)
        else:
            pygame.mixer.music.set_volume(self.old_volume)
            self.volume_slider.set(self.old_volume * 100)
    
    def load_sample_tracks(self):
        """Загружает несколько тестовых треков для демонстрации"""
        sample_tracks = [
            ("Lofi Chill Mix", "Chillhop Music", "3:45"),
            ("Summer Vibes", "Tropical House", "4:20"),
            ("Deep Focus", "Study Music", "5:10"),
            ("Evening Jazz", "Jazz Vibes", "4:55"),
            ("Workout Energy", "Power Music", "3:30")
        ]
        
        for i, (track, artist, duration) in enumerate(sample_tracks):
            track_frame = tk.Frame(self.playlist_frame, bg='#181818')
            track_frame.pack(fill=tk.X, pady=2)
            
            # Номер трека
            num_label = tk.Label(track_frame,
                               text=str(i+1),
                               font=self.time_font,
                               bg='#181818',
                               fg='#b3b3b3',
                               width=3)
            num_label.pack(side=tk.LEFT, padx=10)
            
            # Иконка воспроизведения
            play_icon = tk.Label(track_frame,
                               text="▶",
                               font=('Arial', 10),
                               bg='#181818',
                               fg='#181818')
            play_icon.pack(side=tk.LEFT)
            
            # Информация о треке
            info_frame = tk.Frame(track_frame, bg='#181818')
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
            
            track_label = tk.Label(info_frame,
                                 text=track,
                                 font=self.song_font,
                                 bg='#181818',
                                 fg='white',
                                 anchor='w')
            track_label.pack(fill=tk.X)
            
            artist_label = tk.Label(info_frame,
                                  text=artist,
                                  font=self.time_font,
                                  bg='#181818',
                                  fg='#b3b3b3',
                                  anchor='w')
            artist_label.pack(fill=tk.X)
            
            # Длительность
            dur_label = tk.Label(track_frame,
                               text=duration,
                               font=self.time_font,
                               bg='#181818',
                               fg='#b3b3b3')
            dur_label.pack(side=tk.RIGHT, padx=20)
            
            # Эффекты при наведении
            def on_enter(e, frame=track_frame, icon=play_icon, num=num_label):
                frame.config(bg='#282828')
                icon.config(bg='#282828', fg='white')
                num.config(bg='#282828')
                info_frame.config(bg='#282828')
                track_label.config(bg='#282828')
                artist_label.config(bg='#282828')
                dur_label.config(bg='#282828')
            
            def on_leave(e, frame=track_frame, icon=play_icon, num=num_label):
                frame.config(bg='#181818')
                icon.config(bg='#181818', fg='#181818')
                num.config(bg='#181818')
                info_frame.config(bg='#181818')
                track_label.config(bg='#181818')
                artist_label.config(bg='#181818')
                dur_label.config(bg='#181818')
            
            track_frame.bind("<Enter>", on_enter)
            track_frame.bind("<Leave>", on_leave)
            
            # Храним информацию о треке
            self.track_frames[track] = {
                'frame': track_frame,
                'track_label': track_label,
                'artist_label': artist_label
            }
    
    def add_songs(self):
        files = filedialog.askopenfilenames(
            title="Выберите песни",
            filetypes=[("Audio Files", "*.mp3 *.wav *.ogg *.flac")]
        )
        
        if files:
            for file in files:
                if file not in self.playlist:
                    self.playlist.append(file)
            
            # Сохраняем в текущий плейлист
            self.user_playlists[self.current_playlist] = self.playlist
            self.save_playlists()
            
            # Обновляем отображение
            self.refresh_playlist_display()
            
            messagebox.showinfo("Успешно", f"Добавлено {len(files)} треков в '{self.current_playlist}'")
    
    def clear_playlist(self):
        """Очистить весь плейлист"""
        if self.playlist:
            if messagebox.askyesno("Очистить плейлист", 
                                 f"Вы уверены, что хотите очистить плейлист '{self.current_playlist}'?"):
                # Останавливаем воспроизведение
                if self.playing:
                    pygame.mixer.music.stop()
                    self.playing = False
                    self.paused = False
                    self.play_btn.config(text="▶")
                
                # Останавливаем микс если активен
                if self.mix_mode:
                    self.stop_mix_mode()
                    self.mix_mode = False
                    self.mix_btn.config(fg='white')
                
                # Очищаем плейлист
                self.playlist.clear()
                self.user_playlists[self.current_playlist] = []
                self.save_playlists()
                
                # Обновляем отображение
                self.refresh_playlist_display()
                
                # Сбрасываем информацию о текущем треке
                self.current_track_label.config(text="Не воспроизводится")
                self.current_artist_label.config(text=f"Плейлист '{self.current_playlist}' очищен")
                self.time_current.config(text="0:00")
                self.time_total.config(text="0:00")
                self.progress_canvas.coords(self.progress_fg, 0, 0, 0, 4)
                
                print(f"Плейлист '{self.current_playlist}' очищен")
    
    def update_track_count(self):
        """Обновляет счетчик треков"""
        count = len(self.playlist)
        self.track_count_label.config(text=f"{count} треков")
    
    def add_track_to_display(self, index, file_path):
        """Добавляет трек в отображаемый плейлист"""
        song_name = os.path.basename(file_path)
        
        track_frame = tk.Frame(self.scrollable_frame, bg='#181818')
        track_frame.pack(fill=tk.X, pady=2)
        
        # Номер трека
        num_label = tk.Label(track_frame,
                           text=str(index + 1),
                           font=self.time_font,
                           bg='#181818',
                           fg='#b3b3b3',
                           width=3)
        num_label.pack(side=tk.LEFT, padx=10)
        
        # Иконка воспроизведения
        play_icon = tk.Label(track_frame,
                           text="▶",
                           font=('Arial', 10),
                           bg='#181818',
                           fg='#181818')
        play_icon.pack(side=tk.LEFT)
        
        # Информация о треке
        info_frame = tk.Frame(track_frame, bg='#181818')
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        track_label = tk.Label(info_frame,
                             text=song_name,
                             font=self.song_font,
                             bg='#181818',
                             fg='white',
                             anchor='w')
        track_label.pack(fill=tk.X)
        
        # Получаем информацию о файле
        try:
            audio = MP3(file_path)
            duration = time.strftime('%M:%S', time.gmtime(audio.info.length))
            bitrate = f"{audio.info.bitrate // 1000} kbps"
            artist_info = f"{duration} • {bitrate}"
        except:
            artist_info = "Неизвестный артист"
            duration = "--:--"
        
        artist_label = tk.Label(info_frame,
                              text=artist_info,
                              font=self.time_font,
                              bg='#181818',
                              fg='#b3b3b3',
                              anchor='w')
        artist_label.pack(fill=tk.X)
        
        # Длительность
        dur_label = tk.Label(track_frame,
                           text=duration,
                           font=self.time_font,
                           bg='#181818',
                           fg='#b3b3b3')
        dur_label.pack(side=tk.RIGHT, padx=20)
        
        # Кнопка удаления из плейлиста
        delete_btn = tk.Button(track_frame,
                             text="🗑️",
                             font=('Arial', 8),
                             bg='#181818',
                             fg='#b3b3b3',
                             relief='flat',
                             width=2,
                             cursor='hand2',
                             command=lambda path=file_path: self.remove_from_playlist(path))
        delete_btn.pack(side=tk.RIGHT, padx=5)
        
        # Эффекты при наведении и клике
        def on_enter(e):
            track_frame.config(bg='#282828')
            for widget in [num_label, play_icon, info_frame, track_label, 
                          artist_label, dur_label, delete_btn]:
                widget.config(bg='#282828')
            play_icon.config(fg='white')
        
        def on_leave(e):
            track_frame.config(bg='#181818')
            for widget in [num_label, play_icon, info_frame, track_label, 
                          artist_label, dur_label, delete_btn]:
                widget.config(bg='#181818')
            play_icon.config(fg='#181818')
        
        def on_click(e):
            index = self.playlist.index(file_path)
            self.current_song_index = index
            self.play_song()
        
        track_frame.bind("<Enter>", on_enter)
        track_frame.bind("<Leave>", on_leave)
        track_frame.bind("<Button-1>", on_click)
        
        # Храним информацию о треке
        self.track_frames[file_path] = {
            'frame': track_frame,
            'track_label': track_label,
            'artist_label': artist_label
        }
    
    def remove_from_playlist(self, file_path):
        """Удаляет трек из плейлиста"""
        if file_path in self.playlist:
            # Если этот трек сейчас играет, останавливаем
            if self.playing and self.playlist[self.current_song_index] == file_path:
                pygame.mixer.music.stop()
                self.playing = False
                self.paused = False
                self.play_btn.config(text="▶")
            
            # Удаляем из плейлиста
            self.playlist.remove(file_path)
            self.user_playlists[self.current_playlist] = self.playlist
            self.save_playlists()
            
            # Обновляем отображение
            self.refresh_playlist_display()
            
            print(f"Трек удален из плейлиста")
    
    def play_song(self):
        if not self.playlist:
            return
            
        song_path = self.playlist[self.current_song_index]
        song_name = os.path.basename(song_path)
        
        try:
            pygame.mixer.music.load(song_path)
            pygame.mixer.music.play()
            self.playing = True
            self.paused = False
            
            # Обновление информации
            self.current_track_label.config(text=song_name)
            self.play_btn.config(text="⏸")
            
            # Получение информации о треке
            try:
                audio = MP3(song_path)
                self.song_length = audio.info.length
                total_time = time.strftime('%M:%S', time.gmtime(self.song_length))
                self.time_total.config(text=total_time)
            except:
                self.song_length = 300
                self.time_total.config(text="5:00")
            
            # Добавляем в историю
            if song_name not in self.recently_played:
                self.recently_played.append(song_name)
            
        except Exception as e:
            print(f"Ошибка воспроизведения: {e}")
            self.current_artist_label.config(text="Ошибка воспроизведения файла")
    
    def play_pause(self):
        if not self.playlist:
            self.current_artist_label.config(text="Плейлист пуст. Добавьте музыку.")
            return
            
        if not self.playing:
            if self.paused:
                pygame.mixer.music.unpause()
                self.paused = False
                self.playing = True
                self.play_btn.config(text="⏸")
            else:
                self.play_song()
        else:
            pygame.mixer.music.pause()
            self.playing = False
            self.paused = True
            self.play_btn.config(text="▶")
    
    def next_song(self):
        if not self.playlist:
            return
            
        if self.shuffle_mode:
            self.current_song_index = random.randint(0, len(self.playlist) - 1)
        else:
            self.current_song_index = (self.current_song_index + 1) % len(self.playlist)
        
        self.play_song()
    
    def prev_song(self):
        if not self.playlist:
            return
            
        self.current_song_index = (self.current_song_index - 1) % len(self.playlist)
        self.play_song()
    
    def set_volume(self, val):
        self.volume = float(val) / 100
        pygame.mixer.music.set_volume(self.volume)
    
    def on_progress_click(self, event):
        """Обработка клика по прогресс-бару"""
        self.on_progress_drag(event)
    
    def on_progress_drag(self, event):
        """Обработка перетаскивания прогресс-бара"""
        if hasattr(self, 'song_length') and self.song_length > 0:
            canvas_width = self.progress_canvas.winfo_width()
            if canvas_width > 0:
                click_pos = min(max(event.x / canvas_width, 0), 1)
                new_time = self.song_length * click_pos
                pygame.mixer.music.set_pos(new_time)
                
                # Немедленное обновление отображения
                self.time_current.config(text=time.strftime('%M:%S', time.gmtime(new_time)))
                bar_width = int(canvas_width * click_pos)
                self.progress_canvas.coords(self.progress_fg, 0, 0, bar_width, 4)
    
    def update_time(self):
        if self.playing and hasattr(self, 'song_length'):
            current_time = pygame.mixer.music.get_pos() / 1000
            
            # Проверка на завершение трека
            if current_time >= self.song_length and self.song_length > 0:
                if self.repeat_mode:
                    pygame.mixer.music.rewind()
                    pygame.mixer.music.play()
                else:
                    self.next_song()
            elif current_time >= 0:  # Корректное время
                # Обновление времени
                self.time_current.config(text=time.strftime('%M:%S', 
                                                          time.gmtime(current_time)))
                
                # Обновление прогресс-бара
                if self.song_length > 0:
                    progress = current_time / self.song_length
                    canvas_width = self.progress_canvas.winfo_width()
                    if canvas_width > 0:
                        bar_width = int(canvas_width * progress)
                        self.progress_canvas.coords(self.progress_fg, 0, 0, 
                                                   bar_width, 4)
        
        self.root.after(100, self.update_time)
    
    def animate_visualizer(self):
        """Анимация визуализатора"""
        if hasattr(self, 'viz_canvas') and self.viz_canvas.winfo_exists():
            self.viz_canvas.delete("all")
            
            width = self.viz_canvas.winfo_width()
            height = self.viz_canvas.winfo_height()
            
            if width > 10 and height > 10:
                num_bars = 30
                bar_width = max(2, width // (num_bars * 2))
                
                for i in range(num_bars):
                    x = i * (bar_width * 1.5) + 20
                    
                    base_height = height * 0.3
                    if self.playing:
                        time_factor = (time.time() * 2 + i * 0.3) % 1
                        dynamic_height = base_height * (0.5 + 0.5 * abs(time_factor - 0.5))
                    else:
                        dynamic_height = base_height * 0.3
                    
                    color_intensity = int(100 + 155 * (i / num_bars))
                    color = f'#{color_intensity:02x}{255:02x}{color_intensity:02x}'
                    
                    bar_height = int(dynamic_height * (0.7 + 0.3 * (i % 3)))
                    self.viz_canvas.create_rectangle(x, height - bar_height,
                                                   x + bar_width, height,
                                                   fill=color, outline='')
        
        if self.root.winfo_exists():
            self.root.after(100, self.animate_visualizer)

def main():
    root = tk.Tk()
    app = ModernMusicPlayer(root)
    
    # Центрируем окно
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    # Сообщение при закрытии
    def on_closing():
        # Сохраняем данные
        app.save_playlists()
        
        # Останавливаем музыку
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    root.mainloop()

if __name__ == "__main__":
    main()