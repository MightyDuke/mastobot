import random
from pathlib import Path
from mastobot import Module

class FolderMemes(Module):
    @classmethod
    def get_random_meme(cls):
        return random.choice([
            file
            for file in Path(cls.meme_folder).iterdir()
            if file.is_file()
        ])

    async def start(self):
        await self.cron(self.post_meme, self.schedule)
        await self.post_meme()

    async def post_meme(self):
        meme = self.get_random_meme()
        await self.post_image(meme)