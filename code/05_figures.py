"""Step 5: static figures for the blog (release/blog/b_*.png, 1800 px wide) and the paper (release/paper/f_*.png), all from
data/results.json, data/features.csv, data/people.csv and the base map (WORK/base.pkl, from 02_basemap.py)."""
import pickle, shutil
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly, Wedge
from matplotlib.collections import PatchCollection
import numpy as np, pandas as pd, geopandas as gpd
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
plt.rcParams.update({"font.family": "IBM Plex Mono", "font.size": 12, "axes.edgecolor": "#6E604E", "axes.labelcolor": "#2B2119",
                     "xtick.color": "#6E604E", "ytick.color": "#6E604E", "text.color": "#2B2119"})
PAPER, INK, MUT, RED, RULE, SEA, ICE, SHELF = "#F6EED8", "#2B2119", "#6E604E", "#A3261B", "#E2D3AE", "#DCE6EA", "#FFFFFF", "#EEF3F6"

R = jload(f"{DATA}/results.json")
F = pd.read_csv(f"{DATA}/features.csv", keep_default_na=False, na_values=[""])
PE = pd.read_csv(f"{DATA}/people.csv", keep_default_na=False, na_values=[""])
B = pickle.load(open(f"{WORK}/base.pkl", "rb"))
BLOG = os.path.join(ROOT, "release", "blog"); PAP = os.path.join(ROOT, "release", "paper")
os.makedirs(BLOG, exist_ok=True); os.makedirs(PAP, exist_ok=True)
ncol = lambda n: NCOL.get(n, NCOL["Other"])


def save(fig, name):
    fig.savefig(f"{BLOG}/b_{name}.png", dpi=200, facecolor=fig.get_facecolor())
    shutil.copy(f"{BLOG}/b_{name}.png", f"{PAP}/f_{name}.png")
    plt.close(fig)


def polys(g):
    for p in (g.geoms if hasattr(g, "geoms") else [g]):
        yield np.array(p.exterior.coords)


def antarctica(ax, lw=0.7, ext=3000, claims=False):
    ax.set_facecolor(SEA)
    ax.add_collection(PatchCollection([MPoly(r) for r in polys(B["shelves"])], facecolor=SHELF, edgecolor="none", lw=0, zorder=1))
    ax.add_collection(PatchCollection([MPoly(r) for r in polys(B["ground"])], facecolor=ICE, edgecolor="#5E7486", lw=lw, zorder=2))
    from pyproj import Transformer
    T = Transformer.from_crs(4326, 3031, always_xy=True)
    for la in (-60, -70, -80):
        x, y = T.transform(np.linspace(-180, 180, 361), np.full(361, la)); ax.plot(np.array(x) / 1000, np.array(y) / 1000, color="#7C93A3", lw=.5, ls=(0, (3, 4)), alpha=.6, zorder=1.5)
    for lo in range(-180, 180, 30):
        x, y = T.transform(np.full(30, lo), np.linspace(-60, -89.5, 30)); ax.plot(np.array(x) / 1000, np.array(y) / 1000, color="#7C93A3", lw=.5, ls=(0, (3, 4)), alpha=.6, zorder=1.5)
    if claims:
        for nat, nm, a, b in CLAIMS:
            for lo in (a, b):
                x, y = T.transform([lo, lo], [-60, -89.99]); ax.plot(np.array(x) / 1000, np.array(y) / 1000, color=ncol(nat), lw=1.2, ls=(0, (6, 4)), alpha=.8, zorder=3)
    ax.set_xlim(-ext, ext); ax.set_ylim(-ext * .9, ext * .95); ax.set_aspect("equal"); ax.axis("off")


def title(fig, t, s, y=0.965):
    H = fig.get_figheight()
    y = 1 - 0.3 / H
    fig.text(0.04, y, t, fontproperties=DISP, fontsize=26, color=INK, va="top")
    if s: fig.text(0.04, y - 0.52 / H, s, fontsize=11, color=MUT, va="top")


def foot(fig, s="Data: SCAR Composite Gazetteer of Antarctica (CC BY 4.0), Wikidata (CC0)  ·  maps.tristanhotham.com/antarctica-names"):
    fig.text(0.04, 0.012, s, fontsize=8.5, color=MUT)


# ---- 1. the map: every feature by naming nation
fig = plt.figure(figsize=(9, 9.6), facecolor=PAPER)
ax = fig.add_axes([0.04, 0.16, 0.92, 0.72]); antarctica(ax, claims=True)
order = [n["nation"] for n in R["nations"][:12]]
d = F.sample(frac=1, random_state=3)
c = [ncol(n) if n in order else (NCOL["Not known"] if n == "Not known" else NCOL["Other"]) for n in d.nation]
ax.scatter(d.x, d.y, s=2.2, c=c, lw=0, zorder=4)
title(fig, "Who named Antarctica?", f"{R['source']['features']:,} named features, coloured by the nation that named them. Dashed lines: claims.")
hs = [plt.Line2D([], [], marker="o", ls="", color=ncol(n), ms=7, label=n) for n in order] + [plt.Line2D([], [], marker="o", ls="", color=NCOL["Other"], ms=7, label="Other or not known")]
fig.legend(handles=hs, loc="lower center", ncol=5, frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, 0.03), handletextpad=.2, columnspacing=1.2)
foot(fig); save(fig, "map")

# ---- 2. nations
fig, ax = plt.subplots(figsize=(9, 6.2), facecolor=PAPER); fig.subplots_adjust(left=0.24, right=0.9, top=0.84, bottom=0.08)
rows = R["nations"][:14][::-1]
ax.barh([r["nation"] for r in rows], [r["n"] for r in rows], color=[ncol(r["nation"]) for r in rows], height=.7)
for i, r in enumerate(rows): ax.text(r["n"] + 60, i, f"{r['n']:,}  ({r['pct']:.0f}%)", va="center", fontsize=10.5)
ax.set_facecolor(PAPER); [ax.spines[s].set_visible(False) for s in ("top", "right", "bottom")]; ax.set_xticks([])
title(fig, "Features named by each nation", "The nation that first named each feature, from the gazetteer narratives.")
foot(fig); save(fig, "nations")

# ---- 3. claims
fig, ax = plt.subplots(figsize=(9, 5.6), facecolor=PAPER); fig.subplots_adjust(left=0.36, right=0.97, top=0.8, bottom=0.17)
cols = ["United States", "United Kingdom", "Australia", "Norway", "New Zealand", "Russia", "Argentina", "Chile", "France", "Japan", "Bulgaria"]
for i, cl in enumerate(R["claims"][::-1]):
    left = 0; tot = cl["n"]; vals = {t["nation"]: t["n"] for t in cl["top"]}
    rest = tot - sum(vals.values())
    for n, v in list(vals.items()) + [("Other", rest)]:
        if v <= 0: continue
        ax.barh(i, v / tot * 100, left=left, color=ncol(n) if n in cols else NCOL["Other"], height=.7, edgecolor=PAPER, lw=.8)
        if v / tot > .08: ax.text(left + v / tot * 50, i, f"{v / tot * 100:.0f}%", ha="center", va="center", fontsize=9.5, color="white")
        left += v / tot * 100
ax.set_yticks(range(len(R["claims"]))); ax.set_yticklabels([("Marie Byrd Land (unclaimed)" if c["claim"] == "Unclaimed" else c["name"]) for c in R["claims"][::-1]], fontsize=10.5)
ax.set_xlim(0, 100); ax.set_xticks([]); ax.set_facecolor(PAPER); [ax.spines[s].set_visible(False) for s in ax.spines]
hs = [plt.Rectangle((0, 0), 1, 1, color=ncol(n)) for n in cols] + [plt.Rectangle((0, 0), 1, 1, color=NCOL["Other"])]
fig.legend(hs, cols + ["Others"], loc="lower center", ncol=6, frameon=False, fontsize=8.5, bbox_to_anchor=(0.5, 0.0))
title(fig, "Who named the features in each claim", "Features inside each national sector, by naming nation. The Peninsula claims overlap. Undersea features left out.")
save(fig, "claims")

# ---- 4. decades
fig, ax = plt.subplots(figsize=(9, 5.6), facecolor=PAPER); fig.subplots_adjust(left=0.09, right=0.98, top=0.8, bottom=0.2)
D = list(range(1820, 2030, 10)); top = list(R["dec_nation"].keys())[:8]; bot = np.zeros(len(D))
for n in top:
    v = np.array([R["dec_nation"][n].get(str(x), 0) for x in D]); ax.bar(D, v, bottom=bot, width=8, color=ncol(n), label=n); bot += v
v = np.array([R["decades"].get(str(x), 0) for x in D]) - bot; ax.bar(D, v, bottom=bot, width=8, color=NCOL["Other"], label="Other")
ax.set_facecolor(PAPER); [ax.spines[s].set_visible(False) for s in ("top", "right")]
ax.set_xticks([1820, 1860, 1900, 1940, 1980, 2020]); ax.set_xticklabels(["1820s", "1860s", "1900s", "1940s", "1980s", "2020s"])
ax.annotate("IGY 1957 to 1958", xy=(1950, 3000), xytext=(1880, 4300), fontsize=10.5, color=RED, arrowprops=dict(arrowstyle="-", color=RED, lw=.8))
ax.annotate("Heroic age", xy=(1905, 330), xytext=(1868, 1500), fontsize=10.5, color=RED, arrowprops=dict(arrowstyle="-", color=RED, lw=.8))
fig.legend(loc="lower center", ncol=5, frameon=False, fontsize=9.5, bbox_to_anchor=(0.53, 0.0))
title(fig, "Names given in each decade", "By year of naming (or first approval), stacked by naming nation.")
save(fig, "decades")

# ---- 5. kinds by nation
KK = ["person", "ship", "institution", "place", "myth", "word", "nature", "descriptive", "association", "other"]
fig, ax = plt.subplots(figsize=(9, 7.4), facecolor=PAPER); fig.subplots_adjust(left=0.2, right=0.97, top=0.86, bottom=0.25)
rows = R["nations"][:12][::-1]
for i, r in enumerate(rows):
    left = 0
    for k in KK:
        v = r[k + "_pct"] or 0
        ax.barh(i, v, left=left, color=KIND_COL[k], height=.72, edgecolor=PAPER, lw=.6)
        if v > 9: ax.text(left + v / 2, i, f"{v:.0f}%", ha="center", va="center", fontsize=9, color="white" if k in ("person", "ship", "place", "descriptive", "myth") else INK)
        left += v
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r["nation"] for r in rows], fontsize=10.5); ax.set_xlim(0, 100); ax.set_xticks([])
ax.set_facecolor(PAPER); [ax.spines[s].set_visible(False) for s in ax.spines]
hs = [plt.Rectangle((0, 0), 1, 1, color=KIND_COL[k]) for k in KK]
fig.legend(hs, [KIND_NAME[k] for k in KK], loc="lower left", ncol=2, frameon=False, fontsize=9, bbox_to_anchor=(0.03, 0.0))
title(fig, "What each nation names its features after", "Share of features whose narrative says what the name means.")
save(fig, "kinds")

# ---- 6. roles
RK = list(R["role_names"].keys()); RC = ["#7B57A8", "#E0A11B", "#2E9A8C", "#2F5FA7", "#C8322B", "#B4532A", "#9C7BC0", "#D8D0C2"]
fig, ax = plt.subplots(figsize=(9, 5.8), facecolor=PAPER); fig.subplots_adjust(left=0.2, right=0.97, top=0.83, bottom=0.22)
NR = ["All", "United States", "United Kingdom", "Australia", "New Zealand", "Norway", "Russia", "France", "Bulgaria"][::-1]
for i, n in enumerate(NR):
    left = 0
    for k, c in zip(RK, RC):
        v = R["roles"][n][k]["pct"]; ax.barh(i, v, left=left, color=c, height=.72, edgecolor=PAPER, lw=.6)
        if v > 9: ax.text(left + v / 2, i, f"{v:.0f}%", ha="center", va="center", fontsize=9, color="white" if k != "other" else INK)
        left += v
ax.set_yticks(range(len(NR))); ax.set_yticklabels(["All nations" if n == "All" else n for n in NR], fontsize=10.5); ax.set_xlim(0, 100); ax.set_xticks([])
ax.set_facecolor(PAPER); [ax.spines[s].set_visible(False) for s in ax.spines]
fig.legend([plt.Rectangle((0, 0), 1, 1, color=c) for c in RC], [R["role_names"][k] for k in RK], loc="lower center", ncol=2, frameon=False, fontsize=9, bbox_to_anchor=(0.55, 0.0))
title(fig, "What the honoured people did", "Features named after a person, by what the narrative says about them.")
save(fig, "roles")

# ---- 7. women by era
fig, ax = plt.subplots(figsize=(9, 5), facecolor=PAPER); fig.subplots_adjust(left=0.3, right=0.93, top=0.8, bottom=0.12)
E = [e for e in R["women"]["by_era"] if e["persons"] >= 20][::-1]
ax.barh([e["label"] for e in E], [e["pct"] for e in E], color="#C8322B", height=.65)
for i, e in enumerate(E): ax.text(e["pct"] + .1, i, f"{e['pct']:.1f}%  ({e['n']} of {e['persons']:,})", va="center", fontsize=10)
ax.set_facecolor(PAPER); [ax.spines[s].set_visible(False) for s in ("top", "right", "bottom")]; ax.set_xticks([]); ax.set_xlim(0, max(e["pct"] for e in E) * 1.6)
title(fig, "Women among the people honoured", "Share of features named after a person that honour a woman, by period of naming.")
foot(fig, "Every candidate read by hand. Data: SCAR Composite Gazetteer (CC BY 4.0)  ·  maps.tristanhotham.com/antarctica-names"); save(fig, "women")

# ---- 8. birthplaces on a world map
ne = gpd.read_file(f"{GEO}/ne_50m_admin_0_countries.geojson"); ne = ne[ne.ADMIN != "Antarctica"]
fig = plt.figure(figsize=(9, 5.4), facecolor=PAPER); ax = fig.add_axes([0.02, 0.06, 0.96, 0.76]); ax.set_facecolor(SEA)
ne.plot(ax=ax, color="#ECD9AC", edgecolor="#9C8656", lw=.3)
L = PE[PE.blat.notna()].copy(); g = L.groupby([L.blat.round(1), L.blon.round(1)]).n_features.sum().reset_index()
ax.scatter(g.blon, g.blat, s=6 + g.n_features * 9, color="#C8322B", alpha=.65, edgecolor=INK, lw=.3, zorder=3)
ax.set_xlim(-170, 190); ax.set_ylim(-58, 80); ax.set_aspect(1.15); ax.axis("off")
title(fig, "Where the people on Antarctica were born", f"{R['people']['located']:,} people in Wikidata; {R['people']['europe_pct']:.0f}% were born in Europe. Circles sized by features.")
foot(fig); save(fig, "birthplaces")
print(sorted(os.listdir(BLOG)))
