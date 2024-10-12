import asyncio
import json
import os
import random
import sys
import time
from collections import Counter
from typing import Optional

import aiohttp
from loguru import logger

from app.article import Article
from app.helper import (
    ARTICLE_LIST_FILE_RELATIVE_PATH,
    LOCAL_DIR,
    _time_my_method,
    check_if_file_locked,
    convert_to_batches,
    get_lock_file_path,
    read_list_from_txt_file,
)
from app.valid_words import ValidWords

DEBUG = True

PROCESSED_ARTICLE_OBJ: list[Article] = []
UNPROCESSED_ARTICLES = 0
MAX_PROCESSING_TIME_PER_RUN = 30

OUTPUT_COUNT_FILE = f"{LOCAL_DIR}/processed.json"
OUTPUT_PROCESSED_URLS_FILE = f"{LOCAL_DIR}/processed.txt"


@_time_my_method
async def process_article(
    client_session: aiohttp.ClientSession, link: str, batch_idx: int, sub_idx: int
):
    global UNPROCESSED_ARTICLES
    idx = f"ARTICLE_{batch_idx+1}_{sub_idx+1}"
    logger.debug(f"Article Processing started for {idx =}")
    article_obj = Article(client_session=client_session, url=link)
    if check_if_file_locked(file_path=article_obj.json_file_path):
        logger.warning(
            f"Article Processing SKIPPED because of concurrent lock for {idx =}"
        )
        return None

    lock_file_path = get_lock_file_path(file_path=article_obj.json_file_path)
    os.makedirs(os.path.dirname(lock_file_path), exist_ok=True)
    with open(lock_file_path, encoding="utf-8", mode="w") as _:
        await article_obj.process()
        if article_obj.processed:
            PROCESSED_ARTICLE_OBJ.append(article_obj)
        else:
            UNPROCESSED_ARTICLES += 1
        os.remove(lock_file_path)

    logger.debug(f"Article Processing ended for {idx =}")


@_time_my_method
async def process_batch(batch_idx: int, batch: list[str]):
    logger.debug(f"Batch Processing started for {batch_idx =}")
    client_session = aiohttp.ClientSession()
    tasks = []
    for idx, link in enumerate(batch):
        tasks.append(
            process_article(
                client_session=client_session, link=link, batch_idx=batch_idx, sub_idx=idx
            )
        )

    await asyncio.gather(*tasks, return_exceptions=True)
    logger.debug(f"Batch Processing ended for {batch_idx =}")
    await client_session.close()


@_time_my_method
async def start_article_processing(article_links: list[str]):
    start_time = time.time()
    # tasks = []
    for batch_idx, batch in enumerate(convert_to_batches(article_links, batch_size=15)):
        # tasks.append(process_batch(batch_idx=batch_idx, batch=batch))
        # NOTE: if crossed threshold don't run the processing
        # we can't keep user waiting
        elapsed_time = round(time.time() - start_time, 2)
        if elapsed_time > MAX_PROCESSING_TIME_PER_RUN:
            logger.error(
                f"{elapsed_time} reached max threshold of {MAX_PROCESSING_TIME_PER_RUN}"
            )
            return
        await process_batch(batch_idx=batch_idx, batch=batch)
    # await asyncio.gather(*tasks, return_exceptions=True)


@_time_my_method
async def finalize_processed_records(
    total_article_count: int,
    previously_processed_urls: Optional[list[str]] = None,
    previously_processed_count: Optional[dict[str, int]] = None,
):
    # NOTE: this can be further optimise
    # to store calculated results for each run
    # and don't run processing for successful articles
    logger.info(f"{UNPROCESSED_ARTICLES =}")
    logger.info(f"{len(PROCESSED_ARTICLE_OBJ) =}")
    processed_urls = previously_processed_urls or []
    run_specific_processed_files = []
    collection_output = Counter(previously_processed_count) or None
    for article_obj in PROCESSED_ARTICLE_OBJ:
        processed_urls.append(article_obj.url)
        run_specific_processed_files.append(article_obj.json_file_path)
        if not collection_output:
            # first iteration
            collection_output = Counter(article_obj.result)
            continue
        collection_output = collection_output + Counter(article_obj.result)

    remaining_articles = total_article_count - len(processed_urls) - UNPROCESSED_ARTICLES

    final_output = {
        "total_article_count": total_article_count,
        "total_processed_articles": len(processed_urls),
        "processed_articles": len(PROCESSED_ARTICLE_OBJ),
        "failed_to_process": UNPROCESSED_ARTICLES,
        "skipped_articles_to_be_processed": remaining_articles,
        "most_common_words": (
            dict(collection_output.most_common(10)) if collection_output else None
        ),
        "message": "Run the script again to get remaining articles processed",
    }

    if collection_output:
        os.makedirs(os.path.dirname(OUTPUT_COUNT_FILE), exist_ok=True)
        with open(OUTPUT_COUNT_FILE, encoding="utf-8", mode="w") as f:
            json.dump(dict(collection_output), f)

    if processed_urls:
        os.makedirs(os.path.dirname(OUTPUT_PROCESSED_URLS_FILE), exist_ok=True)
        with open(OUTPUT_PROCESSED_URLS_FILE, encoding="utf-8", mode="w") as f:
            for url in processed_urls:
                f.write(f"{url}\n")

    for file in run_specific_processed_files:
        os.remove(file)

    print(json.dumps(final_output, sort_keys=False, indent=4))


async def fetch_previously_processed_urls() -> Optional[list[str]]:
    logger.debug("Fetching previously processed urls")

    processed_urls = read_list_from_txt_file(file_path=OUTPUT_PROCESSED_URLS_FILE)
    logger.debug(f"Fetched: {len(processed_urls)}")

    return processed_urls


async def fetch_previously_processed_count() -> Optional[dict[str, int]]:
    logger.debug("Fetching previously processed count")

    if not os.path.isfile(OUTPUT_COUNT_FILE):
        logger.debug("no previous processed count found")
        return None

    processed_count = None
    with open(OUTPUT_COUNT_FILE, encoding="utf-8") as f:
        processed_count = json.load(f)

    return processed_count


@_time_my_method
async def runner():
    # load valid words
    valid_words = await ValidWords.get_valid_words()
    logger.info(f"Got {len(valid_words)} valid words")
    # fetch data from previous runs
    previously_processed_count = await fetch_previously_processed_count()
    previously_processed_urls = await fetch_previously_processed_urls()
    article_links = read_list_from_txt_file(file_path=ARTICLE_LIST_FILE_RELATIVE_PATH)
    logger.info(f"Total Articles: {len(article_links)}")
    if previously_processed_urls:
        article_links = list(set(article_links) - set(previously_processed_urls))

    logger.info(f"Articles to process: {len(article_links)}")
    # NOTE: this if for concurrency,
    # so multiple instances have less chance of picking same file
    random.shuffle(article_links)
    await start_article_processing(article_links=article_links)

    if check_if_file_locked(file_path=OUTPUT_COUNT_FILE):
        logger.warning(
            "found lock for count processing. "
            "This script will run in processing only mode"
        )
        final_output = {
            "total_article_count": len(article_links),
            "processed_articles": len(PROCESSED_ARTICLE_OBJ),
            "failed_to_process": UNPROCESSED_ARTICLES,
            "message": (
                "The script completed in processing only mode."
                "Articles read here ain't completely counted."
            ),
        }
        print(json.dumps(final_output, sort_keys=False, indent=4))
    else:
        # refetch processed urls and processed count for concurrency
        # maybe some other process updated it
        previously_processed_count = await fetch_previously_processed_count()
        previously_processed_urls = await fetch_previously_processed_urls()
        lock_file_path = get_lock_file_path(file_path=OUTPUT_COUNT_FILE)
        os.makedirs(os.path.dirname(lock_file_path), exist_ok=True)
        with open(lock_file_path, encoding="utf-8", mode="w") as _:
            await finalize_processed_records(
                total_article_count=len(article_links),
                previously_processed_count=previously_processed_count,
                previously_processed_urls=previously_processed_urls,
            )
            logger.info("Removing count lock file")
            os.remove(lock_file_path)


if __name__ == "__main__":
    logger.remove()
    if DEBUG:
        logger.add(sys.stdout, level="TRACE")
    else:
        logger.add("file.log", level="TRACE", mode="w")
    print("Processing started and is going to take sometime, please don't exit")
    asyncio.run(runner())
