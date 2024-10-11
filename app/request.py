import asyncio
from typing import Optional

import aiohttp
from loguru import logger

IS_RATE_LIMIT_REACHED = False
WAIT_FOR_SECONDS = 10


async def process_request(
    client_session: aiohttp.ClientSession, url: str, is_retry: bool = False
) -> Optional[str]:
    global IS_RATE_LIMIT_REACHED
    if IS_RATE_LIMIT_REACHED:
        logger.warning("Rate limit counter is reached. Let's wait for sometime.")
        await asyncio.sleep(WAIT_FOR_SECONDS)

    response = await client_session.get(url)
    if 200 <= response.status < 300:
        IS_RATE_LIMIT_REACHED = False
        return await response.text()
    # we hit rate limiting
    if response.status == 429:
        IS_RATE_LIMIT_REACHED = True
        logger.error("We hit rate limit. Requests will wait for some time.")
        if not is_retry:
            return await process_request(
                client_session=client_session, url=url, is_retry=True
            )
    else:
        logger.error(
            f"Something else happened || {response.status =} || {await response.text() =}"
        )
