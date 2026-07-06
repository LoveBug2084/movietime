#!/usr/bin/env python3
import sys
import requests
import re
import time

def extract_resolution(name):
    if not name:
        return ""
    patterns = [
        (r'(?i)\b2160p\b', '4K'),
        (r'(?i)\b4[kK]\b', '4K'),
        (r'(?i)\b[Uu][Hh][Dd]\b', '4K'),
        (r'(?i)\b1080p\b', '1080p'),
        (r'(?i)\b720p\b', '720p'),
        (r'(?i)\b480p\b', '480p'),
        (r'(?i)\b360p\b', '360p'),
    ]
    for pattern, label in patterns:
        if re.search(pattern, name):
            return label
    return ""

def score_torrent(name, title):
    if not name or not title:
        return 0
    name_lower = name.lower()
    title_lower = title.lower()
    noise_terms = ["trailer", "review", "soundtrack", "interview", "behind the scenes",
                   "featurette", "making of", "documentary", "short film", "episode",
                   "s01", "s02", "s03", "s04", "s05", "s06", "s07", "s08", "s09", "s10",
                   "season", "complete series", "tv series", "ebook", "audiobook", 
                   "kindle", "kobo", "nook", "epub", "mobi", "azw3", "azw", "cbz", "cbr",
                   "mp3", "flac", "m4b", "aax", "ogg", "wma"]
    for noise in noise_terms:
        if noise in name_lower:
            return 0
    title_words = re.sub(r'[^a-z0-9\s]', ' ', title_lower).split()
    name_words = set(re.sub(r'[^a-z0-9\s]', ' ', name_lower).split())
    if not title_words:
        return 0
    clean_title = re.sub(r'[^a-z0-9\s]', ' ', title_lower).strip()
    clean_name = re.sub(r'[^a-z0-9\s]', ' ', name_lower).strip()
    if clean_title in clean_name or clean_name in clean_title:
        return 200
    match_count = sum(1 for w in title_words if w in name_words)
    word_score = int((match_count / len(title_words)) * 100)
    res_bonus = 10 if extract_resolution(name) else 0
    total = word_score + res_bonus
    return total if (match_count >= len(title_words) // 2 + 1 or total >= 60) else 0

def search_apibay(query):
    try:
        url = f"https://apibay.org/q.php?q={query}"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, timeout=10, headers=headers)
        results = resp.json()
        torrents = []
        for r in results:
            name = r.get("name", "")
            info_hash = r.get("info_hash", "")
            if info_hash and len(info_hash) == 40:
                torrents.append({
                    "name": name,
                    "info_hash": info_hash,
                    "seeders": int(r.get("seeders", 0)),
                    "magnet": f"magnet:?xt=urn:btih:{info_hash}&dn={name}",
                    "resolution": extract_resolution(name),
                    "score": score_torrent(name, query)
                })
        return torrents
    except Exception as e:
        print(f"Error searching apibay: {e}")
        return []

def search_magnetz(query):
    try:
        url = f"https://magnetz.eu/api/magnets/search?query={query}"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, timeout=10, headers=headers)
        results = resp.json()
        torrents = []
        for r in results:
            name = r.get("name", "")
            info_hash = r.get("info_hash", "")
            swarm = r.get("swarm", {})
            seeders = swarm.get("seeders", 0) if isinstance(swarm, dict) else 0
            if info_hash and len(info_hash) == 40:
                torrents.append({
                    "name": name,
                    "info_hash": info_hash,
                    "seeders": int(seeders),
                    "magnet": r.get("magnet") or f"magnet:?xt=urn:btih:{info_hash}&dn={name}",
                    "resolution": extract_resolution(name),
                    "score": score_torrent(name, query)
                })
        return torrents
    except Exception as e:
        print(f"Error searching magnetz: {e}")
        return []

def main():
    if len(sys.argv) < 2:
        print("Usage: ./torrent_search.py <search_query>")
        sys.exit(1)
    query = " ".join(sys.argv[1:])
    print(f"Searching for: {query}...")
    all_torrents = []
    print("Checking Apibay...")
    all_torrents.extend(search_apibay(query))
    print("Checking Magnetz...")
    all_torrents.extend(search_magnetz(query))
    unique_torrents = {}
    for t in all_torrents:
        ih = t["info_hash"]
        if t["score"] <= 0:
            continue
        if ih not in unique_torrents or t["seeders"] > unique_torrents[ih]["seeders"]:
            unique_torrents[ih] = t
    final_torrents = list(unique_torrents.values())
    final_torrents.sort(key=lambda t: (t["score"], t["seeders"]), reverse=True)
    if not final_torrents:
        print("No matching torrents found.")
        return
    print(f"\nFound {len(final_torrents)} results:\n")
    print(f"{'Resolution':<12} {'Seeders':<10} {'Name'}")
    print("-" * 60)
    for t in final_torrents[:20]:
        print(f"{t['resolution']:<12} {t['seeders']:<10} {t['name']}")
        print(f"Magnet: {t['magnet']}\n")

if __name__ == "__main__":
    main()
