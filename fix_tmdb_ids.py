import json
import os

DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "download")

fixed = 0
for root, dirs, files in os.walk(DOWNLOAD_DIR):
    for f in files:
        if f == ".movietimeStatus":
            path = os.path.join(root, f)
            with open(path) as fh:
                data = json.load(fh)
            if isinstance(data.get("tmdb_id"), int):
                data["tmdb_id"] = str(data["tmdb_id"])
                with open(path, "w") as fh:
                    json.dump(data, fh)
                fixed += 1
                print(f"Fixed: {path} -> {data['tmdb_id']}")

print(f"\nDone. Fixed {fixed} files.")
