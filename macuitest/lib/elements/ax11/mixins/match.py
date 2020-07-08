import fnmatch


def match_filter(**kwargs):
    def _match(obj):
        for k in kwargs.keys():
            try:
                val = getattr(obj, k)
            except AttributeError:
                return False
            if isinstance(val, str):
                if not fnmatch.fnmatch(val, kwargs[k]):
                    return False
            else:
                if val != kwargs[k]:
                    return False
        return True

    return _match
