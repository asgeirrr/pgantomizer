from functools import reduce


def get_in(nested_dict, keys, default=None):
    def get_or_none(mapping, key):
        return mapping.get(key) if mapping else default

    return reduce(get_or_none, keys, nested_dict) if keys else default
