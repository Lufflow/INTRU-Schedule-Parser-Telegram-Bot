import aiohttp
import asyncio
from typing import Optional


class AsyncRequester:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()

    async def get_session(self) -> aiohttp.ClientSession:
        async with self._lock:
            if self.session is None or self.session.closed:
                self.session = aiohttp.ClientSession(
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "ru-RU,ru;q=0.9",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Connection": "keep-alive",
                        "DNT": "1",
                    },
                    timeout=aiohttp.ClientTimeout(total=30),
                    connector=aiohttp.TCPConnector(
                        limit=10,
                        ttl_dns_cache=300,
                        use_dns_cache=True,
                    )
                )
            return self.session

    async def get(self, url: str, max_retries: int = 3) -> Optional[str]:
        session = await self.get_session()

        for attempt in range(max_retries):
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 429:
                        retry_after = int(
                            response.headers.get('Retry-After', 5))
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        await asyncio.sleep(2 ** attempt)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == max_retries - 1:
                    return None
                await asyncio.sleep(2 ** attempt)

        return None

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()


requester = AsyncRequester()
