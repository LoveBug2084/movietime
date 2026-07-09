#!/usr/bin/env python3
"""Check every movie name on TMDB, fix directory IDs that don't match."""

import json
import os
import re
import shutil
import sys
import time
import urllib.request
import urllib.parse

API_KEY = open(os.path.join(os.path.dirname(__file__), ".tmdb")).read().strip()
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "download")
SEARCH_URL = "https://api.themoviedb.org/3/search/movie"


def clean_movie_name(raw):
    name = raw.replace('.', ' ')
    m = re.search(r'19\d{2}|20\d{2}', name)
    if m:
        name = name[:m.start()]
    return name.strip()


def search_tmdb(title):
    params = {'api_key': API_KEY, 'query': title}
    url = SEARCH_URL + '?' + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data.get('results'):
                return data['results'][0]['id']
    except Exception as e:
        print(f"  ERROR: {e}")
    return None


def main():
    if not os.path.isdir(DOWNLOAD_DIR):
        print(f"Error: {DOWNLOAD_DIR}/ not found")
        sys.exit(1)

    for tmdb_dir in sorted(os.listdir(DOWNLOAD_DIR)):
        tmdb_path = os.path.join(DOWNLOAD_DIR, tmdb_dir)
        if not os.path.isdir(tmdb_path):
            continue

        for hash_dir in sorted(os.listdir(tmdb_path)):
            hash_path = os.path.join(tmdb_path, hash_dir)
            status_file = os.path.join(hash_path, ".movietimeStatus")
            if not os.path.isfile(status_file):
                continue

            with open(status_file) as f:
                status = json.load(f)

            raw_name = status.get('name', '')
            if not raw_name:
                continue

            title = clean_movie_name(raw_name)

            time.sleep(1)

            correct_id = search_tmdb(title)

            stored_id = status.get('tmdb_id')
            stored_str = str(stored_id) if stored_id else 'None'
            found_str = str(correct_id) if correct_id else 'None'

            print(f"{stored_str}, {found_str}, {title}")
            sys.stdout.flush()

            if correct_id and str(correct_id) != tmdb_dir:
                new_path = os.path.join(DOWNLOAD_DIR, str(correct_id), hash_dir)
                os.makedirs(os.path.join(DOWNLOAD_DIR, str(correct_id)), exist_ok=True)

                status['tmdb_id'] = correct_id
                with open(os.path.join(hash_path, ".movietimeStatus"), 'w') as f:
                    json.dump(status, f)

                if os.path.exists(new_path):
                    for item in os.listdir(hash_path):
                        src = os.path.join(hash_path, item)
                        dst = os.path.join(new_path, item)
                        if os.path.exists(dst):
                            if os.path.isdir(src):
                                shutil.copytree(src, dst, dirs_exist_ok=True)
                                shutil.rmtree(src)
                            else:
                                os.replace(src, dst)
                        else:
                            shutil.move(src, dst)
                    shutil.rmtree(hash_path)
                else:
                    shutil.move(hash_path, new_path)

    for tmdb_dir in sorted(os.listdir(DOWNLOAD_DIR)):
        tmdb_path = os.path.join(DOWNLOAD_DIR, tmdb_dir)
        if os.path.isdir(tmdb_path) and not os.listdir(tmdb_path):
            os.rmdir(tmdb_path)
            print(f"CLEANED: {tmdb_dir} (empty)")


if __name__ == '__main__':
    main()
