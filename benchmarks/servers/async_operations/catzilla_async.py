#!/usr/bin/env python3

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'python'))

from catzilla import Catzilla


async def _yield_once() -> int:
    await asyncio.sleep(0)
    return 1


def create_app() -> Catzilla:
    app = Catzilla(
        production=True,
        use_jemalloc=True,
        memory_profiling=False,
        auto_memory_tuning=True,
    )

    @app.get('/async/raw')
    async def raw_async(request):
        return {
            'framework': 'catzilla',
            'mode': 'raw_async',
            'value': 1,
        }

    @app.get('/async/yield-once')
    async def yield_once(request):
        value = await _yield_once()
        return {
            'framework': 'catzilla',
            'mode': 'yield_once',
            'value': value,
        }

    @app.get('/async/fanout')
    async def fanout_async(request):
        results = await asyncio.gather(_yield_once(), _yield_once(), _yield_once())
        return {
            'framework': 'catzilla',
            'mode': 'fanout_async',
            'value': sum(results),
        }

    @app.get('/async/chain/42')
    async def chain_async(request):
        steps = 42
        total = 0
        for _ in range(steps):
            total += await _yield_once()
        return {
            'framework': 'catzilla',
            'mode': 'chain_async',
            'steps': steps,
            'value': total,
        }

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description='Catzilla async benchmark server')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8070)
    args = parser.parse_args()

    app = create_app()
    app.listen(args.port, args.host)


if __name__ == '__main__':
    main()