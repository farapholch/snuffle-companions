#!/usr/bin/env python3
"""Genererar grisarna: geometrier, pälsar, entiteter, klientdefinitioner,
spawnägg, spawnregler, renderarkontroller, tryffeln och språkfiler.

Ingenting ritas eller skrivs för hand som kan räknas fram ur en tabell. Samma
maskineri som tools/make_dogs.py i Loyal Companions — kubtabell in, geometri
och textur ut ur SAMMA tabell, så UV och bild inte kan glida isär.

DET SOM GÖR EN GRIS TILL EN GRIS ÄR TRYNET. En hund känns igen på silhuetten,
men alla grisar har ungefär samma silhuett: låg, bred, tung. Trynet är det enda
som säger "gris" på en halv sekund, så det är en egen kub som sticker rakt ut
ur ansiktet och målas i en färg som bryter mot pälsen. Raserna skiljs sedan åt
på storlek, färg och öronform.

    python3 tools/make_pigs.py
"""
import json, math, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/opt/purrfect-companions")
import render_regression as rr          # PNG-läsning/-skrivning

BP = f"{BASE}/SnuffleCompanions_BP"
RP = f"{BASE}/SnuffleCompanions_RP"
NS = "gris"
TW = TH = 128                          # texturduk; grisar är större kuber än hundar

# Det grisen gräver upp och äter. Tryffeln är vår egen; rotfrukterna finns i
# spelet, och en gris ska kunna lockas med en morot utan att paketet uppfinner
# ett eget lockbete.
TAMFODER = ["carrot"]
AVELSFODER = [f"{NS}:tryffel", "potato", "beetroot"]
# Jordarter grisen kan böka i. Läses av skriptet via språkfilen? Nej — listan
# lever i skriptet också, och strukturtestet jämför de två listorna. Två
# ställen som ska hållas i synk är exakt den fälla hundpaketet gick i, men här
# går den inte att undvika: entitets-JSON kan inte läsa skriptet och tvärtom.
# minecraft:rooted_dirt FINNS INTE I BEDROCK — där heter blocket
# minecraft:dirt_with_roots. Namnet togs från Javas blocklista, och ID-testet
# mot motorn fångade det; ingen fil på disk hade gjort det.
BOKBAR = ["minecraft:grass_block", "minecraft:dirt", "minecraft:coarse_dirt",
          "minecraft:podzol", "minecraft:mycelium", "minecraft:dirt_with_roots",
          "minecraft:moss_block", "minecraft:mud"]


# --- kroppen -----------------------------------------------------------------
# Måtten är i modellenheter (16 = ett block). Allt hänger ihop: huvudet sitter
# framför kroppen, trynet framför huvudet, svansen bakom. Ändras kroppslängden
# följer resten med.
def kroppsdelar(bh=6, kl=16, kb=10, kh=8, hs=8, tl=3, oron="upp", ludd=False):
    """bh benhöjd, kl kroppslängd, kb kroppsbredd, kh kroppshöjd,
    hs huvudstorlek, tl trynets längd.

    HUVUDET SITTER LÅGT OCH ÄR PLATTARE ÄN DET ÄR BRETT. Med ett kubiskt huvud
    lika högt som brett stack skallen upp ÖVER ryggen, och renderingen visade
    två lika stora lådor efter varandra — grisen läste som ett tvåpucklat djur.
    Huvudets ovansida ligger nu i jämnhöjd med ryggen, som på en riktig gris."""
    hh = hs * 0.85                                    # huvudets höjd
    hz = -kl / 2 - hs * 0.55                          # huvudets framkant i z
    hy = bh + kh - hh                                 # ovansidan i jämnhöjd med ryggen
    # TRYNET FÅR INTE ÄTA ANSIKTET. Med bredden 0,55*hs och höjden 0,42*hh
    # täckte det över halva huvudets framsida, och framifrån fanns ingen plats
    # kvar åt ögonen — de trängdes upp i pannan och läste som ögonbryn.
    tb = hs * 0.45                                    # trynets bredd
    th_ = hh * 0.30                                   # trynets höjd
    d = [
        ("body", "body", None, [-kb / 2, bh, -kl / 2], [kb, kh, kl]),
        ("head", "head", None, [-hs / 2, hy, hz], [hs, hh, hs * 0.65]),
        # TRYNET STICKER RAKT UT och är trubbigt avskuret. Första försöket
        # smalnade av det som en hundnos och grisen såg ut som en rosa varg.
        ("tryne", "head", None, [-tb / 2, hy + hh * 0.15, hz - tl], [tb, th_, tl]),
        # TRYNSKIVAN. En avlång låda är ingen grisnos. Tamworthens tryne är
        # 4,5 enheter långt och blev en TUB som stack rakt fram — från sidan
        # läste grisen som en myrslok, och det var precis vad spelaren sa.
        #
        # En gris känns igen på att nosen slutar i en PLATT SKIVA som är
        # bredare och högre än nosryggen. Skivan sitter längst fram, är en halv
        # enhet tjock och sticker ut en tiondel så den inte flimrar mot trynets
        # framsida (z-fighting). NÄSBORRARNA MÅLAS PÅ SKIVAN, inte på trynet —
        # det är skivan man ser framifrån.
        ("trynskiva", "head", None,
         [-(tb + 1) / 2, hy + hh * 0.15 - 0.5, hz - tl - 0.4], [tb + 1, th_ + 1, 0.5]),
    ]
    if oron == "upp":
        # Uppstående öron sitter BAKÅT på skallen, inte på framkanten — en gris
        # har öronen nästan i nacken.
        for x in (-hs / 2, hs / 2 - 2):
            d.append(("ora", "head", None, [x, hy + hh - 1, hz + hs * 0.3], [2, 3.5, 1.5]))
    else:
        # Hängöron helt utanför skallen, annars smälter de ihop med huvudet
        # till ett mörkt block — samma fälla som hundarnas hängöron.
        for x in (-hs / 2 - 1.5, hs / 2):
            d.append(("ora", "head", None, [x, hy + hh - 4.5, hz + hs * 0.2], [1.5, 4.5, 3.5]))
    bz = [-kl / 2 + 0.5, kl / 2 - 4.5]                # fram- och bakben i z
    for i, (x, z) in enumerate([(-kb / 2 + 0.5, bz[0]), (kb / 2 - 4.5, bz[0]),
                                (-kb / 2 + 0.5, bz[1]), (kb / 2 - 4.5, bz[1])]):
        d.append(("ben", f"leg{i}", None, [x, 0, z], [4, bh, 4]))
    # SVANSEN ÄR EN KROK, inte ett spö. Två små kuber i vinkel läser som en
    # knorr; en enda avlång kub läser som en råttsvans.
    d.append(("svans", "tail", None, [-1, bh + kh - 3, kl / 2], [2, 2, 2]))
    d.append(("svans", "tail", None, [-1, bh + kh - 1.5, kl / 2 + 1], [2, 2, 2]))
    if ludd:
        # ULLEN. En mangalitsa utan ull är bara en blek gris. Kuberna
        # ÖVERLAPPAR kroppen så de inte svävar, och de sitter på rygg och sidor
        # där ullen faktiskt är tjockast.
        d.append(("ull", "body", None, [-kb / 2 - 1, bh + kh - 4, -kl / 2 + 1], [kb + 2, 4.5, kl - 2]))
        d.append(("ull", "head", None, [-hs / 2 - 0.75, hy + hh - 2.5, hz + 1], [hs + 1.5, 3, hs * 0.5]))
    # SADELN: en kub över ryggen som bara syns när grisen är sadlad. Samma
    # trick som hundarnas halsband — renderarkontroller kan bara tända och
    # släcka BEN, inte färga dem, så varje tillstånd får en egen kub.
    d.append(("sadel", "sadel", "body", [-kb / 2 - 0.5, bh + kh - 0.5, -kl / 2 + 5],
              [kb + 1, 2, 8]))
    # VÄSKORNA hänger på sidorna och syns bara med kista på. De sitter BAKOM
    # sadeln så ryttarens ben inte går igenom dem.
    for x in (-kb / 2 - 2.5, kb / 2 - 0.5):
        d.append(("vaska", "vaskor", "body", [x, bh + kh - 6, kl / 2 - 8], [3, 5, 6]))
    # LERAN. En gris VÄLTRAR SIG — det är det mest ikoniska djuret gör, och
    # ingenting i paketet gjorde det.
    #
    # LERAN SITTER UNDERTILL, inte på ryggen. Första försöket la ett lager över
    # ryggen och det läste som en SADEL, inte som lera — vilket är helt logiskt:
    # en gris som vältrat sig har LEGAT i geggan, så det är magen, sidorna
    # nedtill och benen som blir smutsiga.
    #
    # ÖVERLAPPAR med en tiondel så ytorna inte flimrar mot varandra
    # (z-fighting); två ytor på exakt samma plats blinkar.
    d.append(("lera", "lera", "body", [-kb / 2 - 0.1, bh - 0.1, -kl / 2 + 0.4],
              [kb + 0.2, kh * 0.5, kl - 0.8]))
    # ...och stänk på benen. De hänger i VARJE bens eget ben, annars blir leran
    # stående still medan grisen går.
    for i, (x, z) in enumerate([(-kb / 2 + 0.4, -kl / 2 + 0.4), (kb / 2 - 4.4, -kl / 2 + 0.4),
                                (-kb / 2 + 0.4, kl / 2 - 4.6), (kb / 2 - 4.4, kl / 2 - 4.6)]):
        d.append(("lera", "lera", f"leg{i}", [x, -0.1, z], [4.2, bh * 0.55, 4.2]))
    # TRYFFELN I TRYNET: syns när grisen just bökat upp något och ännu inte
    # släppt det. Hängd i huvudbenet så den följer med när grisen tittar upp.
    d.append(("tryffel", "tryffel", "head", [-1.25, hy + hh * 0.15 - 2.75, hz - tl + 0.5],
              [2.5, 2.5, 2.5]))
    return d


PIVOT = lambda bh, kl, kb, kh, hs: {
    "body": [0, bh + kh / 2, 0],
    "head": [0, bh + kh - hs * 0.5, -kl / 2],   # nacken, där huvudet möter bålen
    "leg0": [-kb / 2 + 2.5, bh, -kl / 2 + 2.5], "leg1": [kb / 2 - 2.5, bh, -kl / 2 + 2.5],
    "leg2": [-kb / 2 + 2.5, bh, kl / 2 - 2.5], "leg3": [kb / 2 - 2.5, bh, kl / 2 - 2.5],
    "tail": [0, bh + kh - 2, kl / 2],
    "sadel": [0, bh + kh, 0], "vaskor": [0, bh + kh - 4, kl / 2 - 5],
    "lera": [0, bh + kh / 2, 0],
    "tryffel": [0, bh + kh - hs * 0.5, -kl / 2],
}

# (benhöjd, kroppslängd, kroppsbredd, kroppshöjd, huvud, tryne, öron, ull)
KROPPAR = {
    "normal":  (6, 16, 10, 8, 8, 3, "upp", False),
    "stor":    (7, 18, 11, 9, 9, 3, "hang", False),    # lantras: tung och storvuxen
    "ludd":    (6, 15, 10, 8.5, 8, 3, "hang", True),   # mangalitsa: ullgris
    "liten":   (4.5, 12, 8, 7, 7, 2.5, "upp", False),  # kunekune: låg och rund
    "lang":    (6.5, 18, 8.5, 7.5, 8, 4.5, "upp", False),  # tamworth: lång kropp, långt tryne
}


def packa(delar):
    """Hyllpackning av UV-ytan. Kuber sorteras på höjd och läggs ut i rader.

    Bedrocks utfällning av en kub (b,h,d) är 2*(d+b) bred och d+h hög."""
    rutor = []
    for i, (_roll, _ben, _f, _o, size) in enumerate(delar):
        b, h, d = size
        rutor.append((i, math.ceil(2 * (d + b)), math.ceil(d + h)))
    x = y = radhojd = 0
    uv = {}
    for i, w, h in sorted(rutor, key=lambda r: -r[2]):
        if x + w > TW:
            x, y, radhojd = 0, y + radhojd, 0
        if y + h > TH:
            raise SystemExit(f"UV-ytan räcker inte till ({TW}x{TH})")
        uv[i] = [x, y]
        x += w
        radhojd = max(radhojd, h)
    return uv


def geometri(namn, matt):
    bh, kl, kb, kh, hs, tl, oron, ludd = matt
    delar = kroppsdelar(bh, kl, kb, kh, hs, tl, oron, ludd)
    uv = packa(delar)
    ben = {}
    for i, (_roll, benamn, forlder, origin, size) in enumerate(delar):
        b = ben.setdefault(benamn, {"name": benamn, "pivot": PIVOT(bh, kl, kb, kh, hs).get(
            benamn, [0, bh, 0]), "cubes": []})
        if forlder:
            b["parent"] = forlder
        b["cubes"].append({"origin": origin, "size": size, "uv": uv[i]})
    return {
        "description": {
            "identifier": f"geometry.gris_{namn}",
            # MÅSTE stämma med PNG-filen, annars läses UV i fel skala och
            # modellen blir obegriplig i spelet — servern märker ingenting.
            "texture_width": TW, "texture_height": TH,
            "visible_bounds_width": 3, "visible_bounds_height": 2.5,
            "visible_bounds_offset": [0, 0.9, 0],
        },
        "bones": list(ben.values()),
    }, delar, uv


def skriv_geometrier():
    g, delar, uv = {}, {}, {}
    for namn, matt in KROPPAR.items():
        g[namn], delar[namn], uv[namn] = geometri(namn, matt)
    json.dump({"format_version": "1.12.0",
               "minecraft:geometry": [g[n] for n in KROPPAR]},
              open(f"{RP}/models/entity/gris.geo.json", "w"), indent=2)
    return delar, uv


def renderarkontroller():
    """Egen renderarkontroller: controller.render.default visar allt, och då
    skulle grisen alltid gå omkring med sadel, väskor OCH en tryffel i trynet."""
    json.dump({"format_version": "1.10.0", "render_controllers": {
        "controller.render.gris": {
            "geometry": "Geometry.default",
            "materials": [{"*": "Material.default"}],
            "textures": ["Texture.default"],
            "part_visibility": [
                {"*": True},
                {"sadel": f"q.property('{NS}:sadlad') == 1"},
                {"vaskor": f"q.property('{NS}:vaskor') == 1"},
                {"tryffel": f"q.property('{NS}:bar') == 1"},
                {"lera": f"q.property('{NS}:lerig') == 1"}]}}},
        open(f"{RP}/render_controllers/gris.render_controllers.json", "w"), indent=2)


# --- pälsen ------------------------------------------------------------------
def sh(c, k):
    return tuple(min(255, int(v * k)) for v in c[:3]) + (255,)


# FYRA TEXLAR PER ENHET sedan v1.4.0, samma mekanism som katt- och hundpaketet:
# geometrin deklarerar TW x TH uv-enheter och PNG:en är SKALA gånger det.
# Innan dess var varje sida ett färgfält; grisen var en rosa låda med två
# prickar. Nu har huden fläckvis mönstring och glesa borst, ullen krusar sig,
# leran är klumpig, sadeln har sömmar och trynskivan är en skiva.
SKALA = 4
sys.path.insert(0, "/opt/purrfect-companions/tools")
from make_cat_pals import Duk, korn, blanda, skala as ton, lum, _h

SIDSKUGGA = {"top": 1.06, "bottom": 0.80, "north": 1.0, "south": 0.95,
             "east": 0.95, "west": 0.95}

# Sadel, väskor och tryffel har föremålens färger, inte grisens.
UTRUSTNING = {"sadel": (118, 74, 42), "vaska": (96, 62, 38), "tryffel": (84, 62, 48),
              "lera": (86, 68, 52)}


def _R(f):
    return tuple(v * SKALA for v in f)


def hud(bas, sida, borst=True, k=0.6):
    """Grishud: ljus uppifrån, fläckvis mönstring och glesa mörka borst."""
    bas = tuple(bas[:3])
    morkare = blanda(bas, (0, 0, 0), 0.12)

    def fn(a, b, x, y):
        c = ton(bas, SIDSKUGGA[sida] * (1.05 - 0.14 * b))
        n = _h(x // 5, y // 5, 31) * 0.6 + _h(x // 11, y // 11, 32) * 0.4
        c = blanda(c, morkare, max(0.0, n - 0.5) * 0.5)
        if borst and _h(x // 2, y // 4, 33) < 0.05 and (y % 4) < 3:
            c = ton(c, 0.86)                                   # ett borststrå
        return korn(c, x, y, k)
    return fn


def pals(rasid, delar, uv, farg):
    """Målar en hel hud ur kubtabellen: en yta per kubsida, sedan mönstren,
    sist ansiktet."""
    duk = Duk(TW * SKALA, TH * SKALA)
    P, SK, UN, TR = (tuple(farg["pals"]), tuple(farg["skugga"]),
                     tuple(farg["under"]), tuple(farg["tryne"]))

    def fyll(f, fn):
        duk.yta(_R(f), fn, 255)

    def rect(x0, y0, w, h, c):
        duk.yta((x0 * SKALA, y0 * SKALA, w * SKALA, h * SKALA),
                lambda a, b, x, y: korn(tuple(c[:3]), x, y, 0.5), 255)

    sidor = {}
    for i, (roll, benamn, _f, _o, size) in enumerate(delar):
        b_, h_, d_ = size
        u, v = uv[i]
        f = rr.faces(u, v, b_, h_, d_)
        sidor.setdefault(roll, []).append((f, size))
        if roll in ("sadel", "vaska", "tryffel", "lera"):
            _utrustning(duk, roll, f, size)
            continue
        if roll == "ull":
            for namn, yta in f.items():
                fyll(yta, _ull(UN, namn))
            continue
        grund = {"ora": SK, "tryne": TR, "trynskiva": TR}.get(roll, P)
        for namn, yta in f.items():
            fyll(yta, hud(grund, namn, borst=(roll in ("body", "head", "ben"))))
        if roll == "ora":
            inre = blanda(SK, TR, 0.5)
            fyll(f["north"], lambda a, b, x, y: korn(inre, x, y, 0.4)
                 if 0.2 < b < 0.9 and abs(a - 0.5) < 0.1 + 0.3 * b else hud(SK, "north", False)(a, b, x, y))

    for mall in farg.get("monster", []):
        MONSTER[mall](rect, sidor, farg, fyll)

    # ANSIKTET sist, så inget mönster målar över ögonen.
    mork = blanda(P, (0, 0, 0), 0.75) if lum(P) > 70 else blanda(P, (255, 255, 255), 0.35)
    for f, size in sidor["head"]:
        hs, hh = size[0], size[1]
        fx, fy, fw, fh = f["north"]
        # ÖGONEN I ÖVRE TREDJEDELEN, räknat ur huvudets höjd; storleken följer
        # huvudet — ett litet öga på familjens största huvud var Blossoms bugg.
        cy = fh * 0.32
        rx = 0.62 if hs >= 8 else 0.48
        ry = rx * 0.9
        ogon = [(1.6, cy, +1), (fw - 1.6, cy, -1)]
        iris, iris_m = tuple(farg["ogon"]), blanda(tuple(farg["ogon"]), (0, 0, 0), 0.45)
        glans = blanda(UN, (255, 255, 255), 0.5)

        # LEENDET. En gris utan mun är en gris utan uttryck; ett leende under
        # trynet och rosiga kinder är hela skillnaden mellan "gris" och "glad
        # gris". Munnen ligger på skallens framsida, i remsan under trynet,
        # och böjer UPPÅT i vinklarna. Kinderna är en antydan till rodnad
        # snett under ögonen, mest synlig på de ljusa grisarna.
        mun = blanda(mork, TR, 0.25)
        kind = blanda(P, (226, 96, 110), 0.40)
        tryne_botten = 0.85                         # trynet slutar 15 % ovanför hakan

        def ansikte(a, b, x, y, fn0=hud(P, "north")):
            X, Y = a * fw, b * fh
            c = fn0(a, b, x, y)
            for ex, ey, _i in ogon:
                if math.hypot((X - ex + _i * 0.3) / 1.1, (Y - (ey + ry + 1.0)) / 0.8) < 1.0:
                    c = blanda(c, kind, 0.7)
            # munnen: en båge som hänger under trynet och vänder upp mot kinderna
            # TRYNSKIVAN SKYMMER. Den är bredare och lägre än trynet (ner till
            # 92 % av huvudets höjd, ut till 29 % från mitten), så två försök
            # med en båge under trynet gav bara ett streck: resten låg bakom
            # skivan. Mungiporna måste därför ut FÖRBI skivans kant och upp mot
            # kinderna för att synas — det är där ett grin sitter ändå.
            mitt_b = tryne_botten + 0.11
            for tecken in (-1, 1):
                t = tecken * (a - 0.5) / 0.42          # 0 i mitten, 1 vid mungipan
                if 0 <= t <= 1.0:
                    kurva = mitt_b - 0.28 * t * t
                    if abs(b - kurva) < 0.05:
                        return mun
            for ex, ey, inat in ogon:
                dx, dy = (X - ex) / rx, (Y - ey) / ry
                r = math.hypot(dx, dy)
                if r > 1.0:
                    if abs(X - ex) < rx + 0.2 and 0 < ey - ry - Y < 0.4:
                        return blanda(c, mork, 0.2)                  # brynet
                    continue
                if r > 0.80:
                    return mork
                if math.hypot(X - ex, Y - ey) < 0.24:
                    return blanda(iris_m, (0, 0, 0), 0.8)
                if math.hypot(X - (ex + inat * 0.22), Y - (ey - 0.22)) < 0.16:
                    return glans
                return blanda(iris, iris_m, 0.15 + 0.5 * (dy + 1) / 2)
            return c
        fyll(f["north"], ansikte)

    # NÄSBORRARNA ÄR HELA POÄNGEN. Två ovala hål på skivan, med glapp emellan,
    # och en svagt mörkare ring runt skivans kant så den läser som en skiva.
    nosborre = blanda(TR, (0, 0, 0), 0.6) if lum(TR) > 130 else blanda(TR, (255, 255, 255), 0.5)
    for f, size in sidor["trynskiva"]:
        fx, fy, fw, fh = f["north"]

        def skiva(a, b, x, y):
            X, Y = a * fw, b * fh
            c = korn(ton(TR, 1.04 - 0.1 * b), x, y, 0.4)
            if a < 0.08 or a > 0.92 or b < 0.1 or b > 0.9:
                c = ton(c, 0.88)
            for nx in (fw * 0.31, fw * 0.69):
                if math.hypot((X - nx) / (fw * 0.09), (Y - fh * 0.5) / (fh * 0.22)) < 1.0:
                    return nosborre
            return c
        fyll(f["north"], skiva)

    for f, size in sidor["tryne"]:
        fyll(f["top"], hud(ton(TR, 1.08), "top", False))
    rr.write_png(f"{RP}/textures/entity/{rasid}.png", TW * SKALA, TH * SKALA, duk.px)


def _ull(UN, sida):
    """Krusig ull: små ljusa bågar i ett fast rutnät, som lockar."""
    UN = tuple(UN[:3])
    ljus, mork = blanda(UN, (255, 255, 255), 0.3), blanda(UN, (0, 0, 0), 0.18)

    def fn(a, b, x, y):
        cx, cy = x % 5, y % 5
        c = ton(UN, SIDSKUGGA[sida] * (1.04 - 0.1 * b))
        r = math.hypot(cx - 2, cy - 2)
        if 1.2 < r < 2.3 and cy <= 2:
            c = ljus
        elif 1.2 < r < 2.3:
            c = mork
        return korn(c, x, y, 0.6)
    return fn


def _utrustning(duk, roll, f, size):
    c = tuple(UTRUSTNING[roll][:3])
    for namn, yta in f.items():
        X0, Y0, FW, FH = _R(yta)

        def fn(a, b, x, y, namn=namn, FW=FW, FH=FH):
            X, Y = a * FW, b * FH
            col = ton(c, SIDSKUGGA[namn] * (1.05 - 0.14 * b))
            if roll == "sadel":
                # läder med sömmar och två mörka remmar tvärs över
                if namn in ("east", "west"):
                    col = ton(col, 0.85)
                if namn == "top" and abs(b - 0.5) * FH < 2.0:
                    return ton(c, 0.55)
                if namn in ("east", "west") and abs(a - 0.5) * FW < 2.0:
                    return ton(c, 0.55)
                if (1 <= X < 2 or FW - 2 <= X < FW - 1 or 1 <= Y < 2 or FH - 2 <= Y < FH - 1) and (x + y) % 3:
                    return blanda(c, (255, 255, 255), 0.4)
                return korn(col, x, y, 0.4)
            if roll == "vaska":
                # segelduk med en rem och ett spänne fram
                if (x + y) % 2 == 0:
                    col = ton(col, 1.03)
                if namn in ("east", "west", "north", "south") and abs(b - 0.35) < 0.05:
                    return ton(c, 0.6)                           # remmen
                if namn in ("east", "west") and abs(a - 0.5) < 0.1 and 0.28 < b < 0.62:
                    return (200, 176, 100) if (abs(a - 0.5) < 0.06 and 0.32 < b < 0.58) else (110, 90, 50)
                if namn in ("east", "west") and b < 0.3:
                    col = ton(col, 0.9)                           # locket
                return korn(col, x, y, 0.4)
            if roll == "tryffel":
                # knotig: mörka gropar och ljusa knölar i ett fast mönster
                n = _h(x // 2, y // 2, 41)
                if n > 0.85:
                    return blanda(c, (255, 255, 255), 0.35)
                if n < 0.2:
                    return blanda(c, (0, 0, 0), 0.35)
                return korn(col, x, y, 0.5)
            # LERAN: klumpig och blöt, med torkad ljusare kant upptill och rinn
            n = _h(x // 3, y // 3, 51) * 0.7 + _h(x // 7, y // 7, 52) * 0.3
            col = blanda(col, (0, 0, 0), max(0.0, n - 0.5) * 0.6)
            if b < 0.12 and _h(x, 0, 53) < 0.6:
                col = blanda(col, (170, 150, 120), 0.4)           # torkad kant
            if _h(x // 2, 0, 54) < 0.12 and b < 0.5:
                col = ton(col, 0.85)                              # rinn
            return korn(col, x, y, 0.6)
        duk.yta((X0, Y0, FW, FH), fn, 255)


# --- mönstren ---------------------------------------------------------------
def m_sockor(rect, sidor, farg, fyll):
    """Ljusa klövar: nedre tredjedelen av varje bensida, med klövspringa."""
    UN, SK = tuple(farg["under"]), tuple(farg["skugga"])
    for f, size in sidor["ben"]:
        for namn in ("north", "south", "east", "west"):
            k = SIDSKUGGA[namn]

            def fn(a, b, x, y, k=k, namn=namn):
                if b < 0.66 + 0.03 * math.sin(a * 9 + 1):
                    return None
                if b > 0.86 and namn in ("north", "south") and abs(a - 0.5) < 0.05:
                    return blanda(UN, (0, 0, 0), 0.4)             # klövspringan
                return korn(ton(UN, k), x, y, 0.5)
            fyll(f[namn], fn)
        fyll(f["bottom"], lambda a, b, x, y: korn(ton(UN, 0.75), x, y, 0.5))


def m_band(rect, sidor, farg, fyll):
    """Sadelband: ett brett ljust bälte tvärs över bålen — hampshiregrisen."""
    UN = tuple(farg["under"])
    for f, size in sidor["body"]:
        for namn in ("east", "west", "top"):
            k = SIDSKUGGA[namn]
            if namn == "top":
                fyll(f[namn], lambda a, b, x, y, k=k: korn(ton(UN, k), x, y, 0.5)
                     if 0.22 + 0.02 * math.sin(a * 11) < b < 0.44 + 0.02 * math.sin(a * 9) else None)
            else:
                fyll(f[namn], lambda a, b, x, y, k=k: korn(ton(UN, k), x, y, 0.5)
                     if 0.22 + 0.02 * math.sin(b * 11) < a < 0.44 + 0.02 * math.sin(b * 9) else None)


def m_blas(rect, sidor, farg, fyll):
    """Bläs: en ljus rand mitt i ansiktet och över nosryggen."""
    UN = tuple(farg["under"])
    for f, size in sidor["head"]:
        fw = f["north"][2]
        fyll(f["north"], lambda a, b, x, y: korn(UN, x, y, 0.5)
             if abs(a - 0.5) * fw < 0.7 + 0.3 * b else None)
        fyll(f["top"], lambda a, b, x, y: korn(ton(UN, 1.05), x, y, 0.5)
             if abs(a - 0.5) * f["top"][2] < 0.9 else None)


def m_flackar(rect, sidor, farg, fyll):
    """Runda fläckar över hela grisen. Deterministiska, så samma gris får
    samma fläckar varje körning."""
    SK = tuple(farg["skugga"])
    for roll in ("body", "head", "ben", "svans"):
        for f, size in sidor.get(roll, []):
            for namn, (fx, fy, fw, fh) in f.items():
                flackar = []
                n = int(fx * 31 + fy * 17) & 0x7FFFFFFF
                for _ in range(max(1, int(fw * fh / 16))):
                    n = (n * 1103515245 + 12345) & 0x7FFFFFFF
                    flackar.append(((n >> 7) % 1000 / 1000 * fw, (n >> 17) % 1000 / 1000 * fh,
                                    0.9 + ((n >> 3) & 3) * 0.35, 0.7 + ((n >> 5) & 3) * 0.2))
                k = SIDSKUGGA[namn]

                def fn(a, b, x, y, flackar=flackar, fw=fw, fh=fh, k=k):
                    X, Y = a * fw, b * fh
                    for px_, py_, r, e in flackar:
                        if math.hypot((X - px_) / r, (Y - py_) / (r * e)) < 1.0 + 0.08 * math.sin(X * 5 + Y * 3):
                            return korn(ton(SK, k), x, y, 0.5)
                    return None
                fyll((fx, fy, fw, fh), fn)


def m_ullkrus(rect, sidor, farg, fyll):
    """Ullen krusar sig redan i grundmålningen (_ull); mönstret finns kvar som
    namn i RASER och gör inget mer."""
    return


MONSTER = {"sockor": m_sockor, "band": m_band, "blas": m_blas,
           "flackar": m_flackar, "ullkrus": m_ullkrus}


# --- raserna -----------------------------------------------------------------
# Fem grisar som ska gå att skilja åt på en halv sekund, och som ska vara olika
# att ANVÄNDA — inte bara att titta på. Näsan, farten och bärförmågan skiljer
# sig, och det är den skillnaden som gör att man väljer gris efter uppgift.
#
# (id, namn, ras, kropp, skala, biom, nos, fart, liv, färger)
#   nos  = hur långt grisen känner malm genom berget (block)
#   fart = minecraft:movement
#   liv  = minecraft:health
RASER = [
    ("nilla", "Nilla", "Kunekune", "liten", 0.85, "plains", 6, 0.26, 14,
     dict(pals=(226, 168, 128), skugga=(168, 112, 78), under=(246, 224, 200),
          tryne=(232, 158, 152), ogon=(64, 44, 36), monster=["flackar"])),
    ("bramble", "Bramble", "Mangalitsa", "ludd", 1.0, "taiga", 7, 0.24, 20,
     dict(pals=(206, 178, 128), skugga=(150, 122, 82), under=(240, 224, 186),
          tryne=(198, 152, 132), ogon=(72, 54, 34), monster=["ullkrus"])),
    ("blossom", "Blossom", "Large White", "stor", 1.1, "plains", 5, 0.22, 24,
     dict(pals=(238, 186, 178), skugga=(196, 136, 130), under=(250, 224, 220),
          tryne=(236, 152, 150), ogon=(74, 48, 44), monster=["sockor"])),
    ("soot", "Soot", "Berkshire", "normal", 1.0, "forest", 12, 0.25, 18,
     dict(pals=(48, 44, 48), skugga=(28, 26, 30), under=(240, 238, 232),
          tryne=(96, 76, 78), ogon=(198, 150, 70), monster=["sockor", "blas"])),
    ("ember", "Ember", "Tamworth", "lang", 1.0, "savanna", 8, 0.32, 16,
     dict(pals=(186, 92, 44), skugga=(132, 60, 28), under=(226, 158, 96),
          tryne=(214, 134, 118), ogon=(80, 50, 30), monster=["band"])),
]

# SPRÅKEN. Familjen spelar på svenska, så sv_SE innehåller svensk text — inte
# en ordagrann kopia av en_US, vilket är exakt vad hundpaketet levererade i tre
# versioner innan någon läste efter.
RAS_SV = {"Kunekune": "Kunekune", "Mangalitsa": "Ullgris",
          "Large White": "Lantras", "Berkshire": "Berkshire",
          "Tamworth": "Tamworth"}
SPRAK = {
    "en_US": dict(agg="Spawn {n}", tryffel="Truffle", sadla="Saddle up",
                  kista="Fit saddlebags", kommando="Command",
                  lage=("Follow", "Snuffle", "Stay"),
                  hittade="Your pig roots up a truffle.",
                  vittring="{n} picks up a scent: {m} {r}, {d} blocks off.",
                  ingenting="{n} snuffles around and finds nothing.",
                  riktning=("north", "east", "south", "west"),
                  behover_sadel="This pig needs a saddle before you can ride it."),
    "sv_SE": dict(agg="Skapa {n}", tryffel="Tryffel", sadla="Sadla",
                  kista="Sätt på sadelväskor", kommando="Kommando",
                  lage=("Följ", "Böka", "Stanna"),
                  hittade="Grisen bökar upp en tryffel.",
                  vittring="{n} får vittring: {m} {r}, {d} block bort.",
                  ingenting="{n} bökar runt och hittar ingenting.",
                  riktning=("norrut", "österut", "söderut", "västerut"),
                  behover_sadel="Grisen behöver en sadel innan du kan rida den."),
}
# Malmerna grisen kan känna, i den ordning den bryr sig om dem. Namnen visas i
# vittringsmeddelandet, så de hör hemma i språktabellen och inte i skriptet.
MALM = [
    ("minecraft:ancient_debris", "Ancient debris", "Forntida spillror"),
    ("minecraft:diamond_ore", "Diamond", "Diamant"),
    ("minecraft:deepslate_diamond_ore", "Diamond", "Diamant"),
    ("minecraft:emerald_ore", "Emerald", "Smaragd"),
    ("minecraft:deepslate_emerald_ore", "Emerald", "Smaragd"),
    ("minecraft:gold_ore", "Gold", "Guld"),
    ("minecraft:deepslate_gold_ore", "Gold", "Guld"),
    ("minecraft:iron_ore", "Iron", "Järn"),
    ("minecraft:deepslate_iron_ore", "Iron", "Järn"),
    ("minecraft:lapis_ore", "Lapis", "Lapis"),
    ("minecraft:deepslate_lapis_ore", "Lapis", "Lapis"),
    ("minecraft:redstone_ore", "Redstone", "Rödsten"),
    ("minecraft:deepslate_redstone_ore", "Redstone", "Rödsten"),
    ("minecraft:copper_ore", "Copper", "Koppar"),
    ("minecraft:deepslate_copper_ore", "Copper", "Koppar"),
    ("minecraft:coal_ore", "Coal", "Kol"),
    ("minecraft:deepslate_coal_ore", "Coal", "Kol"),
]


def sprakrader(spr):
    t = SPRAK[spr]
    rader = []
    for rasid, namn, ras, _k, _s, _b, _n, _f, _l, _farg in RASER:
        r = RAS_SV[ras] if spr == "sv_SE" else ras
        rader += [f"entity.{NS}:{rasid}.name={namn} ({r})",
                  f"entity.{rasid}.name={namn} ({r})",
                  f"item.spawn_egg.entity.{NS}:{rasid}.name=" + t["agg"].format(n=namn)]
    rader += [f"item.{NS}:tryffel.name=" + t["tryffel"],
              "action.interact.saddle=" + t["sadla"],
              "action.interact.saddlebags=" + t["kista"],
              "action.interact.command=" + t["kommando"],
              # SKRIPTETS KVITTON hör hemma i tabellen, inte i skriptet. Lades de
              # till i .lang-filen för hand försvann de nästa gång generatorn
              # kördes, för den skriver om filen från grunden.
              f"{NS}.tryffel.hittad=" + t["hittade"],
              f"{NS}.vittring=" + t["vittring"],
              f"{NS}.ingenting=" + t["ingenting"],
              f"{NS}.behover_sadel=" + t["behover_sadel"]]
    rader += [f"{NS}.lage.{i}=" + n for i, n in enumerate(t["lage"])]
    rader += [f"{NS}.riktning.{i}=" + n for i, n in enumerate(t["riktning"])]
    for i, (_id, en, sv) in enumerate(MALM):
        rader.append(f"{NS}.malm.{i}=" + (sv if spr == "sv_SE" else en))
    return rader


def ikon(rasid, farg, oron):
    """16x16 grisansikte — samma formspråk som hund- och kattpaketens spawnägg.
    TRYNET TAR MITTEN. På en 16-pixlarsbild är det enda som hinner läsa som
    "gris" ett stort ljust tryne med två näsborrar."""
    N = 16
    px = [[(0, 0, 0, 0)] * N for _ in range(N)]

    def rect(x0, y0, w, h, c):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                if 0 <= x < N and 0 <= y < N:
                    px[y][x] = c
    p, s, u, o, t = farg["pals"], farg["skugga"], farg["under"], farg["ogon"], farg["tryne"]
    rect(2, 3, 12, 11, p + (255,))
    if oron == "upp":
        rect(2, 0, 3, 4, s + (255,))
        rect(11, 0, 3, 4, s + (255,))
    else:
        rect(0, 3, 2, 7, s + (255,))
        rect(14, 3, 2, 7, s + (255,))
    rect(2, 3, 12, 1, sh(p, 1.16))
    rect(4, 8, 8, 5, t + (255,))            # trynet
    rect(4, 8, 8, 1, sh(t, 1.15))
    rect(6, 10, 1, 2, (38, 24, 28, 255))    # näsborrar
    rect(9, 10, 1, 2, (38, 24, 28, 255))
    rect(4, 5, 2, 2, o + (255,))
    rect(10, 5, 2, 2, o + (255,))
    rect(2, 13, 12, 1, sh(p, 0.7))
    rr.write_png(f"{RP}/textures/items/sc_{rasid}.png", N, N, px)


def tryffelikon():
    """16x16 tryffel: en knotig svart klump med ljus ovansida och jord kvar."""
    N = 16
    px = [[(0, 0, 0, 0)] * N for _ in range(N)]

    def rect(x0, y0, w, h, c):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                if 0 <= x < N and 0 <= y < N:
                    px[y][x] = c
    kropp, ljus, jord = (52, 40, 34), (96, 78, 66), (110, 84, 56)
    rect(4, 5, 8, 8, kropp + (255,))
    rect(3, 7, 10, 4, kropp + (255,))       # bredare på mitten: knölig, inte kubisk
    rect(5, 4, 6, 2, kropp + (255,))
    rect(5, 5, 4, 2, ljus + (255,))         # dagerfläck uppe till vänster
    rect(9, 10, 2, 2, ljus + (255,))
    rect(4, 12, 3, 1, jord + (255,))        # jord kvar undertill
    rect(9, 12, 2, 1, jord + (255,))
    rr.write_png(f"{RP}/textures/items/sc_tryffel.png", N, N, px)


# --- entiteterna -------------------------------------------------------------
def entitet(rasid, skala, nos, fart, liv):
    """Beteendedefinitionen. Allt som går att uttrycka i JSON bor här; bara
    bökandet och vittringen kräver skript.

    RIDNINGEN ÄR VANILLA. minecraft:rideable plus behavior.controlled_by_player
    ger full WASD-styrning som en häst — inte morot-på-pinne-styrningen som
    vanilla-grisen har, och som är hela anledningen till att ingen rider gris."""
    ident = f"{NS}:{rasid}"
    return {
        "format_version": "1.20.50",
        "minecraft:entity": {
            "description": {
                "identifier": ident,
                "is_spawnable": True, "is_summonable": True, "is_experimental": False,
                "properties": {
                    f"{NS}:tam": {"type": "int", "range": [0, 1], "default": 0,
                                  "client_sync": True},
                    f"{NS}:lage": {"type": "int", "range": [0, 2], "default": 0,
                                   "client_sync": True},
                    f"{NS}:sadlad": {"type": "int", "range": [0, 1], "default": 0,
                                     "client_sync": True},
                    f"{NS}:vaskor": {"type": "int", "range": [0, 1], "default": 0,
                                     "client_sync": True},
                    f"{NS}:bar": {"type": "int", "range": [0, 1], "default": 0,
                                  "client_sync": True},
                    # lerig: syns som ett lager på ryggen. client_sync krävs —
                    # renderarkontrollern körs på KLIENTEN och kan inte läsa en
                    # egenskap servern inte skickar.
                    f"{NS}:lerig": {"type": "int", "range": [0, 1], "default": 0,
                                    "client_sync": True},
                },
            },
            "components": {
                "minecraft:type_family": {"family": ["sc_gris", "mob"]},
                "minecraft:health": {"value": liv, "max": liv},
                # TRÄFFYTAN FÖLJER STORLEKEN. Den var 0,9 för alla fem trots skala
                # 0,85-1,1, så en kunekune var lika bred att gå in i som en
                # lantras. minecraft:scale skalar MODELLEN, inte kollisionslådan
                # — samma fel fanns i hund- och kattpaketet och rättades där i
                # augusti; grisarna var de sista kvar.
                "minecraft:collision_box": {"width": round(0.9 * skala, 2),
                                            "height": round(0.9 * skala, 2)},
                "minecraft:physics": {},
                "minecraft:pushable": {"is_pushable": True},
                "minecraft:movement": {"value": fart},
                "minecraft:movement.basic": {},
                "minecraft:jump.static": {},
                "minecraft:navigation.walk": {"can_path_over_water": True,
                                              "avoid_water": True},
                "minecraft:nameable": {},
                "minecraft:behavior.float": {"priority": 0},
                "minecraft:behavior.panic": {"priority": 2, "speed_multiplier": 1.4},
                "minecraft:behavior.look_at_player": {"priority": 10, "look_distance": 8},
                "minecraft:behavior.random_look_around": {"priority": 11},
                "minecraft:behavior.random_stroll": {"priority": 12, "speed_multiplier": 0.8},
                "minecraft:ambient_sound_interval": {"value": 20.0, "range": 30.0,
                                                     "event_name": "ambient"},
                "minecraft:tameable": {
                    "probability": 0.4, "tame_items": TAMFODER,
                    "tame_event": {"event": f"{NS}:on_tame", "target": "self"}},
            },
            "component_groups": {
                f"{NS}:tamed": {
                    "minecraft:is_tamed": {},
                    "minecraft:persistent": {},
                    "minecraft:healable": {
                        "force_use": True,
                        "items": [{"item": "carrot", "heal_amount": 3},
                                  {"item": "potato", "heal_amount": 2},
                                  {"item": "beetroot", "heal_amount": 2},
                                  {"item": f"{NS}:tryffel", "heal_amount": 6}]},
                    "minecraft:interact": {"interactions": [
                        # SADELN FÖRST. Interaktionerna prövas uppifrån och ner,
                        # och kommandobytet måste ligga EFTER sadeln — annars
                        # byter en sadel i handen läge i stället för att sadla.
                        {"on_interact": {"filters": {"all_of": [
                            {"test": "is_family", "subject": "other", "value": "player"},
                            {"test": "is_owner", "subject": "other"},
                            {"test": "has_equipment", "domain": "hand",
                             "subject": "other", "value": "saddle"},
                            {"test": "int_property", "domain": f"{NS}:sadlad", "value": 0}]},
                            "event": f"{NS}:sadla", "target": "self"},
                         "use_item": True, "play_sounds": "saddle",
                         "interact_text": "action.interact.saddle"},
                        {"on_interact": {"filters": {"all_of": [
                            {"test": "is_family", "subject": "other", "value": "player"},
                            {"test": "is_owner", "subject": "other"},
                            {"test": "has_equipment", "domain": "hand",
                             "subject": "other", "value": "chest"},
                            {"test": "int_property", "domain": f"{NS}:vaskor", "value": 0}]},
                            "event": f"{NS}:vaskor_pa", "target": "self"},
                         "use_item": True, "play_sounds": "armor.equip_leather",
                         "interact_text": "action.interact.saddlebags"},
                        {"on_interact": {"filters": {"all_of": [
                            {"test": "is_family", "subject": "other", "value": "player"},
                            {"test": "is_owner", "subject": "other"},
                            {"test": "has_equipment", "domain": "hand",
                             "subject": "other", "value": "stick"}]},
                            "event": f"{NS}:nasta_lage", "target": "self"},
                         "play_sounds": "beacon.power",
                         "interact_text": "action.interact.command"}]},
                },
                # LÄGENA. Följer, bökar, stannar. Grupperna innehåller BARA de
                # beteenden som skiljer dem åt; random_stroll ligger i
                # baskomponenterna, annars står en gris i bökläge helt stilla.
                f"{NS}:foljer": {
                    "minecraft:behavior.follow_owner": {
                        "priority": 6, "speed_multiplier": 1.15,
                        "start_distance": 8, "stop_distance": 2}},
                f"{NS}:bokar": {
                    # Bökläget håller sig NÄRA ägaren men strosar fritt. Utan
                    # den bortre gränsen vandrar grisen iväg och bökar upp
                    # tryfflar i en annan dalgång.
                    "minecraft:behavior.follow_owner": {
                        "priority": 7, "speed_multiplier": 1.0,
                        "start_distance": 16, "stop_distance": 8}},
                f"{NS}:stannar": {},
                f"{NS}:sadlad": {
                    "minecraft:rideable": {
                        "seat_count": 1, "family_types": ["player"],
                        "interact_text": "action.interact.ride",
                        "seats": {"position": [0, 0.9, -0.2]}},
                    # STYRNINGEN. Utan den här går grisen dit den själv vill
                    # med en spelare på ryggen, precis som vanilla-grisen utan
                    # morot — och det är just det paketet finns för att slippa.
                    # UTAN PRIORITET, precis som vaniljas pig_saddled. En etta
                    # eller nolla här krockar med behavior.float, och två mål med
                    # samma prioritet är odefinierat i Bedrock.
                    "minecraft:behavior.controlled_by_player": {},
                    "minecraft:input_ground_controlled": {},
                },
                f"{NS}:vaskor": {
                    "minecraft:inventory": {"container_type": "horse",
                                            "inventory_size": 15,
                                            "can_be_siphoned_from": False},
                },
                f"{NS}:vuxen": {"minecraft:scale": {"value": skala}},
                f"{NS}:kulting": {
                    "minecraft:scale": {"value": skala * 0.5},
                    "minecraft:is_baby": {},
                    "minecraft:ageable": {
                        "duration": 1200,
                        "grow_up": {"event": f"{NS}:vuxen_nu", "target": "self"},
                        "feed_items": AVELSFODER + TAMFODER}},
                f"{NS}:parar": {
                    "minecraft:breedable": {
                        "require_tame": True, "require_full_health": True,
                        "breeds_with": [{"mate_type": ident, "baby_type": ident,
                                         "breed_event": {"event": f"{NS}:fodd",
                                                         "target": "baby"}}],
                        "love_filters": {"test": "has_component", "subject": "self",
                                         "operator": "!=", "value": "minecraft:is_baby"},
                        "breed_items": AVELSFODER},
                    "minecraft:behavior.breed": {"priority": 4, "speed_multiplier": 1.0}},
            },
            "events": {
                f"{NS}:on_tame": {
                    "add": {"component_groups": [f"{NS}:tamed", f"{NS}:foljer",
                                                 f"{NS}:parar"]},
                    "set_property": {f"{NS}:tam": 1}},
                # LÄGESBYTET är en sekvens som prövas uppifrån och ner, så det
                # HÖGSTA värdet måste stå först. Med 0 först föll bytet igenom
                # alla tre grenarna i samma anrop och läget stod stilla.
                f"{NS}:nasta_lage": {"sequence": [
                    {"filters": {"test": "int_property", "domain": f"{NS}:lage", "value": 2},
                     "set_property": {f"{NS}:lage": 0},
                     "add": {"component_groups": [f"{NS}:foljer"]},
                     "remove": {"component_groups": [f"{NS}:bokar", f"{NS}:stannar"]}},
                    {"filters": {"test": "int_property", "domain": f"{NS}:lage", "value": 1},
                     "set_property": {f"{NS}:lage": 2},
                     "add": {"component_groups": [f"{NS}:stannar"]},
                     "remove": {"component_groups": [f"{NS}:foljer", f"{NS}:bokar"]}},
                    {"filters": {"test": "int_property", "domain": f"{NS}:lage", "value": 0},
                     "set_property": {f"{NS}:lage": 1},
                     "add": {"component_groups": [f"{NS}:bokar"]},
                     "remove": {"component_groups": [f"{NS}:foljer", f"{NS}:stannar"]}}]},
                f"{NS}:sadla": {"add": {"component_groups": [f"{NS}:sadlad"]},
                                "set_property": {f"{NS}:sadlad": 1}},
                f"{NS}:vaskor_pa": {"add": {"component_groups": [f"{NS}:vaskor"]},
                                    "set_property": {f"{NS}:vaskor": 1}},
                f"{NS}:bar_pa": {"set_property": {f"{NS}:bar": 1}},
                f"{NS}:bar_av": {"set_property": {f"{NS}:bar": 0}},
                f"{NS}:lerig_pa": {"set_property": {f"{NS}:lerig": 1}},
                f"{NS}:lerig_av": {"set_property": {f"{NS}:lerig": 0}},
                # VUXENGRUPPEN läggs på vid spawn, men INTE på en kulting: både
                # den och kultinggruppen sätter minecraft:scale, och i
                # hundpaketet vann fel grupp så valparna blev fullstora. Därför
                # tar gris:fodd bort vuxengruppen explicit.
                "minecraft:entity_spawned": {
                    "add": {"component_groups": [f"{NS}:vuxen"]}},
                f"{NS}:fodd": {
                    "add": {"component_groups": [f"{NS}:kulting", f"{NS}:tamed",
                                                 f"{NS}:foljer"]},
                    "remove": {"component_groups": [f"{NS}:vuxen"]},
                    "set_property": {f"{NS}:tam": 1}},
                f"{NS}:vuxen_nu": {
                    "add": {"component_groups": [f"{NS}:vuxen", f"{NS}:parar"]},
                    "remove": {"component_groups": [f"{NS}:kulting"]}},
            },
        },
    }


def klient(rasid, kropp):
    return {
        "format_version": "1.10.0",
        "minecraft:client_entity": {"description": {
            "identifier": f"{NS}:{rasid}",
            "materials": {"default": "entity_alphatest"},
            "textures": {"default": f"textures/entity/{rasid}"},
            "geometry": {"default": f"geometry.gris_{kropp}"},
            "animations": {"walk": "animation.quadruped.walk",
                           "look_at_target": "animation.common.look_at_target"},
            "scripts": {"animate": [{"walk": "query.modified_move_speed"},
                                    "look_at_target"]},
            "render_controllers": ["controller.render.gris"],
            "spawn_egg": {"texture": f"sc_{rasid}", "texture_index": 0}}},
    }


def spawnregel(rasid, biom):
    """Grisarna spawnar SPARSAMT. Vanilla-grisen finns redan överallt; ett
    paket som lägger fem raser till med vanliga vikter gör världen till en
    svinstia. Vikten är därför en tredjedel av vanilla-grisens."""
    return {
        "format_version": "1.8.0",
        "minecraft:spawn_rules": {
            "description": {"identifier": f"{NS}:{rasid}",
                            "population_control": "animal"},
            "conditions": [{
                "minecraft:spawns_on_surface": {},
                "minecraft:brightness_filter": {"min": 7, "max": 15,
                                                "adjust_for_weather": False},
                "minecraft:weight": {"default": 3},
                "minecraft:herd": {"min_size": 2, "max_size": 3},
                "minecraft:biome_filter": {"test": "has_biome_tag", "operator": "==",
                                           "value": biom},
                "minecraft:height_filter": {"min": 60, "max": 200}}]},
    }


def tryffeln():
    """Tryffeln: det grisen bökar upp. Mat som mättar bra, och det bästa
    avelsfodret — belöningen och verktyget är samma sak, så det man hittar har
    en användning även när skafferiet är fullt."""
    return {
        "format_version": "1.20.50",
        "minecraft:item": {
            "description": {"identifier": f"{NS}:tryffel", "menu_category":
                            {"category": "nature"}},
            "components": {
                "minecraft:icon": {"texture": "sc_tryffel"},
                "minecraft:max_stack_size": 64,
                # saturation_modifier SOM SIFFRA. Vanilla skriver "normal" och
                # liknande namn i sina egna föremål, men ett eget föremål på
                # format_version 1.20.50 underkänner strängen: "Failed to parse
                # field saturation_modifier: invalid numeric value". Felet står
                # bara i ContentLog, och föremålet blir oätligt utan ett ord.
                "minecraft:food": {"nutrition": 4, "saturation_modifier": 0.6},
                "minecraft:use_modifiers": {"use_duration": 1.6,
                                            "movement_modifier": 0.35},
                "minecraft:use_animation": "eat"}},
    }


def ljud():
    """Ljuden lånas från vanilla-grisen. Egna ljudfiler kräver .ogg i paketet,
    och en gris som låter som en gris är viktigare än en gris som låter unik.
    TONHÖJDEN FÖLJER STORLEKEN: kultingen gnyr ljust, lantrasen grymtar mörkt."""
    ljud = {}
    for rasid, _n, _r, _k, skala, _b, _nos, _f, _l, _farg in RASER:
        # Stor gris = låg ton. Skalan 0,85–1,1 mappas till 1,15–0,85.
        p = round(2.0 - skala, 2)
        ljud[f"{NS}:{rasid}"] = {
            "volume": 0.9, "pitch": [round(p - 0.08, 2), round(p + 0.08, 2)],
            "events": {"ambient": "mob.pig.say", "hurt": "mob.pig.say",
                       "death": "mob.pig.death", "step": "mob.pig.step"}}
    return {"format_version": "1.10.0", "entity_sounds": {"entities": ljud}}


def skriv(sokvag, data):
    json.dump(data, open(sokvag, "w"), indent=2)


def main():
    delar, uv = skriv_geometrier()
    renderarkontroller()
    for rasid, _n, _r, kropp, skala, biom, nos, fart, liv, farg in RASER:
        pals(rasid, delar[kropp], uv[kropp], farg)
        ikon(rasid, farg, KROPPAR[kropp][6])
        skriv(f"{BP}/entities/{rasid}.json", entitet(rasid, skala, nos, fart, liv))
        skriv(f"{RP}/entity/{rasid}.json", klient(rasid, kropp))
        skriv(f"{BP}/spawn_rules/{rasid}.json", spawnregel(rasid, biom))
    tryffelikon()
    skriv(f"{BP}/items/tryffel.json", tryffeln())
    skriv(f"{RP}/sounds.json", ljud())
    skriv(f"{RP}/textures/item_texture.json", {
        "resource_pack_name": "snuffle", "texture_name": "atlas.items",
        "texture_data": {f"sc_{r[0]}": {"textures": f"textures/items/sc_{r[0]}"}
                         for r in RASER} |
                        {"sc_tryffel": {"textures": "textures/items/sc_tryffel"}}})
    for spr in SPRAK:
        rader = sprakrader(spr)
        for mapp in (BP, RP):
            open(f"{mapp}/texts/{spr}.lang", "w").write("\n".join(rader) + "\n")
            json.dump(list(SPRAK), open(f"{mapp}/texts/languages.json", "w"), indent=2)
    # NOSTABELLEN TILL SKRIPTET. Skriptet kan inte läsa entitets-JSON, och en
    # handskriven kopia av räckvidderna i main.js skulle glida isär från
    # RASER vid första rasjusteringen. Den skrivs därför ut härifrån.
    tabell = {f"{NS}:{r[0]}": {"nos": r[6]} for r in RASER}
    open(f"{BP}/scripts/raser.js", "w").write(
        "// GENERERAD AV tools/make_pigs.py — ändra i RASER, inte här.\n"
        "export const RASER = " + json.dumps(tabell, indent=2) + ";\n"
        "export const BOKBAR = " + json.dumps(BOKBAR, indent=2) + ";\n"
        "export const MALM = " + json.dumps([m[0] for m in MALM], indent=2) + ";\n")
    print(f"{len(RASER)} grisar, {len(KROPPAR)} kroppar, {len(MALM)} malmer")


if __name__ == "__main__":
    main()
