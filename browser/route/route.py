from typing import List

from fastapi import APIRouter

from browser.route import converter, healthcheck
from browser.server.server import BrowserServer


def register_routes(server: BrowserServer) -> List[APIRouter]:
    """
    This function registers the route to the FastAPI app.

    :param server: The server object.
    :return: The router that contains all the route.
    """

    # All the routing addresses will start with /v1.
    router = APIRouter(prefix="/v1")

    router.include_router(healthcheck.route())
    router.include_router(converter.route(server))

    return [router]
