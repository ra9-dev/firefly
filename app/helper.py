import hashlib
import os
import time

from loguru import logger

LOCAL_DIR = "local_tmp"
WORDS_MASTERLIST_FILE_LINK = (
    "https://raw.githubusercontent.com/dwyl/english-words/master/words.txt"
)
ARTICLE_LIST_FILE_RELATIVE_PATH = "endg-urls"


def _time_my_method(func):
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        response = await func(*args, **kwargs)
        logger.trace(
            f"Execution Time {func.__name__} || {round(time.time() - start_time, 4)} secs"
        )
        return response

    return wrapper


def _get_string_hash(to_hash_str: str):
    hash_object = hashlib.sha256()
    hash_object.update(to_hash_str.encode("utf-8"))

    # Return the hexadecimal representation of the hash
    return hash_object.hexdigest()


def convert_to_batches(iterable, batch_size=10):
    iter_len = len(iterable)
    for ndx in range(0, iter_len, batch_size):
        yield iterable[ndx : min(ndx + batch_size, iter_len)]


def clean_html_word(word: str) -> str:
    # Remove leading/trailing quotes and commas
    word = word.strip("\",+.'_!@#$?^-")
    return word


# TODO: can be later optimised to remove lock files,
# if created more than 1 minute or so
def check_if_file_locked(file_path: str) -> bool:
    return bool(os.path.isfile(get_lock_file_path(file_path=file_path)))


def get_lock_file_path(file_path: str) -> str:
    return f"{file_path}.lock"


def read_list_from_txt_file(file_path: str) -> list[str]:
    if not os.path.isfile(file_path):
        logger.debug(f"{file_path =} not found. Returning empty list")
        return []

    with open(file_path, encoding="utf-8") as f:
        list_elems = f.read().split("\n")
        # NOTE: to cater for empty last line
        if not list_elems[-1]:
            del list_elems[-1]
        return list_elems
