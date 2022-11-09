import aiocron
import asyncio
import logging
from atoot import MastodonAPI
from functools import wraps

class Module:
    def __init__(self, mastobot):
        self.mastobot = mastobot
        self.logger = logging.getLogger(f"Mastobot.{self.__class__.__name__}")

    async def cron(self, func, spec):
        @wraps(func)
        async def wrapper():
            self.mastobot.logger.info(f"Executing scheduled function \"{func.__qualname__}\"")

            try:
                await func()
            except Exception as e:
                self.mastobot.logger.error(f"Exception occured in \"{func.__qualname__}\": {e}")

        aiocron.crontab(spec, func=lambda: asyncio.create_task(wrapper()))
        self.mastobot.logger.info(f"Scheduled function \"{func.__qualname__}\" with schedule \"{spec}\"")

    async def connect(self):
        if getattr(self, "instance_url", None) == None:
            raise ValueError(f"Module {self.__class__.__name__} is missing instance url")

        if getattr(self, "access_token", None) == None:
            raise ValueError(f"Module {self.__class__.__name__} is missing access token")

        self.api = await MastodonAPI.create(self.instance_url, access_token=self.access_token)
        await self.api.verify_app_credentials()

    async def start(self):
        pass

    async def post_image(self, path):
        with open(path, "rb") as file:
            attachment = await self.api.upload_attachment(file)

        await self.api.create_status(media_ids=(attachment["id"],))