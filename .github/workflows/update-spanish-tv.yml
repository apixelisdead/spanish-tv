import re
import unicodedata
import urllib.request
from pathlib import Path

# Source 1: Dearbulut "Best" playlist.
# It contains one best-ranked stream per channel and is refreshed from
# Dearbulut's health-checked dataset.
DEARBULUT = "https://dearbulut.github.io/iptv/playlists/best.m3u"

# Source 2: IPTVspain public TDT playlist.
# Used as a fallback when Dearbulut does not currently have the channel.
IPTVSPAIN = "https://raw.githubusercontent.com/vk496/IPTVspain/master/spain.m3u8"

EPG = "https://dearbulut.github.io/iptv/epg/es.xml.gz"
OUTPUT = Path(__file__).with_name("Spanish-TV.m3u")

CHANNELS = [
    ("La 1", ["La1.es"], ["La 1", "LA 1"]),
    ("La 2", ["La2.es"], ["La 2", "LA 2"]),
    ("Antena 3", ["Antena3.es"], ["Antena 3", "ANTENA 3"]),
    ("Cuatro", ["Cuatro.es"], ["Cuatro", "CUATRO"]),
    ("Telecinco", ["Telecinco.es"], ["Telecinco", "TELECINCO"]),
    ("La Sexta", ["LaSexta.es"], ["La Sexta", "LA SEXTA"]),
    ("24 Horas", ["24Horas.es", "24h.es"], ["24 Horas", "24h", "CANAL 24 HORAS"]),
    ("Teledeporte", ["Teledeporte.es", "tdp.es"], ["Teledeporte", "tdp", "TDP"]),
    ("Clan", ["Clan.es", "clan.es"], ["Clan", "CLAN"]),
    ("TVE Internacional", ["TVEInternacionalEuropeAsia.es"], [
        "TVE Internacional", "TVE Internacional Europe-Asia",
        "TVE Internacional Europa-Asia"
    ]),
    ("Neox", ["Neox.es"], ["Neox", "NEOX"]),
    ("Nova", ["Nova.es"], ["Nova", "NOVA"]),
    ("Atreseries", ["Atreseries.es"], ["Atreseries", "ATRESERIES"]),
    ("Mega", ["Mega.es"], ["Mega", "MEGA"]),
    ("FDF", ["FactoriadeFiccion.es"], ["FDF", "Factoría de Ficción", "Factoria de Ficcion"]),
    ("Divinity", ["Divinity.es"], ["Divinity", "DIVINITY"]),
    ("Energy", ["Energy.es"], ["Energy", "ENERGY"]),
    ("Be Mad", ["BeMad.es"], ["Be Mad", "BE MAD", "BEMAD"]),
    ("Boing", ["Boing.es"], ["Boing", "BOING"]),
    ("Squirrel 2", ["Squirrel2.es", "ParamountNetwork.es"], ["Squirrel 2", "Squirrel2", "Paramount Network", "Paramount Channel"]),
    ("Euronews", ["Euronews.es"], ["Euronews", "euronews"]),
    ("El País", ["ElPaisTV.es"], ["El País", "El Pais", "El País TV"]),
    ("Telemadrid", ["Telemadrid.es"], ["Telemadrid"]),
    ("Canal Sur Andalucía", ["CanalSurAndalucia.es"], ["Canal Sur Andalucía", "Canal Sur"]),
    ("TV3Cat", ["TV3CAT.es"], ["TV3Cat", "TV3 CAT", "TV3"]),
    ("Aragón TV", ["AragonTV.es"], ["Aragón TV", "Aragon TV"]),
    ("ETB1", ["ETB1.es"], ["ETB1"]),
    ("ETB2", ["ETB2.es"], ["ETB2"]),
    ("À Punt TV", ["APunt.es"], ["À Punt TV", "A Punt TV", "À Punt", "A Punt"]),
    ("Canal Extremadura", ["CanalExtremadura.es", "CanalExtremaduraSatelite.es"], [
        "Canal Extremadura", "Canal Extremadura Satélite", "Canal Extremadura Sat"
    ]),
]

def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.lower().strip()
    value = re.sub(r"[\(\)\[\]\{\}]", " ", value)
    value = re.sub(r"\b(hd|fhd|uhd|4k|sd|hevc|satellite|satelite)\b", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()

id_to_canonical = {}
name_to_canonical = {}

for canonical, ids, names in CHANNELS:
    for channel_id in ids:
        id_to_canonical[channel_id.lower()] = canonical
    for name in names:
        name_to_canonical[norm(name)] = canonical

def download(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Spanish-TV-playlist-updater/2.0"}
    )
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8-sig")

def parse_m3u(data):
    lines = [x.strip() for x in data.splitlines() if x.strip()]
    found = {}

    for i, line in enumerate(lines):
        if not line.startswith("#EXTINF:") or i + 1 >= len(lines):
            continue

        url = lines[i + 1]
        if not url or url.startswith("#"):
            continue

        tvg_id = re.search(r'tvg-id="([^"]+)"', line)
        tvg_name = re.search(r'tvg-name="([^"]+)"', line)
        display_name = line.split(",", 1)[1] if "," in line else ""

        canonical = None

        # First use exact tvg-id because that's the most reliable identifier.
        if tvg_id:
            canonical = id_to_canonical.get(tvg_id.group(1).strip().lower())

        # Then fall back to normalized names.
        if canonical is None:
            for candidate in (
                tvg_name.group(1) if tvg_name else "",
                display_name,
            ):
                n = norm(candidate)
                if n in name_to_canonical:
                    canonical = name_to_canonical[n]
                    break

        if canonical and canonical not in found:
            found[canonical] = (line, url)

    return found

all_sources = [
    ("Dearbulut best", DEARBULUT),
    ("IPTVspain", IPTVSPAIN),
]

matches = {}
source_used = {}

for source_name, source_url in all_sources:
    print(f"Downloading {source_name}: {source_url}")
    data = download(source_url)
    source_matches = parse_m3u(data)

    print(f"  matched {len(source_matches)} requested channels")

    for canonical, entry in source_matches.items():
        # Dearbulut gets priority because its playlist is health-ranked.
        if canonical not in matches:
            matches[canonical] = entry
            source_used[canonical] = source_name

missing = [canonical for canonical, _ids, _names in CHANNELS if canonical not in matches]

print()
print(f"Total available across both sources: {len(matches)}/{len(CHANNELS)}")
for canonical, _, _ in CHANNELS:
    if canonical in matches:
        print(f"  OK   {canonical:<24} [{source_used[canonical]}]")
    else:
        print(f"  MISS {canonical}")

# Do not destroy a good playlist because an upstream source had a temporary
# outage. Require at least 20 of our 30 channels.
if len(matches) < 20:
    raise RuntimeError(
        f"Only {len(matches)} channels were found across both sources; "
        "refusing to replace the existing playlist."
    )

out = [f'#EXTM3U x-tvg-url="{EPG}"']

for number, (canonical, _, _) in enumerate(CHANNELS, start=1):
    if canonical not in matches:
        continue

    extinf, url = matches[canonical]

    # Rewrite only the parts we control; retain logo/tvg-id/group metadata.
    prefix = extinf.split(",", 1)[0]
    prefix = re.sub(r'\s+tvg-chno="[^"]*"', "", prefix)
    prefix = re.sub(r'\s+tvg-name="[^"]*"', "", prefix)
    display = canonical

    extinf = f'{prefix} tvg-chno="{number}" tvg-name="{canonical}",{display}'
    out.extend([extinf, url])

OUTPUT.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"\nWrote {OUTPUT} with {len(matches)} channels.")
