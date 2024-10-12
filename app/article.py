import json
import os

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from loguru import logger

from app.helper import (
    LOCAL_DIR,
    _get_string_hash,
    check_if_file_locked,
    clean_html_word,
)
from app.request import process_request
from app.valid_words import ValidWords


class Article:
    def __init__(self, client_session: ClientSession, url: str) -> None:
        self.client_session = client_session
        self.url = url
        self.url_hash = _get_string_hash(to_hash_str=self.url)
        self.json_file_path = f"{LOCAL_DIR}/jsons/{self.url_hash}.json"
        self.is_pre_existing_lock = check_if_file_locked(file_path=self.json_file_path)
        self.processed = False
        self.result: dict[str, int] = {}

    async def process(self):
        logger.debug(f"processing: {self.url_hash}")
        # if lock was pre existing, complete the process again
        # Maybe the process was stuck in between back then
        if not os.path.isfile(self.json_file_path) or self.is_pre_existing_lock:
            return await self.__process()

        article_word_count = None
        with open(self.json_file_path, encoding="utf-8") as f:
            article_word_count = json.load(f)

        if article_word_count:
            self.result = article_word_count
            self.processed = True
            return self.result

        await self.__process()

    async def __process(self):
        html_content = await process_request(
            client_session=self.client_session, url=self.url
        )
        if not html_content:
            return None

        soup = BeautifulSoup(html_content, "html.parser")
        raw_text = soup.get_text()
        cleaned_word_list = [clean_html_word(word=word) for word in raw_text.split(" ")]
        cleaned_word_list = raw_text.split(" ")

        valid_words = await ValidWords.get_valid_words()
        article_word_count: dict[str, int] = {}
        for word in cleaned_word_list:
            # dict searching faster
            # so if word already in dict
            # don't search in valid words list
            if word in article_word_count:
                article_word_count[word] += 1
                continue
            # if word is not part of valid word list, move on
            if word not in valid_words:
                continue
            article_word_count[word] = 0

        if not article_word_count:
            self.processed = False
            return None

        self.processed = True
        self.result = article_word_count

        os.makedirs(os.path.dirname(self.json_file_path), exist_ok=True)
        with open(self.json_file_path, encoding="utf-8", mode="w") as f:
            json.dump(self.result, f)

        return self.result
