# Bugs

## Hover reorder bug — progress torrents move to end of list

**File:** `templates/index.html` — `updateCardWithTorrent()` (~line 1516)

**Symptom:** When hovering over a movie card, torrents with progress move to the end of the list instead of staying sorted by progress descending.

**Root cause:** The `existingMap` is built from DOM items BEFORE the update loop, but the update loop creates new items (via `document.createElement`) and appends them to `listEl`. These new items are NOT in `existingMap`. The reorder loop (lines 1648-1652) only moves items that exist in `existingMap`, using `appendChild` which pushes them to the end. New items stay at their appended position, and existing items (with progress) get shuffled to the end.

**Example:**
- Before hover: `[R1(progress=100), R2(progress=0)]`
- API returns: `[R1(progress=100), R3(progress=0, seeders=100)]` — R3 is new
- DOM after update loop: `[R1_el, R2_el, R3_new_el]`
- Reorder moves R1 to end: `[R2_el, R3_new_el, R1_el]` — progress=100 now at end

**Fix:** After the update loop, query the DOM again to get ALL items (existing + newly created), build a fresh map, and use `insertBefore` for precise repositioning instead of `appendChild`:

```javascript
// After update loop and cleanup of unused items:
const allCurrentItems = Array.from(listEl.querySelectorAll('.resolution-item'));
const currentMap = {};
allCurrentItems.forEach(el => { currentMap[el.dataset.infoHash] = el; });

const sortedHashes = torrents.map(t => t.info_hash || '');
let prevEl = null;
sortedHashes.forEach(ih => {
    const el = currentMap[ih];
    if (!el) return;
    if (prevEl) {
        if (el !== prevEl.nextSibling) {
            listEl.insertBefore(el, prevEl.nextSibling);
        }
    } else {
        if (listEl.firstElementChild !== el) {
            listEl.prepend(el);
        }
    }
    prevEl = el;
});
```
