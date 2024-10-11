import asyncio
import json
import time
from collections import Counter

import aiohttp
from loguru import logger

from app.article import Article
from app.helper import (
    ARTICLE_LIST_FILE_RELATIVE_PATH,
    _time_my_method,
    convert_to_batches,
)
from app.valid_words import ValidWords

TOP_RECORDS = None
# TOP_RECORDS = 10000

PROCESSED_ARTICLE_OBJ: list[Article] = []
UNPROCESSED_ARTICLES = 0
MAX_PROCESSING_TIME_PER_RUN = 30


@_time_my_method
async def fetch_all_article_links() -> list:
    article_links = []
    with open(ARTICLE_LIST_FILE_RELATIVE_PATH, encoding="utf-8") as f:
        article_links = f.read().split("\n")

    return article_links


@_time_my_method
async def process_article(
    client_session: aiohttp.ClientSession, link: str, batch_idx: int, sub_idx: int
):
    global UNPROCESSED_ARTICLES
    idx = f"ARTICLE_{batch_idx+1}_{sub_idx+1}"
    logger.debug(f"Article Processing started for {idx =}")
    article_obj = Article(client_session=client_session, url=link)
    await article_obj.process()
    if article_obj.processed:
        PROCESSED_ARTICLE_OBJ.append(article_obj)
    else:
        UNPROCESSED_ARTICLES += 1
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
    for batch_idx, batch in enumerate(convert_to_batches(article_links, batch_size=10)):
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
async def finalize_processed_records(total_article_count: int):
    # NOTE: this can be further optimise
    # to store calculated results for each run
    # and don't run processing for successful articles
    logger.info(f"{UNPROCESSED_ARTICLES =}")
    logger.info(f"{len(PROCESSED_ARTICLE_OBJ) =}")
    collection_output = None
    for article_obj in PROCESSED_ARTICLE_OBJ:
        if not collection_output:
            # first iteration
            collection_output = Counter(article_obj.result)
            continue
        collection_output = collection_output + Counter(article_obj.result)

    final_output = {
        "total_article_count": total_article_count,
        "processed_articles": len(PROCESSED_ARTICLE_OBJ),
        "failed_to_process": UNPROCESSED_ARTICLES,
        "skipped_articles": total_article_count
        - len(PROCESSED_ARTICLE_OBJ)
        - UNPROCESSED_ARTICLES,
        "most_common_words": (
            dict(collection_output.most_common(10)) if collection_output else None
        ),
    }

    print(json.dumps(final_output, sort_keys=False, indent=4))


@_time_my_method
async def runner():
    # load valid words
    valid_words = await ValidWords.get_valid_words()
    logger.info(f"Got {len(valid_words)} valid words")
    article_links = await fetch_all_article_links()
    data_set = article_links[:TOP_RECORDS] if TOP_RECORDS else article_links
    await start_article_processing(article_links=data_set)
    await finalize_processed_records(total_article_count=len(article_links))


if __name__ == "__main__":
    logger.remove()
    logger.add("file.log", level="TRACE", mode="w")
    # logger.add(sys.stdout, level="INFO")
    asyncio.run(runner())
