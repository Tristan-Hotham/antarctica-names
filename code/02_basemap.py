"""Step 2: the polar base map in EPSG:3031 (km), for the page and the figures.

Coast including the ice shelves: the ocean polygons of the OpenFreeMap vector tiles (OpenMapTiles 'water' layer, class
ocean; OpenStreetMap data, ODbL) at zoom 6 for every tile south of 60 S, decoded in memory; land = everything south of 60 S
that is not ocean. Grounded ice and rock: Natural Earth 1:50m land (public domain), whose Antarctic outline leaves out the
ice shelves, so ice shelves = OSM land minus Natural Earth land. Claims are sectors from the pole to 60 S (common.CLAIMS).
Outputs: data/base_land.geojson, data/base_shelves.geojson, data/base_claims.geojson, data/base_grat.geojson (EPSG:3031 km,
x east, y north) and WORK/base.pkl for the figures.
"""
import io, urllib.request, json, pickle, math
from concurrent.futures import ThreadPoolExecutor
import numpy as np, geopandas as gpd
import mapbox_vector_tile as mvt
from shapely.geometry import shape, Polygon, MultiPolygon, box, mapping, LineString, Point
from shapely.ops import unary_union, transform
from pyproj import Transformer
from common import *

UA = {"User-Agent": "antarctica-names-study/1.0 (research; maps.tristanhotham.com)"}
URL = json.load(urllib.request.urlopen(urllib.request.Request("https://tiles.openfreemap.org/planet", headers=UA)))["tiles"][0]
Z = 6; N = 2 ** Z


def lat_of(y):
    return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / N))))


def y_of(lat):
    return int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * N)


Y0 = y_of(-60.0)
tiles = [(x, y) for x in range(N) for y in range(Y0, N)]


def fetch(t):
    x, y = t
    for k in range(4):
        try:
            b = urllib.request.urlopen(urllib.request.Request(URL.format(z=Z, x=x, y=y), headers=UA), timeout=60).read()
            d = mvt.decode(b, default_options={"y_coord_down": True})
            out = []
            lay = d.get("water")
            ext = lay["extent"] if lay else 4096
            if lay:
                for f in lay["features"]:
                    if f["properties"].get("class") != "ocean": continue
                    g = shape(f["geometry"])
                    def tf(px, py, z=None):
                        lon = (x + np.asarray(px) / ext) / N * 360 - 180
                        yy = y + np.asarray(py) / ext
                        lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * yy / N))))
                        return lon, lat
                    out.append(transform(tf, g).buffer(0))
            return t, out
        except Exception as e:
            err = e
    raise err


with ThreadPoolExecutor(8) as ex:
    res = list(ex.map(fetch, tiles))
ocean = unary_union([g for _, gs in res for g in gs]).buffer(0)
south = box(-180, -85.0511, 180, -60)
land_ll = south.difference(ocean).union(box(-180, -90, 180, -85.0511)).buffer(0)
print("tiles", len(tiles), "ocean parts", sum(len(gs) for _, gs in res))

T = Transformer.from_crs(4326, 3031, always_xy=True)
proj = lambda g: transform(lambda a, b, c=None: tuple(np.asarray(v) / 1000 for v in T.transform(a, b)), g)


def densify(g, step=0.25):
    return g.segmentize(step)


land = proj(densify(land_ll)).buffer(0).simplify(1.0)
ne = gpd.read_file(f"{GEO}/ne_50m_land.geojson")
ne = ne[ne.bounds.maxy < -59]
ground = proj(densify(unary_union(ne.geometry).intersection(box(-180, -90, 180, -60)))).buffer(0).simplify(1.0)
shelves = land.difference(ground.buffer(0.5)).buffer(0)
shelves = MultiPolygon([p for p in (shelves.geoms if hasattr(shelves, "geoms") else [shelves]) if p.area > 30])
ground = ground.intersection(land.buffer(2)).buffer(0)
print("land km2 %.0f, grounded %.0f, shelves %.0f" % (land.area, ground.area, shelves.area))


def r2(g):
    return json.loads(json.dumps(mapping(g), default=float), parse_float=lambda s: round(float(s), 1))


def save(name, feats):
    jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/{name}.geojson")


save("base_land", [{"type": "Feature", "properties": {"k": "ground"}, "geometry": r2(ground)}])
save("base_shelves", [{"type": "Feature", "properties": {"k": "shelf"}, "geometry": r2(shelves)}])
claims = []
for nat, nm, a, b in CLAIMS + [("Unclaimed",) + UNCLAIMED]:
    lons = np.linspace(a, b, 60)
    ring = [(0.0, 0.0)] + [tuple(float(v) for v in np.asarray(T.transform(lo, -60.0)) / 1000) for lo in lons] + [(0.0, 0.0)]
    claims.append({"type": "Feature", "properties": {"nation": nat, "name": nm, "w": a, "e": b},
                   "geometry": r2(Polygon(ring))})
save("base_claims", claims)
grat = []
for la in (-60, -65, -70, -75, -80, -85):
    pts = [tuple(float(v) for v in np.asarray(T.transform(lo, la)) / 1000) for lo in np.linspace(-180, 180, 181)]
    grat.append({"type": "Feature", "properties": {"lat": la}, "geometry": r2(LineString(pts))})
for lo in range(-180, 180, 30):
    pts = [tuple(float(v) for v in np.asarray(T.transform(lo, la)) / 1000) for la in np.linspace(-60, -89.5, 40)]
    grat.append({"type": "Feature", "properties": {"lon": lo}, "geometry": r2(LineString(pts))})
save("base_grat", grat)
pickle.dump({"land": land, "ground": ground, "shelves": shelves}, open(f"{WORK}/base.pkl", "wb"))
for n in ("base_land", "base_shelves", "base_claims", "base_grat"):
    print(n, os.path.getsize(f"{DATA}/{n}.geojson") // 1024, "KB")
