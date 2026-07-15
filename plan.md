# MovieTime: Persistent Cards + HashMap Architecture

## Background & Problem

Progress bars disappear when switching between full view and library view in MovieTime. This happens because `renderMovies()` calls `grid.innerHTML = ''` which destroys all card DOM elements. When `checkDownload()` polling tries to update a card's progress bar, the element no longer exists.

## Goal

One persistent set of card elements shared between full and library views. Library view reuses full-view cards via O(1) HashMap lookup. Progress bars survive view switches because the same DOM elements are reused.

## Files to Modify

- **`templates/index.html`** — All changes are in this single file (frontend only)

No backend changes needed. Backend already sorts library by `last_updated` from `.movietimeStatus` files and includes `last_updated` field.

## Key Code Locations in `templates/index.html`

| What | Line | Notes |
|------|------|-------|
| Global state vars (`displayMovies`, `libraryMovies`, etc.) | ~766 | Where `cardMap` will be added |
| `toggleViewMode()` | 966 | Switches between full/library views, calls `renderMovies()` |
| `loadDownloadedMovies()` | 992 | Fetches library data from `/api/downloads/list` |
| `loadAll()` | 1055 | Loads TMDB data + downloads on startup |
| `renderMovies()` | 1192 | **Main function to modify** — currently destroys and recreates all cards |
| `updateCardWithTorrent()` | 1383 | Populates resolution list on a card — has early return guard at line 1398 |
| `showDeleteConfirm()` | ~822 | Deletes a movie — must clean up `cardMap` |
| `checkDownload()` | ~1419 | Polls `/api/status` every 2s, writes progress into DOM elements |
| `setupTorrentHover()` | ~2084 | Adds card to grid on hover in full view |

## Implementation Plan

### Step 1: Add global `cardMap`

Near the other global variables (~line 766):

```javascript
let cardMap = new Map(); // movie_id → card DOM element
```

### Step 2: Rewrite `renderMovies()` to reuse cards

**Current flow (broken):**
```
grid.innerHTML = ''  →  destroys all cards  →  recreate each card from scratch
```

**New flow:**
```
grid.innerHTML = ''  →  cards removed from DOM but stay in cardMap
                      →  for each movie:
                          if cardMap.has(movie.id) → reuse existing card
                          else → create new card, add to cardMap
                          append card to grid
```

Key details for the rewrite:

a) **Remove cards from DOM without destroying references:**
```javascript
while (grid.firstChild) {
    grid.removeChild(grid.firstChild);
}
```
Cards stay in `cardMap` even when removed from DOM.

b) **Reuse existing cards:**
```javascript
const existingCard = cardMap.get(movie.id);
if (existingCard) {
    // Update dataset attributes
    existingCard.dataset.source = source;
    existingCard.dataset.infoHash = dlKey || '';
    existingCard.dataset.movieId = movie.id;
    existingCard.dataset.movieTitle = title;
    existingCard.dataset.movieYear = year || '';

    // Clear and refresh resolution list
    const listEl = existingCard.querySelector('.resolution-list');
    if (listEl) listEl.innerHTML = '';

    if (movie.resolutions && movie.resolutions.length > 0) {
        updateCardWithTorrent(existingCard, movie.resolutions.map(r => ({
            resolution: r.resolution || 'Local',
            size: r.size || '0',
            seeders: 'Local',
            info_hash: r.info_hash || '',
            magnet: r.magnet || '',
            name: r.name || movie.title || title,
            progress: r.progress || 0,
            is_playable: r.is_playable || false,
            dl_status: r.dl_status || '',
            category: 'movies'
        })));
    }

    // Re-attach context menu for downloaded
    if (source === 'downloaded' && movie.resolutions && movie.resolutions.length > 0) {
        existingCard.oncontextmenu = (e) => {
            e.preventDefault();
            showDeleteConfirm(existingCard, movie);
        };
    }

    // Re-attach hover for non-downloaded
    if (movie.seeders) {
        existingCard.dataset.movieTitle = title;
        existingCard.onmouseenter = () => setupTorrentHover(existingCard, movie);
    }

    card = existingCard;
} else {
    // Create new card (existing card-creation logic)
    // ...
    cardMap.set(movie.id, card);
}
```

c) **Critical: clearing `.resolution-list` innerHTML before calling `updateCardWithTorrent()`** — otherwise the early return guard at line 1398 (`if (listEl.children.length === torrents.length) return`) will skip the update.

### Step 3: Clean up `cardMap` on delete

In `showDeleteConfirm()` (~line 822), after `card.remove()`:
```javascript
cardMap.delete(movie.id);
```

In `showDeleteTorrentConfirm()`, individual torrent deletion does NOT remove from `cardMap` (card may have other resolutions).

### Step 4: Handle library-only movies

Some downloaded movies may not have a card in `cardMap` yet (e.g., on a different page of full view). For these:
- Create a new card using existing card-creation logic
- Add to `cardMap`
- They'll be reused the next time they appear in any view

## Flow After the Fix

1. Full view page 1 renders → 100 cards created → all added to `cardMap`
2. User starts download on movie #42 → `checkDownload()` updates its progress bar
3. User switches to library → `renderMovies()` called with library movies
4. Movie #42 found in `cardMap` → **same card element reused** → progress bar intact
5. Movie #500 (downloaded but not on page 1) not in `cardMap` → new card created, added to `cardMap`
6. User switches back to full view page 1 → movie #42's card reused again → progress still there
7. User pages to page 5 → movie #500's card reused from `cardMap`

## Edge Cases to Handle

- **`updateCardWithTorrent()` early return**: Must clear `.resolution-list` innerHTML before calling when reusing cards
- **Card dataset updates**: Source, infoHash, movieId, movieYear attributes must be updated on reused cards (source may change from `full` to `downloaded`)
- **Event handlers**: `oncontextmenu` and `onmouseenter` must be re-attached with correct `movie` data when reusing cards
- **`activeCard` reference**: Used by `checkDownload()` — still references valid element since we reuse the same DOM node
- **`downloadPollInterval`**: Still works because it references the same card
- **`loadDownloads()` / `checkPlayable()`**: Called at end of `renderMovies()` — still works, finds card in DOM

## What Stays the Same (No Changes Needed)

- Backend (`/api/downloads/list`, `/api/status`, `/api/start`, `/api/play`) — already has `last_updated` sorting
- `checkDownload()` polling — still references same card element
- `activeCard` / `downloadPollInterval` — still valid
- `enrichLibraryMovies()` — no changes needed
- `toggleViewMode()` / `loadAll()` — no changes needed
- `setupTorrentHover()` — no changes needed

## Testing Checklist

- [ ] Start a download in full view → switch to library → progress bar persists
- [ ] Start a download in library → switch to full view → progress bar persists
- [ ] Switch views multiple times → progress never resets
- [ ] Pagination still works (page through full view)
- [ ] Library sorts by most recent download time
- [ ] Delete a movie → card removed from cardMap and DOM
- [ ] Download completes → card updates correctly in both views
- [ ] Source attribute updates correctly (full → downloaded) when card is reused
- [ ] Multiple resolutions display correctly on reused cards
- [ ] Right-click delete context menu works on reused cards
