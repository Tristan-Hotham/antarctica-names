"""Reddit collage (reddit/antarctica_names_collage.png, 3000 x 1900) and the social card (header.png, 1200 x 630).
Run from anywhere: python3 reddit/collage.py"""
import os, sys, runpy
HERE = os.path.dirname(os.path.abspath(__file__)); ROOTD = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOTD, "code"))
import matplotlib.patheffects as pe
G = runpy.run_path(os.path.join(ROOTD, "code", "05_figures.py"), run_name="figs")   # styles, base map and figures
globals().update({k: v for k, v in G.items() if not k.startswith("__")})
import matplotlib.pyplot as plt, numpy as np

R = jload(os.path.join(DATA, "results.json"))
SRC = "Data: SCAR Composite Gazetteer of Antarctica (CC BY 4.0), Wikidata (CC0), OpenStreetMap, Natural Earth  ·  Analysis and map: Dr Tristan Hotham  ·  maps.tristanhotham.com/antarctica-names"
halo = [pe.withStroke(linewidth=5, foreground=SEA)]
order = [n["nation"] for n in R["nations"][:11]]


def dots(ax, s=2.6):
    d = F.sample(frac=1, random_state=3)
    c = [ncol(n) if n in order else NCOL["Other"] for n in d.nation]
    ax.scatter(d.x, d.y, s=s, c=c, lw=0, zorder=4)


fig = plt.figure(figsize=(15, 9.5), dpi=200, facecolor=PAPER)
ax = fig.add_axes([0.0, 0.07, 0.56, 0.86]); antarctica(ax, claims=True, ext=3150); dots(ax)
ax.set_facecolor(SEA)
# region notes, on the sea
NOTES = [(-3000, 2350, "Antarctic Peninsula\nBritain, Bulgaria, USA,\nArgentina and Chile", "left"),
         (-600, 2850, "Dronning Maud Land\nNorway and Japan", "center"),
         (2950, -2600, "Australian Antarctic\nTerritory: Australia,\nRussia and the USA", "right"),
         (-2950, -1450, "Marie Byrd Land\n(unclaimed): USA", "left"),
         (-150, -2750, "Ross Dependency\nUSA and New Zealand", "center")]
for x, y, t, ha in NOTES:
    ax.text(x, y, t, fontsize=12.5, ha=ha, va="center", color=INK, zorder=7, linespacing=1.25,
            bbox=dict(boxstyle="round,pad=0.35", facecolor=PAPER, edgecolor="none", alpha=0.97))   # opaque: claim lines stop at the label
fig.text(0.585, 0.94, "Who named Antarctica?", fontproperties=DISP, fontsize=38, color=INK, va="top")
fig.text(0.585, 0.845, f"{R['source']['features']:,} place names in the SCAR Composite Gazetteer,\nby the nation that named each one and what it honours", fontsize=14, color=MUT, va="top", linespacing=1.35)
# big numbers
S = [(f"{R['us_uk_pct']:.0f}%", "named by the United States\nor the United Kingdom"),
     (f"{R['kind']['person']['pct_stated']:.0f}%", "of names with a recorded\nmeaning honour a person"),
     (f"{R['women']['pct_person']:.1f}%", "of the people honoured\nare women"),
     (f"{R['eras'][5]['pct']:.0f}%", "of dated names given\n1960 to 1979")]
for i, (b, s) in enumerate(S):
    x = 0.585 + (i % 2) * 0.205; y = 0.75 - (i // 2) * 0.125
    fig.text(x, y, b, fontproperties=DISP, fontsize=40, color=RED, va="top")
    fig.text(x, y - 0.065, s, fontsize=12, color=INK, va="top", linespacing=1.3)
# bars: features by nation
bx = fig.add_axes([0.66, 0.1, 0.31, 0.32]); bx.set_facecolor(PAPER)
rows = R["nations"][:11][::-1]
bx.barh([r["nation"] for r in rows], [r["n"] for r in rows], color=[ncol(r["nation"]) for r in rows], height=.72)
for i, r in enumerate(rows): bx.text(r["n"] + 70, i, f"{r['n']:,}", va="center", fontsize=11)
[bx.spines[s].set_visible(False) for s in ("top", "right", "bottom")]; bx.set_xticks([]); bx.tick_params(axis="y", labelsize=12)
bx.set_title("Features named, by nation\n(dot colours; grey: other or not known)", loc="left", fontsize=12, color=MUT, x=-0.27, pad=10)
fig.text(0.02, 0.018, SRC, fontsize=8.8, color=MUT)
fig.text(0.02, 0.045, "Polar stereographic projection. Dashed lines: national claims, frozen by the Antarctic Treaty. Each dot is a named feature.", fontsize=9.5, color=MUT)
out = os.path.join(HERE, "antarctica_names_collage.png")
fig.savefig(out, dpi=200, facecolor=PAPER); plt.close(fig)

# social card 1200 x 630
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=PAPER)
ax = fig.add_axes([0.52, 0.0, 0.48, 1.0]); antarctica(ax, claims=False, ext=3000); dots(ax, s=1.6)
fig.text(0.05, 0.86, "Who named", fontproperties=DISP, fontsize=50, color=INK, va="top")
fig.text(0.05, 0.69, "Antarctica?", fontproperties=DISP, fontsize=50, color=RED, va="top")
fig.text(0.05, 0.44, f"{R['us_uk_pct']:.0f}% named by the United States and Britain", fontsize=15, color=INK)
fig.text(0.05, 0.37, f"Only {R['women']['pct_person']:.1f}% of the people honoured are women", fontsize=15, color=INK)
fig.text(0.05, 0.30, f"{R['source']['features']:,} place names, mapped", fontsize=15, color=INK)
fig.text(0.05, 0.08, "Dr Tristan Hotham · maps.tristanhotham.com/antarctica-names", fontsize=11.5, color=MUT)
fig.savefig(os.path.join(ROOTD, "header.png"), dpi=100, facecolor=PAPER); plt.close(fig)
from PIL import Image
print(Image.open(out).size, Image.open(os.path.join(ROOTD, "header.png")).size)
