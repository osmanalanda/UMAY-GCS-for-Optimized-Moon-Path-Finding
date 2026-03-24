"""
LUNAR ROVER NAVIGATION DASHBOARD  v3.0
=======================================
Kurulum: pip install PySide6
Çalıştır: python main.py

İçerik:
- Gerçek A* algoritması + Occupancy Grid
- Simscape/Simulink UDP/TCP bağlantısı
- Araç telemetrisi paneli
- Navigasyon komut logu
- Canlı harita + rota görselleştirme
"""

import sys, socket, json, math, threading, random, heapq
from datetime import datetime
from collections import deque

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QTextEdit, QFrame, QSplitter,
    QGroupBox, QLineEdit, QSpinBox, QComboBox, QProgressBar,
    QTabWidget, QStatusBar,
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QRectF, QPointF
from PySide6.QtGui import (
    QFont, QColor, QPainter, QPen, QBrush, QPainterPath, QRadialGradient,
)

# ─────────────────────────────────────────────────────────────────────────────
#  RENK PALETİ
# ─────────────────────────────────────────────────────────────────────────────
C = {
    # ── Arka planlar — koyu uzay paleti ──────────────
    "bg":        "#0D1117",   # ana sayfa — neredeyse siyah
    "panel":     "#161C26",   # kart/panel — koyu lacivert-gri
    "panel2":    "#1C2535",   # biraz daha açık panel
    "header":    "#0A0F1A",   # başlık — en koyu
    "input":     "#1A2234",   # input alanı

    # ── Vurgu renkleri — soft, parlak değil ──────────
    "blue":      "#4A9EFF",   # ana mavi — soft
    "blue_dk":   "#1D4ED8",   # koyu mavi (hover)
    "blue_lt":   "#1A2D4A",   # mavi arka plan (card)
    "cyan":      "#22D3EE",   # cyan vurgu
    "cyan_dk":   "#0E7490",   # koyu cyan

    "green":     "#34D399",   # yeşil — soft mint
    "green_dk":  "#059669",   # koyu yeşil
    "green_lt":  "#0D2620",   # yeşil arka plan

    "amber":     "#FBBF24",   # amber — soft sarı
    "amber_dk":  "#D97706",   # koyu amber
    "amber_lt":  "#2D1F08",   # amber arka plan

    "red":       "#F87171",   # kırmızı — soft
    "red_dk":    "#DC2626",   # koyu kırmızı
    "red_lt":    "#2D1010",   # kırmızı arka plan

    # ── Metin renkleri — yüksek kontrast ─────────────
    "text":      "#E2E8F0",   # birincil metin — açık gri-beyaz
    "text2":     "#94A3B8",   # ikincil metin — orta gri
    "text3":     "#475569",   # soluk metin — koyu gri

    # ── Kenarlıklar ───────────────────────────────────
    "border":    "#1E2D42",   # normal kenarlık
    "border2":   "#2A3F5F",   # biraz daha belirgin
    "border_hi": "#4A9EFF",   # vurgulu kenarlık (aktif)

    # ── Log ekranı renkleri ───────────────────────────
    "log_bg":    "#0A0F1A",   # log arka plan
    "log_bg2":   "#080D15",   # nav log arka plan
    "lc_text":   "#CBD5E1",   # log metin
    "lc_dim":    "#334155",   # soluk log metin
    "lc_cyan":   "#22D3EE",   # cyan komut
    "lc_green":  "#34D399",   # yeşil komut
    "lc_amber":  "#FBBF24",   # amber uyarı
    "lc_red":    "#F87171",   # kırmızı hata
}

SS = f"""
QMainWindow, QWidget {{
    background: {C['bg']};
    color: {C['text']};
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}}

/* ── Paneller ─────────────────────────────────── */
QFrame#Card {{
    background: {C['panel']};
    border: 1px solid {C['border']};
    border-radius: 8px;
}}
QFrame#CardBlue {{
    background: {C['blue_lt']};
    border: 1px solid {C['blue_dk']};
    border-radius: 8px;
}}
QFrame#CardGreen {{
    background: {C['green_lt']};
    border: 1px solid {C['green_dk']};
    border-radius: 8px;
}}
QFrame#CardAmber {{
    background: {C['amber_lt']};
    border: 1px solid {C['amber_dk']};
    border-radius: 8px;
}}
QFrame#CardRed {{
    background: {C['red_lt']};
    border: 1px solid {C['red_dk']};
    border-radius: 8px;
}}
QFrame#Header {{
    background: {C['header']};
    border-bottom: 1px solid {C['border']};
}}
QFrame#ConnPanel {{
    background: {C['panel2']};
    border: 1px solid {C['border_hi']};
    border-radius: 8px;
}}

/* ── GroupBox ─────────────────────────────────── */
QGroupBox {{
    background: {C['panel']};
    border: 1px solid {C['border']};
    border-radius: 8px;
    margin-top: 14px;
    padding: 10px 8px 8px 8px;
    font-size: 11px;
    font-weight: bold;
    color: {C['text3']};
    letter-spacing: 1px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    background: {C['panel']};
    color: {C['cyan']};
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 2px;
}}

/* ── Telemetri değer etiketleri ───────────────── */
QLabel#LBigG {{ font-size:22px; font-weight:bold; color:{C['green']};  font-family:'Consolas',monospace; }}
QLabel#LBigA {{ font-size:22px; font-weight:bold; color:{C['amber']};  font-family:'Consolas',monospace; }}
QLabel#LBigR {{ font-size:22px; font-weight:bold; color:{C['red']};    font-family:'Consolas',monospace; }}
QLabel#LBig  {{ font-size:22px; font-weight:bold; color:{C['text']};   font-family:'Consolas',monospace; }}
QLabel#LSmall {{
    font-size: 10px; font-weight: bold;
    color: {C['text3']}; letter-spacing: 2px;
}}

/* ── Butonlar ─────────────────────────────────── */
QPushButton {{
    background: {C['panel2']}; color: {C['blue']};
    border: 1px solid {C['blue_dk']}; border-radius: 6px;
    padding: 7px 18px; font-size: 12px; font-weight: bold;
}}
QPushButton:hover {{ background: {C['blue_dk']}; color: white; border-color: {C['blue']}; }}
QPushButton#BtnConn {{
    background: {C['green_dk']}; color: white;
    border-color: {C['green_dk']}; padding: 9px 26px; font-size: 13px;
}}
QPushButton#BtnConn:hover {{ background: #047857; }}
QPushButton#BtnDisc {{
    background: {C['red_dk']}; color: white;
    border-color: {C['red_dk']}; padding: 9px 26px; font-size: 13px;
}}
QPushButton#BtnDisc:hover {{ background: #B91C1C; }}
QPushButton#BtnClr {{
    background: {C['panel2']}; color: {C['text2']};
    border-color: {C['border2']}; padding: 4px 12px; font-size: 11px;
}}

/* ── Input alanları ───────────────────────────── */
QLineEdit, QSpinBox, QComboBox {{
    background: {C['input']}; color: {C['text']};
    border: 1px solid {C['border2']}; border-radius: 6px;
    padding: 6px 10px; font-size: 13px;
}}
QLineEdit:focus, QSpinBox:focus {{
    border-color: {C['blue']}; background: {C['panel2']};
}}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{
    background: {C['panel2']}; color: {C['text']};
    border: 1px solid {C['border2']}; selection-background-color: {C['blue_dk']};
}}

/* ── Progress bar ─────────────────────────────── */
QProgressBar {{
    background: {C['input']}; border: 1px solid {C['border']};
    border-radius: 4px; font-size: 1px;
}}
QProgressBar::chunk {{ background: {C['green']}; border-radius: 3px; }}
QProgressBar#pbA::chunk {{ background: {C['amber']}; }}
QProgressBar#pbR::chunk {{ background: {C['red']};   }}

/* ── Log ekranları ────────────────────────────── */
QTextEdit#NavLog {{
    background: {C['log_bg2']}; color: {C['lc_text']}; border: none;
    font-family: 'Consolas','Courier New',monospace; font-size: 14px;
    padding: 10px 12px;
}}
QTextEdit#TelLog {{
    background: {C['log_bg']}; color: {C['lc_text']}; border: none;
    font-family: 'Consolas','Courier New',monospace; font-size: 12px;
    padding: 8px 10px;
}}

/* ── Tab widget ───────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {C['border']};
    background: {C['panel']};
    border-radius: 0 0 8px 8px;
}}
QTabBar::tab {{
    background: {C['bg']}; color: {C['text3']};
    border: 1px solid {C['border']}; border-bottom: none;
    padding: 8px 22px; font-size: 12px; font-weight: bold;
    border-radius: 6px 6px 0 0; margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {C['panel']}; color: {C['cyan']};
    border-color: {C['cyan_dk']};
}}
QTabBar::tab:hover:!selected {{
    background: {C['panel2']}; color: {C['text2']};
}}

/* ── Durum çubuğu ─────────────────────────────── */
QStatusBar {{
    background: {C['header']}; color: {C['text3']};
    font-size: 11px; padding: 2px 8px;
    border-top: 1px solid {C['border']};
}}

/* ── Splitter ─────────────────────────────────── */
QSplitter::handle {{ background: {C['border']}; width: 3px; }}

/* ── Scrollbar ────────────────────────────────── */
QScrollBar:vertical {{
    background: {C['panel']}; width: 7px; border-radius: 4px; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {C['border2']}; border-radius: 4px; min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background: {C['blue']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""


# ─────────────────────────────────────────────────────────────────────────────
#  OCCUPANCY GRID  —  Ay yüzeyi engel haritası
# ─────────────────────────────────────────────────────────────────────────────
class OccupancyGrid:
    """
    GRID_SIZE x GRID_SIZE boyutunda 2D harita.
    Her hücre:  0 = serbest,  1 = engel,  0..1 arası = maliyet (eğim, krater yakını)
    Simscape'ten gelen engel koordinatları buraya yazılır.
    A* bu harita üzerinde çalışır.
    """
    GRID_SIZE = 50          # 50x50 hücre
    OBSTACLE_RADIUS = 2     # engel etrafında kaç hücre bloklansın

    def __init__(self):
        n = self.GRID_SIZE
        self.grid = [[0.0] * n for _ in range(n)]   # maliyet haritası
        self.blocked = [[False] * n for _ in range(n)]  # kesin engel
        self._add_static_features()

    def _add_static_features(self):
        """Sabit kraterler ve kayalar — başlangıç haritası"""
        n = self.GRID_SIZE
        craters = [
            (22, 27, 4),   # (col, row, yarıçap)
            (35, 12, 3),
            (7,  35, 4),
            (40, 38, 5),
            (15, 18, 2),
        ]
        for cx, cy, r in craters:
            for dy in range(-r - 2, r + 3):
                for dx in range(-r - 2, r + 3):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < n and 0 <= ny < n:
                        dist = math.sqrt(dx*dx + dy*dy)
                        if dist <= r:
                            self.blocked[ny][nx] = True
                            self.grid[ny][nx] = 1.0
                        elif dist <= r + 2:
                            # krater kenarı — yüksek maliyet ama geçilebilir
                            cost = 0.5 * (1 - (dist - r) / 2)
                            self.grid[ny][nx] = max(self.grid[ny][nx], cost)

    def add_obstacle(self, col: float, row: float):
        """
        Simscape'ten gelen engel koordinatını haritaya yaz.
        col, row: 0.0-1.0 arası normalize koordinat
        """
        n = self.GRID_SIZE
        gc = int(col * n)
        gr = int(row * n)
        r = self.OBSTACLE_RADIUS
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                nx, ny = gc + dx, gr + dy
                if 0 <= nx < n and 0 <= ny < n:
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist <= r:
                        self.blocked[ny][nx] = True
                        self.grid[ny][nx] = 1.0
                    else:
                        self.grid[ny][nx] = max(self.grid[ny][nx], 0.4)

    def cost(self, col: int, row: int) -> float:
        """Hücre geçiş maliyeti. Engel = sonsuz."""
        if self.blocked[row][col]:
            return float('inf')
        return 1.0 + self.grid[row][col] * 8.0  # eğim/krater yakını = daha pahalı

    def is_free(self, col: int, row: int) -> bool:
        n = self.GRID_SIZE
        if not (0 <= col < n and 0 <= row < n):
            return False
        return not self.blocked[row][col]


# ─────────────────────────────────────────────────────────────────────────────
#  A* ALGORITMA MOTORU
# ─────────────────────────────────────────────────────────────────────────────
class AStarPlanner:
    """
    Gerçek A* implementasyonu.
    - 8 yönlü hareket (çapraz dahil)
    - Öklid heuristiği
    - OccupancyGrid üzerinde çalışır
    - Dinamik engel eklenince rota yeniden hesaplanır
    """

    def __init__(self, grid: OccupancyGrid):
        self.grid = grid
        self.path = []          # [(col, row), ...]  grid koordinatları
        self.path_norm = []     # [(x, y), ...]  0-1 normalize

    # 8 komşu yön — (dcol, drow, maliyet_çarpanı)
    DIRS = [
        (0,  1,  1.0), (0, -1,  1.0), ( 1, 0,  1.0), (-1,  0, 1.0),
        (1,  1,  1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414),
    ]

    @staticmethod
    def heuristic(c1, r1, c2, r2) -> float:
        return math.sqrt((c1-c2)**2 + (r1-r2)**2)

    def plan(self, start_norm, goal_norm) -> list:
        """
        start_norm, goal_norm: (x, y) normalize (0-1)
        Döndürür: normalize (x, y) listesi
        """
        n = self.grid.GRID_SIZE
        sc = int(start_norm[0] * n)
        sr = int(start_norm[1] * n)
        gc = int(goal_norm[0]  * n)
        gr = int(goal_norm[1]  * n)

        sc = max(0, min(n-1, sc)); sr = max(0, min(n-1, sr))
        gc = max(0, min(n-1, gc)); gr = max(0, min(n-1, gr))

        if not self.grid.is_free(sc, sr):
            sc, sr = self._nearest_free(sc, sr)
        if not self.grid.is_free(gc, gr):
            gc, gr = self._nearest_free(gc, gr)

        # open set: (f, g, col, row, parent)
        open_heap = []
        h0 = self.heuristic(sc, sr, gc, gr)
        heapq.heappush(open_heap, (h0, 0.0, sc, sr, None))

        came_from = {}   # (col, row) → (parent_col, parent_row)
        g_score   = {(sc, sr): 0.0}
        visited   = set()

        while open_heap:
            f, g, col, row, parent = heapq.heappop(open_heap)

            if (col, row) in visited:
                continue
            visited.add((col, row))
            came_from[(col, row)] = parent

            if col == gc and row == gr:
                return self._reconstruct(came_from, gc, gr, n)

            for dc, dr, w in self.DIRS:
                nc, nr = col + dc, row + dr
                if not self.grid.is_free(nc, nr):
                    continue
                if (nc, nr) in visited:
                    continue
                cell_cost = self.grid.cost(nc, nr)
                if cell_cost == float('inf'):
                    continue
                ng = g + w * cell_cost
                if ng < g_score.get((nc, nr), float('inf')):
                    g_score[(nc, nr)] = ng
                    f_new = ng + self.heuristic(nc, nr, gc, gr)
                    heapq.heappush(open_heap, (f_new, ng, nc, nr, (col, row)))

        return []  # yol bulunamadı

    def _reconstruct(self, came_from, gc, gr, n):
        path = []
        node = (gc, gr)
        while node is not None:
            path.append(node)
            node = came_from.get(node)
        path.reverse()
        # Normalize et
        result = [(c / n, r / n) for c, r in path]
        self.path = [(c, r) for c, r in path]
        self.path_norm = result
        return result

    def _nearest_free(self, col, row):
        """En yakın serbest hücreyi bul"""
        n = self.grid.GRID_SIZE
        for radius in range(1, 8):
            for dc in range(-radius, radius+1):
                for dr in range(-radius, radius+1):
                    nc, nr = col+dc, row+dr
                    if 0 <= nc < n and 0 <= nr < n and self.grid.is_free(nc, nr):
                        return nc, nr
        return col, row

    def replan_needed(self, rover_norm, obstacles: list) -> bool:
        """Rota üzerinde yeni engel var mı? Varsa yeniden plan yap."""
        n = self.grid.GRID_SIZE
        for obs in obstacles:
            oc = int(obs[0] * n)
            or_ = int(obs[1] * n)
            for (pc, pr) in self.path:
                if abs(pc - oc) <= 3 and abs(pr - or_) <= 3:
                    return True
        return False


# ─────────────────────────────────────────────────────────────────────────────
#  SIMULINK / SIMSCAPE ALICI
# ─────────────────────────────────────────────────────────────────────────────
class SimulinkReceiver(QObject):
    data_received     = Signal(dict)
    connection_status = Signal(str, bool)

    def __init__(self):
        super().__init__()
        self.sock = None
        self.running = False
        self.host, self.port, self.protocol = "127.0.0.1", 25000, "UDP"

    def set_connection(self, host, port, protocol):
        self.host, self.port, self.protocol = host, port, protocol

    def start_listening(self):
        self.running = True
        try:
            if self.protocol == "UDP":
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.sock.bind((self.host, self.port))
                self.sock.settimeout(1.0)
                self.connection_status.emit(f"UDP dinleniyor  {self.host}:{self.port}", True)
                while self.running:
                    try:
                        data, _ = self.sock.recvfrom(4096)
                        self.data_received.emit(json.loads(data.decode()))
                    except socket.timeout:
                        continue
            else:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.host, self.port))
                self.sock.settimeout(1.0)
                self.connection_status.emit(f"TCP bağlandı  {self.host}:{self.port}", True)
                buf = ""
                while self.running:
                    try:
                        buf += self.sock.recv(1024).decode()
                        while "\n" in buf:
                            line, buf = buf.split("\n", 1)
                            self.data_received.emit(json.loads(line.strip()))
                    except socket.timeout:
                        continue
        except Exception as e:
            self.connection_status.emit(f"Bağlantı hatası: {e}", False)

    def stop(self):
        self.running = False
        if self.sock:
            try: self.sock.close()
            except: pass


# ─────────────────────────────────────────────────────────────────────────────
#  DEMO VERİ ÜRETECİ
# ─────────────────────────────────────────────────────────────────────────────
class DemoGen(QObject):
    data_ready = Signal(dict)

    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.timer.timeout.connect(self._gen)
        self.t = 0
        self.battery = 92.0
        self.lat = 0.00210
        self.lon = 0.00340
        self.heading = 90.0
        self.scenario = {
            5:  ("OBSTACLE_DETECTED", "⚠ ENGEL TESPİT EDİLDİ — mesafe: 3.2 m"),
            8:  ("RECALCULATING",     "◈ ROTA YENİDEN HESAPLANIYOR..."),
            11: ("TURN_NORTH_45",     "↺ KUZEY'E 45° DÖN"),
            16: ("MOVE_FORWARD",      "→ İLERLE — 4.1 m düz hat"),
            22: ("CRATER_PROXIMITY",  "⚠ KRATER YAKINI — sağ: 1.8 m"),
            25: ("TURN_EAST_30",      "↺ DOĞU'YA 30° DÖN"),
            30: ("SLOPE_WARNING",     "▲ EĞİM UYARISI — %18 tespit edildi"),
            34: ("SPEED_REDUCE",      "▼ HIZ AZALT  0.15 m/s"),
            40: ("OBSTACLE_CLEAR",    "✓ ENGEL SERBEST — rota temiz"),
            44: ("MOVE_FORWARD",      "→ İLERLE — hedefe 12.3 m kaldı"),
            52: ("WAYPOINT_REACHED",  "★ WAYPOINT-1 ULAŞILDI"),
            56: ("TURN_WEST_60",      "↺ BATI'YA 60° DÖN"),
            62: ("OBSTACLE_DETECTED", "⚠ ENGEL TESPİT EDİLDİ — mesafe: 2.1 m"),
            65: ("TURN_SOUTH_20",     "↺ GÜNEY'E 20° DÖN"),
            70: ("MOVE_FORWARD",      "→ İLERLE — alternatif rota aktif"),
        }

    def start(self): self.timer.start(500)
    def stop(self):  self.timer.stop()

    def _gen(self):
        self.t += 1
        self.battery = max(0, self.battery - 0.02)
        self.heading = (self.heading + random.uniform(-0.5, 0.5)) % 360
        self.lat += 0.000001 * math.cos(math.radians(self.heading))
        self.lon += 0.000001 * math.sin(math.radians(self.heading))
        status, nav_cmd = "MOVING", ""
        if self.t in self.scenario:
            status, nav_cmd = self.scenario[self.t]
        if "RECALC" in status or "STOP" in status: spd = 0.0
        elif "REDUCE" in status: spd = 0.12
        else: spd = 0.28 + random.uniform(-0.05, 0.05)
        self.data_ready.emit({
            "battery":       round(self.battery, 1),
            "speed":         round(abs(spd), 3),
            "heading":       round(self.heading, 1),
            "lat":           round(self.lat, 6),
            "lon":           round(self.lon, 6),
            "altitude":      round(-0.8 + math.sin(self.t*0.1)*1.2, 2),
            "temp":          round(-42.0 + math.sin(self.t*0.05)*3, 1),
            "signal":        round(94 + random.uniform(-3, 3), 1),
            "status":        status,
            "obstacle_dist": round(2.5 + math.sin(self.t*0.2)*1.5, 2),
            "nav_cmd":       nav_cmd,
            "wheel_rpm":     round(12.4 + random.uniform(-1, 1), 1),
            "cpu_temp":      round(38 + random.uniform(-2, 2), 1),
            # Simscape'ten gelen engel listesi (demo: zaman zaman rastgele engel)
            "obstacles":     self._demo_obstacles(),
        })

    def _demo_obstacles(self):
        """Demo mod: belirli adımlarda sanal engel koordinatı üret"""
        if self.t in (5, 22, 62):
            x = 0.3 + random.uniform(0, 0.4)
            y = 0.3 + random.uniform(0, 0.4)
            return [{"x": round(x,3), "y": round(y,3)}]
        return []


# ─────────────────────────────────────────────────────────────────────────────
#  HARİTA CANVAS  —  OccupancyGrid + A* rota
# ─────────────────────────────────────────────────────────────────────────────
class MapCanvas(QWidget):
    # A* yeniden hesaplandı sinyali (log için)
    replan_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self.setMinimumSize(340, 340)

        # Occupancy grid ve A* planlayıcı
        self.og = OccupancyGrid()
        self.planner = AStarPlanner(self.og)

        self.rover_pos = QPointF(0.08, 0.08)
        self.heading   = 90.0
        self.trail     = deque(maxlen=120)

        # Waypoint sırası
        self.waypoints = [
            (0.25, 0.25),
            (0.75, 0.35),
            (0.80, 0.80),
        ]
        self.wp_index = 0

        # İlk rotayı hesapla
        self.astar_path = []   # normalize (x,y) listesi
        self._replan()

        # Dinamik engeller (Simscape'ten gelir)
        self.dynamic_obstacles = []

        # Harita renklendirme için cost cache
        self._cost_cache = None
        self._build_cost_cache()

    def _build_cost_cache(self):
        n = self.og.GRID_SIZE
        self._cost_cache = []
        for r in range(n):
            row = []
            for c in range(n):
                if self.og.blocked[r][c]:
                    row.append(2.0)
                else:
                    row.append(self.og.grid[r][c])
            self._cost_cache.append(row)

    def _replan(self):
        if self.wp_index >= len(self.waypoints):
            self.astar_path = []
            return
        goal = self.waypoints[self.wp_index]
        path = self.planner.plan(
            (self.rover_pos.x(), self.rover_pos.y()),
            goal
        )
        self.astar_path = path
        if path:
            dir_cmd = self._path_to_direction(path)
            self.replan_signal.emit(dir_cmd)

    def _path_to_direction(self, path) -> str:
        """İlk iki waypoint'e bakarak yön komutu üret"""
        if len(path) < 2:
            return "→ HEDEFE ULAŞILDI"
        dx = path[1][0] - path[0][0]
        dy = path[1][1] - path[0][1]
        angle = math.degrees(math.atan2(dy, dx)) % 360
        compass = ["DOĞU","GÜNEYDOĞU","GÜNEY","GÜNEYBATI",
                   "BATI","KUZEYBATI","KUZEY","KUZEYDOĞU"]
        idx = int((angle + 22.5) / 45) % 8
        deg = round(angle, 1)
        return f"↺ {compass[idx]} YÖNÜNE {deg}° — A* ROTA AKTİF"

    def add_obstacle(self, x: float, y: float):
        """Simscape'ten gelen engeli haritaya ekle, rotayı yeniden hesapla"""
        self.og.add_obstacle(x, y)
        self.dynamic_obstacles.append((x, y))
        self._build_cost_cache()
        self._replan()

    def update_rover(self, data: dict):
        # Engelleri işle
        for obs in data.get("obstacles", []):
            ox, oy = obs.get("x", 0), obs.get("y", 0)
            if (ox, oy) not in self.dynamic_obstacles:
                self.add_obstacle(ox, oy)

        # Rover'ı ilerlet
        spd = data.get("speed", 0)
        if spd > 0 and self.astar_path and len(self.astar_path) > 1:
            # Bir sonraki yol noktasına doğru ilerle
            next_x, next_y = self.astar_path[1]
            dx = next_x - self.rover_pos.x()
            dy = next_y - self.rover_pos.y()
            dist = math.sqrt(dx*dx + dy*dy)
            step = 0.006 * spd
            if dist < step:
                self.astar_path.pop(0)
                # Waypoint'e ulaştık mı?
                if len(self.astar_path) <= 1 and self.wp_index < len(self.waypoints):
                    wp = self.waypoints[self.wp_index]
                    if abs(self.rover_pos.x()-wp[0]) < 0.05 and abs(self.rover_pos.y()-wp[1]) < 0.05:
                        self.wp_index = min(self.wp_index+1, len(self.waypoints))
                        self._replan()
            else:
                move = step / dist
                new_x = self.rover_pos.x() + dx * move
                new_y = self.rover_pos.y() + dy * move
                self.rover_pos = QPointF(
                    max(0.01, min(0.99, new_x)),
                    max(0.01, min(0.99, new_y))
                )
                self.heading = math.degrees(math.atan2(dy, dx))
        else:
            # A* yolu yoksa heading'e göre küçük adım
            self.heading = data.get("heading", self.heading)

        self.trail.append(QPointF(self.rover_pos))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        n = self.og.GRID_SIZE
        cw = w / n   # hücre genişliği
        ch = h / n   # hücre yüksekliği

        # ── Arka plan — cost haritası ──
        for r in range(n):
            for c in range(n):
                cost = self._cost_cache[r][c]
                if cost >= 1.0:
                    color = QColor(180, 50, 50, 230)    # engel: koyu kırmızı
                elif cost > 0.3:
                    color = QColor(140, 90, 20, int(cost * 200))   # yüksek maliyet: koyu amber
                elif cost > 0.05:
                    color = QColor(100, 80, 20, int(cost * 140))   # orta: soluk sarı
                else:
                    color = QColor(18, 26, 42)           # serbest: koyu lacivert-gri
                p.fillRect(
                    int(c*cw), int(r*ch),
                    max(1, int(cw)+1), max(1, int(ch)+1),
                    color
                )

        # ── Izgara ──
        p.setPen(QPen(QColor(40, 58, 80, 120), 0.4))
        step = max(1, n // 10)
        for i in range(0, n+1, step):
            p.drawLine(int(i*cw), 0, int(i*cw), h)
            p.drawLine(0, int(i*ch), w, int(i*ch))

        def px(nx, ny):
            return QPointF(nx * w, ny * h)

        # ── A* Rota ──
        if len(self.astar_path) > 1:
            pts = [px(x, y) for x, y in self.astar_path]
            # Gölge
            pen = QPen(QColor(0, 97, 194, 35), 7)
            p.setPen(pen)
            for i in range(1, len(pts)): p.drawLine(pts[i-1], pts[i])
            # Ana çizgi
            pen = QPen(QColor("#0061C2"), 2.5)
            pen.setDashPattern([6, 3])
            p.setPen(pen)
            for i in range(1, len(pts)): p.drawLine(pts[i-1], pts[i])
            # Düğüm noktaları (her 5 adımda bir)
            p.setBrush(QBrush(QColor(0, 97, 194, 120)))
            p.setPen(Qt.NoPen)
            for i, (nx, ny) in enumerate(self.astar_path):
                if i % 5 == 0:
                    pp = px(nx, ny)
                    p.drawEllipse(pp, 3, 3)

        # ── Rover izi ──
        if len(self.trail) > 1:
            pts = [px(pt.x(), pt.y()) for pt in self.trail]
            for i in range(1, len(pts)):
                a = int(15 + 210 * i / len(pts))
                p.setPen(QPen(QColor(0, 97, 194, a), 2))
                p.drawLine(pts[i-1], pts[i])

        # ── Waypoints ──
        for i, (wx, wy) in enumerate(self.waypoints):
            wpp = px(wx, wy)
            if i < self.wp_index:
                col = QColor(60, 80, 100)    # tamamlandı — soluk
            elif i == self.wp_index:
                col = QColor(251, 191, 36)   # aktif — amber
            else:
                col = QColor(74, 158, 255)   # bekleyen — soft mavi
            p.setBrush(QBrush(col))
            p.setPen(QPen(col.lighter(130), 1.5))
            p.drawEllipse(wpp, 8, 8)
            p.setFont(QFont("Segoe UI", 9, QFont.Bold))
            p.setPen(col.lighter(160))
            p.drawText(int(wpp.x())+11, int(wpp.y())+4, f"WP{i+1}")

        # ── Dinamik engeller (Simscape'ten geldi) ──
        for (ox, oy) in self.dynamic_obstacles:
            op = px(ox, oy)
            p.setBrush(QBrush(QColor(220, 80, 80, 200)))
            p.setPen(QPen(QColor(255, 120, 120), 1.5))
            p.drawEllipse(op, 5, 5)

        # ── Rover ──
        rp = px(self.rover_pos.x(), self.rover_pos.y())
        g2 = QRadialGradient(rp, 18)
        g2.setColorAt(0, QColor(0, 97, 194, 50))
        g2.setColorAt(1, QColor(0, 97, 194, 0))
        p.setBrush(QBrush(g2)); p.setPen(Qt.NoPen); p.drawEllipse(rp, 18, 18)
        p.save(); p.translate(rp); p.rotate(self.heading)
        body = QPainterPath()
        body.moveTo(0, -11); body.lineTo(-6, 6); body.lineTo(0, 3); body.lineTo(6, 6)
        body.closeSubpath()
        p.setBrush(QBrush(QColor("#0061C2")))
        p.setPen(QPen(QColor("white"), 1.2))
        p.drawPath(body); p.restore()

        # ── Bilgi çubuğu ──
        p.setPen(QColor(100, 130, 160))
        p.setFont(QFont("Consolas", 8))
        p.drawText(4, h-5,
            f"WP:{self.wp_index+1}/{len(self.waypoints)}  "
            f"ENG:{len(self.dynamic_obstacles)}  "
            f"ROTA:{len(self.astar_path)} adim")

        # ── Lejant ──
        lx, ly = w - 115, 8
        p.setFont(QFont("Segoe UI", 8))
        items = [
            (QColor(180, 50, 50), "Engel/Krater"),
            (QColor(140, 90, 20), "Yuksek maliyet"),
            (QColor(74, 158, 255), "A* Rota"),
        ]
        for i, (col, lbl) in enumerate(items):
            p.fillRect(lx, ly + i*14, 10, 10, col)
            p.setPen(QColor(160, 190, 220))
            p.drawText(lx+13, ly + i*14 + 9, lbl)


# ─────────────────────────────────────────────────────────────────────────────
#  SİMÜLASYON FEED
# ─────────────────────────────────────────────────────────────────────────────
class SimFeed(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(250)
        self.data = {}
        self.t = 0
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(120)

    def _tick(self): self.t += 1; self.update()
    def update_data(self, d): self.data = d

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QColor("#141D2B"))
        p.setPen(QPen(QColor(255,255,255,10), 0.5))
        for i in range(0, w, 30): p.drawLine(i, 0, i, h)
        for j in range(0, h, 30): p.drawLine(0, j, w, j)
        sy = int((self.t * 3) % h)
        p.setPen(QPen(QColor(56, 189, 248, 18), 2)); p.drawLine(0, sy, w, sy)
        p.setPen(QColor("#475569")); p.setFont(QFont("Consolas", 12))
        p.drawText(QRectF(0, 0, w, h), Qt.AlignCenter,
            "SİMÜLASYON FEED\n\nSimulink / Simscape görüntüsü\nUDP bağlantısı kurulunca aktarılacak\n\nudp://127.0.0.1:25001")
        p.setFont(QFont("Consolas", 9)); p.setPen(QColor(56, 189, 248, 130))
        p.drawText(8, 18, f"SIM  |  {'LIVE' if self.data else 'STANDBY'}  |  FRAME {self.t:06d}")
        if self.data:
            p.setFont(QFont("Consolas", 11, QFont.Bold)); p.setPen(QColor("#4ADE80"))
            for i, ln in enumerate([
                f"SPD  {self.data.get('speed',0):.3f} m/s",
                f"HDG  {self.data.get('heading',0):06.1f}",
                f"ALT  {self.data.get('altitude',0):+.2f} m",
                f"BAT  {self.data.get('battery',0):.1f}%",
            ]):
                p.drawText(w - 175, 22 + i*20, ln)


# ─────────────────────────────────────────────────────────────────────────────
#  ANA PENCERE
# ─────────────────────────────────────────────────────────────────────────────
class Dashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lunar Rover GCS — Navigation Control System v3.0")
        self.setMinimumSize(1400, 900)
        self.resize(1560, 960)
        self.setStyleSheet(SS)

        self.sim_connected = False
        self.demo = DemoGen()
        self.demo.data_ready.connect(self._on_data)
        self.recv = SimulinkReceiver()
        self.recv.data_received.connect(self._on_data)
        self.recv.connection_status.connect(self._on_conn_status)

        self._build_ui()
        self._start_demo()

    # ── UI ───────────────────────────────────────────────────────────────────
    def _build_ui(self):
        cw = QWidget(); self.setCentralWidget(cw)
        root = QVBoxLayout(cw); root.setSpacing(0); root.setContentsMargins(0,0,0,0)
        root.addWidget(self._mk_header())
        body = QWidget()
        bl = QVBoxLayout(body); bl.setContentsMargins(10,10,10,10); bl.setSpacing(8)
        bl.addWidget(self._mk_telem())
        bl.addWidget(self._mk_conn_panel())
        spl = QSplitter(Qt.Horizontal); spl.setHandleWidth(6)
        spl.addWidget(self._mk_left()); spl.addWidget(self._mk_right())
        spl.setSizes([820, 640])
        bl.addWidget(spl, 1)
        root.addWidget(body, 1)
        self.status_bar = QStatusBar(); self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(
            "Demo mode  —  Gerçek A* aktif  —  Simulink bağlantısı için bağlantı panelini kullan")

    def _mk_header(self):
        # Tüm header lacivert — beyaz parça kalmıyor
        bar = QFrame()
        bar.setObjectName("Header")
        bar.setFixedHeight(64)
        bar.setStyleSheet(f"background: {C['header']}; border: none;")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 0, 20, 0)
        lay.setSpacing(0)

        # ── Sol: Logo + proje adı ──────────────────
        logo_dot = QLabel("◈")
        logo_dot.setFont(QFont("Segoe UI", 22))
        logo_dot.setStyleSheet("color: #38BDF8; margin-right: 10px;")
        lay.addWidget(logo_dot)

        name_col = QWidget()
        name_col.setStyleSheet("background: transparent;")
        name_vl = QVBoxLayout(name_col)
        name_vl.setContentsMargins(0, 0, 0, 0)
        name_vl.setSpacing(1)

        umay = QLabel("UMAY GCS")
        umay.setFont(QFont("Segoe UI", 20, QFont.Bold))
        umay.setStyleSheet("color: #FFFFFF; letter-spacing: 4px; background: transparent;")

        sub = QLabel("AUTONOMOUS LUNAR ROVER  ·  A* NAVIGATION ENGINE")
        sub.setFont(QFont("Segoe UI", 9))
        sub.setStyleSheet("color: #64748B; letter-spacing: 2px; background: transparent;")

        name_vl.addWidget(umay)
        name_vl.addWidget(sub)
        lay.addWidget(name_col)

        # ── Orta: ayırıcı çizgi ───────────────────
        lay.addStretch()

        # ── Sağ: saat + bağlantı rozeti ──────────
        self.clk = QLabel()
        self.clk.setFont(QFont("Consolas", 12, QFont.Bold))
        self.clk.setStyleSheet("color: #94A3B8; background: transparent; margin-right: 18px;")
        lay.addWidget(self.clk)

        # Bağlantı rozeti — belirgin renk farkıyla
        self.badge = QLabel("  ○  DEMO  ")
        self.badge.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.badge.setStyleSheet(
            "background: #451A03; color: #FED7AA;"
            "border: 1px solid #92400E;"
            "border-radius: 6px; padding: 4px 12px;")
        lay.addWidget(self.badge)

        tmr = QTimer(self)
        tmr.timeout.connect(self._tick_clk)
        tmr.start(1000)
        self._tick_clk()
        return bar

    def _mk_telem(self):
        frame = QFrame(); frame.setObjectName("Card")
        lay = QHBoxLayout(frame); lay.setContentsMargins(10,6,10,6); lay.setSpacing(4)

        def tile(lbl_txt, min_w=95):
            f = QFrame(); f.setObjectName("Card"); f.setMinimumWidth(min_w)
            vl = QVBoxLayout(f); vl.setContentsMargins(7,4,7,4); vl.setSpacing(1)
            lb = QLabel(lbl_txt); lb.setObjectName("LSmall"); lb.setAlignment(Qt.AlignCenter)
            val = QLabel("—"); val.setObjectName("LBigG")
            val.setFont(QFont("Consolas",19,QFont.Bold)); val.setAlignment(Qt.AlignCenter)
            vl.addWidget(lb); vl.addWidget(val)
            return f, val

        def div():
            d = QFrame(); d.setFrameShape(QFrame.VLine)
            d.setStyleSheet(f"color:{C['border']};"); return d

        # Batarya — daraltılmış
        bf = QFrame(); bf.setObjectName("Card"); bf.setFixedWidth(100)
        bvl = QVBoxLayout(bf); bvl.setContentsMargins(7,4,7,4); bvl.setSpacing(2)
        bl_ = QLabel("BATTERY"); bl_.setObjectName("LSmall"); bl_.setAlignment(Qt.AlignCenter)
        self.bat_val = QLabel("92.0 %"); self.bat_val.setObjectName("LBigG")
        self.bat_val.setFont(QFont("Consolas",16,QFont.Bold)); self.bat_val.setAlignment(Qt.AlignCenter)
        self.bat_bar = QProgressBar(); self.bat_bar.setRange(0,100); self.bat_bar.setValue(92)
        self.bat_bar.setFixedHeight(6)
        bvl.addWidget(bl_); bvl.addWidget(self.bat_val); bvl.addWidget(self.bat_bar)
        lay.addWidget(bf); lay.addWidget(div())

        f, self.spd_v  = tile("SPEED  m/s");  lay.addWidget(f); lay.addWidget(div())
        f, self.hdg_v  = tile("HEADING  deg"); lay.addWidget(f); lay.addWidget(div())
        f, self.tmp_v  = tile("TEMP  C");      lay.addWidget(f); lay.addWidget(div())
        f, self.sig_v  = tile("SIGNAL  %");    lay.addWidget(f); lay.addWidget(div())
        f, self.rpm_v  = tile("WHEEL RPM");    lay.addWidget(f); lay.addWidget(div())
        f, self.cpu_v  = tile("CPU  C");       lay.addWidget(f); lay.addWidget(div())

        # Rover status
        sf = QFrame(); sf.setObjectName("CardGreen"); sf.setMinimumWidth(138)
        svl = QVBoxLayout(sf); svl.setContentsMargins(10,4,10,4); svl.setSpacing(1)
        sl = QLabel("ROVER STATUS"); sl.setObjectName("LSmall"); sl.setAlignment(Qt.AlignCenter)
        sl.setStyleSheet(f"color:{C['text3']};font-size:10px;font-weight:bold;letter-spacing:2px;")
        self.st_val = QLabel("MOVING")
        self.st_val.setFont(QFont("Segoe UI",14,QFont.Bold))
        self.st_val.setStyleSheet(f"color:{C['green']};letter-spacing:2px;")
        self.st_val.setAlignment(Qt.AlignCenter)
        svl.addWidget(sl); svl.addWidget(self.st_val)
        lay.addWidget(sf); lay.addStretch()
        return frame

    def _mk_conn_panel(self):
        frame = QFrame(); frame.setObjectName("ConnPanel")
        lay = QHBoxLayout(frame); lay.setContentsMargins(16,10,16,10); lay.setSpacing(14)
        ico = QLabel("SIMULINK CONNECTTI AYARLARI")
        ico.setFont(QFont("Segoe UI",12,QFont.Bold))
        ico.setStyleSheet(f"color:{C['blue']};letter-spacing:1px;")
        lay.addWidget(ico)

        def sep():
            d = QFrame(); d.setFrameShape(QFrame.VLine)
            d.setStyleSheet(f"color:{C['border']};"); return d

        def lbl(t):
            l = QLabel(t); l.setFont(QFont("Segoe UI",12,QFont.Bold))
            l.setStyleSheet(f"color:{C['text2']};"); return l

        lay.addWidget(sep())
        lay.addWidget(lbl("Protocol:"))
        self.proto = QComboBox(); self.proto.addItems(["UDP","TCP"])
        self.proto.setFixedWidth(80); self.proto.setFixedHeight(36)
        lay.addWidget(self.proto)

        lay.addWidget(lbl("Host / IP:"))
        self.host_inp = QLineEdit("127.0.0.1")
        self.host_inp.setFixedWidth(145); self.host_inp.setFixedHeight(36)
        lay.addWidget(self.host_inp)

        lay.addWidget(lbl("Port:"))
        self.port_inp = QSpinBox(); self.port_inp.setRange(1024,65535)
        self.port_inp.setValue(25000); self.port_inp.setFixedWidth(92); self.port_inp.setFixedHeight(36)
        lay.addWidget(self.port_inp)
        lay.addWidget(sep())

        self.conn_btn = QPushButton("CONNECT"); self.conn_btn.setObjectName("BtnConn")
        self.conn_btn.setFixedHeight(38); self.conn_btn.clicked.connect(self._toggle_conn)
        lay.addWidget(self.conn_btn)

        # Bağlantı durum etiketi
        self.conn_status_lbl = QLabel("Not connected")
        self.conn_status_lbl.setFont(QFont("Consolas", 10))
        self.conn_status_lbl.setStyleSheet(f"color:{C['text3']}; margin-left:4px;")
        lay.addWidget(self.conn_status_lbl)

        lay.addStretch()

        hint = QLabel("Simulink UDP Send  |  IP: 127.0.0.1  |  Port: 25000  |  Format: JSON")
        hint.setFont(QFont("Consolas",10)); hint.setStyleSheet(f"color:{C['text3']};")
        lay.addWidget(hint)
        return frame

    def _mk_left(self):
        w = QWidget(); vl = QVBoxLayout(w)
        vl.setContentsMargins(0,0,4,0); vl.setSpacing(6)
        tabs = QTabWidget()
        mt = QWidget(); mvl = QVBoxLayout(mt); mvl.setContentsMargins(4,4,4,4)
        self.map_c = MapCanvas()
        self.map_c.replan_signal.connect(self._on_replan)
        mvl.addWidget(self.map_c)
        hint = QLabel(
            "Rover  |  WP Waypoint  |  Red=Obstacle  |  Amber=High cost  |  Blue=A* route  |  Yellow=Active WP")
        hint.setFont(QFont("Segoe UI",9))
        hint.setStyleSheet(f"color:{C['text3']};padding:2px 4px;")
        mvl.addWidget(hint); tabs.addTab(mt,"  A* MAP  ")

        st = QWidget(); svl_ = QVBoxLayout(st); svl_.setContentsMargins(4,4,4,4)
        self.sim_feed = SimFeed(); svl_.addWidget(self.sim_feed)
        tabs.addTab(st,"  SIM FEED  ")
        vl.addWidget(tabs); return w

    def _mk_right(self):
        w = QWidget(); vl = QVBoxLayout(w)
        vl.setContentsMargins(4,0,0,0); vl.setSpacing(8)

        # ── Group 1: Vehicle Status & Position ───────
        g1 = QGroupBox("VEHICLE STATUS  &  POSITION")
        g1l = QVBoxLayout(g1); g1l.setSpacing(6)

        pf = QFrame(); pf.setObjectName("Card")
        pg = QGridLayout(pf); pg.setContentsMargins(14,10,14,10)
        pg.setSpacing(7); pg.setColumnStretch(1,1); pg.setColumnStretch(3,1)

        def pos_cell(lbl_t, col_l, col_v, row):
            lb = QLabel(lbl_t); lb.setFont(QFont("Segoe UI",10,QFont.Bold))
            lb.setStyleSheet(f"color:{C['text2']};")
            vl_ = QLabel("—"); vl_.setFont(QFont("Consolas",13,QFont.Bold))
            vl_.setStyleSheet(f"color:{C['blue']};")
            pg.addWidget(lb, row, col_l)
            pg.addWidget(vl_, row, col_v)
            return vl_

        # Konum bilgileri — sol sütun
        self.p_lat = pos_cell("LAT :",    0, 1, 0)
        self.p_lon = pos_cell("LON :",    0, 1, 1)
        self.p_alt = pos_cell("ALT :",    0, 1, 2)
        self.p_obs = pos_cell("OBS DIST:",0, 1, 3)

        # SPD + HDG — sağ sütun (telemetri akışının yerine)
        sep_line = QFrame(); sep_line.setFrameShape(QFrame.VLine)
        sep_line.setStyleSheet(f"color:{C['border2']};")
        pg.addWidget(sep_line, 0, 2, 4, 1)

        self.p_spd = pos_cell("SPEED :",   3, 4, 0)
        self.p_hdg = pos_cell("HEADING :", 3, 4, 1)
        self.p_wpt = pos_cell("WAYPOINT:", 3, 4, 2)
        self.p_rta = pos_cell("ROUTE PTS:",3, 4, 3)

        g1l.addWidget(pf)
        vl.addWidget(g1, 1)   # sabit küçük alan

        # ── Group 2: Navigation Engine (büyütüldü) ───
        g2 = QGroupBox("NAVIGATION ENGINE  —  A* MANEUVER COMMANDS")
        g2l = QVBoxLayout(g2); g2l.setSpacing(5); g2l.setContentsMargins(8,12,8,8)

        # Active command banner
        cf = QFrame(); cf.setObjectName("CardBlue"); cf.setFixedHeight(48)
        cl = QHBoxLayout(cf); cl.setContentsMargins(14,5,14,5)
        ct = QLabel("ACTIVE CMD:"); ct.setFont(QFont("Segoe UI",11,QFont.Bold))
        ct.setStyleSheet(f"color:{C['text2']};")
        self.act_cmd = QLabel("STANDBY")
        self.act_cmd.setFont(QFont("Consolas",15,QFont.Bold))
        self.act_cmd.setStyleSheet(f"color:{C['cyan']};letter-spacing:2px;")
        cl.addWidget(ct); cl.addWidget(self.act_cmd, 1)
        g2l.addWidget(cf)

        # Nav log header bar
        nh = QFrame(); nh.setFixedHeight(30)
        nh.setStyleSheet(f"background:{C['log_bg2']};border-radius:4px 4px 0 0;")
        nhl = QHBoxLayout(nh); nhl.setContentsMargins(12,0,10,0)
        nh_lbl = QLabel("A* NAVIGATION LOG  —  MANEUVER COMMANDS")
        nh_lbl.setFont(QFont("Consolas",11,QFont.Bold))
        nh_lbl.setStyleSheet(f"color:{C['lc_green']};")
        nhl.addWidget(nh_lbl); nhl.addStretch()
        clr = QPushButton("Clear"); clr.setObjectName("BtnClr")
        clr.setFixedHeight(22); clr.setFont(QFont("Segoe UI",10))
        nhl.addWidget(clr); g2l.addWidget(nh)

        self.nav_log = QTextEdit(); self.nav_log.setObjectName("NavLog")
        self.nav_log.setReadOnly(True)
        clr.clicked.connect(self.nav_log.clear)
        g2l.addWidget(self.nav_log, 1)
        vl.addWidget(g2, 4)   # nav log 4x daha fazla alan alır
        return w

    # ── Bağlantı ─────────────────────────────────────────────────────────────
    def _toggle_conn(self):
        if not self.sim_connected:
            host  = self.host_inp.text().strip() or "127.0.0.1"
            port  = self.port_inp.value()
            proto = self.proto.currentText()

            # Bağlanmadan önce portu test et
            self.conn_btn.setEnabled(False)
            self.conn_btn.setText("DENENIYOR...")
            self.conn_status_lbl.setText(f"{proto} {host}:{port} deneniyor...")
            self.conn_status_lbl.setStyleSheet(f"color:{C['amber']}; margin-left:4px;")
            QApplication.processEvents()

            reachable = self._test_connection(host, port, proto)

            if not reachable:
                # Bağlantı kurulamadı — demo modda kal
                self.conn_btn.setEnabled(True)
                self.conn_btn.setText("CONNECT")
                self.conn_status_lbl.setText(f"CONNECTTI KURULAMADI  ({proto} {host}:{port})")
                self.conn_status_lbl.setStyleSheet(f"color:{C['red']}; font-weight:bold; margin-left:4px;")
                self.status_bar.showMessage(
                    f"HATA: {proto} {host}:{port} unreachable — Demo mode continuing")
                return

            # Bağlantı başarılı
            self.demo.stop()
            self.recv.set_connection(host, port, proto)
            threading.Thread(target=self.recv.start_listening, daemon=True).start()
            self.sim_connected = True

            self.conn_btn.setEnabled(True)
            self.conn_btn.setText("■  KES")
            self.conn_btn.setObjectName("BtnDisc")
            self.conn_btn.style().unpolish(self.conn_btn)
            self.conn_btn.style().polish(self.conn_btn)

            self.conn_status_lbl.setText(f"CONNECTED  {proto}  {host}:{port}")
            self.conn_status_lbl.setStyleSheet(f"color:{C['green']}; font-weight:bold; margin-left:4px;")

            # Header rozeti güncelle — protokol + adres net gösterilsin
            self.badge.setText(f"  ●  {proto}  {host}:{port}  ")
            self.badge.setStyleSheet(
                "background:#14532D; color:#86EFAC;"
                "border:1px solid #166534;"
                "border-radius:6px; padding:4px 12px;")
            self.status_bar.showMessage(f"CONNECTDI: {proto} {host}:{port}")

        else:
            # Bağlantıyı kes
            self.recv.stop()
            self.sim_connected = False

            self.conn_btn.setEnabled(True)
            self.conn_btn.setText("CONNECT")
            self.conn_btn.setObjectName("BtnConn")
            self.conn_btn.style().unpolish(self.conn_btn)
            self.conn_btn.style().polish(self.conn_btn)

            self.conn_status_lbl.setText("Not connected")
            self.conn_status_lbl.setStyleSheet(f"color:{C['text3']}; margin-left:4px;")

            self.badge.setText("  ○  DEMO  ")
            self.badge.setStyleSheet(
                "background:#451A03; color:#FED7AA;"
                "border:1px solid #92400E;"
                "border-radius:6px; padding:4px 12px;")
            self.status_bar.showMessage("Demo mode — Simulink connection closed")
            self._start_demo()

    def _test_connection(self, host: str, port: int, proto: str) -> bool:
        """
        Gerçekten bağlanılabilir mi test et.
        UDP: port'a test paketi gönder + 1 saniyelik yanıt bekle
        TCP: bağlantı kur ve hemen kapat
        """
        try:
            if proto == "TCP":
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2.0)
                s.connect((host, port))
                s.close()
                return True
            else:  # UDP
                # UDP bağlantısız olduğu için port'u bind etmeye çalışırız
                # Aynı makinedeyse port müsait mi kontrol et
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(1.5)
                # Test paketi gönder
                test_msg = json.dumps({"ping": True}).encode()
                s.sendto(test_msg, (host, port))
                # Yanıt bekle (Simulink cevap vermeyebilir ama port açıksa OS hata vermez)
                # Localhost için bind testi yap
                if host in ("127.0.0.1", "localhost"):
                    try:
                        s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        s2.bind((host, port))
                        s2.close()
                        s.close()
                        # Port boşsa — Simulink bağlı değil ama dinleyebiliriz
                        return True
                    except OSError:
                        # Port zaten kullanımda — Simulink orada, bağlanabiliriz
                        s.close()
                        return True
                s.close()
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    def _on_conn_status(self, msg, ok):
        self.status_bar.showMessage(f"{'BAGLI' if ok else 'HATA'}  {msg}")
        if ok:
            self.conn_status_lbl.setText(f"CONNECTED  —  {msg}")
            self.conn_status_lbl.setStyleSheet(f"color:{C['green']}; font-weight:bold; margin-left:4px;")
        else:
            self.conn_status_lbl.setText(f"HATA: {msg}")
            self.conn_status_lbl.setStyleSheet(f"color:{C['red']}; font-weight:bold; margin-left:4px;")
            # Bağlantı kurulamadıysa demo'ya geri dön
            self.sim_connected = False
            self.conn_btn.setText("CONNECT"); self.conn_btn.setObjectName("BtnConn")
            self.conn_btn.style().unpolish(self.conn_btn); self.conn_btn.style().polish(self.conn_btn)
            self.badge.setText("  ○  DEMO  ")
            self.badge.setStyleSheet(
                "background:#451A03; color:#FED7AA;"
                "border:1px solid #92400E; border-radius:6px; padding:4px 12px;")
            self._start_demo()

    # ── Data update ───────────────────────────────────────────────────────────
    def _on_data(self, d: dict):
        bat = d.get("battery", 0)
        self.bat_val.setText(f"{bat:.0f}%")
        self.bat_bar.setValue(int(bat))
        if bat < 20:   obj, pb = "LBigR", "pbR"
        elif bat < 40: obj, pb = "LBigA", "pbA"
        else:          obj, pb = "LBigG", ""
        self.bat_val.setObjectName(obj); self.bat_bar.setObjectName(pb)
        for ww in [self.bat_val, self.bat_bar]:
            ww.style().unpolish(ww); ww.style().polish(ww)

        self.spd_v.setText(f"{d.get('speed',0):.3f}")
        self.hdg_v.setText(f"{d.get('heading',0):.1f}")
        self.tmp_v.setText(f"{d.get('temp',0):.1f}")
        self.sig_v.setText(f"{d.get('signal',0):.1f}")
        self.rpm_v.setText(f"{d.get('wheel_rpm',0):.1f}")
        self.cpu_v.setText(f"{d.get('cpu_temp',0):.1f}")

        status = d.get("status", "UNKNOWN")
        self.st_val.setText(status)
        if any(x in status for x in ["OBSTACLE","WARNING","PROXIMITY"]):
            self.st_val.setStyleSheet(
                f"color:{C['amber']};font-size:14px;font-weight:bold;letter-spacing:2px;")
        elif any(x in status for x in ["STOP","ERROR","RECALC"]):
            self.st_val.setStyleSheet(
                f"color:{C['red']};font-size:14px;font-weight:bold;letter-spacing:2px;")
        else:
            self.st_val.setStyleSheet(
                f"color:{C['green']};font-size:14px;font-weight:bold;letter-spacing:2px;")

        # Position panel (left col)
        self.p_lat.setText(f"{d.get('lat',0):.6f}")
        self.p_lon.setText(f"{d.get('lon',0):.6f}")
        self.p_alt.setText(f"{d.get('altitude',0):+.2f} m")
        self.p_obs.setText(f"{d.get('obstacle_dist',0):.2f} m")

        # Position panel (right col) — SPD + HDG moved here from tel_log
        self.p_spd.setText(f"{d.get('speed',0):.3f} m/s")
        self.p_hdg.setText(f"{d.get('heading',0):.1f} deg")
        self.p_wpt.setText(f"WP {self.map_c.wp_index + 1} / {len(self.map_c.waypoints)}")
        self.p_rta.setText(f"{len(self.map_c.astar_path)} pts")

        cmd = d.get("nav_cmd", "")
        if cmd:
            self.act_cmd.setText(cmd)
            self._write_nav(cmd, d)

        self.map_c.update_rover(d)
        self.sim_feed.update_data(d)

    def _on_replan(self, direction_cmd: str):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        msg  = f'<span style="color:{C["lc_dim"]};font-size:12px;">[{ts}]</span>&nbsp;'
        msg += f'<span style="color:{C["lc_cyan"]};font-size:15px;font-weight:bold;">A* ROUTE CALCULATED</span>'
        msg += (f'<br><span style="color:#64748B;font-size:13px;">'
                f'&nbsp;&nbsp;&nbsp;&nbsp;{direction_cmd}'
                f'</span><br>')
        self.nav_log.append(msg)
        self.act_cmd.setText("A* ROUTE ACTIVE")
        sb = self.nav_log.verticalScrollBar(); sb.setValue(sb.maximum())

    def _write_nav(self, cmd, d):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        if "OBSTACLE" in cmd or "PROXIMITY" in cmd: col, pfx = C["lc_amber"], "UYARI"
        elif "WARNING" in cmd or "SLOPE" in cmd:    col, pfx = C["lc_amber"], "EGIM"
        elif "TURN" in cmd:                          col, pfx = C["lc_cyan"],  "TURN"
        elif "WAYPOINT" in cmd:                      col, pfx = "#FFD700",     "WPT"
        elif "RECALC" in cmd:                        col, pfx = C["lc_red"],   "RECALC"
        elif "CLEAR" in cmd or "REACHED" in cmd:    col, pfx = C["lc_green"], "OK"
        else:                                        col, pfx = C["lc_green"], "FWD"

        msg  = f'<span style="color:{C["lc_dim"]};font-size:12px;">[{ts}]</span>&nbsp;'
        msg += f'<span style="color:{col};font-size:16px;font-weight:bold;">[{pfx}] {cmd}</span>'

        if "TURN" in cmd:
            pts = cmd.split("_")
            if len(pts) >= 3:
                msg += (f'<br><span style="color:#64748B;font-size:13px;">'
                        f'&nbsp;&nbsp;&nbsp;&nbsp;'
                        f'Current heading: <b style="color:{C["lc_text"]}">{d.get("heading",0):.1f} deg</b>'
                        f'  →  Turn {pts[1]} {pts[2]} deg  |  '
                        f'Speed: <b style="color:{C["lc_text"]}">{d.get("speed",0):.3f} m/s</b></span>')
        elif "OBSTACLE" in cmd or "PROXIMITY" in cmd:
            msg += (f'<br><span style="color:#64748B;font-size:13px;">'
                    f'&nbsp;&nbsp;&nbsp;&nbsp;'
                    f'Distance: <b style="color:{C["lc_amber"]}">{d.get("obstacle_dist",0):.2f} m</b>'
                    f'  |  Recalculating A* route...</span>')
        elif "WAYPOINT" in cmd:
            msg += (f'<br><span style="color:#64748B;font-size:13px;">'
                    f'&nbsp;&nbsp;&nbsp;&nbsp;'
                    f'Position: <b style="color:{C["lc_text"]}">'
                    f'{d.get("lat",0):.6f}, {d.get("lon",0):.6f}</b>'
                    f'  |  Computing next waypoint...</span>')

        msg += "<br>"
        self.nav_log.append(msg)
        sb = self.nav_log.verticalScrollBar(); sb.setValue(sb.maximum())

    def _log(self, txt, key="green"):
        col = {"green":C["lc_green"],"cyan":C["lc_cyan"],
               "amber":C["lc_amber"],"red":C["lc_red"],"dim":C["lc_dim"]}.get(key,C["lc_green"])
        self.nav_log.append(f'<span style="color:{col};font-size:14px;">{txt}</span>')

    def _start_demo(self):
        self.demo.t = 0; self.demo.battery = 92.0; self.demo.start()
        self._log("SYSTEM INITIALIZED  —  Demo mode active", "cyan")
        self._log("A* NAVIGATION ENGINE ready  (OccupancyGrid 50x50)", "cyan")
        self._log("MAP loaded  —  5 craters + static obstacles marked", "cyan")
        self._log("WAYPOINT sequence:  WP1 -> WP2 -> WP3", "cyan")
        self._log("─" * 48, "dim")

    def _tick_clk(self):
        self.clk.setText(datetime.utcnow().strftime("UTC  %Y-%m-%d  %H:%M:%S"))

    def closeEvent(self, e):
        self.demo.stop(); self.recv.stop(); e.accept()


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Lunar Rover GCS")
    w = Dashboard()
    w.show()
    sys.exit(app.exec())