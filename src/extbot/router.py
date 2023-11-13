"""Реализация маршрутизатора для автоматического определения версии API"""


from aiohttp import web


class ApiVersionRouter:
    """Маршрутизатор для автоматического определения версии API"""

    def __init__(self, logger, api_v1_bot, api_v2_bot=None):
        self._log = logger
        self._api_v1_bot = api_v1_bot
        self._api_v2_bot = api_v2_bot

    def get_routes(self):
        return [
            web.post("/", self.index),
            web.post("/v1", self.v1),
            web.post("/v2", self.v2),
        ]

    async def index(self, request):
        api_dialect = request.headers.get("X-Bot-API-Dialect", "")
        api_version = request.headers.get("X-Bot-API-Version", "")
        webim_version = request.headers.get("X-Webim-Version", "")

        full_api_version = f"{api_dialect} {api_version}".strip()
        self._log.debug(
            f"Routing request from Webim version {webim_version!r},"
            f" Bot API version {full_api_version!r}"
        )

        if api_version.startswith("2."):
            return await self.v2(request)
        elif api_version.startswith("1."):
            return await self.v1(request)
        elif not api_version:
            self._log.warning(
                "Received request but could not decide which Bot API version to use."
                " This can happen if you are using an old or non-standard Webim"
                " release. In that case specify Bot API version by adding /v2 or /v1"
                " suffix to Exbot's API URL in Webim settings"
            )
            raise web.HTTPNotFound
        else:
            self._log.warning(
                f"Rejecting request with unsupported Bot API version {api_version!r}."
            )
            raise web.HTTPNotFound

    async def v2(self, request):
        if self._api_v2_bot is None:
            self._log.warning(
                "Rejecting request for Bot API v2 that is not configured."
                " See extbot --help for the required arguments"
            )
            raise web.HTTPNotFound
        return await self._api_v2_bot.webhook(request)

    async def v1(self, request):
        return await self._api_v1_bot.webhook(request)
