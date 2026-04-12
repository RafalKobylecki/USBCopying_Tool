# Copyright (C) 2026 Rafał Kobylecki (metallmaniac82@gmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import tkinter as tk
from tkinter import ttk


class AppGUI:
    """
    Warstwa odpowiedzialna wyłącznie za budowę interfejsu użytkownika.

    Klasa nie zawiera logiki kopiowania plików ani detekcji urządzeń USB.
    Jej zadaniem jest:
    - zdefiniowanie geometrii wszystkich paneli i kontrolek,
    - utworzenie widoków Tkinter,
    - przygotowanie kontrolek, które później są obsługiwane przez klasę USBCopyGUI.

    Układ okna został podzielony na trzy pionowe strefy:
    1. Lewa kolumna  - panel sterowania aplikacją.
    2. Środkowa kolumna - folder źródłowy, połączony panel opcji i wyboru plików, status ogólny.
    3. Prawa kolumna - lista wykrytych pamięci masowych USB, ułożona pionowo jedna pod drugą.
    """

    def __init__(self, root, translator):
        self.root = root
        self.tr = translator
        self.create_menu()
        self.setup_geometry_map()
        self.setup_ui()

    def setup_geometry_map(self):
        """
        Przygotowanie mapy geometrii dla całego okna.

        Wszystkie rozmiary i pozycje są wyliczane na podstawie wymiaru bazowego okna,
        aby łatwiej było utrzymać spójność układu przy różnych rozdzielczościach.
        """
        w = self.base_width
        h = self.base_height

        # ==============================
        # PODZIAŁ GŁÓWNY OKNA APLIKACJI
        # ==============================
        # LEWA KOLUMNA:
        # - wąska strefa sterowania użytkownika,
        # - zawiera przyciski odświeżania, startu, zatrzymania i zamknięcia.
        left_x = 10
        left_w = int(w * 0.24)

        # ŚRODKOWA KOLUMNA:
        # - obszar roboczy związany ze źródłem danych i konfiguracją kopiowania,
        # - zawiera panel źródła, połączony panel opcji/wyboru plików i status ogólny.
        middle_x = int(w * 0.26)
        middle_w = int(w * 0.33)

        # PRAWA KOLUMNA:
        # - panel urządzeń USB,
        # - każde wykryte urządzenie jest pokazywane jako osobny wiersz,
        #   ułożony pionowo jeden pod drugim.
        right_x = int(w * 0.61)
        right_w = int(w * 0.37)

        self.geom = {
            # =====================================
            # LEWA STRONA GUI - PANEL STEROWANIA
            # =====================================
            'left_panel': {'x': left_x, 'y': 10, 'w': left_w, 'h': h - 60},
            'refresh_btn': {'x': 18, 'y': 42, 'w': int(w * 0.22), 'h': 44},
            'copy_btn': {'x': 18, 'y': 94, 'w': int(w * 0.22), 'h': 44},
            'stop_btn': {'x': 18, 'y': 146, 'w': int(w * 0.22), 'h': 44},
            'left_hint': {'x': 18, 'y': int(h - 200), 'w': int(w * 0.20), 'h': 60},
            'exit_btn': {'x': 18, 'y': int(h - 120), 'w': int(w * 0.22), 'h': 44},

            # =====================================
            # ŚRODKOWA KOLUMNA - FOLDER ŹRÓDŁOWY
            # =====================================
            'source_frame': {'x': middle_x, 'y': 10, 'w': middle_w, 'h': 190},
            'source_entry': {'x': 10, 'y': 12, 'w': int(middle_w * 0.58), 'h': 28},
            'browse_btn': {'x': int(middle_w * 0.62), 'y': 10, 'w': int(middle_w * 0.22), 'h': 32},
            'source_listbox': {'x': 10, 'y': 52, 'w': int(middle_w * 0.74), 'h': 120},
            'source_scroll': {'x': int(middle_w * 0.78), 'y': 52, 'w': 18, 'h': 120},

            # ==========================================================
            # ŚRODKOWA KOLUMNA - POŁĄCZONY PANEL OPCJI I WYBORU PLIKÓW
            # ==========================================================
            # Sekcja 1:
            # - Copy to folder
            # - pod nią pole folder name
            #
            # Sekcja 2:
            # - Copy only files to drive root
            # - pod nią przycisk wyboru plików i opis aktualnego wyboru.
            'options_frame': {'x': middle_x, 'y': 210, 'w': middle_w, 'h': 260},
            'folder_mode_radio': {'x': 16, 'y': 20, 'w': int(middle_w * 0.78), 'h': 24},
            'folder_name_label': {'x': 16, 'y': 54, 'w': 110, 'h': 24},
            'folder_name_entry': {'x': 130, 'y': 54, 'w': int(middle_w * 0.40), 'h': 24},
            'flatten_mode_radio': {'x': 16, 'y': 100, 'w': int(middle_w * 0.82), 'h': 40},
            'select_files_btn': {'x': 16, 'y': 148, 'w': 130, 'h': 32},
            'selection_summary_label': {'x': 16, 'y': 188, 'w': int(middle_w * 0.82), 'h': 52},

            # =====================================
            # ŚRODKOWA KOLUMNA - STATUS OGÓLNY
            # =====================================
            'status_frame': {'x': middle_x, 'y': 480, 'w': middle_w, 'h': 140},
            'overall_progress': {'x': 10, 'y': 16, 'w': int(middle_w * 0.90), 'h': 24},
            'overall_file_label': {'x': 10, 'y': 50, 'w': int(middle_w * 0.90), 'h': 24},
            'status_label': {'x': 10, 'y': 78, 'w': int(middle_w * 0.90), 'h': 24},

            # =====================================
            # PRAWA KOLUMNA - WYKRYTE NOŚNIKI USB
            # =====================================
            'usb_frame': {'x': right_x, 'y': 10, 'w': right_w, 'h': 610},
            'usb_canvas': {'x': 10, 'y': 10, 'w': int(right_w * 0.86), 'h': 540},
            'usb_scrollbar': {'x': int(right_w * 0.90), 'y': 10, 'w': 18, 'h': 540},
        }

        # Szerokość pojedynczej karty urządzenia USB.
        # Karty są renderowane pionowo w jednej kolumnie.
        self.usb_card_w = int(self.geom['usb_canvas']['w'] * 0.92)
        self.usb_card_h = 90

    def setup_ui(self):
        """
        Budowa wszystkich kontrolek GUI na podstawie wcześniej przygotowanej mapy geometrii.
        """
        self.root.title(self.tr.get('window.title'))
        self.root.configure(bg='#f0f0f0')

        # =====================================
        # LEWA STRONA - PANEL STEROWANIA
        # =====================================
        self.left_panel = tk.LabelFrame(
            self.root,
            text=self.tr.get('labels.control_frame', default='🎮 Control'),
            font=('Arial', 11, 'bold')
        )
        g = self.geom['left_panel']
        self.left_panel.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])

        g = self.geom['refresh_btn']
        self.refresh_btn = tk.Button(
            self.root,
            text=self.tr.get('buttons.refresh_usb'),
            command=self.refresh_usb,
            bg='#FF9800',
            fg='white',
            font=('Arial', 9, 'bold')
        )
        self.refresh_btn.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])

        g = self.geom['copy_btn']
        self.copy_btn = tk.Button(
            self.root,
            text=self.tr.get('buttons.start_copy'),
            command=self.start_copy,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 11, 'bold'),
            state='disabled'
        )
        self.copy_btn.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])

        g = self.geom['stop_btn']
        self.stop_btn = tk.Button(
            self.root,
            text=self.tr.get('buttons.stop_copy'),
            command=self.stop_copy,
            bg='#f44336',
            fg='white',
            font=('Arial', 11, 'bold'),
            state='disabled'
        )
        self.stop_btn.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])

        g = self.geom['left_hint']
        self.left_hint = tk.Label(
            self.root,
            text=self.tr.get('labels.control_hint', default='Use these buttons to start or stop copying.'),
            anchor='nw',
            justify='left',
            fg='gray',
            bg='#f0f0f0',
            wraplength=g['w'],
            font=('Arial', 8)
        )
        self.left_hint.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])

        g = self.geom['exit_btn']
        self.exit_btn = tk.Button(
            self.root,
            text=self.tr.get('buttons.exit_app', default='Exit'),
            command=self.on_closing,
            bg='#616161',
            fg='white',
            font=('Arial', 11, 'bold')
        )
        self.exit_btn.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])

        # =====================================
        # ŚRODKOWA KOLUMNA - PANEL ŹRÓDŁA
        # =====================================
        self.source_frame = tk.LabelFrame(
            self.root,
            text=self.tr.get('labels.source_frame'),
            font=('Arial', 11, 'bold')
        )
        g = self.geom['source_frame']
        self.source_frame.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])

        g = self.geom['source_entry']
        self.source_entry = tk.Entry(self.source_frame, textvariable=self.source_path, font=('Arial', 10))
        self.source_entry.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])

        g = self.geom['browse_btn']
        self.browse_btn = tk.Button(
            self.source_frame,
            text=self.tr.get('buttons.browse'),
            command=self.browse_source,
            bg='#2196F3',
            fg='white',
            font=('Arial', 9, 'bold')
        )
        self.browse_btn.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])

        g = self.geom['source_listbox']
        self.source_listbox = tk.Listbox(self.source_frame, font=('Arial', 9))
        self.source_listbox.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])

        g = self.geom['source_scroll']
        self.scrollbar_source = ttk.Scrollbar(self.source_frame, orient='vertical', command=self.source_listbox.yview)
        self.scrollbar_source.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])
        self.source_listbox.configure(yscrollcommand=self.scrollbar_source.set)

        # ======================================================
        # ŚRODKOWA KOLUMNA - POŁĄCZONY PANEL OPCJI I WYBORU PLIKÓW
        # ======================================================
        self.options_frame = tk.LabelFrame(
            self.root,
            text=self.tr.get('labels.options_frame'),
            font=('Arial', 11, 'bold')
        )
        g = self.geom['options_frame']
        self.options_frame.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])

        self.folder_mode = tk.BooleanVar(value=True)

        # Opcja 1: kopiowanie do podfolderu na nośniku USB.
        g = self.geom['folder_mode_radio']
        self.folder_mode_radio = tk.Radiobutton(
            self.options_frame,
            text=self.tr.get('radio.folder_mode'),
            variable=self.folder_mode,
            value=True,
            command=self.on_copy_mode_changed,
            font=('Arial', 9),
            anchor='w',
            justify='left'
        )
        self.folder_mode_radio.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])

        # Etykieta i pole nazwy folderu używanego w trybie Copy to folder.
        g = self.geom['folder_name_label']
        self.folder_name_label = tk.Label(
            self.options_frame,
            text=self.tr.get('labels.folder_name'),
            font=('Arial', 9, 'bold'),
            anchor='w'
        )
        self.folder_name_label.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])

        self.folder_name = tk.StringVar(value='')
        g = self.geom['folder_name_entry']
        self.folder_name_entry = tk.Entry(self.options_frame, textvariable=self.folder_name, font=('Arial', 9))
        self.folder_name_entry.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])

        # Opcja 2: kopiowanie samych plików do katalogu głównego nośnika.
        # Tekst jest zawijany na szerokość panelu, dlatego szerokość pobieramy z geometrii,
        # a nie z lokalnej zmiennej pomocniczej.
        g = self.geom['flatten_mode_radio']
        self.flatten_mode_radio = tk.Radiobutton(
            self.options_frame,
            text=self.tr.get('radio.flatten_mode'),
            variable=self.folder_mode,
            value=False,
            command=self.on_copy_mode_changed,
            font=('Arial', 9),
            anchor='w',
            justify='left',
            wraplength=int(self.geom['options_frame']['w'] * 0.82)
        )
        self.flatten_mode_radio.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])

        # Przycisk otwarcia okna wyboru plików dla trybu drive root.
        g = self.geom['select_files_btn']
        self.select_files_btn = tk.Button(
            self.options_frame,
            text=self.tr.get('buttons.select_files'),
            command=self.open_file_selection,
            bg='#607D8B',
            fg='white',
            font=('Arial', 9, 'bold')
        )
        self.select_files_btn.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])

        # Podsumowanie aktualnie wybranych plików lub informacja, że kopiowane będą wszystkie.
        g = self.geom['selection_summary_label']
        self.selection_summary_label = tk.Label(
            self.options_frame,
            text='',
            anchor='nw',
            justify='left',
            wraplength=g['w'],
            font=('Arial', 9)
        )
        self.selection_summary_label.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])

        # =====================================
        # ŚRODKOWA KOLUMNA - STATUS OGÓLNY
        # =====================================
        self.status_frame = tk.LabelFrame(
            self.root,
            text=self.tr.get('labels.status_frame'),
            font=('Arial', 11, 'bold')
        )
        g = self.geom['status_frame']
        self.status_frame.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])

        g = self.geom['overall_progress']
        self.overall_progress = ttk.Progressbar(self.status_frame, mode='determinate', maximum=100)
        self.overall_progress.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])

        g = self.geom['overall_file_label']
        self.overall_file_label = tk.Label(
            self.status_frame,
            text=self.tr.get('status.overall_files', copied=0, total=0, percent=0),
            font=('Arial', 10, 'bold')
        )
        self.overall_file_label.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])

        g = self.geom['status_label']
        self.status_label = tk.Label(
            self.status_frame,
            text=self.tr.get('status.ready'),
            fg='green',
            font=('Arial', 10)
        )
        self.status_label.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])

        # =====================================
        # PRAWA KOLUMNA - LISTA NOŚNIKÓW USB
        # =====================================
        self.usb_frame = tk.LabelFrame(
            self.root,
            text=self.tr.get('labels.usb_frame'),
            font=('Arial', 11, 'bold')
        )
        g = self.geom['usb_frame']
        self.usb_frame.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])

        g = self.geom['usb_canvas']
        self.usb_canvas = tk.Canvas(self.usb_frame, highlightthickness=0)
        self.usb_canvas.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])

        g = self.geom['usb_scrollbar']
        self.usb_scrollbar = ttk.Scrollbar(self.usb_frame, orient='vertical', command=self.usb_canvas.yview)
        self.usb_scrollbar.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])
        self.usb_canvas.configure(yscrollcommand=self.usb_scrollbar.set)

        # Wewnętrzna ramka przewijana. To do niej dodawane są kolejne panele USB.
        self.usb_scrollable_frame = tk.Frame(self.usb_canvas)
        self.usb_canvas_window = self.usb_canvas.create_window((0, 0), window=self.usb_scrollable_frame, anchor='nw')
        self.usb_scrollable_frame.bind(
            '<Configure>',
            lambda e: self.usb_canvas.configure(scrollregion=self.usb_canvas.bbox('all'))
        )
        self.usb_canvas.bind(
            '<Configure>',
            lambda e: self.usb_canvas.itemconfigure(self.usb_canvas_window, width=e.width)
        )

        self.update_selection_summary()

    def create_usb_progress_row(self, usb_path):
        """
        Tworzy pojedynczy panel postępu dla jednego urządzenia USB.

        Panele są układane pionowo: jeden pod drugim.
        Każdy panel zawiera:
        - etykietę urządzenia,
        - pasek postępu,
        - licznik skopiowanych plików,
        - bieżący status operacji dla tego nośnika.
        """
        index = len(self.progress_bars)
        x = 8
        y = 8 + index * (self.usb_card_h + 10)

        frame = tk.Frame(self.usb_scrollable_frame, bd=1, relief='groove')
        frame.place(x=x, y=y, width=self.usb_card_w, height=self.usb_card_h)

        tk.Label(
            frame,
            text=self.tr.get('status.usb_label', usb_path=usb_path),
            font=('Arial', 9, 'bold'),
            anchor='w'
        ).place(x=6, y=6, width=self.usb_card_w - 12, height=18)

        progress_var = tk.DoubleVar(value=0)
        self.progress_bars[usb_path] = progress_var
        ttk.Progressbar(frame, variable=progress_var, maximum=100).place(x=6, y=28, width=self.usb_card_w - 12, height=18)

        file_counter_var = tk.StringVar(value=self.tr.get('status.file_counter', copied=0, total=0))
        self.file_counters[usb_path] = file_counter_var
        tk.Label(
            frame,
            textvariable=file_counter_var,
            font=('Arial', 8, 'bold'),
            fg='blue',
            anchor='w'
        ).place(x=6, y=50, width=self.usb_card_w - 12, height=14)

        status_text = tk.StringVar(value=self.tr.get('status.waiting'))
        self.status_labels[usb_path] = status_text
        tk.Label(
            frame,
            textvariable=status_text,
            font=('Arial', 8),
            fg='gray',
            anchor='w'
        ).place(x=6, y=66, width=self.usb_card_w - 12, height=16)

        self.usb_scrollable_frame.configure(
            width=self.geom['usb_canvas']['w'],
            height=max(self.geom['usb_canvas']['h'], (index + 1) * (self.usb_card_h + 10) + 10)
        )
        return frame

    def update_usb_scrollbar_visibility(self):
        """
        Pokazuje scrollbar tylko wtedy, gdy liczba urządzeń USB nie mieści się wygodnie
        w obszarze prawego panelu.
        """
        if len(getattr(self, 'usb_drives', [])) > 5:
            g = self.geom['usb_scrollbar']
            self.usb_scrollbar.place(x=g['x'], y=g['y'], width=g['w'], height=g['h'])
        else:
            self.usb_scrollbar.place_forget()
            self.usb_canvas.yview_moveto(0)
