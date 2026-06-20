"""
ZYNORIQ — per-state draw schedule (times-of-day + clock times) and helpers
to figure out, right now, which session ("Matin"/"Midi"/"Soir"/"Nuit" etc.)
is the next one coming up for a given state.

Used by app.py (for the home page snapshot / schedule-check) and by
seo_pages.py (so the /predictions/<state> page can base its "last draw" and
suggestions on the session that's actually coming up next, instead of just
the most recent draw overall).
"""
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

DRAW_SCHEDULE = {
    "AR": [{"tod":"Midday","time":"12:59 PM CT"}, {"tod":"Evening","time":"6:59 PM CT"}],
    "AZ": [{"tod":"Evening","time":"7:00 PM MST"}],
    "CA": [{"tod":"Midday","time":"1:00 PM PT"},  {"tod":"Evening","time":"6:30 PM PT"}],
    "CO": [{"tod":"Midday","time":"1:30 PM MT"}, {"tod":"Evening","time":"7:30 PM MT"}],
    "CT": [{"tod":"Midday","time":"1:57 PM ET"},  {"tod":"Night","time":"10:29 PM ET"}],
    "DC": [{"tod":"Midday","time":"1:50 PM ET"}, {"tod":"Evening","time":"7:50 PM ET"}, {"tod":"Night","time":"11:30 PM ET"}],
    "DE": [{"tod":"Midday","time":"1:58 PM ET"},  {"tod":"Night","time":"7:57 PM ET"}],
    "FL": [{"tod":"Midday","time":"1:30 PM ET"},  {"tod":"Evening","time":"9:45 PM ET"}],
    "GA": [{"tod":"Midday","time":"12:29 PM ET"}, {"tod":"Evening","time":"6:59 PM ET"}, {"tod":"Night","time":"11:34 PM ET"}],
    "IA": [{"tod":"Midday","time":"12:20 PM CT"}, {"tod":"Evening","time":"10:00 PM CT"}],
    "ID": [{"tod":"Midday","time":"1:59 PM MT"}, {"tod":"Night","time":"7:59 PM MT"}],
    "IL": [{"tod":"Midday","time":"12:40 PM CT"}, {"tod":"Evening","time":"9:22 PM CT"}],
    "IN": [{"tod":"Midday","time":"1:20 PM ET"},  {"tod":"Evening","time":"11:00 PM ET"}],
    "KS": [{"tod":"Midday","time":"1:10 PM CT"}, {"tod":"Evening","time":"9:10 PM CT"}],
    "KY": [{"tod":"Midday","time":"1:20 PM ET"}, {"tod":"Evening","time":"11:00 PM ET"}],
    "LA": [{"tod":"Evening","time":"9:59 PM CT"}],
    "MA": [{"tod":"Midday","time":"2:00 PM ET"},  {"tod":"Night","time":"9:00 PM ET"}],
    "MD": [{"tod":"Midday","time":"12:27 PM ET"}, {"tod":"Evening","time":"7:56 PM ET"}],
    "ME": [{"tod":"Midday","time":"1:10 PM ET"}, {"tod":"Evening","time":"6:50 PM ET"}],
    "MI": [{"tod":"Midday","time":"12:59 PM ET"}, {"tod":"Evening","time":"7:29 PM ET"}],
    "MN": [{"tod":"Evening","time":"6:17 PM CT"}],
    "MO": [{"tod":"Midday","time":"12:45 PM CT"}, {"tod":"Evening","time":"8:59 PM CT"}],
    "MS": [{"tod":"Midday","time":"2:30 PM CT"}, {"tod":"Evening","time":"9:30 PM CT"}],
    "NC": [{"tod":"Midday","time":"3:00 PM ET"},  {"tod":"Evening","time":"11:22 PM ET"}],
    "NE": [{"tod":"Evening","time":"9:59 PM CT"}],
    "NH": [{"tod":"Midday","time":"1:10 PM ET"}, {"tod":"Evening","time":"6:55 PM ET"}],
    "NJ": [{"tod":"Midday","time":"12:59 PM ET"}, {"tod":"Evening","time":"10:57 PM ET"}],
    "NM": [{"tod":"Midday","time":"1:00 PM MT"}, {"tod":"Evening","time":"9:30 PM MT"}],
    "NY": [{"tod":"Midday","time":"2:30 PM ET"},  {"tod":"Evening","time":"10:30 PM ET"}],
    "OH": [{"tod":"Midday","time":"12:29 PM ET"}, {"tod":"Evening","time":"7:29 PM ET"}],
    "OK": [{"tod":"Evening","time":"9:10 PM CT"}],
    "OR": [{"tod":"Midday","time":"1:00 PM PT"}, {"tod":"Midday","time":"4:00 PM PT"}, {"tod":"Evening","time":"7:00 PM PT"}, {"tod":"Night","time":"10:00 PM PT"}],
    "PA": [{"tod":"Midday","time":"1:35 PM ET"},  {"tod":"Evening","time":"6:59 PM ET"}],
    "PR": [{"tod":"Midday","time":"2:00 PM AT"}, {"tod":"Night","time":"9:00 PM AT"}],
    "RI": [{"tod":"Midday","time":"1:30 PM ET"},  {"tod":"Evening","time":"7:29 PM ET"}],
    "SC": [{"tod":"Midday","time":"12:59 PM ET"}, {"tod":"Evening","time":"6:59 PM ET"}],
    "TN": [{"tod":"Morning","time":"9:28 AM CT"}, {"tod":"Midday","time":"12:28 PM CT"}, {"tod":"Evening","time":"6:28 PM CT"}],
    "TX": [{"tod":"Morning","time":"10:00 AM CT"}, {"tod":"Midday","time":"12:27 PM CT"}, {"tod":"Evening","time":"6:00 PM CT"}, {"tod":"Night","time":"10:12 PM CT"}],
    "VA": [{"tod":"Midday","time":"1:59 PM ET"},  {"tod":"Night","time":"11:00 PM ET"}],
    "VT": [{"tod":"Midday","time":"1:10 PM ET"}, {"tod":"Evening","time":"6:55 PM ET"}],
    "WA": [{"tod":"Evening","time":"8:00 PM PT"}],
    "WI": [{"tod":"Midday","time":"1:30 PM CT"},  {"tod":"Evening","time":"9:00 PM CT"}],
    "WV": [{"tod":"Evening","time":"6:59 PM ET"}],

}

DRAW_SCHEDULE_4 = {
    "CA": [{"tod":"Midday","time":"1:00 PM PT"},   {"tod":"Evening","time":"6:30 PM PT"}],
    "CT": [{"tod":"Midday","time":"1:57 PM ET"},   {"tod":"Night","time":"10:29 PM ET"}],
    "DC": [{"tod":"Midday","time":"1:50 PM ET"},   {"tod":"Evening","time":"7:50 PM ET"}],
    "DE": [{"tod":"Midday","time":"1:58 PM ET"},   {"tod":"Night","time":"7:57 PM ET"}],
    "FL": [{"tod":"Midday","time":"1:30 PM ET"},   {"tod":"Evening","time":"9:45 PM ET"}],
    "GA": [{"tod":"Midday","time":"12:29 PM ET"},  {"tod":"Evening","time":"6:59 PM ET"}, {"tod":"Night","time":"11:34 PM ET"}],
    "IL": [{"tod":"Midday","time":"12:40 PM CT"},  {"tod":"Evening","time":"9:22 PM CT"}],
    "IN": [{"tod":"Midday","time":"1:20 PM ET"},   {"tod":"Evening","time":"11:00 PM ET"}],
    "KY": [{"tod":"Midday","time":"1:20 PM ET"},   {"tod":"Evening","time":"11:00 PM ET"}],
    "MD": [{"tod":"Midday","time":"12:27 PM ET"},  {"tod":"Evening","time":"7:56 PM ET"}],
    "MI": [{"tod":"Midday","time":"12:59 PM ET"},  {"tod":"Evening","time":"7:29 PM ET"}],
    "MO": [{"tod":"Midday","time":"12:45 PM CT"},  {"tod":"Evening","time":"8:59 PM CT"}],
    "NC": [{"tod":"Midday","time":"3:00 PM ET"},   {"tod":"Evening","time":"11:22 PM ET"}],
    "NJ": [{"tod":"Midday","time":"12:59 PM ET"},  {"tod":"Evening","time":"10:57 PM ET"}],
    "NY": [{"tod":"Midday","time":"2:30 PM ET"},   {"tod":"Evening","time":"10:30 PM ET"}],
    "OH": [{"tod":"Midday","time":"12:29 PM ET"},  {"tod":"Evening","time":"7:29 PM ET"}],
    "PA": [{"tod":"Midday","time":"1:35 PM ET"},   {"tod":"Evening","time":"6:59 PM ET"}],
    "SC": [{"tod":"Midday","time":"12:59 PM ET"},  {"tod":"Evening","time":"6:59 PM ET"}],
    "TN": [{"tod":"Midday","time":"12:28 PM CT"},  {"tod":"Evening","time":"6:28 PM CT"}],
    "TX": [{"tod":"Morning","time":"10:00 AM CT"}, {"tod":"Midday","time":"12:27 PM CT"}, {"tod":"Evening","time":"6:00 PM CT"}, {"tod":"Night","time":"10:12 PM CT"}],
    "VA": [{"tod":"Midday","time":"1:59 PM ET"},   {"tod":"Night","time":"11:00 PM ET"}],
    "WI": [{"tod":"Midday","time":"1:30 PM CT"},   {"tod":"Evening","time":"9:00 PM CT"}],
}

_TZ_ABBREV = {
    "ET": "America/New_York",
    "CT": "America/Chicago",
    "MT": "America/Denver",
    "MST": "America/Phoenix",
    "PT": "America/Los_Angeles",
    "AT": "America/Puerto_Rico",
}

_TIME_RE = re.compile(r"(\d{1,2}):(\d{2})\s*(AM|PM)\s*([A-Z]+)")


def _parse_schedule_time(time_str: str) -> tuple[int, int, str]:
    """'12:29 PM ET' -> (hour24, minute, IANA tz name)."""
    m = _TIME_RE.match(time_str)
    hour, minute, ampm, tz_abbrev = int(m.group(1)), int(m.group(2)), m.group(3), m.group(4)
    if ampm == "PM" and hour != 12:
        hour += 12
    elif ampm == "AM" and hour == 12:
        hour = 0
    return hour, minute, _TZ_ABBREV.get(tz_abbrev, "America/New_York")


def next_draw_session(state_code: str) -> dict | None:
    """
    Of all the sessions in DRAW_SCHEDULE for this state, return the one
    whose scheduled clock time is the soonest from right now (today if it
    hasn't happened yet, otherwise tomorrow).

    Returns {"tod": ..., "time": ..., "date": "YYYY-MM-DD"} where "date" is
    the date (in the session's local timezone) on which that next draw will
    happen — or None if the state has no schedule.
    """
    sched = DRAW_SCHEDULE.get(state_code.upper())
    if not sched:
        return None

    best = None
    for entry in sched:
        hour, minute, tz_name = _parse_schedule_time(entry["time"])
        now = datetime.now(ZoneInfo(tz_name))
        scheduled_today = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if scheduled_today > now:
            when, draw_date = scheduled_today, now.date()
        else:
            when, draw_date = scheduled_today + timedelta(days=1), now.date() + timedelta(days=1)
        if best is None or when < best[0]:
            best = (when, entry, draw_date)

    when, entry, draw_date = best
    return {"tod": entry["tod"], "time": entry["time"], "date": draw_date.isoformat()}
