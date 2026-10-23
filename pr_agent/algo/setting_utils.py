def normalize_setting_list(value, *, split_commas: bool = False) -> list:
    """Return a setting value as a list without iterating plain strings by character."""
    if value is None or value == "":
        return []
    if isinstance(value, str):
        if split_commas:
            return [item.strip() for item in value.split(",") if item.strip()]
        return [value]
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]
