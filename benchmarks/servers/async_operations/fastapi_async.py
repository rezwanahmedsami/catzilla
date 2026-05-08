#!/usr/bin/env python3

import asyncio

from fastapi import FastAPI


async def _yield_once() -> int:
    await asyncio.sleep(0)
    return 1


def create_app() -> FastAPI:
    app = FastAPI(title='FastAPI Async Benchmark Server')

    @app.get('/async/raw')
    async def raw_async():
        return {
            'framework': 'fastapi',
            'mode': 'raw_async',
            'value': 1,
        }

    @app.get('/async/yield-once')
    async def yield_once():
        value = await _yield_once()
        return {
            'framework': 'fastapi',
            'mode': 'yield_once',
            'value': value,
        }

    @app.get('/async/fanout')
    async def fanout_async():
        results = await asyncio.gather(_yield_once(), _yield_once(), _yield_once())
        return {
            'framework': 'fastapi',
            'mode': 'fanout_async',
            'value': sum(results),
        }

    @app.get('/async/chain/{steps}')
    async def chain_async(steps: int):
        total = 0
        for _ in range(steps):
            total += await _yield_once()
        return {
            'framework': 'fastapi',
            'mode': 'chain_async',
            'steps': steps,
            'value': total,
        }

    return app


app = create_app()


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='127.0.0.1', port=8071)