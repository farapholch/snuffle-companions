#!/bin/bash
# Publicerar sajten (snuffle.pelleops.se, nginx :8094).
#
# SAJTEN ERBJUDER INGEN NEDLADDNING. Paketet ska hämtas i butiken, inte härifrån
# — därför bygger det här skriptet inget .mcaddon och kopierar inget. Leveransen
# sköts av tools/snuffle-ship.
#
# Sidorna bor i site/, bilderna genereras av tools/make_promo.py,
# tools/make_logo.py och tools/render_pigs.py.
set -e
SRC=/opt/snuffle-companions
DEST=/var/www/snuffle
VERSION=$(python3 -c "import json;print('.'.join(map(str,json.load(open('$SRC/SnuffleCompanions_BP/manifest.json'))['header']['version'])))")

mkdir -p "$DEST"

# SIDORNA SPEGLAS, inte bara kopieras. Tas en sida bort ur site/ ligger den
# annars kvar publikt för alltid — en död sida som ingen länkar till men som
# gamla länkar och sökmotorer hittar.
for GAMMAL in "$DEST"/*.html; do
  [ -e "$GAMMAL" ] || continue
  [ -f "$SRC/site/$(basename "$GAMMAL")" ] || { echo "   tar bort $(basename "$GAMMAL")"; rm -f "$GAMMAL"; }
done
cp "$SRC"/site/*.html "$DEST/"

# BARA BILDERNA SIDAN ANVÄNDER. publish/ innehåller också butiksbilder och
# enstaka felsökningsrenderingar, och de har inget på en publik sajt att göra.
for BILD in logo.png hero.png pigs.png favicon.png apple-touch-icon.png pack_icon.png; do
  cp "$SRC/publish/$BILD" "$DEST/"
done

# INGEN .mcaddon PÅ SAJTEN. Ligger det en kvar sedan tidigare tas den bort — en
# gammal fil som fortfarande går att hämta är värre än ingen fil alls.
find "$DEST" -maxdepth 1 -name "*.mcaddon" -printf "   tar bort %f\n" -delete

# NEDLADDNINGSKNAPPEN. Den publika CurseForge-adressen går inte att härleda:
# nya projekt måste godkännas innan sidan finns, och sluggen är inte
# projektnamnet — hundpaketets blev "loyal-companions-dogs". Ligger sluggen i
# .curseforge-slug blir det en riktig knapp, annars står rutan kvar som säger att
# filen väntar på godkännande. Att lägga in länken är alltså
#   echo <slug> > .curseforge-slug && ./publish_site.sh
# i stället för en handredigering i HTML, som det blev för hundpaketet.
SLUGFIL="$SRC/.curseforge-slug"
if [ -s "$SLUGFIL" ]; then
  SLUG=$(tr -d '[:space:]' < "$SLUGFIL")
  NED="<a class=\"cta\" href=\"https://www.curseforge.com/minecraft-bedrock/addons/$SLUG\">Get it on CurseForge</a>
<p class=\"cap\">Version __VERSION__ — free. Open the .mcaddon and Minecraft installs it.</p>"
  echo "   nedladdningsknapp: $SLUG"
else
  NED="<div class=\"soon\">
<p class=\"soonhead\">Version __VERSION__ is finished and tested</p>
<p class=\"cap\">It is waiting to be approved on CurseForge. Nothing to download here yet.</p>
</div>"
  echo "   ingen .curseforge-slug än — rutan står kvar"
fi
NED="$NED" python3 - "$DEST/index.html" <<'PYNED'
import os, sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
assert "__NEDLADDNING__" in s, "platshållaren __NEDLADDNING__ saknas i sidan"
open(p, "w", encoding="utf-8").write(s.replace("__NEDLADDNING__", os.environ["NED"]))
PYNED

# Versionsnumret på sidan hängde kvar i fem releaser i kattprojektet när det
# redigerades för hand — sidan bär en platshållare i stället, som fylls i här.
sed -i "s/__VERSION__/$VERSION/g" "$DEST/index.html"

# CACHEN. Cloudflare håller bilder i fyra timmar och vi har ingen token att rensa
# med, så en ny hjältebild syns inte förrän TTL:en löpt ut. Versionsstämpla
# länkarna i stället: samma fil, ny URL vid varje release.
sed -i -E "s/(src=\"[^\"]+\.png)\"/\1?v=$VERSION\"/g" "$DEST/index.html"

chmod 644 "$DEST"/* 2>/dev/null || true
echo "publicerat v$VERSION till $DEST (https://snuffle.pelleops.se)"
