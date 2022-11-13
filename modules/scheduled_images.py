import random
from collections import deque
from mastobot import Module

class ScheduledImages(Module):
    async def start(self):
        self.last_images = deque(maxlen=10)
        self.file_service = self.mastobot.services[self.file_service_name]

        await self.cron(self.post_scheduled_image, self.schedule)

    async def get_random_image(self):
        possible_images = await self.file_service.ls(self.image_folder)

        image = random.choice(tuple(set(possible_images) - set(self.last_images)))
        self.last_images.append(image)

        return image

    async def post_scheduled_image(self):
        try:
            image = await self.get_random_image()

            async with self.file_service.get(image) as file:
                attachment = await self.api.upload_attachment(file)

            await self.api.create_status(media_ids=(attachment["id"],))

        except Exception as e:
            self.logger.error(f"Error when posting an image, trying again: {e}")
            return await self.post_scheduled_image()

        self.logger.info(f"Posted an image: {image}")