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

