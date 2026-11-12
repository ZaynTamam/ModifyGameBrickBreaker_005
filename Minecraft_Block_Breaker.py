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


