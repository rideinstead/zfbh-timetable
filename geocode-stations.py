"""One-off: find coordinates for every station in zfbh-timetable.json via OpenStreetMap Nominatim.

Writes stations.csv (name,lat,lon,osm). Only OSM railway station/halt hits inside Bosnia count;
anything else is printed as UNMATCHED and left for a hand-edit of stations.csv.
Coordinates (c) OpenStreetMap contributors, ODbL. Run: python geocode-stations.py
"""
import csv, json, os, time, unicodedata, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
BOX = {'ba': (42.4, 45.3, 15.7, 19.7), 'hr': (42.8, 43.2, 17.2, 17.7)}   # sanity boxes: Bosnia; Ploce (not in the site's station list)


def fold(s):   # Ilidža -> Ilidza: OSM often carries the plain-ASCII or another spelling
    return unicodedata.normalize('NFKD', s.replace('đ', 'dj').replace('Đ', 'Dj')).encode('ascii', 'ignore').decode()


HINT = {'Gora': 'Gora Zenica'}   # plain 'Gora' finds a different halt 78 km away (caught by a speed check, see README)


def lookup(name, cc):
    for q in (HINT.get(name, name), name, fold(name), name + ' railway station', fold(name) + ' railway station', name + ' željeznička stanica'):   # bare name usually matches OSM best
        qs = urllib.parse.urlencode({'q': q, 'countrycodes': cc, 'format': 'json', 'limit': 8})
        req = urllib.request.Request('https://nominatim.openstreetmap.org/search?' + qs, headers={'User-Agent': 'zfbh-timetable/0.1'})
        res = json.load(urllib.request.urlopen(req, timeout=30))
        time.sleep(1.2)   # Nominatim policy: at most 1 request per second
        for r in res:
            lat, lon = float(r['lat']), float(r['lon'])
            s, n, w, e = BOX[cc]
            if r['class'] == 'railway' and r['type'] in ('station', 'halt') and s <= lat <= n and w <= lon <= e:
                return lat, lon, r['osm_type'] + '/' + str(r['osm_id'])


doc = json.load(open(os.path.join(HERE, 'zfbh-timetable.json'), encoding='utf-8'))
names = sorted({s['station'] for t in doc['trains'] for s in t['stops']})
rows, missing = [], []
for n in names:
    hit = lookup(n, 'hr' if n == 'Ploče' else 'ba')
    (rows.append((n, *hit)) if hit else missing.append(n))
with open(os.path.join(HERE, 'stations.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f); w.writerow(['name', 'lat', 'lon', 'osm']); w.writerows(rows)
print(len(rows), 'of', len(names), 'stations found')
print('UNMATCHED:', ascii(missing))
