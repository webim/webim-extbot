"""Модуль настроек логирования и запуска бота"""


import argparse
import logging
import sys
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


def get_logger(verbose):
    formatter = logging.Formatter(
        "[%(asctime)s %(module)s] %(message)s", "%Y-%m-%d %H:%M:%S"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)

    logger = logging.getLogger("extbot")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    return logger


def validate_int(value):
    try:
        int_value = int(value)
        if str(int_value) == value:
            return int_value
    except ValueError:
        pass
    raise argparse.ArgumentTypeError(f"expected integer, not {value!r}")


def positive_int(value):
    int_value = validate_int(value)
    if int_value > 0:
        return int_value
    raise argparse.ArgumentTypeError(f"expected positive integer, not {value!r}")


def tcp_port(value):
    int_value = validate_int(value)
    if _PORT_MIN <= int_value <= _PORT_MAX:
        return int_value
    raise argparse.ArgumentTypeError(
        f"expected integer between {_PORT_MIN} and {_PORT_MAX}, not {value!r}"
    )


def domain(value):
    if validators.domain(value):
        return value
    raise argparse.ArgumentTypeError(
        f"expected domain name, e.g. demo.webim.ru, not {value!r}"
    )


def server_address(value):
    if (
        validators.ipv4(value)
        or validators.ipv6(value)
        or validators.domain(value)
        or all(c in _NAIVE_HOSTNAME_CHAR_SET for c in value)
    ):
        return value
    raise argparse.ArgumentTypeError(f"expected ip address or hostname, not {value!r}")


def get_argument_parser():
    parser = argparse.ArgumentParser(
        prog="extbot",
        description="Webim external bot sample",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
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
    parser.add_argument("--custom-button", help="add extra button with this text")
    parser.add_argument(
        "--custom-button-response",
        help="respond with this text when the custom button is clicked",
    )
    parser.add_argument(
        "--debug",  # deprecated
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--verbose", action="store_true", help="print verbose messages to stdout"
    )
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def main():
    parser = get_argument_parser()
    args = parser.parse_args()

    app = web.Application()

    logger = get_logger(args.verbose or args.debug)

    if args.debug:
        logger.warning(
            "--debug is deprecated and will be removed in a future Extbot version."
            " Please use --verbose instead"
        )

    v1_bot = ApiV1Sample(logger, args.custom_button, args.custom_button_response)

    if args.api_domain and args.api_token:
        v2_bot = ApiV2Sample(
            logger,
            args.api_domain,
            args.api_token,
            args.agent_id,
            args.dep_key,
            args.custom_button,
            args.custom_button_response,
        )
        app.on_cleanup.append(v2_bot.cleanup)
    else:
        v2_bot = None
        logger.warning(
            "Only legacy Bot API v1 will be available."
            " If you intend to use Bot API v2,"
            " see extbot --help for the required arguments"
        )

    router = ApiVersionRouter(logger, v1_bot, v2_bot)

    routes = router.get_routes()
    app.add_routes(routes)

    index_url = f"http://{args.host}:{args.port}/"
    logger.info(f"Exbot is running on {index_url}")

    try:
        web.run_app(app, host=args.host, port=args.port, print=None)
    except Exception as e:
        logger.critical(f"Error running server on {index_url}: {e}")
        sys.exit(1)
