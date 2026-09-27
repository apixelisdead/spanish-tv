import urllib.request
import re
from pathlib import Path

SOURCE = "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlists/playlist_spain.m3u8"
OUTPUT = Path(__file__).with_name("Spanish-TV.m3u")

# These are tvg-id values, so the script keeps the exact current stream/metadata
# published by the upstream playlist instead of hard-coding stream URLs.
WANTED = [
    "La1.es","La2.es","Antena3.es","Cuatro.es","Telecinco.es","LaSexta.es",
    "24h.es","tdp.es","clan.es","TVEInternacionalEuropeAsia.es",
    "Neox.es","Nova.es","Atreseries.es","Mega.es","FactoriadeFiccion.es",
    "Divinity.es","Energy.es","BeMad.es","Boing.es","ParamountNetwork.es",
    "Euronews.es","ElPaisTV.es",
    "Telemadrid.es","CanalSurAndalucia.es","TV3CAT.es","AragonTV.es",
    "ETB1.es","ETB2.es","APunt.es","CanalExtremadura.es"
]

data = urllib.request.urlopen(SOURCE, timeout=20).read().decode("utf-8")
lines = [x.strip() for x in data.splitlines() if x.strip()]

result = [lines[0]]
wanted_set = set(WANTED)
found = set()

for i, line in enumerate(lines):
    if not line.startswith("#EXTINF:"):
        continue
    m = re.search(r'tvg-id="([^"]+)"', line)
    if not m or m.group(1) not in wanted_set:
        continue
    if i + 1 >= len(lines) or lines[i + 1].startswith("#"):
        continue
    tvgid = m.group(1)
    if tvgid in found:
        continue
    result.extend([line, lines[i + 1]])
    found.add(tvgid)

missing = [x for x in WANTED if x not in found]
if missing:
    print("Warning: not found:", ", ".join(missing))

OUTPUT.write_text("\n".join(result) + "\n", encoding="utf-8")
print(f"Created {OUTPUT} with {len(found)} channels.")
