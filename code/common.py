"""Shared paths, groupings and helpers for the antarctica-names study ("Who named Antarctica?").

Raw inputs (read in place, never modified):
  SCAR  /home/claude/newdata/raw_new9/scar.csv.gz
        The SCAR Composite Gazetteer of Antarctica (CGA), as served by the Australian Antarctic Data Centre geoserver
        (layer SCAR_CGA_PLACE_NAMES), CC BY 4.0. One row per name in one national gazetteer: place_name_mapping, gaz_id,
        country_name (the country whose gazetteer lists the name), latitude, longitude, altitude, feature_type_name,
        narrative, named_for, date_named, scar_common_id (the same feature in several national gazetteers) and others.
  WD    /home/claude/newdata/raw_new9/antarctica.tsv.gz
        Wikidata (CC0), queried through QLever: features with coordinates in Antarctica (?f, label, ?coord, P31 ?type), what they
        are named after (P138 ?named, label, P31 ?ntype; Q5 = human), and for people the birthplace coordinates (?bcoord),
        birthplace country (?bcountry), date of birth (?born) and citizenship (?ncountry). One row per type combination.
  MTN   /home/claude/newdata/raw_new9/mountains.tsv.gz  (Wikidata, CC0): used only for the sex (P21) and birthplace item of
        people who also appear there.
  LABELS data/wikidata_labels.csv: English labels of the Wikidata items in the extract, collected from the header-matched
        item/label column pairs of other Wikidata extracts (all CC0); used for country and type labels only.
  GEO   /home/claude/newdata/raw/geo/: Natural Earth 1:50m land and 1:10m countries and populated places (public domain).
  OFM   OpenFreeMap vector tiles (https://tiles.openfreemap.org/planet, OpenMapTiles schema, OpenStreetMap data ODbL):
        the ocean polygons south of 60 degrees S at zoom 6, for the coastline including ice shelves (04_basemap.py).
  FONTS /home/claude/ref/fonts (Fraunces, Source Serif 4, IBM Plex Mono)
"""
import json, gzip, os, re, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAWD = os.environ.get("AN_RAW", "/home/claude/newdata/raw_new9")
SCAR = f"{RAWD}/scar.csv.gz"
WD = f"{RAWD}/antarctica.tsv.gz"
MTN = f"{RAWD}/mountains.tsv.gz"
LABELS = os.environ.get("AN_LABELS", os.path.join(ROOT, "data", "wikidata_labels.csv"))
GEO = os.environ.get("AN_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("AN_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.environ.get("AN_WORK", "/home/claude/scratch/antarctica-names/work")   # intermediates, not in the repo
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "antarctica-names"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
WDURL = "https://www.wikidata.org/wiki/"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
SCAR_CITE = ("Secretariat SCAR (1992, updated 2014) Composite Gazetteer of Antarctica, Scientific Committee on Antarctic Research "
             "(the citation form the Australian Antarctic Data Centre recommends); served by the Australian Antarctic Data Centre, CC BY 4.0")

# national gazetteers as named in country_name, with short names and colours
GAZ = {"United States of America": "United States", "United Kingdom": "United Kingdom", "Russia": "Russia",
       "New Zealand": "New Zealand", "Australia": "Australia", "Argentina": "Argentina", "Chile": "Chile", "Norway": "Norway",
       "Bulgaria": "Bulgaria", "Germany": "Germany", "Poland": "Poland", "China": "China", "Japan": "Japan", "France": "France",
       "Unknown": "Undersea (SCUFN)", "Belgium": "Belgium", "Italy": "Italy", "Spain": "Spain", "Korea, Republic of": "South Korea",
       "India": "India", "Austria": "Austria", "Ecuador": "Ecuador", "Uruguay": "Uruguay", "Canada": "Canada",
       "South Africa": "South Africa", "Ukraine": "Ukraine"}
NCOL = {"United States": "#2F5FA7", "United Kingdom": "#C8322B", "Russia": "#7B57A8", "New Zealand": "#1F2F4D", "Australia": "#E0A11B",
        "Argentina": "#5BA3C9", "Chile": "#B4532A", "Norway": "#2E9A8C", "Bulgaria": "#55803A", "Germany": "#3A3A3A", "Poland": "#D9677F",
        "China": "#E05A2B", "Japan": "#C2185B", "France": "#4C6FBF", "Belgium": "#C8A21E", "Sweden": "#7FA7D9", "Italy": "#6E9E4A",
        "Undersea (SCUFN)": "#8FA9B8", "Other": "#9C9284", "Not known": "#C9C0B0"}
MAIN_NATIONS = ["United States", "United Kingdom", "New Zealand", "Australia", "Norway", "Russia", "Argentina", "Chile",
                "Bulgaria", "Japan", "Germany", "China", "Poland", "France", "Belgium"]

# what a feature is named after: groups for the charts, in order
KINDS = [("person", "A person", "#C8322B"), ("group", "People as a group", "#E07A6C"), ("ship", "A ship", "#2F5FA7"),
         ("vehicle", "An aircraft, vehicle or spacecraft", "#5BA3C9"), ("institution", "An institution, expedition or operation", "#E0A11B"),
         ("place", "A place elsewhere", "#2E9A8C"), ("event", "An event or date", "#B4532A"),
         ("myth", "Myth and fiction", "#7B57A8"), ("word", "Stars, letters, words and works", "#9C7BC0"),
         ("nature", "Wildlife and plants", "#55803A"), ("descriptive", "Its shape, colour or story (descriptive)", "#8C8478"),
         ("association", "A nearby feature (association)", "#BBB3A6"), ("other", "Other or unclear", "#D8D0C2"),
         ("unknown", "Not stated", "#ECE5D6")]
KIND_NAME = {k: n for k, n, _ in KINDS}
KIND_COL = {k: c for k, _, c in KINDS}

# Antarctic territorial claims (Antarctic Treaty, Article IV: frozen, not recognised by most states). Longitudes east positive.
CLAIMS = [("Norway", "Dronning Maud Land", -20, 44.633), ("Australia", "Australian Antarctic Territory", 44.633, 136.183),
          ("France", "Adélie Land", 136.183, 142.033), ("Australia", "Australian Antarctic Territory", 142.033, 160),
          ("New Zealand", "Ross Dependency", 160, 210), ("Chile", "Chilean Antarctic Territory", -90, -53),
          ("United Kingdom", "British Antarctic Territory", -80, -20), ("Argentina", "Argentine Antarctica", -74, -25)]
UNCLAIMED = ("Marie Byrd Land (unclaimed)", -150, -90)
CONT_ORDER = ["Europe", "North America", "Oceania", "South America", "Asia", "Africa"]
ERAS = [(1700, 1896, "Before 1897"), (1897, 1922, "Heroic age, 1897 to 1922"), (1923, 1945, "1923 to 1945"),
        (1946, 1956, "1946 to 1956"), (1957, 1959, "IGY, 1957 to 1959"), (1960, 1979, "1960 to 1979"),
        (1980, 1999, "1980 to 1999"), (2000, 2030, "2000 onwards")]


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def nonan(v):
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if isinstance(v, dict):
        return {str(k): nonan(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jsave(obj, path, indent=None):
    obj = nonan(obj)
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "wt", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


WORDS = "zero one two three four five six seven eight nine ten eleven twelve".split()


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "word": return WORDS[int(v)] if int(v) < len(WORDS) else f"{int(v):,}"
    if f == "Word": return (WORDS[int(v)] if int(v) < len(WORDS) else f"{int(v):,}").capitalize()
    raise ValueError(f)


def fill(tpl, R, keep=("DOI", "DOI_URL", "BLOG_URL")):
    return re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}",
                  lambda m: m.group(0) if m.group(1) in keep else fmt(get(R, m.group(1)), m.group(3)), tpl)


def ps(lon, lat):
    """Antarctic polar stereographic (EPSG:3031, true scale at 71 S, WGS84), in km. Used for maps and distances."""
    from pyproj import Transformer
    global _T
    try:
        _T
    except NameError:
        _T = Transformer.from_crs(4326, 3031, always_xy=True)
    x, y = _T.transform(lon, lat)
    import numpy as np
    return np.asarray(x) / 1000, np.asarray(y) / 1000
