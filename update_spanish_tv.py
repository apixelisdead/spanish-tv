import re
import urllib.request
import urllib.parse
import unicodedata
from pathlib import Path

OUTPUT = Path(__file__).with_name("Spanish-TV.m3u")

# Sources are deliberately ordered:
# 1) Official links collected by TDTChannels (they document that their M3U8
#    entries are official playback links).
# 2) Dearbulut's Spain playlist / health-checked data.
# We no longer use the old IPTVspain archive.
OFFICIAL_SOURCE = "https://www.tdtchannels.com/lists/tv.m3u8"
HEALTHY_ES_SOURCE = "https://dearbulut.github.io/iptv/playlists/country/es.m3u"
HEALTHY_ALL_SOURCE = "https://dearbulut.github.io/iptv/playlists/online.m3u"

# Dearbulut's XMLTV IDs match its tvg-id / Nexus IDs and are a useful
# cross-source guide for this curated playlist.
EPG = "https://dearbulut.github.io/iptv/epg/es.xml.gz"

# These are the 30 primary channels we want.  Some commercial channels may
# not have a stable public official M3U8, so the script can replace them with
# backup Spanish public/free channels when no working stream is available.
PRIMARY = [
    "La 1", "La 2", "Antena 3", "Cuatro", "Telecinco", "La Sexta",
    "24 Horas", "Teledeporte", "Clan", "TVE Internacional",
    "Neox", "Nova", "Atreseries", "Mega", "FDF",
    "Divinity", "Energy", "Be Mad", "Boing", "Squirrel 2",
    "Euronews", "El País", "Telemadrid", "Canal Sur Andalucía",
    "TV3Cat", "Aragón TV", "ETB1", "ETB2", "À Punt TV",
    "Canal Extremadura",
]

# Public/free replacements that TDTChannels maintains with official M3U8
# links. They are only used if one of PRIMARY cannot be populated.
BACKUPS = [
    "3/24",
    "Esport3",
    "TVG Europa",
    "TPA7",
    "TV Canaria",
    "La Otra",
    "TRECE",
    "Real Madrid TV",
    "Squirrel",
    "betevé",
    "24h Catalunya",
    "La 2 Cat",
    "Canal Sur 2 Accesible",
    "SX3",
    "7 TeleValencia",
    "La 8 Mediterráneo",
    "TVG Mira Radio Galega",
    "TVG Universo Castelao",
    "Distrito TV",
    "El Toro TV",
]

ALIASES = {
    "La 1": ["La 1", "La1"],
    "La 2": ["La 2", "La2"],
    "Antena 3": ["Antena 3", "Antena3", "A3"],
    "Cuatro": ["Cuatro"],
    "Telecinco": ["Telecinco"],
    "La Sexta": ["La Sexta", "LaSexta"],
    "24 Horas": ["24 Horas", "24h", "Canal 24 Horas", "24 H"],
    "Teledeporte": ["Teledeporte", "TDP"],
    "Clan": ["Clan"],
    "TVE Internacional": [
        "TVE Internacional", "TVE Int. Europa", "TVE Internacional Europe-Asia",
        "TVE Internacional Europa-Asia", "TVE Int Europa"
    ],
    "Neox": ["Neox"],
    "Nova": ["Nova"],
    "Atreseries": ["Atreseries"],
    "Mega": ["Mega"],
    "FDF": ["FDF", "Factoría de Ficción", "Factoria de Ficcion"],
    "Divinity": ["Divinity"],
    "Energy": ["Energy"],
    "Be Mad": ["Be Mad", "BEMAD"],
    "Boing": ["Boing"],
    "Squirrel 2": ["Squirrel 2", "Squirrel2", "Squirrel Dos"],
    "Euronews": ["Euronews", "euronews"],
    "El País": ["El País", "El Pais", "El País TV", "El Pais TV"],
    "Telemadrid": ["Telemadrid"],
    "Canal Sur Andalucía": ["Canal Sur Andalucía", "Canal Sur"],
    "TV3Cat": ["TV3Cat", "TV3 CAT", "TV3"],
    "Aragón TV": ["Aragón TV", "Aragon TV"],
    "ETB1": ["ETB1"],
    "ETB2": ["ETB2"],
    "À Punt TV": ["À Punt TV", "A Punt TV", "À Punt", "A Punt"],
    "Canal Extremadura": [
        "Canal Extremadura", "Canal Extremadura Satélite", "Canal Extremadura Sat"
    ],
    "3/24": ["3/24", "324"],
    "Esport3": ["Esport3"],
    "TVG Europa": ["TVG Europa"],
    "TPA7": ["TPA7", "TPA", "TPA 7"],
    "TV Canaria": ["TV Canaria", "Televisión Canaria"],
    "La Otra": ["La Otra", "LaOtra"],
    "TRECE": ["TRECE", "13 TV", "13TV"],
    "Real Madrid TV": ["Real Madrid TV", "Real Madrid TV Español", "RMTV"],
    "Squirrel": ["Squirrel"],
    "betevé": ["betevé", "Beteve"],
    "24h Catalunya": ["24h Catalunya", "24 Horas Catalunya", "24 H Catalunya"],
    "La 2 Cat": ["La 2 Cat", "La 2 Catalunya"],
    "Canal Sur 2 Accesible": ["Canal Sur 2 Accesible", "Canal Sur 2"],
    "SX3": ["SX3"],
    "7 TeleValencia": ["7 TeleValencia", "7TV"],
    "La 8 Mediterráneo": ["La 8 Mediterráneo", "La 8 Mediterraneo"],
    "TVG Mira Radio Galega": ["TVG Mira Radio Galega"],
    "TVG Universo Castelao": ["TVG Universo Castelao"],
    "Distrito TV": ["Distrito TV", "DistritoTV"],
    "El Toro TV": ["El Toro TV"],
}

# Direct streams that the user has personally confirmed as working in VLC.
# They are preferred over dynamically discovered alternatives because that is
# stronger evidence for this particular UK setup than a remote health check.
KNOWN_GOOD = {
    "La 1": (
        "La1.es",
        "https://rtvelivestream.rtve.es/rtvesec/la1/la1_main_dvr.m3u8",
    ),
    "La 2": (
        "La2.es",
        "https://rtvelivestream.rtve.es/rtvesec/la2/la2_main.m3u8",
    ),
    "24 Horas": (
        "24h.es",
        "https://rtvelivestream.rtve.es/rtvesec/24h/24h_main_dvr.m3u8",
    ),
    "Teledeporte": (
        "Teledeporte.es",
        "https://rtve01p.origin.c21livecloud.com/live-origin/tdp-hls/bitrate_1.m3u8",
    ),
    "Clan": (
        "Clan.es",
        "https://lge-lgla2.otteravision.com/lge/lgcla/lgcla.m3u8",
    ),
    "TVE Internacional": (
        "TVEInternacionalEuropeAsia.es",
        "https://rtvelivestream-rtveplayplus.rtve.es/rtvesec/int/tvei_eu_main_1080.m3u8",
    ),
    "Squirrel 2": (
        "Squirrel2.es",
        "http://4.30.180.36:8420/paramount/index.m3u8?token=test",
    ),
    "Euronews": (
        "Euronews.es",
        "https://euronews-live-spa-es.fast.rakuten.tv/v1/master/0547f18649bd788bec7b67b746e47670f558b6b2/production-LiveChannel-6571/bitok/eyJzdGlkIjoiMDA0YjY0NTMtYjY2MC00ZTZkLTlkNzEtMTk3YTM3ZDZhZWIxIiwibWt0IjoiZXMiLCJjaCI6NjU3MSwicHRmIjoxfQ==/26034/euronews-es.m3u8",
    ),
    "El País": (
        "ElPaisTV.es",
        "https://d2epgk1fomaa1g.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-9n8y4tw0bk3an/live/fast-channel-el-pais/fast-channel-el-pais.m3u8",
    ),
    "Canal Sur Andalucía": (
        "CanalSurAndalucia.es",
        "https://d4oe4cnrgi9c9.cloudfront.net/master.m3u8",
    ),
    "TV3Cat": (
        "TV3CAT.es",
        "https://directes3-tv-int.3catdirectes.cat/live-content/tvi-hls/master.m3u8",
    ),
    "ETB1": (
        "ETB1.es",
        "https://cdn1.etbon.eus/etb1/index.m3u8",
    ),
    "ETB2": (
        "ETB2.es",
        "https://cdn1.etbon.eus/etb2/index.m3u8",
    ),
    "À Punt TV": (
        "APunt.es",
        "https://fastly.live.brightcove.com/1846756479408303045/eu-central-1/6057955885001/eyJhbGciOiJIUzI1NiJ9.eyJob3N0IjoiZWFxNWh4LmVncmVzcy53YzQ3bTEiLCJpc3MiOiJibGl2ZS1wbGF5YmFjay1zb3VyY2UtYXBpIiwic3ViIjoicGF0aG1hcHRva2VuIiwiYXVkIjpbIjYwNTc5NTU4ODUwMDEiXSwianRpIjoiMTg0Njc1NjQ3OTQwODMwNDUifQ.o6wb_VA-TVxl3ERgr7FKLlaTjY7smErmsf73QAydySE/playlist-hls-dvr.m3u8",
    ),
    "Canal Extremadura": (
        "CanalExtremadura.es",
        "https://d2ymuyhevki1a491-a491.cloudfront.net/wct-ddd2992e-86fc-4611-a491-7f392259e9ba/continuous/9be76611-d2cd-474d-bf19-ef702ba31b02/index.m3u8",
    ),
}

# Exact streams the user already tested and found unusable.  Never select
# these again even if a source republishes them.
BLOCKED_URL_PARTS = [
    "livestartover-i.akamaized.net/antena3/",
    "linear02-i.akamaihd.net/hls/live/837811/cuatro/",
    "videohd.live:19360/8016/",
    "livestartover.atresmedia.com/lasexta/",
    "livestartover.atresmedia.com/geoneox/",
    "livestartover-i.akamaized.net/geoa3series/",
    "15.204.246.24:8080/MEGAHD/",
    "linear02-i.akamaihd.net/hls/live/837813/fdf/",
    "linear02-i.akamaihd.net/hls/live/837816/energy/",
    "ncdn.telewebion.ir/baenergy/",
    "linear02-i.akamaihd.net/hls/live/837815/bemad/",
    "pastebin.com/raw/afgk7wAC",
    "telemadrid-23-secure2.akamaized.net/master.m3u8",
    "cartv.streaming.aranova.es/hls/live/aragontv_canal1.m3u8",
]

def norm(value):
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()

ALIAS_TO_CANONICAL = {}
for canonical, aliases in ALIASES.items():
    for alias in aliases:
        ALIAS_TO_CANONICAL[norm(alias)] = canonical

def blocked(url):
    u = (url or "").lower()
    return any(part.lower() in u for part in BLOCKED_URL_PARTS)

def download(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 Spanish-TV-Updater/1.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8-sig", errors="replace")

def parse_m3u(data, source_name):
    lines = [line.strip() for line in data.splitlines() if line.strip()]
    found = []

    for i, line in enumerate(lines):
        if not line.startswith("#EXTINF:"):
            continue

        j = i + 1
        extra = []
        while j < len(lines) and lines[j].startswith("#") and not lines[j].startswith("#EXTINF:"):
            extra.append(lines[j])
            j += 1

        if j >= len(lines):
            continue

        url = lines[j].strip()
        if not url or url.startswith("#") or not url.lower().startswith(("http://", "https://")):
            continue

        if not url.lower().split("?", 1)[0].endswith(".m3u8"):
            continue

        tvg_id_match = re.search(r'tvg-id="([^"]+)"', line)
        tvg_name_match = re.search(r'tvg-name="([^"]+)"', line)
        tvg_country_match = re.search(r'tvg-country="([^"]*)"', line)
        display = line.split(",", 1)[1].strip() if "," in line else ""

        country = (tvg_country_match.group(1).strip().upper() if tvg_country_match else "")
        tvg_id = tvg_id_match.group(1).strip() if tvg_id_match else ""
        candidates = [
            tvg_name_match.group(1).strip() if tvg_name_match else "",
            display,
        ]

        canonical = None
        for candidate in candidates:
            n = norm(candidate)
            if n in ALIAS_TO_CANONICAL:
                canonical = ALIAS_TO_CANONICAL[n]
                break

        if canonical is None or blocked(url):
            continue

        found.append({
            "canonical": canonical,
            "extinf": line,
            "extra": extra,
            "url": url,
            "country": country,
            "tvg_id": tvg_id,
            "source": source_name,
        })

    return found

def hls_health(url):
    """Return True for a healthy manifest, False for a definite failure."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "VLC/3.0 Spanish-TV-Updater", "Accept": "*/*"},
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            if response.status < 200 or response.status >= 400:
                return False
            raw = response.read(32768)
            text = raw.decode("utf-8", errors="ignore")
            if "#EXTM3U" not in text:
                return False

            # If it is a master playlist, fetch the first child playlist too.
            if "#EXT-X-STREAM-INF" in text:
                lines = [x.strip() for x in text.splitlines() if x.strip()]
                for idx, item in enumerate(lines):
                    if item.startswith("#EXT-X-STREAM-INF") and idx + 1 < len(lines):
                        child = lines[idx + 1]
                        if child.startswith("#"):
                            continue
                        child_url = urllib.parse.urljoin(url, child)
                        child_req = urllib.request.Request(
                            child_url,
                            headers={"User-Agent": "VLC/3.0 Spanish-TV-Updater"},
                        )
                        with urllib.request.urlopen(child_req, timeout=8) as child_resp:
                            if child_resp.status < 200 or child_resp.status >= 400:
                                return False
                            child_text = child_resp.read(16384).decode("utf-8", errors="ignore")
                            return "#EXTM3U" in child_text
            return True
    except Exception:
        return False

def source_candidates():
    all_candidates = []

    for source_name, url in [
        ("TDTChannels official", OFFICIAL_SOURCE),
        ("Dearbulut Spain", HEALTHY_ES_SOURCE),
        ("Dearbulut online", HEALTHY_ALL_SOURCE),
    ]:
        print(f"Downloading {source_name}: {url}")
        try:
            entries = parse_m3u(download(url), source_name)
        except Exception as exc:
            print(f"  WARNING: could not download source: {exc}")
            continue

        print(f"  parsed {len(entries)} usable M3U8 entries")

        for entry in entries:
            # Dearbulut online is global. Only accept Spain-tagged entries
            # there, preventing the Nova.rs / Mega.cl / Energy.ir mistake we
            # saw in the previous playlist.
            if source_name == "Dearbulut online":
                if entry["country"] and entry["country"] != "ES":
                    continue
                if not entry["country"] and not entry["tvg_id"].lower().endswith(".es"):
                    continue

            all_candidates.append(entry)

    return all_candidates

def make_extinf(canonical, number, entry):
    source_extinf = entry.get("extinf", "")
    logo_match = re.search(r'tvg-logo="([^"]+)"', source_extinf)
    group_match = re.search(r'group-title="([^"]+)"', source_extinf)

    tvg_id = entry.get("tvg_id") or ""
    if not tvg_id:
        safe = re.sub(r"[^A-Za-z0-9]+", "", canonical)
        tvg_id = safe + ".es"

    logo = logo_match.group(1) if logo_match else ""
    group = group_match.group(1) if group_match else "Spain"

    parts = [
        '#EXTINF:-1',
        f'tvg-id="{tvg_id}"',
        f'tvg-chno="{number}"',
        f'tvg-name="{canonical}"',
        f'group-title="{group}"',
    ]
    if logo:
        parts.append(f'tvg-logo="{logo}"')

    return " ".join(parts) + f",{canonical}"

# Build candidate list
dynamic = source_candidates()

# Index candidates by canonical name, keeping source priority.
by_channel = {}
priority = {
    "TDTChannels official": 0,
    "Dearbulut Spain": 1,
    "Dearbulut online": 2,
}
for entry in dynamic:
    by_channel.setdefault(entry["canonical"], []).append(entry)

for key in by_channel:
    by_channel[key].sort(key=lambda x: priority.get(x["source"], 99))

selected = {}
source_used = {}

# 1) Lock in the 15 streams personally confirmed by the user.
for canonical, (tvg_id, url) in KNOWN_GOOD.items():
    selected[canonical] = {
        "canonical": canonical,
        "tvg_id": tvg_id,
        "url": url,
        "source": "user-tested",
        "extinf": "",
        "extra": [],
        "country": "ES",
    }
    source_used[canonical] = "user-tested"

# 2) For everything else, try official first, then health-checked Spain.
for canonical in PRIMARY:
    if canonical in selected:
        continue

    for candidate in by_channel.get(canonical, []):
        if hls_health(candidate["url"]):
            selected[canonical] = candidate
            source_used[canonical] = candidate["source"]
            break

# 3) Fill any gaps from well-maintained public Spanish channels.
for canonical in BACKUPS:
    if len(selected) >= 30:
        break
    if canonical in selected:
        continue

    for candidate in by_channel.get(canonical, []):
        if hls_health(candidate["url"]):
            selected[canonical] = candidate
            source_used[canonical] = candidate["source"]
            break

# Final ordering: primary order first, then backups.
ordered = [c for c in PRIMARY if c in selected]
ordered += [c for c in BACKUPS if c in selected and c not in ordered]

if len(ordered) < 20:
    raise RuntimeError(
        f"Only {len(ordered)} usable channels were selected; refusing to "
        "replace the previous playlist."
    )

print()
print(f"Selected {len(ordered)} channels:")
for index, canonical in enumerate(ordered, start=1):
    print(f"  {index:02d}  {canonical:<28} [{source_used[canonical]}]")

lines = [f'#EXTM3U x-tvg-url="{EPG}"']
for number, canonical in enumerate(ordered, start=1):
    entry = selected[canonical]
    if source_used[canonical] == "user-tested":
        extinf = (
            f'#EXTINF:-1 tvg-id="{entry["tvg_id"]}" '
            f'tvg-chno="{number}" tvg-name="{canonical}" '
            f'group-title="Spain",{canonical}'
        )
    else:
        extinf = make_extinf(canonical, number, entry)

    lines.extend([extinf, entry["url"]])

OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"\nWrote {OUTPUT} with {len(ordered)} channels.")
