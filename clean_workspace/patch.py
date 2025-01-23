import logging

import backoff
import requests
import todoist_api_python.http_requests

# backoff does not log by default
logging.getLogger("backoff").addHandler(logging.StreamHandler())

def hash_function_code(func):
    import hashlib
    import inspect

    source = inspect.getsource(func)
    return hashlib.sha256(source.encode()).hexdigest()


# https://github.com/Doist/todoist-api-python/issues/38
# backoff all non-200 errors
def patch_todoist_api():
    if hasattr(patch_todoist_api, "complete") and patch_todoist_api.complete:
        return

    patch_targets = [
        ("ef2cb886b6c826b187e0b2ecd9ab406843b0130cc713398c218d6f430f253ea4","delete"),
        ("818cb060ea340f3cc47bdfbe9ace53470fadd58f6eae829a090ed4740afbb185","get"),
        ("d5d41e2c29049515d295d81a6d40b4890fbec8d8482cfb401630f8ef2f77e4d5","json"),
        ("e78617f97603c15e9330beecf4081ca8549605233ba4d65761248c09153652cb","post")
    ]

    for hash, target in patch_targets:
        original_function = getattr(todoist_api_python.http_requests, target)

        if not original_function:
            logging.warning(f"could not find {target} in todoist_api_python.http_requests when patching")
        
        if (original_function_hash := hash_function_code(original_function)) != hash:
            logging.warning(f"hash mismatch for {target} in todoist_api_python.http_requests when patching: {original_function_hash}")

        setattr(
            todoist_api_python.http_requests,
            f"original_{target}",
            original_function,
        )

        # TODO pretty sure authorization errors are retried :/

        def extract_retry_time(exception):
            """
            raw response on 429:

            b'{"error":"Too many requests. Limits reached. Try again later","error_code":35,"error_extra":{"event_id":"07c3fb965eaa4ec6a42e977c3e035c6b","retry_after":66},"error_tag":"LIMITS_REACHED","http_code":429}'
            """

            if (
                not isinstance(exception, requests.exceptions.HTTPError)
                or exception.response.status_code != 429
            ):
                raise exception

            retry_after_in_seconds = exception.response.json()["error_extra"][
                "retry_after"
            ]

            # add 10s of buffer
            return retry_after_in_seconds + 10

        patched_function = backoff.on_exception(
            backoff.runtime,
            (requests.exceptions.HTTPError),
            value=extract_retry_time,
            max_tries=8,
        )(original_function)

        patched_function2 = backoff.on_exception(
            backoff.expo,
            # RequestException superclass is IOError, which is a low-level py error
            # tried using HTTPError as the retry, but at scale the Todoist API has lots of interesting failures
            (requests.exceptions.RequestException),
            max_tries=30,
        )(patched_function)

        setattr(
            todoist_api_python.http_requests,
            target,
            patched_function2,
        )

    patch_todoist_api.complete = True


patch_todoist_api()
