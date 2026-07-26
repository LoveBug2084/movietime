# DOM Reads Audit — Frontend (`templates/index.html`)

DOMs should be write only. They should only reflect information from the real sources (JS data model).

## 34 DOM Reads That Should Use JS Data Sources

---

### Category 1: `card.dataset.*` Reads Used for Logic Decisions

| # | Line | What's Read | What It Should Read From |
|---|------|-------------|--------------------------|
| 1 | 1269 | infoHash from first resolution-item | `currentDownloadInfoHash` JS variable |
| 2 | 1270 | movieId from card | `currentDownloadMovieId` JS variable |
| 3 | 1361 | infoHash from first resolution-item | `movie.resolutions` array |
| 4 | 1366-1367 | Whether card has matching resolution-item | `movie.resolutions` array |
| 5 | 1368 | movieId from card | `movie.id` from closure |
| 6 | 1471 | infoHash from first resolution-item | `movie.resolutions` array |
| 7 | 1476-1477 | Whether card has matching resolution-item | `movie.resolutions` array |
| 8 | 1478 | movieId from card | `movie.id` from closure |
| 9 | 1541 | movieId from card | `movie.id` passed as parameter to `updateCardWithTorrent()` |
| 10 | 1554 | movieTitle from card | `movie.title` passed as parameter to `updateCardWithTorrent()` |
| 11 | 1555 | movieYear from card | `movie.year` passed as parameter to `updateCardWithTorrent()` |
| 12 | 1598 | infoHash from all existing items | JS-side resolution tracking map |
| 13 | 1648 | source from card | `source` param or JS `viewMode` state |
| 14 | 1652 | movieId from card | `movie` object from closure |
| 15 | 1713 | source from card | `source` param or JS `viewMode` state |
| 16 | 1717 | movieId from card | `movie` object from closure |
| 17 | 1925 | movieId from card | `movie` object or `currentDownload` state |
| 18 | 1963 | movieId from card | `movie.id` from context |
| 19 | 2002-2003 | infoHash from first resolution-item | `movie.resolutions` array |
| 20 | 2005 | movieId from card | `movie.id` from function param |
| 21 | 2027 | movieYear from card (fallback) | `movie.year` authoritative source |
| 22 | 2167 | infoHash existence from resolution-item | `movie.resolutions` array |
| 23 | 2171 | infoHash from resolution-item | `movie.resolutions` best resolution |
| 24 | 2174 | movieId from card | `movie` from `cardMap` or param |
| 25 | 2211 | movieId from card | `cardMap` lookup or state variable |
| 26 | 2259-2260 | hash match + movieId from card | Reverse map `hash -> movie/card` |

### Category 2: Full DOM Scans (querySelectorAll All Cards)

| # | Line(s) | What's Read | What It Should Read From |
|---|---------|-------------|--------------------------|
| 27 | 1866-1868 | Scans all cards for matching hash (progress update) | `hashToCard` reverse-lookup map |
| 28 | 1895-1897 | Scans all cards for matching hash (cancelled download) | `hashToCard` reverse-lookup map |
| 29 | 2204-2209 | Scans all cards for matching hash (startPlayback) | `hashToCard` reverse-lookup map |
| 30 | 2257-2260 | Scans all cards for matching hash (playable check) | `hashToCard` reverse-lookup map |

### Category 3: textContent Reads for State

| # | Line(s) | What's Read | What It Should Read From |
|---|---------|-------------|--------------------------|
| 31 | 903-908 | Movie count parsed from DOM text | `totalDatabaseMovies` JS variable |
| 32 | 977-982 | Movie count parsed from DOM text | `totalDatabaseMovies` JS variable |

### Category 4: classList.contains for State

| # | Line | What's Read | What It Should Read From |
|---|------|-------------|--------------------------|
| 33 | 961 | `classList.contains('downloading')` | `activeCard === card` JS check |

### Category 5: DOM QuerySelector for Card Lookup

| # | Line | What's Read | What It Should Read From |
|---|------|-------------|--------------------------|
| 34 | 1495 | `querySelector('.movie-card[data-movie-id="..."]')` | `cardMap.get(prevMovieId)` |

---

## Note: "First Hash" Reads (Items 3, 6, 19, 22, 23)

These read `card.querySelector('.resolution-item')?.dataset.infoHash` to grab the first resolution item's hash. While this is a DOM read, it is **currently safe** because `updateCardWithTorrent()` explicitly reorders all DOM elements to match the sorted `torrents` array (lines 1736-1751). The first `.resolution-item` in the DOM is always the best torrent (downloaded, best match, highest progress).

Still a DOM read — but not a bug in practice because the DOM order is kept in sync with the data model sort.

---

## Highest-Impact Fixes

### 1. Create `hashToCard` / `hashToMovieId` reverse-lookup map
Eliminates matches 27, 28, 29, 30, and partially 3, 4, 6, 7, 19, 22, 26.
Four full DOM scans are performed (lines 1866, 1895, 2204, 2257) on every status check / playback call.

### 2. Pass `movie` and `source` as parameters to `updateCardWithTorrent()`
Eliminates matches 9, 10, 11, 13, 14, 15, 16.
Currently this function has no parameters for the movie or source, so it reverse-engineers them from `card.dataset.*`.

### 3. Store active download state in JS variables
(`currentDownloadInfoHash`, `currentDownloadMovieId`)
Eliminates matches 1, 2, 33.

### 4. Track movie count in a JS variable
Instead of parsing it from textContent.
Eliminates matches 31, 32.

### 5. Pass `movie` through closures in card onclick handlers
Instead of reading `card.dataset.movieId`.
Eliminates matches 5, 8, 17, 18, 20, 24, 25.
