#!/usr/bin/env python3
"""Scan download/misc/, identify each movie via TMDB, and organize into download/<tmdb_id>/<hash>/ or download/_unknown/<hash>/."""

import os
import re
import json
import time
import hashlib
import requests

DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "download")
MISC_DIR = os.path.join(DOWNLOAD_DIR, "misc")
TMDB_KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tmdb")

VIDEO_EXTENSIONS = {'.mkv', '.mp4', '.avi', '.mov', '.m4v', '.wmv', '.flv', '.webm'}

STATUS_FILE_NAME = ".movietimeStatus"

def read_tmdb_key():
    with open(TMDB_KEY_FILE) as f:
        return f.read().strip()

def extract_title_year(filename):
    name = os.path.splitext(filename)[0]
    name = name.replace('.', ' ').replace('_', ' ')
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', name)
    year = year_match.group(1) if year_match else None
    if year:
        title = name[:year_match.start()].strip()
    else:
        title = name.strip()
    title = re.sub(r'\s+', ' ', title).strip()
    title = re.sub(r'\b(2160p|1080p|720p|480p|360p|BluRay|WEB-DL|WEBRip|HDTS|HDRip|DVDRip|x264|x265|HEVC|AAC|AC3|5\.[01]|BONE|LOL|YTS|V3SP4EV3R|MVGroup|MULTI|ITA|ENG|Remastered|Extended|Special[ .]Cut|Proper|Real|Internal)\b', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s+', ' ', title).strip()
    title = re.sub(r'[-–]\s*$', '', title).strip()
    return title, year

def extract_resolution(filename):
    res_match = re.search(r'\b(2160p|1080p|720p|480p|360p|4K|UHD)\b', filename, re.IGNORECASE)
    if res_match:
        r = res_match.group(1).upper()
        if r == 'UHD':
            return '4K'
        return r if r != '2160P' else '4K'
    return 'N/A'

def search_tmdb(api_key, title, year=None):
    params = {"api_key": api_key, "query": title, "language": "en-US"}
    if year:
        params["year"] = year
    resp = requests.get("https://api.themoviedb.org/3/search/movie", params=params, timeout=10)
    if not resp.ok:
        return None
    data = resp.json()
    results = data.get("results", [])
    if not results:
        return None
    for r in results:
        if r.get("vote_count", 0) > 0:
            return r["id"]
    return results[0]["id"]

def random_hash():
    return hashlib.sha256(os.urandom(32)).hexdigest()[:40].upper()

def process_file(api_key, filename):
    filepath = os.path.join(MISC_DIR, filename)
    if not os.path.isfile(filepath):
        return
    ext = os.path.splitext(filename)[1].lower()
    if ext not in VIDEO_EXTENSIONS:
        return

    print(f"Processing: {filename}")
    title, year = extract_title_year(filename)
    if not title:
        print(f"  Could not extract title from filename, skipping")
        return

    tmdb_id = search_tmdb(api_key, title, year)
    if tmdb_id:
        tmdb_str = str(tmdb_id)
        print(f"  TMDB match: {tmdb_id}")
    else:
        tmdb_str = "_unknown"
        print(f"  No TMDB match, using _unknown")

    hash_dir = os.path.join(DOWNLOAD_DIR, tmdb_str, random_hash())
    os.makedirs(hash_dir, exist_ok=True)

    dest_path = os.path.join(hash_dir, filename)
    os.rename(filepath, dest_path)
    print(f"  Moved to: {dest_path}")

    resolution = extract_resolution(filename)
    status = {
        "progress": 100,
        "downloaded_bytes": os.path.getsize(dest_path),
        "total_bytes": os.path.getsize(dest_path),
        "status": "ready",
        "is_playable": True,
        "last_updated": time.time(),
        "magnet": "",
        "name": filename,
        "tmdb_id": tmdb_id,
        "resolution": resolution
    }
    status_path = os.path.join(hash_dir, STATUS_FILE_NAME)
    with open(status_path, "w") as f:
        json.dump(status, f)
    print(f"  Created: {status_path}")

def main():
    api_key = read_tmdb_key()
    if not os.path.isdir(MISC_DIR):
        print(f"Directory not found: {MISC_DIR}")
        return
    files = sorted(os.listdir(MISC_DIR))
    for f in files:
        process_file(api_key, f)

if __name__ == "__main__":
    main()
