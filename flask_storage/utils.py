def force_str(name, encoding='utf-8'):
    if isinstance(name, str):
        return name
    else:
        return name.encode(encoding)


def force_unicode(name, encoding='utf-8'):
    if isinstance(name, unicode):
        return name
    else:
        return name.decode(encoding)
