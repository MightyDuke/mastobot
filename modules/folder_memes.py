import random
from pathlib import Path
from mastobot import Module, schedule

class FolderMemes(Module):
    meme_folder = "/home/josef/Downloads/memes"

    @classmethod
    def get_random_meme(cls):
        return random.choice([
            file
            for file in Path(cls.meme_folder).iterdir()
            if file.is_file()
        ])

    async def start(self):
        await self.post_meme()

    @schedule("0 * * * *")
    async def post_meme(self):
        meme = self.get_random_meme()
        await self.post_image(meme)