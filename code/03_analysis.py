"""Step 3: every number quoted anywhere goes into data/results.json; the page data into data/site.json.
Unit: a feature (one SCAR common id, after merging 8 duplicates). 'Naming nation' is who first named it, read from the
narratives (see 01_clean.py); 'gazetteer' is a national list that includes the name. Shares of kinds are of all features
unless 'of stated' is said: then features whose narrative says what they are named after."""
import pandas as pd, numpy as np
from collections import Counter
from common import *
import parse as PA

F = pd.read_csv(f"{DATA}/features.csv", keep_default_na=False, na_values=[""])
PE = pd.read_csv(f"{DATA}/people.csv", keep_default_na=False, na_values=[""])
N = pd.read_csv(f"{DATA}/names.csv", keep_default_na=False, na_values=[""])
CM = jload(f"{WORK}/clean_meta.json")
pc = lambda a, b: round(100 * a / b, 2) if b else None
R = {"meta": {"page": PAGE, "repo": REPO, "scar": SCAR_CITE}}
F["nation"] = F.nation.fillna("Not known")
known = F.kind != "unknown"
R["source"] = {"rows": CM["rows"], "features": len(F), "gazetteers": int(N.gaz[N.gaz != "Undersea (SCUFN)"].nunique()),
               "multi": int((F.n_gaz > 1).sum()), "multi_pct": pc((F.n_gaz > 1).sum(), len(F)), "single": int((F.n_gaz == 1).sum()),
               "different": int(F.different.sum()), "different_pct_multi": pc(F.different.sum(), (F.n_gaz > 1).sum()),
               "merged": int(len(pd.read_csv(f"{DATA}/overrides_merge.csv"))), "undersea": int(F.undersea.sum()), "undersea_scufn": int((F.nation == "Undersea (SCUFN)").sum()),
               "wd_features": CM["wd_features"], "wd_linked": CM["wd_linked"], "wd_linked_pct": pc(CM["wd_linked"], CM["wd_features"]),
               "people": len(PE), "people_located": int(PE.blat.notna().sum()), "features_with_person_wd": int(F.wd_person.notna().sum()),
               "nation_known": int((F.nation != "Not known").sum()), "nation_known_pct": pc((F.nation != "Not known").sum(), len(F)),
               "nation_src": F.nation_src.value_counts().to_dict(), "stated": int(known.sum()), "stated_pct": pc(known.sum(), len(F)),
               "year_known": int(F.year.notna().sum()), "year_narr": int((F.year_src == "narrative").sum())}
G = N.gaz.value_counts()
R["gaz"] = [{"gaz": g, "n": int(n), "only": int(((F.n_gaz == 1) & (F.gazetteers == g)).sum())} for g, n in G.items()]

# ---- what features are named after
kc = F.kind.value_counts()
R["kind"] = {k: {"n": int(kc.get(k, 0)), "pct": pc(kc.get(k, 0), len(F)), "pct_stated": pc(kc.get(k, 0), known.sum()) if k != "unknown" else None,
                 "name": KIND_NAME[k]} for k, *_ in KINDS}
R["kind"]["people_all"] = {"n": int(kc.get("person", 0) + kc.get("group", 0)), "pct_stated": pc(kc.get("person", 0) + kc.get("group", 0), known.sum())}
R["kind"]["vessels"] = {"n": int(kc.get("ship", 0) + kc.get("vehicle", 0)), "pct_stated": pc(kc.get("ship", 0) + kc.get("vehicle", 0), known.sum())}

# ---- naming nations
NAT = F.nation.value_counts()
nats = [n for n in NAT.index if n != "Not known"]
REAL = [n for n in nats if n != "Undersea (SCUFN)"]   # the GEBCO/SCUFN undersea list is not a nation


def in_claim(lon, a, b):
    lon = np.asarray(lon)
    if b > 180: return (lon >= a) | (lon <= b - 360)
    return (lon >= a) & (lon < b)


CL = {}
for nat, nm, a, b in CLAIMS:
    CL.setdefault(nat, []).append((a, b))
# Peter I Island (68.8 S, 90.6 W) is a Norwegian dependency claimed on its own, outside the sector claims and inside the
# longitudes of unclaimed Marie Byrd Land: its features count with Norway's claim and not with the unclaimed sector.
PETER = F.lat.between(-69.1, -68.6) & F.lon.between(-91.2, -90.2)
R["peter_i"] = int(PETER.sum())
F["claim"] = "Unclaimed"
for nat, nm, a, b in CLAIMS:   # Argentina/Chile/UK overlap: a feature can be in several claims
    m = in_claim(F.lon, a, b)
    F.loc[m & (F.claim == "Unclaimed"), "claim"] = nat
    F.loc[m & (F.claim != "Unclaimed") & (F.claim != nat) & ~F.claim.str.contains(nat), "claim"] += "/" + nat
LAND = F.undersea == 0          # claims cover land and ice shelves: undersea (sea-floor) features are left out of every claim share
F.loc[~LAND, "claim"] = "Undersea"
F.loc[PETER & LAND, "claim"] = "Norway"
F["mby"] = in_claim(F.lon, UNCLAIMED[1], UNCLAIMED[2]) & LAND & ~PETER
NB = []
for n in nats[:16]:
    f = F[F.nation == n]; k = f[f.kind != "unknown"]; kk = k.kind.value_counts()
    row = {"nation": n, "n": len(f), "pct": pc(len(f), len(F)), "stated": len(k),
           **{f"{x}_pct": pc(kk.get(x, 0), len(k)) for x in ("person", "place", "descriptive", "ship", "association", "myth", "nature", "institution", "word", "other")},
           "year_median": None if f.year.isna().all() else int(f.year.median()), "women": int(f.woman.sum())}
    if n in CL:
        ins = np.zeros(len(f), bool)
        fl = f.undersea.values == 0
        for a, b in CL[n]: ins |= in_claim(f.lon, a, b)
        if n == "Norway": ins |= PETER[f.index].values
        row["own_claim_pct"] = pc((ins & fl).sum(), fl.sum())
    NB.append(row)
R["nations"] = NB
R["nation_n"] = {r["nation"]: r for r in NB}
R["n_nations"] = len(REAL)
R["not_known"] = int(NAT.get("Not known", 0))
US, UK = R["nation_n"]["United States"], R["nation_n"]["United Kingdom"]
R["us_uk_pct"] = round(US["pct"] + UK["pct"], 2)
# claims: who named the features inside each claim
CLR = []
for nat in ["Norway", "Australia", "France", "New Zealand", "Chile", "United Kingdom", "Argentina"]:
    m = np.zeros(len(F), bool)
    for a, b in CL[nat]: m |= in_claim(F.lon, a, b)
    if nat == "Norway": m |= PETER.values
    m &= LAND.values
    f = F[m]; v = f.nation.value_counts()
    CLR.append({"claim": nat, "name": [x[1] for x in CLAIMS if x[0] == nat][0], "n": int(m.sum()), "own_pct": pc(v.get(nat, 0), len(f)),
                "top": [{"nation": a, "n": int(b), "pct": pc(b, len(f))} for a, b in v.head(4).items()]})
mb = F[F.mby]; v = mb.nation.value_counts()
CLR.append({"claim": "Unclaimed", "name": UNCLAIMED[0], "n": len(mb), "own_pct": None, "top": [{"nation": a, "n": int(b), "pct": pc(b, len(mb))} for a, b in v.head(4).items()]})
R["claims"] = CLR
R["claim_n"] = {c["claim"]: c for c in CLR}

# ---- when
E = []
for a, b, lab in ERAS:
    f = F[F.year.between(a, b)]
    E.append({"label": lab, "from": a, "to": b, "n": len(f), "pct": pc(len(f), F.year.notna().sum()),
              "top": [{"nation": x, "n": int(y)} for x, y in f.nation.value_counts().head(3).items()]})
R["eras"] = E
dec = (F.year // 10 * 10).value_counts().sort_index()
R["decades"] = {int(k): int(v) for k, v in dec.items()}
R["peak_decade"] = int(dec.idxmax()); R["peak_decade_n"] = int(dec.max())
R["dec_nation"] = {n: {int(k): int(v) for k, v in (F[F.nation == n].year // 10 * 10).value_counts().sort_index().items()} for n in nats[:10]}
R["since2000"] = int((F.year >= 2000).sum()); R["since2000_pct"] = pc((F.year >= 2000).sum(), F.year.notna().sum())
R["before1900"] = int((F.year < 1900).sum())
R["bulg_since2000_pct"] = pc(((F.year >= 2000) & (F.nation == "Bulgaria")).sum(), (F.year >= 2000).sum())
R["year_median"] = int(F.year.median())
b = F[F.nation == "Bulgaria"]
R["bulgaria"] = {"n": len(b), "place_n": int((b.kind == "place").sum()), "place_pct": R["nation_n"]["Bulgaria"]["place_pct"],
                 "since2000_pct": pc((b.year >= 2000).sum(), b.year.notna().sum())}

# ---- people in Wikidata: where they were born
L = PE[PE.continent.notna()]
cc = L.continent.value_counts(); ct = L.country.value_counts()
R["people"] = {"n": len(PE), "located": len(L), "cont": {c: {"n": int(cc.get(c, 0)), "pct": pc(cc.get(c, 0), len(L))} for c in CONT_ORDER},
               "top": [{"country": a, "n": int(b), "pct": pc(b, len(L))} for a, b in ct.head(12).items()], "n_countries": int(ct.size),
               "europe_pct": pc(cc.get("Europe", 0), len(L)), "south_n": int(cc.get("South America", 0) + cc.get("Africa", 0)),
               "asia_n": int(cc.get("Asia", 0)), "africa_n": int(cc.get("Africa", 0)), "sam_n": int(cc.get("South America", 0)),
               "oce_n": int(cc.get("Oceania", 0)), "born_median": int(PE.born.median()),
               "top_people": [{"name": r.name, "n": int(r.n_features), "country": r.country if isinstance(r.country, str) else ""} for r in PE.sort_values(["n_features", "born"], ascending=[False, True]).head(12).itertuples()]}
# born in the naming nation? person features with a located Wikidata namesake
home = {"United States": "United States", "United Kingdom": "United Kingdom", "Norway": "Norway", "Australia": "Australia",
        "New Zealand": "New Zealand", "Russia": "Russia", "France": "France", "Belgium": "Belgium", "Germany": "Germany",
        "Bulgaria": "Bulgaria", "Poland": "Poland", "Chile": "Chile", "Argentina": "Argentina", "Japan": "Japan", "Sweden": "Sweden"}
pp = PE.set_index("pid")
HX = []
for r in F[F.wd_person.notna()].itertuples():
    pid = r.wd_person.split("; ")[0]
    if pid in pp.index and isinstance(pp.loc[pid, "country"], str):
        HX.append((r.nation, pp.loc[pid, "country"]))
HX = pd.DataFrame(HX, columns=["nation", "born"])
R["home"] = []
for n in ["United States", "United Kingdom", "Australia", "New Zealand", "Norway", "France", "Russia", "Bulgaria"]:
    h = HX[HX.nation == n]
    if len(h) >= 25:
        R["home"].append({"nation": n, "n": len(h), "home_pct": pc((h.born == home[n]).sum(), len(h)),
                          "top_other": [x for x in h[h.born != home[n]].born.value_counts().head(3).index]})
R["home_n"] = {x["nation"]: x for x in R["home"]}

# ---- women
P_ = F[F.kind == "person"]
W = F[F.woman == 1]
R["women"] = {"n": len(W), "pct_person": pc(len(W), len(P_)),
              "by_era": [{"label": lab, "n": int(W.year.between(a, b).sum()), "persons": int(P_.year.between(a, b).sum()),
                          "pct": pc(W.year.between(a, b).sum(), P_.year.between(a, b).sum())} for a, b, lab in ERAS],
              "since1990": int((W.year >= 1990).sum()), "since1990_pct": pc((W.year >= 1990).sum(), (P_.year >= 1990).sum()),
              "before1990_pct": pc((W.year < 1990).sum(), (P_.year < 1990).sum()),
              "nation": {n: int((W.nation == n).sum()) for n in W.nation.value_counts().head(6).index}}
rel = W.honoree.str.contains(r"\b(?:wife|widow|daughter|mother|sister|niece|fianc|Queen|Princess|Lady|Mrs|Mme|Madame)\b", case=False)
R["women"]["relatives_royals"] = int(rel.sum()); R["women"]["relatives_royals_pct"] = pc(rel.sum(), len(W))
R["women"]["pre1990_rel_pct"] = pc((rel & (W.year < 1990)).sum(), (W.year < 1990).sum())
R["women"]["post1990_rel_pct"] = pc((rel & (W.year >= 1990)).sum(), (W.year >= 1990).sum())
R["women"]["big"] = [n for n in ["Queen Maud Land", "Victoria Land", "Marie Byrd Land", "Princess Elizabeth Land", "Queen Mary Land", "Adelaide Island",
                                 "Ronne Ice Shelf", "Ingrid Christensen Coast", "Princess Astrid Coast", "Princess Ragnhild Coast", "Queen Mary Coast", "Adélie Coast"] if n in set(W.name)]

# ---- surnames on the map: person features by surname, and every feature whose name carries it
sur = P_[P_.surname.notna() & (P_.surname.str.len() >= 3)]
spec = [set(PA.specific(n)) for n in F.name]
cnt = Counter(PA.fold(s) for s in sur.surname)
carry = Counter()
for sp in spec:
    for t in sp: carry[t] += 1
carry = Counter()
for sp, k in zip(spec, F.kind):
    if k in ("person", "association"):
        for t in sp: carry[t] += 1
S = sorted(((s, n, carry.get(s, 0)) for s, n in cnt.items() if len(s) >= 3 and n >= 3), key=lambda x: (-x[1], -x[2]))
R["surnames"] = [{"surname": s.title(), "person": n, "carry": c} for s, n, c in S[:20]]
keys = P_[P_.pkey.notna()].pkey.value_counts()
R["pkeys"] = [{"key": k, "n": int(v)} for k, v in keys.head(20).items()]

# ---- what the honoured people did, read from the honoree text (first matching group, in this order)
ROLES = [("royal", "Royalty, heads of state and politicians", r"\b(?:King|Queen|Prince|Princess|Emperor|Empress|Crown Prince|President|Prime Minister|Minister|Senator|Governor|Secretary of|Congressman|Ambassador|statesman|politician|Czar|Tsar|Khan|ruler|monarch|sovereign)\b"),
         ("patron", "Patrons, sponsors and officials", r"\b(?:patron|sponsor|supporter|contributor|benefactor|donor|donated|subscribed|financ|fund|chairman|Chairman|director|Director|Secretary|secretary|President of|official|administrator|committee|Committee|Board)\b"),
         ("science", "Scientists and surveyors", r"(?:ologist|scientist|physicist|chemist|geodesist|surveyor|cartographer|oceanographer|botanist|zoologist|naturalist|researcher|astronomer|mathematician|geographer|engineer|physician|surgeon|medical officer|doctor|Dr\.?\s|Prof|USARP|USAP|investigator|specialist|scientific)"),
         ("military", "Naval and military personnel", r"\b(?:USN|USNR|RN|RAN|RNZN|USAF|USMC|USCG|RAF|RAAF|RNZAF|Navy|Army|Air Force|Marine|Squadron|VX-?6|VXE-?6|Lt\.|Lieut|Cdr\.|Comdr|Capt\.|Captain|Admiral|Adm\.|Col\.|Maj\.|Sgt|Ensign|Petty Officer|pilot|navigator|helicopter|aircrew|crewman|airman)\b"),
         ("support", "Support staff: cooks, radio operators, mechanics", r"\b(?:cook|radio|radioman|mechanic|electrician|carpenter|builder|technician|operator|handyman|dog handler|steward|storekeeper|plumber|driver|messman|seaman|sailor|stoker|fireman|boatswain|mate|clerk|typist|photographer|weather observer|observer|assistant|field assistant)\b"),
         ("explorer", "Explorers, whalers and sealers", r"\b(?:explorer|expedition|whaler|whaling|sealer|sealing|navigator|discover|leader|member of)\b"),
         ("arts", "Writers, artists and composers", r"\b(?:writer|poet|novelist|composer|painter|artist|author|musician|singer|sculptor|playwright)\b")]


def role(h):
    h = str(h)[:220]
    for k, _, rx in ROLES:
        if re.search(rx, h): return k
    return "other"


P_ = P_.assign(role=P_.honoree.map(role))
F.loc[P_.index, "role"] = P_.role
RO = {}
for n in ["All", "United States", "United Kingdom", "Australia", "New Zealand", "Norway", "Bulgaria", "Russia", "France"]:
    f = P_ if n == "All" else P_[P_.nation == n]
    v = f.role.value_counts()
    RO[n] = {"n": len(f), **{k: {"n": int(v.get(k, 0)), "pct": pc(v.get(k, 0), len(f))} for k in [r[0] for r in ROLES] + ["other"]}}
R["roles"] = RO; R["role_names"] = {k: n for k, n, _ in ROLES}; R["role_names"]["other"] = "Others or unclear"
R["us_support_military_pct"] = round(RO["United States"]["support"]["pct"] + RO["United States"]["military"]["pct"], 2)

# ---- several nations, different names
D = F[F.different == 1].copy()
D["nn"] = D.different_names.str.count(r"\|") + 2
R["different"] = {"n": len(D), "pct": pc(len(D), (F.n_gaz > 1).sum()),
                  "by_gaz": {g: int(D.gazetteers.str.contains(g).sum()) for g in ["Argentina", "Chile", "Russia", "Norway", "Germany", "United Kingdom", "United States"]},
                  "examples": [{"name": r.name, "names": r.names[:400], "nn": int(r.nn)} for r in D.sort_values(["nn", "n_gaz"], ascending=False).head(10).itertuples()]}

# ---- overrides and audit
OW = pd.read_csv(f"{DATA}/overrides_women.csv"); OF = pd.read_csv(f"{DATA}/overrides_features.csv"); OPp = pd.read_csv(f"{DATA}/overrides_people.csv")
AU = pd.read_csv(f"{DATA}/audit_sample_60.csv")
R["checks"] = {"women_read": len(OW), "women_yes": int((OW.verdict == "yes").sum()), "women_no": int((OW.verdict == "no").sum()),
               "kind_fixes": len(OF), "bp_unmapped": int((OPp.field == "birthplace_unknown").sum()), "merged": R["source"]["merged"],
               "audit_n": len(AU), "audit_decidable": int((AU.correct_now.fillna("") != "").sum()),
               "audit_first_faults": int(AU.note.str.contains("first pass wrong").sum()),
               "audit_first_ok_pct": pc((AU.correct_now == "yes").sum(), (AU.correct_now.fillna("") != "").sum()),
               "review_kind": int(OF.note.str.contains("review").sum()), "review_women": int(OW.note.fillna("").str.contains("review").sum()),
               "links_removed": int((OPp.field == "link").sum()), "uk_century_fixed": CM["uk_century_fixed"]}
R["kind_names"] = KIND_NAME; R["kind_cols"] = KIND_COL; R["ncol"] = NCOL
jsave(R, f"{DATA}/results.json", indent=1)

# ---- page data (site.json): features and people, compact arrays
nat_l = list(dict.fromkeys(MAIN_NATIONS + [n for n in nats if n not in MAIN_NATIONS] + ["Not known"]))
kind_l = [k for k, *_ in KINDS]
gaz_l = [g for g in G.index]
pidx = {p: i for i, p in enumerate(PE.pid)}
r1 = lambda v: None if pd.isna(v) else round(float(v), 1)
feats = []
for r in F.itertuples():
    pi = pidx.get(r.wd_person.split("; ")[0], -1) if isinstance(r.wd_person, str) else -1
    feats.append([int(r.fid), r.name, r1(r.x), r1(r.y), nat_l.index(r.nation), kind_l.index(r.kind), None if pd.isna(r.year) else int(r.year),
                  [gaz_l.index(g) for g in r.gazetteers.split("; ")], (r.honoree[:180] if isinstance(r.honoree, str) else ""), pi,
                  r.ftype, int(r.woman), (r.names[:300] if r.different else ""), round(float(r.lat), 3), round(float(r.lon), 3)])
people = [[r.pid, r.name, None if pd.isna(r.born) else int(r.born), r1(r.blon), r1(r.blat), r.country if isinstance(r.country, str) else "",
           r.near_town if isinstance(r.near_town, str) else "", None if pd.isna(r.near_km) else float(r.near_km),
           [int(x) for x in str(r.features).split(";")]] for r in PE.itertuples()]
site = {"fcols": ["fid", "name", "x", "y", "nation", "kind", "year", "gaz", "honoree", "person", "type", "woman", "names", "lat", "lon"],
        "pcols": ["pid", "name", "born", "lon", "lat", "country", "near", "near_km", "features"],
        "features": feats, "people": people, "nations": [[n, NCOL.get(n, NCOL["Other"])] for n in nat_l],
        "kinds": [[k, KIND_NAME[k], KIND_COL[k]] for k in kind_l], "gaz": gaz_l}
jsave(site, f"{DATA}/site.json")
print("results ok; site", os.path.getsize(f"{DATA}/site.json") // 1024, "KB")
print({k: v["pct_stated"] for k, v in R["kind"].items() if isinstance(v, dict) and "pct_stated" in v})
print([(x["nation"], x["n"], x.get("own_claim_pct")) for x in NB[:10]])
print(R["claims"]); print(R["eras"]); print(R["people"]["cont"], R["home"]); print(R["women"]); print(R["surnames"][:12]); print(R["different"]["n"], R["different"]["examples"][:3])
