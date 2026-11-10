#!/usr/bin/env python3
"""生産者・ショップのページの下地になる地図（assets/maps/japan.svg, world.svg）を作る。

    python3 tools/make_maps.py <ne_10m_admin_1_states_provinces.geojson> <ne_50m_admin_0_countries.geojson>

地図データは Natural Earth（パブリックドメイン）。リポジトリには入れず、作り直すときだけ取ってくる:
  https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson
  https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson
図法と範囲は tools/build_posts.py の MAPS と同じものを使う（ピンの位置がずれないように）。
地図そのものは一度作れば変わらない。生産者やショップが増えても、作り直すのはピンだけ（build_posts.py）。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_posts import MAPS, ROOT, project  # noqa: E402

OUT = ROOT / "assets" / "maps"
LAND, EDGE, JAPAN_TINT = "#e2ddca", "#faf8f1", "#c9d6bd"


def rings(geom):
    if geom["type"] == "Polygon":
        return geom["coordinates"]
    if geom["type"] == "MultiPolygon":
        return [r for poly in geom["coordinates"] for r in poly]
    return []


def simplify(pts, tol):
    """閉じた輪を、始点から一番遠い点で2本に割ってから間引く（始点と終点が同じだと線にならないため）。"""
    if len(pts) < 4:
        return pts
    x0, y0 = pts[0]
    k = max(range(len(pts)), key=lambda i: (pts[i][0] - x0) ** 2 + (pts[i][1] - y0) ** 2)
    if k in (0, len(pts) - 1):
        return pts
    return _dp(pts[: k + 1], tol)[:-1] + _dp(pts[k:], tol)


def _dp(pts, tol):
    """Douglas-Peucker（投影後のピクセル座標で）。"""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (x1, y1), (x2, y2) = pts[a], pts[b]
        dx, dy = x2 - x1, y2 - y1
        n = (dx * dx + dy * dy) ** 0.5 or 1e-9
        best, idx = 0.0, None
        for i in range(a + 1, b):
            x0, y0 = pts[i]
            d = abs(dy * x0 - dx * y0 + x2 * y1 - y2 * x1) / n
            if d > best:
                best, idx = d, i
        if idx is not None and best > tol:
            keep[idx] = True
            stack += [(a, idx), (idx, b)]
    return [p for p, k in zip(pts, keep) if k]


def area(pts):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]))) / 2


def path(ring_list, m, tol, min_area, lat_split=None):
    out = []
    for ring in ring_list:
        if lat_split is not None:
            # 沖縄・奄美は囲みへ、それ以外は本図へ（リングの中心の緯度で振り分け）
            clat = sum(p[1] for p in ring) / len(ring)
            clng = sum(p[0] for p in ring) / len(ring)
            inset = m.get("inset")
            in_inset = inset and clat < inset["lat_max"] and clng < inset["lng_max"]
            if lat_split != in_inset:
                continue
        pts = [project(m, lat, lng) for lng, lat in ring]
        pts = simplify(pts, tol)
        if len(pts) < 3 or area(pts) < min_area:
            continue
        if not any(-20 <= x <= m["w"] + 20 and -20 <= y <= m["h"] + 20 for x, y in pts):
            continue
        out.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z")
    return "".join(out)


def japan(admin1):
    m = MAPS["japan"]
    feats = [f for f in json.loads(Path(admin1).read_text())["features"] if f["properties"].get("adm0_a3") == "JPN"]
    main = "".join(path(rings(f["geometry"]), m, 0.7, 6, lat_split=False) for f in feats)
    ins = "".join(path(rings(f["geometry"]), m, 0.7, 3, lat_split=True) for f in feats)
    i = m["inset"]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {m["w"]} {m["h"]}" role="img" aria-label="Map of Japan">'
           f'<path fill="{LAND}" stroke="{EDGE}" stroke-width="1" stroke-linejoin="round" d="{main}"/>'
           f'<rect x="{i["x"]}" y="{i["y"]}" width="{i["w"]}" height="{i["h"]}" fill="none" stroke="#cfc8b3" stroke-width="1.2" stroke-dasharray="5 5" rx="6"/>'
           f'<path fill="{LAND}" stroke="{EDGE}" stroke-width="1" stroke-linejoin="round" d="{ins}"/></svg>')
    return svg


def world(countries):
    m = MAPS["world"]
    feats = [f for f in json.loads(Path(countries).read_text())["features"] if f["properties"].get("ADM0_A3") != "ATA"]
    other = "".join(path(rings(f["geometry"]), m, 0.35, 0.6) for f in feats if f["properties"].get("ADM0_A3") != "JPN")
    jp = "".join(path(rings(f["geometry"]), m, 0.2, 0.05) for f in feats if f["properties"].get("ADM0_A3") == "JPN")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {m["w"]} {m["h"]}" role="img" aria-label="World map">'
            f'<path fill="{LAND}" stroke="{EDGE}" stroke-width=".5" stroke-linejoin="round" d="{other}"/>'
            f'<path fill="{JAPAN_TINT}" stroke="{EDGE}" stroke-width=".4" d="{jp}"/></svg>')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, svg in (("japan", japan(sys.argv[1])), ("world", world(sys.argv[2]))):
        f = OUT / f"{name}.svg"
        f.write_text(svg, encoding="utf-8")
        print("wrote", f.relative_to(ROOT), f"{len(svg)//1024} KB")


if __name__ == "__main__":
    main()
