#!/usr/bin/env python3
"""Butiksbilder och paketikon, byggda ur paketets egna modeller.

Ingen Minecraft-klient finns på maskinen, så en riktig skärmdump går inte att ta
här. Allt ritas i block om 16 px så miljön läser som Minecraft i stället för som
en målning: gräset varierar per block, träden har stammar med streck.

  publish/hero.png       1280x720 — butikssida och sajt
  publish/pack_icon.png  256x256  — kopieras in i BÅDA paketen

En paketikon som saknas ger en grå ruta i spelets paketlista, och det ser ut som
ett trasigt paket långt innan någon provat det.

    python3 tools/make_promo.py
"""
import math, os, runpy, shutil, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/opt/purrfect-companions")
sys.path.insert(0, "/opt/purrfect-companions/tools/promo")
sys.path.insert(0, f"{BASE}/tools")
import render_regression as rr
import make_video as mv                     # text() och paste()
import render_pigs as rp

W, H = 1280, 720
# make_video.text() och paste() klipper mot SIN modulnivås W/H — trailerns
# 480x270. Utan den här raden hamnar allt utanför duken.
mv.W, mv.H = W, H
B = 16
HORISONT = int(H * 0.54)
# BAKGRUNDEN ATT NYCKLA BORT är gräsets färg, inte magenta. make_video.paste
# skalar ner med boxmedelvärde och räknar med de genomskinliga pixlarnas FÄRG i
# medelvärdet — med magenta bakom får varje gris en rosa kant. Med gräsfärgen
# blir samma kant osynlig.
NYCKEL = (106, 152, 62, 255)

HIMMEL_TOPP = (96, 156, 226)
HIMMEL_BOTTEN = (188, 218, 242)
GRAS = [(106, 152, 62), (98, 143, 58), (114, 160, 66), (90, 134, 54)]
JORD = [(122, 88, 58), (104, 74, 48), (136, 100, 66)]
BARK = (108, 78, 48)
STRECK = (74, 54, 34)
LOV = [(74, 128, 52), (64, 114, 46), (84, 140, 58)]


def slump(n):
    """Deterministiskt brus — bilden ska bli IDENTISK varje körning, annars blir
    varje ombyggnad en ny bild att granska."""
    n = (n * 1103515245 + 12345) & 0x7FFFFFFF
    return (n >> 16) & 0x7FFF


def duk():
    img = []
    for y in range(H):
        k = min(1.0, y / HORISONT)
        img.append([tuple(int(HIMMEL_TOPP[i] + (HIMMEL_BOTTEN[i] - HIMMEL_TOPP[i]) * k)
                          for i in range(3)) + (255,)] * W)
    return [list(r) for r in img]


def rita(img, x0, y0, w, h, c):
    for y in range(int(y0), int(y0 + h)):
        for x in range(int(x0), int(x0 + w)):
            if 0 <= y < H and 0 <= x < W:
                img[y][x] = c


def moln(img):
    for i, (cx, cy, bredd) in enumerate([(4, 3, 7), (28, 2, 5), (50, 4, 6), (66, 2, 4)]):
        for b in range(bredd):
            hoj = 1 + (slump(i * 13 + b) % 2)
            rita(img, (cx + b) * B, (cy + (b % 2)) * B, B, hoj * B, (248, 251, 255, 255))


def kullar(img):
    for lager, (bas, farg) in enumerate([(HORISONT - 2 * B, (92, 132, 64)),
                                         (HORISONT - B, (78, 118, 52))]):
        for bx in range(0, W // B + 1):
            hoj = (slump(bx * 7 + lager * 91) % 3) * (B // 2)
            rita(img, bx * B, bas - hoj, B, hoj + 3 * B, farg + (255,))


def mark(img):
    """Ängen sedd framifrån: GRÄSTOPPAR hela vägen ner, inte en jordvägg. Två
    rader gräs och jord under blir en tvärsnittsbild, som om man tittade in i en
    grop; man ser inte jordlagret när man står på en äng."""
    for by, y in enumerate(range(HORISONT, H, B)):
        for bx, x in enumerate(range(0, W, B)):
            n = slump(bx * 31 + by * 17)
            f = 0.88 + min(0.26, by * 0.022)
            rita(img, x, y, B, B, tuple(min(255, int(v * f)) for v in GRAS[n % 4]) + (255,))
            if n % 6 == 0:
                rita(img, x + (n % 12), y + 2, 2, B // 3, (128, 176, 74, 255))
            if n % 53 == 0:
                rita(img, x + 6, y + 4, 4, 4, [(255, 214, 66, 255), (255, 255, 255, 255),
                                               (240, 120, 170, 255)][n % 3])


def bokat(img, bx, by, bredd, hoj=3):
    """UPPBÖKAD JORD med en tryffel i. Utan den syns inte vad grisarna GÖR — en
    äng med fem grisar på är en bild av grisar, inte av ett tillägg som handlar
    om att leta.

    FLÄCKEN MÅSTE HA HÖJD. Första versionen var ett block hög och åtta bred, och
    på en äng sedd snett uppifrån läste den som en LIGGANDE PLANKA, inte som ett
    hål i gräset. Tre rader med avrundade hörn läser som en fläck.

    Kanten är ojämn: en rak rektangel ser ut som en plöjd åker, inte som något
    någon har rotat i."""
    y0 = HORISONT + by * B
    for rad in range(hoj):
        # SMALNAR AV FRÅN MITTEN OCH UT, så fläcken blir rundad i stället för
        # fyrkantig. Första formeln var "0 i mitten, annars 1 eller 2", och för
        # en TVÅRADIG fläck finns ingen mittrad — översta raden krympte med två
        # och understa med noll, så fläcken blev ett T.
        krymp = int(abs(rad - (hoj - 1) / 2) + 0.5)
        for i in range(krymp, bredd - krymp):
            n = slump(bx * 17 + i * 5 + rad * 41)
            if n % 11 == 0:                     # hål i kanten
                continue
            rita(img, (bx + i) * B, y0 + rad * B, B, B, JORD[n % 3] + (255,))
    # KASTAD JORD ovanför fläcken — spåret efter trynet som slängde upp den
    for i in range(bredd):
        if slump(bx * 11 + i) % 3 == 0:
            rita(img, (bx + i) * B + 4, y0 - B // 3, B // 2, B // 3, JORD[0] + (255,))
    # tryffeln: en knöl mitt i fläcken, med en ljus dagerfläck
    tx, ty = (bx + bredd // 2) * B - 2, y0 + (hoj // 2) * B + 3
    rita(img, tx, ty, 15, 11, (60, 46, 38, 255))
    rita(img, tx + 3, ty + 2, 5, 4, (112, 92, 74, 255))


def trad(img, bx, marknivå, hojd):
    x = bx * B
    rita(img, x, marknivå - hojd * B, B, hojd * B, BARK + (255,))
    for i in range(hojd):
        if slump(bx * 5 + i) % 3 == 0:
            rita(img, x, marknivå - (i + 1) * B + B // 3, B, B // 3, STRECK + (255,))
    top = marknivå - hojd * B
    for ly in range(-3, 2):
        bredd = 5 - abs(ly)
        for lx in range(-(bredd // 2), bredd // 2 + 1):
            n = slump(bx * 3 + lx * 11 + ly * 7)
            if n % 7 == 0:
                continue
            rita(img, x + lx * B, top + ly * B, B, B, LOV[n % 3] + (255,))


def gris(img, rasid, cx, cy, hojd, yaw, visa=()):
    geoid, tex = next((g, t) for r, g, t in rp.rasklient() if r == rasid)
    src = rp.rita(geoid, tex, 300, 300, yaw=yaw, pitch=10, visa=visa, bakgrund=NYCKEL)
    nyckl = [[(p[0], p[1], p[2], 0 if p[:3] == NYCKEL[:3] else 255) for p in rad]
             for rad in src]
    # SKUGGAN LÄGGS DÄR KLÖVARNA FAKTISKT LANDAR, och var det är MÄTS i
    # renderingen i stället för att antas. Ett antaget värde ger skuggor som
    # ligger en bit ifrån djuren, olika mycket för olika kroppar — en kunekune
    # fyller inte rutan som en lantras.
    nedersta = max((y for y in range(300) if any(p[3] for p in nyckl[y])), default=260)
    # paste() CENTRERAR på sitt cy-argument, och vi ger den cy - hojd/2 — alltså
    # står bilden med UNDERKANTEN på cy.
    fot_y = cy - hojd + int(hojd * (nedersta + 1) / 300)
    for i, (bredd, m) in enumerate(((0.72, 0.80), (0.52, 0.64))):
        w2 = int(hojd * bredd)
        rita(img, cx - w2 // 2, fot_y - i, w2, 3 - i,
             tuple(int(v * m) for v in (96, 138, 62)) + (255,))
    mv.paste(img, nyckl, 300, 300, cx, cy - hojd // 2, hojd)


def ordmarke(img):
    """Vit text mot ljus himmel går inte att läsa — en slagskugga räcker inte när
    bakgrunden är ljus åt alla håll. Ett mörkt band bakom texten och en
    HELDRAGEN kontur i åtta riktningar gör det."""
    for y in range(16, 172):
        k = 1.0 - abs(y - 94) / 94.0
        for x in range(W):
            p = img[y][x]
            m = 0.40 + 0.34 * (1 - k)
            img[y][x] = (int(p[0] * m), int(p[1] * m), int(p[2] * m), 255)
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, -2), (-2, 2), (2, 2)):
        mv.text(img, "SNUFFLE PIGS", W // 2 + dx, 54 + dy, 7, (14, 18, 26, 255))
    mv.text(img, "SNUFFLE PIGS", W // 2, 54, 7, (255, 255, 255, 255))
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        mv.text(img, "PIGS THAT SNIFF OUT ORE AND ROOT UP TRUFFLES",
                W // 2 + dx, 132 + dy, 3, (14, 18, 26, 255))
    mv.text(img, "PIGS THAT SNIFF OUT ORE AND ROOT UP TRUFFLES",
            W // 2, 132, 3, (255, 226, 214, 255))


def hero():
    img = duk()
    moln(img)
    kullar(img)
    mark(img)
    for bx, hojd in ((1, 6), (5, 5), (73, 6), (78, 5)):
        trad(img, bx, HORISONT + B, hojd)
    # BÖKADE FLÄCKAR FÖRE GRISARNA, annars målas de över djuren. De ligger i
    # FÖRGRUNDEN och är breda: första försöket la två smala fläckar mitt i
    # ängen, där grisarna stod framför dem, och det enda som syntes var en
    # brun stickare i högerkanten. En bild som ska visa att grisarna LETAR
    # måste visa spåren efter letandet.
    # PLACERADE DÄR DE SYNS. Första försöket la den vänstra fläcken på block 12,
    # exakt där Blossom står — den doldes helt av grisen som skulle ha bökat den.
    # Blocken 12, 24, 36, 59 och 71 är upptagna av djur.
    bokat(img, 3, 10, 7)
    bokat(img, 44, 12, 9)
    # Den tredje låg på block 64 och stack rakt ut ur Brambles tryne — den lästes
    # som en planka i ansiktet på grisen. Längre bak i bilden och längre in.
    bokat(img, 46, 5, 5, hoj=2)
    # EN GRIS PER RAS, inte fem slumpvis valda. Första uppställningen hade
    # Nilla två gånger och Bramble en — en butiksbild som säger "fem raser"
    # ska visa fem olika.
    # BAKRE RADEN FÖRST. Ritas de främre först målar de bakre över dem.
    for rasid, fx, fy, hojd, yaw, visa in (
            ("nilla", 0.30, 0.71, 150, 44, ()),
            ("ember", 0.735, 0.70, 172, 12, ("sadel",)),
            ("bramble", 0.885, 0.85, 196, 18, ()),
            ("blossom", 0.155, 0.90, 240, 30, ("sadel", "vaskor")),
            # TRYFFELBÄRAREN VÄNDS MOT KAMERAN. Vid yaw 22 svängde huvudet undan
            # och tryffeln under käken läste som en brun planka rakt ut ur
            # ansiktet. Nästan rakt framifrån hänger den där den ska.
            ("soot", 0.45, 0.87, 226, 6, ("tryffel",))):
        gris(img, rasid, int(W * fx), int(H * fy), hojd, yaw, visa)
    ordmarke(img)
    os.makedirs(f"{BASE}/publish", exist_ok=True)
    rr.write_png(f"{BASE}/publish/hero.png", W, H, img)
    print(f"  publish/hero.png ({W}x{H})")


def paketikon():
    """256x256 paketikon, HÄRLEDD UR LOGGAN i stället för en egen rendering.

    Skälet är inte lathet: två bilder som ska föreställa samma märke glider isär
    så fort den ena ändras."""
    kalla = f"{BASE}/publish/logo.png"
    if not os.path.exists(kalla):
        runpy.run_path(f"{BASE}/tools/make_logo.py", run_name="__main__")
    lw, lh, lpx = rr.read_png(kalla)
    N = 256
    # NÄRMASTE GRANNE, inte medelvärde: ramens tunna linjer och pixelgräset blir
    # gröt av interpolation, och hela poängen med bilden är att den är pixlig.
    liten = [[lpx[y * lh // N][x * lw // N] for x in range(N)] for y in range(N)]
    p = f"{BASE}/publish/pack_icon.png"
    rr.write_png(p, N, N, liten)
    for pack in ("SnuffleCompanions_BP", "SnuffleCompanions_RP"):
        shutil.copy(p, f"{BASE}/{pack}/pack_icon.png")
    print(f"  publish/pack_icon.png ({N}x{N}, ur loggan) → båda paketen")
    # Sajtens ikoner ur samma källa. En favicon som saknas ger en trasig ruta i
    # flikraden, och en apple-touch-icon som saknas ger en skärmdump av sidan när
    # någon sparar den på hemskärmen.
    for namn, storlek in (("favicon.png", 64), ("apple-touch-icon.png", 180)):
        rr.write_png(f"{BASE}/publish/{namn}", storlek, storlek,
                     [[lpx[y * lh // storlek][x * lw // storlek] for x in range(storlek)]
                      for y in range(storlek)])
    print("  publish/favicon.png + apple-touch-icon.png")


if __name__ == "__main__":
    paketikon()
    hero()
