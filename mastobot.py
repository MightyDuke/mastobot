#!/usr/bin/env python3

import os
import asyncio
import importlib
import inspect
import logging
import re
from pathlib import Path
from modules import Module
from services import Service

class Mastobot:
    @staticmethod
    def assign_env_variables(instance, pattern):
        for key, value in os.environ.items():
            if match := re.match(pattern, key, re.IGNORECASE):
                attribute = match.group(1).lower()

                if not hasattr(instance, attribute):
                    setattr(instance.__class__, attribute, value)

    def __init__(self, modules_path="modules", services_path="services"):
        self.modules = []
        self.services = {}
        self.modules_path = modules_path
        self.services_path = services_path
        self.logger = logging.getLogger("Mastobot")

    def get_classes(self, path, name, base_cls):
        return [
            cls(self)
            for _, cls in inspect.getmembers(importlib.import_module(f"{path}.{name}"))
            if inspect.isclass(cls) and cls != base_cls and issubclass(cls, base_cls)
        ]

    async def load_service(self, name):
        for service in self.get_classes(self.services_path, name, Service):
            self.assign_env_variables(service, rf"MASTOBOT_SERVICE_{service.__class__.__name__}_(\S+)")
            self.logger.info(f"Loaded service \"{service.__class__.__name__}\" from \"{service.__module__}\"")

            self.services[service.__class__.__name__.lower()] = service

    async def load_module(self, name):
        for module in self.get_classes(self.modules_path, name, Module):
            self.assign_env_variables(module, rf"MASTOBOT_MODULE_{module.__class__.__name__}_(\S+)")

            try:
                await module.connect()
            except Exception as e:
                module.logger.error(f"Failed to connect: {e}")
                continue

            self.logger.info(f"Loaded module \"{module.__class__.__name__}\" from \"{module.__module__}\"")

            for key, value in self.services.items():
                setattr(module, key, value)

            self.modules.append(module)

            try:
                await module.start()
            except Exception as e:
                module.logger.error(f"Failed to run start: {e}")
                continue

    async def run(self):
        for service_path in Path(self.services_path).iterdir():
            await self.load_service(service_path.stem)

        for module_path in Path(self.modules_path).iterdir():
            await self.load_module(module_path.stem)

        await asyncio.wait(asyncio.all_tasks())

async def main():
    logging.basicConfig(format="%(levelname)s: (%(name)s) %(message)s", level="INFO")
    logging.getLogger("asyncio").setLevel("CRITICAL")

    mastobot = Mastobot()

    await mastobot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass