# Ideas for Future Development

## Show Downloaded Movies in Folder Button

### Overview
Add a button that shows movies already in the download folder and allows clicking to play them directly - no download needed.

### What's Needed

#### Backend (~20 lines)
- New endpoint `/api/downloads/files` to list video files in `download/` folder
- Return: filename, filesize, path for each video file

#### Frontend (~50 lines)
- New "My Downloads" button in header/toolbar
- Click → fetch file list from new endpoint
- Display as movie cards (can reuse existing card styling)
- Click card → call `/api/play` directly (no download)

### Reusing Existing Code

| Component | Reuse Potential |
|-----------|-----------------|
| Card CSS (.movie-card) | ✅ Already exists |
| startPlayback() | ✅ Calls /api/play |
| Card rendering logic | ✅ Modify for file data |

### Implementation Approach

1. **Backend**: Scan download folder, return list of video files
2. **Frontend**: Add Downloads button next to other buttons
3. **Display**: Use existing card styling, just different data source
4. **Click**: Direct to `/api/play` - no torrent or download needed

### Difficulty: Easy to Medium
- Backend listing: ~20 lines
- Frontend button: ~10 lines
- Card display: ~30 lines

---

## Download Folder by Hash

### Overview
Create a folder in the download directory named with the torrent's info_hash, then save the movie file inside. This allows easy detection of completed downloads that survives app restarts.

### Structure

```
download/
  a1b2c3d4e5f6.../
    Avatar (2009).mkv
  f6e5d4c3b2a1.../
    The Matrix (1999).mkv
```

### Why This Works

- **Reliable detection**: Just check if folder `download/{info_hash}` exists
- **Survives restarts**: Folder persists on disk, not in memory
- **No title matching**: Uses unique info_hash, not dependent on filename
- **Simple checking**: `os.path.exists(f"download/{info_hash}")`

### Implementation

#### Backend Changes

1. **Modify download start** (around line 1036):
   ```python
   # Create folder with info_hash name
   folder_path = os.path.join(DOWNLOAD_DIR, info_hash)
   os.makedirs(folder_path, exist_ok=True)
   atp.save_path = folder_path
   ```

2. **Update find_video_file()**:
   - Check subfolders recursively to find video file
   - Instead of just checking `download/` folder, recurse into hash-named subfolders

#### Frontend Detection

Option A: **Backend check endpoint**
- New endpoint `/api/status/complete` returns list of completed info_hashes
- On page load, check which movies are complete

Option B: **Downloads page** (from earlier idea)
- Button shows all downloaded files
- Auto-recognizes from hash subfolders
- User clicks to play directly

### User Flow

1. User clicks movie card → starts download
2. Download goes into `download/{info_hash}/` folder
3. Download completes
4. App restarts (or stays open)
5. **Detection**: Check if folder `download/{info_hash}/` exists with video file
6. If exists → show play button immediately (no threshold needed if folder exists)
7. User clicks → plays file from that folder

### Benefits

- Works after app restart (folder exists on disk)
- No memory dependency
- Each download in separate folder - cleaner organization
- Easy to identify what was downloaded by checking folder names