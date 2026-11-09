"""Step 7: blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.24075309, https://doi.org/10.5281/zenodo.24075309 and https://blog.tristanhotham.com/2026/10/31/antarctica-names/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Antarctica_Names"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}

# facts in words in the blog and its alt text
assert 3.0 < R["women"]["pct_person"] < 3.6                                              # about one in thirty
assert all(6 <= n["pct"] < 8 for n in R["nations"][2:7])                                 # between 6 and 8 per cent
assert all(c["top"][0]["nation"] == "United Kingdom" and c["top"][0]["pct"] > 33.3 for c in R["claims"] if c["claim"] in ("Chile", "United Kingdom", "Argentina"))
dec = {int(k): v for k, v in R["decades"].items()}
assert all(1200 <= dec[d] <= 2100 for d in (1970, 1980, 1990, 2000, 2010))
assert R["eras"][5]["top"][0]["nation"] == "United States"
assert [s["surname"] for s in R["surnames"][:5]] == ["Smith", "Davis", "Brown", "Johnson", "Wilson"]

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = fill(post, R)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u_), post, re.M) for u_ in used) and "wp:image" not in post
from PIL import Image
for img in used:
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used: os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Who named Antarctica? Twenty thousand place names, the nations that gave them and the people they honour",
        "slug": "antarctica-names",
        "excerpt": f"I mapped {R['source']['features']:,} Antarctic place names by who named them, when and after whom. America and Britain named {R['us_uk_pct']:.0f}% of the continent, and only {R['women']['pct_person']:.1f}% of the people honoured are women.",
        "seo_description": f"Who named Antarctica? {R['source']['features']:,} place names mapped by naming nation, decade and namesake. The US and UK named {R['us_uk_pct']:.0f}%.",
        "tags": ["maps", "Antarctica", "place names", "toponymy", "SCAR", "Wikidata", "data visualisation", "polar history", "geography"],
        "header_alt": f"Title card reading 'Who named Antarctica?' in black and red on parchment, beside a polar map of Antarctica dotted in the colours of the nations that named each feature, with the lines '{R['us_uk_pct']:.0f}% named by the United States and Britain' and 'Only {R['women']['pct_person']:.1f}% of the people honoured are women'."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z): os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(os.path.join(ROOT, "code"))):
        if fn.endswith(".pyc") or fn == "__pycache__": continue
        z.write(os.path.join(ROOT, "code", fn), f"{SLUG}/code/{fn}")
    for fn in sorted(os.listdir(DATA)):
        z.write(os.path.join(DATA, fn), f"{SLUG}/data/{fn}")
    for fn in ("README.md", "LICENSE", "index.html"):
        z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), f"{SLUG}/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("{\\textendash}", "")
ab = re.sub(r"\\textit\{([^}]*)\}", r"\1", ab)
zmeta = {"title": "Who Named Antarctica? The Nations, Years and People behind Twenty Thousand Antarctic Place Names",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/antarctica-names/}}.</p><p>Sources: SCAR Composite Gazetteer of Antarctica (Australian Antarctic Data Centre, CC BY 4.0); Wikidata (CC0), queried with QLever; Natural Earth (public domain); OpenStreetMap (ODbL) via OpenFreeMap. Derived data and text CC BY 4.0, code MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["Antarctica", "toponymy", "place names", "gazetteer", "SCAR", "territorial claims", "commemoration", "Wikidata", "maps", "open data"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://www.wikidata.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
