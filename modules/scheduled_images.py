import random
import asyncio
import aiocron
from collections import deque
from mastobot import Module
from functools import wraps

class ScheduledImages(Module):
    async def cron(self, func, spec):
        @wraps(func)
        async def wrapper():
            self.mastobot.logger.info(f"Executing scheduled function \"{self.name}.{func.__name__}\"")

            try:
                await func()
            except Exception as e:
                self.mastobot.logger.error(f"Exception occured in scheduled function \"{self.name}.{func.__name__}\": {e}")

        aiocron.crontab(spec, func=lambda: asyncio.create_task(wrapper()))
        self.mastobot.logger.info(f"Scheduled function \"{self.name}.{func.__name__}\" with schedule \"{spec}\"")

    async def start(self):
        self.last_images = deque(maxlen=10)
        self.file_service = self.mastobot.services[self.file_service_name]
        await self.cron(self.post_image, self.schedule)

    async def get_random_image(self):
        possible_images = await self.file_service.ls(self.image_folder)

        image = random.choice(tuple(set(possible_images) - set(self.last_images)))
        self.last_images.append(image)

        return image

    async def post_image(self):
        try:
            image = await self.get_random_image()

            async with self.file_service.get(image) as file:
                await self.post_image(file)
        except Exception as e:
            self.logger.error(f"Error when posting an image, trying again: {e}")
            return self.post_image()

        self.logger.info(f"Posted an image: {image}")