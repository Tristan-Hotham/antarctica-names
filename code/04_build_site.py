"""Step 4: build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json (embedded in the page); features and people (data/site.json) and the base maps load when the page opens.
Facts stated in words are checked here. 10.5281/zenodo.24075309, https://doi.org/10.5281/zenodo.24075309 and https://blog.tristanhotham.com/2026/10/31/antarctica-names/ stay as placeholders for the publisher.
Also writes data/world.geojson (Natural Earth 1:50m countries, simplified) for the birthplace map."""
import json
import pandas as pd, geopandas as gpd
from common import *

R = jload(f"{DATA}/results.json")
F = pd.read_csv(f"{DATA}/features.csv", keep_default_na=False, na_values=[""])
NN = R["nation_n"]

# facts stated in words (page, blog, paper, collage, post)
assert [n["nation"] for n in R["nations"][:7]] == ["United States", "United Kingdom", "Norway", "Bulgaria", "Australia", "New Zealand", "Russia"]
assert R["gaz"][2]["gaz"] == "Russia"
assert NN["Argentina"]["own_claim_pct"] > NN["Australia"]["own_claim_pct"] > NN["Norway"]["own_claim_pct"] > 70
assert R["claim_n"]["Australia"]["own_pct"] < 50 and R["claim_n"]["Norway"]["own_pct"] < 60 and R["claim_n"]["Norway"]["own_pct"] > 50
assert R["claim_n"]["New Zealand"]["top"][0]["nation"] == "United States" and R["claim_n"]["Unclaimed"]["top"][0]["nation"] == "United States"
assert R["claim_n"]["Argentina"]["top"][0]["nation"] == "United Kingdom"
assert R["nation_n"]["Argentina"]["own_claim_pct"] < 99.95   # shown to one decimal, never as 100%
assert R["eras"][1]["label"].startswith("Heroic") and R["eras"][5]["label"] == "1960 to 1979" and R["eras"][5]["pct"] == max(e["pct"] for e in R["eras"])
assert R["peak_decade"] == 1960 and 45 < R["bulg_since2000_pct"] < 55
assert 40 < 100 * R["eras"][5]["top"][0]["n"] / R["eras"][5]["n"] < 50 and 40 < 100 * R["dec_nation"]["United States"]["1960"] / R["decades"]["1960"] < 50   # "nearly half"
K = R["kind"]
assert K["person"]["pct_stated"] > 50 and K["descriptive"]["pct_stated"] > K["place"]["pct_stated"] > K["association"]["pct_stated"] > K["ship"]["pct_stated"]
assert NN["Norway"]["descriptive_pct"] > 60 and NN["Japan"]["descriptive_pct"] > 80 and NN["Bulgaria"]["place_pct"] > 50
assert {"Skakktoppen", "Mikazuki Iwa", "Bellingshausenhavet"} <= set(F.name) | set(n.strip() for x in F.names for n in re.findall(r"([^|(]+?) \(", x))
assert [s["surname"] for s in R["surnames"][:5]] == ["Smith", "Davis", "Brown", "Johnson", "Wilson"]
assert R["roles"]["United States"]["military"]["pct"] > 25 and R["roles"]["Australia"]["support"]["pct"] > 20
assert R["roles"]["Bulgaria"]["royal"]["pct"] > 15 and R["roles"]["Bulgaria"]["arts"]["pct"] > 10
P = R["people"]
assert [t["country"] for t in P["top"][:4]] == ["United Kingdom", "United States", "France", "Norway"]
assert [t["name"] for t in P["top_people"][:3]] == ["Roald Amundsen", "Ernest Shackleton", "Douglas Mawson"] and P["top_people"][1]["n"] == P["top_people"][2]["n"]
assert P["cont"]["Oceania"]["n"] > P["cont"]["Asia"]["n"] > P["cont"]["South America"]["n"] > P["cont"]["Africa"]["n"]
assert R["home_n"]["United Kingdom"]["home_pct"] < 50 < R["home_n"]["Norway"]["home_pct"]
W = R["women"]
assert {"Queen Maud Land", "Victoria Land", "Marie Byrd Land", "Ronne Ice Shelf"} <= set(W["big"])
assert 60 < W["pre1990_rel_pct"] < 66.7 and W["post1990_rel_pct"] < 20          # "nearly two in three", "only ..."
wn = F[F.woman == 1]
assert {"Palais Glacier", "Bradshaw Peak"} <= set(wn[wn.year >= 1990].name)
assert R["different"]["by_gaz"]["Argentina"] + R["different"]["by_gaz"]["Chile"] > R["different"]["n"] / 2   # mostly the Peninsula


def world():
    g = gpd.read_file(f"{GEO}/ne_50m_admin_0_countries.geojson")[["ADMIN", "geometry"]]
    g = g[g.ADMIN != "Antarctica"]
    g["geometry"] = g.geometry.simplify(0.08)
    js = json.loads(g.to_json())
    def rnd(c):
        return [rnd(x) for x in c] if isinstance(c[0], list) else [round(c[0], 2), round(c[1], 2)]
    for f in js["features"]:
        f["geometry"]["coordinates"] = rnd(f["geometry"]["coordinates"]); f["properties"] = {"n": f["properties"]["ADMIN"]}; f.pop("id", None); f.pop("bbox", None)
    jsave(js, f"{DATA}/world.geojson")


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = fill(tpl, R)
    left = set(re.findall(r"\{\{[^}]*\}\}", html))
    assert left <= {"10.5281/zenodo.24075309", "https://doi.org/10.5281/zenodo.24075309", "https://blog.tristanhotham.com/2026/10/31/antarctica-names/"}, left
    slim = {k: R[k] for k in R if k not in ("dec_nation_full",)}
    html = html.replace("/*RESULTS*/", json.dumps(slim, ensure_ascii=False, separators=(",", ":")))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv", "Civil Serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    world()
    build()
