#!/usr/bin/env python3

import asyncio
import importlib
import inspect
import logging
import configparser
import argparse
import aiocron
from atoot import MastodonAPI

class Module:
    async def cron(self, func, spec):
        async def wrapper():
            self.logger.info(f"Executing scheduled function \"{func.__name__}\"")

            try:
                await func()
            except Exception as e:
                self.logger.error(f"Exception occured in scheduled function \"{func.__name__}\": {e}")

        aiocron.crontab(spec, func=lambda: asyncio.create_task(wrapper()))
        self.logger.info(f"Scheduled function \"{func.__name__}\" with schedule \"{spec}\"")

    async def connect(self):
        if getattr(self, "instance_url", None) == None:
            raise ValueError(f"Module {self.name} is missing instance url")

        if getattr(self, "access_token", None) == None:
            raise ValueError(f"Module {self.name} is missing access token")

        self.api = await MastodonAPI.create(self.instance_url, access_token=self.access_token)
        await self.api.verify_app_credentials()

    async def post_status(self, status):
        await self.api.create_status(status=status)

    async def post_image(self, path):
        with open(path, "rb") as file:
            attachment = await self.api.upload_attachment(file)

        await self.api.create_status(media_ids=(attachment["id"],))

class Mastobot:
    def __init__(self, config_path):
        self.modules = {}
        self.services = {}

        self.logger = logging.getLogger("Mastobot")

        self.config = configparser.ConfigParser()
        self.config.read(config_path)

    async def load_instance(self, type, config, instance_dict, call_connect):
        components = config[type].split(".")

        try:
            cls = getattr(importlib.import_module(str.join(".", components[:-1])), components[-1])
            instance = cls()
        except Exception as e:
            raise ImportError(f"Failed to load {type} \"{config.name}\" from class \"{config[type]}\"")

        instance.name = config.name
        instance.mastobot = self
        instance.logger = logging.getLogger(f"Mastobot.{config.name}")

        for key, value in config.items():
            if key == type:
                continue

            if not hasattr(instance, key) or not hasattr(instance.__class__, key):
                setattr(instance, key, value)

        if call_connect:
            try:
                await instance.connect()
            except Exception as e:
                raise RuntimeError(f"Failed to connect with {type} {config.name}: {e}")

        self.logger.info(f"Loaded {type} \"{config.name}\" from class \"{config[type]}\"")

        try:
            if callable(getattr(instance, "start", None)):
                result = instance.start()

                if inspect.isawaitable(result):
                    await result
        except Exception as e:
            raise RuntimeError(f"Failed to run start on {type} \"{config.name}\": {e}")

        if config.name in instance_dict:
            raise RuntimeError(f"{type.capitalize()} \"{config.name}\" already exists")

        instance_dict[config.name] = instance

    async def load_instances(self, type, instance_dict, call_connect):
        instance_tasks = []

        for section in self.config.sections():
            if type in self.config[section]:
                instance_tasks.append(asyncio.create_task(
                    self.load_instance(type, self.config[section], instance_dict, call_connect))
                )

        await asyncio.wait(instance_tasks)

    async def start(self):
        await self.load_instances("service", self.services, False)
        await self.load_instances("module", self.modules, True)

    def run(self):
        loop = asyncio.new_event_loop()
        loop.set_exception_handler(lambda _, context: self.logger.error(context["exception"]))

        loop.run_until_complete(self.start())
        loop.run_forever()

def main():
    logging.basicConfig(format="%(levelname)s: (%(name)s) %(message)s", level="INFO")
    logging.getLogger("asyncio").setLevel("CRITICAL")

    parser = argparse.ArgumentParser(
        "mastobot", 
        description="Bot for posting things on Mastodon"
    )

    parser.add_argument("-c", "--config", nargs="?", default="config.ini", help="Config path")
    args = parser.parse_args()

    mastobot = Mastobot(args.config)
    mastobot.run()

if __name__ == "__main__":
    main()