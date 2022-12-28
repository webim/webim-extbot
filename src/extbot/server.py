"""Модуль настроек логирования и запуска бота"""


import logging
import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

from aiohttp import web

from . import __version__
from .api_v1 import ApiV1Sample
from .api_v2 import ApiV2Sample
from .router import ApiVersionRouter


def get_logger(debug):
    formatter = logging.Formatter(
        "[%(asctime)s %(module)s] %(message)s", "%Y-%m-%d %H:%M:%S"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)

    logger = logging.getLogger("extbot")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    return logger


def get_argument_parser():
    parser = ArgumentParser(
        prog="extbot",
        description="Webim external bot sample",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--host", default="localhost", help="bind webhook to this host")
    parser.add_argument(
        "--port", default=8000, type=int, help="bind webhook to this port"
    )
    parser.add_argument(
        "--domain",
        dest="api_domain",
        help="(required for API v2) domain of Webim instance, e.g. demo.webim.ru",
    )
    parser.add_argument(
        "--token",
        dest="api_token",
        help="(required for API v2) token from bot settings",
    )
    parser.add_argument(
        "--agent-id", type=int, help="(API v2) add button to forward chat to this agent"
    )
    parser.add_argument(
        "--dep-key", help="(API v2) add button to forward chat to this department"
    )
    parser.add_argument(
        "--debug", action="store_true", help="display verbose debug messages"
    )
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def main():
    parser = get_argument_parser()
    args = parser.parse_args()

    logger = get_logger(args.debug)

    v1_bot = ApiV1Sample(logger)
    logger.info("API v1 configured")

    if args.api_domain and args.api_token:
        v2_bot = ApiV2Sample(
            logger, args.api_domain, args.api_token, args.agent_id, args.dep_key
        )
        logger.info("API v2 configured")
    else:
        v2_bot = None
        logger.info("API v2 not configured, see extbot --help for required arguments")

    router = ApiVersionRouter(logger, v1_bot, v2_bot)

    routes = [
        web.post("/", router.index),
        web.post("/v1", router.v1),
        web.post("/v2", router.v2),
    ]

    app = web.Application()
    app.add_routes(routes)

    index_url = f"http://{args.host}:{args.port}/"

    logger.info(f"API URL: {index_url} (Webim 10.3+)")
    logger.info(
        f"For older Webim releases specify API version with /v1 or /v2 in the URL"
    )
    web.run_app(app, host=args.host, port=args.port, print=None)
