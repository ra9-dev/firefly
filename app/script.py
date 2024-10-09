import sys
import time
from typing import Optional
from urllib.request import urlopen

from loguru import logger

WORDS_MASTERLIST_FILE_LINK = (
    "https://raw.githubusercontent.com/dwyl/english-words/master/words.txt"
)


def __time_my_method(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        func(*args, **kwargs)
        logger.trace(
            f"Execution Time {func.__name__} || {round(time.time() - start_time, 2)} secs"
        )

    return wrapper


def __check_if_valid_word(word: str) -> Optional[str]:
    if len(word) < 3:
        return None
    if not word.isalpha():
        return None
    return word


@__time_my_method
def read_words():
    valid_words_dict = {}
    with urlopen(WORDS_MASTERLIST_FILE_LINK) as file:
        for word in file.readlines():
            if valid_word := __check_if_valid_word(word=word.decode("utf-8").strip()):
                valid_words_dict[valid_word] = 0

    logger.debug(f"{len(valid_words_dict) =}")


if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stdout, level="TRACE")
    read_words()
