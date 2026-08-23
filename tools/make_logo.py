#!/usr/bin/env python3
"""Projektloggan — den inramade rutan, samma recept som hund- och kattpaketets.

  publish/logo.png   512x512, används som projektavatar och på sajten

VARFÖR DEN SER UT SÅ HÄR (recept ärvt, och skälen gäller ordagrant här):

  * TRE STORA DJUR, inte fem små. Fem grisar i två rader blir en klump som
    inte går att tyda i CurseForge-listan; grannarna som fungerar har EN eller
    TRE stora figurer.
  * MÖRK BOTTEN. Listans grannar är dagsljusbilder; en natthimmel skiljer ut
    rutan, och ljusa grisar lyfter mot mörkt.
  * VIT KONTUR runt varje gris. Utan den smälter Soot ihop med natten.
  * RAM I FYRA LAGER MED HÖRNKLOSSAR. Det är hörnklossarna som får ramen att
    läsa som en ram och inte som en kant.
  * INGEN TEXT. Butiken skriver ut projektnamnet bredvid avataren ändå.

Urvalet är gjort på KONTRAST och SILUETT: Blossom är stor och rosa, Soot är
svart med vita klövar och bläs, Nilla är liten och rödgul. Storlek, färg och
form skiljer sig samtidigt.

BOTTNEN ÄR PLOMMON, inte hundpaketets gröna. Systerpaketen ska gå att skilja åt
som miniatyrer i samma lista, och det gör de på färgen innan man hunnit se vad
för djur det är.

    python3 tools/make_logo.py
"""
import os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/opt/purrfect-companions")
sys.path.insert(0, f"{BASE}/tools")
import render_regression as rr
import render_pigs as rp

P = 512
FRAM = int(P * 0.54)                       # horisonten
TOM = (0, 0, 0, 0)
NYCKEL = (255, 0, 255, 255)

# (ras, x-andel, fotlinje, höjd i px, vad den bär)
# HÖJDERNA ÄR RÄKNADE MOT RAMEN: fotlinjen ligger på 0,86 och ramen på 0,97, så
# klövarna hamnar innanför. En logga med avklippta fötter ser trasig ut.
# GRISAR ÄR BREDARE ÄN HUNDAR vid samma höjd, så siffrorna är lägre än
# hundloggans. Först provades 178-190 px: klövarna hamnade innanför ramen, men
# grisarna gick in i VARANDRA — Blossoms bakdel låg över Soots huvud, och tre
# figurer som överlappar läses som en klump, precis det tre stora djur ska
# undvika. Bredden, inte höjden, är gränsen för en gris.
UPPSTALLNING = [
    ("blossom", 0.180, 0.845, 156, ("sadel",)),
    ("soot", 0.500, 0.880, 168, ("tryffel",)),
    ("nilla", 0.822, 0.845, 136, ()),
]


def brus(n):
    n = (n * 1103515245 + 12345) & 0x7FFFFFFF
    return (n >> 16) & 0x7FFF


duk = [[(0, 0, 0, 255)] * P for _ in range(P)]
for y in range(P):
    k = min(1.0, y / FRAM)
    for x in range(P):
        # svag gloria mitt i bilden: kanterna mörka, men ljusare där grisarna
        # står — annars sjunker de in i botten
        d = (((x - P * 0.5) ** 2 + (y - P * 0.62) ** 2) ** 0.5) / (P * 0.62)
        g = max(0.0, 1.0 - d) ** 2 * 34
        duk[y][x] = (int(30 + 34 * k + g * 1.1), int(18 + 22 * k + g), int(34 + 40 * k + g), 255)


def rita(x0, y0, w, h, c):
    for y in range(int(y0), int(y0 + h)):
        for x in range(int(x0), int(x0 + w)):
            if 0 <= y < P and 0 <= x < P:
                duk[y][x] = c


B = 16                                     # blockstorlek, samma pixelspråk som hjältebilden
for i in range(46):                        # stjärnor, glesa och deterministiska
    n = brus(i * 977)
    ljus = 170 + (n % 70)
    rita(n % P, (n // 7) % int(P * 0.42), 3, 3, (ljus, min(255, ljus + 10), ljus, 255))
for bx in range(0, P // B + 1):            # kullar
    rita(bx * B, FRAM - B - (brus(bx * 7) % 2) * (B // 2), B, 3 * B, (42, 30, 38, 255))
GRAS = [(46, 40, 34), (40, 34, 30), (54, 46, 38), (36, 31, 28)]
for by, y in enumerate(range(FRAM, P, B)):
    for bx, x in enumerate(range(0, P, B)):
        n = brus(bx * 31 + by * 17)
        f = 0.9 + min(0.22, by * 0.03)
        rita(x, y, B, B, tuple(min(255, int(v * f)) for v in GRAS[n % 4]) + (255,))
        if n % 5 == 0:
            rita(x + (n % 11), y + 2, 2, B // 3, (66, 58, 44, 255))
        # UPPBÖKAD JORD, grispaketets motsvarighet till hundloggans nattblommor:
        # små mörka fläckar där någon har rotat. De hör till motivet i stället
        # för att vara pynt.
        if n % 37 == 0:
            rita(x + 4, y + 5, 7, 5, (58, 40, 30, 255))
            rita(x + 6, y + 6, 3, 3, (84, 62, 48, 255))


def blit(dst, src, cx, cy, out_h):
    """Skala och klistra, med TOM som genomskinlig. Jämför mot ett VÄRDE, inte
    mot alfa — sätter man bara alfa=0 och behåller färgen matchar ingenting och
    varje djur får en svart ruta runt sig."""
    sh, sw = len(src), len(src[0])
    k = sh / out_h
    out_w = int(sw / k)
    for oy in range(out_h):
        for ox in range(out_w):
            p = src[min(sh - 1, int(oy * k))][min(sw - 1, int(ox * k))]
            if p == TOM:
                continue
            px, py = cx - out_w // 2 + ox, cy - out_h // 2 + oy
            if 0 <= px < P and 0 <= py < P:
                dst[py][px] = p


for rasid, fx, fy, hojd, visa in UPPSTALLNING:
    geoid, tex = next((g, t) for r, g, t in rp.rasklient() if r == rasid)
    src = rp.rita(geoid, tex, 300, 300, yaw=26, pitch=10, visa=visa, bakgrund=NYCKEL)
    nyckl = [[TOM if p[:3] == NYCKEL[:3] else (p[0], p[1], p[2], 255) for p in rad]
             for rad in src]
    # SPRITEN BESKÄRS till sitt innehåll, annars styr renderarens tomma luft var
    # grisen hamnar och fotlinjen blir olika för olika kroppar.
    rader = [y for y in range(300) if any(p != TOM for p in nyckl[y])]
    kol = [x for x in range(300) if any(nyckl[y][x] != TOM for y in rader)]
    nyckl = [rad[kol[0]:kol[-1] + 1] for rad in nyckl[rader[0]:rader[-1] + 1]]
    sx, sy = int(P * fx), int(P * fy)
    # ELLIPS UNDER GRISEN: en mjuk skugga grundar djuret och skiljer det från
    # marken bättre än en rak stapel.
    for y in range(sy - hojd // 12, sy + hojd // 12):
        for x in range(sx - hojd // 3, sx + hojd // 3):
            e = ((x - sx) / (hojd / 3.0)) ** 2 + ((y - sy) / (hojd / 12.0)) ** 2
            if e < 1.0 and 0 <= y < P and 0 <= x < P:
                f = (1.0 - e) * 0.55
                p = duk[y][x]
                duk[y][x] = (int(p[0] * (1 - f)), int(p[1] * (1 - f)), int(p[2] * (1 - f)), 255)
    ljus = [[(248, 238, 242, 255) if p != TOM else TOM for p in rad] for rad in nyckl]
    for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4), (-3, -3), (3, -3), (-3, 3), (3, 3)):
        blit(duk, ljus, sx + dx, sy - hojd // 2 + dy, hojd)
    blit(duk, nyckl, sx, sy - hojd // 2, hojd)


def klov(hx, hy, sk, c):
    """KLÖVAVTRYCK i himlen — grisarnas motsvarighet till hundloggans
    tassavtryck. En klöv är TVÅ tår, inte fyra: gör man den med tassens fyra
    tår läser den som en hund, och då är hela poängen borta.

    De får inte ligga över grisarna; prydnad framför motivet gör tvärtom mot
    vad en logga ska göra."""
    for i in (0, 1):
        # Tårna smalnar av framåt och lutar utåt — två raka staplar läser som
        # ett utropstecken, inte som en klöv.
        for j in range(4):
            bredd = max(sk, sk * 2 - j // 2 * sk // 2)
            rita(hx + i * 4 * sk + (j // 2) * (sk if i else -sk) // 2,
                 hy + j * sk, bredd, sk, c)


for hx, hy, sk in ((int(P * 0.07), int(P * 0.28), 4), (int(P * 0.87), int(P * 0.19), 5),
                   (int(P * 0.71), int(P * 0.34), 3)):
    klov(hx, hy, sk, (232, 186, 172, 255))

# RAMEN: fyra lager plus hörnklossar.
MORK, GULD, GLIMT = (22, 14, 20, 255), (206, 138, 110, 255), (250, 214, 196, 255)


def kant(t, c):
    for x in range(t, P - t):
        duk[t][x] = duk[P - 1 - t][x] = c
    for y in range(t, P - t):
        duk[y][t] = duk[y][P - 1 - t] = c


for t in range(0, 7):
    kant(t, MORK)
for t in range(7, 13):
    kant(t, GULD)
for t in range(13, 15):
    kant(t, MORK)
kant(15, GLIMT)
for hx in (0, P - 26):
    for hy in (0, P - 26):
        for y in range(hy, hy + 26):
            for x in range(hx, hx + 26):
                k = min(x - hx, y - hy, hx + 25 - x, hy + 25 - y)
                duk[y][x] = MORK if k < 4 else (GLIMT if k < 6 else GULD)

os.makedirs(f"{BASE}/publish", exist_ok=True)
rr.write_png(f"{BASE}/publish/logo.png", P, P, duk)
print(f"  publish/logo.png ({P}x{P})")
