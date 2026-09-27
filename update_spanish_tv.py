import re
import unicodedata
import urllib.request
from pathlib import Path

SOURCE = "https://dearbulut.github.io/iptv/playlists/country/es.m3u"
EPG = "https://dearbulut.github.io/iptv/epg/es.xml.gz"
OUTPUT = Path(__file__).with_name("Spanish-TV.m3u")

# Keep the same curated 30-channel lineup, in the order we want
# CH+/CH- to move through the channels.
CHANNELS = [
    ("La 1", ["La 1", "La 1 (HD)"]),
    ("La 2", ["La 2", "La 2 (HD)"]),
    ("Antena 3", ["Antena 3", "Antena 3 (HD)"]),
    ("Cuatro", ["Cuatro", "Cuatro (HD)"]),
    ("Telecinco", ["Telecinco", "Telecinco (HD)"]),
    ("La Sexta", ["La Sexta", "La Sexta (HD)"]),
    ("24h", ["24h", "24 Horas", "24 Horas (HD)"]),
    ("Teledeporte", ["Teledeporte", "tdp", "Teledeporte (HD)"]),
    ("Clan", ["Clan", "Clan TVE"]),
    ("TVE Internacional", [
        "TVE Internacional",
        "TVE Internacional Europe-Asia",
        "TVE Internacional Europa-Asia",
    ]),
    ("Neox", ["Neox"]),
    ("Nova", ["Nova"]),
    ("Atreseries", ["Atreseries"]),
    ("Mega", ["Mega"]),
    ("FDF", ["FDF", "Factoría de Ficción"]),
    ("Divinity", ["Divinity"]),
    ("Energy", ["Energy"]),
    ("Be Mad", ["Be Mad", "BEMAD"]),
    ("Boing", ["Boing"]),
    ("Paramount Network", ["Paramount Network", "Paramount Channel"]),
    ("Euronews", ["Euronews", "euronews"]),
    ("El País", ["El País", "El Pais"]),
    ("Telemadrid", ["Telemadrid"]),
    ("Canal Sur Andalucía", ["Canal Sur Andalucía", "Canal Sur"]),
    ("TV3Cat", ["TV3Cat", "TV3", "TV3 CAT"]),
    ("Aragón TV", ["Aragón TV", "Aragon TV"]),
    ("ETB1", ["ETB1"]),
    ("ETB2", ["ETB2"]),
    ("À Punt TV", ["À Punt TV", "A Punt TV", "À Punt"]),
    ("Canal Extremadura", ["Canal Extremadura"]),
]

def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.lower().strip()
    value = re.sub(r"[\u24b6-\u24e9]", "", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\b(fallback|hd|fhd|uhd|4k)\b", " ", value)
    return re.sub(r"\s+", " ", value).strip()

wanted = {}
for canonical, aliases in CHANNELS:
    for alias in aliases:
        wanted.setdefault(norm(alias), canonical)

request = urllib.request.Request(
    SOURCE,
    headers={"User-Agent": "Spanish-TV-playlist-updater/1.0"}
)
data = urllib.request.urlopen(request, timeout=30).read().decode("utf-8-sig")
lines = [x.strip() for x in data.splitlines() if x.strip()]

matches = {}
for i, line in enumerate(lines):
    if not line.startswith("#EXTINF:") or i + 1 >= len(lines):
        continue

    url = lines[i + 1]
    if not url or url.startswith("#"):
        continue

    m_name = re.search(r'tvg-name="([^"]*)"', line)
    tvg_name = m_name.group(1) if m_name else ""
    display_name = line.split(",", 1)[1] if "," in line else ""

    candidates = [tvg_name, display_name]
    canonical = None
    for candidate in candidates:
        n = norm(candidate)
        if n in wanted:
            canonical = wanted[n]
            break

    if canonical and canonical not in matches:
        matches[canonical] = (line, url)

missing = [canonical for canonical, _ in CHANNELS if canonical not in matches]

print(f"Source: {SOURCE}")
print(f"Found {len(matches)} of {len(CHANNELS)} requested channels.")
if missing:
    print("Missing:", ", ".join(missing))

# Refuse to overwrite the working playlist if the upstream source changes
# unexpectedly and fewer than 25 of our requested channels are available.
if len(matches) < 25:
    raise RuntimeError(
        f"Only {len(matches)} channels matched; refusing to replace playlist."
    )

out = [f'#EXTM3U x-tvg-url="{EPG}"']

for number, (canonical, _) in enumerate(CHANNELS, start=1):
    if canonical not in matches:
        continue

    extinf, url = matches[canonical]

    # Preserve the upstream tvg-id/logo/group metadata, but give our
    # curated playlist a predictable 1..30 channel order.
    extinf = re.sub(r'\s+tvg-chno="[^"]*"', "", extinf)
    extinf = re.sub(r'\s+tvg-name="[^"]*"', "", extinf)

    if "," in extinf:
        prefix = extinf.split(",", 1)[0]
        extinf = f'{prefix} tvg-name="{canonical}",{canonical}'
    else:
        extinf = f'{extinf},${canonical}'

    if "," in extinf:
        prefix = extinf.split(",", 1)[0]
        extinf = f'{prefix} tvg-chno="{number}",{canonical}'
    else:
        extinf = f'{extinf} tvg-chno="{number}",{canonical}'

    out.extend([extinf, url])

OUTPUT.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"Wrote {OUTPUT} with {len(matches)} channels.")
