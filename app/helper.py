import hashlib
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
