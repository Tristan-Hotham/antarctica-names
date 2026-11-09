"""Step 6: the paper. Fills code/paper_template.tex from data/results.json, adds tables and compiles with xelatex.
Output: release/paper/Hotham_Antarctica_Names.pdf and .tex beside the f_*.png figures. The DOI is a placeholder (https://doi.org/10.5281/zenodo.24075309)
unless the environment variable DOI is set (DOI=10.5281/zenodo.N python3 06_paper.py), as the publisher does."""
import subprocess
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Antarctica_Names"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")
F = pd.read_csv(f"{DATA}/features.csv", keep_default_na=False, na_values=[""])

# statements made in words in the paper only
fr = F[F.nation == "France"]
assert (fr.lon.between(-80, -55)).mean() > 0.4                               # Charcot's Peninsula names
NN = R["nation_n"]; H = R["home_n"]
assert NN["France"]["own_claim_pct"] < 50
assert H["Norway"]["home_pct"] > H["United States"]["home_pct"] > H["United Kingdom"]["home_pct"] > H["Australia"]["home_pct"]
E = [e for e in R["women"]["by_era"] if e["persons"] >= 100]
assert min(E, key=lambda e: e["pct"])["label"] == "1960 to 1979" == R["women"]["by_era"][5]["label"]
assert R["eras"][5]["top"][0]["nation"] == "United States"
assert R["nations"][2]["nation"] == "Norway" and R["nations"][6]["nation"] == "Russia"


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "pc": return f"{round(float(v))}\\%"
    return tex(str(v))


rows = "".join(f"{tex(g['gaz'])} & {g['n']:,} & {g['only']:,}\\\\\n" for g in R["gaz"][:16])
TG = ("\\begin{table}[tbp]\\centering\\small\\caption{Names in each national gazetteer of the SCAR Composite Gazetteer, and features listed only there "
      "(the sixteen largest lists).}\\label{tab:gaz}\\begin{tabular}{lrr}\\toprule Gazetteer & Names & Only in this list\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
lab = {"narrative": "Naming statement names the namer", "only gazetteer": "Only one national list holds it", "discoverer": "Expedition said to have discovered or charted it",
       "earliest approval": "Earliest approval date", "override": "Corrected by hand"}
src = R["source"]["nation_src"]
rows = "".join(f"{lab[k]} & {v:,} & {100 * v / R['source']['features']:.1f}\\\\\n" for k, v in src.items() if k in lab) + f"Not known & {R['not_known']:,} & {100 * R['not_known'] / R['source']['features']:.1f}\\\\\n"
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{How the naming nation was decided.}\\label{tab:src}\\begin{tabular}{lrr}\\toprule Rule & Features & \\%\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
f1 = lambda v: "" if v is None else f"{v:.1f}"
rows = "".join(f"{tex(n['nation'])} & {n['n']:,} & {n['pct']:.1f} & {f1(n['person_pct'])} & {f1(n['descriptive_pct'])} & {f1(n['place_pct'])} & {n['year_median'] or ''} & {f1(n.get('own_claim_pct'))}\\\\\n" for n in R["nations"][:15])
TN = ("\\begin{table}[tbp]\\centering\\small\\caption{The fifteen leading naming nations: features, share of all features, shares (of features with a recorded meaning) "
      "named after a person, descriptive and after a place elsewhere, median naming year, and share of the nation's names inside its own claim.}\\label{tab:nations}"
      "\\begin{tabular}{lrrrrrrr}\\toprule Nation & Features & \\% & Person & Descr. & Place & Year & In claim\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(e['label'])} & {e['n']:,} & {e['pct']:.1f} & {tex(', '.join(t['nation'] for t in e['top']))}\\\\\n" for e in R["eras"])
TE = ("\\begin{table}[tbp]\\centering\\small\\caption{Dated features by period of naming, with the three leading naming nations.}\\label{tab:eras}"
      "\\begin{tabular}{lrrl}\\toprule Period & Features & \\% & Leading nations\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")

t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("\\url{{{meta.page}}}", "\\url{%s}" % PAGE).replace("\\url{{{meta.repo}}}", "\\url{%s}" % REPO)
t = t.replace("{{AI}}", AI)
for k, v in (("GAZ", TG), ("SRC", TS), ("NATIONS", TN), ("ERAS", TE)):
    t = t.replace("{{TABLE_%s}}" % k, v)
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
DOI = os.environ.get("DOI")
t = t.replace("https://doi.org/10.5281/zenodo.24055580", f"\\url{{https://doi.org/{DOI}}}" if DOI else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:4]
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:10])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–") + txt.count("--"), "DOI_URL shown:", "https://doi.org/10.5281/zenodo.24075309" in txt)
