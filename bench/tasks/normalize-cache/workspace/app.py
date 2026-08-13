_CACHE = {}


def get_user_profile(name: str) -> dict[str, str]:
    if name in _CACHE:
        return _CACHE[name]

    normalized = name.strip().lower()
    profile = {"username": normalized}
    _CACHE[name] = profile
    return profile
