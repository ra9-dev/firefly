import os
from typing import Optional
from urllib.request import urlopen

from loguru import logger

from app.helper import LOCAL_DIR, WORDS_MASTERLIST_FILE_LINK, _time_my_method

LOCAL_FILE_PATH = f"{LOCAL_DIR}/valid_words.txt"


class ValidWords:
    valid_words: list[str] = []

    @classmethod
    def __check_if_valid_word(cls, word: str) -> Optional[str]:
        if len(word) < 3:
            return None
        if not word.isalpha():
            return None
        return word

    @classmethod
    @_time_my_method
    async def get_valid_words(cls) -> list[str]:
        logger.debug("Fetching valid words")
        if cls.valid_words:
            logger.debug("Found valid words from class context")
            return cls.valid_words

        # if class not loaded yet, try reading from local file
        # this is to prevent calling url again and again
        logger.debug("valid words not in class context. fetching from local storage")
        if not os.path.isfile(LOCAL_FILE_PATH):
            logger.debug("no file found yet")
            return await cls.read_remote_file()

        file_words = None
        with open(LOCAL_FILE_PATH, encoding="utf-8") as f:
            file_words = f.read().split("\n")
            file_words = [
                word for word in file_words if cls.__check_if_valid_word(word=word)
            ]

        if file_words:
            cls.valid_words = file_words
            return cls.valid_words

        logger.debug("valid words not in local storage. fetching from file link")
        return await cls.read_remote_file()

    @classmethod
    async def read_remote_file(cls):
        cls.valid_words = []
        with urlopen(WORDS_MASTERLIST_FILE_LINK) as file:
            for word in file.readlines():
                if valid_word := cls.__check_if_valid_word(
                    word=word.decode("utf-8").strip()
                ):
                    cls.valid_words.append(valid_word)

        os.makedirs(os.path.dirname(LOCAL_FILE_PATH), exist_ok=True)
        with open(LOCAL_FILE_PATH, encoding="utf-8", mode="w") as f:
            for word in cls.valid_words:
                f.write(f"{word}\n")

        return cls.valid_words
