# ŽFBH timetable (unofficial)

Stop-by-stop timetable of Željeznice Federacije BiH (Bosnia and Herzegovina), rebuilt from
<https://www.zfbh.ba/red-voznje/>, because the operator publishes no GTFS. A community feed (`ba_ZFBiH` on Transitous, ŽFBH and Željeznice RS) exists but covers 2025 only and ended 2025-12-13; this repo has the 2025/2026 ŽFBH timetable (ŽRS is not covered).

- `zfbh-timetable.json`: 39 trains, 54 stations. Each train has its route, rank, service rules
  (days, date ranges, "not on weekends/public holidays") and a time at every stop.
- `zfbh-timetable.py`: rebuilds the JSON. The main table only lists termini; the script also
  queries the site's station-pair form (about 55 requests, paused between each) for intermediate stops.
  It checks that the rebuilt stops start and end at the main-table times.

## GTFS

[`zfbh-gtfs.zip`](https://github.com/rideinstead/zfbh-timetable/releases/latest/download/zfbh-gtfs.zip) (attached to the latest [release](https://github.com/rideinstead/zfbh-timetable/releases)) is the same data as a GTFS feed (40 stops, 7 routes, 39 trips). Rebuild it with
`python geocode-stations.py` (once, writes `stations.csv`) and `python make-gtfs.py` (writes `dist/zfbh-gtfs.zip`).

- Stop coordinates come from OpenStreetMap via Nominatim, matched by name to railway stations/halts
  (c) OpenStreetMap contributors, [ODbL](https://www.openstreetmap.org/copyright). Spot-check them before relying on them.
- Validity is an **assumption**: from 2025-12-14 to 2026-12-12 (the December timetable changes, second Sunday).
  The site states no dates beyond its footnotes.
- No public-holiday exceptions: the site says some trains skip holidays but gives no dates.
- Times are one value per stop (the site gives no dwell times). Trains 390-393, 1390, 1391 and 2158 have only two stops.
- Cross-check against the community feed: 29 of the 39 trains match exactly on first departure and last arrival. The other 10 (390, 392, 393, 720, 721, 2158, 2170, 2171, 2412, 2413) differ from that 2025 feed; I could not tell whether those are 2026 changes or errors here.
- Validated with the MobilityData GTFS validator 8.0.1: no errors. Remaining warnings: four services have already ended and the feed ends within 30 days (both expected).
- Coordinates were checked by the speed a train would need between consecutive stops, not on a map: one wrong match (Gora) was caught and fixed; no segment now implies over 110 km/h.

## Read this first

- **Unofficial.** Not affiliated with ŽFBH. The timetable belongs to ŽFBH; check the source page before travelling.
- **Out of date by design.** The site labels it "2025/2026". Trains 390-393 ended 2026-06-25 and
  1390, 1391 and 2158 ended 2026-09-27. A December timetable change is expected; re-run the script then.
- Trains 390, 391, 392, 393, 1390, 1391 and 2158 have only their two termini (`termini_only`): the form returns no stops for them.
- Service rules are a reading of the site's footnotes. The site prints "25.06.2025" for trains 390 and 391; this repo
  treats it as a typo for 2026 (`date_as_printed` keeps the original).

Code: MIT (see `LICENSE`). Timetable data: source is zfbh.ba; no licence is granted for it here. Coordinates: ODbL (OpenStreetMap).
