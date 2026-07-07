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

---

## 5. Torrent List Progress Not Updating Live

**Issue:** When a movie is downloading/playing, the progress bar below the card updated live (via 2-second polling), but the torrent list shown on hover still showed the original progress from when the list was first fetched. The list was cached and never refreshed.

**Fix in `templates/index.html`:**

1. **Store info_hash on each resolution item** (line 1141): Added `item.dataset.infoHash = torrent.info_hash || '';` so each torrent entry can be identified later.

2. **Live update resolution items from poll** (lines 1518-1524, 1554-1560): In `checkDownload()`, after updating the progress bar, it now also finds `.resolution-item[data-info-hash="..."]` elements in the same card and updates their `.res-progress` text to the current percentage. When status becomes `"ready"`, the item title is also set to `"Ready to play"`.

---

---

## 6. Progress Bar Jumps to 100% on Partial Download — Wrong File Size

**Issue:** A movie at 19% download plays when clicked, but the progress bar jumps to 100% and appears stuck.

**Root cause:** `renderMovies()` creates cards with `data-info-hash` from library data but never sets `data-file-size`. `checkDownload()` uses `parseInt(card.dataset.fileSize) || 1` — when `fileSize` is undefined, `parseInt` gives `NaN`, falling to `1`, making any downloaded byte show as 100%.

**Why it never triggered before:** The old flow always went through `startDownloadFromTorrent()` which set `data-file-size` on the card. The self-healing library merge created a new path where cards had download info but bypassed `startDownloadFromTorrent`.

**Fixes:**

**Backend (`movietime` — `/api/status`):**
- Added `"total_size": status.total_wanted` to both "downloading" responses (lines 2082, 2091)
- `status.total_wanted` reflects only the movie file size because `apply_sequential_priority()` sets non-video files to `dont_download`

**Frontend (`templates/index.html`):**
- `checkDownload()` (line 1559): uses `parseInt(data.total_size)` from backend, removes `card.dataset.fileSize || 1` fallback, guards against 0
- `loadDownloads()` (line 1297): same change
- Removed both `card.dataset.fileSize = ...` assignments (lines 1363, 1438) — dead code

---

## 7. Orange Progress Bar Right Side Misshapen — CSS Class Collision

**Issue:** The orange stage-1 progress bar's right side appeared squared instead of rounded. The green stage-2 bar looked fine.

**Root cause:** The CSS class `.header` (line 29) defined `padding: 20px; position: sticky; top: 0;` for the page header element. When `fill.classList.add('header')` was called on the progress bar fill, it inherited `padding: 20px`, making the fill 50px tall. The parent track (10px tall, `overflow: hidden`) clipped the fill, hiding the `border-radius: 5px` corners.

**Fix:** Renamed progress bar class from `.header` to `.header-stage` in all locations:
- CSS: line 358: `.dl-progress-fill.header` → `.dl-progress-fill.header-stage`
- JS: classList add/remove calls at lines 1304, 1306, 1556, 1561
- No other CSS name collisions found in the file

---

## 8. Download Progress Stops Updating When Switching Pages

**Issue:** With a torrent downloading/playing, switching from the TMDB page to the library (or any page that calls `renderMovies()`) caused the progress bar to freeze. The download continued in the backend but the UI stopped updating.

**Root cause:** `renderMovies()` at line 956-958 clears `downloadPollInterval` and resets `activeCard = null`. After rendering new cards, no new poll was started. The library view was a one-shot snapshot — `loadDownloads()` fetched status once and exited.

**Fix in `templates/index.html` — `renderMovies()`:**
- Saved `wasPolling` and `prevInfoHash` before clearing (lines 956-957)
- After rendering, if polling was active and the new page has a card with the same `data-info-hash`, restart the poll on the new card (lines 1105-1113)
- Both TMDB and library views go through `renderMovies()`, so both benefit from this fix

---

## 9. Auto-Play Re-Triggers on Page Switch After Player Closed

**Issue:** After a download completes and auto-plays, closing mpv and switching pages causes the movie to auto-play again. Each page switch re-triggers playback.

**Root cause:** `renderMovies()` resets `isStreaming = false` (line 966). When the re-enable poll (from fix #8) fires `checkDownload()`, it sees status `'ready'` and `!isStreaming` is true, so it calls `startPlayback()` — starting mpv again.

**Fix in `templates/index.html` — `renderMovies()`:**
- Save `isStreaming` state before clearing (line 956: `const wasStreaming = isStreaming;`)
- Restore it when re-enabling the poll (line 1109: `isStreaming = wasStreaming;`)
- If the user had the player open, `isStreaming` stays true → blocks false auto-play
- If the user never played, `isStreaming` stays false → auto-play on completion still works

---

## Summary of Files Changed

| File | Changes |
|------|---------|
| `movietime` | Commented out apibay; fixed magnetz parsing; year-validated matching in `/api/downloads/list`; deduplication; tmdb_id self-healing in `/api/torrent`; updated labels/comments; sort torrents by progress first; added `total_size` to `/api/status` responses (lines 2082, 2091) |
| `templates/index.html` | Added `isStreaming = true` in `startPlayback()`; added `tmdb_id` to hover/play requests; store info_hash on resolution items; live update torrent list from polling; renamed `.header` to `.header-stage`; removed `card.dataset.fileSize` dead code; `checkDownload`/`loadDownloads` use `data.total_size` from backend; save/restore poll + `isStreaming` across page switches in `renderMovies` |
