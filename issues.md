# Issues Discovered & Changes Made

## 1. Apibay Offline — Switched to Magnetz

**Issue:** Apibay (`apibay.org`) is offline. All calls to `search_apibay` returned errors.

**Changes:**
- Commented out all `search_apibay()` calls across the backend
- Replaced with `search_magnetz()` in all code paths:
  - `rebuild_combined_final()` (line 999-1004)
  - Direct category search in `/api/search` (line 1461-1464)
  - `/api/torrent` endpoint (line 1873-1877)
- Updated API response `"sources"` labels from `"apibay"` to `"magnetz"`
- Updated docstrings/comments referencing "apibay"

**Magnetz API Fix:**
The `search_magnetz()` function had incorrect response parsing:
- API returns `{"data": [...]}` not a bare array — fixed to extract `results["data"]`
- Field `seeders` is on the root object, not nested in `swarm` — fixed
- Field for magnet link is `"magnet_link"` not `"magnet"` — fixed
- `size` returned as integer, not string — fixed with `str()` conversion

---

## 2. Double-Play Bug — Movie Restarts Seconds After Starting

**Issue:** Clicking Play on a ready movie starts playback, then the movie restarts from the beginning ~2 seconds later.

**Root cause:** In `templates/index.html`, `startPlayback()` sets up a 2-second polling interval (`checkDownload`) but never sets the `isStreaming` flag. When the first poll fires, it sees `data.status === 'ready'` and `!isStreaming` is still `true`, so it calls `startPlayback()` a second time — killing the first mpv process and starting a new one.

**Fix:** Added `isStreaming = true;` at the top of `startPlayback()` in `templates/index.html` (line 1583), before any other logic runs.

---

## 3. Library View Shows Duplicate/Incorrect Movie Cards

**Issue:** The "Downloaded" library view showed multiple identical cards for the same movie (e.g., 19 copies of Scarface 1983), and movies like Scarface 1932 were missing or incorrectly labelled.

**Root cause 1 — Overly loose name matching:** The fallback matching in `/api/downloads/list` used `title in torrent_name_lower`, which matched any torrent name containing "scarface" to the first "Scarface" movie in the cache regardless of year. All hash directories got incorrectly assigned `tmdb_id: 111` (Scarface 1983).

**Root cause 2 — No deduplication:** Each hash directory (regardless of how many exist for the same movie) was returned as a separate card. If 19 hash directories all pointed to Scarface 1983, 19 cards appeared.

**Root cause 3 — Stale tmdb_ids on disk:** Once a wrong `tmdb_id` was saved to a `.movietimeStatus` file, the direct ID lookup returned the wrong movie every time — the stale data was never re-validated.

**Fixes in `/api/downloads/list` (`movietime`):**

1. **Year-validated direct ID lookup** (lines 1833-1839): When a status file has `tmdb_id`, the torrent name's year is extracted and compared against the cached movie's year. If they differ, the match is rejected and fallback re-matching runs.

2. **Year-aware fallback matching** (lines 1841-1855): The fallback now also checks the year. A torrent name containing "1932" will only match movies whose cached year is also "1932".

3. **Deduplication by movie ID** (lines 1876-1892): After building the full list, entries with the same `id` are collapsed into a single card, keeping whichever has the highest download progress. Unmatched entries (id: None) are always shown separately.

---

## 4. Hover Self-Healing — tmdb_id Not Saved on Hover

**Issue:** When hovering over a movie card on the main TMDb view, the `/api/torrent` endpoint found matching hash directories on disk but never saved the correct TMDb ID into the `.movietimeStatus` file. The `tmdb_id` was only set when visiting the library view.

**Fix:**

**Backend (`movietime` — `/api/torrent`):**
- Added `tmdb_id` parameter to the endpoint (line 1900)
- When a hash directory exists on disk and `tmdb_id` is provided, the status file is updated with the correct ID (lines 1955-1969)
- Heals both missing status files (with the correct tmdb_id) and existing status files that have a wrong or missing tmdb_id

**Frontend (`templates/index.html`):**
- Hover fetch now includes `&tmdb_id=<movie.id>` (line 1228)
- `playMovie` torrent fetch also includes `&tmdb_id=<movie.id>` (line 1415)

This means normal browsing (hovering over movie cards) gradually self-heals all status files with correct TMDb IDs.

---

## Summary of Files Changed

| File | Changes |
|------|---------|
| `movietime` | Commented out apibay; fixed magnetz parsing; year-validated matching in `/api/downloads/list`; deduplication; tmdb_id self-healing in `/api/torrent`; updated labels/comments |
| `templates/index.html` | Added `isStreaming = true` fix; added `tmdb_id` parameter to hover and play requests |
