# ŽFBH timetable (unofficial)

Stop-by-stop timetable of Željeznice Federacije BiH (Bosnia and Herzegovina), rebuilt from
<https://www.zfbh.ba/red-voznje/>, because the operator publishes no open GTFS feed.

- `zfbh-timetable.json`: 39 trains, 54 stations. Each train has its route, rank, service rules
  (days, date ranges, "not on weekends/public holidays") and a time at every stop.
- `zfbh-timetable.py`: rebuilds the JSON. The main table only lists termini; the script also
  queries the site's station-pair form (about 55 requests, paused between each) for intermediate stops.
  It checks that the rebuilt stops start and end at the main-table times.

## Read this first

- **Unofficial.** Not affiliated with ŽFBH. The timetable belongs to ŽFBH; check the source page before travelling.
- **Out of date by design.** The site labels it "2025/2026". Trains 390-393 ended 2026-06-25 and
  1390, 1391 and 2158 ended 2026-09-27. A December timetable change is expected; re-run the script then.
- Trains 390, 391, 392, 393, 1390, 1391 and 2158 have only their two termini (`termini_only`): the form returns no stops for them.
- Service rules are a reading of the site's footnotes. The site prints "25.06.2025" for trains 390 and 391; this repo
  treats it as a typo for 2026 (`date_as_printed` keeps the original).

Code: MIT (see `LICENSE`). Data: source is zfbh.ba; no licence is granted for it here.
