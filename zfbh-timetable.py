"""Hand-made timetable for Zeljeznice FBiH (Bosnia). The only open GTFS (community, Transitous ba_ZFBiH) ended 2025-12-13.

Scrapes https://www.zfbh.ba/red-voznje/: the main table (termini only) plus the
station-pair form (POST redvoznje_pol / redvoznje_dol), which returns the times at
intermediate stops. Writes zfbh-timetable.json. Run: python zfbh-timetable.py
Re-run after every timetable change (mid-December); the site says "2025/2026".
shortcut: service rules below are typed from the site's footnotes, check them when the page changes.
"""
import html, json, os, re, time, urllib.parse, urllib.request

URL = 'https://www.zfbh.ba/red-voznje/'
HUB = 'Sarajevo'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zfbh-timetable.json')
SUMMER = {'from': '2026-06-26', 'until': '2026-09-27'}
FRI_SUN = ['fri', 'sat', 'sun']
WEEKDAYS = ['mon', 'tue', 'wed', 'thu', 'fri']
ALL = WEEKDAYS + ['sat', 'sun']


def post(a=None, b=None):
    data = urllib.parse.urlencode({'redvoznje_pol': a, 'redvoznje_dol': b}).encode() if a else None
    req = urllib.request.Request(URL, data=data, headers={'User-Agent': 'Mozilla/5.0'})
    return urllib.request.urlopen(req, timeout=30).read().decode('utf-8')


def rows(page):
    """(train, from, to, dep, arr) from every result row; the number may carry footnote stars."""
    out = []
    for r in re.findall(r"<tr class='relacija'>(.*?)(?=<tr|</table>)", page, re.S):
        c = [html.unescape(re.sub(r'<[^>]+>', '', x)).strip() for x in re.findall(r'<td>(.*?)</td>', r, re.S)]
        if len(c) == 5:
            out.append(c)
    return out


def hhmm(s):
    h, m = s.split(':')
    return '%02d:%02d' % (int(h), int(m))


def service(no, stars):
    if no in ('390', '391'):   # site prints "do 25.06.2025": same footnote as 392/393, so almost certainly 2026
        return {'days': ['sun'], 'until': '2026-06-25', 'date_as_printed': '25.06.2025'}
    if no == '392': return {'days': ['sat'], 'until': '2026-06-25'}
    if no == '393': return {'days': ['fri'], 'until': '2026-06-25'}
    if stars in ('**', '****'): return {'days': FRI_SUN, **SUMMER}
    if stars == '***': return {'days': WEEKDAYS, 'no_public_holidays': True}
    if stars == '*****': return {'days': ALL, 'except': {'days': FRI_SUN, **SUMMER}}
    if stars == '******': return {'days': [d for d in ALL if d != 'sat']}
    if stars == '*******': return {'days': [d for d in ALL if d != 'sun']}
    return {'days': ALL}


main = post()
stations = [html.unescape(s).strip() for s in re.findall(r'<option>(.*?)</option>', main.split('redvoznje_dol')[0])]
trains = {}
# main table rows have an <i> icon-free first cell: number, rank, route, dep, arr
for r in re.findall(r'<tr[^>]*>(.*?)</tr>', main, re.S):
    c = [html.unescape(re.sub(r'<[^>]+>', '', x)).strip() for x in re.findall(r'<td[^>]*>(.*?)</td>', r, re.S)]
    mm = re.fullmatch(r'(\d+)(\**)', c[0]) if len(c) == 5 else None
    if not mm or not re.fullmatch(r'\d?\d:\d\d', c[3]):
        continue
    no, stars = mm.groups()
    a, b = [x.strip() for x in re.split(r'\s[-\u2013]\s', c[2])]
    trains[no] = {'train': no, 'rank': c[1], 'from': a, 'to': b, 'service': service(no, stars),
                  'terminus_times': [hhmm(c[3]), hhmm(c[4])], 'stops': {}}
assert trains and len(trains) == main.count('<tr><td>'), 'main table rows lost: %d parsed' % len(trains)

pairs = [(s, HUB) for s in stations if s != HUB] + [('Maglaj', 'Zenica')]   # Maglaj-Zenica trains (2101/2102) skip Sarajevo
for a, b in pairs:
    for no, f, t, dep, arr in rows(post(a, b)):
        no = no.rstrip('*')
        if no in trains:
            trains[no]['stops'].setdefault(f, {})['dep'] = hhmm(dep)
            trains[no]['stops'].setdefault(t, {})['arr'] = hhmm(arr)
    time.sleep(0.4)

for t in trains.values():
    if not t['stops']:   # the form returned nothing for this train: keep the two termini from the main table, flagged
        t['stops'] = [{'station': t['from'], 'dep': t['terminus_times'][0]}, {'station': t['to'], 'arr': t['terminus_times'][1]}]
        t['termini_only'] = True
        print('termini only:', t['train'], ascii(t['from']), '-', ascii(t['to']))
        continue
    t['stops'] = [{'station': s, **v} for s, v in sorted(t['stops'].items(), key=lambda kv: kv[1].get('dep') or kv[1]['arr'])]
    first, last = t['stops'][0], t['stops'][-1]
    got = [first.get('dep'), last.get('arr')]
    # self-check: stops rebuilt from the form must start/end at the main-table times (Ploce is outside the station list)
    if 'Ploče' not in (t['from'], t['to']):
        assert got == t['terminus_times'], (t['train'], got, t['terminus_times'])

doc = {'source': URL, 'operator': 'Zeljeznice Federacije BiH', 'timetable': '2025/2026 (as labelled on the site)',
       'days': ALL, 'trains': sorted(trains.values(), key=lambda t: int(t['train']))}
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(doc, f, ensure_ascii=False, indent=1)
print('wrote', OUT, len(trains), 'trains', len(stations), 'stations')
