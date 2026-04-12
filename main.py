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

import json
import os
import shutil
import subprocess
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from gui import AppGUI

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SETTINGS = {"language": "en"}
LANGUAGE_FILES = {
    "en": BASE_DIR / "lng" / "translations_en.json",
    "pl": BASE_DIR / "lng" / "translations_pl.json",
    "uk": BASE_DIR / "lng" / "translations_uk.json",
}


class SettingsManager:
    def __init__(self, settings_file):
        self.settings_file = Path(settings_file)
        self.data = self.load()

    def load(self):
        if not self.settings_file.exists():
            return dict(DEFAULT_SETTINGS)
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            data = dict(DEFAULT_SETTINGS)
            if isinstance(loaded, dict):
                data.update(loaded)
            return data
        except Exception:
            return dict(DEFAULT_SETTINGS)

    def save(self):
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()


class Translator:
    def __init__(self, language_code='en'):
        self.language_code = language_code if language_code in LANGUAGE_FILES else 'en'
        self.translation_file = LANGUAGE_FILES[self.language_code]
        self.data = self._load_translations()

    def _load_translations(self):
        if not self.translation_file.exists():
            raise FileNotFoundError(f"Translation file not found: {self.translation_file}")
        with open(self.translation_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def set_language(self, language_code):
        self.language_code = language_code if language_code in LANGUAGE_FILES else 'en'
        self.translation_file = LANGUAGE_FILES[self.language_code]
        self.data = self._load_translations()

    def get(self, key, default=None, **kwargs):
        value = self.data
        for part in key.split('.'):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                value = default if default is not None else key
                break
        if isinstance(value, str) and kwargs:
            try:
                return value.format(**kwargs)
            except Exception:
                return value
        return value


class PropertiesDialog(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.tr = app.tr
        self.title(self.tr.get('properties.title'))
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.language_display_to_code = {
            self.tr.get('languages.english'): 'en',
            self.tr.get('languages.polish'): 'pl',
            self.tr.get('languages.ukrainian'): 'uk',
        }
        self.language_code_to_display = {v: k for k, v in self.language_display_to_code.items()}

        container = tk.Frame(self, padx=15, pady=15)
        container.pack(fill='both', expand=True)
        tk.Label(container, text=self.tr.get('properties.language_label'), font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w', pady=(0, 8))
        self.language_combo = ttk.Combobox(container, state='readonly', values=list(self.language_display_to_code.keys()), width=24)
        self.language_combo.grid(row=0, column=1, sticky='ew', pady=(0, 8), padx=(10, 0))
        self.language_combo.set(self.language_code_to_display.get(self.app.current_language, self.tr.get('languages.english')))
        button_frame = tk.Frame(container)
        button_frame.grid(row=1, column=0, columnspan=2, sticky='e', pady=(10, 0))
        tk.Button(button_frame, text=self.tr.get('buttons.cancel'), command=self.destroy, width=12).pack(side='right', padx=(8, 0))
        tk.Button(button_frame, text=self.tr.get('buttons.save'), command=self.on_save, width=12, bg='#4CAF50', fg='white').pack(side='right')
        container.columnconfigure(1, weight=1)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def on_save(self):
        display_name = self.language_combo.get()
        language_code = self.language_display_to_code.get(display_name, 'en')
        self.app.apply_language(language_code)
        self.destroy()


class DuplicateModeDialog(tk.Toplevel):
    def __init__(self, parent, app, duplicates):
        super().__init__(parent)
        self.app = app
        self.tr = app.tr
        self.result = None
        self.title(self.tr.get('duplicate.title'))
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        container = tk.Frame(self, padx=14, pady=14)
        container.pack(fill='both', expand=True)

        tk.Label(
            container,
            text=self.tr.get('duplicate.description', count=len(duplicates)),
            justify='left',
            anchor='w',
            wraplength=540
        ).pack(fill='x', pady=(0, 10))

        duplicates_box = tk.Listbox(container, height=min(8, max(3, len(duplicates))), font=('Arial', 9))
        duplicates_box.pack(fill='both', expand=True, pady=(0, 10))
        for name in duplicates:
            duplicates_box.insert(tk.END, name)

        tk.Label(
            container,
            text=self.tr.get('duplicate.question'),
            justify='left',
            anchor='w',
            wraplength=540,
            font=('Arial', 9, 'bold')
        ).pack(fill='x', pady=(0, 10))

        button_frame = tk.Frame(container)
        button_frame.pack(fill='x')
        tk.Button(
            button_frame,
            text=self.tr.get('duplicate.keep_subfolders'),
            command=lambda: self._close('keep_subfolders'),
            bg='#4CAF50', fg='white'
        ).pack(side='left')
        tk.Button(
            button_frame,
            text=self.tr.get('duplicate.copy_to_root'),
            command=lambda: self._close('copy_to_root')
        ).pack(side='left', padx=(8, 0))
        tk.Button(
            button_frame,
            text=self.tr.get('buttons.cancel'),
            command=lambda: self._close(None)
        ).pack(side='right')

        self.protocol("WM_DELETE_WINDOW", lambda: self._close(None))

    def _close(self, result):
        self.result = result
        self.destroy()


class FileSelectionDialog(tk.Toplevel):
    UNCHECKED = '[ ]'
    CHECKED = '[x]'
    PARTIAL = '[-]'

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.tr = app.tr
        self.title(self.tr.get('selection.title'))
        self.geometry('920x620')
        self.transient(parent)
        self.grab_set()

        self.files = list(self.app.get_flatten_candidates())
        self.selected_rel_paths = set(self.app.selected_flatten_files)
        self.node_to_path = {}
        self.path_to_node = {}
        self.node_kind = {}
        self.folder_nodes = {}
        self.pending_paths = list(self.files)
        self.populate_batch_size = 400

        container = tk.Frame(self, padx=12, pady=12)
        container.pack(fill='both', expand=True)

        tk.Label(
            container,
            text=self.tr.get('selection.description'),
            anchor='w',
            justify='left',
            wraplength=860
        ).pack(fill='x', pady=(0, 8))

        tools = tk.Frame(container)
        tools.pack(fill='x', pady=(0, 8))
        tk.Button(tools, text=self.tr.get('buttons.select_all'), command=self.select_all).pack(side='left')
        tk.Button(tools, text=self.tr.get('selection.select_current_folder'), command=self.select_current_folder).pack(side='left', padx=(8, 0))
        tk.Button(tools, text=self.tr.get('selection.clear_current_folder'), command=self.clear_current_folder).pack(side='left', padx=(8, 0))
        tk.Button(tools, text=self.tr.get('buttons.clear_selection'), command=self.clear_selection).pack(side='left', padx=(8, 0))
        tk.Button(tools, text=self.tr.get('selection.expand_all'), command=self.expand_all).pack(side='right')
        tk.Button(tools, text=self.tr.get('selection.collapse_all'), command=self.collapse_all).pack(side='right', padx=(0, 8))

        tree_frame = tk.Frame(container)
        tree_frame.pack(fill='both', expand=True)

        self.tree = ttk.Treeview(tree_frame, show='tree headings', columns=('kind', 'relative_path'), selectmode='browse')
        self.tree.heading('#0', text=self.tr.get('selection.tree_column_name'))
        self.tree.heading('kind', text=self.tr.get('selection.tree_column_type'))
        self.tree.heading('relative_path', text=self.tr.get('selection.tree_column_path'))
        self.tree.column('#0', width=360, anchor='w')
        self.tree.column('kind', width=100, anchor='center')
        self.tree.column('relative_path', width=360, anchor='w')
        self.tree.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.status_var = tk.StringVar(value=self.tr.get('selection.loading_tree'))
        self.summary_var = tk.StringVar(value='')
        tk.Label(container, textvariable=self.status_var, anchor='w', justify='left').pack(fill='x', pady=(8, 0))
        tk.Label(container, textvariable=self.summary_var, anchor='w', justify='left', font=('Arial', 9, 'bold')).pack(fill='x', pady=(2, 0))

        action_bar = tk.Frame(container)
        action_bar.pack(fill='x', pady=(10, 0))
        tk.Button(action_bar, text=self.tr.get('buttons.cancel'), command=self.destroy, width=12).pack(side='right', padx=(8, 0))
        tk.Button(action_bar, text=self.tr.get('buttons.apply'), command=self.apply_selection, width=12, bg='#4CAF50', fg='white').pack(side='right')

        self.tree.bind('<Double-1>', self.on_double_click)
        self.tree.bind('<space>', self.on_space_toggle)
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_focus_changed)

        self.populate_tree()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.node_to_path.clear()
        self.path_to_node.clear()
        self.node_kind.clear()
        self.folder_nodes.clear()
        self.pending_paths = list(self.files)
        self._populate_tree_chunk()

    def _populate_tree_chunk(self):
        chunk = self.pending_paths[:self.populate_batch_size]
        self.pending_paths = self.pending_paths[self.populate_batch_size:]

        for rel_path in chunk:
            self._insert_path(rel_path)

        loaded = len(self.files) - len(self.pending_paths)
        total = len(self.files)
        self.status_var.set(self.tr.get('selection.loading_progress', loaded=loaded, total=total))

        if self.pending_paths:
            self.after(1, self._populate_tree_chunk)
        else:
            self.status_var.set(self.tr.get('selection.loading_done'))
            self.refresh_all_folder_states()
            self.update_summary()

    def _insert_path(self, rel_path):
        parts = Path(rel_path).parts
        parent = ''
        current_parts = []

        for part in parts[:-1]:
            current_parts.append(part)
            folder_key = '/'.join(current_parts)
            if folder_key not in self.folder_nodes:
                node = self.tree.insert(parent, 'end', text=self._prefixed_text(self.UNCHECKED, part), values=(self.tr.get('selection.folder_type'), folder_key), open=False)
                self.folder_nodes[folder_key] = node
                self.node_to_path[node] = folder_key
                self.path_to_node[folder_key] = node
                self.node_kind[node] = 'folder'
            parent = self.folder_nodes[folder_key]

        file_name = parts[-1]
        file_node = self.tree.insert(parent, 'end', text=self._prefixed_text(self.CHECKED if rel_path in self.selected_rel_paths else self.UNCHECKED, file_name), values=(self.tr.get('selection.file_type'), rel_path))
        self.node_to_path[file_node] = rel_path
        self.path_to_node[rel_path] = file_node
        self.node_kind[file_node] = 'file'

    def _prefixed_text(self, marker, label):
        return f'{marker} {label}'

    def _strip_prefix(self, text):
        if len(text) >= 4 and text[:3] in {self.UNCHECKED, self.CHECKED, self.PARTIAL}:
            return text[4:]
        return text

    def _set_marker(self, node, marker):
        label = self._strip_prefix(self.tree.item(node, 'text'))
        self.tree.item(node, text=self._prefixed_text(marker, label))

    def _get_marker(self, node):
        text = self.tree.item(node, 'text')
        prefix = text[:3] if len(text) >= 3 else self.UNCHECKED
        return prefix if prefix in {self.UNCHECKED, self.CHECKED, self.PARTIAL} else self.UNCHECKED

    def on_double_click(self, event):
        node = self.tree.identify_row(event.y)
        if node:
            self.toggle_node(node)
            return 'break'
        return None

    def on_space_toggle(self, _event):
        node = self.tree.focus()
        if node:
            self.toggle_node(node)
            return 'break'
        return None

    def on_tree_focus_changed(self, _event=None):
        self.update_summary()

    def toggle_node(self, node):
        if self.pending_paths:
            self.status_var.set(self.tr.get('selection.wait_until_loaded'))
            return

        kind = self.node_kind.get(node)
        current = self._get_marker(node)
        should_check = current in {self.UNCHECKED, self.PARTIAL}

        if kind == 'file':
            self._toggle_file(node, should_check)
        elif kind == 'folder':
            self._toggle_folder(node, should_check)

        self._update_parent_states(node)
        self.update_summary()

    def _toggle_file(self, node, checked):
        rel_path = self.node_to_path[node]
        if checked:
            self.selected_rel_paths.add(rel_path)
            self._set_marker(node, self.CHECKED)
        else:
            self.selected_rel_paths.discard(rel_path)
            self._set_marker(node, self.UNCHECKED)

    def _toggle_folder(self, node, checked):
        for item in [node] + self._get_all_descendants(node):
            kind = self.node_kind.get(item)
            if kind == 'file':
                self._toggle_file(item, checked)
            elif kind == 'folder':
                self._set_marker(item, self.CHECKED if checked else self.UNCHECKED)

    def _get_all_descendants(self, node):
        result = []
        stack = list(self.tree.get_children(node))
        while stack:
            child = stack.pop()
            result.append(child)
            stack.extend(self.tree.get_children(child))
        return result

    def _update_parent_states(self, node):
        parent = self.tree.parent(node)
        while parent:
            child_states = [self._get_marker(child) for child in self.tree.get_children(parent)]
            if child_states and all(state == self.CHECKED for state in child_states):
                self._set_marker(parent, self.CHECKED)
            elif any(state in {self.CHECKED, self.PARTIAL} for state in child_states):
                self._set_marker(parent, self.PARTIAL)
            else:
                self._set_marker(parent, self.UNCHECKED)
            parent = self.tree.parent(parent)

    def refresh_all_folder_states(self):
        for node in self.tree.get_children(''):
            self._refresh_subtree_state(node)

    def _refresh_subtree_state(self, node):
        for child in self.tree.get_children(node):
            self._refresh_subtree_state(child)
        if self.node_kind.get(node) == 'folder':
            child_states = [self._get_marker(child) for child in self.tree.get_children(node)]
            if child_states and all(state == self.CHECKED for state in child_states):
                self._set_marker(node, self.CHECKED)
            elif any(state in {self.CHECKED, self.PARTIAL} for state in child_states):
                self._set_marker(node, self.PARTIAL)
            else:
                self._set_marker(node, self.UNCHECKED)

    def select_all(self):
        if self.pending_paths:
            self.status_var.set(self.tr.get('selection.wait_until_loaded'))
            return
        self.selected_rel_paths = set(self.files)
        for node in self.node_to_path:
            self._set_marker(node, self.CHECKED)
        self.refresh_all_folder_states()
        self.update_summary()

    def clear_selection(self):
        if self.pending_paths:
            self.status_var.set(self.tr.get('selection.wait_until_loaded'))
            return
        self.selected_rel_paths.clear()
        for node in self.node_to_path:
            self._set_marker(node, self.UNCHECKED)
        self.refresh_all_folder_states()
        self.update_summary()

    def select_current_folder(self):
        if self.pending_paths:
            self.status_var.set(self.tr.get('selection.wait_until_loaded'))
            return
        node = self.tree.focus()
        if not node:
            return
        if self.node_kind.get(node) == 'file':
            parent = self.tree.parent(node)
            if not parent:
                self._toggle_file(node, True)
                self.update_summary()
                return
            node = parent
        self._toggle_folder(node, True)
        self._update_parent_states(node)
        self.update_summary()

    def clear_current_folder(self):
        if self.pending_paths:
            self.status_var.set(self.tr.get('selection.wait_until_loaded'))
            return
        node = self.tree.focus()
        if not node:
            return
        if self.node_kind.get(node) == 'file':
            self._toggle_file(node, False)
            self._update_parent_states(node)
            self.update_summary()
            return
        self._toggle_folder(node, False)
        self._update_parent_states(node)
        self.update_summary()

    def expand_all(self):
        if self.pending_paths:
            self.status_var.set(self.tr.get('selection.wait_until_loaded'))
            return
        for node, kind in self.node_kind.items():
            if kind == 'folder':
                self.tree.item(node, open=True)

    def collapse_all(self):
        if self.pending_paths:
            self.status_var.set(self.tr.get('selection.wait_until_loaded'))
            return
        for node, kind in self.node_kind.items():
            if kind == 'folder':
                self.tree.item(node, open=False)

    def update_summary(self):
        selected_files = len(self.selected_rel_paths)
        selected_folders = sum(1 for node, kind in self.node_kind.items() if kind == 'folder' and self._get_marker(node) == self.CHECKED)
        self.summary_var.set(self.tr.get('selection.summary_line', files=selected_files, folders=selected_folders, total=len(self.files)))

    def apply_selection(self):
        if self.pending_paths:
            self.status_var.set(self.tr.get('selection.wait_until_loaded'))
            return
        self.app.selected_flatten_files = sorted(self.selected_rel_paths)
        self.app.invalidate_file_cache()
        self.app.update_selection_summary()
        self.destroy()


class USBCopyGUI(AppGUI):
    def __init__(self, root):
        self.root = root
        self.settings = SettingsManager(BASE_DIR / 'settings.json')
        self.current_language = self.settings.get('language', 'en')
        self.tr = Translator(self.current_language)

        self.usb_drives = []
        self.source_path = tk.StringVar()
        self.source_files = []
        self.copying = False
        self.progress_bars = {}
        self.status_labels = {}
        self.file_counters = {}
        self._progress_data = {}
        self._progress_lock = threading.Lock()
        self.selected_flatten_files = []
        self.flatten_duplicate_mode = 'copy_to_root'

        # Cache katalogu źródłowego ogranicza wielokrotne kosztowne rglob('*') podczas pracy GUI.
        self._source_file_cache = []
        self._source_cache_key = None
        self._selected_file_cache = None
        self._selected_file_cache_key = None

        self.root.resizable(True, True)
        self.configure_window_by_screen()
        super().__init__(root, self.tr)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.update_default_folder_name()
        self.refresh_usb()

    def configure_window_by_screen(self):
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        if screen_w >= 3800 or screen_h >= 2100:
            self.base_width, self.base_height = 1800, 1200
        else:
            self.base_width, self.base_height = 1200, 800
        self.root.geometry(f"{self.base_width}x{self.base_height}")
        self.root.minsize(760, 700)

    def invalidate_file_cache(self):
        self._selected_file_cache = None
        self._selected_file_cache_key = None

    def rebuild_source_cache(self):
        source = self.source_path.get().strip()
        if not source or not os.path.exists(source):
            self._source_file_cache = []
            self._source_cache_key = None
            self.invalidate_file_cache()
            return

        source_path = Path(source)
        cache = []
        for path in source_path.rglob('*'):
            if path.is_file():
                rel_path = str(path.relative_to(source_path))
                cache.append((path, rel_path, path.name))
        self._source_file_cache = cache
        self._source_cache_key = source
        self.invalidate_file_cache()

    def ensure_source_cache(self):
        source = self.source_path.get().strip()
        if self._source_cache_key != source:
            self.rebuild_source_cache()

    def update_default_folder_name(self):
        source = self.source_path.get().strip()
        if source and os.path.exists(source) and self.folder_mode.get():
            self.folder_name.set(Path(source).name)

    def get_flatten_candidates(self):
        self.ensure_source_cache()
        return [rel_path for _, rel_path, _ in self._source_file_cache]

    def get_duplicate_filenames(self, rel_paths):
        counts = Counter(Path(p).name for p in rel_paths)
        return sorted([name for name, count in counts.items() if count > 1])

    def ensure_duplicate_mode_for_flatten(self):
        if self.folder_mode.get():
            return True

        rel_paths = [str(p.relative_to(Path(self.source_path.get()))) for p in self.get_files_for_copy()]
        duplicates = self.get_duplicate_filenames(rel_paths)
        if not duplicates:
            self.flatten_duplicate_mode = 'copy_to_root'
            return True

        dialog = DuplicateModeDialog(self.root, self, duplicates)
        self.root.wait_window(dialog)
        if dialog.result is None:
            return False
        self.flatten_duplicate_mode = dialog.result
        return True

    def update_selection_summary(self):
        total_available = len(self.get_flatten_candidates())
        selected = len(self.selected_flatten_files)

        if self.folder_mode.get():
            self.selection_summary_label.config(text=self.tr.get('selection.hidden_in_folder_mode'))
            self.select_files_btn.config(state='disabled')
            self.folder_name_entry.config(state='normal')
            return

        self.select_files_btn.config(state='normal')
        self.folder_name_entry.config(state='disabled')

        if selected == 0 and total_available > 0:
            text = self.tr.get('selection.no_selection_means_all', total=total_available)
        else:
            text = self.tr.get('selection.selected_count', selected=selected, total=total_available)

        duplicates = self.get_duplicate_filenames(self.selected_flatten_files or self.get_flatten_candidates())
        if duplicates:
            text += '\n' + self.tr.get('selection.duplicate_warning', count=len(duplicates))

        self.selection_summary_label.config(text=text)

    def on_copy_mode_changed(self):
        self.update_default_folder_name()
        self.update_selection_summary()

    def show_help(self):
        messagebox.showinfo(self.tr.get('help.title'), self.tr.get('help.content'))

    def show_about_author(self):
        messagebox.showinfo(self.tr.get('about.title'), self.tr.get('about.content'))

    def apply_language(self, language_code):
        self.current_language = language_code if language_code in LANGUAGE_FILES else 'en'
        self.settings.set('language', self.current_language)
        self.tr.set_language(self.current_language)
        self.retranslate_ui()

    def retranslate_ui(self):
        self.root.title(self.tr.get('window.title'))
        self.create_menu()
        self.left_panel.config(text=self.tr.get('labels.control_frame', default='🎮 Control'))
        self.left_hint.config(text=self.tr.get('labels.control_hint', default='Use these buttons to start or stop copying.'))
        self.source_frame.config(text=self.tr.get('labels.source_frame'))
        self.browse_btn.config(text=self.tr.get('buttons.browse'))
        self.usb_frame.config(text=self.tr.get('labels.usb_frame'))
        self.refresh_btn.config(text=self.tr.get('buttons.refresh_usb'))
        self.options_frame.config(text=self.tr.get('labels.options_frame'))
        self.folder_mode_radio.config(text=self.tr.get('radio.folder_mode'))
        self.flatten_mode_radio.config(text=self.tr.get('radio.flatten_mode'))
        self.folder_name_label.config(text=self.tr.get('labels.folder_name'))
        self.select_files_btn.config(text=self.tr.get('buttons.select_files'))
        self.status_frame.config(text=self.tr.get('labels.status_frame'))
        self.copy_btn.config(text=self.tr.get('buttons.start_copy'))
        self.stop_btn.config(text=self.tr.get('buttons.stop_copy'))
        self.exit_btn.config(text=self.tr.get('buttons.exit_app', default='Exit'))

        with self._progress_lock:
            data = dict(self._progress_data)
        total_files = sum(d['total'] for d in data.values()) if data else 0
        copied_files_total = sum(d['copied'] for d in data.values()) if data else 0
        percent = (copied_files_total / total_files) * 100 if total_files > 0 else 0
        self.overall_file_label.config(text=self.tr.get('status.overall_files', copied=copied_files_total, total=total_files, percent=f"{percent:.0f}"))
        self.rebuild_usb_rows()
        self.status_label.config(text=self.tr.get('status.copying_in_progress') if self.copying else self.tr.get('status.ready'), fg='blue' if self.copying else 'green')
        self.update_source_list()
        self.update_selection_summary()

    def rebuild_usb_rows(self):
        current_progress = {usb: self.progress_bars[usb].get() if usb in self.progress_bars else 0 for usb in self.usb_drives}
        for widget in self.usb_scrollable_frame.winfo_children():
            widget.destroy()
        self.progress_bars.clear()
        self.status_labels.clear()
        self.file_counters.clear()

        for usb in self.usb_drives:
            self.create_usb_progress_row(usb)
            with self._progress_lock:
                copied = self._progress_data.get(usb, {}).get('copied', 0)
                total = self._progress_data.get(usb, {}).get('total', 0)
            self.progress_bars[usb].set(current_progress.get(usb, 0))
            if copied >= total and total > 0:
                self.file_counters[usb].set(self.tr.get('status.file_counter_done', copied=copied, total=total))
                self.status_labels[usb].set(self.tr.get('status.completed'))
            else:
                self.file_counters[usb].set(self.tr.get('status.file_counter', copied=copied, total=total))
                self.status_labels[usb].set(self.tr.get('status.waiting') if copied == 0 else self.tr.get('status.copying_generic'))

        self.update_usb_scrollbar_visibility()

    def on_closing(self):
        if messagebox.askokcancel(self.tr.get('dialogs.close.title'), self.tr.get('dialogs.close.message')):
            self.copying = False
            self.root.quit()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label=self.tr.get('menu.file.exit'), command=self.on_closing)
        menubar.add_cascade(label=self.tr.get('menu.file.title'), menu=file_menu)
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label=self.tr.get('menu.settings.properties'), command=self.open_properties)
        menubar.add_cascade(label=self.tr.get('menu.settings.title'), menu=settings_menu)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label=self.tr.get('menu.help.instructions'), command=self.show_help)
        help_menu.add_command(label=self.tr.get('menu.help.about_author'), command=self.show_about_author)
        menubar.add_cascade(label=self.tr.get('menu.help.title'), menu=help_menu)
        self.root.config(menu=menubar)

    def open_properties(self):
        PropertiesDialog(self.root, self)

    def open_file_selection(self):
        if self.folder_mode.get():
            return
        source = self.source_path.get().strip()
        if not source or not os.path.exists(source):
            messagebox.showerror(self.tr.get('dialogs.error.title'), self.tr.get('dialogs.error.select_source'))
            return
        FileSelectionDialog(self.root, self)

    def safe_copy_file(self, src_file, dst_file):
        buffer_size = 1024 * 1024
        try:
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            with open(src_file, 'rb') as src_f, open(dst_file, 'wb') as dst_f:
                shutil.copyfileobj(src_f, dst_f, length=buffer_size)
                dst_f.flush()
                os.fsync(dst_f.fileno())
            return self.copying
        except Exception:
            return False

    def _ui_update_progress(self, usb, copied, total, filename, progress):
        self.file_counters[usb].set(self.tr.get('status.file_counter', copied=copied, total=total))
        self.progress_bars[usb].set(progress)
        self.status_labels[usb].set(self.tr.get('status.copying_file', filename=filename))

    def _ui_update_done(self, usb, copied, total):
        self.file_counters[usb].set(self.tr.get('status.file_counter_done', copied=copied, total=total))
        self.progress_bars[usb].set(100)
        self.status_labels[usb].set(self.tr.get('status.completed'))

    def _ui_update_error(self, usb, error_msg):
        self.status_labels[usb].set(self.tr.get('status.error', error_msg=error_msg))

    def get_files_for_copy(self):
        self.ensure_source_cache()
        source = Path(self.source_path.get())

        if self.folder_mode.get():
            return [abs_path for abs_path, _, _ in self._source_file_cache]

        cache_key = (self._source_cache_key, tuple(sorted(self.selected_flatten_files)))
        if self._selected_file_cache_key == cache_key and self._selected_file_cache is not None:
            return self._selected_file_cache

        if not self.selected_flatten_files:
            result = [abs_path for abs_path, _, _ in self._source_file_cache]
        else:
            selected_set = set(self.selected_flatten_files)
            result = [abs_path for abs_path, rel_path, _ in self._source_file_cache if rel_path in selected_set]

        self._selected_file_cache = result
        self._selected_file_cache_key = cache_key
        return result

    def copy_to_single_usb(self, usb_root):
        try:
            source = Path(self.source_path.get())
            files_to_copy = self.get_files_for_copy()
            total_files = len(files_to_copy)
            copied_files = 0

            with self._progress_lock:
                self._progress_data[usb_root] = {'copied': 0, 'total': total_files}

            self.root.after(0, lambda u=usb_root: self.status_labels[u].set(self.tr.get('status.preparing')))

            if self.folder_mode.get():
                target_dir = Path(usb_root) / self.folder_name.get()
                if target_dir.exists():
                    shutil.rmtree(target_dir, ignore_errors=True)
                target_dir.mkdir(exist_ok=True)

                for src_file in files_to_copy:
                    if not self.copying:
                        break
                    rel_path = src_file.relative_to(source)
                    dst_file = target_dir / rel_path
                    if self.safe_copy_file(src_file, dst_file):
                        copied_files += 1
                        progress = (copied_files / total_files) * 100 if total_files > 0 else 100
                        with self._progress_lock:
                            self._progress_data[usb_root]['copied'] = copied_files
                        self.root.after(0, lambda u=usb_root, cf=copied_files, tf=total_files, fn=str(rel_path), p=progress: self._ui_update_progress(u, cf, tf, fn, p))
            else:
                keep_subfolders = self.flatten_duplicate_mode == 'keep_subfolders'
                for src_file in files_to_copy:
                    if not self.copying:
                        break
                    rel_path = src_file.relative_to(source)
                    dst_file = (Path(usb_root) / rel_path) if keep_subfolders else (Path(usb_root) / src_file.name)
                    if self.safe_copy_file(src_file, dst_file):
                        copied_files += 1
                        progress = (copied_files / total_files) * 100 if total_files > 0 else 100
                        with self._progress_lock:
                            self._progress_data[usb_root]['copied'] = copied_files
                        self.root.after(0, lambda u=usb_root, cf=copied_files, tf=total_files, fn=str(rel_path), p=progress: self._ui_update_progress(u, cf, tf, fn, p))

            self.root.after(0, lambda u=usb_root, cf=copied_files, tf=total_files: self._ui_update_done(u, cf, tf))
            return True
        except Exception as e:
            self.root.after(0, lambda u=usb_root, err=str(e): self._ui_update_error(u, err))
            return False

    def start_copy(self):
        if not self.validate_inputs():
            return
        if not self.folder_mode.get() and not self.ensure_duplicate_mode_for_flatten():
            return

        self.copying = True
        self.copy_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status_label.config(text=self.tr.get('status.copying_in_progress'), fg='blue')
        self.overall_progress['maximum'] = 100
        self.overall_progress['value'] = 0
        self.overall_file_label.config(text=self.tr.get('status.overall_files', copied=0, total=0, percent=0))

        with self._progress_lock:
            self._progress_data.clear()

        for usb in self.usb_drives:
            self.file_counters[usb].set(self.tr.get('status.file_counter', copied=0, total=0))
            self.progress_bars[usb].set(0)
            self.status_labels[usb].set(self.tr.get('status.starting'))

        self.executor = ThreadPoolExecutor(max_workers=len(self.usb_drives))
        for usb in self.usb_drives:
            self.executor.submit(self.copy_to_single_usb, usb)
        self._update_overall_status()

    def _update_overall_status(self):
        if not self.copying:
            return

        with self._progress_lock:
            data = dict(self._progress_data)
        if not data:
            self.root.after(300, self._update_overall_status)
            return

        total_files = sum(d['total'] for d in data.values())
        copied_files_total = sum(d['copied'] for d in data.values())
        percent = (copied_files_total / total_files) * 100 if total_files > 0 else 0

        self.overall_progress['value'] = percent
        self.overall_file_label.config(text=self.tr.get('status.overall_files', copied=copied_files_total, total=total_files, percent=f"{percent:.0f}"))

        if total_files > 0 and copied_files_total >= total_files:
            self.status_label.config(text=self.tr.get('status.all_completed'), fg='green')
            self.copying = False
            self.copy_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            return

        self.root.after(300, self._update_overall_status)

    def stop_copy(self):
        self.copying = False
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
        self.status_label.config(text=self.tr.get('status.stopped'), fg='orange')
        self.copy_btn.config(state='normal')
        self.stop_btn.config(state='disabled')

    def browse_source(self):
        path = filedialog.askdirectory()
        if path:
            self.source_path.set(path)
            self.selected_flatten_files = []
            self.flatten_duplicate_mode = 'copy_to_root'
            self.rebuild_source_cache()
            self.update_source_list()
            self.update_default_folder_name()
            self.update_selection_summary()
            self.update_copy_button()

    def update_source_list(self):
        path = self.source_path.get()
        self.source_listbox.delete(0, tk.END)
        if os.path.exists(path):
            total_size = 0
            file_count = 0
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path):
                    size = os.path.getsize(item_path) / 1024
                    total_size += size
                    file_count += 1
                    self.source_listbox.insert(tk.END, self.tr.get('list.file_item', item=item, size=f"{size:.1f}"))
                elif os.path.isdir(item_path):
                    self.source_listbox.insert(tk.END, self.tr.get('list.dir_item', item=item))
            self.source_listbox.insert(tk.END, self.tr.get('list.summary', file_count=file_count, total_size=f"{total_size:.1f}"))

    def refresh_usb(self):
        for widget in self.usb_scrollable_frame.winfo_children():
            widget.destroy()
        self.progress_bars.clear()
        self.status_labels.clear()
        self.file_counters.clear()
        self.usb_drives = []
        self.usb_scrollable_frame.configure(width=self.geom['usb_canvas']['w'], height=self.geom['usb_canvas']['h'])
        self.usb_canvas.configure(scrollregion=(0, 0, self.geom['usb_canvas']['w'], self.geom['usb_canvas']['h']))
        self.update_usb_scrollbar_visibility()
        self.update_copy_button()
        threading.Thread(target=self._refresh_usb_thread, daemon=True).start()

    def _refresh_usb_thread(self):
        self.usb_drives = self.get_usb_drives()
        self.root.after(0, self._update_usb_list)

    def _update_usb_list(self):
        for widget in self.usb_scrollable_frame.winfo_children():
            widget.destroy()
        self.progress_bars.clear()
        self.status_labels.clear()
        self.file_counters.clear()
        for usb in self.usb_drives:
            self.create_usb_progress_row(usb)
        self.update_usb_scrollbar_visibility()
        self.update_copy_button()

    def get_usb_drives(self):
        try:
            proc = subprocess.run(
                ['powershell', 'Get-WmiObject -Class Win32_LogicalDisk | Select-Object deviceid,volumename,drivetype | ConvertTo-Json -Compress'],
                capture_output=True, text=True, encoding='utf-8', timeout=5
            )
            if proc.returncode != 0:
                return []
            devices = json.loads(proc.stdout)
            if isinstance(devices, dict):
                devices = [devices]
            return [d['deviceid'].rstrip(':') + ':\\' for d in devices if d['drivetype'] == 2]
        except Exception:
            return []

    def update_copy_button(self):
        source_ok = bool(self.source_path.get() and os.path.exists(self.source_path.get()))
        usb_ok = bool(self.usb_drives)
        self.copy_btn.config(state='normal' if source_ok and usb_ok else 'disabled')

    def validate_inputs(self):
        source = self.source_path.get()
        if not source or not os.path.exists(source):
            messagebox.showerror(self.tr.get('dialogs.error.title'), self.tr.get('dialogs.error.select_source'))
            return False
        if not self.usb_drives:
            messagebox.showerror(self.tr.get('dialogs.error.title'), self.tr.get('dialogs.error.connect_usb'))
            return False
        files_for_copy = self.get_files_for_copy()
        if not files_for_copy:
            messagebox.showerror(self.tr.get('dialogs.error.title'), self.tr.get('dialogs.error.no_files_selected'))
            return False
        return True


def main():
    root = tk.Tk()
    app = USBCopyGUI(root)
    app.retranslate_ui()
    root.mainloop()


if __name__ == '__main__':
    main()
