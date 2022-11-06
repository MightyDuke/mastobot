import os
import asyncio
import importlib
import inspect
import aiocron
import logging
import atoot
from pathlib import Path
from functools import wraps

scheduled_functions = {}

def schedule(spec):
    def wrapper(func):
        scheduled_functions[func] = spec
        return func

    return wrapper

class Module:
    def __init__(self, mastobot):
        self.mastobot = mastobot
        self.logger = logging.getLogger(f"Mastobot.{self.__class__.__name__}")
        self.name = self.__class__.__name__

        for member in "access_token", "instance_url":
            if not hasattr(self, member):
                setattr(self, member, os.environ.get(f"mastobot_{self.name}_{member}".upper(), None))

    async def connect(self):
        if getattr(self, "instance_url", None) == None:
            raise ValueError(f"Module {self.name} is missing instance url")

        if getattr(self, "access_token", None) == None:
            raise ValueError(f"Module {self.name} is missing access token")

        self.api = await atoot.MastodonAPI.create(self.instance_url, access_token=self.access_token)
        await self.api.verify_app_credentials()

    async def start(self):
        pass

    def run_scheduled_functions(self):
        for func in scheduled_functions:
            @wraps(func)
            async def wrapper(self):
                self.mastobot.logger.info(f"Executing scheduled function \"{func.__qualname__}\"")

                try:
                    await func(self)
                except Exception as e:
                    self.mastobot.logger.info(f"Exception occured in \"{func.__qualname__}\": {e}")

            aiocron.crontab(scheduled_functions[func], func=lambda: asyncio.create_task(wrapper(self)))

    async def post_image(self, path):
        with open(path, "rb") as file:
            attachment = await self.api.upload_attachment(file)

        await self.api.create_status(media_ids=(attachment["id"],))

class Mastobot:
    def __init__(self, modules_path="modules"):
        self.modules = []
        self.modules_path = modules_path
        self.logger = logging.getLogger("Mastobot")

    async def load_module(self, name):
        python_module = importlib.import_module(f"{self.modules_path}.{name}")
        modules = [
            cls
            for cls_name, cls in inspect.getmembers(python_module, inspect.isclass)
            if cls_name != "Module" and cls.__mro__[-2].__name__ == "Module"
        ]

        for cls in modules:
            module = cls(self)

            try:
                await module.connect()
            except Exception as e:
                module.logger.error(f"Failed to connect: {e}")
                continue

            self.logger.info(f"Loaded module \"{module.name}\" from \"{python_module.__name__}\"")
            self.modules.append(module)

            try:
                await module.start()
            except Exception as e:
                module.logger.error(f"Failed to run start: {e}")
                continue

            module.run_scheduled_functions()

    async def run(self):
        for module_path in Path(self.modules_path).iterdir():
            await self.load_module(module_path.stem)

        await asyncio.wait(asyncio.all_tasks())

__all__ = (Mastobot, Module, schedule)

async def main():
    logging.basicConfig(format="%(levelname)s: (%(name)s) %(message)s", level="INFO")
    logging.getLogger("asyncio").setLevel("CRITICAL")

    mastobot = Mastobot()

    await mastobot.run()

if __name__ == "__main__":
    asyncio.run(main())