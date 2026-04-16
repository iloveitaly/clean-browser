def hash_function_code(func):
    import hashlib
    import inspect

    source = inspect.getsource(func)
    return hashlib.sha256(source.encode()).hexdigest()


_patch_complete = False


def patch_todoist_api():
    global _patch_complete
    if _patch_complete:
        return
    _patch_complete = True


patch_todoist_api()
