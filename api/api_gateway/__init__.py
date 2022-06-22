import asyncio
import threading


def run_in_background(func, *args):
    if asyncio.iscoroutinefunction(func):
        loop = asyncio.get_event_loop()
        loop.create_task(func(*args))
    else:
        t = threading.Thread(target=func, args=args)
        t.start()
