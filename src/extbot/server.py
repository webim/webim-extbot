"""Модуль настроек логирования и запуска бота"""


import logging
import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

from aiohttp import web

from . import __version__
from .api_v1 import ApiV1Sample
from .api_v2 import ApiV2Sample


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

    routes = []

    if args.api_domain and args.api_token:
        v2_bot = ApiV2Sample(
            logger, args.api_domain, args.api_token, args.agent_id, args.dep_key
        )
        v2_route = web.post("/v2", v2_bot.webhook)
        routes.append(v2_route)
        logger.info(f"API v2 URL: http://{args.host}:{args.port}/v2")
    else:
        logger.info("API v2 not available, see extbot --help for required arguments")

    v1_bot = ApiV1Sample(logger)
    v1_route = web.post("/v1", v1_bot.webhook)
    routes.append(v1_route)
    logger.info(f"API v1 URL: http://{args.host}:{args.port}/v1")

    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, host=args.host, port=args.port, print=None)
