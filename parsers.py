import json
from typing import List

def parse_followers_from_instagram_json(file_bytes) -> List[str]:
    data = json.loads(file_bytes.decode("utf-8"))
    usernames = []

    if isinstance(data, list):
        for entry in data:
            sld = entry.get("string_list_data") or []
            for item in sld:
                val = (item.get("value") or "").strip().lstrip("@").lower()
                if val:
                    usernames.append(val)
    elif isinstance(data, dict):
        for key in ["relationships_followers", "followers", "followers_list"]:
            arr = data.get(key)
            if isinstance(arr, list):
                for entry in arr:
                    sld = entry.get("string_list_data") or []
                    for item in sld:
                        val = (item.get("value") or "").strip().lstrip("@").lower()
                        if val:
                            usernames.append(val)

    return sorted(set(usernames))
