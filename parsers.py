import json
from typing import List

def parse_followers_from_instagram_json(file_bytes) -> List[str]:
    """
    Acepta el contenido del archivo JSON de 'Download your information' de Instagram.
    Los nombres de archivo pueden variar ('followers_1.json', 'followers_and_following.json', etc.)
    Devuelve una lista de usernames en minúscula sin '@'.
    """
    data = json.loads(file_bytes.decode("utf-8"))
    usernames = []

    # Formatos comunes:
    # 1) [{"string_list_data":[{"value":"username","href":"https://instagram.com/username","timestamp":...}]} ...]
    # 2) {"relationships_followers": [{"string_list_data":[{"value":"username", ...}]}], ...}
    if isinstance(data, list):
        for entry in data:
            sld = entry.get("string_list_data") or []
            for item in sld:
                val = (item.get("value") or "").strip().lstrip("@").lower()
                if val:
                    usernames.append(val)
    elif isinstance(data, dict):
        # intentar rutas típicas
        for key in ["relationships_followers", "followers", "followers_list"]:
            arr = data.get(key)
            if isinstance(arr, list):
                for entry in arr:
                    sld = entry.get("string_list_data") or []
                    for item in sld:
                        val = (item.get("value") or "").strip().lstrip("@").lower()
                        if val:
                            usernames.append(val)

    # normalizar únicos
    usernames = sorted(set(usernames))
    return usernames
