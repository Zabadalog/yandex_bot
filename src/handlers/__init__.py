import dp

from .registration import router as registration_router
from .status       import router as status_router
from .yandex       import router as yandex_router
from .tracking     import router as tracking_router
from .help         import router as help_router

__all__ = [
    registration_router,
    status_router,
    yandex_router,
    tracking_router,
    help_router,
]