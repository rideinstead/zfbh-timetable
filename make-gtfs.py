"""Convert zfbh-timetable.json + stations.csv into a GTFS feed: dist/zfbh-gtfs.zip. Run: python make-gtfs.py

shortcut: no public-holiday exceptions (the site says some trains skip them but lists no dates), add
calendar_dates removals once ZFBH publishes the holiday list.
Assumption: the 2025/2026 timetable runs from the December 2025 change to the day before the December 2026 one
(second Sunday of December, the usual European date); the site states neither.
"""
import csv, datetime as dt, io, json, os, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
FEED_START, FEED_END = dt.date(2025, 12, 14), dt.date(2026, 12, 12)
DAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
FULL = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']   # GTFS calendar.txt column names

doc = json.load(open(os.path.join(HERE, 'zfbh-timetable.json'), encoding='utf-8'))
coords = {r['name']: r for r in csv.DictReader(open(os.path.join(HERE, 'stations.csv'), encoding='utf-8'))}
names = sorted({s['station'] for t in doc['trains'] for s in t['stops']})
assert all(n in coords for n in names), 'no coordinates for: %s' % ascii([n for n in names if n not in coords])
stop_id = {n: 'S%02d' % i for i, n in enumerate(names, 1)}


def d8(d): return d.strftime('%Y%m%d')
def iso(s): return dt.date.fromisoformat(s)
def hms(s): return s + ':00'


tables = {k: [] for k in ('agency', 'stops', 'routes', 'trips', 'stop_times', 'calendar', 'calendar_dates', 'feed_info')}
tables['agency'].append(dict(agency_id='ZFBH', agency_name='Zeljeznice Federacije BiH', agency_url='https://www.zfbh.ba',
                             agency_timezone='Europe/Sarajevo', agency_lang='bs'))
for n in names:
    tables['stops'].append(dict(stop_id=stop_id[n], stop_name=n, stop_lat=coords[n]['lat'], stop_lon=coords[n]['lon']))

services, routes = {}, {}
for t in doc['trains']:
    sv = t['service']
    key = json.dumps(sv, sort_keys=True)
    if key not in services:
        sid = 'SV%d' % (len(services) + 1)
        start, end = max(FEED_START, iso(sv.get('from', '2000-01-01'))), min(FEED_END, iso(sv.get('until', '2999-01-01')))
        services[key] = sid
        tables['calendar'].append({'service_id': sid, **{f: int(d in sv['days']) for d, f in zip(DAYS, FULL)},
                                   'start_date': d8(start), 'end_date': d8(end)})
        ex = sv.get('except')
        if ex:   # e.g. 2170/2171: daily, but not Fri-Sun in summer -> one removal per such date
            lo, hi = max(start, iso(ex['from'])), min(end, iso(ex['until']))
            for i in range((hi - lo).days + 1):
                day = lo + dt.timedelta(i)
                if DAYS[day.weekday()] in ex['days']:
                    tables['calendar_dates'].append(dict(service_id=sid, date=d8(day), exception_type=2))
    pair = tuple(sorted((t['from'], t['to'])))
    rk = (pair, t['rank'])
    if rk not in routes:
        routes[rk] = 'R%d' % (len(routes) + 1)
        tables['routes'].append(dict(route_id=routes[rk], agency_id='ZFBH', route_short_name='',   # names are over 12 chars; GTFS allows a long name alone
                                     route_long_name='%s (%s)' % (' - '.join(pair), t['rank']), route_type=2))
    tid = 'T' + t['train']
    tables['trips'].append(dict(route_id=routes[rk], service_id=services[key], trip_id=tid, trip_headsign=t['to'],
                                trip_short_name=t['train'], direction_id=int(t['from'] != pair[0])))
    for i, s in enumerate(t['stops'], 1):
        tables['stop_times'].append(dict(trip_id=tid, arrival_time=hms(s.get('arr') or s['dep']),
                                         departure_time=hms(s.get('dep') or s['arr']), stop_id=stop_id[s['station']],
                                         stop_sequence=i, timepoint=1))
tables['feed_info'].append(dict(feed_publisher_name='rideinstead (unofficial)', feed_publisher_url='https://github.com/rideinstead/zfbh-timetable',
                                feed_lang='bs', feed_contact_url='https://github.com/rideinstead/zfbh-timetable/issues', feed_start_date=d8(FEED_START), feed_end_date=d8(FEED_END), feed_version=d8(dt.date.today())))

# self-checks: ids resolve, times never go backwards inside a trip, coordinates sit in the Balkans
sids = {r['service_id'] for r in tables['calendar']}
assert all(t['service_id'] in sids and t['route_id'] in set(routes.values()) for t in tables['trips'])
last = {}
for r in tables['stop_times']:
    assert r['arrival_time'] <= r['departure_time'] and r['arrival_time'] >= last.get(r['trip_id'], '00:00:00'), r
    last[r['trip_id']] = r['departure_time']
assert all(42 < float(s['stop_lat']) < 46 and 15 < float(s['stop_lon']) < 20 for s in tables['stops'])
assert len(last) == len(doc['trains'])

os.makedirs(os.path.join(HERE, 'dist'), exist_ok=True)
with zipfile.ZipFile(os.path.join(HERE, 'dist', 'zfbh-gtfs.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
    for name, rows in tables.items():
        if rows:
            buf = io.StringIO()
            w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator='\n')
            w.writeheader(); w.writerows(rows)
            z.writestr(name + '.txt', buf.getvalue())
print({k: len(v) for k, v in tables.items()})
