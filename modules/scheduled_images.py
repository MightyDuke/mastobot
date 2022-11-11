import random
import asyncio
import aiocron
from collections import deque
from mastobot import Module

class ScheduledImages(Module):
    async def start(self):
        self.last_images = deque(maxlen=10)

        if not self.file_service_name in self.mastobot.services:
            raise KeyError(f"Missing service: {self.file_service_name}")

        self.file_service = self.mastobot.services[self.file_service_name]

        async def wrapper():
            self.logger.info(f"Posting scheduled image")
            await self.post_image()

        aiocron.crontab(self.schedule, func=lambda: asyncio.create_task(wrapper()))
        self.logger.info(f"Scheduled posting an image with schedule \"{self.schedule}\"")

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
            return await self.post_image()

        self.logger.info(f"Posted an image: {image}")