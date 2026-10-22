# load_generator.py
import asyncio

import httpx


async def main(n_requests: int = 100, concurrency: int = 10) -> None:
    """Send n_requests to the monitored service, at most `concurrency` at a time."""
    limit = asyncio.Semaphore(concurrency)

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=30) as client:

        async def send(i: int) -> int:
            async with limit:
                payload = {"prompt": f"Summarize ticket {i}"}
                resp = await client.post("/v1/complete", json=payload)
                return resp.status_code

        codes = await asyncio.gather(*(send(i) for i in range(n_requests)))

    print({code: codes.count(code) for code in sorted(set(codes))})


if __name__ == "__main__":
    asyncio.run(main())
