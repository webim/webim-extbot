"""Модуль настроек логирования и запуска бота"""


import asyncio
import logging
import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, ArgumentTypeError
from string import ascii_letters, digits

import validators
from aiohttp import web

from . import __version__
from .api_v1 import ApiV1Sample
from .api_v2 import ApiV2Sample
from .router import ApiVersionRouter

_PORT_MIN = 1
_PORT_MAX = 65535
_NAIVE_HOSTNAME_CHAR_SET = set(ascii_letters + digits + "_-")


def get_event_loop():
    loop = asyncio.new_event_loop()
    # aiohttp передаёт исключения при запуске сервера в loop.call_exception_handler, но
    # в вызов web.run_app исключение тоже пробрасывается; чтобы дважды не обрабатывать,
    # в exception handler'е игнорируем
    loop.set_exception_handler(lambda _loop, _context: ...)
    return loop


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


def validate_int(value):
    try:
        int_value = int(value)
        if str(int_value) == value:
            return int_value
    except ValueError:
        pass
    raise ArgumentTypeError(f"expected integer, not {value!r}")


def positive_int(value):
    int_value = validate_int(value)
    if int_value > 0:
        return int_value
    raise ArgumentTypeError(f"expected positive integer, not {value!r}")


def tcp_port(value):
    int_value = validate_int(value)
    if _PORT_MIN <= int_value <= _PORT_MAX:
        return int_value
    raise ArgumentTypeError(
        f"expected integer between {_PORT_MIN} and {_PORT_MAX}, not {value!r}"
    )


def domain(value):
    if validators.domain(value):
        return value
    raise ArgumentTypeError(f"expected domain name, e.g. demo.webim.ru, not {value!r}")


def server_address(value):
    if (
        validators.ipv4(value)
        or validators.ipv6(value)
        or validators.domain(value)
        or all(c in _NAIVE_HOSTNAME_CHAR_SET for c in value)
    ):
        return value
    raise ArgumentTypeError(f"expected ip address or hostname, not {value!r}")


def get_argument_parser():
    parser = ArgumentParser(
        prog="extbot",
        description="Webim external bot sample",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--host",
        default="localhost",
        type=server_address,
        help="bind webhook to this host",
    )
    parser.add_argument(
        "--port", default=8000, type=tcp_port, help="bind webhook to this port"
    )
    parser.add_argument(
        "--domain",
        dest="api_domain",
        type=domain,
        help="(required for API v2) domain of Webim instance, e.g. demo.webim.ru",
    )
    parser.add_argument(
        "--token",
        dest="api_token",
        help="(required for API v2) token from bot settings",
    )
    parser.add_argument(
        "--agent-id",
        type=positive_int,
        help="(API v2) add button to forward chat to this agent",
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

    app = web.Application()

    logger = get_logger(args.debug)

    v1_bot = ApiV1Sample(logger)
    logger.info("API v1 configured")

    if args.api_domain and args.api_token:
        v2_bot = ApiV2Sample(
            logger, args.api_domain, args.api_token, args.agent_id, args.dep_key
        )
        app.on_cleanup.append(v2_bot.cleanup)
        logger.info("API v2 configured")
    else:
        v2_bot = None
        logger.info("API v2 not configured, see extbot --help for required arguments")

    router = ApiVersionRouter(logger, v1_bot, v2_bot)

    routes = router.get_routes()
    app.add_routes(routes)

    loop = get_event_loop()

    index_url = f"http://{args.host}:{args.port}/"

    logger.info(f"API URL: {index_url} (Webim 10.3+)")
    logger.info(
        "For older Webim releases specify API version with /v1 or /v2 in the URL"
    )

    try:
        web.run_app(app, host=args.host, port=args.port, print=None, loop=loop)
    except Exception as e:
        logger.critical(f"Error running server on {index_url}: {e}")
        sys.exit(1)
