"""Step 1: read the SCAR Composite Gazetteer and the Wikidata extract and write the clean tables.

Outputs
  data/names.csv     one row per name in a national gazetteer (the SCAR rows, trimmed): gaz_id, feature id (scar_common_id),
                     name, gazetteer country, coordinates, type, approval date.
  data/features.csv  one row per feature (scar_common_id): the lead name, coordinates (EPSG:4326 and EPSG:3031 km), type,
                     the gazetteers listing it and their names, whether the names differ, who named it (nation and the text
                     that says so), what it is named after (kind, the honoree text, the honoured surname), whether the honoree is
                     a woman (rules, then checked by hand), the naming year and its source, and the Wikidata link.
  data/people.csv    one row per person a feature is named after in Wikidata (P138, human), with the features, birth year,
                     birthplace coordinates, modern country and continent (Natural Earth), nearest large town.
Rules for reading the narratives are in code/parse.py. Hand corrections are in data/overrides_*.csv.
"""
import sys, unicodedata, difflib
import pandas as pd, numpy as np, geopandas as gpd
from shapely.geometry import Point
from common import *
import parse as P

from parse import fold, specific


# ---------------------------------------------------------------- SCAR
d = pd.read_csv(SCAR, dtype=str)
n_rows = len(d)
d = d[~d.is_deleted.isin(["Y", "y"])].copy()
d["lat"] = d.latitude.astype(float); d["lon"] = d.longitude.astype(float)
d["gaz"] = d.country_name.fillna("Unknown").map(GAZ)
assert d.gaz.notna().all(), d.country_name.unique()
d["fid"] = d.scar_common_id.astype(int)
# duplicates: the same feature under two common ids (same name within 2 km), merged (data/overrides_merge.csv)
for o in pd.read_csv(f"{DATA}/overrides_merge.csv").itertuples():
    assert (d.fid == o.fid_from).any(), o
    d.loc[d.fid == o.fid_from, "fid"] = o.fid_to
d["txt"] = (d.narrative.fillna("") + " " + d.named_for.fillna("")).map(P.WS)
d["nf"] = d.named_for.fillna("").map(P.WS)
d["approved"] = pd.to_numeric(d.date_named.str[:4], errors="coerce")
d.loc[(d.approved < 1770) | (d.approved > 2026), "approved"] = np.nan
# century slip in the source: 226 British approvals dated 1901 to 1910 are UK-APC decisions of 2001 to 2010 (date_named_old reads
# 2001 where date_named reads 1901; 157 of the narratives cite "APC, 200x"; several honour people born after 1940)
n_century = int(((d.gaz == "United Kingdom") & d.approved.between(1901, 1910)).sum())
d.loc[(d.gaz == "United Kingdom") & d.approved.between(1901, 1910), "approved"] += 100
d["name"] = d.place_name_mapping.str.strip()
d["cls"] = d.scar_feature_class.fillna("").str.strip()   # SCAR feature class; 6 = undersea (sea-floor) features

PRIO = ["United States", "United Kingdom", "New Zealand", "Australia", "Bulgaria", "Germany", "Poland", "Norway", "Japan", "China",
        "Italy", "South Korea", "India", "Spain", "Belgium", "France", "Chile", "Argentina", "Ecuador", "Uruguay", "Austria",
        "Canada", "South Africa", "Ukraine", "Undersea (SCUFN)", "Russia"]
d["prio"] = d.gaz.map({g: i for i, g in enumerate(PRIO)})
d = d.sort_values(["fid", "prio", "gaz_id"])[["gaz_id", "fid", "name", "gaz", "lat", "lon", "feature_type_name", "altitude", "txt", "nf", "approved", "prio", "cls"]]

def same_name(a, b):
    A, B = specific(a), specific(b)
    if not A or not B:
        return True
    for x in A:
        for y in B:
            if x == y or (len(x) >= 3 and len(y) >= 3 and (difflib.SequenceMatcher(None, x, y).ratio() >= 0.6 or x in y or y in x)):
                return True
    return False


import time; _t0 = time.time()
rows = []
for _i, (fid, g) in enumerate(d.groupby("fid", sort=True)):
    if _i % 2000 == 0: print(_i, round(time.time() - _t0), flush=True)
    lead = g.iloc[0]
    gl = list(dict.fromkeys(g.gaz))
    # who named it: the first narrative (in priority order) whose naming statement names an agency, expedition or leader
    nat = hit = ctx = None; nat_gaz = None
    for r in g.itertuples():
        if r.txt:
            nat, hit, ctx = P.namer_of(r.txt)
            if nat:
                nat_gaz = r.gaz; break
    nat_src = "narrative" if nat else None
    if not nat:   # the first expedition said to have discovered, charted or mapped it (in priority order of narratives)
        for r in g.itertuples():
            if r.txt and r.gaz in ("United States", "United Kingdom", "New Zealand", "Australia"):
                nat, hit = P.discoverer_of(r.txt)
                if nat:
                    nat_src, nat_gaz, ctx = "discoverer", r.gaz, None; break
    if not nat:
        real = [x for x in gl if x != "Undersea (SCUFN)"]
        if len(set(real)) == 2 and "Russia" in real:   # the Russian gazetteer transliterates most other nations' names
            real = [x for x in real if x != "Russia"]
        if len(set(real)) == 1:
            nat, nat_src = real[0], "only gazetteer"
        elif g.approved.notna().any():
            e = g[g.approved == g.approved.min()]
            if e.gaz.nunique() == 1:
                nat, nat_src = e.gaz.iloc[0], "earliest approval"
    # what it is named after: the first narrative (in priority order) that the rules can read
    kind, hon, prep, ksrc, nar = "unknown", "", "", None, ""
    for r in g.itertuples():
        c = P.clauses(r.txt) if r.txt else None
        # a statement about this very feature ("Ginger Reef was named in 2017 after the dog ...") beats one about its group
        own = re.search(re.escape(r.name) + r"[^.]{0,40}?\bwas (?:re)?named\b[^.]{0,40}?\b(for|after|in recognition of)\b(.*)", r.txt) if r.txt else None
        if own:
            c = ("", own.group(1), own.group(2).strip())
        if c is None and r.nf and not P.clauses(r.nf):
            c = ("", "for", r.nf)
        if c:
            k = P.kind(c[1], c[2])
            if k != "unknown":
                kind, hon, prep, ksrc, nar = k, c[2][:400], c[1], r.gaz, r.txt
                break
    if not nar:
        x = g[g.txt != ""]
        nar = x.txt.iloc[0] if len(x) else ""
        ksrc = x.gaz.iloc[0] if len(x) else None
    # the naming year: a year in the naming statement (the namer clause, 'named in 1957', 'APC, 1962'), else the first approval
    yrs = []
    for r in g.itertuples():
        t = r.txt
        if not t: continue
        for m in re.finditer(r"\b(?:re)?named\b([^.;]{0,120}?)\b(?:for|after|in honou?r of|because|in association with)\b", t, re.I):
            yrs += P.years_in(m.group(1))
        yrs += [int(y) for y in re.findall(r"\bnamed(?: [^.;]{0,40}?)? in (1[789]\d\d|20[012]\d)\b", t, re.I)]
        yrs += [int(y) for y in re.findall(r"\bAPC,? ?(1[89]\d\d|20[012]\d)", t)]
        yrs += [int(y) for y in re.findall(r"\(?(?:US-?ACAN|UK-?APC|NZ-?APC|ANCA|BGN)\)?,? (?:in )?(1[89]\d\d|20[012]\d)\b", t)]
    yrs = [y for y in yrs if 1770 <= y <= 2026]
    ap = g.approved.min()
    ny, ysrc = None, None
    if yrs:
        ny, ysrc = min(yrs), "narrative"
        if pd.notna(ap) and ny > ap: ny, ysrc = int(ap), "approval"
    elif pd.notna(ap):
        ny, ysrc = int(ap), "approval"
    names = list(dict.fromkeys(g.name))
    diff = [n for n in names if not same_name(n, lead["name"])]
    rows.append(dict(fid=fid, name=lead["name"], lead_gaz=lead.gaz, lat=g.lat.mean() if g.lat.max() - g.lat.min() < 0.5 else lead.lat,
                     lon=lead.lon, ftype=lead.feature_type_name if isinstance(lead.feature_type_name, str) else "",
                     alt=pd.to_numeric(g.altitude, errors="coerce").max(), n_gaz=len(set(gl)), gazetteers="; ".join(gl),
                     names=" | ".join(f"{a} ({b})" for a, b in zip(g.name, g.gaz)), n_names=len(names), different=int(len(diff) > 0),
                     different_names=" | ".join(diff), nation=nat, nation_src=nat_src, nation_hit=hit, nation_gaz=nat_gaz,
                     kind=kind, prep=prep, honoree=hon, kind_gaz=ksrc, narrative=nar[:1500], year=ny, year_src=ysrc,
                     approved=ap, gaz_ids=";".join(g.gaz_id), seabed=int((g.cls == "6").all())))
F = pd.DataFrame(rows)
x, y = ps(F.lon.values, F.lat.values); F["x"], F["y"] = np.round(x, 2), np.round(y, 2)
# undersea (sea-floor) features: every national entry is in SCAR feature class 6, or only the GEBCO/SCUFN undersea list holds it.
# They are kept in the feature counts but left out of every claim share (a claim is land and ice shelf).
F["undersea"] = ((F.seabed == 1) | ((F.gazetteers == "Undersea (SCUFN)") & (F.n_gaz == 1))).astype(int)

# documented corrections of the kind and the nation (data/overrides_features.csv)
OF = pd.read_csv(f"{DATA}/overrides_features.csv")
for o in OF.itertuples():
    m = F.fid == o.fid; assert m.sum() == 1, o
    F.loc[m, o.field] = o.value
    if o.field == "nation": F.loc[m, "nation_src"] = "override"

# ---------------------------------------------------------------- the honoured person's name and surname, women
TOK = re.compile(r"^(?:" + P.PRE + r")*(?:(?:the |a )?" + P.TITLE + r"\s)*", re.I)


def person_name(h):
    h = re.sub(r"^(?:the |a |an )?(?:" + P.NAT + r"\s)*(?:[\w'-]+\s)?" + P.ROLE + r",?\s", "", h, flags=re.I) if re.match(r"(?:the |a |an )?(?:" + P.NAT + r"\s)*(?:[\w'-]+\s)?" + P.ROLE + r",?\s[A-Z]", h, flags=re.I) else h
    h = TOK.sub("", h).strip()
    h = re.sub(r"^(?:then |late |the late )", "", h)
    m = re.match(r"((?:[A-ZÀ-Ý][\w'’.-]*|[a-z]{1,3}[A-Z][\w'’-]+|de|von|van|der|du|la|le|da|di|del|d'|\"[^\"]{1,20}\"|\([^)]{1,25}\))(?:\s(?:[A-ZÀ-Ý][\w'’.-]*|de|von|van|der|den|du|la|le|da|di|del|dos|d'|Mac|Mc|\"[^\"]{1,20}\"|\([A-Za-z\" ]{1,25}\))){0,6})", h)
    if not m: return "", ""
    nm = re.sub(r"\s*\([^)]*\)", "", m.group(1)).strip().rstrip(".,")
    nm = re.sub(r"\s(?:Jr|Sr|II|III|IV)\.?$", "", nm)
    nm = re.sub(r"\s(?:USN|USNR|USA|USAF|USMC|USCG|RN|RAN|RNZN|RAF|RAAF|RNZAF|RNVR|RM|NZ|UK|US)$", "", nm)
    toks = nm.split()
    if not toks: return "", ""
    sur = toks[-1]
    if len(toks) >= 2 and toks[-2].lower() in ("de", "von", "van", "du", "la", "le", "da", "di", "del", "der", "dos"):
        sur = toks[-2] + " " + sur
    if re.fullmatch(r"(?:[A-Z]\.?)+", sur) or sur.lower() in ("de", "von", "van", "du", "la", "le", "da", "di", "del"): return nm, ""
    return nm, sur


def person_key(nm, sur):
    """first initial + surname, folded: 'Capt. Robert F. Scott' and 'Robert Falcon Scott' -> 'r scott'"""
    if not sur: return ""
    toks = [t for t in re.sub(r"\([^)]*\)|\"[^\"]*\"", " ", nm).split() if t]
    first = toks[0] if len(toks) > 1 else ""
    return (fold(first)[:1] + " " + fold(sur)).strip()


F["person"] = ""; F["surname"] = ""
pm = F.kind == "person"
pn = F.loc[pm, "honoree"].map(person_name)
F.loc[pm, "person"] = pn.str[0]; F.loc[pm, "surname"] = pn.str[1]
F["pkey"] = [person_key(a, b) for a, b in zip(F.person, F.surname)]
# the surname should usually appear in the feature's own name: flag where it does not (honoree probably misread)
F["sur_in_name"] = [int(bool(s) and fold(s) in fold(n)) for s, n in zip(F.surname, F.name + " " + F.names)]


def woman_cue(r):
    if r.kind != "person": return ""
    h = r.honoree[:160]
    m = re.match(r"(?:the |a |an )?(?:then |late |former |present |reigning |then reigning )*(Queen|Princess|Empress|Duchess|Countess|Baroness|Lady|Dame|Mrs\.?|Miss|Ms\.?|Mme\.?|Madame|Mademoiselle|Mlle\.?|Frau|Fräulein|Señora|Sra\.?|Doña|wife|widow|daughter|daughters|sister|sisters|mother|grandmother|granddaughter|niece|aunt|fianc[ée]e|girlfriend|bride|woman|women)\b", h, re.I)
    if m: return m.group(1)
    m = re.match(r"(?:his|her|their|[A-Z][\w-]+'s) (wife|daughter|sister|mother|widow|niece|fianc[ée]e|granddaughter|daughters)\b", h)
    if m: return m.group(1)
    first = TOK.sub("", h).split(" ")[0].strip(",.")
    if first in P.FIRSTNAME_WOMEN: return "first name " + first
    if re.search(r"\b(?:she|her)\b", h[:200]) and not re.search(r"\b(?:he|his|him)\b", h[:200]) and r.kind == "person": return "she/her"
    if re.search(r"\b(?:first woman|first women|woman to|women to|female)\b", h[:200], re.I): return "woman"
    return ""


F["woman_cue"] = [woman_cue(r) for r in F.itertuples()]
OW = pd.read_csv(f"{DATA}/overrides_women.csv")       # every candidate read by hand: verdict yes/no, plus additions
F["woman"] = 0
for o in OW.itertuples():
    m = F.fid == o.fid; assert m.sum() == 1, o
    F.loc[m, "woman"] = int(o.verdict == "yes")
assert (F[F.woman == 1].kind == "person").all(), F[(F.woman == 1) & (F.kind != "person")][["fid", "name", "kind"]]
miss = F[(F.woman_cue != "") & ~F.fid.isin(OW.fid)]
if len(miss):
    miss[["fid", "name", "lead_gaz", "woman_cue", "honoree"]].assign(honoree=miss.honoree.str[:150]).to_csv(f"{WORK}/women_to_review.csv", index=False)
    print("WOMEN TO REVIEW:", len(miss), f"{WORK}/women_to_review.csv")


# ---------------------------------------------------------------- Wikidata
LB = pd.read_csv(LABELS).set_index("qid").label.to_dict()
q = lambda s: re.sub(r".*/(Q\d+)>$", r"\1", s) if isinstance(s, str) else s
W = pd.read_csv(WD, sep="\t", dtype=str, quoting=3); W.columns = [c.lstrip("?") for c in W.columns]
for c in ("f", "type", "named", "ntype", "bcountry", "ncountry"): W[c] = W[c].map(q)
for c in ("fLabel", "namedLabel"): W[c] = W[c].str.extract(r'^"(.*)"', expand=False)
xy = W.coord.str.extract(r"POINT\(([-\d.eE]+) ([-\d.eE]+)\)").astype(float); W["flon"], W["flat"] = xy[0], xy[1]
bxy = W.bcoord.str.extract(r"POINT\(([-\d.eE]+) ([-\d.eE]+)\)").astype(float); W["blon"], W["blat"] = bxy[0], bxy[1]
WF = W.drop_duplicates("f")[["f", "fLabel", "flon", "flat"]].dropna()
# match each Wikidata feature to a SCAR feature: same folded name (any gazetteer) within 25 km
d["fold"] = d.name.map(fold)
byname = {}
for r in d[["fold", "fid", "lat", "lon"]].itertuples():
    byname.setdefault(r.fold, []).append((r.fid, r.lat, r.lon))
link = {}
for r in WF.itertuples():
    c = byname.get(fold(r.fLabel), [])
    best = None
    for fid, la, lo in c:
        dk = math.hypot((lo - r.flon) * 111 * math.cos(math.radians(la)), (la - r.flat) * 111)
        if dk < 25 and (best is None or dk < best[1]): best = (fid, dk)
    if best: link[r.f] = best
WF["fid"] = WF.f.map(lambda k: link.get(k, (None,))[0])
print("Wikidata features", len(WF), "linked to SCAR", WF.fid.notna().sum())
H = W[(W.ntype == "Q5") & W.f.isin(link)].copy()
H["fid"] = H.f.map(lambda k: link[k][0])
# documented wrong links (data/overrides_people.csv, field link: the Wikidata feature id is in 'wikidata_value')
OP = pd.read_csv(f"{DATA}/overrides_people.csv")
for o in OP[OP.field == "link"].itertuples():
    m = (H.f == o.wikidata_value) & (H.named == o.pid); assert m.sum() >= 1, o
    H = H[~m]
pairs = H.drop_duplicates(["fid", "named"])[["fid", "f", "named", "namedLabel"]]
# a person per SCAR feature: if one feature has several Wikidata items, keep each distinct person once
F = F.merge(pairs.groupby("fid").agg(wd_item=("f", "first"), wd_person=("named", lambda s: "; ".join(dict.fromkeys(s))),
                                       wd_label=("namedLabel", lambda s: "; ".join(dict.fromkeys(x for x in s if isinstance(x, str))))).reset_index(), on="fid", how="left")
F["wd_feature"] = F.fid.map(WF.dropna(subset=["fid"]).astype({"fid": int}).groupby("fid").f.first())

# people: birthplace (first with coordinates), year, citizenship
MT = pd.read_csv(MTN, sep="\t", dtype=str, quoting=3); MT.columns = [c.lstrip("?") for c in MT.columns]
for c in ("p", "bplace", "sex"): MT[c] = MT[c].map(q)
msex = MT.drop_duplicates("p").set_index("p").sex.map({"Q6581072": "female", "Q6581097": "male"})
mbp = MT.drop_duplicates("p").set_index("p").bplace
prow = []
for pid, g in H.groupby("named"):
    g = g.sort_values(["blat"], na_position="last")
    b = g[g.blat.notna()].iloc[0] if g.blat.notna().any() else g.iloc[0]
    by = re.match(r"^(-?\d+)-", str(g.born.dropna().iloc[0])) if g.born.notna().any() else None
    prow.append(dict(pid=pid, name=g.namedLabel.dropna().iloc[0] if g.namedLabel.notna().any() else pid, born=int(by.group(1)) if by else None,
                     blon=b.blon, blat=b.blat, wd_country=LB.get(b.bcountry, b.bcountry) if isinstance(b.bcountry, str) else "",
                     citizenship="; ".join(sorted(set(LB.get(c, c) for c in g.ncountry.dropna()))), n_bcoord=g.bcoord.nunique(),
                     sex=msex.get(pid, ""), bplace_item=mbp.get(pid, ""), features=";".join(str(x) for x in sorted(set(g.fid)))))
PE = pd.DataFrame(prow)
for o in OP[OP.field == "birthplace"].itertuples():
    m = PE.pid == o.pid; assert m.sum() == 1, o
    PE.loc[m, ["blon", "blat", "wd_country"]] = [o.blon, o.blat, f"{o.corrected_value} (override)"]
for o in OP[OP.field == "birthplace_unknown"].itertuples():
    m = PE.pid == o.pid; assert m.sum() == 1, o
    PE.loc[m, ["blon", "blat"]] = [np.nan, np.nan]
for o in OP[OP.field == "label"].itertuples():
    PE.loc[PE.pid == o.pid, "name"] = o.corrected_value
ne = gpd.read_file(f"{GEO}/ne_10m_admin_0_countries.geojson")[["ADM0_A3", "ADMIN", "CONTINENT", "geometry"]]
has = PE.blat.notna()
pts = gpd.GeoDataFrame(PE[has][["pid"]], geometry=[Point(a, b) for a, b in zip(PE[has].blon, PE[has].blat)], crs=ne.crs)
j = gpd.sjoin(pts, ne, how="left", predicate="within").drop_duplicates("pid")
miss = j[j.ADM0_A3.isna()][["pid", "geometry"]]
if len(miss):
    jn = gpd.sjoin_nearest(miss.to_crs(3857), ne.to_crs(3857), how="left", max_distance=30000).drop_duplicates("pid")
    j = j.set_index("pid"); jn = jn.set_index("pid")
    for c in ("ADM0_A3", "ADMIN", "CONTINENT"): j.loc[jn.index, c] = jn[c]
    j = j.reset_index()
j = j.set_index("pid")
PE["iso3"] = PE.pid.map(j.ADM0_A3); PE["country"] = PE.pid.map(j.ADMIN); PE["continent"] = PE.pid.map(j.CONTINENT)
PE.loc[PE.continent == "Seven seas (open ocean)", "continent"] = None
PE["country"] = PE.country.replace({"United States of America": "United States", "Republic of Serbia": "Serbia", "Czechia": "Czech Republic",
                                    "United Republic of Tanzania": "Tanzania", "The Bahamas": "Bahamas"})
# nearest Natural Earth populated place, as a label (the extract has no birthplace names)
pp = gpd.read_file(f"{GEO}/ne_10m_populated_places_simple.geojson")[["name", "adm0name", "pop_max", "geometry"]]
pp = pp.to_crs(3857); pts = gpd.GeoDataFrame(PE[PE.blat.notna()][["pid"]], geometry=[Point(a, b) for a, b in zip(PE[PE.blat.notna()].blon, PE[PE.blat.notna()].blat)], crs=4326).to_crs(3857)
jn = gpd.sjoin_nearest(pts, pp, how="left", distance_col="dist").drop_duplicates("pid").set_index("pid")
PE["near_town"] = PE.pid.map(jn["name"]); PE["near_km"] = PE.pid.map((jn.dist / 1000 * np.cos(np.radians(PE.set_index("pid").blat.reindex(jn.index)))).round(1))
PE["n_features"] = PE.features.str.count(";") + 1
# people without an English label in the extract take the name read from the narrative of their first feature
_pn = F.set_index("fid").person
nolab = PE.name.str.fullmatch(r"Q\d+")
PE.loc[nolab, "name"] = [(_pn.get(int(f.split(";")[0]), "") or pid) for f, pid in zip(PE.loc[nolab, "features"], PE.loc[nolab, "pid"])]
PE["label_src"] = np.where(nolab, "narrative", "wikidata")
F.to_csv(f"{DATA}/features.csv", index=False)
PE.to_csv(f"{DATA}/people.csv", index=False)
d[["gaz_id", "fid", "name", "gaz", "lat", "lon", "feature_type_name", "approved"]].rename(columns={"feature_type_name": "ftype"}).to_csv(f"{DATA}/names.csv", index=False)
jsave({"rows": n_rows, "rows_kept": len(d), "wd_features": len(WF), "wd_linked": int(WF.fid.notna().sum()),
       "wd_rows": len(W), "uk_century_fixed": n_century, "wd_human_rows": int((W.ntype == "Q5").sum()), "wd_humans_all": int(W[W.ntype == "Q5"].named.nunique())}, f"{WORK}/clean_meta.json")
print(len(d), "names;", len(F), "features;", F.kind.value_counts().to_dict())
print("nation:", F.nation.value_counts(dropna=False).head(16).to_dict())
print("people", len(PE), "located", int(PE.blat.notna().sum()))
