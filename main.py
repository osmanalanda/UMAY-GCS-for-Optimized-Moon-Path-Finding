import sys, socket, json, math, threading, random, heapq
from datetime import datetime
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict
from enum import IntEnum

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QTextEdit, QFrame, QSplitter,
    QGroupBox, QLineEdit, QSpinBox, QComboBox, QProgressBar,
    QTabWidget, QStatusBar, QCheckBox, QSlider,
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QRectF, QPointF
from PySide6.QtGui import (
    QFont, QColor, QPainter, QPen, QBrush, QPainterPath,
    QRadialGradient, QLinearGradient,
)


# ── WebEngine — 3D Rover Viewer (opsiyonel, kurulu değilse devre dışı) ──
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtCore import QUrl
    import tempfile, os as _os
    _WEB_AVAILABLE = True
except ImportError:
    _WEB_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════════════
#  RENK PALETİ
# ═══════════════════════════════════════════════════════════════════════════════
# ──────────────────────────────────────────────────────────────────────────────
#  BATTLESPACE MILITARY THEME  —  tüm renk ve font tanımları
#  Orijinal: Battlespace Command Interface v5.0
#  Uyarlama: UMAY GCS Lunar Rover Navigation System
# ──────────────────────────────────────────────────────────────────────────────
C = {
    # ── Arka planlar — military dark olive ───────────────────────────────────
    "bg":        "#0F1208",   # ana sayfa — neredeyse siyah, hafif yeşil tonu
    "panel":     "#181C0A",   # kart/panel — koyu zeytinyağı
    "panel2":    "#202414",   # biraz daha açık panel
    "panel3":    "#282C1A",   # vurgulu panel arka planı
    "header":    "#0F1208",   # başlık — bg ile aynı, alt çizgi ayırt eder
    "input":     "#1A1E0E",   # input alanı
    # ── Vurgu renkleri — taktik altın + mavi ─────────────────────────────────
    "blue":      "#4A7AB8",   # mavi — taktik mavi
    "blue_dk":   "#183050",   # koyu mavi
    "blue_lt":   "#0A1422",   # mavi arka plan
    "cyan":      "#C8A830",   # GOLD — birincil vurgu (battlespace temasında altın)
    "cyan_dk":   "#7A6418",   # koyu altın
    "green":     "#6AA830",   # taktik yeşil — operational
    "green_dk":  "#3A6010",   # koyu yeşil
    "green_lt":  "#0E1808",   # yeşil arka plan
    "amber":     "#C07820",   # amber — uyarı
    "amber_dk":  "#7A4810",   # koyu amber
    "amber_lt":  "#1E1208",   # amber arka plan
    "red":       "#C03030",   # tehdit kırmızısı
    "red_dk":    "#6A1818",   # koyu kırmızı (border)
    "red_lt":    "#380808",   # kırmızı arka plan
    "purple":    "#78A8D8",   # intel mavi — intel/comms
    "purple_dk": "#183858",   # koyu intel mavi
    "purple_lt": "#0A1828",   # intel arka plan
    # ── Metin ────────────────────────────────────────────────────────────────
    "text":      "#DEDAD5",   # birincil metin — warm off-white
    "text2":     "#9A9470",   # ikincil metin — tanned
    "text3":     "#585438",   # soluk metin — olive shadow
    # ── Kenarlıklar ──────────────────────────────────────────────────────────
    "border":    "#363820",   # normal kenarlık — olive
    "border2":   "#4A4C28",   # biraz daha belirgin
    "border_hi": "#7A7840",   # vurgulu kenarlık
    # ── Log ekranı renkleri ───────────────────────────────────────────────────
    "log_bg":    "#0A0D04",
    "log_bg2":   "#080B04",
    "lc_text":   "#CECA98",   # log metin — field notes sarısı
    "lc_dim":    "#383A20",
    "lc_cyan":   "#C8A830",   # gold — komut rengi
    "lc_green":  "#6AA830",   # taktik yeşil
    "lc_amber":  "#C07820",   # amber uyarı
    "lc_red":    "#C03030",   # tehdit kırmızısı
    "lc_purple": "#78A8D8",   # intel mavi
}

SS = f"""
QMainWindow, QWidget {{
    background: {C['bg']};
    color: {C['text']};
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
}}
/* ── Panel çerçeveleri — sıfır köşe, askeri keskin hat ── */
QFrame#Card {{
    background: {C['panel']};
    border: 1px solid {C['border']};
    border-radius: 2px;
}}
QFrame#CardBlue  {{ background: {C['blue_lt']};   border: 1px solid {C['blue_dk']};   border-radius: 2px; }}
QFrame#CardGreen {{ background: {C['green_lt']};  border: 1px solid {C['green_dk']};  border-radius: 2px; }}
QFrame#CardAmber {{ background: {C['amber_lt']};  border: 1px solid {C['amber_dk']};  border-radius: 2px; }}
QFrame#CardRed   {{ background: {C['red_lt']};    border: 1px solid {C['red_dk']};    border-radius: 2px; }}
QFrame#CardPurple{{ background: {C['purple_lt']}; border: 1px solid {C['purple_dk']}; border-radius: 2px; }}
QFrame#Header    {{ background: {C['header']};    border-bottom: 2px solid {C['border_hi']}; }}
QFrame#ConnPanel {{ background: {C['panel2']};    border: 1px solid {C['border_hi']};  border-radius: 0px; }}
/* ── GroupBox — taktik section header stili ── */
QGroupBox {{
    background: {C['panel']}; border: 1px solid {C['border']};
    border-radius: 0px; margin-top: 16px;
    padding: 10px 8px 8px 8px;
    font-family: 'Consolas','Courier New',monospace;
    font-size: 10px; font-weight: bold;
    color: {C['text3']}; letter-spacing: 2px;
}}
QGroupBox::title {{
    subcontrol-origin: margin; left: 10px; padding: 0 5px;
    background: {C['panel2']}; color: {C['cyan']};
    font-family: 'Consolas','Courier New',monospace;
    font-size: 10px; font-weight: bold; letter-spacing: 3px;
}}
/* ── Telemetri büyük değer etiketleri ── */
QLabel#LBigG  {{ font-size:20px; font-weight:bold; color:{C['green']};  font-family:'Consolas',monospace; letter-spacing:1px; }}
QLabel#LBigA  {{ font-size:20px; font-weight:bold; color:{C['amber']};  font-family:'Consolas',monospace; letter-spacing:1px; }}
QLabel#LBigR  {{ font-size:20px; font-weight:bold; color:{C['red']};    font-family:'Consolas',monospace; letter-spacing:1px; }}
QLabel#LBigP  {{ font-size:20px; font-weight:bold; color:{C['purple']}; font-family:'Consolas',monospace; letter-spacing:1px; }}
QLabel#LBig   {{ font-size:20px; font-weight:bold; color:{C['text']};   font-family:'Consolas',monospace; letter-spacing:1px; }}
QLabel#LSmall {{ font-size:9px;  font-weight:bold; color:{C['text3']};
                 font-family:'Consolas',monospace; letter-spacing:3px; }}
/* ── Butonlar — köşesiz taktik stil ── */
QPushButton {{
    background: {C['panel2']}; color: {C['text2']};
    border: 1px solid {C['border_hi']}; border-radius: 0px;
    padding: 5px 16px; font-size: 11px; font-weight: bold;
    font-family: 'Consolas','Courier New',monospace; letter-spacing: 1px;
}}
QPushButton:hover {{ background: {C['panel3']}; color: {C['text']}; border-color: {C['text2']}; }}
QPushButton#BtnConn  {{ background:{C['green_dk']}; color:{C['green']}; border-color:{C['green_dk']}; padding:8px 24px; }}
QPushButton#BtnConn:hover  {{ background:#2A5010; color:#8ACA50; border-color:#4A8020; }}
QPushButton#BtnDisc  {{ background:{C['red_lt']}; color:{C['red']}; border-color:{C['red_dk']}; padding:8px 24px; }}
QPushButton#BtnDisc:hover  {{ background:{C['red_dk']}; color:#FF5050; }}
QPushButton#BtnClr   {{ background:{C['panel2']}; color:{C['text3']}; border-color:{C['border']};
                         padding:3px 10px; font-size:10px; }}
QPushButton#BtnAmber {{ background:{C['amber_lt']}; color:{C['amber']}; border-color:{C['amber_dk']};
                         padding:4px 12px; font-size:11px; font-weight:bold; border-radius:0px; }}
QPushButton#BtnAmber:hover {{ background:{C['amber_dk']}; color:{C['text']}; }}
QPushButton#BtnGreen {{ background:{C['green_lt']}; color:{C['green']}; border-color:{C['green_dk']};
                         padding:4px 12px; font-size:11px; font-weight:bold; border-radius:0px; }}
QPushButton#BtnGreen:hover {{ background:{C['green_dk']}; color:{C['text']}; }}
QPushButton#BtnRed   {{ background:{C['red_lt']}; color:{C['red']}; border-color:{C['red_dk']};
                         padding:4px 12px; font-size:11px; font-weight:bold; border-radius:0px; }}
QPushButton#BtnRed:hover   {{ background:{C['red_dk']}; color:{C['text']}; }}
/* ── Input alanları ── */
QLineEdit, QSpinBox, QComboBox {{
    background:{C['input']}; color:{C['text']};
    border:1px solid {C['border2']}; border-radius:0px;
    padding:5px 8px; font-size:12px;
    font-family:'Consolas','Courier New',monospace;
}}
QLineEdit:focus, QSpinBox:focus {{ border-color:{C['cyan']}; background:{C['panel2']}; }}
QComboBox::drop-down {{ border:none; width:20px; }}
QComboBox QAbstractItemView {{
    background:{C['panel2']}; color:{C['text']};
    border:1px solid {C['border2']}; selection-background-color:{C['blue_dk']};
    font-family:'Consolas','Courier New',monospace;
}}
/* ── CheckBox — taktik tick ── */
QCheckBox {{
    color:{C['text2']}; spacing:5px; font-size:11px;
    font-family:'Consolas','Courier New',monospace;
}}
QCheckBox::indicator {{
    width:13px; height:13px;
    border:1px solid {C['border2']}; border-radius:0px; background:{C['input']};
}}
QCheckBox::indicator:checked {{ background:{C['cyan']}; border-color:{C['border_hi']}; }}
/* ── Slider ── */
QSlider::groove:horizontal {{ background:{C['input']}; height:3px; border-radius:0px; }}
QSlider::handle:horizontal {{
    background:{C['cyan']}; width:12px; height:12px;
    margin:-5px 0; border-radius:0px;
    border:1px solid {C['border_hi']};
}}
QSlider::sub-page:horizontal {{ background:{C['cyan_dk']}; border-radius:0px; }}
/* ── Progress bar ── */
QProgressBar {{
    background:{C['input']}; border:1px solid {C['border']};
    border-radius:0px; font-size:1px;
}}
QProgressBar::chunk       {{ background:{C['green']}; border-radius:0px; }}
QProgressBar#pbA::chunk   {{ background:{C['amber']}; }}
QProgressBar#pbR::chunk   {{ background:{C['red']};   }}
/* ── Log ekranları — terminal yeşil ── */
QTextEdit#NavLog {{
    background:{C['log_bg2']}; color:{C['lc_text']}; border:none;
    font-family:'Consolas','Courier New',monospace; font-size:13px;
    padding:10px 12px; border-left:2px solid {C['border']};
}}
QTextEdit#TelLog {{
    background:{C['log_bg']}; color:{C['lc_text']}; border:none;
    font-family:'Consolas','Courier New',monospace; font-size:11px;
    padding:8px 10px;
}}
/* ── Tab widget — flat military ── */
QTabWidget::pane {{
    border:1px solid {C['border']};
    background:{C['panel']}; border-radius:0px;
}}
QTabBar::tab {{
    background:{C['bg']}; color:{C['text3']};
    border:1px solid {C['border']}; border-bottom:none;
    padding:7px 18px; font-size:11px; font-weight:bold;
    font-family:'Consolas','Courier New',monospace;
    letter-spacing:2px; border-radius:0px; margin-right:1px;
}}
QTabBar::tab:selected  {{
    background:{C['panel2']}; color:{C['cyan']};
    border-color:{C['cyan_dk']}; border-top:2px solid {C['cyan']};
}}
QTabBar::tab:hover:!selected {{ background:{C['panel2']}; color:{C['text2']}; }}
/* ── Status bar ── */
QStatusBar {{
    background:{C['panel']}; color:{C['text3']};
    font-size:10px; padding:2px 8px;
    font-family:'Consolas','Courier New',monospace; letter-spacing:1px;
    border-top:2px solid {C['border_hi']};
}}
/* ── Splitter ── */
QSplitter::handle {{ background:{C['border_hi']}; width:2px; }}
/* ── Scrollbar ── */
QScrollBar:vertical {{
    background:{C['panel']}; width:6px; border-radius:0px; margin:0;
}}
QScrollBar::handle:vertical {{
    background:{C['border2']}; border-radius:0px; min-height:20px;
}}
QScrollBar::handle:vertical:hover {{ background:{C['cyan']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
"""


# ═══════════════════════════════════════════════════════════════════════════════
#  LUNAR HAZARD TİPLERİ
# ═══════════════════════════════════════════════════════════════════════════════
class CellType(IntEnum):
    FREE       = 0
    CRATER     = 1
    BOULDER    = 2
    RIDGE      = 3
    SOFT_DUST  = 4   # toz — geçilebilir, yüksek maliyet
    SHADOW     = 5   # gölge — kamera kör, LiDAR aktif
    IMPASSABLE = 9

INF_COST = float('inf')
MAX_SLOPE_DEG  = 25.0
MAX_CRATER_D   = 0.8    # m
SHADOW_PENALTY = 5.0
DUST_PENALTY   = 3.0
GRID_RES_M     = 0.5    # m/hücre

CELL_RENDER_COLORS = {
    CellType.FREE:      QColor(18,  22,  8),    # koyu zeytinyağı — terrain
    CellType.CRATER:    QColor(80,  15,  15,  230),
    CellType.BOULDER:   QColor(100, 65,  10,  220),
    CellType.RIDGE:     QColor(60,  30,  90,  200),
    CellType.SOFT_DUST: QColor(70,  58,  8,   180),
    CellType.SHADOW:    QColor(8,   10,  30,  220),
    CellType.IMPASSABLE:QColor(70,  8,   8,   240),
}


# ═══════════════════════════════════════════════════════════════════════════════
#  LUNAR OCCUPANCY GRID  (OccupancyGrid + hazard katmanı birleşik)
# ═══════════════════════════════════════════════════════════════════════════════
class LunarOccupancyGrid:
    """
    50×50 ay yüzeyi haritası.
    Her hücre hem OccupancyGrid maliyeti hem de CellType taşır.
    D* Lite ve A* bu sınıfın cost() metodunu kullanır.
    Simscape'ten gelen engeller add_obstacle() ile eklenir.
    """
    GRID_SIZE      = 50
    OBSTACLE_RADIUS = 2

    def __init__(self, seed: int = 42):
        n = self.GRID_SIZE
        self.n = n
        self.ctype   = [[CellType.FREE] * n for _ in range(n)]
        self.slope   = [[0.0]           * n for _ in range(n)]
        self.height  = [[0.0]           * n for _ in range(n)]
        self.lum     = [[1.0]           * n for _ in range(n)]
        self.dust_cm = [[0.0]           * n for _ in range(n)]
        self.traf    = [[1.0]           * n for _ in range(n)]
        self._dynamic_obs: list = []   # Simscape'ten gelen (x_norm, y_norm)
        self._rng = random.Random(seed)
        self._generate(seed)

    # ── Prosedürel arazi üretimi ────────────────────────────────────────────
    def _generate(self, seed: int):
        rng = self._rng
        n   = self.n

        # Eğim katmanı
        for r in range(n):
            for c in range(n):
                sl = (
                    abs(math.sin(r*0.13+1.1) * math.cos(c*0.09+0.7)) * 20 +
                    abs(math.sin(r*0.31+2.3) * math.cos(c*0.27+1.1)) * 8
                )
                self.slope[r][c] = sl
                self.traf[r][c]  = max(0.3, 1.0 - sl/60.0)

        # Kraterler
        craters = [
            (22, 27, 4), (35, 12, 3), (7, 35, 4),
            (40, 38, 5), (15, 18, 2),
        ]
        for cx, cy, rad in craters:
            depth = rng.uniform(0.8, 2.0)
            for dr in range(-rad-2, rad+3):
                for dc in range(-rad-2, rad+3):
                    nr, nc = cy+dr, cx+dc
                    if not self._ib(nr, nc): continue
                    dist = math.sqrt(dr**2+dc**2)
                    if dist <= rad:
                        self.ctype[nr][nc]  = CellType.CRATER
                        self.height[nr][nc] = round(-depth*(1-dist/rad), 2)
                    elif dist <= rad+2:
                        self.slope[nr][nc] = max(self.slope[nr][nc], 35.0)
                        self.height[nr][nc] = depth*0.25

        # Kayalar/Boulder
        for _ in range(20):
            br = rng.randint(0, n-1); bc = rng.randint(0, n-1)
            if self.ctype[br][bc] == CellType.FREE:
                self.ctype[br][bc]  = CellType.BOULDER
                self.height[br][bc] = rng.uniform(0.5, 2.0)

        # Toz yamaları
        for _ in range(6):
            pr = rng.randint(0, n-1); pc = rng.randint(0, n-1)
            pr2 = rng.randint(2, 7)
            for dr in range(-pr2, pr2+1):
                for dc in range(-pr2, pr2+1):
                    nr, nc = pr+dr, pc+dc
                    if self._ib(nr,nc) and self.ctype[nr][nc] == CellType.FREE:
                        self.ctype[nr][nc]   = CellType.SOFT_DUST
                        self.dust_cm[nr][nc] = round(rng.uniform(5,20), 1)
                        self.traf[nr][nc]    = rng.uniform(0.3, 0.6)

        # Gölge şeritleri
        for _ in range(8):
            sr = rng.randint(0, n-1); sc = rng.randint(0, n-1)
            length = rng.randint(3, 10)
            for i in range(length):
                nr = sr+i
                if self._ib(nr, sc) and self.ctype[nr][sc] == CellType.FREE:
                    self.ctype[nr][sc] = CellType.SHADOW
                    self.lum[nr][sc]   = round(rng.uniform(0.0, 0.15), 2)

    def _ib(self, r: int, c: int) -> bool:
        return 0 <= r < self.n and 0 <= c < self.n

    # ── Maliyet hesabı (D*/A* için) ─────────────────────────────────────────
    def cell_cost(self, r: int, c: int) -> float:
        if not self._ib(r, c):
            return INF_COST
        ct = self.ctype[r][c]
        if ct in (CellType.CRATER, CellType.BOULDER,
                  CellType.RIDGE, CellType.IMPASSABLE):
            return INF_COST
        if self.slope[r][c] > MAX_SLOPE_DEG:
            return INF_COST
        cost = 1.0
        if ct == CellType.SHADOW:    cost *= SHADOW_PENALTY
        if ct == CellType.SOFT_DUST: cost *= 1.0 + self.dust_cm[r][c]/10.0
        sl = self.slope[r][c]
        if sl > 10.0:
            cost *= 1.0 + ((sl-10.0)/15.0)**2
        cost *= (2.0 - self.traf[r][c])
        return cost

    def is_passable(self, r: int, c: int) -> bool:
        return self.cell_cost(r, c) < INF_COST

    def add_obstacle(self, x_norm: float, y_norm: float):
        """Simscape'ten gelen normalize koordinat. (0-1 arası)"""
        gc = int(x_norm * self.n)
        gr = int(y_norm * self.n)
        r  = self.OBSTACLE_RADIUS
        for dr in range(-r, r+1):
            for dc in range(-r, r+1):
                nr, nc = gr+dr, gc+dc
                if self._ib(nr, nc):
                    dist = math.sqrt(dr**2+dc**2)
                    if dist <= r:
                        self.ctype[nr][nc]  = CellType.IMPASSABLE
                        self.slope[nr][nc]  = 0.0
                    else:
                        if self.ctype[nr][nc] == CellType.FREE:
                            self.ctype[nr][nc] = CellType.SOFT_DUST
                            self.traf[nr][nc]  = 0.4
        self._dynamic_obs.append((x_norm, y_norm))

    def clear_start_goal(self, positions: list):
        """Başlangıç ve hedef çevresini temizle."""
        for pos in positions:
            gr, gc = pos
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    nr, nc = gr+dr, gc+dc
                    if self._ib(nr, nc):
                        self.ctype[nr][nc]  = CellType.FREE
                        self.slope[nr][nc]  = 5.0
                        self.height[nr][nc] = 0.0

    # ── OccupancyGrid uyumlu API (eski kod için) ────────────────────────────
    @property
    def GRID_SIZE_COMPAT(self):
        return self.n

    def cost(self, col: int, row: int) -> float:
        return self.cell_cost(row, col)

    def is_free(self, col: int, row: int) -> bool:
        return self.is_passable(row, col)


# ═══════════════════════════════════════════════════════════════════════════════
#  LUNAR SENSOR SUITE
# ═══════════════════════════════════════════════════════════════════════════════
class LunarSensorSuite:
    """
    TUA aracının sensör paketi simülasyonu.
    LiDAR · IMU · Kamera · Termal sensör
    """
    def __init__(self, og: LunarOccupancyGrid, sensor_range: int = 4):
        self.og    = og
        self.range = sensor_range

    def scan(self, rover_r: int, rover_c: int) -> List[Tuple[Tuple[int,int], CellType]]:
        """
        Rover konumunu merkez alarak çevreyi tara.
        Yeni tehlike tespitleri döndür.
        Gerçek implementasyonda bu sensör verisi Simscape'ten gelir.
        """
        detections = []
        for dr in range(-self.range, self.range+1):
            for dc in range(-self.range, self.range+1):
                nr, nc = rover_r+dr, rover_c+dc
                if not self.og._ib(nr, nc):
                    continue
                ct = self.og.ctype[nr][nc]
                # LiDAR: krater derinliği
                if self.og.height[nr][nc] < -MAX_CRATER_D:
                    detections.append(((nr, nc), CellType.CRATER))
                # LiDAR: boulder yüksekliği
                elif self.og.height[nr][nc] > 0.5 and ct == CellType.FREE:
                    detections.append(((nr, nc), CellType.BOULDER))
                # IMU + LiDAR: eğim
                elif self.og.slope[nr][nc] > MAX_SLOPE_DEG and ct == CellType.FREE:
                    detections.append(((nr, nc), CellType.RIDGE))
                # Kamera: luminans (gölge tespiti)
                elif self.og.lum[nr][nc] < 0.15 and ct == CellType.FREE:
                    detections.append(((nr, nc), CellType.SHADOW))
                # Termal + görüntü: toz kalınlığı
                elif self.og.dust_cm[nr][nc] > 10.0 and ct == CellType.FREE:
                    detections.append(((nr, nc), CellType.SOFT_DUST))
        return detections

    def apply_detections(self, detections) -> bool:
        """Algılanan hücre tiplerini haritaya uygula. Değişim olduysa True döndür."""
        changed = False
        for (nr, nc), new_type in detections:
            if self.og.ctype[nr][nc] != new_type:
                self.og.ctype[nr][nc] = new_type
                changed = True
        return changed


# ═══════════════════════════════════════════════════════════════════════════════
#  A* PLANLAYICI
# ═══════════════════════════════════════════════════════════════════════════════
class AStarPlanner:
    """8-yönlü A* — OctileDistance heuristiği. Normalize (0-1) koordinatlar."""

    DIRS = [
        (0,1,1.0),(0,-1,1.0),(1,0,1.0),(-1,0,1.0),
        (1,1,1.414),(1,-1,1.414),(-1,1,1.414),(-1,-1,1.414),
    ]

    def __init__(self, og: LunarOccupancyGrid):
        self.og   = og
        self.path = []
        self.path_norm = []

    @staticmethod
    def heur(c1, r1, c2, r2) -> float:
        dr, dc = abs(r1-r2), abs(c1-c2)
        return max(dr,dc) + (math.sqrt(2)-1)*min(dr,dc)

    def plan(self, start_norm, goal_norm) -> list:
        n  = self.og.n
        sc = max(0, min(n-1, int(start_norm[0]*n)))
        sr = max(0, min(n-1, int(start_norm[1]*n)))
        gc = max(0, min(n-1, int(goal_norm[0]*n)))
        gr = max(0, min(n-1, int(goal_norm[1]*n)))

        if not self.og.is_free(sc, sr): sc, sr = self._nearest_free(sc, sr)
        if not self.og.is_free(gc, gr): gc, gr = self._nearest_free(gc, gr)

        open_heap = []
        heapq.heappush(open_heap, (self.heur(sc,sr,gc,gr), 0.0, sc, sr, None))
        g_score  = {(sc, sr): 0.0}
        came_from= {}
        visited  = set()

        while open_heap:
            f, g, col, row, parent = heapq.heappop(open_heap)
            if (col, row) in visited: continue
            visited.add((col, row))
            came_from[(col, row)] = parent
            if col == gc and row == gr:
                return self._reconstruct(came_from, gc, gr, n)
            for dc, dr, w in self.DIRS:
                nc, nr = col+dc, row+dr
                if not self.og.is_free(nc, nr): continue
                if (nc, nr) in visited: continue
                cc = self.og.cell_cost(nr, nc)
                if cc >= INF_COST: continue
                ng = g + w * cc
                if ng < g_score.get((nc,nr), INF_COST):
                    g_score[(nc,nr)] = ng
                    heapq.heappush(open_heap,
                        (ng + self.heur(nc,nr,gc,gr), ng, nc, nr, (col,row)))
        return []

    def _reconstruct(self, came_from, gc, gr, n):
        path = []
        node = (gc, gr)
        while node is not None:
            path.append(node)
            node = came_from.get(node)
        path.reverse()
        self.path = [(c, r) for c, r in path]
        self.path_norm = [(c/n, r/n) for c, r in path]
        return self.path_norm

    def _nearest_free(self, col, row):
        n = self.og.n
        for rad in range(1, 10):
            for dc in range(-rad, rad+1):
                for dr in range(-rad, rad+1):
                    nc, nr = col+dc, row+dr
                    if 0<=nc<n and 0<=nr<n and self.og.is_free(nc, nr):
                        return nc, nr
        return col, row

    def replan_needed(self, new_obstacles: list) -> bool:
        n = self.og.n
        for (ox_n, oy_n) in new_obstacles:
            oc = int(ox_n*n); or_ = int(oy_n*n)
            for (pc, pr) in self.path:
                if abs(pc-oc) <= 3 and abs(pr-or_) <= 3:
                    return True
        return False


# ═══════════════════════════════════════════════════════════════════════════════
#  D* LITE PLANLAYICI
# ═══════════════════════════════════════════════════════════════════════════════
class DStarLitePlanner:
    """
    D* Lite — Koenig & Likhachev (2002).
    Dinamik harita güncellemelerinde yalnızca etkilenen
    düğümleri yeniden hesaplar. A*'dan çok daha verimli.

    Kullanım:
        planner = DStarLitePlanner(og, start_grid, goal_grid)
        planner.compute_shortest_path()
        path = planner.extract_path()
        # Engel algılanınca:
        planner.update_obstacle(pos_grid, INF_COST)
        planner.km += planner.h(old_start, new_start)
        planner.start = new_start
        planner.compute_shortest_path()
        path = planner.extract_path()
    """
    def __init__(self, og: LunarOccupancyGrid,
                 start: Tuple[int,int], goal: Tuple[int,int]):
        self.og    = og
        self.start = start
        self.goal  = goal
        self.km    = 0.0
        self.g:   Dict[Tuple,float] = {}
        self.rhs: Dict[Tuple,float] = {}
        self._U:  list = []
        self._init_planner()

    def _h(self, a, b) -> float:
        dr, dc = abs(a[0]-b[0]), abs(a[1]-b[1])
        return max(dr,dc) + (math.sqrt(2)-1)*min(dr,dc)

    def _g(self, s)   -> float: return self.g.get(s, INF_COST)
    def _rhs(self, s) -> float: return self.rhs.get(s, INF_COST)

    def _key(self, s):
        mn = min(self._g(s), self._rhs(s))
        return (mn + self._h(self.start, s) + self.km, mn)

    def _key_lt(self, k1, k2) -> bool:
        return k1[0] < k2[0] or (k1[0] == k2[0] and k1[1] < k2[1])

    def _init_planner(self):
        self.rhs[self.goal] = 0.0
        heapq.heappush(self._U, (self._key(self.goal), self.goal))

    def _update_vertex(self, s):
        if s != self.goal:
            best = INF_COST
            for nr, nc, step in self._neighbors(s):
                cc = self.og.cell_cost(nr, nc)
                if cc < INF_COST:
                    best = min(best, step*cc + self._g((nr,nc)))
            self.rhs[s] = best
        if self._g(s) != self._rhs(s):
            heapq.heappush(self._U, (self._key(s), s))

    def _neighbors(self, s):
        r, c = s
        for dr, dc in [(0,1),(1,0),(0,-1),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]:
            nr, nc = r+dr, c+dc
            if self.og._ib(nr, nc):
                yield (nr, nc, math.sqrt(dr**2+dc**2))

    def compute_shortest_path(self):
        visited = set()
        iters   = 0
        max_iter = self.og.n * self.og.n * 4
        while self._U and iters < max_iter:
            iters += 1
            k_old, s = heapq.heappop(self._U)
            if s in visited: continue
            k_new = self._key(s)
            if self._key_lt(k_old, k_new):
                heapq.heappush(self._U, (k_new, s)); continue
            start_key = self._key(self.start)
            if not self._key_lt(k_old, start_key) and \
               self._rhs(self.start) == self._g(self.start):
                break
            visited.add(s)
            if self._g(s) > self._rhs(s):
                self.g[s] = self._rhs(s)
                for nr, nc, _ in self._neighbors(s):
                    self._update_vertex((nr, nc))
            else:
                self.g[s] = INF_COST
                self._update_vertex(s)
                for nr, nc, _ in self._neighbors(s):
                    self._update_vertex((nr, nc))

    def extract_path(self) -> Optional[List[Tuple[int,int]]]:
        path = [self.start]
        cur  = self.start
        seen = set()
        for _ in range(self.og.n * self.og.n):
            if cur == self.goal: return path
            if cur in seen:      return None
            seen.add(cur)
            best_cost = INF_COST
            best_next = None
            for nr, nc, step in self._neighbors(cur):
                cc = self.og.cell_cost(nr, nc)
                if cc < INF_COST:
                    total = step*cc + self._g((nr,nc))
                    if total < best_cost:
                        best_cost = total
                        best_next = (nr, nc)
            if best_next is None: return None
            cur = best_next
            path.append(cur)
        return None

    def update_obstacle(self, pos: Tuple[int,int]):
        """Yeni engel eklendiğinde ilgili düğümleri güncelle."""
        self._update_vertex(pos)
        for nr, nc, _ in self._neighbors(pos):
            self._update_vertex((nr, nc))

    def move_start(self, new_start: Tuple[int,int]):
        """Araç hareket ettiğinde başlangıç noktasını güncelle (km artışı ile)."""
        self.km    += self._h(self.start, new_start)
        self.start  = new_start


# ═══════════════════════════════════════════════════════════════════════════════
#  HİBRİT NAVİGATÖR  (D* Lite birincil, A* yedek)
# ═══════════════════════════════════════════════════════════════════════════════
class HybridNavigator:
    """
    Üst seviye navigasyon yöneticisi.
    D* Lite → başarısız olursa A* devreye girer.
    Sensor tespit → harita güncelleme → replan zincirini yönetir.
    """
    def __init__(self, og: LunarOccupancyGrid,
                 start_norm, goal_norm, use_dstar: bool = True):
        self.og         = og
        self.n          = og.n
        self.use_dstar  = use_dstar
        self.start_norm = start_norm
        self.goal_norm  = goal_norm

        # Grid koordinatlarına çevir
        self.start_g = self._to_grid(start_norm)
        self.goal_g  = self._to_grid(goal_norm)
        og.clear_start_goal([self.start_g, self.goal_g])

        # Planlayıcılar
        self.astar  = AStarPlanner(og)
        self.dstar  = DStarLitePlanner(og, self.start_g, self.goal_g)
        self.sensor = LunarSensorSuite(og, sensor_range=4)

        self.path_norm: List = []   # aktif normalize rota
        self.path_grid: List = []   # aktif grid rota
        self.rover_g   = self.start_g
        self.trajectory: List = [list(self.start_g)]
        self.stats = {
            'steps': 0, 'replans': 0, 'dstar_ok': 0,
            'astar_fallbacks': 0, 'hazards': 0,
        }
        self._last_replan_reason = ""

    def _to_grid(self, norm) -> Tuple[int,int]:
        return (
            max(0, min(self.n-1, int(norm[1]*self.n))),
            max(0, min(self.n-1, int(norm[0]*self.n))),
        )

    def _to_norm(self, grid) -> Tuple[float,float]:
        return (grid[1]/self.n, grid[0]/self.n)

    def initial_plan(self) -> bool:
        if self.use_dstar:
            self.dstar.compute_shortest_path()
            path_g = self.dstar.extract_path()
            if path_g:
                self.path_grid = path_g
                self.path_norm = [self._to_norm(p) for p in path_g]
                self.stats['dstar_ok'] += 1
                return True
        # A* fallback
        path_n = self.astar.plan(self.start_norm, self.goal_norm)
        if path_n:
            self.path_norm = path_n
            self.path_grid = self.astar.path
            self.stats['astar_fallbacks'] += 1
            return True
        return False

    def sensor_step(self) -> Tuple[bool, str]:
        """
        Sensör taraması yap → gerekirse replan.
        Döndürür: (replan_yapıldı_mı, sebep)
        """
        r, c = self.rover_g
        detections = self.sensor.scan(r, c)
        changed    = self.sensor.apply_detections(detections)

        if not changed:
            return False, ""

        new_hazards = [(self._to_norm((nr, nc)), ct)
                       for (nr, nc), ct in detections
                       if ct in (CellType.CRATER, CellType.BOULDER,
                                 CellType.RIDGE, CellType.IMPASSABLE)]
        self.stats['hazards'] += len(new_hazards)

        # Rota üzerinde engel var mı?
        for (nr, nc), _ in detections:
            for (pr, pc) in self.path_grid:
                if abs(pr-nr)<=2 and abs(pc-nc)<=2:
                    return self._replan("SENSOR — Rota üzerinde engel")

        return False, ""

    def _replan(self, reason: str) -> Tuple[bool, str]:
        self.stats['replans'] += 1
        self._last_replan_reason = reason

        if self.use_dstar:
            # D* Lite: start güncelle + yeniden hesapla
            self.dstar.move_start(self.rover_g)
            for (nr, nc), ct in [(p, self.og.ctype[p[0]][p[1]])
                                 for p in self.path_grid]:
                if ct in (CellType.CRATER, CellType.BOULDER,
                          CellType.RIDGE, CellType.IMPASSABLE):
                    self.dstar.update_obstacle((nr, nc))
            self.dstar.compute_shortest_path()
            path_g = self.dstar.extract_path()
            if path_g:
                self.path_grid = path_g
                self.path_norm = [self._to_norm(p) for p in path_g]
                self.stats['dstar_ok'] += 1
                return True, reason

        # A* fallback
        curr_norm = self._to_norm(self.rover_g)
        path_n = self.astar.plan(curr_norm, self.goal_norm)
        if path_n:
            self.path_norm = path_n
            self.path_grid = self.astar.path
            self.stats['astar_fallbacks'] += 1
            return True, f"{reason} [A* fallback]"
        return False, f"{reason} [YOL YOK]"

    def move_step(self) -> bool:
        """Bir adım ilerle. Başarılıysa True döndür."""
        if len(self.path_grid) < 2:
            return False
        if self.path_grid[0] == self.rover_g:
            self.path_grid.pop(0)
            if self.path_norm: self.path_norm.pop(0)
        if not self.path_grid:
            return False
        self.rover_g = self.path_grid[0]
        self.trajectory.append(list(self.rover_g))
        self.stats['steps'] += 1
        return True

    def is_done(self) -> bool:
        r, c = self.rover_g
        gr, gc = self.goal_g
        return abs(r-gr) <= 1 and abs(c-gc) <= 1

    def set_goal(self, x_norm: float, y_norm: float):
        """
        Hedef noktayı (OSCAR) güncelle ve rotayı yeniden hesapla.
        x_norm, y_norm: 0-1 arası normalize koordinat.
        """
        new_goal_g = self._to_grid((x_norm, y_norm))
        # Yeni hedef geçerli ve geçilebilir mi kontrol et
        nr, nc = new_goal_g
        if not self.og._ib(nr, nc):
            return False
        self.goal_g    = new_goal_g
        self.goal_norm = (x_norm, y_norm)
        self.og.clear_start_goal([new_goal_g])
        # D* Lite yeniden başlat — hedef değişti
        self.dstar = DStarLitePlanner(self.og, self.rover_g, self.goal_g)
        ok, _ = self._replan("OSCAR yeniden konuşlandı")
        return ok

    def add_external_obstacle(self, x_norm: float, y_norm: float):
        """Simscape'ten gelen engeli haritaya ekle ve replan tetikle."""
        self.og.add_obstacle(x_norm, y_norm)
        if self.use_dstar:
            obs_g = self._to_grid((x_norm, y_norm))
            self.dstar.update_obstacle(obs_g)
        self._replan(f"Simscape engel ({x_norm:.2f},{y_norm:.2f})")

    def summary(self) -> str:
        dist = self.stats['steps'] * GRID_RES_M
        return (f"{dist:.1f}m | {self.stats['replans']} replan | "
                f"D*:{self.stats['dstar_ok']} A*:{self.stats['astar_fallbacks']} | "
                f"{self.stats['hazards']} tehlike")

    def direction_hint(self) -> str:
        if len(self.path_grid) < 2:
            return "HEDEFE ULAŞILDI"
        r0, c0 = self.rover_g
        r1, c1 = self.path_grid[1] if len(self.path_grid) > 1 else self.goal_g
        dr, dc = r1-r0, c1-c0
        angle  = math.degrees(math.atan2(dc, -dr)) % 360
        comp   = ["KUZEY","KUZEYDOĞU","DOĞU","GÜNEYDOĞU",
                  "GÜNEY","GÜNEYBATI","BATI","KUZEYBATI"]
        idx    = int((angle+22.5)/45) % 8
        return f"{comp[idx]}  {angle:.1f}°  —  {'D*' if self.use_dstar else 'A*'} AKTİF"


# ═══════════════════════════════════════════════════════════════════════════════
#  SIMULINK / SIMSCAPE ALICI
# ═══════════════════════════════════════════════════════════════════════════════
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
                        data, _ = self.sock.recvfrom(8192)
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

    @staticmethod
    def test_connection(host, port, protocol) -> bool:
        try:
            if protocol == "TCP":
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2.0); s.connect((host, port)); s.close()
                return True
            else:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(1.5)
                s.sendto(json.dumps({"ping": True}).encode(), (host, port))
                if host in ("127.0.0.1", "localhost"):
                    try:
                        s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        s2.bind((host, port)); s2.close(); s.close()
                        return True
                    except OSError:
                        s.close(); return True
                s.close(); return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False


# ═══════════════════════════════════════════════════════════════════════════════
#  DEMO VERİ ÜRETECİ
# ═══════════════════════════════════════════════════════════════════════════════
class DemoGen(QObject):
    data_ready = Signal(dict)

    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.timer.timeout.connect(self._gen)
        self.t = 0
        self.battery = 92.0
        self.lat = 0.00210; self.lon = 0.00340
        self.heading = 90.0
        self.scenario = {
            5:  ("OBSTACLE_DETECTED", "⚠ ENGEL TESPİT EDİLDİ — mesafe: 3.2 m"),
            8:  ("RECALCULATING",     "◈ ROTA YENİDEN HESAPLANIYOR — D* Lite aktif"),
            11: ("TURN_NORTH_45",     "↺ KUZEY'E 45° DÖN"),
            16: ("MOVE_FORWARD",      "→ İLERLE — 4.1 m düz hat"),
            22: ("CRATER_PROXIMITY",  "⚠ KRATER YAKINI — sağ: 1.8 m — gölge bölge"),
            25: ("TURN_EAST_30",      "↺ DOĞU'YA 30° DÖN"),
            30: ("SLOPE_WARNING",     "▲ EĞİM UYARISI — %18 — hız azalt"),
            34: ("SPEED_REDUCE",      "▼ HIZ AZALT  0.15 m/s — toz yamağı"),
            40: ("DUST_PATCH_CLEAR",  "✓ TOZ YAMAĞI SERBEST — rota temiz"),
            44: ("MOVE_FORWARD",      "→ İLERLE — hedefe 12.3 m kaldı"),
            52: ("WAYPOINT_REACHED",  "★ WAYPOINT-1 ULAŞILDI"),
            56: ("TURN_WEST_60",      "↺ BATI'YA 60° DÖN"),
            62: ("OBSTACLE_DETECTED", "⚠ ENGEL TESPİT EDİLDİ — mesafe: 2.1 m"),
            65: ("SHADOW_ENTER",      "◐ GÖLGE BÖLGESİ — kamera kör — LiDAR aktif"),
            70: ("MOVE_FORWARD",      "→ İLERLE — alternatif rota aktif"),
            78: ("SHADOW_EXIT",       "☀ GÖLGE ÇIKIŞI — kamera yeniden aktif"),
            84: ("BOULDER_AVOID",     "⊘ BOULDER KAÇINIM — rota güncellendi"),
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
        elif "REDUCE" in status or "DUST" in status: spd = 0.12
        elif "SHADOW" in status: spd = 0.15
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
            "dust_level":    round(max(0, 30 + math.sin(self.t*0.15)*25), 1),
            "obstacles":     self._demo_obstacles(),
        })

    def _demo_obstacles(self):
        if self.t in (5, 22, 62):
            x = 0.3 + random.uniform(0, 0.4)
            y = 0.3 + random.uniform(0, 0.4)
            return [{"x": round(x,3), "y": round(y,3)}]
        return []


# ═══════════════════════════════════════════════════════════════════════════════
#  HARİTA CANVAS  —  Lunar Hazard görselleştirmesi + D*/A* rota
# ═══════════════════════════════════════════════════════════════════════════════
class LunarMapCanvas(QWidget):
    """
    Tam lunar haritası widget'ı.
    - CellType renk kodlaması
    - D* Lite / A* rota görselleştirmesi
    - Rover izi ve anten animasyonu
    - Sensör menzili halkası
    - Gölge katmanı toggle
    - Tıkla-engel-ekle özelliği
    - Waypoint sırası yönetimi
    """
    replan_signal   = Signal(str)    # replan logu için
    obstacle_signal = Signal(float, float)  # yeni engel koordinatları

    START_NORM = (0.05, 0.05)
    GOAL_NORM  = (0.92, 0.92)

    def __init__(self):
        super().__init__()
        self.setMinimumSize(360, 360)
        self.setCursor(Qt.CrossCursor)

        # Harita ve navigatör
        self.og  = LunarOccupancyGrid(seed=42)
        self.nav = HybridNavigator(self.og, self.START_NORM, self.GOAL_NORM,
                                   use_dstar=True)

        # Görselleştirme durumu
        self.show_shadows   = True
        self.show_sensor_ring = True
        self.show_cost_overlay= True
        self.sensor_range   = 4
        self.trail          = deque(maxlen=150)
        self.replan_markers = []   # replan yapılan noktalar
        self.anim_tick      = 0

        # İlk plan
        ok = self.nav.initial_plan()
        if ok:
            dir_h = self.nav.direction_hint()
            self.replan_signal.emit(f"✦ İLK ROTA  {dir_h}  ({len(self.nav.path_grid)} adım)")

        # Render zamanlayıcı (animasyon için)
        self._anim_t = QTimer(self)
        self._anim_t.timeout.connect(self._tick_anim)
        self._anim_t.start(80)

        # Hareket durumu
        self.paused      = False
        self._move_accum = 0.0   # sub-step birikimi (yavaş hız için)
        self.move_speed  = 1.0   # 0.1 – 5.0 arası çarpan

    def _tick_anim(self):
        self.anim_tick += 1
        self.update()

    # ── Hız / Duraklatma API ────────────────────────────────────────────────
    def set_move_speed(self, value: float):
        """value: 0.1 – 5.0 arası hız çarpanı."""
        self.move_speed = max(0.1, min(5.0, value))

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def toggle_pause(self) -> bool:
        self.paused = not self.paused
        return self.paused

    def reset_route(self):
        """Sadece aracı, izi ve rotayı sıfırla — harita engelleri korunur."""
        self.nav.rover_g    = self.nav.start_g
        self.nav.trajectory = [list(self.nav.start_g)]
        self.nav.path_grid  = []
        self.nav.path_norm  = []
        self.nav.stats      = {k: 0 for k in self.nav.stats}
        self.trail          = deque(maxlen=150)
        self.replan_markers = []
        self._move_accum    = 0.0
        self.paused         = False
        # Yeni D* Lite örneği
        self.nav.dstar = DStarLitePlanner(
            self.og, self.nav.start_g, self.nav.goal_g)
        ok = self.nav.initial_plan()
        dir_h = self.nav.direction_hint() if ok else "YOL BULUNAMADI"
        self.replan_signal.emit(f"↺ ROTA SIFIRLANDI  {dir_h}  ({len(self.nav.path_grid)} adım)")

    def full_reset(self):
        """Haritayı, engelleri, aracı ve rotayı tamamen sıfırla."""
        self.og  = LunarOccupancyGrid(seed=42)
        self.nav = HybridNavigator(self.og, self.START_NORM, self.GOAL_NORM,
                                   use_dstar=self.nav.use_dstar)
        self.nav.sensor = LunarSensorSuite(self.og, sensor_range=self.sensor_range)
        self.trail          = deque(maxlen=150)
        self.replan_markers = []
        self._move_accum    = 0.0
        self.paused         = False
        ok = self.nav.initial_plan()
        dir_h = self.nav.direction_hint() if ok else "YOL BULUNAMADI"
        self.replan_signal.emit(
            f"⟳ TAM SIFIRLAMA  Harita yenilendi  {dir_h}  ({len(self.nav.path_grid)} adım)")

    def set_algo(self, use_dstar: bool):
        self.nav.use_dstar = use_dstar
        ok = self.nav.initial_plan()
        algo = "D* Lite" if use_dstar else "A*"
        self.replan_signal.emit(f"⟳ ALGORİTMA DEĞİŞTİ → {algo}  ({len(self.nav.path_grid)} adım)")

    def set_sensor_range(self, val: int):
        self.sensor_range = val
        self.nav.sensor.range = val

    def toggle_shadows(self, on: bool):
        self.show_shadows = on

    def toggle_sensor_ring(self, on: bool):
        self.show_sensor_ring = on

    def toggle_cost_overlay(self, on: bool):
        self.show_cost_overlay = on

    def update_rover(self, data: dict):
        """Demo/Simscape verisini alarak haritayı güncelle."""
        if self.paused:
            return

        for obs in data.get("obstacles", []):
            ox, oy = obs.get("x", 0.0), obs.get("y", 0.0)
            prev_path = list(self.nav.path_grid)
            self.nav.add_external_obstacle(ox, oy)
            if self.nav.path_grid != prev_path:
                dir_h = self.nav.direction_hint()
                self.replan_signal.emit(
                    f"⚠ SİMSCAPE ENGELİ ({ox:.2f},{oy:.2f}) → {dir_h}")
                self.replan_markers.append(tuple(self.nav.rover_g))

        replanned, reason = self.nav.sensor_step()
        if replanned:
            dir_h = self.nav.direction_hint()
            self.replan_signal.emit(f"◈ REPLAN [{reason}] → {dir_h}")
            self.replan_markers.append(tuple(self.nav.rover_g))

        spd = data.get("speed", 0.0)
        if spd > 0.05 and self.nav.path_norm and len(self.nav.path_norm) > 1:
            self._move_accum += self.move_speed
            steps = int(self._move_accum)
            self._move_accum -= steps
            for _ in range(max(1, steps)):
                if len(self.nav.path_norm) > 1:
                    self.nav.move_step()
                    self.trail.append(QPointF(*self._to_px_norm(
                        self.nav.path_norm[0] if self.nav.path_norm
                        else self.NAV_NORM_POS)))

        # Hedefe ulaşıldı mı kontrol et
        if self.nav.is_done():
            self.replan_signal.emit("★ HEDEF NOKTA ULAŞILDI — OBJ SECURED")

    @property
    def NAV_NORM_POS(self):
        r, c = self.nav.rover_g
        return (c/self.og.n, r/self.og.n)

    def mousePressEvent(self, event):
        """Tıkla → OSCAR (hedef) noktasını yeni konuma taşı ve replan tetikle."""
        w, h = self.width(), self.height()
        xn = event.position().x() / w
        yn = event.position().y() / h
        if 0 < xn < 1 and 0 < yn < 1:
            ok = self.nav.set_goal(xn, yn)
            if ok:
                gx, gy = self.nav.goal_g
                self.replan_signal.emit(
                    f"◎ OSCAR YENİDEN KONUŞLANDI → ({xn:.2f},{yn:.2f}) "
                    f"grid:({gx},{gy})  {self.nav.direction_hint()}")
            else:
                self.replan_signal.emit(
                    f"✗ OSCAR geçersiz konum ({xn:.2f},{yn:.2f}) — impassable")

    def _to_px_norm(self, norm):
        return (norm[0]*self.width(), norm[1]*self.height())

    def _to_px_grid(self, r, c):
        n = self.og.n
        return (c/n*self.width(), r/n*self.height())

    # ── paintEvent — ASKERİ RADAR GÖRÜNÜMÜ ──────────────────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        n    = self.og.n
        cw   = w / n
        ch   = h / n

        # ══ KATMAN 0: Radar arka planı ═══════════════════════════════════════
        p.fillRect(0, 0, w, h, QColor(3, 7, 1))

        # Koyu vinyette — sabit ekran merkezi
        vign = QRadialGradient(w//2, h//2, max(w,h)*0.75)
        vign.setColorAt(0.0, QColor(0,0,0,0))
        vign.setColorAt(1.0, QColor(0,0,0,200))
        p.setBrush(QBrush(vign)); p.setPen(Qt.NoPen)
        p.drawRect(0, 0, w, h)

        # ══ KATMAN 1: Radar — araç merkezli ══════════════════════════════════
        # Radar merkezi = rover'ın anlık piksel konumu
        _rnx, _rny = self.NAV_NORM_POS
        cx = int(_rnx * w)
        cy = int(_rny * h)
        # Yarıçap: haritanın ~%30'u — ekrandan taşmasın
        max_r = min(w, h) * 0.30
        for ring in range(1, 6):
            r_px = int(max_r * ring / 5)
            alpha = 55 + ring * 15
            p.setPen(QPen(QColor(25, 60, 15, alpha), 0.5))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(cx-r_px, cy-r_px, r_px*2, r_px*2)
            p.setFont(QFont("Consolas", 7))
            p.setPen(QColor(40, 80, 20, 130))
            dist_m = int(ring * n * 0.5 / 5)
            p.drawText(cx + r_px + 3, cy - 2, f"{dist_m}m")

        # Radar tarama çizgileri
        p.setPen(QPen(QColor(25, 55, 12, 45), 0.3))
        for angle_deg in range(0, 360, 30):
            rad = math.radians(angle_deg)
            x2 = int(cx + max_r * math.cos(rad))
            y2 = int(cy + max_r * math.sin(rad))
            p.drawLine(cx, cy, x2, y2)

        # Dönen sweep ışını
        sweep_angle = (self.anim_tick * 3) % 360
        sweep_rad   = math.radians(sweep_angle)
        sweep_path  = QPainterPath()
        sweep_path.moveTo(cx, cy)
        span = 20
        for da in range(0, span + 1, 2):
            a = math.radians(sweep_angle - da)
            fade = (1.0 - da / span)
            px_ = int(cx + max_r * math.cos(a))
            py_ = int(cy + max_r * math.sin(a))
            sweep_path.lineTo(px_, py_)
        sweep_path.closeSubpath()
        p.setBrush(QBrush(QColor(50, 160, 25, 20)))
        p.setPen(Qt.NoPen)
        p.drawPath(sweep_path)
        # Sweep ana çizgisi
        p.setPen(QPen(QColor(70, 210, 35, 150), 1.0))
        x2 = int(cx + max_r * math.cos(sweep_rad))
        y2 = int(cy + max_r * math.sin(sweep_rad))
        p.drawLine(cx, cy, x2, y2)

        # ══ KATMAN 2: Arazi tehlike hücreleri ════════════════════════════════
        for r in range(n):
            for c in range(n):
                ct = self.og.ctype[r][c]
                if ct == CellType.SHADOW and not self.show_shadows:
                    ct = CellType.FREE
                if ct == CellType.FREE:
                    if self.show_cost_overlay:
                        sl = self.og.slope[r][c]
                        if sl > 15:
                            alpha = int(min(110, (sl - 15) * 5))
                            p.fillRect(int(c*cw), int(r*ch),
                                       max(1,int(cw)+1), max(1,int(ch)+1),
                                       QColor(30, 65, 15, alpha))
                    continue
                col_map = {
                    CellType.CRATER:    QColor(170,  35,  18, 195),
                    CellType.BOULDER:   QColor(150, 115,  18, 185),
                    CellType.RIDGE:     QColor( 95,  55, 155, 175),
                    CellType.SOFT_DUST: QColor(115,  95,  18, 155),
                    CellType.SHADOW:    QColor( 18,  18,  75, 195),
                    CellType.IMPASSABLE:QColor(155,  18,  18, 215),
                }
                col = col_map.get(ct, QColor(35, 70, 15, 75))
                p.fillRect(int(c*cw), int(r*ch),
                           max(1,int(cw)+1), max(1,int(ch)+1), col)

        # ══ KATMAN 3: Koordinat ızgara ════════════════════════════════════════
        p.setPen(QPen(QColor(25, 55, 12, 60), 0.3))
        step = max(1, n // 8)
        for i in range(0, n + 1, step):
            p.drawLine(int(i*cw), 0, int(i*cw), h)
            p.drawLine(0, int(i*ch), w, int(i*ch))

        def px(xn, yn): return QPointF(xn*w, yn*h)

        # ══ KATMAN 4: D*/A* rota ═════════════════════════════════════════════
        pn = self.nav.path_norm
        if len(pn) > 1:
            pts = [px(x, y) for x, y in pn]
            pen = QPen(QColor(55, 190, 38, 155), 1.2)
            pen.setDashPattern([4, 3])
            p.setPen(pen)
            for i in range(1, len(pts)):
                p.drawLine(pts[i-1], pts[i])
            p.setBrush(QBrush(QColor(55, 190, 38, 95)))
            p.setPen(Qt.NoPen)
            for i, (xn, yn) in enumerate(pn):
                if i % 5 == 0:
                    p.drawRect(int(xn*w)-2, int(yn*h)-2, 4, 4)

        # ══ KATMAN 5: Rover izi ═══════════════════════════════════════════════
        traj = self.nav.trajectory
        if len(traj) > 1:
            for i in range(1, len(traj)):
                r0, c0 = traj[i-1]; r1, c1 = traj[i]
                a = int(5 + 150 * i / len(traj))
                p.setPen(QPen(QColor(35, 150, 25, a), 1.4))
                p.drawLine(QPointF(c0/n*w, r0/n*h), QPointF(c1/n*w, r1/n*h))

        # ══ KATMAN 6: Replan noktaları ════════════════════════════════════════
        for (rr, rc) in self.replan_markers[-15:]:
            pp = QPointF(rc/n*w, rr/n*h)
            p.setBrush(QBrush(QColor(190, 155, 18, 195)))
            p.setPen(Qt.NoPen)
            p.drawRect(int(pp.x())-3, int(pp.y())-3, 6, 6)

        # ══ KATMAN 7: Dinamik engel blipleri ══════════════════════════════════
        for (ox, oy) in self.og._dynamic_obs[-30:]:
            op = px(ox, oy)
            blip_a = int(abs(math.sin(self.anim_tick * 0.2)) * 95 + 115)
            p.setBrush(QBrush(QColor(190, 38, 38, blip_a)))
            p.setPen(QPen(QColor(245, 55, 55, 175), 0.8))
            p.drawRect(int(op.x())-5, int(op.y())-5, 10, 10)
            p.drawLine(int(op.x())-8, int(op.y()), int(op.x())+8, int(op.y()))
            p.drawLine(int(op.x()), int(op.y())-8, int(op.x()), int(op.y())+8)

        # ══ KATMAN 8: Sensör menzil halkası ══════════════════════════════════
        if self.show_sensor_ring:
            xn, yn = self.NAV_NORM_POS
            rp = px(xn, yn)
            sr_px = self.sensor_range * (w / n)
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(QColor(55, 175, 28, 75), 0.7))
            p.drawEllipse(rp, sr_px, sr_px)
            p.setPen(QPen(QColor(55, 175, 28, 35), 0.4))
            p.drawEllipse(rp, sr_px * 0.65, sr_px * 0.65)

        # ══ KATMAN 9: Rover ══════════════════════════════════════════════════
        xn, yn = self.NAV_NORM_POS
        rp = px(xn, yn)
        r0, c0 = self.nav.rover_g
        heading = 0.0
        if len(self.nav.path_grid) > 1:
            r1, c1 = self.nav.path_grid[1]
            heading = math.degrees(math.atan2(c1 - c0, -(r1 - r0)))

        pulse_r = int(11 + abs(math.sin(self.anim_tick * 0.12)) * 5)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(70, 210, 35, 55), 0.7))
        p.drawEllipse(rp, pulse_r, pulse_r)

        p.save(); p.translate(rp); p.rotate(heading)
        body = QPainterPath()
        body.moveTo(0, -12); body.lineTo(-7, 7); body.lineTo(0, 3); body.lineTo(7, 7)
        body.closeSubpath()
        p.setBrush(QBrush(QColor(35, 150, 25, 215)))
        p.setPen(QPen(QColor(110, 245, 75), 1.4))
        p.drawPath(body)
        dome_p = abs(math.sin(self.anim_tick * 0.15)) * 0.5 + 0.5
        p.setBrush(QBrush(QColor(175, 245, 95, int(220 * dome_p))))
        p.setPen(Qt.NoPen)
        p.drawRect(-2, -14, 5, 5)
        p.restore()

        # ══ KATMAN 10: LIMA (başlangıç) ve OSCAR (hedef) markerları ══════════
        sp = px(*self.START_NORM)
        p.setBrush(QBrush(QColor(18, 55, 130, 175)))
        p.setPen(QPen(QColor(75, 135, 230), 1.4))
        p.drawRect(int(sp.x())-6, int(sp.y())-6, 12, 12)
        p.setFont(QFont("Consolas", 7, QFont.Bold))
        p.setPen(QColor(75, 135, 230))
        p.drawText(int(sp.x())+9, int(sp.y())+4, "LIMA")

        gp = px(*self.nav.goal_norm)   # dinamik — tıklamayla güncellenir
        goal_p = abs(math.sin(self.anim_tick * 0.07)) * 0.5 + 0.5
        p.setBrush(QBrush(QColor(155, 18, 18, int(175 * goal_p))))
        p.setPen(QPen(QColor(215, 55, 55), 1.8))
        p.drawRect(int(gp.x())-8, int(gp.y())-8, 16, 16)
        p.setPen(QPen(QColor(215, 55, 55, int(215 * goal_p)), 1.4))
        p.drawLine(int(gp.x())-5, int(gp.y())-5, int(gp.x())+5, int(gp.y())+5)
        p.drawLine(int(gp.x())+5, int(gp.y())-5, int(gp.x())-5, int(gp.y())+5)
        p.setFont(QFont("Consolas", 7, QFont.Bold))
        p.setPen(QColor(215, 55, 55))
        p.drawText(int(gp.x())+11, int(gp.y())+4, "OSCAR")

        # ══ KATMAN 11: HUD alt çubuğu ════════════════════════════════════════
        algo_str  = "D*LITE" if self.nav.use_dstar else "A*"
        stat_str  = "HOLD" if self.paused else "MOVE"
        gr, gc    = self.nav.goal_g; rr2, cc2 = self.nav.rover_g
        dist_m    = math.sqrt((gr - rr2)**2 + (gc - cc2)**2) * 0.5
        info = (f"ALG:{algo_str}  STATUS:{stat_str}  SPD:{self.move_speed:.1f}x  "
                f"DIST:{dist_m:.0f}m  OBS:{len(self.og._dynamic_obs)}  "
                f"RTE:{len(self.nav.path_norm)}  REPLAN:{self.nav.stats['replans']}")
        p.fillRect(0, h - 16, w, 16, QColor(1, 4, 0, 225))
        p.setPen(QColor(50, 105, 25))
        p.setFont(QFont("Consolas", 8))
        p.drawText(4, h - 4, info)

        # ══ KATMAN 12: Lejant ═════════════════════════════════════════════════
        lx, ly = w - 142, 8
        p.fillRect(lx - 5, ly - 5, 147, 120, QColor(1, 4, 0, 215))
        p.setPen(QPen(QColor(35, 70, 15, 140), 0.5))
        p.drawRect(lx - 5, ly - 5, 147, 120)
        p.setFont(QFont("Consolas", 8))
        legend = [
            (QColor(170,  35, 18), "CRATER"),
            (QColor(150, 115, 18), "BOULDER"),
            (QColor( 95,  55,155), "RIDGE"),
            (QColor(115,  95, 18), "DUST ZONE"),
            (QColor( 18,  18, 75), "SHADOW"),
            (QColor( 55, 190, 38), "NAV ROUTE"),
            (QColor( 35, 150, 25), "TRAIL"),
        ]
        for i, (col, lbl) in enumerate(legend):
            p.fillRect(lx, ly + i*15, 10, 9, col)
            p.setPen(QColor(55, 110, 28))
            p.drawText(lx + 14, ly + i*15 + 9, lbl)

        # ══ KATMAN 13: Hız göstergesi ════════════════════════════════════════
        spd_str = f"SPD {self.move_speed:.1f}x"
        if self.move_speed < 0.5:
            spd_col = QColor(38, 115, 195)
        elif self.move_speed > 3.0:
            spd_col = QColor(195, 38, 38)
        elif self.move_speed > 1.5:
            spd_col = QColor(195, 125, 18)
        else:
            spd_col = QColor(55, 175, 38)
        p.fillRect(4, h - 32, 80, 14, QColor(1, 4, 0, 225))
        p.setPen(spd_col)
        p.setFont(QFont("Consolas", 8, QFont.Bold))
        p.drawText(6, h - 21, spd_str)

        # ══ KATMAN 14: HOLD overlay ═══════════════════════════════════════════
        if self.paused:
            p.fillRect(0, 0, w, h, QColor(0, 0, 0, 135))
            pulse = abs(math.sin(self.anim_tick * 0.08)) * 60 + 155
            box_w, box_h = 195, 48
            bx = (w - box_w) // 2
            by = (h - box_h) // 2
            p.fillRect(bx, by, box_w, box_h, QColor(1, 4, 0, 248))
            p.setPen(QPen(QColor(55, 195, 28, int(pulse)), 1.4))
            p.drawRect(bx, by, box_w, box_h)
            p.setPen(QPen(QColor(55, 195, 28, int(pulse * 0.3)), 0.5))
            p.drawRect(bx + 3, by + 3, box_w - 6, box_h - 6)
            p.setPen(QColor(55, 195, 28, int(pulse)))
            p.setFont(QFont("Consolas", 14, QFont.Bold))
            p.drawText(bx, by, box_w, box_h, Qt.AlignCenter, "[ HOLD ]")



# ═══════════════════════════════════════════════════════════════════════════════
#  SİMÜLASYON FEED WIDGET
# ═══════════════════════════════════════════════════════════════════════════════
class SimFeed(QWidget):
    """
    Simülasyon Feed — üstten çekim videosu oynatıcısı.
    PySide6.QtMultimedia kullanır (pip install PySide6 ile gelir).
    Video: UsttenVideo.mp4  |  Kontroller: Play/Pause · döngü · tam ekran
    """

    VIDEO_PATH = r"C:\Users\aland\OneDrive\Masaüstü\TUA_AstroHackathon\ArkadanVideo.mp4"

    def __init__(self):
        super().__init__()
        self.data = {}   # update_data uyumu için
        vl = QVBoxLayout(self)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)

        # ── Başlık ────────────────────────────────────────────────────────
        hdr = QFrame()
        hdr.setStyleSheet(
            f"background:{C['panel2']};border-bottom:1px solid {C['border_hi']};"
            f"border-top:2px solid {C['cyan']};")
        hdr.setFixedHeight(28)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(10, 0, 10, 0)
        t = QLabel("SIM FEED  //  AERIAL VIEW")
        t.setFont(QFont("Consolas", 10, QFont.Bold))
        t.setStyleSheet(f"color:{C['cyan']};letter-spacing:3px;background:transparent;")
        hl.addWidget(t); hl.addStretch()
        self._status_lbl = QLabel("STANDBY")
        self._status_lbl.setFont(QFont("Consolas", 9))
        self._status_lbl.setStyleSheet(
            f"color:{C['amber']};letter-spacing:2px;background:transparent;")
        hl.addWidget(self._status_lbl)
        vl.addWidget(hdr)

        # ── Video ya da fallback ───────────────────────────────────────────
        try:
            from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
            from PySide6.QtMultimediaWidgets import QVideoWidget
            from PySide6.QtCore import QUrl

            self._player = QMediaPlayer(self)
            self._audio  = QAudioOutput(self)
            self._audio.setVolume(0.0)          # sessiz — sadece görüntü
            self._player.setAudioOutput(self._audio)

            self._video_w = QVideoWidget()
            self._video_w.setStyleSheet("background:#000;")
            self._player.setVideoOutput(self._video_w)
            vl.addWidget(self._video_w, 1)

            # Kontrol çubuğu
            ctrl = QFrame()
            ctrl.setStyleSheet(
                f"background:{C['panel2']};border-top:1px solid {C['border_hi']};")
            ctrl.setFixedHeight(36)
            cl = QHBoxLayout(ctrl); cl.setContentsMargins(8, 4, 8, 4); cl.setSpacing(8)

            def mk_btn(label, slot, w=90):
                b = QPushButton(label); b.setFixedHeight(24); b.setFixedWidth(w)
                b.setStyleSheet(
                    f"background:{C['panel3']};color:{C['cyan']};"
                    f"border:1px solid {C['border_hi']};border-radius:0px;"
                    f"font-family:Consolas;font-size:10px;font-weight:bold;letter-spacing:1px;")
                b.clicked.connect(slot); return b

            self._btn_play = mk_btn("[ PLAY ]", self._toggle_play, 95)
            self._btn_loop = mk_btn("[ LOOP: ON ]", self._toggle_loop, 110)
            self._looping  = True

            cl.addWidget(self._btn_play)
            cl.addWidget(self._btn_loop)
            cl.addStretch()

            # Dosya yolu etiketi
            path_lbl = QLabel(f"SRC: {self.VIDEO_PATH}")
            path_lbl.setFont(QFont("Consolas", 8))
            path_lbl.setStyleSheet(f"color:{C['text3']};background:transparent;")
            cl.addWidget(path_lbl)
            vl.addWidget(ctrl)

            # Oynatma sinyalleri
            from PySide6.QtMultimedia import QMediaPlayer as _MP
            self._player.playbackStateChanged.connect(self._on_state)
            self._player.mediaStatusChanged.connect(self._on_status)
            self._player.errorOccurred.connect(self._on_error)

            # Videoyu yükle ve başlat
            import os
            if os.path.exists(self.VIDEO_PATH):
                self._player.setSource(QUrl.fromLocalFile(self.VIDEO_PATH))
                self._player.play()
                self._status_lbl.setText("LIVE")
                self._status_lbl.setStyleSheet(
                    f"color:{C['green']};letter-spacing:2px;background:transparent;")
            else:
                self._status_lbl.setText("FILE NOT FOUND")

        except ImportError:
            self._player = None
            self._build_fallback(vl)

    def _toggle_play(self):
        if self._player is None: return
        from PySide6.QtMultimedia import QMediaPlayer
        if self._player.playbackState() == QMediaPlayer.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def _toggle_loop(self):
        self._looping = not self._looping
        txt = "[ LOOP: ON ]" if self._looping else "[ LOOP: OFF ]"
        self._btn_loop.setText(txt)

    def _on_state(self, state):
        from PySide6.QtMultimedia import QMediaPlayer
        if state == QMediaPlayer.PlayingState:
            self._btn_play.setText("[ PAUSE ]")
        else:
            self._btn_play.setText("[ PLAY ]")

    def _on_status(self, status):
        from PySide6.QtMultimedia import QMediaPlayer
        # Döngü: video bitince başa sar
        if status == QMediaPlayer.EndOfMedia and self._looping:
            self._player.setPosition(0)
            self._player.play()

    def _on_error(self, error, msg):
        self._status_lbl.setText(f"ERR: {msg[:40]}")
        self._status_lbl.setStyleSheet(
            f"color:{C['red']};letter-spacing:1px;background:transparent;")

    def _build_fallback(self, vl):
        f = QFrame(); f.setStyleSheet(f"background:{C['panel']};")
        fl = QVBoxLayout(f)
        lbl = QLabel(
            "PySide6-Multimedia kurulu değil.\n\n"
            "pip install PySide6\n\n"
            "(Zaten kuruluysa Python ortamını kontrol et)")
        lbl.setFont(QFont("Consolas", 11))
        lbl.setStyleSheet(f"color:{C['text3']};background:transparent;")
        lbl.setAlignment(Qt.AlignCenter)
        fl.addWidget(lbl)
        vl.addWidget(f, 1)

    def update_data(self, d):
        self.data = d   # uyum için korundu, kullanılmıyor




# ═══════════════════════════════════════════════════════════════════════════════
#  ROVER 3D GÖRÜNTÜLEYICI PANELİ  —  Three.js + GLB via QWebEngineView
# ═══════════════════════════════════════════════════════════════════════════════
class RoverViewPanel(QWidget):
    """
    TUA!13.glb modelini Three.js ile render eder.
    - İlk açılışta Three.js dosyaları otomatik indirilir ve cache'lenir
    - Sonraki açılışlarda cache kullanılır (internet gerekmez)
    - QWebEngineView gerektirir: pip install PySide6-WebEngine
    """

    # Aday GLB yolları — ilk bulunan kullanılır
    _GLB_CANDIDATES = [
        r"C:\Users\aland\OneDrive\Masaüstü\TUA_AstroHackathon\TUA!13.glb",
        "TUA!13.glb",
        "TUA_13.glb",
    ]

    # Three.js modül URL'leri (r161 — küçük boyut)
    _THREE_URLS = {
        "three.min.js":       "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js",
        "GLTFLoader.js":      "https://cdn.jsdelivr.net/npm/three@0.128/examples/js/loaders/GLTFLoader.js",
        "OrbitControls.js":   "https://cdn.jsdelivr.net/npm/three@0.128/examples/js/controls/OrbitControls.js",
    }

    def __init__(self):
        super().__init__()
        import os as _os
        # Script ile aynı klasörde .three_cache/ klasörü
        self._cache_dir = _os.path.join(
            _os.path.dirname(_os.path.abspath(__file__)), ".three_cache")
        _os.makedirs(self._cache_dir, exist_ok=True)

        vl = QVBoxLayout(self)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)

        # ── Başlık ────────────────────────────────────────────────────────
        hdr = QFrame()
        hdr.setStyleSheet(
            f"background:{C['panel2']};border-bottom:1px solid {C['border_hi']};"
            f"border-top:2px solid {C['cyan']};")
        hdr.setFixedHeight(28)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(10, 0, 10, 0)
        t = QLabel("TUA ROVER  //  3D SYSTEMS VIEW")
        t.setFont(QFont("Consolas", 10, QFont.Bold))
        t.setStyleSheet(f"color:{C['cyan']};letter-spacing:3px;background:transparent;")
        hl.addWidget(t); hl.addStretch()
        sub = QLabel("LMB:ROTATE  RMB:PAN  SCROLL:ZOOM")
        sub.setFont(QFont("Consolas", 9))
        sub.setStyleSheet(f"color:{C['text3']};letter-spacing:1px;background:transparent;")
        hl.addWidget(sub)
        vl.addWidget(hdr)

        if _WEB_AVAILABLE:
            self._vl = vl
            self._status_lbl = None
            self._init_viewer()
        else:
            self._build_fallback(vl,
                "PySide6-WebEngine kurulu değil.\n\n"
                "Terminalde şunu çalıştır:\n"
                "pip install PySide6-WebEngine\n\n"
                "Ardından uygulamayı yeniden başlat.")

    # ── Viewer başlatma ───────────────────────────────────────────────────
    def _init_viewer(self):
        """GLB ve Three.js hazırsa viewer aç, değilse status label göster."""
        import os as _os
        # GLB bul
        glb_path = None
        for p in self._GLB_CANDIDATES:
            if _os.path.exists(p):
                glb_path = p
                break
        # Script klasörü de dene
        script_dir = _os.path.dirname(_os.path.abspath(__file__))
        for name in ("TUA!13.glb", "TUA_13.glb"):
            candidate = _os.path.join(script_dir, name)
            if _os.path.exists(candidate):
                glb_path = candidate
                break

        if glb_path is None:
            self._build_fallback(self._vl,
                "GLB dosyası bulunamadı.\n\n"
                r"Beklenen: C:\Users\aland\OneDrive\Masaüstü\TUA_AstroHackathon\TUA!13.glb"
                "\n\nVeya umay_gcs.py ile aynı klasöre 'TUA!13.glb' olarak koy.")
            return

        # Three.js cache kontrolü
        missing = [k for k in self._THREE_URLS if
                   not _os.path.exists(_os.path.join(self._cache_dir, k))]

        if missing:
            self._show_download_ui(glb_path, missing)
        else:
            self._open_viewer(glb_path)

    # ── İndirme UI ────────────────────────────────────────────────────────
    def _show_download_ui(self, glb_path, missing):
        """Three.js dosyaları eksik — indirme butonu göster."""
        f = QFrame(); f.setStyleSheet(f"background:{C['panel']};")
        fl = QVBoxLayout(f); fl.setAlignment(Qt.AlignCenter); fl.setSpacing(12)

        lbl = QLabel(
            "Three.js kütüphanesi henüz indirilmedi.\n\n"
            "İlk kullanımda bir kez indirilir (~800 KB),\n"
            "sonraki açılışlarda internet gerekmez.")
        lbl.setFont(QFont("Consolas", 11)); lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"color:{C['text2']};background:transparent;")
        fl.addWidget(lbl)

        self._status_lbl = QLabel("")
        self._status_lbl.setFont(QFont("Consolas", 10))
        self._status_lbl.setAlignment(Qt.AlignCenter)
        self._status_lbl.setStyleSheet(f"color:{C['amber']};background:transparent;")
        fl.addWidget(self._status_lbl)

        btn = QPushButton("[ DOWNLOAD & LAUNCH ]")
        btn.setFixedWidth(260); btn.setFixedHeight(34)
        btn.setStyleSheet(
            f"background:{C['green_lt']};color:{C['green']};"
            f"border:1px solid {C['green_dk']};border-radius:0px;"
            f"font-family:Consolas;font-size:12px;font-weight:bold;letter-spacing:2px;")
        btn.clicked.connect(lambda: self._do_download(glb_path, f, btn))
        fl.addWidget(btn)
        self._vl.addWidget(f, 1)

    def _do_download(self, glb_path, container, btn):
        """Three.js dosyalarını indir, bitince viewer'ı aç."""
        import urllib.request, os as _os
        btn.setEnabled(False)
        btn.setText("[ DOWNLOADING... ]")
        QApplication.processEvents()

        for name, url in self._THREE_URLS.items():
            dest = _os.path.join(self._cache_dir, name)
            if _os.path.exists(dest):
                continue
            self._status_lbl.setText(f"İndiriliyor: {name}")
            QApplication.processEvents()
            try:
                urllib.request.urlretrieve(url, dest)
            except Exception as e:
                self._status_lbl.setText(f"HATA: {name}\n{e}")
                btn.setText("[ RETRY ]"); btn.setEnabled(True)
                return

        self._status_lbl.setText("Tamamlandı!")
        QApplication.processEvents()
        # Container'ı kaldır ve viewer aç
        container.setParent(None)
        self._open_viewer(glb_path)

    # ── Viewer ────────────────────────────────────────────────────────────
    def _open_viewer(self, glb_path):
        """GLB + cache'deki Three.js ile HTML oluştur ve WebView'da aç."""
        import base64, tempfile, os as _os

        with open(glb_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")

        def js(name):
            path = _os.path.join(self._cache_dir, name)
            with open(path, "r", encoding="utf-8", errors="replace") as f2:
                return f2.read()

        three_js      = js("three.min.js")
        gltf_js       = js("GLTFLoader.js")
        orbit_js      = js("OrbitControls.js")

        html = self._build_html(b64, three_js, gltf_js, orbit_js)

        tmp = tempfile.NamedTemporaryFile(
            suffix=".html", delete=False, mode="w", encoding="utf-8")
        tmp.write(html); tmp.flush()
        self._tmp_path = tmp.name; tmp.close()

        view = QWebEngineView()
        view.setUrl(QUrl.fromLocalFile(self._tmp_path))
        self._vl.addWidget(view, 1)

    def closeEvent(self, e):
        import os as _os
        if hasattr(self, "_tmp_path"):
            try: _os.unlink(self._tmp_path)
            except: pass
        super().closeEvent(e)

    def _build_fallback(self, vl, msg):
        f = QFrame(); f.setStyleSheet(f"background:{C['panel']};")
        fl = QVBoxLayout(f)
        lbl = QLabel(msg); lbl.setFont(QFont("Consolas", 11))
        lbl.setStyleSheet(f"color:{C['text3']};background:transparent;")
        lbl.setAlignment(Qt.AlignCenter); fl.addWidget(lbl)
        vl.addWidget(f, 1)

    @staticmethod
    def _build_html(b64: str, three_js: str, gltf_js: str, orbit_js: str) -> str:
        # three r128 uses global THREE, GLTFLoader ve OrbitControls
        # classic script tag approach (non-module) — r128 supports this
        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0a0d04;overflow:hidden;font-family:Consolas,monospace}}
canvas{{display:block;width:100vw;height:100vh}}
#hud{{position:absolute;bottom:6px;left:6px;right:6px;
  display:flex;justify-content:space-between;pointer-events:none;}}
.hb{{background:rgba(2,6,1,.88);border:1px solid rgba(40,80,20,.55);
  padding:3px 9px;color:#3d7a1e;font-size:10px;letter-spacing:1px;}}
.g{{color:#c8a830}}
#title{{position:absolute;top:6px;left:50%;transform:translateX(-50%);
  background:rgba(2,6,1,.88);border:1px solid rgba(200,168,48,.35);
  border-top:2px solid #c8a830;padding:3px 16px;color:#c8a830;
  font-size:9px;letter-spacing:3px;pointer-events:none;}}
#loading{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
  color:#3d7a1e;font-size:13px;letter-spacing:2px;pointer-events:none;}}
</style></head><body>
<div id="title">TUA ROVER  //  AUTONOMOUS LUNAR VEHICLE</div>
<div id="loading">INITIALIZING...</div>
<div id="hud">
  <div class="hb">LMB <span class="g">ROTATE</span> &nbsp; RMB <span class="g">PAN</span> &nbsp; SCROLL <span class="g">ZOOM</span></div>
  <div class="hb" id="cam">CAM: ORBIT</div>
  <div class="hb"><span class="g">TUA-1</span> &nbsp; UMAY GCS v4.0</div>
</div>
<script>
{three_js}
</script>
<script>
{gltf_js}
</script>
<script>
{orbit_js}
</script>
<script>
(function(){{
var renderer=new THREE.WebGLRenderer({{antialias:true}});
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(window.innerWidth,window.innerHeight);
renderer.shadowMap.enabled=true;
renderer.shadowMap.type=THREE.PCFSoftShadowMap;
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=1.15;
document.body.appendChild(renderer.domElement);

var scene=new THREE.Scene();
scene.background=new THREE.Color(0x0a0d04);
scene.fog=new THREE.Fog(0x0a0d04,12,55);

var camera=new THREE.PerspectiveCamera(45,window.innerWidth/window.innerHeight,0.01,200);
camera.position.set(2.2, 1.4, 2.8);

scene.add(new THREE.AmbientLight(0x304820,1.4));
var sun=new THREE.DirectionalLight(0xffe8b0,3.8);
sun.position.set(6,9,5);sun.castShadow=true;
sun.shadow.mapSize.width=2048;sun.shadow.mapSize.height=2048;
sun.shadow.camera.near=0.5;sun.shadow.camera.far=60;
sun.shadow.camera.left=-6;sun.shadow.camera.right=6;
sun.shadow.camera.top=6;sun.shadow.camera.bottom=-6;
sun.shadow.bias=-0.0004;scene.add(sun);
var fill=new THREE.DirectionalLight(0x1a3020,1.1);
fill.position.set(-5,3,-4);scene.add(fill);
var rim=new THREE.PointLight(0xc8a830,0.9,15);
rim.position.set(-3,4,-3);scene.add(rim);

var ground=new THREE.Mesh(
  new THREE.CircleGeometry(8,64),
  new THREE.MeshStandardMaterial({{color:0x161408,roughness:0.96,metalness:0.0}})
);
ground.rotation.x=-Math.PI/2;ground.receiveShadow=true;scene.add(ground);
var grid=new THREE.GridHelper(16,32,0x1a2006,0x1a2006);
grid.material.opacity=0.35;grid.material.transparent=true;
grid.position.y=0.002;scene.add(grid);

var controls=new THREE.OrbitControls(camera,renderer.domElement);
controls.enableDamping=true;controls.dampingFactor=0.06;
controls.minDistance=0.4;controls.maxDistance=18;
controls.maxPolarAngle=Math.PI/1.75;
controls.target.set(0,0.3,0);controls.update();

controls.addEventListener('change',function(){{
  var d=camera.position.distanceTo(controls.target);
  var az=(Math.atan2(camera.position.x-controls.target.x,
    camera.position.z-controls.target.z)*180/Math.PI+360)%360;
  var el=Math.asin((camera.position.y-controls.target.y)/d)*180/Math.PI;
  document.getElementById('cam').textContent=
    'AZ '+az.toFixed(0)+'  EL '+el.toFixed(0)+'  DST '+d.toFixed(2)+'m';
}});

var b64="{b64}";
var bin=atob(b64);
var buf=new ArrayBuffer(bin.length);
var u8=new Uint8Array(buf);
for(var i=0;i<bin.length;i++)u8[i]=bin.charCodeAt(i);

var modelRoot=null;
var loader=new THREE.GLTFLoader();
loader.parse(buf.slice(0),'',(gltf)=>{{
  var model=gltf.scene;

  // ── SolidWorks Z-up → Three.js Y-up ──────────────────────────────
  model.rotation.x = -Math.PI / 2;
  model.rotation.y = Math.PI;

  // ── Scale & center ────────────────────────────────────────────────
  model.updateMatrixWorld(true);
  var box = new THREE.Box3().setFromObject(model);
  var center = box.getCenter(new THREE.Vector3());
  var size   = box.getSize(new THREE.Vector3());
  var scale  = 1.9 / Math.max(size.x, size.y, size.z);
  model.scale.setScalar(scale);

  // X/Z merkezle
  model.position.x = -center.x * scale;
  model.position.z = -center.z * scale;
  model.position.y = 0;

  // Tekerleri zemine oturt
  model.updateMatrixWorld(true);
  var box2 = new THREE.Box3().setFromObject(model);
  model.position.y -= box2.min.y;

  // ── Material ──────────────────────────────────────────────────────
  model.traverse(function(c){{
    if(c.isMesh){{
      c.castShadow=true;c.receiveShadow=true;
      if(c.material){{
        var ms=Array.isArray(c.material)?c.material:[c.material];
        ms.forEach(function(m){{
          if(m.isMeshStandardMaterial||m.isMeshPhongMaterial){{
            m.metalness=Math.min((m.metalness||0)+0.3,0.88);
            m.roughness=Math.max((m.roughness||0.5)-0.12,0.12);
            m.needsUpdate=true;
          }}
        }});
      }}
    }}
  }});

  // ── Pivot Group — sadece grubu döndüreceğiz, model'e dokunmayacağız ──
  // Bu gimbal lock sorununu tamamen önler.
  var pivot = new THREE.Group();
  pivot.add(model);
  scene.add(pivot);
  modelRoot = pivot;   // auto-rotate artık pivot'u döndürür

  // Kamera hedefini modelin merkezine ayarla
  model.updateMatrixWorld(true);
  var bc = new THREE.Box3().setFromObject(model).getCenter(new THREE.Vector3());
  controls.target.copy(bc);
  controls.update();
  document.getElementById('loading').style.display='none';
}},function(err){{
  document.getElementById('loading').textContent='LOAD ERROR: '+err;
  console.error(err);
}});

var autoRot=true,lastPt=Date.now();
renderer.domElement.addEventListener('pointerdown',function(){{autoRot=false;lastPt=Date.now();}});
renderer.domElement.addEventListener('pointerup',function(){{lastPt=Date.now();}});

var clock=new THREE.Clock();
(function loop(){{
  requestAnimationFrame(loop);
  var dt=clock.getDelta();
  if(!autoRot&&Date.now()-lastPt>4000)autoRot=true;
  // Sadece Y ekseninde döndür — pivot grubu döner, model'in kendi rotasyonu sabit kalır
  if(autoRot&&modelRoot)modelRoot.rotation.y+=dt*0.28;
  controls.update();
  renderer.render(scene,camera);
}})();

window.addEventListener('resize',function(){{
  camera.aspect=window.innerWidth/window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth,window.innerHeight);
}});
}})();
</script>
</body></html>"""


# ═══════════════════════════════════════════════════════════════════════════════
#  KAM TEMİZLEME SİSTEMİ BİLGİ PANELİ
# ═══════════════════════════════════════════════════════════════════════════════
class CleaningSystemPanel(QWidget):
    """
    Küresel cam temizleme sistemi değerlendirmesi.
    Uygulanabilirlik, riskler ve alternatifler.
    """
    def __init__(self):
        super().__init__()
        vl = QVBoxLayout(self)
        vl.setContentsMargins(12, 8, 12, 8)
        vl.setSpacing(8)

        title = QLabel("KÜRESEL CAM TEMİZLEME SİSTEMİ — DEĞERLENDIRME")
        title.setFont(QFont("Consolas", 11, QFont.Bold))
        title.setStyleSheet(f"color:{C['cyan']};letter-spacing:1px;")
        vl.addWidget(title)

        score_row = QHBoxLayout()
        score_row.setSpacing(10)
        for label, val, col, card in [
            ("Uygulanabilirlik", "60 %", C['amber'],   "CardAmber"),
            ("TRL Küresel",     "4/9",   C['amber'],   "CardAmber"),
            ("TRL EDS",         "6/9",   C['green'],   "CardGreen"),
            ("TRL Piezo",       "7/9",   C['green'],   "CardGreen"),
        ]:
            f = QFrame(); f.setObjectName(card)
            fl = QVBoxLayout(f); fl.setContentsMargins(8,4,8,4); fl.setSpacing(1)
            fl.addWidget(QLabel(label, font=QFont("Consolas",8,QFont.Bold),
                                styleSheet=f"color:{C['text3']};font-size:9px;letter-spacing:1px;"))
            vl2 = QLabel(val, font=QFont("Consolas",15,QFont.Bold),
                         styleSheet=f"color:{col};")
            vl2.setAlignment(Qt.AlignCenter)
            fl.addWidget(vl2)
            score_row.addWidget(f)
        vl.addLayout(score_row)

        info = QTextEdit()
        info.setObjectName("TelLog")
        info.setReadOnly(True)
        info.setFont(QFont("Consolas", 11))
        info.setStyleSheet(f"background:{C['log_bg']}; color:{C['lc_text']}; border:none; padding:8px;")
        info.setHtml(self._build_html())
        vl.addWidget(info, 1)

    def _build_html(self):
        c = C
        def row(lbl, txt, col=None):
            col = col or c['lc_text']
            return (f'<tr>'
                    f'<td style="color:{c["lc_dim"]};padding:2px 8px 2px 0;white-space:nowrap;">'
                    f'{lbl}</td>'
                    f'<td style="color:{col};">{txt}</td></tr>')

        def head(t, col):
            return (f'<tr><td colspan="2" style="padding-top:8px;padding-bottom:2px;">'
                    f'<b style="color:{col};font-size:12px;letter-spacing:1px;">{t}</b></td></tr>')

        return f"""
<table style="font-size:12px;font-family:Consolas,monospace;line-height:1.7;width:100%;">
{head("⚙  MEKANİZMA", c['cyan'])}
{row("Çalışma Prensibi", "Küresel dom dönerek araç gövdesindeki fırça/contaya sürtünür")}
{row("Temizleme Süresi", "~5 saniye / döngü")}
{row("Enerji", "Mevcut dönme aktuatörü — ek güç yok")}

{head("✓  AVANTAJLAR", c['green'])}
{row("Vakum uyumluluğu", "Dışa açık hareketli parça yok — vakumda güvenli")}
{row("Kaba toz", "50–100 µm gevşek regolith için etkili")}
{row("Maliyet", "Ek mekanizma gerektirmiyor")}

{head("⚠  RİSK VE KISITLAR", c['amber'])}
{row("Elektrostatik bağlanma", "UV + kozmik ışın → güçlü yük → mekanik silme YETERSİZ")}
{row("Aşındırıcılık", "Kuvars taneleri (Mohs 7) → tekrar silme camı çizer")}
{row("Vakum kaynaklaması", "Metal-metal temas → cold welding riski")}
{row("Termal şok", "−180°C → +120°C geçişte conta arızası")}
{row("Yeniden dağılım", "Küçük partiküller yayılabilir, kaldırılmayabilir")}

{head("★  ÖNERİLEN HİBRİT ÇÖZÜM", c['purple'])}
{row("Birincil (sürekli)", "Elektrodinamik Toz Kalkanı — EDS (NASA TRL:6)", c['green'])}
{row("İkincil (tetikleyici)", "Piezoelektrik vibrasyon — 50-200 kHz, 0.5 W (TRL:7)", c['green'])}
{row("Acil (manuel)", "Küresel rotasyon — mevcut mekanizma (TRL:4)", c['amber'])}
{row("Önleyici", "Hidrofobik nano kaplama — yapışmayı azaltır (TRL:8)", c['cyan'])}

{head("📡  SIMSCAPE ENTEGRASYONU", c['cyan'])}
{row("Sensör çıkışı", "cam_opacity: 0.0-1.0 (0=temiz, 1=kör)")}
{row("Temizleme tetik", "opacity > 0.3 → cleaning_cmd: 1 → UDP port:25001")}
{row("EDS aktivasyon", "opacity > 0.1 → eds_pwm: 40% → sürekli koruma")}
{row("Sonuç", "cam_opacity < 0.05 → temizleme başarılı")}
</table>
"""


# ═══════════════════════════════════════════════════════════════════════════════
#  ANA PENCERE  —  UMAY GCS Dashboard
# ═══════════════════════════════════════════════════════════════════════════════
class Dashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UMAY GCS — Lunar Rover Navigation Control System  v4.0")
        self.setMinimumSize(1440, 920)
        self.resize(1620, 1000)
        self.setStyleSheet(SS)

        self.sim_connected = False
        self.demo  = DemoGen()
        self.demo.data_ready.connect(self._on_data)
        self.recv  = SimulinkReceiver()
        self.recv.data_received.connect(self._on_data)
        self.recv.connection_status.connect(self._on_conn_status)

        self._build_ui()
        self._start_demo()

    # ── UI İnşası ─────────────────────────────────────────────────────────────
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
        spl.setSizes([860, 620])
        bl.addWidget(spl, 1)
        root.addWidget(body, 1)
        self.status_bar = QStatusBar(); self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(
            "UMAY GCS v4.0  |  D* Lite + A* Hibrit Aktif  |  "
            "Demo mode  |  Haritaya tıkla → engel ekle  |  "
            "Simlink için bağlantı panelini kullan")

    def _mk_header(self):
        bar = QFrame(); bar.setObjectName("Header"); bar.setFixedHeight(44)
        lay = QHBoxLayout(bar); lay.setContentsMargins(14,0,14,0); lay.setSpacing(0)

        # Sol: taktik sembol + başlık
        dot = QLabel("◈")
        dot.setFont(QFont("Consolas", 18, QFont.Bold))
        dot.setStyleSheet(f"color:{C['cyan']};margin-right:10px;background:transparent;")
        lay.addWidget(dot)

        title = QLabel("UMAY GCS")
        title.setFont(QFont("Consolas", 16, QFont.Bold))
        title.setStyleSheet(
            f"color:{C['text']};letter-spacing:5px;background:transparent;")
        lay.addWidget(title)

        sep1 = QLabel("  //  ")
        sep1.setStyleSheet(f"color:{C['border_hi']};background:transparent;font-size:14px;")
        lay.addWidget(sep1)

        sub = QLabel("AUTONOMOUS LUNAR ROVER  ·  D* LITE + A*  ·  HAZARD ENGINE")
        sub.setFont(QFont("Consolas", 9))
        sub.setStyleSheet(f"color:{C['text3']};letter-spacing:2px;background:transparent;")
        lay.addWidget(sub)
        lay.addStretch()

        # Sağ: saat
        self.clk = QLabel()
        self.clk.setFont(QFont("Consolas", 11, QFont.Bold))
        self.clk.setStyleSheet(f"color:{C['text2']};background:transparent;margin-right:16px;")
        lay.addWidget(self.clk)

        # Bağlantı rozeti
        self.badge = QLabel("  ○  DEMO  ")
        self.badge.setFont(QFont("Consolas", 10, QFont.Bold))
        self.badge.setStyleSheet(
            f"background:{C['amber_lt']};color:{C['amber']};"
            f"border:1px solid {C['amber_dk']};border-radius:0px;padding:3px 10px;"
            f"letter-spacing:2px;")
        lay.addWidget(self.badge)

        tmr = QTimer(self); tmr.timeout.connect(self._tick_clk); tmr.start(1000)
        self._tick_clk()
        return bar

    def _mk_telem(self):
        frame = QFrame(); frame.setObjectName("Card")
        lay = QHBoxLayout(frame); lay.setContentsMargins(10,6,10,6); lay.setSpacing(4)

        def tile(lbl_t, min_w=95):
            f = QFrame(); f.setObjectName("Card"); f.setMinimumWidth(min_w)
            vl = QVBoxLayout(f); vl.setContentsMargins(7,4,7,4); vl.setSpacing(1)
            lb = QLabel(lbl_t); lb.setObjectName("LSmall"); lb.setAlignment(Qt.AlignCenter)
            val = QLabel("—"); val.setObjectName("LBigG")
            val.setFont(QFont("Consolas",19,QFont.Bold)); val.setAlignment(Qt.AlignCenter)
            vl.addWidget(lb); vl.addWidget(val)
            return f, val

        def div():
            d = QFrame(); d.setFrameShape(QFrame.VLine)
            d.setStyleSheet(f"color:{C['border']};"); return d

        # Batarya
        bf = QFrame(); bf.setObjectName("Card"); bf.setFixedWidth(110)
        bvl = QVBoxLayout(bf); bvl.setContentsMargins(7,4,7,4); bvl.setSpacing(2)
        bl_ = QLabel("BATTERY"); bl_.setObjectName("LSmall"); bl_.setAlignment(Qt.AlignCenter)
        self.bat_val = QLabel("92.0 %"); self.bat_val.setObjectName("LBigG")
        self.bat_val.setFont(QFont("Consolas",16,QFont.Bold)); self.bat_val.setAlignment(Qt.AlignCenter)
        self.bat_bar = QProgressBar(); self.bat_bar.setRange(0,100); self.bat_bar.setValue(92)
        self.bat_bar.setFixedHeight(6)
        bvl.addWidget(bl_); bvl.addWidget(self.bat_val); bvl.addWidget(self.bat_bar)
        lay.addWidget(bf); lay.addWidget(div())

        f, self.spd_v   = tile("SPEED m/s");  lay.addWidget(f); lay.addWidget(div())
        f, self.hdg_v   = tile("HEADING°");   lay.addWidget(f); lay.addWidget(div())
        f, self.tmp_v   = tile("TEMP °C");    lay.addWidget(f); lay.addWidget(div())
        f, self.sig_v   = tile("SIGNAL %");   lay.addWidget(f); lay.addWidget(div())
        f, self.rpm_v   = tile("WHEEL RPM");  lay.addWidget(f); lay.addWidget(div())
        f, self.cpu_v   = tile("CPU °C");     lay.addWidget(f); lay.addWidget(div())
        f, self.dust_v  = tile("DUST %", 90); lay.addWidget(f); lay.addWidget(div())

        # Rover status
        sf = QFrame(); sf.setObjectName("CardGreen"); sf.setMinimumWidth(148)
        svl_ = QVBoxLayout(sf); svl_.setContentsMargins(10,4,10,4); svl_.setSpacing(1)
        sl = QLabel("ROVER STATUS"); sl.setObjectName("LSmall"); sl.setAlignment(Qt.AlignCenter)
        sl.setStyleSheet(f"color:{C['text3']};font-size:10px;font-weight:bold;letter-spacing:2px;")
        self.st_val = QLabel("MOVING")
        self.st_val.setFont(QFont("Consolas",14,QFont.Bold))
        self.st_val.setStyleSheet(f"color:{C['green']};letter-spacing:2px;")
        self.st_val.setAlignment(Qt.AlignCenter)
        svl_.addWidget(sl); svl_.addWidget(self.st_val)
        lay.addWidget(sf); lay.addStretch()
        return frame

    def _mk_conn_panel(self):
        frame = QFrame(); frame.setObjectName("ConnPanel")
        lay = QHBoxLayout(frame); lay.setContentsMargins(14,8,14,8); lay.setSpacing(10)
        ico = QLabel("CONNECTION SETTINGS")
        ico.setFont(QFont("Consolas", 11, QFont.Bold))
        ico.setStyleSheet(f"color:{C['cyan']};letter-spacing:2px;")
        lay.addWidget(ico)

        def sep():
            d = QFrame(); d.setFrameShape(QFrame.VLine)
            d.setStyleSheet(f"color:{C['border']};"); return d
        def lbl(t):
            l = QLabel(t); l.setFont(QFont("Consolas", 11, QFont.Bold))
            l.setStyleSheet(f"color:{C['text2']};"); return l

        lay.addWidget(sep())
        lay.addWidget(lbl("PROTO:"))
        self.proto = QComboBox(); self.proto.addItems(["UDP","TCP"])
        self.proto.setFixedWidth(78); self.proto.setFixedHeight(32)
        lay.addWidget(self.proto)
        lay.addWidget(lbl("HOST:"))
        self.host_inp = QLineEdit("127.0.0.1")
        self.host_inp.setFixedWidth(140); self.host_inp.setFixedHeight(32)
        lay.addWidget(self.host_inp)
        lay.addWidget(lbl("PORT:"))
        self.port_inp = QSpinBox(); self.port_inp.setRange(1024,65535)
        self.port_inp.setValue(25000); self.port_inp.setFixedWidth(88); self.port_inp.setFixedHeight(32)
        lay.addWidget(self.port_inp); lay.addWidget(sep())

        self.conn_btn = QPushButton("CONNECT"); self.conn_btn.setObjectName("BtnConn")
        self.conn_btn.setFixedHeight(34); self.conn_btn.clicked.connect(self._toggle_conn)
        lay.addWidget(self.conn_btn)
        self.conn_status_lbl = QLabel("NOT CONNECTED")
        self.conn_status_lbl.setFont(QFont("Consolas", 10))
        self.conn_status_lbl.setStyleSheet(f"color:{C['text3']};margin-left:4px;letter-spacing:1px;")
        lay.addWidget(self.conn_status_lbl); lay.addStretch()

        hint = QLabel("SIMULINK: UDP SEND  //  IP:127.0.0.1  PORT:25000  FMT:JSON")
        hint.setFont(QFont("Consolas", 9))
        hint.setStyleSheet(f"color:{C['text3']};letter-spacing:1px;")
        lay.addWidget(hint)
        return frame

    def _mk_left(self):
        w = QWidget(); vl = QVBoxLayout(w)
        vl.setContentsMargins(0,0,4,0); vl.setSpacing(6)
        tabs = QTabWidget()

        # ── Tab 1: Lunar Harita ───────────────────────────────────────────
        mt = QWidget(); mvl = QVBoxLayout(mt); mvl.setContentsMargins(4,4,4,4); mvl.setSpacing(4)
        self.map_c = LunarMapCanvas()
        self.map_c.replan_signal.connect(self._on_replan)
        mvl.addWidget(self.map_c, 1)

        # ── Kontrol Paneli (2 satır) — BATTLESPACE MILITARY ─────────────
        ctrl_frame = QFrame()
        ctrl_frame.setStyleSheet(
            f"background:{C['panel2']};border:1px solid {C['border_hi']};"
            f"border-top:2px solid {C['cyan']};border-radius:0px;")
        ctrl_vl = QVBoxLayout(ctrl_frame)
        ctrl_vl.setContentsMargins(8, 5, 8, 5); ctrl_vl.setSpacing(4)

        def mk_clbl(txt):
            l = QLabel(txt)
            l.setStyleSheet(
                f"color:{C['text3']};font-family:Consolas,monospace;font-size:10px;"
                f"font-weight:bold;letter-spacing:2px;background:transparent;")
            return l

        def mk_sep_v():
            d = QFrame(); d.setFrameShape(QFrame.VLine)
            d.setStyleSheet(f"color:{C['border_hi']};max-width:1px;")
            return d

        # ── Row 1: ALG · SENSOR · OVERLAYS ───────────────────────────────
        row1 = QHBoxLayout(); row1.setSpacing(8)
        row1.addWidget(mk_clbl("ALG:"))
        self.algo_combo = QComboBox()
        self.algo_combo.addItems(["D* LITE [HYBRID]", "A* [FULL PLAN]"])
        self.algo_combo.setFixedWidth(155); self.algo_combo.setFixedHeight(22)
        self.algo_combo.currentIndexChanged.connect(lambda i: self.map_c.set_algo(i == 0))
        row1.addWidget(self.algo_combo)
        row1.addWidget(mk_sep_v())

        row1.addWidget(mk_clbl("SENSOR:"))
        sens_sl = QSlider(Qt.Horizontal); sens_sl.setRange(2, 8); sens_sl.setValue(4)
        sens_sl.setFixedWidth(75); sens_sl.setFixedHeight(14)
        sens_sl.valueChanged.connect(self.map_c.set_sensor_range)
        row1.addWidget(sens_sl)
        self.sens_lbl = QLabel("4")
        self.sens_lbl.setStyleSheet(
            f"color:{C['cyan']};font-family:Consolas;font-size:11px;"
            f"font-weight:bold;min-width:14px;background:transparent;")
        sens_sl.valueChanged.connect(lambda v: self.sens_lbl.setText(str(v)))
        row1.addWidget(self.sens_lbl)
        row1.addWidget(mk_sep_v())

        cb_style = (f"color:{C['text2']};font-family:Consolas;font-size:10px;"
                    f"letter-spacing:1px;spacing:4px;background:transparent;")
        for cb_txt, cb_slot in [
            ("SHADOW",  lambda s: self.map_c.toggle_shadows(bool(s))),
            ("SENSOR",  lambda s: self.map_c.toggle_sensor_ring(bool(s))),
            ("TERRAIN", lambda s: self.map_c.toggle_cost_overlay(bool(s))),
        ]:
            cb = QCheckBox(cb_txt); cb.setChecked(True)
            cb.setStyleSheet(cb_style)
            cb.stateChanged.connect(cb_slot)
            row1.addWidget(cb)
        row1.addStretch()
        ctrl_vl.addLayout(row1)

        # ── Row 2: SPD · HOLD · REROUTE · RESET · REPLAN ─────────────────
        row2 = QHBoxLayout(); row2.setSpacing(6)

        row2.addWidget(mk_clbl("SPD:"))
        self.spd_slider = QSlider(Qt.Horizontal)
        self.spd_slider.setRange(1, 50); self.spd_slider.setValue(10)
        self.spd_slider.setFixedWidth(105); self.spd_slider.setFixedHeight(14)
        self.spd_slider.valueChanged.connect(self._on_speed_slider)
        row2.addWidget(self.spd_slider)
        self.spd_slider_lbl = QLabel("1.0x")
        self.spd_slider_lbl.setStyleSheet(
            f"color:{C['amber']};font-family:Consolas;font-size:11px;"
            f"font-weight:bold;min-width:32px;background:transparent;")
        row2.addWidget(self.spd_slider_lbl)
        row2.addWidget(mk_sep_v())

        btn_cfg = [
            ("[ HOLD ]",    "amber",  24, 105, "_toggle_pause", "btn_pause"),
            ("[ REROUTE ]", "green",  24, 115, "_reset_route",  None),
            ("[ RESET ]",   "red",    24, 100, "_full_reset",   None),
        ]
        for label, tone, hgt, wdt, slot, attr in btn_cfg:
            btn = QPushButton(label)
            btn.setFixedHeight(hgt); btn.setFixedWidth(wdt)
            bg   = C[f"{tone}_lt"]
            fg   = C[tone]
            bdr  = C[f"{tone}_dk"]
            btn.setStyleSheet(
                f"background:{bg};color:{fg};border:1px solid {bdr};"
                f"border-radius:0px;font-family:Consolas;font-size:11px;"
                f"font-weight:bold;letter-spacing:2px;")
            getattr(btn, "clicked").connect(getattr(self, slot))
            if attr:
                setattr(self, attr, btn)
            row2.addWidget(btn)

        row2.addWidget(mk_sep_v())
        btn_rp = QPushButton("[ REPLAN ]")
        btn_rp.setFixedHeight(24)
        btn_rp.setStyleSheet(
            f"background:{C['panel3']};color:{C['cyan']};"
            f"border:1px solid {C['border_hi']};border-radius:0px;"
            f"font-family:Consolas;font-size:11px;font-weight:bold;letter-spacing:2px;")
        btn_rp.clicked.connect(self._force_replan)
        row2.addWidget(btn_rp)
        row2.addStretch()
        ctrl_vl.addLayout(row2)

        mvl.addWidget(ctrl_frame)

        mvl.addWidget(ctrl_frame)
        hint = QLabel(
            "CLICK MAP → SET OSCAR (TARGET)  |  GREEN RING=SENSOR  |  GREEN DASHES=NAV ROUTE  |  GREEN=TRAIL  |  YELLOW=REPLAN")
        hint.setFont(QFont("Consolas",8))
        hint.setStyleSheet(f"color:{C['text3']};padding:1px 4px;")
        mvl.addWidget(hint)
        tabs.addTab(mt,"  ◈ LUNAR MAP  ")

        # ── Tab 2: Sim Feed ───────────────────────────────────────────────
        st = QWidget(); svl_ = QVBoxLayout(st); svl_.setContentsMargins(4,4,4,4)
        self.sim_feed = SimFeed(); svl_.addWidget(self.sim_feed)
        tabs.addTab(st,"  ⊡ SIM FEED  ")

        # ── Tab 3: Temizleme Sistemi ──────────────────────────────────────
        cleaning_tab = CleaningSystemPanel()
        tabs.addTab(cleaning_tab, "  ◐ CLEANING SYS  ")

        # ── Tab 4: 3D Rover Görüntüleyici ─────────────────────────────────
        self.rover_panel = RoverViewPanel()
        tabs.addTab(self.rover_panel, "  ◉ ROVER 3D  ")

        vl.addWidget(tabs); return w

    def _mk_right(self):
        w = QWidget(); vl = QVBoxLayout(w)
        vl.setContentsMargins(4,0,0,0); vl.setSpacing(8)

        # ── Group 1: Vehicle Status & Position ───────────────────────────
        g1 = QGroupBox("VEHICLE STATUS  &  POSITION")
        g1l = QVBoxLayout(g1); g1l.setSpacing(6)
        pf = QFrame(); pf.setObjectName("Card")
        pg = QGridLayout(pf); pg.setContentsMargins(14,10,14,10)
        pg.setSpacing(7); pg.setColumnStretch(1,1); pg.setColumnStretch(3,1)

        def pos_cell(lbl_t, col_l, col_v, row):
            lb = QLabel(lbl_t); lb.setFont(QFont("Consolas",10,QFont.Bold))
            lb.setStyleSheet(f"color:{C['text3']};letter-spacing:1px;")
            vl_ = QLabel("—"); vl_.setFont(QFont("Consolas",12,QFont.Bold))
            vl_.setStyleSheet(f"color:{C['cyan']};letter-spacing:1px;")
            pg.addWidget(lb, row, col_l); pg.addWidget(vl_, row, col_v)
            return vl_

        self.p_lat = pos_cell("LAT :",     0, 1, 0)
        self.p_lon = pos_cell("LON :",     0, 1, 1)
        self.p_alt = pos_cell("ALT :",     0, 1, 2)
        self.p_obs = pos_cell("OBS DIST:", 0, 1, 3)
        sep_line = QFrame(); sep_line.setFrameShape(QFrame.VLine)
        sep_line.setStyleSheet(f"color:{C['border2']};")
        pg.addWidget(sep_line, 0, 2, 4, 1)
        self.p_spd = pos_cell("SPEED :",    3, 4, 0)
        self.p_hdg = pos_cell("HEADING :",  3, 4, 1)
        self.p_wpt = pos_cell("TARGET   :", 3, 4, 2)
        self.p_rta = pos_cell("ROUTE PTS:", 3, 4, 3)
        g1l.addWidget(pf)
        vl.addWidget(g1, 1)

        # ── Group 2: Navigation Engine log ───────────────────────────────
        g2 = QGroupBox("NAVIGATION ENGINE  —  D* LITE + A*  |  MANEUVER COMMANDS")
        g2l = QVBoxLayout(g2); g2l.setSpacing(5); g2l.setContentsMargins(8,12,8,8)

        # Aktif komut banner
        cf = QFrame(); cf.setObjectName("CardBlue"); cf.setFixedHeight(48)
        cl = QHBoxLayout(cf); cl.setContentsMargins(14,5,14,5)
        ct = QLabel("ACTIVE CMD:"); ct.setFont(QFont("Consolas",11,QFont.Bold))
        ct.setStyleSheet(f"color:{C['text2']};")
        self.act_cmd = QLabel("STANDBY")
        self.act_cmd.setFont(QFont("Consolas",15,QFont.Bold))
        self.act_cmd.setStyleSheet(f"color:{C['cyan']};letter-spacing:2px;")
        cl.addWidget(ct); cl.addWidget(self.act_cmd, 1)
        g2l.addWidget(cf)

        # Algoritma durum satırı
        af = QFrame(); af.setObjectName("CardPurple"); af.setFixedHeight(34)
        al = QHBoxLayout(af); al.setContentsMargins(12,4,12,4)
        self.algo_lbl = QLabel("D* LITE AKTİF  |  A* YEDEK HAZIR")
        self.algo_lbl.setFont(QFont("Consolas",11,QFont.Bold))
        self.algo_lbl.setStyleSheet(f"color:{C['purple']};")
        self.replan_cnt_lbl = QLabel("REPLAN: 0  |  TEHLIKE: 0")
        self.replan_cnt_lbl.setFont(QFont("Consolas",10))
        self.replan_cnt_lbl.setStyleSheet(f"color:{C['text2']};")
        al.addWidget(self.algo_lbl); al.addStretch(); al.addWidget(self.replan_cnt_lbl)
        g2l.addWidget(af)

        # Nav log başlık
        nh = QFrame(); nh.setFixedHeight(28)
        nh.setStyleSheet(f"background:{C['panel2']};border-bottom:1px solid {C['border']};")
        nhl = QHBoxLayout(nh); nhl.setContentsMargins(12,0,10,0)
        nh_lbl = QLabel("NAV LOG  //  D* LITE · A* · SENSOR · HAZARD")
        nh_lbl.setFont(QFont("Consolas",10,QFont.Bold))
        nh_lbl.setStyleSheet(f"color:{C['lc_green']};letter-spacing:2px;")
        nhl.addWidget(nh_lbl); nhl.addStretch()
        clr = QPushButton("CLR"); clr.setObjectName("BtnClr")
        clr.setFixedHeight(20); clr.setFont(QFont("Consolas",9))
        nhl.addWidget(clr); g2l.addWidget(nh)

        self.nav_log = QTextEdit(); self.nav_log.setObjectName("NavLog")
        self.nav_log.setReadOnly(True)
        clr.clicked.connect(self.nav_log.clear)
        g2l.addWidget(self.nav_log, 1)
        vl.addWidget(g2, 4)
        return w

    # ── Replan / Navigasyon ───────────────────────────────────────────────────
    def _force_replan(self):
        """Zorla replan butonu."""
        nav = self.map_c.nav
        ok, reason = nav._replan("Manuel zorla replan")
        self._on_replan(f"{'✓' if ok else '✗'} ZORLA REPLAN → {nav.direction_hint()}")

    # ── Hız / Durdur / Sıfırla ───────────────────────────────────────────────
    def _on_speed_slider(self, val: int):
        """Slider 1-50 → 0.1x – 5.0x çarpan. Demo timer da orantılı hızlanır."""
        speed = val / 10.0
        self.map_c.set_move_speed(speed)
        self.spd_slider_lbl.setText(f"{speed:.1f}x")
        # Demo timer aralığını da ayarla: hız arttıkça daha sık tick
        # Temel: 500ms; hız 1x=500ms, 5x=100ms, 0.1x=2000ms
        base_ms = int(500 / max(0.1, speed))
        base_ms = max(80, min(2000, base_ms))
        if self.demo.timer.isActive():
            self.demo.timer.setInterval(base_ms)
        # Renk güncelle
        if speed < 0.5:
            col = C['blue']
        elif speed > 3.0:
            col = C['red']
        elif speed > 1.5:
            col = C['amber']
        else:
            col = C['green']
        self.spd_slider_lbl.setStyleSheet(
            f"color:{col};font-family:Consolas;font-size:12px;"
            f"font-weight:bold;min-width:36px;")

    def _toggle_pause(self):
        """Durdur / Devam Et toggle."""
        paused = self.map_c.toggle_pause()
        if paused:
            self.btn_pause.setText("[ RESUME ]")
            self.btn_pause.setStyleSheet(f"background:{C['green_lt']};color:{C['green']};"f"border:1px solid {C['green_dk']};border-radius:0px;"f"font-family:Consolas;font-size:11px;font-weight:bold;letter-spacing:2px;")
            self._log("[ HOLD ] NAVIGATION SUSPENDED", "amber")
            self.status_bar.showMessage("[ HOLD ] — Press RESUME to continue")
        else:
            self.btn_pause.setText("[ HOLD ]")
            self.btn_pause.setStyleSheet(f"background:{C['amber_lt']};color:{C['amber']};"f"border:1px solid {C['amber_dk']};border-radius:0px;"f"font-family:Consolas;font-size:11px;font-weight:bold;letter-spacing:2px;")
            self._log("[ RESUME ] NAVIGATION ACTIVE", "green")
            self.status_bar.showMessage("[ ACTIVE ] Navigation running")
        self.btn_pause.style().unpolish(self.btn_pause)
        self.btn_pause.style().polish(self.btn_pause)

    def _reset_route(self):
        """Rotayı yeniden başlat — harita engelleri korunur."""
        was_paused = self.map_c.paused
        self.map_c.reset_route()
        if was_paused:
            self.map_c.paused = False
            self.btn_pause.setText("[ HOLD ]")
            self.btn_pause.setStyleSheet(f"background:{C['amber_lt']};color:{C['amber']};"f"border:1px solid {C['amber_dk']};border-radius:0px;"f"font-family:Consolas;font-size:11px;font-weight:bold;letter-spacing:2px;")
            self.btn_pause.style().unpolish(self.btn_pause)
            self.btn_pause.style().polish(self.btn_pause)
        self._log("[ REROUTE ] Route reset — map obstacles retained", "green")
        self.status_bar.showMessage("[ REROUTE ] Route reset — rover at LIMA")

    def _full_reset(self):
        """Haritayı, engelleri ve aracı tamamen sıfırla."""
        self.map_c.full_reset()
        self.btn_pause.setText("⏸  DURDUR")
        self.btn_pause.setObjectName("BtnAmber")
        self.btn_pause.style().unpolish(self.btn_pause)
        self.btn_pause.style().polish(self.btn_pause)
        self.spd_slider.setValue(10)
        self._log("[ RESET ] Full reset — map and rover reinitialized", "cyan")
        self.status_bar.showMessage("[ RESET ] Full reset complete")

    def _on_replan(self, direction_cmd: str):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        # Log rengi belirle
        if "D*" in direction_cmd and "A*" not in direction_cmd:
            col = C['lc_cyan']
        elif "A*" in direction_cmd:
            col = C['purple']
        elif "⚠" in direction_cmd or "ENGELİ" in direction_cmd:
            col = C['lc_amber']
        elif "★" in direction_cmd:
            col = "#FFD700"
        else:
            col = C['lc_green']

        msg  = f'<span style="color:{C["lc_dim"]};font-size:11px;">[{ts}]</span>&nbsp;'
        msg += f'<span style="color:{col};font-size:14px;font-weight:bold;">{direction_cmd}</span><br>'
        self.nav_log.append(msg)
        self.act_cmd.setText(direction_cmd[:50] + ("…" if len(direction_cmd) > 50 else ""))

        # Sayaç güncelle
        stats = self.map_c.nav.stats
        self.replan_cnt_lbl.setText(
            f"REPLAN:{stats['replans']}  D*:{stats['dstar_ok']}  "
            f"A*:{stats['astar_fallbacks']}  TEHLIKE:{stats['hazards']}")

        sb = self.nav_log.verticalScrollBar(); sb.setValue(sb.maximum())

    # ── Data Handler ──────────────────────────────────────────────────────────
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
        self.dust_v.setText(f"{d.get('dust_level',0):.0f}")

        # Toz uyarı rengi
        dust = d.get('dust_level', 0)
        if dust > 60:
            self.dust_v.setObjectName("LBigR")
        elif dust > 30:
            self.dust_v.setObjectName("LBigA")
        else:
            self.dust_v.setObjectName("LBigG")
        self.dust_v.style().unpolish(self.dust_v); self.dust_v.style().polish(self.dust_v)

        status = d.get("status", "UNKNOWN")
        self.st_val.setText(status)
        if any(x in status for x in ["OBSTACLE","WARNING","PROXIMITY","SHADOW","DUST"]):
            self.st_val.setStyleSheet(
                f"color:{C['amber']};font-size:14px;font-weight:bold;letter-spacing:2px;")
        elif any(x in status for x in ["STOP","ERROR","RECALC"]):
            self.st_val.setStyleSheet(
                f"color:{C['red']};font-size:14px;font-weight:bold;letter-spacing:2px;")
        else:
            self.st_val.setStyleSheet(
                f"color:{C['green']};font-size:14px;font-weight:bold;letter-spacing:2px;")

        self.p_lat.setText(f"{d.get('lat',0):.6f}")
        self.p_lon.setText(f"{d.get('lon',0):.6f}")
        self.p_alt.setText(f"{d.get('altitude',0):+.2f} m")
        self.p_obs.setText(f"{d.get('obstacle_dist',0):.2f} m")
        self.p_spd.setText(f"{d.get('speed',0):.3f} m/s")
        self.p_hdg.setText(f"{d.get('heading',0):.1f}°")
        gx,gy = self.map_c.nav.goal_g; n=self.map_c.og.n
        self.p_wpt.setText(f"({gx},{gy}) norm({gx/n:.2f},{gy/n:.2f})")
        self.p_rta.setText(f"{len(self.map_c.nav.path_norm)} pts")

        cmd = d.get("nav_cmd", "")
        if cmd:
            self._write_nav(cmd, d)

        self.map_c.update_rover(d)
        self.sim_feed.update_data(d)

        # Algoritma durum etiketi
        use_d = self.map_c.nav.use_dstar
        self.algo_lbl.setText(
            ("D* LITE AKTİF  |  A* YEDEK HAZIR" if use_d
             else "A* PLANlayici AKTİF  |  D* LITE HAZIR"))

    def _write_nav(self, cmd, d):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        if "OBSTACLE" in cmd or "PROXIMITY" in cmd or "BOULDER" in cmd:
            col, pfx = C["lc_amber"],  "HAZARD"
        elif "SHADOW" in cmd:
            col, pfx = C["purple"],    "SHADOW"
        elif "DUST" in cmd:
            col, pfx = C["lc_amber"],  "DUST"
        elif "WARNING" in cmd or "SLOPE" in cmd:
            col, pfx = C["lc_amber"],  "SLOPE"
        elif "TURN" in cmd:
            col, pfx = C["lc_cyan"],   "TURN"
        elif "WAYPOINT" in cmd:
            col, pfx = "#FFD700",      "WPT"
        elif "RECALC" in cmd:
            col, pfx = C["lc_red"],    "REPLAN"
        elif "CLEAR" in cmd or "REACHED" in cmd or "EXIT" in cmd:
            col, pfx = C["lc_green"],  "OK"
        else:
            col, pfx = C["lc_green"],  "FWD"

        msg  = f'<span style="color:{C["lc_dim"]};font-size:11px;">[{ts}]</span>&nbsp;'
        msg += f'<span style="color:{col};font-size:15px;font-weight:bold;">[{pfx}] {cmd}</span>'

        if "TURN" in cmd:
            pts = cmd.split("_")
            if len(pts) >= 3:
                msg += (f'<br><span style="color:#64748B;font-size:12px;">'
                        f'&nbsp;&nbsp;HDG:{d.get("heading",0):.1f}° → {pts[1]} {pts[2]}° | '
                        f'SPD:{d.get("speed",0):.3f} m/s</span>')
        elif "OBSTACLE" in cmd or "BOULDER" in cmd:
            msg += (f'<br><span style="color:#64748B;font-size:12px;">'
                    f'&nbsp;&nbsp;DIST:{d.get("obstacle_dist",0):.2f}m | '
                    f'D* Lite yeniden hesaplıyor...</span>')
        elif "SHADOW" in cmd:
            msg += (f'<br><span style="color:#64748B;font-size:12px;">'
                    f'&nbsp;&nbsp;Kamera kör → LiDAR-only mod aktif | '
                    f'SPD azaltılıyor</span>')
        elif "DUST" in cmd:
            msg += (f'<br><span style="color:#64748B;font-size:12px;">'
                    f'&nbsp;&nbsp;Toz kalınlığı:∼{d.get("dust_level",0):.0f}% | '
                    f'Trafik kabiliyeti: düşük</span>')
        elif "WAYPOINT" in cmd:
            msg += (f'<br><span style="color:#64748B;font-size:12px;">'
                    f'&nbsp;&nbsp;POS:{d.get("lat",0):.6f},{d.get("lon",0):.6f} | '
                    f'Sonraki WP hesaplanıyor...</span>')

        msg += "<br>"
        self.nav_log.append(msg)
        sb = self.nav_log.verticalScrollBar(); sb.setValue(sb.maximum())
        self.act_cmd.setText(f"[{pfx}] {cmd[:45]}")

    def _log(self, txt, key="green"):
        col = {"green":C["lc_green"],"cyan":C["lc_cyan"],
               "amber":C["lc_amber"],"red":C["lc_red"],
               "purple":C["purple"],"dim":C["lc_dim"]}.get(key, C["lc_green"])
        self.nav_log.append(f'<span style="color:{col};font-size:13px;">{txt}</span>')

    # ── Bağlantı ──────────────────────────────────────────────────────────────
    def _toggle_conn(self):
        if not self.sim_connected:
            host  = self.host_inp.text().strip() or "127.0.0.1"
            port  = self.port_inp.value()
            proto = self.proto.currentText()
            self.conn_btn.setEnabled(False)
            self.conn_btn.setText("DENENIYOR...")
            self.conn_status_lbl.setText(f"{proto} {host}:{port} deneniyor...")
            self.conn_status_lbl.setStyleSheet(f"color:{C['amber']};margin-left:4px;")
            QApplication.processEvents()

            ok = SimulinkReceiver.test_connection(host, port, proto)
            if not ok:
                self.conn_btn.setEnabled(True)
                self.conn_btn.setText("CONNECT")
                self.conn_status_lbl.setText(f"BAĞLANTI KURULAMADI  ({proto} {host}:{port})")
                self.conn_status_lbl.setStyleSheet(f"color:{C['red']};font-weight:bold;margin-left:4px;")
                self.status_bar.showMessage(f"HATA: {proto} {host}:{port} erişilemiyor — Demo devam ediyor")
                return

            self.demo.stop()
            self.recv.set_connection(host, port, proto)
            threading.Thread(target=self.recv.start_listening, daemon=True).start()
            self.sim_connected = True
            self.conn_btn.setEnabled(True)
            self.conn_btn.setText("■  KES"); self.conn_btn.setObjectName("BtnDisc")
            self.conn_btn.style().unpolish(self.conn_btn)
            self.conn_btn.style().polish(self.conn_btn)
            self.conn_status_lbl.setText(f"BAĞLANDI  {proto}  {host}:{port}")
            self.conn_status_lbl.setStyleSheet(f"color:{C['green']};font-weight:bold;margin-left:4px;")
            self.badge.setText(f"  ●  {proto}  {host}:{port}  ")
            self.badge.setStyleSheet(
                f"background:{C['green_lt']};color:{C['green']};"
                f"border:1px solid {C['green_dk']};border-radius:0px;padding:3px 10px;letter-spacing:2px;")
            self.status_bar.showMessage(f"BAĞLANDI: {proto} {host}:{port}")
            self._log(f"✦ SİMULINK BAĞLANTISI KURULDU — {proto} {host}:{port}", "green")
        else:
            self.recv.stop()
            self.sim_connected = False
            self.conn_btn.setEnabled(True)
            self.conn_btn.setText("CONNECT"); self.conn_btn.setObjectName("BtnConn")
            self.conn_btn.style().unpolish(self.conn_btn)
            self.conn_btn.style().polish(self.conn_btn)
            self.conn_status_lbl.setText("NOT CONNECTED")
            self.conn_status_lbl.setStyleSheet(f"color:{C['text3']};margin-left:4px;")
            self.badge.setText("  ○  DEMO  ")
            self.badge.setStyleSheet(
                f"background:{C['amber_lt']};color:{C['amber']};"
                f"border:1px solid {C['amber_dk']};border-radius:0px;padding:3px 10px;letter-spacing:2px;")
            self.status_bar.showMessage("Demo mode — Simulink bağlantısı kapatıldı")
            self._start_demo()

    def _on_conn_status(self, msg, ok):
        self.status_bar.showMessage(f"{'BAĞLI' if ok else 'HATA'}  {msg}")
        if ok:
            self.conn_status_lbl.setText(f"CONNECTED — {msg}")
            self.conn_status_lbl.setStyleSheet(f"color:{C['green']};font-weight:bold;margin-left:4px;")
        else:
            self.conn_status_lbl.setText(f"HATA: {msg}")
            self.conn_status_lbl.setStyleSheet(f"color:{C['red']};font-weight:bold;margin-left:4px;")
            self.sim_connected = False
            self.conn_btn.setText("CONNECT"); self.conn_btn.setObjectName("BtnConn")
            self.conn_btn.style().unpolish(self.conn_btn); self.conn_btn.style().polish(self.conn_btn)
            self.badge.setText("  ○  DEMO  ")
            self.badge.setStyleSheet(
                f"background:{C['amber_lt']};color:{C['amber']};"
                f"border:1px solid {C['amber_dk']};border-radius:0px;padding:3px 10px;letter-spacing:2px;")
            self._start_demo()

    def _start_demo(self):
        self.demo.t = 0; self.demo.battery = 92.0; self.demo.start()
        for line in [
            ("✦ UMAY GCS v4.0 başlatıldı — Demo mod aktif", "cyan"),
            ("✦ D* Lite + A* Hibrit Planlayıcı HAZIR", "cyan"),
            ("✦ LunarOccupancyGrid 50×50 yüklendi — Krater:5 Boulder:20 Toz:6 Gölge:8", "cyan"),
            ("✦ LunarSensorSuite: LiDAR · IMU · Kamera · Termal aktif", "cyan"),
            (f"✦ HEDEF: {self.map_c.GOAL_NORM}  |  BAŞLANGIÇ: {self.map_c.START_NORM}", "green"),
            ("── Haritaya tıklayarak engel ekleyebilirsin ──────────────────────", "dim"),
        ]:
            self._log(*line)

    def _tick_clk(self):
        self.clk.setText(datetime.utcnow().strftime("UTC  %Y-%m-%d  %H:%M:%S"))

    def closeEvent(self, e):
        self.demo.stop(); self.recv.stop(); e.accept()


# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("UMAY GCS")
    w = Dashboard()
    w.show()
    sys.exit(app.exec())
