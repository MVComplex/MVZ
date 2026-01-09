# ui/main_window.py
from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QFrame, QMessageBox, QStackedWidget,
    QSystemTrayIcon, QMenu, QCheckBox, QApplication, QComboBox
)
from PySide6.QtCore import Qt, QProcess, QTimer, QSettings, QUrl
from PySide6.QtGui import QAction, QPixmap, QIcon, QDesktopServices

import os
import sys
import datetime
import time
import ctypes
import subprocess
import shlex
import json
import urllib.request
import urllib.error
import tempfile
from typing import Optional, List, Tuple

# --- КОНФИГУРАЦИЯ ОБНОВЛЕНИЙ ---
UPDATE_OWNER = "MVComplex"
UPDATE_REPO = "MVZ"
UPDATE_ASSET_NAME = "MVZ.exe"
UPDATE_CHECK_URL = f"https://api.github.com/repos/{UPDATE_OWNER}/{UPDATE_REPO}/releases/latest"
# -------------------------------

try:
    import psutil
except ImportError:
    psutil = None

try:
    from discord_rpc import DiscordRPC, PYPRESENCE_AVAILABLE
except ImportError:
    PYPRESENCE_AVAILABLE = False
    DiscordRPC = None

CREATE_NO_WINDOW = 0x08000000
APP_VERSION = "1.3.0"

ALT11_BAT_CANDIDATES = [
    "general (ALT11).bat",
    "general-ALT11.bat",
    "general_ALT11.bat",
]

# -------------------- Styles --------------------

DARK_STYLESHEET = """
QMainWindow { background: #0F172A; }
QFrame#Sidebar { background: #020617; border-right: 1px solid #1E293B; min-width: 220px; max-width: 220px; }
QPushButton[objectName="Nav"] {
    background: transparent; color: #9CA3AF; border: none; border-radius: 10px;
    padding: 10px 14px; text-align: left; font-size: 14px; font-weight: 500; margin: 4px 10px;
}
QPushButton[objectName="Nav"]:hover { background: rgba(59,130,246,0.12); color: #BFDBFE; }
QPushButton[objectName="Nav"]:checked {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #2563EB, stop:1 #0EA5E9);
    color: #FFFFFF; font-weight: 600;
}
QPushButton[objectName="Action"] {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #22C55E, stop:1 #16A34A);
    color: #F9FAFB; border: none; border-radius: 14px; padding: 10px 22px;
    font-size: 14px; font-weight: 600; min-width: 150px;
}
QPushButton[objectName="Action"]:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #4ADE80, stop:1 #22C55E);
}
QPushButton[objectName="Action"]:pressed { background: #15803D; }
QPushButton[objectName="Action"]:disabled { background: #1F2933; color: #64748B; }
QCheckBox { color: #CBD5E1; spacing: 8px; font-size: 13px; }
QCheckBox::indicator {
    width: 18px; height: 18px; border-radius: 4px;
    border: 2px solid #475569; background: #020617;
}
QCheckBox::indicator:hover { border-color: #64748B; }
QCheckBox::indicator:checked { background: #1D4ED8; border-color: #60A5FA; }
QTextEdit {
    background: #020617; color: #E2E8F0; border: 1px solid #1F2937;
    border-radius: 12px; padding: 10px; font-size: 13px; selection-background-color: #2563EB;
}
QComboBox {
    background: #020617; color: #E5E7EB; border: 1px solid #1F2937;
    border-radius: 10px; padding: 6px 32px 6px 10px; font-size: 13px;
}
QComboBox:hover { border-color: #3B82F6; }
QLabel { color: #E2E8F0; }
"""

LIGHT_STYLESHEET = """
QMainWindow { background: #F9FAFB; }
QFrame#Sidebar { background: #EFF2F7; border-right: 1px solid #D1D5DB; min-width: 220px; max-width: 220px; }
QPushButton[objectName="Nav"] {
    background: transparent; color: #4B5563; border: none; border-radius: 10px;
    padding: 10px 14px; text-align: left; font-size: 14px; font-weight: 500; margin: 4px 10px;
}
QPushButton[objectName="Nav"]:hover { background: #E0F2FE; color: #1D4ED8; }
QPushButton[objectName="Nav"]:checked { background: #2563EB; color: #FFFFFF; font-weight: 600; }
QPushButton[objectName="Action"] {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #3B82F6, stop:1 #2563EB);
    color: #FFFFFF; border: none; border-radius: 14px; padding: 10px 22px;
    font-size: 14px; font-weight: 600; min-width: 150px;
}
QPushButton[objectName="Action"]:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #60A5FA, stop:1 #3B82F6);
}
QPushButton[objectName="Action"]:pressed { background: #1D4ED8; }
QPushButton[objectName="Action"]:disabled { background: #E5E7EB; color: #9CA3AF; }
QCheckBox { color: #111827; spacing: 8px; font-size: 13px; }
QCheckBox::indicator {
    width: 18px; height: 18px; border-radius: 4px;
    border: 2px solid #9CA3AF; background: #F9FAFB;
}
QCheckBox::indicator:hover { border-color: #6B7280; }
QCheckBox::indicator:checked { background: #3B82F6; border-color: #1D4ED8; }
QTextEdit {
    background: #FFFFFF; color: #111827; border: 1px solid #D1D5DB;
    border-radius: 12px; padding: 10px; font-size: 13px;
}
QComboBox {
    background: #FFFFFF; color: #111827; border: 1px solid #D1D5DB;
    border-radius: 10px; padding: 6px 32px 6px 10px; font-size: 13px;
}
QComboBox:hover { border-color: #3B82F6; }
QLabel { color: #111827; }
"""

PURPLE_STYLESHEET = """
QMainWindow { background: #050816; }
QFrame#Sidebar { background: #0B1020; border-right: 1px solid #4C1D95; min-width: 220px; max-width: 220px; }
QPushButton[objectName="Nav"] {
    background: transparent; color: #C4B5FD; border: none; border-radius: 10px;
    padding: 10px 14px; text-align: left; font-size: 14px; font-weight: 500; margin: 4px 10px;
}
QPushButton[objectName="Nav"]:hover { background: rgba(129,140,248,0.18); color: #E0E7FF; }
QPushButton[objectName="Nav"]:checked {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7C3AED, stop:1 #6366F1);
    color: #FFFFFF; font-weight: 600;
}
QPushButton[objectName="Action"] {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #8B5CF6, stop:1 #6366F1);
    color: #F9FAFB; border: none; border-radius: 14px; padding: 10px 22px;
    font-size: 14px; font-weight: 600; min-width: 150px;
}
QPushButton[objectName="Action"]:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #A855F7, stop:1 #818CF8);
}
QPushButton[objectName="Action"]:pressed { background: #4C1D95; }
QPushButton[objectName="Action"]:disabled { background: #111827; color: #6B7280; }
QCheckBox { color: #E5E7EB; spacing: 8px; font-size: 13px; }
QCheckBox::indicator {
    width: 18px; height: 18px; border-radius: 4px;
    border: 2px solid #4C1D95; background: #020617;
}
QCheckBox::indicator:hover { border-color: #7C3AED; }
QCheckBox::indicator:checked { background: #7C3AED; border-color: #C4B5FD; }
QTextEdit {
    background: #020617; color: #E5E7EB; border: 1px solid #312E81;
    border-radius: 12px; padding: 10px; font-size: 13px; selection-background-color: #6366F1;
}
QComboBox {
    background: #020617; color: #E5E7EB; border: 1px solid #312E81;
    border-radius: 10px; padding: 6px 32px 6px 10px; font-size: 13px;
}
QComboBox:hover { border-color: #7C3AED; }
QLabel { color: #E5E7EB; }
"""

# -------------------- Helpers --------------------

SW_HIDE = 0


def ensure_hidden_console():
    """
    FIX для --noconsole/--windowed:
    создаём консоль (если её нет), и сразу прячем, чтобы консоль не всплывала,
    но дочерние процессы (winws) работали как в console-сборке.
    """
    if os.name != "nt":
        return

    try:
        k32 = ctypes.windll.kernel32
        u32 = ctypes.windll.user32

        hwnd = k32.GetConsoleWindow()
        if hwnd:
            u32.ShowWindow(hwnd, SW_HIDE)
            return

        k32.AllocConsole()
        hwnd = k32.GetConsoleWindow()
        if hwnd:
            u32.ShowWindow(hwnd, SW_HIDE)
    except Exception:
        pass


def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def _pid_alive(pid: int) -> bool:
    if pid is None or pid <= 0:
        return False
    if psutil:
        try:
            return psutil.pid_exists(pid) and psutil.Process(pid).is_running()
        except Exception:
            return False
    try:
        out = subprocess.check_output(
            ["cmd", "/c", f'tasklist /FI "PID eq {pid}"'],
            creationflags=CREATE_NO_WINDOW,
        ).decode("utf-8", errors="replace")
        return str(pid) in out
    except Exception:
        return False


_winws_process_cache = None
_cache_time = 0.0
CACHE_DURATION = 2.0


def get_winws_process():
    global _winws_process_cache, _cache_time
    now = time.time()
    if _winws_process_cache and now - _cache_time < CACHE_DURATION:
        try:
            if _winws_process_cache.is_running():
                return _winws_process_cache
        except Exception:
            pass
    _winws_process_cache = None
    _cache_time = now
    if psutil:
        try:
            for p in psutil.process_iter(["pid", "name"]):
                if p.info["name"] == "winws.exe":
                    _winws_process_cache = p
                    break
        except Exception:
            pass
    return _winws_process_cache


def resource_path(relative_path):
    """
    Возвращает абсолютный путь к ресурсу.
    Работает и в PyInstaller (sys._MEIPASS), и в обычном режиме.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def _app_dir() -> str:
    """
    Возвращает папку, где лежит EXE (или main.py).
    Используется для поиска батников и конфигов рядом с программой.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def resolve_alt11_bat() -> str:
    app_dir = _app_dir()
    candidates = []
    for name in ALT11_BAT_CANDIDATES:
        candidates.append(os.path.join(app_dir, name))
        candidates.append(os.path.join(app_dir, "ZZZ", name))
    for p in candidates:
        if os.path.isfile(p):
            return p
    return candidates[0]


def _parse_bat_variables_and_command(bat_path: str) -> Tuple[str, List[str], str]:
    bat_dir = os.path.abspath(os.path.dirname(bat_path))
    env = {}

    def get_var(k):
        return env.get(k.lower())

    def set_var(k, v):
        env[k.lower()] = v

    set_var("~dp0", bat_dir + "\\")

    bin_dir = os.path.join(bat_dir, "bin")
    if os.path.isdir(bin_dir):
        set_var("BIN", bin_dir + "\\")
    else:
        set_var("BIN", bat_dir + "\\")

    with open(bat_path, "r", encoding="utf-8", errors="ignore") as f:
        raw_lines = f.readlines()

    lines = []
    buf = ""
    for raw in raw_lines:
        s = raw.strip()
        if not s:
            continue
        low = s.lower()
        if low.startswith("rem ") or low.startswith("::") or low.startswith("@"):
            continue
        if s.endswith("^"):
            buf += s[:-1] + " "
        else:
            buf += s
            lines.append(buf.strip())
            buf = ""
    if buf:
        lines.append(buf)

    winws_cmd_parts = None

    for ln in lines:
        resolved_ln = ln.replace("%~dp0", bat_dir + "\\")
        for _ in range(10):
            if "%" not in resolved_ln:
                break
            new_ln = ""
            i = 0
            while i < len(resolved_ln):
                if resolved_ln[i] == "%":
                    j = resolved_ln.find("%", i + 1)
                    if j != -1:
                        var_name = resolved_ln[i + 1:j]
                        val = get_var(var_name)
                        if val is not None:
                            new_ln += val
                            i = j + 1
                            continue
                new_ln += resolved_ln[i]
                i += 1
            if new_ln == resolved_ln:
                break
            resolved_ln = new_ln

        try:
            parts = shlex.split(resolved_ln, posix=False)
        except ValueError:
            continue
        if not parts:
            continue
        cmd_lower = parts[0].lower()

        if cmd_lower == "if":
            continue

        if cmd_lower == "set":
            remainder = resolved_ln[3:].strip()
            if remainder.startswith('"') and remainder.endswith('"'):
                remainder = remainder[1:-1]
            if "=" in remainder:
                k, v = remainder.split("=", 1)
                k, v = k.strip(), v.strip()
                if v.startswith('"') and v.endswith('"'):
                    v = v[1:-1]
                set_var(k, v)
        elif "winws.exe" in resolved_ln.lower():
            winws_cmd_parts = parts
            break

    if not winws_cmd_parts:
        raise RuntimeError("Не найдена команда winws.exe")

    idx = -1
    for i, p in enumerate(winws_cmd_parts):
        if "winws.exe" in p.lower():
            idx = i
            break
    if idx == -1:
        raise RuntimeError("winws.exe потерялся при парсинге")

    exe_raw = winws_cmd_parts[idx].strip('"')
    raw_args = winws_cmd_parts[idx + 1:]
    exe = exe_raw

    if not os.path.isabs(exe):
        cands = [
            os.path.join(bat_dir, exe),
            os.path.join(bat_dir, "bin", "winws.exe"),
            os.path.join(_app_dir(), "bin", "winws.exe"),
            os.path.join(bat_dir, "winws.exe"),
        ]
        for c in cands:
            if os.path.isfile(c):
                exe = c
                break

    final_args = []
    for arg in raw_args:
        clean = arg.replace('"', '')
        if "=" in clean and any(k in clean for k in ["ipset", "hostlist", "fake", "tls", "quic", "pattern"]):
            key, val = clean.split("=", 1)
            if not val or val.startswith("-"):
                final_args.append(f"{key}={val}")
                continue
            if os.path.isfile(val):
                final_args.append(f"{key}={val}")
                continue
            possible_paths = [
                os.path.join(bat_dir, val),
                os.path.join(bat_dir, "lists", val),
                os.path.join(bat_dir, "bin", val),
                os.path.join(_app_dir(), val),
                os.path.join(_app_dir(), "lists", val),
            ]
            found_path = None
            for p in possible_paths:
                if os.path.isfile(p):
                    found_path = p
                    break
            if found_path:
                final_args.append(f"{key}={found_path}")
            else:
                final_args.append(f"{key}={val}")
        else:
            final_args.append(clean)

    return exe, final_args, bat_dir


# -------------------- Main Window --------------------

class MainWindow(QMainWindow):
    TASK_NAME = "MVZ_Autostart"

    def __init__(self):
        super().__init__()

        # --- ФИКС ДЛЯ ЛОГОТИПА ---
        icon_path = None
        candidates = [
            resource_path("mvz-round.ico"),
            os.path.join(_app_dir(), "mvz-round.ico"),
            os.path.join(os.path.dirname(__file__), "mvz-round.ico")
        ]
        for p in candidates:
            if os.path.isfile(p):
                icon_path = p
                break

        if icon_path:
            self.setWindowIcon(QIcon(icon_path))

        self.setWindowTitle("MVZapret (MVZ)")
        self.resize(1200, 750)

        self.settings = QSettings("MVZ", "MVZapret")
        self.current_theme_name = self.settings.value("theme", "dark")
        self.alt11_bat_path = resolve_alt11_bat()

        self.detached_running = False
        self.session_start_time: Optional[datetime.datetime] = None
        self.winws_pid: Optional[int] = None

        self.winws_process_obj = None

        self.crash_check_timer = QTimer(self)
        self.crash_check_timer.setSingleShot(True)
        self.crash_check_timer.setInterval(2500)
        self.crash_check_timer.timeout.connect(self._check_startup_status)

        self.monitor_timer = QTimer(self)
        self.monitor_timer.setInterval(3000)
        self.monitor_timer.timeout.connect(self.poll_running)

        self.uptime_timer = QTimer(self)
        self.uptime_timer.setInterval(1000)
        self.uptime_timer.timeout.connect(self.update_uptime_footer)

        self._really_quit = False
        self.net_optimized_once = False
        self._hires_timer_enabled = False
        self.uptime_footer: Optional[QLabel] = None
        self.priority_label: Optional[QLabel] = None

        root = QHBoxLayout()
        central = QWidget()
        central.setLayout(root)
        self.setCentralWidget(central)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(0, 16, 0, 16)
        side.setSpacing(0)

        logo_container = QWidget()
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 16, 0, 32)
        logo_layout.setSpacing(0)

        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignCenter)

        # --- ФИКС ДЛЯ ЛОГОТИПА В UI ---
        logo_file_name = "mvz_logo.png"
        logo_candidates = [
            resource_path(logo_file_name),
            os.path.join(_app_dir(), logo_file_name),
            os.path.join(os.path.dirname(__file__), "..", logo_file_name)
        ]

        pix = None
        for p in logo_candidates:
            if os.path.isfile(p):
                temp_pix = QPixmap(p)
                if not temp_pix.isNull():
                    pix = temp_pix
                    break

        if pix:
            icon_lbl.setPixmap(pix.scaled(200, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            icon_lbl.setText("MVZ")
            icon_lbl.setStyleSheet("font-size:28px;color:#60A5FA;font-weight:700;")

        logo_layout.addWidget(icon_lbl, 0, Qt.AlignHCenter)
        side.addWidget(logo_container)

        self.btn_home = QPushButton("Главная")
        self.btn_home.setObjectName("Nav")
        self.btn_home.setCheckable(True)
        self.btn_home.setChecked(True)

        self.btn_settings = QPushButton("Настройки")
        self.btn_settings.setObjectName("Nav")
        self.btn_settings.setCheckable(True)

        self.btn_logs = QPushButton("Журнал")
        self.btn_logs.setObjectName("Nav")
        self.btn_logs.setCheckable(True)

        self.btn_info = QPushButton("Инфо")
        self.btn_info.setObjectName("Nav")
        self.btn_info.setCheckable(True)

        for b in (self.btn_home, self.btn_settings, self.btn_logs, self.btn_info):
            b.setCursor(Qt.PointingHandCursor)
            b.setMinimumHeight(48)
            side.addWidget(b)

        side.addStretch(1)

        self.pages = QStackedWidget()
        page_home = self._create_home_page()
        page_settings = self._create_settings_page()
        page_log = self._create_log_page()
        page_info = self._create_info_page()
        for w in (page_home, page_settings, page_log, page_info):
            self.pages.addWidget(w)

        root.addWidget(sidebar, 0)
        root.addWidget(self.pages, 1)

        self.btn_home.clicked.connect(lambda: self.switch_tab(0))
        self.btn_settings.clicked.connect(lambda: self.switch_tab(1))
        self.btn_logs.clicked.connect(lambda: self.switch_tab(2))
        self.btn_info.clicked.connect(lambda: self.switch_tab(3))

        self.run_btn.clicked.connect(self.run_alt11_internal)
        self.stop_btn.clicked.connect(self.stop_winws)
        self.optimize_btn.clicked.connect(self.optimize_network)

        self.apply_theme_by_name(self.current_theme_name)
        self.update_buttons(running=False)

        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.windowIcon())
        self.tray.activated.connect(self.on_tray_activated)

        tray_menu = QMenu(self)
        act_show = QAction("Открыть MVZ", self, triggered=self.show_main_from_tray)
        act_run = QAction("Запустить", self, triggered=self.run_alt11_internal)
        act_stop = QAction("Остановить", self, triggered=self.stop_winws)

        self.act_autostart = QAction("Автозапуск при входе", self, checkable=True)
        self.act_autostart.setChecked(self.is_autostart_enabled())
        self.act_autostart.toggled.connect(self.set_autostart_enabled)

        act_exit = QAction("Выход", self, triggered=self.exit_from_tray)

        tray_menu.addAction(act_show)
        tray_menu.addSeparator()
        tray_menu.addAction(act_run)
        tray_menu.addAction(act_stop)
        tray_menu.addSeparator()
        tray_menu.addAction(self.act_autostart)
        tray_menu.addSeparator()
        tray_menu.addAction(act_exit)

        self.tray.setContextMenu(tray_menu)
        self.tray.show()

        self.update_status_indicator(False)
        self.uptime_timer.start()

        self.discord_rpc = None
        self.discord_update_timer = QTimer(self)
        self.discord_update_timer.setInterval(30000)
        self.discord_update_timer.timeout.connect(self._update_discord_status)

        if PYPRESENCE_AVAILABLE and DiscordRPC:
            try:
                self.discord_rpc = DiscordRPC()
            except Exception:
                self.discord_rpc = None
        else:
            self.append_log("[Discord RPC] pypresence не установлен")

        if PYPRESENCE_AVAILABLE and DiscordRPC and hasattr(self, "discord_rpc_cb"):
            self.discord_rpc_cb.setChecked(True)
            self.on_toggle_discord_rpc(True)

        # --- AUTO UPDATE TIMER ---
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(6 * 60 * 60 * 1000)  # 6 часов
        self.update_timer.timeout.connect(self.check_updates_silent)
        self.update_timer.start()
        QTimer.singleShot(5_000, self.check_updates_silent)

        # =============================================================
        # === ФИКС: АВТОЗАПУСК ОБХОДА (ПЕРЕНЕСЕНО В КОНЕЦ INIT) ===
        # =============================================================

        # 1. Загружаем настройки
        is_win_autostart = self.is_autostart_enabled()
        auto_run_bypass = self.settings.value("auto_run_bypass", False, type=bool)

        # 2. Настраиваем чекбокс и привязываем сохранение
        if hasattr(self, "auto_run_cb"):
            self.auto_run_cb.blockSignals(True)  # Временно блочим, чтобы не вызвать триггер
            self.auto_run_cb.setChecked(auto_run_bypass)
            self.auto_run_cb.setEnabled(is_win_autostart)
            self.auto_run_cb.blockSignals(False)

            # При клике сохраняем настройку в реестр
            self.auto_run_cb.toggled.connect(lambda checked: self.settings.setValue("auto_run_bypass", checked))

        # 3. Если включено — запускаем
        if is_win_autostart and auto_run_bypass:
            self.append_log("[Autostart] Запуск обхода через 1 сек...")
            QTimer.singleShot(1000, self.run_alt11_internal)

    # ---------- UPDATE LOGIC ----------
    def _version_tuple(self, v: str):
        v = v.strip().split()[0]
        v = v.lstrip("v")
        parts = v.split(".")
        out = []
        for p in parts:
            try:
                out.append(int(p))
            except ValueError:
                out.append(0)
        while len(out) < 3:
            out.append(0)
        return tuple(out[:3])

    def check_updates_silent(self):
        try:
            req = urllib.request.Request(UPDATE_CHECK_URL, headers={"User-Agent": "MVZ-Updater"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode("utf-8", errors="replace"))
            tag = data.get("tag_name", "").strip()
            if not tag:
                return

            if self._version_tuple(tag) <= self._version_tuple(APP_VERSION):
                return

            assets = data.get("assets", [])
            dl_url = None
            for a in assets:
                if a.get("name") == UPDATE_ASSET_NAME:
                    dl_url = a.get("browser_download_url")
                    break

            if not dl_url:
                return

            res = QMessageBox.question(
                self,
                "Обновление MVZ",
                f"Вышла новая версия: {tag}\n\nСкачать и обновить?",
                QMessageBox.Yes | QMessageBox.No
            )
            if res == QMessageBox.Yes:
                self._download_and_update(dl_url)

        except urllib.error.HTTPError as e:
            if e.code == 404:
                pass  # Молчим если нет релиза
            else:
                self.append_log(f"[Update] Ошибка HTTP: {e.code}")
        except Exception as e:
            self.append_log(f"[Update] Ошибка проверки: {e}")

    def _download_and_update(self, url: str):
        self.append_log(f"[Update] Скачивание: {url}")
        tmp_dir = tempfile.gettempdir()
        filename = url.split("/")[-1]
        new_exe = os.path.join(tmp_dir, filename)

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MVZ-Updater"})
            with urllib.request.urlopen(req, timeout=60) as r, open(new_exe, "wb") as f:
                while True:
                    chunk = r.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
        except Exception as e:
            QMessageBox.critical(self, "MVZ", f"Ошибка скачивания:\n{e}")
            return

        if getattr(sys, "frozen", False):
            current_exe = sys.executable
        else:
            return

        updater = os.path.join(tmp_dir, "MVZ_updater.bat")
        bat = f"""@echo off
chcp 65001 >nul
set "CUR={current_exe}"
set "NEW={new_exe}"
:wait
timeout /t 1 /nobreak >nul
tasklist /fi "imagename eq {os.path.basename(current_exe)}" | find /i "{os.path.basename(current_exe)}" >nul
if not errorlevel 1 goto wait
copy /y "%NEW%" "%CUR%" >nul
start "" "%CUR%"
del "%NEW%" >nul
del "%~f0" >nul
"""
        with open(updater, "w", encoding="utf-8", errors="ignore") as f:
            f.write(bat)

        subprocess.Popen(["cmd", "/c", updater], creationflags=CREATE_NO_WINDOW)
        self._really_quit = True
        QApplication.quit()

    # ---------- Темы ----------
    def apply_theme_by_name(self, name: str):
        self.current_theme_name = name
        if name == "light":
            self.setStyleSheet(LIGHT_STYLESHEET)
        elif name == "purple":
            self.setStyleSheet(PURPLE_STYLESHEET)
        else:
            self.setStyleSheet(DARK_STYLESHEET)

    def on_theme_changed(self, index: int):
        name = "dark"
        if index == 1:
            name = "light"
        elif index == 2:
            name = "purple"
        self.apply_theme_by_name(name)
        self.settings.setValue("theme", name)

    # ---------- UI PAGES ----------
    def _create_home_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(12)

        title_row = QHBoxLayout()
        title = QLabel("MVZapret")
        title.setStyleSheet("font-size:24px;font-weight:700;")
        title_row.addWidget(title)
        title_row.addStretch()

        self.current_profile_label = QLabel(f"ALT11: {os.path.basename(self.alt11_bat_path)}")
        self.current_profile_label.setStyleSheet("font-size:12px;color:#94A3B8;")
        title_row.addWidget(self.current_profile_label)
        lay.addLayout(title_row)

        status_row = QHBoxLayout()
        status_row.setSpacing(12)

        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(20, 20)
        self.status_indicator.setStyleSheet("background:#DC2626;border-radius:10px;border:2px solid #450A0A;")

        self.status_label = QLabel("Остановлен")
        self.status_label.setStyleSheet("font-size:16px;font-weight:600;")

        status_row.addWidget(self.status_indicator)
        status_row.addWidget(self.status_label)
        status_row.addStretch()

        btns = QHBoxLayout()
        btns.setSpacing(16)

        self.run_btn = QPushButton("Запустить")
        self.run_btn.setObjectName("Action")
        self.run_btn.setCursor(Qt.PointingHandCursor)

        self.stop_btn = QPushButton("Остановить")
        self.stop_btn.setObjectName("Action")
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.setStyleSheet(
            "QPushButton{background:#EF4444;color:#FFF;border:none;border-radius:14px;"
            "padding:10px 22px;font-size:14px;font-weight:600;}"
            "QPushButton:hover{background:#DC2626;}"
            "QPushButton:disabled{background:#1F2933;color:#64748B;}"
        )

        btns.addWidget(self.run_btn)
        btns.addWidget(self.stop_btn)
        btns.addStretch()

        self.optimize_btn = QPushButton("Оптимизация пинга")
        self.optimize_btn.setObjectName("Action")
        self.optimize_btn.setCursor(Qt.PointingHandCursor)

        self.priority_label = QLabel("")
        self.priority_label.setStyleSheet("font-size:12px;")

        footer = QHBoxLayout()
        footer.addStretch()
        self.uptime_footer = QLabel("Время работы: —")
        self.uptime_footer.setStyleSheet("font-size:14px;font-weight:600;")
        footer.addWidget(self.uptime_footer)
        footer.addStretch()

        lay.addLayout(status_row)
        lay.addLayout(btns)
        lay.addWidget(self.optimize_btn)
        lay.addWidget(self.priority_label)
        lay.addStretch()
        lay.addLayout(footer)
        return page

    def _create_settings_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(10)

        title = QLabel("Настройки")
        title.setStyleSheet("font-size:24px;font-weight:700;")
        lay.addWidget(title)

        self.autostart_cb = QCheckBox("Автозапуск при входе в Windows (MVZ)")
        self.autostart_cb.setChecked(self.is_autostart_enabled())
        self.autostart_cb.toggled.connect(self.on_toggle_autostart)
        lay.addWidget(self.autostart_cb)

        self.auto_run_cb = QCheckBox("Запускать обход автоматически при старте MVZ")
        # ВАЖНО: не ставим setChecked(False) здесь, чтобы не сбить настройки.
        # Инициализация происходит в __init__
        lay.addWidget(self.auto_run_cb)

        self.discord_rpc_cb = QCheckBox("Discord Rich Presence")
        self.discord_rpc_cb.setChecked(False)
        self.discord_rpc_cb.setEnabled(PYPRESENCE_AVAILABLE and DiscordRPC is not None)
        self.discord_rpc_cb.toggled.connect(self.on_toggle_discord_rpc)
        lay.addWidget(self.discord_rpc_cb)

        theme_row = QHBoxLayout()
        theme_lbl = QLabel("Тема оформления:")
        theme_row.addWidget(theme_lbl)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Тёмная", "Светлая", "Фиолетовая"])
        name_to_index = {"dark": 0, "light": 1, "purple": 2}
        idx_theme = name_to_index.get(self.current_theme_name, 0)
        self.theme_combo.setCurrentIndex(idx_theme)
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        theme_row.addWidget(self.theme_combo, 1)

        lay.addLayout(theme_row)
        lay.addStretch()
        return page

    def _create_log_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        title = QLabel("Журнал событий")
        title.setStyleSheet("font-size:24px;font-weight:700;")

        self.log = QTextEdit()
        self.log.setReadOnly(True)

        lay.addWidget(title)
        lay.addWidget(self.log, 1)
        return page

    def _create_info_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(20)

        title = QLabel("Информация")
        title.setStyleSheet("font-size:24px;font-weight:700;")
        lay.addWidget(title)

        def link_card(title_text, url):
            card = QFrame()
            card.setStyleSheet(
                "QFrame{background:rgba(76,29,149,0.6);border:2px solid #7C3AED;border-radius:16px;padding:20px;}"
                "QFrame:hover{border-color:#A855F7;background:rgba(129,140,248,0.15);}"
            )
            l = QVBoxLayout(card)
            l.setSpacing(8)
            t = QLabel(title_text)
            t.setStyleSheet("color:#F9FAFB;font-size:18px;font-weight:700;")
            lk = QLabel(f'<a href="{url}" style="color:#C4B5FD;text-decoration:none;">{url}</a>')
            lk.setOpenExternalLinks(True)
            lk.setTextInteractionFlags(Qt.TextBrowserInteraction)
            l.addWidget(t)
            l.addWidget(lk)
            return card

        lay.addWidget(link_card("Discord", "https://discord.gg/RtQ8fYnP8p"))
        lay.addWidget(link_card("Telegram", "https://t.me/motyait2"))
        lay.addStretch()

        ver_row = QHBoxLayout()
        ver_row.addStretch()
        ver = QLabel(f"Version {APP_VERSION}")
        ver.setStyleSheet("color:#64748B;font-size:12px;")
        ver_row.addWidget(ver)
        ver_row.addStretch()

        lay.addLayout(ver_row)
        return page

    def switch_tab(self, idx: int):
        self.pages.setCurrentIndex(idx)
        self.btn_home.setChecked(idx == 0)
        self.btn_settings.setChecked(idx == 1)
        self.btn_logs.setChecked(idx == 2)
        self.btn_info.setChecked(idx == 3)

    def update_buttons(self, running: bool):
        self.run_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.optimize_btn.setEnabled(running)

    def update_status_indicator(self, running: bool):
        if running:
            self.status_indicator.setStyleSheet("background:#10B981;border-radius:10px;border:2px solid #064E3B;")
            self.status_label.setText("Запущен")
            self.tray.setToolTip("MVZ - Запущен")
        else:
            self.status_indicator.setStyleSheet("background:#DC2626;border-radius:10px;border:2px solid #450A0A;")
            self.status_label.setText("Остановлен")
            self.tray.setToolTip("MVZ - Остановлен")

    def append_log(self, s: str):
        if hasattr(self, "log") and self.log is not None:
            if self.log.document().blockCount() > 1000:
                cursor = self.log.textCursor()
                cursor.movePosition(cursor.Start)
                cursor.movePosition(cursor.Down, cursor.KeepAnchor, 100)
                cursor.removeSelectedText()
            self.log.append(s)

    def _create_hidden_proc(self) -> QProcess:
        p = QProcess(self)
        try:
            p.setCreateProcessArgumentsModifier(lambda a: a.setCreationFlags(a.creationFlags() | CREATE_NO_WINDOW))
        except Exception:
            pass
        return p

    def _kill_by_name(self, name: str):
        killer = self._create_hidden_proc()
        killer.setProcessChannelMode(QProcess.MergedChannels)
        killer.start("taskkill", ["/IM", name, "/F", "/T"])
        killer.waitForFinished(4000)

    def _kill_by_pid(self, pid: int):
        killer = self._create_hidden_proc()
        killer.setProcessChannelMode(QProcess.MergedChannels)
        killer.start("taskkill", ["/PID", str(pid), "/F", "/T"])
        killer.waitForFinished(4000)

    def kill_running_instances(self, note=True):
        if self.winws_pid:
            try:
                self._kill_by_pid(self.winws_pid)
            except Exception:
                pass
        try:
            self._kill_by_name("winws.exe")
        except Exception:
            pass
        self.winws_pid = None
        self.winws_process_obj = None
        if note:
            self.append_log("[MVZ] Завершены процессы winws.exe")

    def _is_running_now(self) -> bool:
        if self.winws_pid and psutil is not None:
            return _pid_alive(self.winws_pid)

        if self.winws_process_obj is not None:
            if self.winws_process_obj.poll() is None:
                return True

        checker = self._create_hidden_proc()
        checker.setProcessChannelMode(QProcess.MergedChannels)
        checker.start("tasklist", ["/FI", "IMAGENAME eq winws.exe"])
        checker.waitForFinished(2000)
        out = bytes(checker.readAllStandardOutput()).decode("utf-8", errors="replace")
        return "winws.exe" in out

    def poll_running(self):
        running = self._is_running_now()
        if running != self.detached_running:
            self.detached_running = running
            self.update_buttons(running)
            self.update_status_indicator(running)
            self.append_log("[MVZ] " + ("Запущен" if running else "Остановлен"))
            self._enable_hires_timer(running)
            if not running:
                self.monitor_timer.stop()

    def update_uptime_footer(self):
        if not hasattr(self, "uptime_footer") or self.uptime_footer is None:
            return
        if psutil is None:
            self.uptime_footer.setText("Время работы: —")
            return

        if self.winws_pid and _pid_alive(self.winws_pid):
            try:
                p = psutil.Process(self.winws_pid)
                ct = datetime.datetime.fromtimestamp(p.create_time())
                up = datetime.datetime.now() - ct
                self.uptime_footer.setText(f"Время работы: {str(up).split('.')[0]}")
                return
            except Exception:
                pass

        p = get_winws_process()
        if not p:
            self.uptime_footer.setText("Время работы: —")
            return
        try:
            ct = datetime.datetime.fromtimestamp(p.create_time())
            up = datetime.datetime.now() - ct
            self.uptime_footer.setText(f"Время работы: {str(up).split('.')[0]}")
        except Exception:
            self.uptime_footer.setText("Время работы: —")

    def run_alt11_internal(self):
        # FIX: в noconsole-сборке создаём скрытую консоль, чтобы winws не ломался
        ensure_hidden_console()

        batpath = resolve_alt11_bat()
        if not os.path.isfile(batpath):
            QMessageBox.critical(self, "MVZ", f"Не найден ALT11 .bat:\n{batpath}")
            return
        try:
            exe, args, workdir = _parse_bat_variables_and_command(batpath)
            if not os.path.isfile(exe):
                raise FileNotFoundError(exe)
        except Exception as e:
            QMessageBox.critical(self, "MVZ", f"Ошибка парсинга батника:\n{e}\n\nПроверьте файл.")
            return

        self.kill_running_instances(note=False)
        self.append_log(f"[MVZ] Старт Internal: {exe}")
        self.append_log(f"[DEBUG] Аргументы: {' '.join(args)}")

        for arg in args:
            if "=" in arg:
                key, val = arg.split("=", 1)
                if any(k in key for k in ["ipset", "hostlist", "fake", "tls", "quic", "pattern"]):
                    if (".txt" in val or ".bin" in val) and not os.path.isfile(val):
                        self.append_log(f"[WARNING] Файл не найден: {val}")

        try:
            # Оставлено как у тебя: PIPE нужен для чтения причин падения
            proc = subprocess.Popen(
                [exe] + args,
                cwd=workdir,
                creationflags=CREATE_NO_WINDOW,
                stderr=subprocess.PIPE
            )
        except Exception as e:
            self.append_log(f"[MVZ] Ошибка запуска: {e}")
            self.update_buttons(False)
            self.update_status_indicator(False)
            return

        self.winws_pid = proc.pid
        self.winws_process_obj = proc  # Сохраняем объект для диагностики
        self.detached_running = True
        self.session_start_time = datetime.datetime.now()
        self.update_buttons(True)
        self.update_status_indicator(True)
        self.monitor_timer.start()
        self.crash_check_timer.start()
        if self.tray.supportsMessages():
            self.tray.showMessage("MVZ", "ALT11 Запущен", QSystemTrayIcon.Information, 3000)
        self._optimize_network_silent()
        self._boost_winws_priority()
        self._enable_hires_timer(True)

    def _check_startup_status(self):
        if self.winws_process_obj is not None:
            if self.winws_process_obj.poll() is not None:
                err_output = ""
                try:
                    if self.winws_process_obj.stderr:
                        err_output = self.winws_process_obj.stderr.read().decode("utf-8", errors="replace").strip()
                except Exception:
                    err_output = ""

                self.append_log("[MVZ] ПАДЕНИЕ ПРОЦЕССА! Код возврата: " + str(self.winws_process_obj.returncode))
                if err_output:
                    self.append_log("[MVZ ОШИБКА WINWS]: " + err_output)
                    QMessageBox.critical(self, "Ошибка запуска winws", f"Программа упала с ошибкой:\n\n{err_output}")
                else:
                    self.append_log("[MVZ] Процесс упал молча. Возможно проблема в правах или путях.")

                self.update_buttons(False)
                self.update_status_indicator(False)
                return

        if not self._is_running_now():
            self.append_log("[MVZ] Внимание: процесс завершился сразу после старта!")
            self.update_buttons(False)
            self.update_status_indicator(False)

    def stop_winws(self):
        self.kill_running_instances(note=False)
        stopped = not self._is_running_now()
        self.detached_running = False
        self.update_buttons(False)
        self.update_status_indicator(False)
        self.crash_check_timer.stop()
        self.append_log("[MVZ] Остановлен" + ("" if stopped else " (процессы остались)"))
        self._enable_hires_timer(False)
        if self.tray.supportsMessages():
            self.tray.showMessage("MVZ", "Остановлен", QSystemTrayIcon.Warning, 3000)

    def optimize_network(self):
        if not is_admin():
            QMessageBox.warning(self, "MVZ", "Нужны права администратора.")
            return
        self._apply_netsh_settings(verbose=True)
        if self.priority_label is not None:
            self.priority_label.setText("Приоритет повышен")

    def _optimize_network_silent(self):
        if self.net_optimized_once:
            return
        self.net_optimized_once = True
        if is_admin():
            self._apply_netsh_settings(verbose=False)

    def _apply_netsh_settings(self, verbose: bool):
        cmds = [
            ("netsh", ["int", "tcp", "set", "global", "ecncapability=disabled"]),
            ("netsh", ["int", "tcp", "set", "global", "autotuninglevel=normal"]),
            ("netsh", ["int", "tcp", "set", "global", "rss=enabled"]),
            ("netsh", ["int", "tcp", "set", "global", "rsc=enabled"]),
            ("netsh", ["int", "tcp", "set", "supplemental", "template=internet", "congestionprovider=cubic"]),
            ("ipconfig", ["/flushdns"]),
        ]
        ok_all = True
        for prog, args in cmds:
            pr = self._create_hidden_proc()
            pr.setProcessChannelMode(QProcess.MergedChannels)
            pr.start(prog, args)
            pr.waitForFinished(7000)
            if verbose:
                out = bytes(pr.readAllStandardOutput()).decode("utf-8", errors="replace").strip()
                if out:
                    self.append_log(f"[Оптимизация] {prog} -> {out}")
            if pr.exitCode() != 0:
                ok_all = False
        if verbose:
            self.append_log("[Оптимизация] Готово." + ("" if ok_all else " (с предупреждениями)"))

    def _boost_winws_priority(self):
        if psutil is None:
            return
        try:
            if self.winws_pid and _pid_alive(self.winws_pid):
                psutil.Process(self.winws_pid).nice(psutil.HIGH_PRIORITY_CLASS)
                self.append_log("[Оптимизация] Приоритет winws.exe: HIGH")
                return
            p = get_winws_process()
            if p:
                p.nice(psutil.HIGH_PRIORITY_CLASS)
                self.append_log("[Оптимизация] Приоритет winws.exe: HIGH")
        except Exception:
            pass

    def _enable_hires_timer(self, enable: bool):
        try:
            winmm = ctypes.WinDLL("winmm")
            if enable and not self._hires_timer_enabled:
                winmm.timeBeginPeriod(1)
                self._hires_timer_enabled = True
                self.append_log("[Оптимизация] Таймеры: 1 ms")
            if not enable and self._hires_timer_enabled:
                winmm.timeEndPeriod(1)
                self._hires_timer_enabled = False
                self.append_log("[Оптимизация] Таймеры: по умолчанию")
        except Exception:
            pass

    def _update_discord_status(self):
        try:
            if self.discord_rpc and getattr(self.discord_rpc, "connected", False):
                if self.detached_running:
                    self.discord_rpc.update_running("ALT11", self.session_start_time)
                else:
                    self.discord_rpc.update_idle()
        except Exception:
            pass

    def on_toggle_discord_rpc(self, enabled: bool):
        if not (PYPRESENCE_AVAILABLE and DiscordRPC):
            self.append_log("[Discord RPC] pypresence не установлен")
            if hasattr(self, "discord_rpc_cb"):
                self.discord_rpc_cb.setChecked(False)
            return
        if enabled:
            if not self.discord_rpc:
                try:
                    self.discord_rpc = DiscordRPC()
                except Exception:
                    self.discord_rpc = None
            if self.discord_rpc and self.discord_rpc.connect():
                self._update_discord_status()
                self.discord_update_timer.start()
        else:
            try:
                if self.discord_rpc:
                    self.discord_rpc.disconnect()
            except Exception:
                pass
            self.discord_update_timer.stop()
            self.append_log("[Discord RPC] Отключено")

    def closeEvent(self, event):
        if not self._really_quit and self.tray and self.tray.isVisible():
            self.hide()
            event.ignore()
        else:
            try:
                if self.discord_update_timer:
                    self.discord_update_timer.stop()
                if self.discord_rpc:
                    self.discord_rpc.disconnect()
                self._enable_hires_timer(False)
            except Exception:
                pass
            event.accept()

    def show_main_from_tray(self):
        self.showNormal()
        self.activateWindow()
        try:
            self.raise_()
        except Exception:
            pass

    def on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_main_from_tray()

    def exit_from_tray(self):
        self._really_quit = True
        try:
            if self.discord_update_timer:
                self.discord_update_timer.stop()
            if self.discord_rpc:
                self.discord_rpc.disconnect()
            self._enable_hires_timer(False)
        except Exception:
            pass
        QApplication.quit()

    def _autostart_command_and_cwd(self):
        if getattr(sys, "frozen", False):
            exe = sys.executable
            # ВАЖНО: возвращаем путь к EXE и рабочую папку
            return f'"{exe}"', os.path.dirname(exe)

        # Для разработки
        py_dir = os.path.dirname(sys.executable)
        pythonw = os.path.join(py_dir, "pythonw.exe")
        script = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
        if os.path.isfile(pythonw):
            cmd = f'"{pythonw}" "{script}"'
        else:
            cmd = f'"{sys.executable}" "{script}"'
        return cmd, os.path.dirname(script)

    def is_autostart_enabled(self) -> bool:
        p = self._create_hidden_proc()
        p.start("schtasks", ["/Query", "/TN", self.TASK_NAME])
        ok = p.waitForFinished(4000)
        return ok and p.exitCode() == 0

    def _create_or_update_task(self) -> bool:
        cmd, _cwd = self._autostart_command_and_cwd()
        args = [
            "/Create", "/SC", "ONLOGON", "/TN", self.TASK_NAME,
            "/TR", cmd, "/RL", "HIGHEST", "/F", "/DELAY", "0000:10",
        ]
        p = self._create_hidden_proc()
        p.start("schtasks", args)
        p.waitForFinished(8000)
        return p.exitCode() == 0

    def _delete_task(self) -> bool:
        p = self._create_hidden_proc()
        p.start("schtasks", ["/Delete", "/TN", self.TASK_NAME, "/F"])
        p.waitForFinished(6000)
        return True

    def set_autostart_enabled(self, enable: bool):
        ok = self._create_or_update_task() if enable else self._delete_task()
        if not ok:
            self.append_log("[MVZ] Не удалось изменить автозапуск")
        st = self.is_autostart_enabled()
        if hasattr(self, "autostart_cb"):
            self.autostart_cb.blockSignals(True)
            self.autostart_cb.setChecked(st)
            self.autostart_cb.blockSignals(False)
        if hasattr(self, "act_autostart"):
            self.act_autostart.blockSignals(True)
            self.act_autostart.setChecked(st)
            self.act_autostart.blockSignals(False)
        if hasattr(self, "auto_run_cb"):
            self.auto_run_cb.setEnabled(st)
            if not st:
                # Если автозапуск выключен, то и "запускать батник" не имеет смысла при старте
                # Но саму галочку можно не снимать, просто она недоступна
                pass

    def on_toggle_autostart(self, checked: bool):
        self.set_autostart_enabled(checked)
        self.append_log("[MVZ] Автозапуск " + ("включён" if checked else "выключен"))
