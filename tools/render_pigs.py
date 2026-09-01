#!/usr/bin/env python3
"""Renderar grisarna ur paketets EGNA filer, så man kan se dem utan Minecraft.

Servern renderar ingenting och det finns ingen klient på maskinen. Utan den här
bilden är enda sättet att veta hur en gris ser ut att fråga någon som har
spelet uppe — och då upptäcks fel som sneda ögon, ben som smälter ihop eller
ett tryne som pekar åt fel håll först efter en release.

Motorn är kattprojektets, lånad via hundpaketet: kub-för-kub-rasterisering med
z-buffert och rotation kring benens pivotar.

    python3 tools/render_pigs.py             # publish/pigs.png, alla raser
    python3 tools/render_pigs.py soot        # en enda, större
    python3 tools/render_pigs.py --framifran # vyn man möter i spelet
"""
import json, math, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/opt/purrfect-companions")
sys.path.insert(0, "/opt/purrfect-companions/tools/promo")
import render_regression as rr

RP = f"{BASE}/SnuffleCompanions_RP"
GEO = {g["description"]["identifier"]: g
       for g in json.load(open(f"{RP}/models/entity/gris.geo.json"))["minecraft:geometry"]}

# En pose som sätter varje rörligt ben i arbete. Står något stilla här kan dess
# pivot vara hur fel som helst utan att synas.
POSE = {"head": (-6, 22, 0), "leg0": (24, 0, 0), "leg1": (-24, 0, 0),
        "leg2": (-20, 0, 0), "leg3": (20, 0, 0), "tail": (8, 0, 12)}
# De valfria delarna, i renderarkontrollerns ordning. Visas de alltid går grisen
# omkring med sadel, väskor OCH en tryffel i trynet i varje bild.
VALFRIA = ("sadel", "vaskor", "tryffel", "lera")


def rasklient():
    ut = []
    for f in sorted(os.listdir(f"{RP}/entity")):
        d = json.load(open(f"{RP}/entity/{f}"))["minecraft:client_entity"]["description"]
        ut.append((d["identifier"].split(":")[1], d["geometry"]["default"],
                   d["textures"]["default"]))
    return ut


def rita(geoid, texnamn, W, H, yaw=34, pitch=14, pose=POSE, visa=(),
         bakgrund=(22, 26, 34, 255)):
    tw, th, tex = rr.read_png(f"{RP}/{texnamn}.png")
    geo = GEO[geoid]
    ya, pa = math.radians(yaw), math.radians(pitch)
    dolda = {n for n in VALFRIA if n not in visa}

    def cam(p):
        x, y, z = p
        xr = x * math.cos(ya) + z * math.sin(ya)
        zr = -x * math.sin(ya) + z * math.cos(ya)
        return (xr, y * math.cos(pa) - zr * math.sin(pa), zr * math.cos(pa) + y * math.sin(pa))

    ben = [(b["name"], b.get("pivot", [0, 0, 0]), b.get("cubes", []))
           for b in geo["bones"] if b["name"] not in dolda]
    # RAMEN ÄR GRISENS, inte hundens. Med hundpaketets ram (±9 i x, ±13 i z)
    # skars lantrasens tryne och bakdel av — en gris är bredare och längre.
    hörn = [cam((x, y, z)) for x in (-11, 11) for y in (0, 22) for z in (-16, 12)]
    minx, maxx = min(c[0] for c in hörn), max(c[0] for c in hörn)
    miny, maxy = min(c[1] for c in hörn), max(c[1] for c in hörn)
    pad = int(min(W, H) * 0.05)
    sc = min((W - 2 * pad) / (maxx - minx), (H - 2 * pad) / (maxy - miny))
    offx = pad - minx * sc + (W - 2 * pad - (maxx - minx) * sc) / 2
    offy = pad - miny * sc + (H - 2 * pad - (maxy - miny) * sc) / 2
    cv = [[bakgrund] * W for _ in range(H)]
    zb = [[9e9] * W for _ in range(H)]
    for namn, pivot, kuber in ben:
        deg = pose.get(namn, (0, 0, 0))
        for c in kuber:
            ox, oy, oz = c["origin"]; w, h, d = c["size"]; U, V = c["uv"]
            F = rr.faces(U, V, w, h, d)
            fns = {"top": lambda a, b: (ox + a * w, oy + h, oz + b * d),
                   "bottom": lambda a, b: (ox + a * w, oy, oz + b * d),
                   "north": lambda a, b: (ox + a * w, oy + (1 - b) * h, oz),
                   "south": lambda a, b: (ox + a * w, oy + (1 - b) * h, oz + d),
                   "east": lambda a, b: (ox + w, oy + (1 - b) * h, oz + a * d),
                   "west": lambda a, b: (ox, oy + (1 - b) * h, oz + a * d)}
            for fnamn, fn in fns.items():
                u0, v0, fw, fh = F[fnamn]; skugga = rr.SH[fnamn]
                steg = max(int(max(fw, fh) * sc * 1.6), 10)
                for i in range(steg + 1):
                    for j in range(steg + 1):
                        a, b = i / steg, j / steg
                        p = fn(a, b)
                        X, Y, Z = cam(rr.rot(p, pivot, deg) if any(deg) else p)
                        px = int(X * sc + offx); py = int(H - (Y * sc + offy))
                        if not (0 <= px < W and 0 <= py < H) or Z >= zb[py][px]:
                            continue
                        col = tex[min(th - 1, max(0, int(v0 + b * fh)))][
                            min(tw - 1, max(0, int(u0 + a * fw)))]
                        if col[3] < 8:
                            continue
                        cv[py][px] = (int(col[0] * skugga), int(col[1] * skugga),
                                      int(col[2] * skugga), 255)
                        zb[py][px] = Z
    return cv


def framifran(fil="/tmp/grisar-framifran.png"):
    """RAKT FRAMIFRÅN — vyn spelaren möter när en gris kommer emot en.

    Trekvartsvyn döljer just det som brukar gå fel: att kroppen är en pelare,
    att trynet sitter för högt eller att öronen smält ihop med skallen."""
    RUTA = 240
    raser = rasklient()
    W, H = RUTA * len(raser), RUTA
    duk = [[(26, 30, 38, 255)] * W for _ in range(H)]
    for i, (rasid, geoid, tex) in enumerate(raser):
        b = rita(geoid, tex, RUTA, RUTA, yaw=0, pitch=4, pose={},
                 bakgrund=(26, 30, 38, 255))
        for y in range(RUTA):
            for x in range(RUTA):
                duk[y][i * RUTA + x] = b[y][x]
    rr.write_png(fil, W, H, duk)
    print(f"  {fil} — {', '.join(r[0] for r in raser)} rakt framifrån")


def ark(fil=None, W=None, H=None, RUTA=200, ETIKETT=34, KOL=5):
    """Kontaktkarta över alla raser — en PRODUKTBILD, inte en felsökningsdump.

    Namnen står under grisarna och bottnen är samma toning som sajten, så
    bilden sitter i sidan i stället för att ligga ovanpå den."""
    import make_video as mv                       # text() lånas från trailern

    raser = rasklient()
    rader = math.ceil(len(raser) / KOL)
    W = W or RUTA * KOL
    H = H or (RUTA + ETIKETT) * rader
    mv.W, mv.H = W, H
    bx0 = (W - RUTA * KOL) // 2
    by0 = (H - (RUTA + ETIKETT) * rader) // 2
    # samma toning som sajtens body, så bilden hör ihop med sidan
    duk = [[(int(26 + 10 * y / H), int(20 + 8 * y / H), int(24 + 8 * y / H), 255)
            for _ in range(W)] for y in range(H)]
    for i, (rasid, geoid, tex) in enumerate(raser):
        # Var tredje gris bär något, så sadel, väskor och tryffel alla syns i
        # produktbilden utan att varje gris blir en julgran.
        visa = (("sadel",), ("tryffel",), ("sadel", "vaskor"))[i % 3]
        bild = rita(geoid, tex, RUTA, RUTA, visa=visa, bakgrund=(0, 0, 0, 0))
        rx, ry = bx0 + (i % KOL) * RUTA, by0 + (i // KOL) * (RUTA + ETIKETT)
        for y in range(6, RUTA - 2):
            for x in range(6, RUTA - 6):
                kant = min(x - 6, y - 6, RUTA - 7 - x, RUTA - 3 - y)
                duk[ry + y][rx + x] = (58, 42, 50, 255) if kant < 1 else (40, 30, 36, 255)
        # VIT KONTUR. Utan den försvinner Soot — nästan svart päls mot mörk
        # botten är ingen bild alls.
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, -1), (-1, 1), (1, 1)):
            for y in range(RUTA):
                for x in range(RUTA):
                    if bild[y][x][3] and 0 <= ry + y + dy < H and 0 <= rx + x + dx < W:
                        duk[ry + y + dy][rx + x + dx] = (240, 232, 236, 255)
        for y in range(RUTA):
            for x in range(RUTA):
                if bild[y][x][3]:
                    duk[ry + y][rx + x] = bild[y][x]
        mv.text(duk, rasid.upper(), rx + RUTA // 2, ry + RUTA + 8,
                2 if RUTA < 260 else 3, (226, 168, 138, 255))
    os.makedirs(f"{BASE}/publish", exist_ok=True)
    fil = fil or f"{BASE}/publish/pigs.png"
    rr.write_png(fil, W, H, duk)
    print(f"  {os.path.relpath(fil, BASE)} ({W}x{H}) — {', '.join(r[0] for r in raser)}")


def butiksbild():
    """1280x720-version av kontaktkartan — butikernas skärmbildsformat.
    CurseForge visar skärmbilder i 16:9, och skalas pixelkonst om av butiken
    själv blir den grötig."""
    ark(fil=f"{BASE}/publish/store-pigs.png", W=1280, H=720, RUTA=240, ETIKETT=42, KOL=5)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--butik"]:
        butiksbild()
    elif sys.argv[1:2] == ["--framifran"]:
        framifran()
    elif len(sys.argv) > 1:
        rasid = sys.argv[1]
        geoid, tex = next((g, t) for r, g, t in rasklient() if r == rasid)
        rr.write_png(f"{BASE}/publish/pig-{rasid}.png", 400, 400,
                     rita(geoid, tex, 400, 400, visa=("sadel", "tryffel")))
        print(f"  publish/pig-{rasid}.png")
    else:
        ark()
