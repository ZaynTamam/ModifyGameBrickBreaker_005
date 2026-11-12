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

