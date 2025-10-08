from fastapi import APIRouter

from browser.schema import HealthCheckResponse


def route() -> APIRouter:
    """
    This function loads the router.

    :param g: The global instance.
    """

    router = APIRouter(prefix="/health")

    @router.get(
        "",
        summary="Health check",
        responses={200: {"model": HealthCheckResponse}},
    )
    def healthcheck():
        return HealthCheckResponse(
            status="ok",
        )

    return router
