from asyncio import gather, ensure_future, get_event_loop, iscoroutine, iscoroutinefunction
from collections import namedtuple
from collections.abc import Iterable
from functools import partial
from typing import List
Loader = namedtuple('Loader', 'key,future')

class DataLoader(object):
    batch = True
    max_batch_size = None
    cache = True

    def __init__(self, batch_load_fn=None, batch=None, max_batch_size=None, cache=None, get_cache_key=None, cache_map=None, loop=None):
        self._loop = loop
        if batch_load_fn is not None:
            self.batch_load_fn = batch_load_fn
        assert iscoroutinefunctionorpartial(self.batch_load_fn), 'batch_load_fn must be coroutine. Received: {}'.format(self.batch_load_fn)
        if not callable(self.batch_load_fn):
            raise TypeError('DataLoader must be have a batch_load_fn which accepts Iterable<key> and returns Future<Iterable<value>>, but got: {}.'.format(batch_load_fn))
        if batch is not None:
            self.batch = batch
        if max_batch_size is not None:
            self.max_batch_size = max_batch_size
        if cache is not None:
            self.cache = cache
        self.get_cache_key = get_cache_key or (lambda x: x)
        self._cache = cache_map if cache_map is not None else {}
        self._queue = []

    def load(self, key=None):
        """
        Loads a key, returning a `Future` for the value represented by that key.
        """
        if key is None:
            raise ValueError("The load method requires a key")

        cache_key = self.get_cache_key(key)

        if self.cache and cache_key in self._cache:
            return self._cache[cache_key]

        future = self._loop.create_future() if self._loop else get_event_loop().create_future()
        self._queue.append(Loader(key=key, future=future))

        if self.cache:
            self._cache[cache_key] = future

        if not self.batch:
            ensure_future(dispatch_queue(self))
        elif len(self._queue) >= (self.max_batch_size or float('inf')):
            ensure_future(dispatch_queue(self))

        return future

    def load_many(self, keys):
        """
        Loads multiple keys, returning a list of values

        >>> a, b = await my_loader.load_many([ 'a', 'b' ])

        This is equivalent to the more verbose:

        >>> a, b = await gather(
        >>>    my_loader.load('a'),
        >>>    my_loader.load('b')
        >>> )
        """
        if not isinstance(keys, Iterable):
            raise TypeError("The loader.load_many() method must be called with Iterable<key> but got: {}".format(keys))

        return gather(*[self.load(key) for key in keys])

    def clear(self, key):
        """
        Clears the value at `key` from the cache, if it exists. Returns itself for
        method chaining.
        """
        cache_key = self.get_cache_key(key)
        if cache_key in self._cache:
            del self._cache[cache_key]
        return self

    def clear_all(self):
        """
        Clears the entire cache. To be used when some event results in unknown
        invalidations across this particular `DataLoader`. Returns itself for
        method chaining.
        """
        self._cache.clear()
        return self

    def prime(self, key, value):
        """
        Adds the provided key and value to the cache. If the key already exists, no
        change is made. Returns itself for method chaining.
        """
        cache_key = self.get_cache_key(key)
        if cache_key not in self._cache:
            future = self._loop.create_future() if self._loop else get_event_loop().create_future()
            future.set_result(value)
            self._cache[cache_key] = future
        return self

def dispatch_queue(loader):
    """
    Given the current state of a Loader instance, perform a batch load
    from its current queue.
    """
    queue = loader._queue
    loader._queue = []

    if not queue:
        return

    keys = [l.key for l in queue]
    try:
        batch_future = loader.batch_load_fn(keys)
        if not iscoroutine(batch_future):
            raise ValueError("DataLoader batch_load_fn must return a coroutine.")
    except Exception as e:
        return failed_dispatch(loader, queue, e)

    def batch_callback(results):
        if len(results) != len(keys):
            return failed_dispatch(
                loader,
                queue,
                ValueError(
                    "DataLoader must resolve a list of the same length as the list of keys."
                    "\nExpected {} values, received {}.".format(len(keys), len(results))
                ),
            )

        for l, value in zip(queue, results):
            if isinstance(value, Exception):
                l.future.set_exception(value)
            else:
                l.future.set_result(value)

        return results

    return ensure_future(batch_future).add_done_callback(
        lambda future: batch_callback(future.result())
    )

def failed_dispatch(loader, queue, error):
    """
    Do not cache individual loads if the entire batch dispatch fails,
    but still reject each request so they do not hang.
    """
    for l in queue:
        if loader.cache:
            loader.clear(l.key)
        l.future.set_exception(error)
