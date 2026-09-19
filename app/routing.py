from app.router import Router
from app.middlewares.logger import logging_middleware
from app.middlewares.request_id import request_id_middleware

router: Router = Router()
router.use(request_id_middleware)
router.use(logging_middleware)