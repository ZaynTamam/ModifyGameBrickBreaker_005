"""
ModifyGameBrickBreaker_005_Craft
================================
Brick Breaker - CRAFT EDITION (tema Minecraft, boss, roguelite)

Referensi awal : GeeksforGeeks - "Brick Breaker Game In Python using Pygame"
Dibuat dengan bantuan AI (Claude) lalu dimodifikasi/dikembangkan.

Catatan: ini game fan-made bergaya blok/pixel. Semua tekstur dan sprite digambar
dari kode (tanpa file aset), tidak memakai aset resmi apa pun.

FITUR UTAMA
-----------
* Blok bertekstur pixel: Dirt, Grass, Planks, Stone, Obsidian, Bedrock (tak bisa
  hancur), TNT (ledakan berantai), Diamond Ore (drop item pasti), Ender Crystal.
* 8 stage dengan 4 tema dunia (Overworld, Gua, Nether, The End):
  6 level biasa + 3 BOSS (Creeper Raksasa, Wither, Ender Dragon).
* Boss punya HP bar, fase 2 (di bawah 50% HP), dan serangan proyektil.
  Proyektil bisa dihancurkan dengan memukulnya pakai bola atau panah.
* Item jatuh bertema Minecraft: Perisai, Wither (jebakan), Soul Sand, Ender Pearl,
  Apel Emas, Busur, Pickaxe (bola menembus blok).
* ROGUELITE: tiap boss kalah (selain boss terakhir) pilih 1 dari 3 perk acak
  yang permanen sampai game selesai: Sharpness, Fortune, Looting, Unbreaking,
  Netherite Shield, Fire Aspect, Respawn Anchor, Regeneration, Health Boost,
  Totem of Undying.
* Combo & pengali skor, high score tersimpan (JSON), efek suara prosedural,
  partikel, screen shake, kontrol keyboard + mouse, 60 FPS dengan delta-time.
* MENU UTAMA baru: tombol bergaya blok, navigasi keyboard/mouse, layar
  Cara Bermain, Koleksi (blok/item/perk/boss), toggle suara (tersimpan), Keluar.

KONTROL
-------
  KIRI/KANAN atau A/D atau Mouse : gerakkan paddle
  SPACE / Klik kiri               : luncurkan bola / tembak panah
  1 / 2 / 3 atau klik kartu       : pilih perk setelah boss
  P atau ESC                      : pause

  Di menu:
  ATAS/BAWAH atau W/S atau Mouse  : pilih tombol
  ENTER / SPACE / Klik            : konfirmasi
  ESC                             : keluar (menu utama) / kembali (sub-menu)
"""

import json
import math
import os
import random
from array import array

import pygame

pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()

# ----------------------------------------------------------------------------
# KONSTANTA
# ----------------------------------------------------------------------------
WIDTH, HEIGHT = 800, 640
FPS = 60
HUD_H = 64

COLS = 12
BRICK_W, BRICK_H, GAP = 56, 24, 4
GRID_W = COLS * BRICK_W + (COLS - 1) * GAP
GRID_X = (WIDTH - GRID_W) // 2
GRID_Y_NORMAL = HUD_H + 34
GRID_Y_BOSS = 296
CELL = 4

BASE_LIVES = 3
BASE_MAX_LIVES = 5
BASE_PADDLE_W = 110

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (170, 180, 205)
GOLD = (255, 215, 90)

# Layout menu
GROUND_Y = HEIGHT - 48
BTN_W, BTN_H = 340, 46
BTN_Y0, BTN_STEP = 232, 58

# Layout stage. '.' kosong | d dirt | g grass | p planks | s stone (2 hit)
# o obsidian (3 hit) | b bedrock (tak bisa hancur) | t TNT | D diamond ore
# c ender crystal (3 hit)
LV1 = ["gggggggggggg",
       "dddpdddddpdd",
       "dddddddddddd",
       "ssddddddddss"]
LV2 = ["ssssssssssss",
       "sdddssssdddd",
       "ssDsssssssDs",
       "dddddddddddd",
       "bbsssbbsssbb"]
LV3 = ["dsdsdsdsdsds",
       "sDsssttsssDs",
       "sssssssssss.",
       "obbooooobbo."]
LV4 = ["tootootootoo",
       "osssssssssso",
       "ottbbbbbbtto",
       "sDsDsDsDsDsD"]
LV5 = ["oooooooooooo",
       "oDoDoDoDoDoD",
       "oooooooooooo",
       "bobobobobobo"]
B1 = ["d..d..dd..d.",
      ".p..pp..pp.."]
B2 = ["o....oo....o",
      "bb........bb"]
B3 = ["..c...c...c.",
      "oo........oo"]

STAGES = [
    {"name": "Padang Rumput", "layout": LV1, "theme": "day"},
    {"name": "Gua Batu", "layout": LV2, "theme": "cave"},
    {"name": "Creeper Raksasa", "layout": B1, "theme": "day", "boss": "creeper"},
    {"name": "Tambang Dalam", "layout": LV3, "theme": "cave"},
    {"name": "Nether", "layout": LV4, "theme": "nether"},
    {"name": "Wither", "layout": B2, "theme": "nether", "boss": "wither"},
    {"name": "The End", "layout": LV5, "theme": "end"},
    {"name": "Ender Dragon", "layout": B3, "theme": "end", "boss": "dragon"},
]
for _st in STAGES:
    for _row in _st["layout"]:
        assert len(_row) == COLS, "Panjang baris layout harus %d" % COLS

THEMES = {
    "day": ((105, 165, 240), (180, 222, 255)),
    "cave": ((24, 24, 28), (54, 54, 60)),
    "nether": ((48, 8, 8), (135, 34, 10)),
    "end": ((10, 6, 22), (34, 14, 56)),
}

BLOCK_INFO = {  # hp, poin, warna partikel
    "d": (1, 10, (134, 96, 67)),
    "g": (1, 10, (98, 164, 56)),
    "p": (1, 10, (168, 132, 76)),
    "s": (2, 25, (128, 128, 128)),
    "o": (3, 45, (70, 40, 120)),
    "b": (999, 0, (80, 80, 80)),
    "t": (1, 30, (205, 45, 35)),
    "D": (2, 80, (70, 230, 230)),
    "c": (3, 60, (255, 120, 220)),
}

CRACKS = [
    [(10, 2), (18, 10), (14, 18)],
    [(34, 22), (40, 12), (48, 16)],
    [(26, 3), (29, 12), (24, 21)],
]


# Sprite pixel 8x8
SPRITE_DEFS = {
    "apple": ([
        "....bg..", "...bgg..", ".yyyyyy.", "yywyyyYy",
        "ywyyyyYy", "yyyyyyYy", ".yyyyYy.", "..yYYy.."],
        {"y": (255, 215, 60), "Y": (200, 150, 20), "g": (60, 170, 60),
         "w": (255, 245, 170), "b": (110, 70, 30)}),
    "pearl": ([
        "..kkkk..", ".kEEEEk.", "kEEhhEEk", "kEhEEEEk",
        "kEEEEeEk", "kEEEeeEk", ".keeeek.", "..kkkk.."],
        {"k": (10, 60, 60), "e": (20, 130, 110), "E": (40, 190, 160),
         "h": (150, 255, 230)}),
    "arrow": ([
        "......tt", "......kt", ".....k..", "....k...",
        "...k....", ".fk.....", "ff......", "f......."],
        {"t": (170, 170, 185), "k": (150, 110, 60), "f": (235, 235, 235)}),
    "pickaxe": ([
        ".dddddd.", "dD.hh.Dd", "d..hh..d", "...hh...",
        "...hh...", "...hh...", "...hh...", "...hh..."],
        {"d": (80, 230, 230), "D": (30, 150, 170), "h": (140, 95, 45)}),
    "shield": ([
        "IIIIIIII", "IbbbbbbI", "IbiiiibI", "IbiiiibI",
        "IbbiibbI", ".IbbbbI.", "..IbbI..", "...II..."],
        {"I": (120, 120, 135), "b": (130, 85, 40), "i": (205, 205, 215)}),
    "soulsand": ([
        "NNNNNNNN", "NnnnnnnN", "NnknnknN", "NnknnknN",
        "NnnnnnnN", "NnkkkknN", "NnnnnnnN", "NNNNNNNN"],
        {"N": (60, 42, 34), "n": (95, 68, 52), "k": (20, 12, 10)}),
    "wither": ([
        "kkkkkkkk", "kggggggk", "kgkggkgk", "kgkggkgk",
        "kggkkggk", "kggggggk", "kgkgkgkk", "kkkkkkkk"],
        {"k": (25, 25, 30), "g": (110, 70, 150)}),
    "sword": ([
        "......dd", ".....ddd", "....ddd.", "b..ddd..",
        ".bddd...", "..bb....", ".hb.b...", "hh......"],
        {"d": (80, 230, 230), "b": (140, 95, 45), "h": (100, 65, 30)}),
    "heart": ([
        ".rr..rr.", "rrrrrrrr", "rwrrrrrr", "rrrrrrrr",
        ".rrrrrr.", "..rrrr..", "...rr...", "........"],
        {"r": (230, 50, 70), "w": (255, 170, 180)}),
    "diamond": ([
        "..dddd..", ".dwddDd.", "dwddddDd", "dddddDDd",
        ".dddDDd.", "..dDDd..", "...dd...", "........"],
        {"d": (70, 235, 230), "D": (30, 150, 170), "w": (200, 255, 255)}),
    "emerald": ([
        "..dddd..", ".dwddDd.", "dwddddDd", "dddddDDd",
        ".dddDDd.", "..dDDd..", "...dd...", "........"],
        {"d": (60, 220, 100), "D": (20, 130, 50), "w": (190, 255, 200)}),
    "fire": ([
        "...r....", "..rr.r..", "..rrrr..", ".rroorr.",
        ".roooor.", "rroyyoor", "rooyyoor", ".rooooo."],
        {"r": (220, 50, 20), "o": (255, 140, 20), "y": (255, 230, 90)}),
    "totem": ([
        "..yyyy..", ".yyyyyy.", "yykyykyy", "yyyyyyyy",
        ".yykkyy.", ".yyyyyy.", "..yyyy..", "...yy..."],
        {"y": (255, 215, 60), "k": (20, 110, 70)}),
}

# Power-up jatuh: kode -> (label, sprite, warna)
POWERUPS = {
    "W": ("Perisai", "shield", (190, 190, 205)),
    "N": ("Wither", "wither", (170, 100, 220)),
    "S": ("Soul Sand", "soulsand", (170, 125, 95)),
    "M": ("Ender Pearl", "pearl", (60, 220, 190)),
    "L": ("Apel Emas", "apple", (255, 215, 70)),
    "G": ("Busur", "arrow", (235, 235, 235)),
    "P": ("Pickaxe", "pickaxe", (80, 230, 230)),
}
POWER_WEIGHTS = [("W", 22), ("N", 12), ("S", 14), ("M", 18), ("L", 6),
                 ("G", 17), ("P", 12)]

# Perk roguelite
PERKS = {
    "sharpness": {"name": "Sharpness", "sprite": "sword", "max": 3,
                  "desc": ["Bola: +1 damage", "ke blok & boss"]},
    "fortune": {"name": "Fortune", "sprite": "diamond", "max": 3,
                "desc": ["Drop power-up", "lebih sering +7%"]},
    "looting": {"name": "Looting", "sprite": "emerald", "max": 3,
                "desc": ["Skor semua blok", "naik +25%"]},
    "unbreaking": {"name": "Unbreaking", "sprite": "pickaxe", "max": 3,
                   "desc": ["Durasi power-up", "lebih lama +40%"]},
    "shield": {"name": "Netherite Shield", "sprite": "shield", "max": 3,
               "desc": ["Paddle lebih lebar", "(+18 px)"]},
    "fire": {"name": "Fire Aspect", "sprite": "fire", "max": 3,
             "desc": ["25%: hit membakar", "blok di sekitarnya"]},
    "anchor": {"name": "Respawn Anchor", "sprite": "pearl", "max": 2,
               "desc": ["Bola selamat dari", "jatuh 1x per stage"]},
    "regen": {"name": "Regeneration", "sprite": "apple", "max": 2,
              "desc": ["+1 nyawa setiap", "stage selesai"]},
    "health": {"name": "Health Boost", "sprite": "heart", "max": 3,
               "desc": ["+1 nyawa maksimum", "& isi 1 nyawa"]},
    "totem": {"name": "Totem of Undying", "sprite": "totem", "max": 3,
              "desc": ["Hidup lagi saat", "nyawa habis (1x)"]},
}

# Teks untuk layar Koleksi
BLOCK_DESC = {
    "d": ("Dirt", "Hancur dalam 1 hit"),
    "g": ("Grass", "Hancur dalam 1 hit"),
    "p": ("Planks", "Hancur dalam 1 hit"),
    "s": ("Stone", "Butuh 2 hit"),
    "o": ("Obsidian", "Butuh 3 hit"),
    "b": ("Bedrock", "Tidak bisa dihancurkan"),
    "t": ("TNT", "Ledakan berantai"),
    "D": ("Diamond Ore", "2 hit, drop item pasti"),
    "c": ("Ender Crystal", "3 hit, lindungi Dragon"),
}
ITEM_DESC = {
    "W": "Paddle melebar sementara",
    "N": "Paddle menyempit (jebakan!)",
    "S": "Bola bergerak lebih lambat",
    "M": "Bola bertambah banyak",
    "L": "+1 nyawa",
    "G": "Paddle menembakkan panah",
    "P": "Bola menembus blok",
}
BOSS_INFO = [
    ("creeper", "Creeper Raksasa",
     "Melempar TNT ke arah paddle.", "Fase 2: TNT ganda & lebih cepat."),
    ("wither", "Wither",
     "Menembakkan tengkorak ke paddle.", "Fase 2: tiga tengkorak sekaligus."),
    ("dragon", "Ender Dragon",
     "Napas ungu menyebar 5 arah.", "Hancurkan Ender Crystal agar damage penuh!"),
]
CODEX_TABS = ["BLOK", "ITEM", "PERK", "BOSS"]
SPLASHES = ["Hancurkan semuanya!", "Pukul bolanya!", "Awas TNT!",
            "Kalahkan 3 boss!", "Bebas bedrock!", "Mine & Bounce!",
            "Pilih perkmu!", "100% blok!"]

(MENU, READY, PLAYING, PAUSED, LEVEL_CLEAR, PERK, GAME_OVER, WIN,
 HOWTO, CODEX) = range(10)

SAVE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "highscore_005_craft.json")


# ----------------------------------------------------------------------------
# HELPER
# ----------------------------------------------------------------------------
def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def shade(color, k):
    return tuple(int(clamp(c * k, 0, 255)) for c in color)


def hash_noise(x, y, seed=0):
    n = (x * 374761393 + y * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def vary(color, amt, n):
    return shade(color, 1 + (n - 0.5) * 2 * amt)


def block_cell_color(kind, cx, cy, n):
    if kind == "d":
        return vary((134, 96, 67), 0.18, n) if n > 0.12 else (96, 66, 44)
    if kind == "g":
        green = vary((98, 164, 56), 0.15, n)
        if cy < 2 or (cy == 2 and n < 0.55):
            return green
        return vary((134, 96, 67), 0.18, n)
    if kind == "p":
        base = (168, 132, 76)
        c = vary(base, 0.08, n)
        return shade(c, 0.72) if cy % 3 == 2 else c
    if kind == "s":
        c = vary((128, 128, 128), 0.16, n)
        return shade(c, 0.6) if n < 0.18 else c
    if kind == "o":
        c = vary((24, 18, 38), 0.4, n)
        return (95, 45, 160) if n > 0.9 else c
    if kind == "b":
        c = vary((70, 70, 70), 0.5, n)
        return (25, 25, 25) if n < 0.2 else c
    if kind == "t":
        if cy in (2, 3):
            return vary((235, 235, 235), 0.04, n)
        return vary((205, 45, 35), 0.12, n)
    if kind == "D":
        c = vary((128, 128, 128), 0.16, n)
        if n < 0.18:
            c = shade(c, 0.6)
        if n > 0.82:
            c = (70, 235, 230)
        elif n > 0.76:
            c = (30, 170, 190)
        return c
    return (255, 0, 255)


def make_block_texture(kind, font):
    surf = pygame.Surface((BRICK_W, BRICK_H))
    cw, ch = BRICK_W // CELL, BRICK_H // CELL
    for cy in range(ch):
        for cx in range(cw):
            col = block_cell_color(kind, cx, cy, hash_noise(cx, cy, ord(kind)))
            surf.fill(col, (cx * CELL, cy * CELL, CELL, CELL))
    if kind == "t":
        img = font.render("TNT", True, (30, 30, 30))
        surf.blit(img, img.get_rect(center=(BRICK_W // 2, BRICK_H // 2)))
    pygame.draw.rect(surf, shade(block_cell_color(kind, 0, 0, 0.5), 0.45),
                     (0, 0, BRICK_W, BRICK_H), 1)
    return surf


def make_button(w, h, hover):
    """Tombol bergaya blok batu: tekstur noise + bevel terang/gelap."""
    surf = pygame.Surface((w, h))
    base = (150, 152, 164) if hover else (112, 114, 122)
    for cy in range(h // CELL + 1):
        for cx in range(w // CELL + 1):
            n = hash_noise(cx, cy, 91 if hover else 90)
            surf.fill(vary(base, 0.07, n), (cx * CELL, cy * CELL, CELL, CELL))
    light, dark = shade(base, 1.3), shade(base, 0.55)
    pygame.draw.rect(surf, light, (0, 0, w, 3))
    pygame.draw.rect(surf, light, (0, 0, 3, h))
    pygame.draw.rect(surf, dark, (0, h - 4, w, 4))
    pygame.draw.rect(surf, dark, (w - 3, 0, 3, h))
    return surf


def make_sprite(grid, palette, scale):
    size = len(grid) * scale
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch != ".":
                s.fill(palette[ch], (x * scale, y * scale, scale, scale))
    return s


def make_textured_grid(grid, scale, colorfn, seed):
    """Tekstur pixel dari grid 8x8, tiap sel dibagi 2x2 blok dengan noise."""
    size = len(grid) * scale
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    sub = scale // 2
    for gy, row in enumerate(grid):
        for gx, ch in enumerate(row):
            base, amt = colorfn(ch)
            for sy in (0, 1):
                for sx in (0, 1):
                    n = hash_noise(gx * 2 + sx, gy * 2 + sy, seed)
                    s.fill(vary(base, amt, n),
                           (gx * scale + sx * sub, gy * scale + sy * sub, sub, sub))
    return s


class Sprites:
    def __init__(self):
        self.cache = {}

    def get(self, name, scale):
        key = (name, scale)
        if key not in self.cache:
            grid, pal = SPRITE_DEFS[name]
            self.cache[key] = make_sprite(grid, pal, scale)
        return self.cache[key]


# ----------------------------------------------------------------------------
# SUARA (prosedural)
# ----------------------------------------------------------------------------
class Sfx:
    RATE = 22050

    def __init__(self):
        self.sounds = {}
        self.ok = False
        self.muted = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(self.RATE, -16, 1, 512)
            self.ok = pygame.mixer.get_init() is not None
        except pygame.error:
            self.ok = False
        if not self.ok:
            return
        mk = self._make
        self.sounds = {
            "launch": mk([(380, 90, 0.30, 0.8, False)]),
            "paddle": mk([(300, 70, 0.35, 0.4, False)]),
            "brick": mk([(260, 60, 0.35, -0.3, False)]),
            "strong": mk([(200, 70, 0.35, -0.2, False)]),
            "metal": mk([(150, 70, 0.30, -0.1, False)]),
            "explode": mk([(0, 280, 0.45, 0.0, True)]),
            "powerup": mk([(520, 70, 0.30, 0, False), (780, 110, 0.30, 0, False)]),
            "laser": mk([(900, 80, 0.20, -0.6, False)]),
            "lose": mk([(300, 380, 0.40, -0.75, False)]),
            "hurt": mk([(220, 160, 0.40, -0.5, False)]),
            "boss_hit": mk([(130, 90, 0.40, 0.3, False)]),
            "boss_die": mk([(0, 650, 0.50, 0.0, True)]),
            "perk": mk([(523, 90, 0.30, 0, False), (659, 90, 0.30, 0, False),
                        (784, 90, 0.30, 0, False), (1046, 200, 0.30, 0, False)]),
            "clear": mk([(523, 110, 0.30, 0, False), (659, 110, 0.30, 0, False),
                         (784, 110, 0.30, 0, False), (1046, 220, 0.30, 0, False)]),
            "gameover": mk([(392, 200, 0.35, 0, False), (330, 200, 0.35, 0, False),
                            (262, 380, 0.35, 0, False)]),
        }

    def _make(self, notes):
        buf = array("h")
        for freq, ms, vol, sweep, noise in notes:
            n = int(self.RATE * ms / 1000)
            phase = 0.0
            for i in range(n):
                t = i / n
                if noise:
                    s = random.uniform(-1, 1)
                else:
                    phase += 2 * math.pi * freq * (1 + sweep * t) / self.RATE
                    s = (math.sin(phase) + 0.3 * math.sin(2 * phase)) / 1.3
                env = min(1.0, i / 120) * (1 - t) ** 1.4
                buf.append(int(s * env * vol * 32767))
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def play(self, name):
        if self.ok and not self.muted and name in self.sounds:
            self.sounds[name].play()


# ----------------------------------------------------------------------------
# OBJEK GAME
# ----------------------------------------------------------------------------
class Paddle:
    def __init__(self):
        self.base_w = float(BASE_PADDLE_W)
        self.w = self.base_w
        self.target_w = self.base_w
        self.h = 16
        self.x = WIDTH / 2
        self.y = HEIGHT - 48
        self.speed = 10.0
        self.effect_timer = 0.0
        self.laser_timer = 0.0
        self.laser_cd = 0.0

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y), int(self.w), self.h)

    def reset_effects(self):
        self.target_w = self.base_w
        self.effect_timer = 0.0
        self.laser_timer = 0.0
        self.laser_cd = 0.0

    def clamp_x(self):
        self.x = clamp(self.x, self.w / 2, WIDTH - self.w / 2)

    def update(self, dt, f):
        if self.effect_timer > 0:
            self.effect_timer -= dt
        if self.effect_timer <= 0:
            self.target_w = self.base_w
        if self.laser_timer > 0:
            self.laser_timer -= dt
        if self.laser_cd > 0:
            self.laser_cd -= dt
        self.w += (self.target_w - self.w) * min(1.0, 0.2 * f)
        self.clamp_x()

    def draw(self, surf):
        r = self.rect
        for i in range(0, r.w, CELL):
            cw = min(CELL, r.w - i)
            for j in range(4):
                n = hash_noise(i // CELL, j, 7)
                col = vary((88, 205, 228), 0.15, n)
                if j == 0:
                    col = shade(col, 1.25)
                elif j == 3:
                    col = shade(col, 0.7)
                pygame.draw.rect(surf, col, (r.x + i, r.y + j * CELL, cw, CELL))
        pygame.draw.rect(surf, (20, 70, 90), r, 1)
        if self.laser_timer > 0:
            for cx in (r.left + 8, r.right - 14):
                pygame.draw.rect(surf, (150, 110, 60), (cx, r.y - 10, 6, 10))
                pygame.draw.rect(surf, (200, 200, 210), (cx - 1, r.y - 14, 8, 5))


class Ball:
    def __init__(self, x, y, speed, stuck=True):
        self.x, self.y = x, y
        self.r = 8
        self.speed = speed
        self.dx, self.dy = 0.0, -1.0
        self.stuck = stuck
        self.dead = False
        self.trail = []
        self.touching = set()

    def set_angle(self, deg):
        a = math.radians(deg)
        self.dx, self.dy = math.sin(a), -math.cos(a)

    def fix_dir(self):
        if abs(self.dy) < 0.22:
            self.dy = 0.22 if self.dy >= 0 else -0.22
        n = math.hypot(self.dx, self.dy)
        self.dx /= n
        self.dy /= n


FLASH = {"brick": None}
TEX = {}


class Brick:
    def __init__(self, x, y, kind, col):
        self.rect = pygame.Rect(x, y, BRICK_W, BRICK_H)
        self.kind = kind
        self.col = col
        self.max_hp = BLOCK_INFO[kind][0]
        self.hp = self.max_hp
        self.points = BLOCK_INFO[kind][1]
        self.alive = True
        self.flash = 0

    @property
    def breakable(self):
        return self.kind != "b"

    def particle_color(self):
        return BLOCK_INFO[self.kind][2]

    def draw(self, surf):
        r = self.rect
        if self.kind == "c":
            pygame.draw.rect(surf, (50, 20, 80), r)
            pygame.draw.rect(surf, (110, 50, 170), r, 2)
            cx, cy = r.center
            pygame.draw.polygon(surf, (255, 120, 220),
                                [(cx, r.top + 2), (cx + 14, cy), (cx, r.bottom - 2),
                                 (cx - 14, cy)])
            pygame.draw.polygon(surf, (255, 220, 250),
                                [(cx, r.top + 6), (cx + 6, cy), (cx, r.bottom - 6),
                                 (cx - 6, cy)])
        else:
            surf.blit(TEX[self.kind], r)
        if self.hp < self.max_hp and self.kind != "b":
            n = min(3, 1 + int((1 - self.hp / self.max_hp) * 3))
            for path in CRACKS[:n]:
                pts = [(r.x + px, r.y + py) for px, py in path]
                pygame.draw.line(surf, (15, 15, 15), pts[0], pts[1], 2)
                pygame.draw.line(surf, (15, 15, 15), pts[1], pts[2], 2)
        if self.flash > 0:
            self.flash -= 1
            if FLASH["brick"] is not None:
                surf.blit(FLASH["brick"], r)


class PowerUp:
    def __init__(self, x, y, kind):
        self.x, self.y = x, y
        self.kind = kind
        self.w, self.h = 24, 24
        self.t = 0.0

    @property
    def rect(self):
        return pygame.Rect(int(self.x - 12), int(self.y - 12), 24, 24)

    def update(self, f):
        self.y += 2.8 * f
        self.t += f

    def draw(self, surf, sprites):
        spr = sprites.get(POWERUPS[self.kind][1], 3)
        bob = int(math.sin(self.t * 0.15) * 2)
        pygame.draw.circle(surf, (0, 0, 0), (int(self.x), int(self.y) + 14), 8)
        pygame.draw.rect(surf, POWERUPS[self.kind][2],
                         (int(self.x) - 15, int(self.y) - 15 + bob, 30, 30), 2)
        surf.blit(spr, (int(self.x) - 12, int(self.y) - 12 + bob))


class Projectile:
    def __init__(self, kind, x, y, vx, vy):
        self.kind = kind
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.w = 24 if kind == "tnt" else 18
        self.h = self.w
        self.dead = False
        self.t = 0.0

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h / 2),
                           self.w, self.h)

    def update(self, f):
        self.x += self.vx * f
        self.y += self.vy * f
        self.t += f
        if self.y > HEIGHT + 30 or self.x < -40 or self.x > WIDTH + 40:
            self.dead = True

    def draw(self, surf):
        r = self.rect
        if self.kind == "tnt":
            blink = int(self.t / 6) % 2 == 0
            pygame.draw.rect(surf, (235, 235, 235) if blink else (205, 45, 35), r)
            pygame.draw.rect(surf, (205, 45, 35), (r.x, r.y, r.w, 8))
            pygame.draw.rect(surf, (205, 45, 35), (r.x, r.bottom - 8, r.w, 8))
            pygame.draw.rect(surf, BLACK, r, 2)
        elif self.kind == "skull":
            pygame.draw.rect(surf, (60, 60, 68), r)
            pygame.draw.rect(surf, BLACK, (r.x + 3, r.y + 5, 4, 4))
            pygame.draw.rect(surf, BLACK, (r.right - 7, r.y + 5, 4, 4))
            pygame.draw.rect(surf, (180, 40, 200), r, 2)
        else:
            pygame.draw.circle(surf, (120, 40, 170), r.center, 11)
            pygame.draw.circle(surf, (210, 90, 240), r.center, 7)
            pygame.draw.circle(surf, (255, 220, 255), r.center, 3)


BOSS_DATA = {
    "creeper": {"name": "Creeper Raksasa", "hp": 26, "w": 128, "h": 128},
    "wither": {"name": "Wither", "hp": 38, "w": 208, "h": 64},
    "dragon": {"name": "Ender Dragon", "hp": 52, "w": 200, "h": 72},
}


class Boss:
    def __init__(self, kind):
        d = BOSS_DATA[kind]
        self.kind = kind
        self.name = d["name"]
        self.max_hp = float(d["hp"])
        self.hp = self.max_hp
        self.w, self.h = d["w"], d["h"]
        self.x = WIDTH / 2 - self.w / 2
        self.base_y = float(HUD_H + 30)
        self.y = self.base_y
        self.vx = random.choice((-1.2, 1.2))
        self.t = 0.0
        self.attack_cd = 2.5
        self.alive = True
        self.hurt_cd = 0.0
        self.flash = 0.0
        self.phase = 1
        self.dir = 1

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def interval(self):
        base = {"creeper": 3.0, "wither": 1.7, "dragon": 3.0}[self.kind]
        return base if self.phase == 1 else base * 0.65

    def update(self, dt, f, game):
        self.t += dt
        if self.hurt_cd > 0:
            self.hurt_cd -= dt
        if self.flash > 0:
            self.flash -= dt
        spd = 1.0 if self.phase == 1 else 1.5
        if self.kind in ("creeper", "wither"):
            self.x += self.vx * spd * f
            if self.x < 10:
                self.x, self.vx = 10, abs(self.vx)
            elif self.x + self.w > WIDTH - 10:
                self.x, self.vx = WIDTH - 10 - self.w, -abs(self.vx)
            if self.kind == "wither":
                self.y = self.base_y + math.sin(self.t * 2) * 10
        else:
            amp = WIDTH / 2 - self.w / 2 - 20
            self.x = WIDTH / 2 - self.w / 2 + math.sin(self.t * 0.8 * spd) * amp
            self.dir = 1 if math.cos(self.t * 0.8 * spd) >= 0 else -1
            self.y = self.base_y + math.sin(self.t * 1.7) * 14
        self.attack_cd -= dt
        if self.attack_cd <= 0:
            self.attack(game)
            self.attack_cd = self.interval()

    def attack(self, game):
        px = game.paddle.x
        r = self.rect
        cx, cy = r.centerx, r.bottom - 8
        if self.kind == "creeper":
            game.shoot("tnt", cx, cy, px, 3.2)
            if self.phase == 2:
                game.shoot("tnt", cx, cy, px + random.choice((-110, 110)), 3.2)
        elif self.kind == "wither":
            if self.phase == 1:
                game.shoot("skull", cx, cy, px, 3.8)
            else:
                for off in (-110, 0, 110):
                    game.shoot("skull", cx, cy, px + off, 3.8)
        else:
            scale = 1.0 if self.phase == 2 else 0.7
            for off in (-200, -100, 0, 100, 200):
                game.shoot("breath", cx, cy, px + off * scale, 3.0)



# ----------------------------------------------------------------------------
# FUNGSI TABRAKAN
# ----------------------------------------------------------------------------
def circle_rect(ball, rect):
    """Return (d2, dx, dy, push) bila bola menabrak rect, selain itu None."""
    cx = clamp(ball.x, rect.left, rect.right)
    cy = clamp(ball.y, rect.top, rect.bottom)
    dx, dy = ball.x - cx, ball.y - cy
    d2 = dx * dx + dy * dy
    if d2 >= ball.r * ball.r:
        return None
    if d2 == 0:
        l, rt = ball.x - rect.left, rect.right - ball.x
        tp, bt = ball.y - rect.top, rect.bottom - ball.y
        m = min(l, rt, tp, bt)
        if m == l:
            dx, dy = -1.0, 0.0
        elif m == rt:
            dx, dy = 1.0, 0.0
        elif m == tp:
            dx, dy = 0.0, -1.0
        else:
            dx, dy = 0.0, 1.0
        push = ball.r + m
    else:
        push = ball.r - math.sqrt(d2)
    return d2, dx, dy, push


def bounce(ball, dx, dy, push):
    if abs(dx) > abs(dy):
        sgn = 1 if dx > 0 else -1
        ball.dx = abs(ball.dx) * sgn
        ball.x += push * sgn
    else:
        sgn = 1 if dy > 0 else -1
        ball.dy = abs(ball.dy) * sgn
        ball.y += push * sgn


# ----------------------------------------------------------------------------
# GAME MANAGER
# ----------------------------------------------------------------------------
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Brick Breaker - Craft Edition (005)")
        self.canvas = pygame.Surface((WIDTH, HEIGHT)).convert()
        self.clock = pygame.time.Clock()
        self.sfx = Sfx()

        self.f_title = pygame.font.Font(None, 84)
        self.f_big = pygame.font.Font(None, 56)
        self.f_med = pygame.font.Font(None, 32)
        self.f_small = pygame.font.Font(None, 24)
        self.f_tiny = pygame.font.Font(None, 20)

        self.sprites = Sprites()
        for k in BLOCK_INFO:
            if k != "c":
                TEX[k] = make_block_texture(k, self.f_tiny)
        fl = pygame.Surface((BRICK_W, BRICK_H), pygame.SRCALPHA)
        fl.fill((255, 255, 255, 110))
        FLASH["brick"] = fl
        self.ball_imgs = {
            "normal": self._make_ball((205, 220, 240), (250, 252, 255)),
            "fire": self._make_ball((255, 120, 20), (255, 225, 90)),
        }
        self.boss_tex = self._make_boss_textures()
        self.boss_flash = {}
        for k, t in self.boss_tex.items():
            o = pygame.Surface(t.get_rect().size, pygame.SRCALPHA)
            o.fill((255, 255, 255, 140))
            self.boss_flash[k] = o
        self.boss_icons = self._make_boss_icons()

        self.bgs = {name: self._make_bg(*cols) for name, cols in THEMES.items()}
        self.dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.dim.fill((0, 0, 8, 170))
        self.dim_light = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.dim_light.fill((0, 0, 20, 110))
        self.glow_ball = self._make_glow(24, (150, 210, 255))
        self.btn_cache = {}
        self.fade = 1.0
        self.fade_surf = pygame.Surface((WIDTH, HEIGHT))
        self.fade_surf.fill(BLACK)
        self.heart_off = self.sprites.get("heart", 2).copy()
        self.heart_off.set_alpha(55)
        self.pause_sel = 0
        self.ready_t = 0.0
        self.banner = True
        self.new_record = False

        # dekor menu
        self.hills = []
        for x in range(0, WIDTH + 32, 32):
            far = 60 + int(26 * math.sin(x * 0.011) + 14 * math.sin(x * 0.031 + 1))
            near = 24 + int(14 * math.sin(x * 0.02 + 2) + 8 * math.sin(x * 0.05))
            self.hills.append((x, far, near))
        self.menu_blocks = [(46, 236, "g", 0.0), (112, 336, "D", 1.3),
                            (54, 436, "t", 2.6), (694, 256, "s", 0.8),
                            (640, 356, "o", 2.1), (700, 456, "d", 3.4)]
        self.splash = random.choice(SPLASHES)
        self.menu_sel = 0
        self.codex_page = 0

        save = self._read_save()
        try:
            self.high = int(save.get("high", 0))
        except (TypeError, ValueError):
            self.high = 0
        self.sfx.muted = bool(save.get("muted", False))
        self.running = True
        self.state = MENU
        self.prev_state = READY
        self.state_timer = 0.0
        self.mouse_mode = False
        self.mouse_x = WIDTH / 2
        self.t = 0.0
        self.shake = 0

        self.paddle = Paddle()
        self.bricks, self.balls, self.powerups = [], [], []
        self.lasers, self.particles, self.texts = [], [], []
        self.projectiles = []
        self.boss = None
        self.theme = "day"
        self.bg_items = self.make_bg_items("day")
        self.score = 0
        self.lives = BASE_LIVES
        self.max_lives = BASE_MAX_LIVES
        self.stage_idx = 0
        self.combo = 0
        self.slow_timer = 0.0
        self.pierce_timer = 0.0
        self.invuln = 0.0
        self.anchor_left = 0
        self.base_speed = 6.0
        self.bonus = 0
        self.perks = {}
        self.totems = 0
        self.perk_choices = []
        self.perk_sel = 0
        self.cleared_boss = False

    # ----- pembuatan aset -----
    def _make_ball(self, outline, fill):
        pat = [".aaa.", "abbba", "abbba", "abbba", ".aaa."]
        return make_sprite(pat, {"a": outline, "b": fill}, 3)

    def _make_glow(self, radius, color):
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for i in range(radius, 0, -1):
            a = int(80 * (1 - i / radius) ** 2)
            pygame.draw.circle(surf, (*color, a), (radius, radius), i)
        return surf

    def _make_bg(self, top, bot):
        bg = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            k = y / HEIGHT
            pygame.draw.line(bg, tuple(int(top[i] + (bot[i] - top[i]) * k)
                                       for i in range(3)), (0, y), (WIDTH, y))
        return bg.convert()

    def _make_boss_textures(self):
        creeper = ["gggggggg", "gggggggg", "gkkggkkg", "gkkggkkg",
                   "gggkkggg", "ggkkkkgg", "ggkkkkgg", "ggkggkgg"]
        skull = ["gggggggg", "gggggggg", "gkkggkkg", "gkwggwkg",
                 "gggkkggg", "gggggggg", "gkgkgkgg", "gkgkgkgg"]

        def cfn(ch):
            return {"g": ((80, 185, 65), 0.22), "k": ((12, 22, 12), 0.2)}[ch]

        def wfn(ch):
            return {"g": ((78, 78, 86), 0.18), "k": ((10, 10, 12), 0.15),
                    "w": ((235, 235, 235), 0.0)}[ch]

        ctex = make_textured_grid(creeper, 16, cfn, 3)
        one = make_textured_grid(skull, 8, wfn, 5)
        wtex = pygame.Surface((208, 64), pygame.SRCALPHA)
        for i in range(3):
            wtex.blit(one, (i * 72, 0))
        return {"creeper": ctex, "wither": wtex}

    def _make_boss_icons(self):
        icons = {
            "creeper": pygame.transform.scale(self.boss_tex["creeper"], (88, 88)),
            "wither": pygame.transform.scale(self.boss_tex["wither"], (144, 44)),
        }
        d = pygame.Surface((144, 44), pygame.SRCALPHA)
        for i in range(144 // 8):
            for j in range(44 // 8 + 1):
                n = hash_noise(i, j, 31)
                col = vary((28, 22, 40), 0.5, n)
                if n > 0.93:
                    col = (70, 40, 110)
                d.fill(col, (i * 8, j * 8, 8, 8))
        pygame.draw.rect(d, (90, 60, 130), d.get_rect(), 2)
        d.fill((255, 80, 230), (96, 10, 12, 8))
        d.fill((255, 80, 230), (118, 22, 12, 8))
        icons["dragon"] = d
        return icons

    def get_button(self, w, h, hover):
        key = (w, h, hover)
        if key not in self.btn_cache:
            self.btn_cache[key] = make_button(w, h, hover)
        return self.btn_cache[key]

    def make_bg_items(self, theme):
        items = []
        if theme == "day":
            for _ in range(6):
                items.append([random.uniform(0, WIDTH), random.uniform(80, 360),
                              random.uniform(0.15, 0.4), 1, (245, 250, 255)])
        else:
            col = {"cave": (120, 120, 130), "nether": (255, 140, 40),
                   "end": (200, 150, 255)}[theme]
            for _ in range(60):
                items.append([random.uniform(0, WIDTH), random.uniform(0, HEIGHT),
                              random.uniform(0.2, 0.8), random.choice((2, 2, 4)),
                              shade(col, random.uniform(0.5, 1.0))])
        return items

    # ----- penyimpanan -----
    def _read_save(self):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def save_high(self):
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as fh:
                json.dump({"high": self.high, "muted": self.sfx.muted}, fh)
        except OSError:
            pass

    def update_high(self):
        if self.score > self.high:
            self.high = self.score

    # ----- perk helper -----
    def lv(self, pid):
        return self.perks.get(pid, 0)

    def dmg(self):
        return 1 + self.lv("sharpness")

    def drop_chance(self):
        return 0.16 + 0.07 * self.lv("fortune")

    def dur_mult(self):
        return 1 + 0.4 * self.lv("unbreaking")

    def multiplier(self):
        return (1 + min(self.combo // 4, 4)) * (1 + 0.25 * self.lv("looting"))

    def refresh_perk_stats(self):
        self.max_lives = BASE_MAX_LIVES + self.lv("health")
        self.paddle.base_w = float(BASE_PADDLE_W + 18 * self.lv("shield"))

    # ----- menu -----
    def menu_items(self):
        return [("MULAI MAIN", "sword"),
                ("CARA BERMAIN", "arrow"),
                ("KOLEKSI", "diamond"),
                ("SUARA : %s" % ("MATI" if self.sfx.muted else "HIDUP"), "pearl"),
                ("KELUAR", "shield")]

    def menu_rect(self, i):
        return pygame.Rect((WIDTH - BTN_W) // 2, BTN_Y0 + i * BTN_STEP, BTN_W, BTN_H)

    def menu_at(self, pos):
        for i in range(len(self.menu_items())):
            if self.menu_rect(i).collidepoint(pos):
                return i
        return None

    def menu_activate(self, i):
        self.sfx.play("brick")
        if i == 0:
            self.start_game()
        elif i == 1:
            self.state = HOWTO
        elif i == 2:
            self.codex_page = 0
            self.state = CODEX
        elif i == 3:
            self.sfx.muted = not self.sfx.muted
            self.save_high()
            self.sfx.play("powerup")
        elif i == 4:
            self.running = False

    def go_menu(self, keep_sel=False):
        self.state = MENU
        self.fade = 1.0
        self.theme = "day"
        self.bg_items = self.make_bg_items("day")
        self.balls, self.powerups, self.lasers = [], [], []
        self.projectiles = []
        self.shake = 0
        if not keep_sel:
            self.menu_sel = 0
            self.splash = random.choice(SPLASHES)

    # ----- menu pause -----
    def pause_items(self):
        return [("LANJUT", "sword"),
                ("SUARA : %s" % ("MATI" if self.sfx.muted else "HIDUP"), "pearl"),
                ("MENU UTAMA", "shield")]

    def pause_rect(self, i):
        return pygame.Rect((WIDTH - BTN_W) // 2, 250 + i * BTN_STEP, BTN_W, BTN_H)

    def pause_at(self, pos):
        for i in range(len(self.pause_items())):
            if self.pause_rect(i).collidepoint(pos):
                return i
        return None

    def pause_activate(self, i):
        self.sfx.play("brick")
        if i == 0:
            self.state = self.prev_state
        elif i == 1:
            self.sfx.muted = not self.sfx.muted
            self.save_high()
            self.sfx.play("powerup")
        elif i == 2:
            self.update_high()
            self.save_high()
            self.go_menu()

    def back_rect(self):
        return pygame.Rect(WIDTH // 2 - 110, 584, 220, 40)

    def codex_tab_rect(self, i):
        return pygame.Rect(60 + i * 128, 104, 118, 34)

    # ----- alur game -----
    def start_game(self):
        self.score = 0
        self.lives = BASE_LIVES
        self.perks = {}
        self.totems = 0
        self.combo = 0
        self.refresh_perk_stats()
        self.paddle.w = self.paddle.base_w
        self.load_stage(0)

    def load_stage(self, idx):
        self.stage_idx = idx
        st = STAGES[idx]
        gy = GRID_Y_BOSS if st.get("boss") else GRID_Y_NORMAL
        self.bricks = []
        for r, row in enumerate(st["layout"]):
            for c, ch in enumerate(row):
                if ch != ".":
                    self.bricks.append(Brick(GRID_X + c * (BRICK_W + GAP),
                                             gy + r * (BRICK_H + GAP), ch, c))
        self.boss = Boss(st["boss"]) if st.get("boss") else None
        self.theme = st["theme"]
        self.bg_items = self.make_bg_items(self.theme)
        self.base_speed = min(9.0, 6.0 + 0.4 * idx)
        self.powerups, self.lasers, self.balls = [], [], []
        self.projectiles = []
        self.paddle.reset_effects()
        self.paddle.x = WIDTH / 2
        self.slow_timer = 0.0
        self.pierce_timer = 0.0
        self.invuln = 0.0
        self.combo = 0
        self.anchor_left = self.lv("anchor")
        self.spawn_ball()
        self.state = READY
        self.ready_t = 0.0
        self.banner = True
        self.fade = 1.0

    def spawn_ball(self):
        p = self.paddle
        self.balls = [Ball(p.x, p.y - 9, self.base_speed, stuck=True)]

    def launch(self):
        for b in self.balls:
            if b.stuck:
                b.stuck = False
                b.set_angle(random.choice((-1, 1)) * random.uniform(12, 28))
        self.sfx.play("launch")
        self.state = PLAYING

    def action(self):
        if self.state == MENU:
            self.menu_activate(self.menu_sel)
        elif self.state in (GAME_OVER, WIN):
            self.start_game()
        elif self.state == READY:
            self.launch()
        elif self.state == PLAYING:
            self.fire_laser()
        elif self.state == LEVEL_CLEAR:
            self.proceed()
        elif self.state == PERK:
            self.confirm_perk(self.perk_sel)
        elif self.state == PAUSED:
            self.state = self.prev_state

    def is_last_stage(self):
        return self.stage_idx + 1 >= len(STAGES)

    def stage_clear(self, boss=False):
        self.bonus = self.lives * 100 + (self.stage_idx + 1) * 100 + (500 if boss else 0)
        self.score += self.bonus
        self.lives = min(self.max_lives, self.lives + self.lv("regen"))
        self.update_high()
        self.balls, self.powerups, self.lasers = [], [], []
        self.projectiles = []
        self.cleared_boss = boss
        self.state = LEVEL_CLEAR
        self.state_timer = 4.0 if boss else 3.0
        self.sfx.play("clear")
        self.confetti()

    def proceed(self):
        if self.cleared_boss and self.is_last_stage():
            self.win()
        elif self.cleared_boss:
            self.open_perk_screen()
        else:
            self.load_stage(self.stage_idx + 1)

    def open_perk_screen(self):
        pool = [p for p in PERKS if self.lv(p) < PERKS[p]["max"]]
        self.perk_choices = random.sample(pool, min(3, len(pool)))
        self.perk_sel = 0
        self.state = PERK
        self.sfx.play("perk")

    def confirm_perk(self, i):
        if not (0 <= i < len(self.perk_choices)):
            return
        pid = self.perk_choices[i]
        self.perks[pid] = self.lv(pid) + 1
        if pid == "totem":
            self.totems += 1
        if pid == "health":
            self.refresh_perk_stats()
            self.lives = min(self.max_lives, self.lives + 1)
        self.refresh_perk_stats()
        self.sfx.play("powerup")
        self.load_stage(self.stage_idx + 1)

    def win(self):
        self.state = WIN
        self.new_record = self.score > self.high
        self.update_high()
        self.save_high()
        self.confetti()

    def game_over(self):
        self.state = GAME_OVER
        self.new_record = self.score > self.high
        self.update_high()
        self.save_high()
        self.sfx.play("gameover")

    def damage_player(self, from_ball):
        """Kurangi nyawa. Return True jika game over."""
        self.lives -= 1
        self.combo = 0
        self.shake = 14
        self.sfx.play("lose" if from_ball else "hurt")
        if self.lives <= 0:
            if self.totems > 0:
                self.totems -= 1
                self.lives = 2
                self.invuln = 2.0
                self.float_text(self.paddle.x, self.paddle.y - 30, "TOTEM!", GOLD)
                self.particles_at(self.paddle.x, self.paddle.y, GOLD, 30, 5.0)
                return False
            self.game_over()
            return True
        return False

    def lose_ball(self):
        if self.damage_player(True):
            return
        self.powerups, self.lasers, self.projectiles = [], [], []
        self.paddle.reset_effects()
        self.slow_timer = 0.0
        self.pierce_timer = 0.0
        self.spawn_ball()
        self.state = READY
        self.ready_t = 0.0
        self.banner = False

    def hurt_player(self):
        if self.invuln > 0:
            return
        if not self.damage_player(False):
            self.invuln = 1.6

    # ----- efek -----
    def particles_at(self, x, y, color, n=10, speed=3.0):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            s = random.uniform(0.4, 1.0) * speed
            self.particles.append([x, y, math.cos(a) * s, math.sin(a) * s - 0.8,
                                   random.uniform(0.35, 0.8), color,
                                   random.choice((3, 4, 6))])
        if len(self.particles) > 450:
            del self.particles[:len(self.particles) - 450]

    def confetti(self):
        pal = [(98, 164, 56), (255, 215, 60), (70, 230, 230), (205, 45, 35)]
        for _ in range(90):
            self.particles_at(random.uniform(80, WIDTH - 80),
                              random.uniform(120, 300), random.choice(pal), 1, 4.5)

    def float_text(self, x, y, msg, color=WHITE):
        self.texts.append([x, y, msg, 0.9, color])

    # ----- blok -----
    def hit_brick(self, b, damage=1):
        if not b.breakable:
            self.sfx.play("metal")
            self.particles_at(b.rect.centerx, b.rect.centery, (200, 200, 210), 4, 2.2)
            b.flash = 4
            return False
        b.hp -= damage
        b.flash = 5
        if b.hp <= 0:
            self.destroy_brick(b)
            return True
        self.sfx.play("strong")
        self.score += 5
        self.particles_at(b.rect.centerx, b.rect.centery, b.particle_color(), 4, 2.4)
        return False

    def destroy_brick(self, first):
        queue = [first]
        exploded = False
        while queue:
            cur = queue.pop()
            if not cur.alive:
                continue
            cur.alive = False
            pts = int(cur.points * self.multiplier())
            self.score += pts
            cx, cy = cur.rect.center
            self.float_text(cx, cy, "+%d" % pts, GOLD)
            self.particles_at(cx, cy, cur.particle_color(), 12, 3.4)
            if cur.kind == "t":
                exploded = True
                self.particles_at(cx, cy, (255, 220, 120), 26, 5.5)
                for o in self.bricks:
                    if (o.alive and o.breakable and o is not cur
                            and abs(o.rect.centerx - cx) <= BRICK_W + GAP + 2
                            and abs(o.rect.centery - cy) <= BRICK_H + GAP + 2):
                        queue.append(o)
            if cur.kind == "D" or random.random() < self.drop_chance():
                kinds, weights = zip(*POWER_WEIGHTS)
                self.powerups.append(PowerUp(cx, cy, random.choices(kinds, weights)[0]))
        if exploded:
            self.shake = max(self.shake, 12)
            self.sfx.play("explode")
        else:
            self.sfx.play("brick")
        self.update_high()

    def register_brick_hit(self, ball, b):
        if b.breakable:
            self.combo += 1
            ball.speed = min(self.base_speed + 3.5, ball.speed + 0.04)
        self.hit_brick(b, self.dmg())
        fire = self.lv("fire")
        if fire and b.breakable and random.random() < 0.25 * fire:
            cx, cy = b.rect.center
            self.particles_at(cx, cy, (255, 140, 20), 10, 3.0)
            for o in self.bricks:
                if (o.alive and o.breakable and o is not b
                        and abs(o.rect.centerx - cx) <= BRICK_W + GAP + 2
                        and abs(o.rect.centery - cy) <= BRICK_H + GAP + 2):
                    self.hit_brick(o, 1)

    # ----- power-up -----
    def apply_powerup(self, kind):
        p = self.paddle
        dm = self.dur_mult()
        self.sfx.play("powerup")
        self.float_text(p.x, p.y - 24, POWERUPS[kind][0], POWERUPS[kind][2])
        if kind == "W":
            p.target_w, p.effect_timer = p.base_w * 1.55, 12.0 * dm
        elif kind == "N":
            p.target_w, p.effect_timer = max(60.0, p.base_w * 0.62), 10.0
        elif kind == "S":
            self.slow_timer = 10.0 * dm
        elif kind == "L":
            self.lives = min(self.max_lives, self.lives + 1)
        elif kind == "G":
            p.laser_timer = 10.0 * dm
        elif kind == "P":
            self.pierce_timer = 8.0 * dm
        elif kind == "M":
            src = next((b for b in self.balls if not b.stuck), None)
            if src:
                for ang in (-22, 22):
                    if len(self.balls) >= 6:
                        break
                    nb = Ball(src.x, src.y, src.speed, stuck=False)
                    a = math.radians(ang)
                    nb.dx = src.dx * math.cos(a) - src.dy * math.sin(a)
                    nb.dy = src.dx * math.sin(a) + src.dy * math.cos(a)
                    nb.fix_dir()
                    self.balls.append(nb)

    def fire_laser(self):
        p = self.paddle
        if p.laser_timer > 0 and p.laser_cd <= 0:
            r = p.rect
            self.lasers.append([r.left + 10, r.top - 10])
            self.lasers.append([r.right - 10, r.top - 10])
            p.laser_cd = 0.3
            self.sfx.play("laser")

    # ----- boss -----
    def shoot(self, kind, x, y, tx, speed):
        dist_y = max(60.0, self.paddle.y - y)
        t = dist_y / speed
        vx = clamp((tx - x) / t, -3.5, 3.5)
        self.projectiles.append(Projectile(kind, x, y, vx, speed))

    def damage_boss(self, dmg, ignore_cd=False):
        b = self.boss
        if not b or not b.alive:
            return
        if b.hurt_cd > 0 and not ignore_cd:
            return
        if b.kind == "dragon" and any(o.kind == "c" and o.alive for o in self.bricks):
            dmg *= 0.5
        b.hp -= dmg
        b.hurt_cd = 0.12
        b.flash = 0.12
        self.sfx.play("boss_hit")
        self.score += int(20 * self.multiplier())
        r = b.rect
        self.particles_at(r.centerx + random.randint(-30, 30), r.bottom - 10,
                          (255, 255, 255), 6, 3.0)
        if b.phase == 1 and b.hp <= b.max_hp / 2:
            b.phase = 2
            self.shake = 20
            self.float_text(r.centerx, r.bottom + 10, "FASE 2!", (255, 120, 60))
        if b.hp <= 0:
            self.boss_defeated()

    def boss_defeated(self):
        b = self.boss
        b.alive = False
        r = b.rect
        pal = [(255, 220, 120), (255, 120, 40), (230, 230, 230), (120, 220, 90)]
        for _ in range(8):
            self.particles_at(r.centerx + random.randint(-r.w // 2, r.w // 2),
                              r.centery + random.randint(-r.h // 2, r.h // 2),
                              random.choice(pal), 16, 6.0)
        self.shake = 30
        self.sfx.play("boss_die")
        self.score += 300
        self.stage_clear(boss=True)

    # ----- update -----
    def control_paddle(self, f):
        k = pygame.key.get_pressed()
        d = (k[pygame.K_RIGHT] or k[pygame.K_d]) - (k[pygame.K_LEFT] or k[pygame.K_a])
        if d:
            self.mouse_mode = False
            self.paddle.x += d * self.paddle.speed * f
        elif self.mouse_mode:
            self.paddle.x += (self.mouse_x - self.paddle.x) * min(1.0, 0.4 * f)
        self.paddle.clamp_x()

    def ball_paddle(self, ball):
        r = self.paddle.rect
        if ball.dy <= 0:
            return
        cx, cy = clamp(ball.x, r.left, r.right), clamp(ball.y, r.top, r.bottom)
        if ((ball.x - cx) ** 2 + (ball.y - cy) ** 2 <= ball.r ** 2
                and ball.y < r.centery):
            ball.y = r.top - ball.r - 0.5
            off = clamp((ball.x - self.paddle.x) / (r.w / 2), -1, 1)
            ball.set_angle(off * 62 + random.uniform(-2, 2))
            self.combo = 0
            self.sfx.play("paddle")
            self.particles_at(ball.x, r.top, (150, 220, 255), 4, 2.0)

    def ball_brick(self, ball):
        pierce = self.pierce_timer > 0
        touching = set()
        best = None
        for b in self.bricks:
            if not b.alive:
                continue
            hit = circle_rect(ball, b.rect)
            if hit is None:
                continue
            if pierce and b.breakable:
                touching.add(id(b))
                if id(b) not in ball.touching:
                    self.register_brick_hit(ball, b)
                continue
            if best is None or hit[0] < best[0][0]:
                best = (hit, b)
        ball.touching = touching
        if best:
            (d2, dx, dy, push), b = best
            bounce(ball, dx, dy, push)
            self.register_brick_hit(ball, b)

    def ball_boss(self, ball):
        b = self.boss
        if not b or not b.alive:
            return
        hit = circle_rect(ball, b.rect)
        if hit is None:
            return
        _, dx, dy, push = hit
        bounce(ball, dx, dy, push)
        if b.hurt_cd <= 0:
            self.combo += 1
            self.damage_boss(self.dmg())

    def ball_projectiles(self, ball):
        for pr in self.projectiles:
            if not pr.dead and circle_rect(ball, pr.rect) is not None:
                pr.dead = True
                self.score += int(20 * self.multiplier())
                self.sfx.play("brick")
                self.particles_at(pr.x, pr.y, (255, 200, 120), 10, 3.0)

    def update_ball(self, ball, f):
        p = self.paddle
        if ball.stuck:
            ball.x, ball.y = p.x, p.y - ball.r - 1
            return
        speed = ball.speed * (0.7 if self.slow_timer > 0 else 1.0)
        dist = speed * f
        steps = max(1, int(dist / 4) + 1)
        sd = dist / steps
        for _ in range(steps):
            ball.x += ball.dx * sd
            ball.y += ball.dy * sd
            if ball.x - ball.r < 0:
                ball.x, ball.dx = ball.r, abs(ball.dx)
            elif ball.x + ball.r > WIDTH:
                ball.x, ball.dx = WIDTH - ball.r, -abs(ball.dx)
            if ball.y - ball.r < HUD_H:
                ball.y, ball.dy = HUD_H + ball.r, abs(ball.dy)
            self.ball_paddle(ball)
            self.ball_brick(ball)
            self.ball_boss(ball)
            if self.state != PLAYING:
                return
            self.ball_projectiles(ball)
            ball.fix_dir()
            if ball.y - ball.r > HEIGHT:
                if self.anchor_left > 0:
                    self.anchor_left -= 1
                    ball.y = HEIGHT - ball.r - 2
                    ball.dy = -abs(ball.dy)
                    ball.fix_dir()
                    self.float_text(ball.x, HEIGHT - 50, "ANCHOR!", (210, 130, 255))
                    self.sfx.play("powerup")
                    self.particles_at(ball.x, HEIGHT - 20, (210, 130, 255), 14, 3.5)
                else:
                    ball.dead = True
                    return
        ball.trail.append((ball.x, ball.y))
        if len(ball.trail) > 10:
            ball.trail.pop(0)

    def update_lasers(self, f):
        keep = []
        for ls in self.lasers:
            ls[1] -= 12 * f
            if ls[1] < HUD_H:
                continue
            hit = False
            if self.boss and self.boss.alive and self.boss.rect.collidepoint(ls[0], ls[1]):
                self.damage_boss(1, ignore_cd=True)
                hit = True
            if not hit:
                for pr in self.projectiles:
                    if not pr.dead and pr.rect.collidepoint(ls[0], ls[1]):
                        pr.dead = True
                        self.particles_at(pr.x, pr.y, (255, 200, 120), 8, 3.0)
                        hit = True
                        break
            if not hit:
                for b in self.bricks:
                    if b.alive and b.rect.collidepoint(ls[0], ls[1]):
                        self.hit_brick(b)
                        hit = True
                        break
            if not hit:
                keep.append(ls)
        self.lasers = keep

    def update_fx(self, dt, f):
        for it in self.bg_items:
            if self.theme == "day":
                it[0] += it[2] * f
                if it[0] > WIDTH + 80:
                    it[0] = -100
            elif self.theme == "nether":
                it[1] -= it[2] * 1.2 * f
                if it[1] < -6:
                    it[0], it[1] = random.uniform(0, WIDTH), HEIGHT + 4
            else:
                it[1] += it[2] * 0.6 * f
                if it[1] > HEIGHT:
                    it[0], it[1] = random.uniform(0, WIDTH), -4
        for p in self.particles:
            p[0] += p[2] * f
            p[1] += p[3] * f
            p[3] += 0.15 * f
            p[4] -= dt
        self.particles = [p for p in self.particles if p[4] > 0]
        for t in self.texts:
            t[1] -= 0.8 * f
            t[3] -= dt
        self.texts = [t for t in self.texts if t[3] > 0]
        if self.shake > 0:
            self.shake -= 1 * f

    def update_playing(self, dt, f):
        self.control_paddle(f)
        self.paddle.update(dt, f)
        if self.invuln > 0:
            self.invuln -= dt
        if self.slow_timer > 0:
            self.slow_timer -= dt
        if self.pierce_timer > 0:
            self.pierce_timer -= dt

        for b in list(self.balls):
            self.update_ball(b, f)
            if self.state != PLAYING:
                return
        self.balls = [b for b in self.balls if not b.dead]

        if self.boss and self.boss.alive:
            self.boss.update(dt, f, self)

        for pr in self.projectiles:
            pr.update(f)
            if not pr.dead and pr.rect.colliderect(self.paddle.rect):
                pr.dead = True
                self.particles_at(pr.x, pr.y, (255, 160, 60), 14, 4.0)
                if pr.kind == "tnt":
                    self.shake = max(self.shake, 10)
                self.hurt_player()
                if self.state != PLAYING:
                    return
        self.projectiles = [pr for pr in self.projectiles if not pr.dead]

        for pu in self.powerups:
            pu.update(f)
            if pu.rect.colliderect(self.paddle.rect):
                self.apply_powerup(pu.kind)
                pu.y = HEIGHT + 100
        self.powerups = [pu for pu in self.powerups if pu.y < HEIGHT + 30]

        self.update_lasers(f)
        if self.state != PLAYING:
            return

        if not self.balls:
            self.lose_ball()
            return
        self.bricks = [b for b in self.bricks if b.alive]
        if not self.boss and not any(b.breakable for b in self.bricks):
            self.stage_clear(boss=False)

    def update(self, dt, f):
        self.t += dt
        self.update_fx(dt, f)
        if self.fade > 0:
            self.fade = max(0.0, self.fade - dt * 2.2)
        if self.state == READY:
            self.ready_t += dt
            self.control_paddle(f)
            self.paddle.update(dt, f)
            for b in self.balls:
                self.update_ball(b, f)
        elif self.state == PLAYING:
            self.update_playing(dt, f)
        elif self.state == LEVEL_CLEAR:
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.proceed()

    # ----- event -----
    def perk_card_rect(self, i):
        return pygame.Rect(40 + i * 250, 190, 220, 300)

    def perk_at(self, pos):
        for i in range(len(self.perk_choices)):
            if self.perk_card_rect(i).collidepoint(pos[0], pos[1]):
                return i
        return None

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.MOUSEMOTION:
                self.mouse_x = e.pos[0]
                self.mouse_mode = True
                if self.state == PERK:
                    i = self.perk_at(e.pos)
                    if i is not None:
                        self.perk_sel = i
                elif self.state == MENU:
                    i = self.menu_at(e.pos)
                    if i is not None and i != self.menu_sel:
                        self.menu_sel = i
                        self.sfx.play("paddle")
                elif self.state == PAUSED:
                    i = self.pause_at(e.pos)
                    if i is not None and i != self.pause_sel:
                        self.pause_sel = i
                        self.sfx.play("paddle")
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.state == PERK:
                    i = self.perk_at(e.pos)
                    if i is not None:
                        self.confirm_perk(i)
                elif self.state == MENU:
                    i = self.menu_at(e.pos)
                    if i is not None:
                        self.menu_sel = i
                        self.menu_activate(i)
                elif self.state == PAUSED:
                    i = self.pause_at(e.pos)
                    if i is not None:
                        self.pause_sel = i
                        self.pause_activate(i)
                elif self.state == HOWTO:
                    if self.back_rect().collidepoint(e.pos):
                        self.sfx.play("paddle")
                        self.go_menu(keep_sel=True)
                elif self.state == CODEX:
                    for i in range(len(CODEX_TABS)):
                        if self.codex_tab_rect(i).collidepoint(e.pos):
                            self.codex_page = i
                            self.sfx.play("paddle")
                    if self.back_rect().collidepoint(e.pos):
                        self.sfx.play("paddle")
                        self.go_menu(keep_sel=True)
                else:
                    self.action()
            elif e.type == pygame.KEYDOWN:
                k = e.key
                if self.state == MENU:
                    n = len(self.menu_items())
                    if k in (pygame.K_UP, pygame.K_w):
                        self.menu_sel = (self.menu_sel - 1) % n
                        self.sfx.play("paddle")
                    elif k in (pygame.K_DOWN, pygame.K_s):
                        self.menu_sel = (self.menu_sel + 1) % n
                        self.sfx.play("paddle")
                    elif k in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.menu_activate(self.menu_sel)
                    elif k == pygame.K_ESCAPE:
                        self.running = False
                    continue
                if self.state == PAUSED:
                    n = len(self.pause_items())
                    if k in (pygame.K_UP, pygame.K_w):
                        self.pause_sel = (self.pause_sel - 1) % n
                        self.sfx.play("paddle")
                    elif k in (pygame.K_DOWN, pygame.K_s):
                        self.pause_sel = (self.pause_sel + 1) % n
                        self.sfx.play("paddle")
                    elif k in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.pause_activate(self.pause_sel)
                    elif k in (pygame.K_p, pygame.K_ESCAPE):
                        self.state = self.prev_state
                    elif k == pygame.K_m:
                        self.pause_activate(2)
                    continue
                if self.state in (HOWTO, CODEX):
                    if k in (pygame.K_ESCAPE, pygame.K_BACKSPACE,
                             pygame.K_RETURN, pygame.K_SPACE):
                        self.sfx.play("paddle")
                        self.go_menu(keep_sel=True)
                    elif self.state == CODEX and k in (pygame.K_LEFT, pygame.K_a):
                        self.codex_page = (self.codex_page - 1) % len(CODEX_TABS)
                        self.sfx.play("paddle")
                    elif self.state == CODEX and k in (pygame.K_RIGHT, pygame.K_d):
                        self.codex_page = (self.codex_page + 1) % len(CODEX_TABS)
                        self.sfx.play("paddle")
                    continue
                if self.state == PERK:
                    if k in (pygame.K_1, pygame.K_2, pygame.K_3):
                        self.confirm_perk(k - pygame.K_1)
                    elif k == pygame.K_LEFT:
                        self.perk_sel = (self.perk_sel - 1) % len(self.perk_choices)
                    elif k == pygame.K_RIGHT:
                        self.perk_sel = (self.perk_sel + 1) % len(self.perk_choices)
                    elif k in (pygame.K_SPACE, pygame.K_RETURN):
                        self.confirm_perk(self.perk_sel)
                    continue
                if k in (pygame.K_SPACE, pygame.K_RETURN):
                    self.action()
                elif k in (pygame.K_p, pygame.K_ESCAPE):
                    if self.state in (READY, PLAYING):
                        self.prev_state = self.state
                        self.state = PAUSED
                        self.pause_sel = 0
                    elif self.state == PAUSED:
                        self.state = self.prev_state
                    elif k == pygame.K_ESCAPE and self.state in (GAME_OVER, WIN):
                        self.go_menu()
                elif k == pygame.K_m and self.state == PAUSED:
                    self.update_high()
                    self.save_high()
                    self.go_menu()

    # ----- gambar -----
    def text(self, surf, msg, font, color, pos, anchor="center", shadow=True):
        img = font.render(msg, True, color)
        rect = img.get_rect()
        setattr(rect, anchor, pos)
        if shadow:
            surf.blit(font.render(msg, True, BLACK), rect.move(2, 2))
        surf.blit(img, rect)

    def title_text(self, surf, msg, font, center, fill=(255, 205, 70),
                   light=(255, 240, 150), outline=(70, 36, 6)):
        """Teks judul bergaya 3D: outline tebal, bayangan, dan highlight atas."""
        img = font.render(msg, True, fill)
        top = font.render(msg, True, light)
        out = font.render(msg, True, outline)
        rect = img.get_rect(center=center)
        for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-3, -3), (3, -3),
                       (-3, 3), (3, 3), (0, 6), (-3, 6), (3, 6), (0, 5)):
            surf.blit(out, rect.move(dx, dy))
        surf.blit(img, rect)
        surf.set_clip(pygame.Rect(0, rect.top, WIDTH, rect.h // 2 - 2))
        surf.blit(top, rect)
        surf.set_clip(None)

    def panel(self, s, rect, border=(100, 100, 110)):
        pygame.draw.rect(s, (30, 30, 36), rect)
        pygame.draw.rect(s, border, rect, 3)
        pygame.draw.rect(s, (14, 14, 18), rect.inflate(-6, -6), 1)

    def draw_button(self, s, r, label, sel, icon=None, font=None):
        font = font or self.f_med
        s.blit(self.get_button(r.w, r.h, sel), r)
        pygame.draw.rect(s, GOLD if sel else (22, 22, 28), r, 3 if sel else 2)
        if icon:
            s.blit(self.sprites.get(icon, 2), (r.x + 16, r.centery - 8))
        self.text(s, label, font, GOLD if sel else WHITE, r.center)
        if sel:
            cy = r.centery
            bob = int(abs(math.sin(self.t * 6)) * 5)
            ax = r.left - 12 - bob
            bx = r.right + 12 + bob
            for pts in ([(ax - 11, cy - 10), (ax, cy), (ax - 11, cy + 10)],
                        [(bx + 11, cy - 10), (bx, cy), (bx + 11, cy + 10)]):
                pygame.draw.polygon(s, GOLD, pts)
                pygame.draw.polygon(s, BLACK, pts, 2)

    def draw_background(self, s):
        s.blit(self.bgs[self.theme], (0, 0))
        if self.theme == "day":
            for x, y, _, _, col in self.bg_items:
                pygame.draw.rect(s, col, (int(x), int(y), 72, 16))
                pygame.draw.rect(s, col, (int(x) + 14, int(y) - 12, 40, 14))
        else:
            for x, y, _, size, col in self.bg_items:
                pygame.draw.rect(s, col, (int(x), int(y), size, size))

    def draw_ball(self, s, b):
        n = len(b.trail)
        for i, (tx, ty) in enumerate(b.trail):
            k = (i + 1) / (n + 1)
            size = max(2, int(10 * k))
            col = (255, 150, 40) if self.pierce_timer > 0 else (150, 210, 255)
            pygame.draw.rect(s, shade(col, 0.6 * k),
                             (int(tx) - size // 2, int(ty) - size // 2, size, size))
        s.blit(self.glow_ball, (int(b.x) - 24, int(b.y) - 24))
        img = self.ball_imgs["fire" if self.pierce_timer > 0 else "normal"]
        s.blit(img, (int(b.x) - 7, int(b.y) - 7))

    def draw_dragon(self, s, b):
        r = b.rect
        flap = math.sin(self.t * 4) * 20
        wing = (46, 28, 70)
        for side in (-1, 1):
            bx = r.centerx + side * 40
            pygame.draw.polygon(s, wing, [
                (bx, r.top + 14), (bx + side * 120, r.top - 36 + flap),
                (bx + side * 90, r.top + 20), (bx + side * 40, r.top + 40)])
            pygame.draw.polygon(s, (80, 50, 120), [
                (bx, r.top + 14), (bx + side * 120, r.top - 36 + flap),
                (bx + side * 95, r.top - 8 + flap * 0.5)], 2)
        for i in range(r.w // 10):
            for j in range(r.h // 10):
                n = hash_noise(i, j, 31)
                col = vary((28, 22, 40), 0.5, n)
                if n > 0.93:
                    col = (70, 40, 110)
                pygame.draw.rect(s, col, (r.x + i * 10, r.y + j * 10, 10, 10))
        hx = r.right - 4 if b.dir > 0 else r.left - 46
        pygame.draw.rect(s, (36, 28, 50), (hx, r.y + 6, 50, 50))
        pygame.draw.rect(s, (90, 60, 130), (hx, r.y + 6, 50, 50), 2)
        ex = hx + (30 if b.dir > 0 else 8)
        pygame.draw.rect(s, (255, 80, 230), (ex, r.y + 18, 12, 8))
        pygame.draw.rect(s, (255, 80, 230), (ex + (0 if b.dir > 0 else 22), r.y + 30, 12, 8))
        if b.flash > 0:
            pygame.draw.rect(s, (255, 255, 255), r, 3)

    def draw_boss(self, s):
        b = self.boss
        if not b or not b.alive:
            return
        r = b.rect
        if b.kind == "dragon":
            self.draw_dragon(s, b)
            return
        s.blit(self.boss_tex[b.kind], r)
        fuse = b.kind == "creeper" and b.attack_cd < 0.5 and self.state == PLAYING
        if b.flash > 0 or (fuse and int(self.t * 20) % 2 == 0):
            s.blit(self.boss_flash[b.kind], r)

    def draw_world(self, s):
        self.draw_background(s)
        for b in self.bricks:
            if b.alive:
                b.draw(s)
        self.draw_boss(s)
        for pu in self.powerups:
            pu.draw(s, self.sprites)
        for pr in self.projectiles:
            pr.draw(s)
        for lx, ly in self.lasers:
            pygame.draw.rect(s, (150, 110, 60), (int(lx) - 1, int(ly), 3, 14))
            pygame.draw.rect(s, (210, 210, 220), (int(lx) - 3, int(ly) - 4, 7, 5))
        for b in self.balls:
            self.draw_ball(s, b)
        if not (self.invuln > 0 and int(self.t * 15) % 2 == 0):
            self.paddle.draw(s)
        for x, y, _, _, life, col, size in self.particles:
            k = clamp(life / 0.5, 0.2, 1.0)
            pygame.draw.rect(s, shade(col, k), (int(x), int(y), size, size))
        for x, y, msg, life, col in self.texts:
            self.text(s, msg, self.f_small, shade(col, clamp(life / 0.5, 0.3, 1.0)),
                      (int(x), int(y)))
        self.draw_hud(s)
        self.draw_bottom_bar(s)

    def draw_hud(self, s):
        pygame.draw.rect(s, (24, 24, 28), (0, 0, WIDTH, HUD_H))
        pygame.draw.rect(s, (70, 70, 78), (0, HUD_H - 3, WIDTH, 3))
        self.text(s, "SKOR %06d" % self.score, self.f_med, WHITE, (12, 20), "midleft")
        self.text(s, "REKOR %06d" % self.high, self.f_small, GRAY, (170, 21), "midleft")
        self.text(s, "STAGE %d/%d" % (self.stage_idx + 1, len(STAGES)), self.f_small,
                  (170, 220, 255), (300, 21), "midleft")
        if self.combo >= 3:
            self.text(s, "COMBO %d  x%g" % (self.combo, round(self.multiplier(), 2)),
                      self.f_small, GOLD, (410, 21), "midleft")
        heart = self.sprites.get("heart", 2)
        for i in range(self.max_lives):
            s.blit(heart if i < self.lives else self.heart_off,
                   (WIDTH - 12 - (i + 1) * 18, 12))
        b = self.boss
        if b and b.alive:
            bw = 420
            bx = (WIDTH - bw) // 2
            by = HUD_H - 20
            pygame.draw.rect(s, BLACK, (bx - 2, by - 2, bw + 4, 12))
            pygame.draw.rect(s, (60, 20, 20), (bx, by, bw, 8))
            col = (220, 40, 50) if b.phase == 1 else (255, 150, 30)
            pygame.draw.rect(s, col, (bx, by, int(bw * max(0.0, b.hp) / b.max_hp), 8))
            self.text(s, b.name.upper(), self.f_tiny, WHITE, (bx - 10, by + 4), "midright")

    def draw_bottom_bar(self, s):
        chips = []
        p = self.paddle
        if p.effect_timer > 0:
            if p.target_w > p.base_w:
                chips.append(("PERISAI", p.effect_timer, POWERUPS["W"][2]))
            else:
                chips.append(("WITHER", p.effect_timer, POWERUPS["N"][2]))
        if self.slow_timer > 0:
            chips.append(("SOUL SAND", self.slow_timer, POWERUPS["S"][2]))
        if p.laser_timer > 0:
            chips.append(("BUSUR", p.laser_timer, POWERUPS["G"][2]))
        if self.pierce_timer > 0:
            chips.append(("PICKAXE", self.pierce_timer, POWERUPS["P"][2]))
        x = 10
        for name, t, col in chips:
            self.text(s, "%s %.0fs" % (name, t), self.f_tiny, col, (x, HEIGHT - 12),
                      "midleft")
            x += 105
        x = WIDTH - 10
        if self.totems > 0:
            x -= 20
            s.blit(self.sprites.get("totem", 2), (x, HEIGHT - 24))
            self.text(s, str(self.totems), self.f_tiny, WHITE, (x - 2, HEIGHT - 12),
                      "midright")
        for pid, lv in self.perks.items():
            if pid == "totem":
                continue
            x -= 38
            s.blit(self.sprites.get(PERKS[pid]["sprite"], 2), (x, HEIGHT - 24))
            self.text(s, str(lv), self.f_tiny, GOLD, (x + 18, HEIGHT - 12), "midleft")


    # ----- menu utama -----
    def draw_menu_scenery(self, s):
        for x, far, near in self.hills:
            pygame.draw.rect(s, (122, 180, 112), (x, GROUND_Y - far, 32, far))
        for x, far, near in self.hills:
            pygame.draw.rect(s, (84, 150, 64), (x, GROUND_Y - near, 32, near))
        for i in range(WIDTH // BRICK_W + 1):
            s.blit(TEX["g"], (i * BRICK_W, GROUND_Y))
            s.blit(TEX["d"], (i * BRICK_W, GROUND_Y + BRICK_H))
        for x, y, kind, ph in self.menu_blocks:
            by = y + int(math.sin(self.t * 1.5 + ph) * 8)
            sw = int(BRICK_W * (0.55 - 0.08 * math.sin(self.t * 1.5 + ph)))
            pygame.draw.ellipse(s, (96, 150, 86),
                                (x + (BRICK_W - sw) // 2, y + BRICK_H + 18, sw, 6))
            s.blit(TEX[kind], (x, by))

    def draw_menu(self, s):
        self.theme = "day"
        self.draw_background(s)
        self.draw_menu_scenery(s)

        bob = math.sin(self.t * 2) * 4
        self.title_text(s, "BRICK BREAKER", self.f_title, (WIDTH // 2, 78 + bob))
        # sub-judul dengan ikon
        self.text(s, "CRAFT EDITION", self.f_med, WHITE, (WIDTH // 2, 138))
        dia = self.sprites.get("diamond", 3)
        s.blit(dia, (WIDTH // 2 - 160, 126))
        s.blit(dia, (WIDTH // 2 + 136, 126))
        # splash text miring berdenyut
        pulse = 1 + 0.06 * math.sin(self.t * 5)
        sp = self.f_small.render(self.splash, True, (255, 255, 70))
        sh = self.f_small.render(self.splash, True, (60, 60, 0))
        base = pygame.Surface((sp.get_width() + 2, sp.get_height() + 2), pygame.SRCALPHA)
        base.blit(sh, (2, 2))
        base.blit(sp, (0, 0))
        base = pygame.transform.rotozoom(base, 14, pulse)
        s.blit(base, base.get_rect(center=(676, 150)))

        for i, (label, icon) in enumerate(self.menu_items()):
            self.draw_button(s, self.menu_rect(i), label, i == self.menu_sel, icon)

        self.text(s, "REKOR TERTINGGI : %06d" % self.high, self.f_small, GOLD,
                  (WIDTH // 2, 540))
        self.text(s, "ATAS/BAWAH atau MOUSE : pilih     ENTER / KLIK : konfirmasi",
                  self.f_tiny, WHITE, (WIDTH // 2, 566))
        self.text(s, "v0.05  Craft Edition", self.f_tiny, WHITE,
                  (WIDTH - 10, HEIGHT - 10), "bottomright")

    # ----- layar sub-menu -----
    def draw_frame(self, s, title):
        self.theme = "day"
        self.draw_background(s)
        s.blit(self.dim_light, (0, 0))
        self.title_text(s, title, self.f_big, (WIDTH // 2, 56))
        mp = pygame.mouse.get_pos()
        back = self.back_rect()
        self.draw_button(s, back, "KEMBALI (ESC)", back.collidepoint(mp),
                         font=self.f_small)

    def draw_keycap(self, s, label, x, y):
        img = self.f_tiny.render(label, True, WHITE)
        w = max(28, img.get_width() + 16)
        r = pygame.Rect(x, y, w, 28)
        pygame.draw.rect(s, (62, 62, 72), r)
        pygame.draw.rect(s, (110, 110, 124), (r.x, r.y, w, 3))
        pygame.draw.rect(s, (30, 30, 36), (r.x, r.bottom - 5, w, 5))
        pygame.draw.rect(s, (14, 14, 18), r, 2)
        s.blit(img, img.get_rect(center=(r.centerx, r.centery - 1)))
        return x + w + 6

    def draw_howto(self, s):
        self.draw_frame(s, "CARA BERMAIN")
        self.panel(s, pygame.Rect(40, 130, 720, 440))
        self.text(s, "KONTROL", self.f_med, GOLD, (70, 160), "midleft")
        rows = [(["<", ">", "A", "D", "MOUSE"], "Gerakkan paddle"),
                (["SPACE", "KLIK"], "Luncurkan bola / tembak panah"),
                (["P", "ESC"], "Pause permainan"),
                (["1", "2", "3"], "Pilih perk setelah boss")]
        for i, (keys, desc) in enumerate(rows):
            y = 190 + i * 40
            x = 70
            for kname in keys:
                x = self.draw_keycap(s, kname, x, y)
            self.text(s, desc, self.f_small, WHITE, (360, y + 14), "midleft")
        self.text(s, "TIPS", self.f_med, GOLD, (70, 376), "midleft")
        tips = ["Pantulkan bola dan hancurkan semua blok untuk menamatkan stage.",
                "Titik tabrak di paddle menentukan sudut pantulan bola.",
                "Pukul proyektil boss dengan bola atau panah agar tidak kena.",
                "Jaga combo tetap tinggi untuk pengali skor yang besar.",
                "Kalahkan boss, lalu pilih 1 dari 3 perk permanen."]
        for i, tip in enumerate(tips):
            self.text(s, "-  " + tip, self.f_small, GRAY, (70, 410 + i * 28), "midleft")

    def draw_codex(self, s):
        self.draw_frame(s, "KOLEKSI")
        mp = pygame.mouse.get_pos()
        for i, name in enumerate(CODEX_TABS):
            r = self.codex_tab_rect(i)
            sel = i == self.codex_page
            s.blit(self.get_button(r.w, r.h, sel or r.collidepoint(mp)), r)
            pygame.draw.rect(s, GOLD if sel else (22, 22, 28), r, 3 if sel else 2)
            self.text(s, name, self.f_small, GOLD if sel else WHITE, r.center)
        self.text(s, "KIRI / KANAN : ganti tab", self.f_tiny, WHITE,
                  (760, 121), "midright")
        self.panel(s, pygame.Rect(40, 144, 720, 428))

        page = self.codex_page
        if page == 0:
            for idx, k in enumerate("dgpsobtDc"):
                x = 66 + (idx % 3) * 236
                y = 170 + (idx // 3) * 124
                if k == "c":
                    Brick(x, y, "c", 0).draw(s)
                else:
                    s.blit(TEX[k], (x, y))
                name, desc = BLOCK_DESC[k]
                self.text(s, name, self.f_small, WHITE, (x, y + 34), "topleft")
                self.text(s, desc, self.f_tiny, GRAY, (x, y + 58), "topleft")
                pts = BLOCK_INFO[k][1]
                if pts:
                    self.text(s, "Poin %d" % pts, self.f_tiny, GOLD, (x, y + 78), "topleft")
        elif page == 1:
            for i, k in enumerate("WNSMLGP"):
                y = 168 + i * 56
                col = POWERUPS[k][2]
                pygame.draw.rect(s, col, (72, y - 4, 40, 40), 2)
                s.blit(self.sprites.get(POWERUPS[k][1], 4), (76, y))
                self.text(s, POWERUPS[k][0], self.f_small, col, (132, y + 16), "midleft")
                self.text(s, ITEM_DESC[k], self.f_small, GRAY, (320, y + 16), "midleft")
        elif page == 2:
            for i, (pid, info) in enumerate(PERKS.items()):
                x = 64 + (i // 5) * 352
                y = 166 + (i % 5) * 78
                s.blit(self.sprites.get(info["sprite"], 4), (x, y + 6))
                self.text(s, "%s  (maks Lv %d)" % (info["name"], info["max"]),
                          self.f_small, WHITE, (x + 48, y + 6), "topleft")
                self.text(s, " ".join(info["desc"]), self.f_tiny, GRAY,
                          (x + 48, y + 32), "topleft")
        else:
            for i, (key, name, d1, d2) in enumerate(BOSS_INFO):
                y = 160 + i * 134
                icon = self.boss_icons[key]
                s.blit(icon, icon.get_rect(center=(138, y + 62)))
                self.text(s, name, self.f_med, GOLD, (250, y + 18), "topleft")
                self.text(s, "HP %d" % BOSS_DATA[key]["hp"], self.f_small,
                          (255, 120, 110), (250, y + 48), "topleft")
                self.text(s, d1, self.f_small, WHITE, (250, y + 72), "topleft")
                self.text(s, d2, self.f_small, GRAY, (250, y + 94), "topleft")

    def draw_banner(self, s, st):
        """Banner intro stage: pita gelap yang meluncur dari kiri/kanan."""
        k = min(1.0, self.ready_t / 0.45)
        off = int((1 - k) ** 3 * WIDTH)
        boss = bool(st.get("boss"))
        cy = HEIGHT - 210
        band = pygame.Surface((WIDTH, 96), pygame.SRCALPHA)
        band.fill((90, 10, 14, 190) if boss else (0, 0, 20, 170))
        s.blit(band, (0, cy - 48))
        line = (255, 90, 90) if boss else GOLD
        pygame.draw.rect(s, line, (0, cy - 48, WIDTH, 3))
        pygame.draw.rect(s, line, (0, cy + 45, WIDTH, 3))
        sub = ("PERINGATAN! BOSS" if boss else
               "STAGE %d / %d" % (self.stage_idx + 1, len(STAGES)))
        self.text(s, sub, self.f_small, line, (WIDTH // 2 - off, cy - 20))
        self.text(s, st["name"].upper(), self.f_big, WHITE, (WIDTH // 2 + off, cy + 12))
        if boss:
            self.text(s, "Pukul proyektilnya untuk menghancurkannya!", self.f_small,
                      WHITE, (WIDTH // 2, cy + 74))

    def draw_pause(self, s):
        s.blit(self.dim, (0, 0))
        self.title_text(s, "PAUSE", self.f_title, (WIDTH // 2, 160))
        for i, (label, icon) in enumerate(self.pause_items()):
            self.draw_button(s, self.pause_rect(i), label, i == self.pause_sel, icon)
        self.text(s, "P / ESC : lanjut main", self.f_tiny, GRAY, (WIDTH // 2, 450))

    def draw_result(self, s, title, color, rows, prompt, note=None):
        """Panel hasil (stage selesai / game over / menang)."""
        s.blit(self.dim, (0, 0))
        light = tuple(min(255, int(c * 1.2 + 25)) for c in color)
        self.title_text(s, title, self.f_big, (WIDTH // 2, 150), fill=color,
                        light=light, outline=(30, 20, 10))
        h = 36 + len(rows) * 42 + (38 if note else 0)
        r = pygame.Rect(200, 200, 400, h)
        self.panel(s, r, color)
        for i, (label, value) in enumerate(rows):
            y = r.y + 36 + i * 42
            self.text(s, label, self.f_med, GRAY, (r.x + 30, y), "midleft")
            self.text(s, value, self.f_med, GOLD, (r.right - 30, y), "midright")
        if note and int(self.t * 3) % 2 == 0:
            self.text(s, note, self.f_small, (120, 230, 140),
                      (r.centerx, r.bottom - 26))
        if int(self.t * 2) % 2 == 0:
            self.text(s, prompt, self.f_small, WHITE, (WIDTH // 2, r.bottom + 40))

    def overlay(self, s, title, lines, color=WHITE):
        s.blit(self.dim, (0, 0))
        self.text(s, title, self.f_big, color, (WIDTH // 2, HEIGHT // 2 - 80))
        for i, ln in enumerate(lines):
            self.text(s, ln, self.f_med, WHITE, (WIDTH // 2, HEIGHT // 2 - 20 + i * 36))

    def draw_perk(self, s):
        s.blit(self.dim, (0, 0))
        self.text(s, "BOSS DIKALAHKAN!", self.f_big, GOLD, (WIDTH // 2, 95))
        self.text(s, "Pilih 1 power-up permanen  (tekan 1 / 2 / 3 atau klik kartu)",
                  self.f_small, WHITE, (WIDTH // 2, 140))
        for i, pid in enumerate(self.perk_choices):
            r = self.perk_card_rect(i)
            sel = i == self.perk_sel
            self.panel(s, r, GOLD if sel else (100, 100, 110))
            info = PERKS[pid]
            cur = self.lv(pid)
            icon = self.sprites.get(info["sprite"], 6)
            s.blit(icon, icon.get_rect(center=(r.centerx, r.y + 70)))
            self.text(s, "[%d]" % (i + 1), self.f_small, GOLD, (r.x + 14, r.y + 18), "midleft")
            self.text(s, info["name"], self.f_small, WHITE, (r.centerx, r.y + 135))
            lvl = "BARU" if cur == 0 else "Lv %d -> %d" % (cur, cur + 1)
            self.text(s, lvl, self.f_small, (120, 230, 140), (r.centerx, r.y + 168))
            for j, ln in enumerate(info["desc"]):
                self.text(s, ln, self.f_tiny, GRAY, (r.centerx, r.y + 215 + j * 24))

    def draw(self):
        s = self.canvas
        if self.state == MENU:
            self.draw_menu(s)
        elif self.state == HOWTO:
            self.draw_howto(s)
        elif self.state == CODEX:
            self.draw_codex(s)
        else:
            self.draw_world(s)
            st = STAGES[self.stage_idx]
            if self.state == READY:
                if self.banner:
                    self.draw_banner(s, st)
                    py = HEIGHT - 120
                else:
                    self.text(s, "Nyawa tersisa : %d" % self.lives, self.f_med,
                              WHITE, (WIDTH // 2, HEIGHT - 180))
                    py = HEIGHT - 140
                if int(self.t * 2.5) % 2 == 0:
                    self.text(s, "SPACE / KLIK untuk meluncurkan", self.f_small,
                              GOLD, (WIDTH // 2, py))
            elif self.state == PAUSED:
                self.draw_pause(s)
            elif self.state == LEVEL_CLEAR:
                title = "BOSS KALAH!" if self.cleared_boss else "STAGE SELESAI!"
                self.draw_result(s, title, GOLD,
                                 [("Bonus", "+%d" % self.bonus),
                                  ("Skor", "%d" % self.score)],
                                 "SPACE untuk lanjut")
            elif self.state == PERK:
                self.draw_perk(s)
            elif self.state == GAME_OVER:
                self.draw_result(s, "GAME OVER", (255, 100, 110),
                                 [("Skor", "%d" % self.score),
                                  ("Rekor", "%d" % self.high),
                                  ("Stage", "%d / %d" % (self.stage_idx + 1, len(STAGES)))],
                                 "SPACE : main lagi     ESC : menu",
                                 "REKOR BARU!" if self.new_record else None)
            elif self.state == WIN:
                self.draw_result(s, "ENDER DRAGON KALAH!", GOLD,
                                 [("Skor akhir", "%d" % self.score),
                                  ("Rekor", "%d" % self.high)],
                                 "SPACE : main lagi     ESC : menu",
                                 "REKOR BARU!" if self.new_record
                                 else "Kamu menamatkan semua stage!")

        if self.fade > 0:
            self.fade_surf.set_alpha(int(255 * self.fade))
            s.blit(self.fade_surf, (0, 0))

        ox = oy = 0
        if self.shake > 0:
            m = int(min(6, self.shake // 2 + 1))
            ox, oy = random.randint(-m, m), random.randint(-m, m)
        self.screen.fill(BLACK)
        self.screen.blit(s, (ox, oy))
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            f = dt * 60.0
            self.handle_events()
            self.update(dt, f)
            self.draw()
        self.update_high()
        self.save_high()
        pygame.quit()


if __name__ == "__main__":
    Game().run()