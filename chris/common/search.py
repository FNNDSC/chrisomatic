"""
These types are private because they represent analogous
features between _ChRIS_ store and _CUBE_, but are not
directly interoperable.
e.g. `https://chrisstore.co/api/v1/plugins/search`
and `https://cube.chrisproject.org/api/v1/plugins/search/`
are analogous but one wouldn't make sense in the context
of the other.
"""
from typing import NewType, Optional, TypeVar, Any, AsyncGenerator, Type, AsyncIterable

import aiohttp
from serde import deserialize, from_dict
from serde.json import from_json


PaginatedUrl = NewType('PluginSearchUrl', str)
T = TypeVar('T')


@deserialize
class _Paginated:
    count: int
    next: Optional[PaginatedUrl]
    previous: Optional[PaginatedUrl]
    results: list[Any]


async def get_paginated(session: aiohttp.ClientSession, url: PaginatedUrl,
                        element_type: Type[T],
                        max_requests: int = 100) -> AsyncGenerator[T, None]:
    if max_requests <= 0:
        raise TooMuchPaginationException()
    res = await session.get(url)
    data: _Paginated = from_json(_Paginated, await res.text())
    for element in data.results:
        yield from_dict(element_type, element)
    if data.next is not None:
        next_results = get_paginated(session, url, element_type,
                                     max_requests - data.count)
        async for next_element in next_results:
            yield next_element


async def peek(x: AsyncIterable[T], mt: Type[Exception] = ValueError) -> T:
    async for e in x:
        return e
    raise mt('x is empty')


class TooMuchPaginationException(Exception):
    pass
