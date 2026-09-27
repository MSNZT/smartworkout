from app.middlewares.exceptions import exception_middleware
from app.middlewares.logger import logging_middleware
from app.middlewares.request_id import request_id_middleware
from app.router import Router


router = Router()

router.use(request_id_middleware)
router.use(logging_middleware)
router.use(exception_middleware)
