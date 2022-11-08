import random
from pathlib import Path
from mastobot import Module

class FolderMemes(Module):
    def __init__(self, mastobot):
        super().__init__(mastobot)
        self.last_memes = []

        if not Path(self.meme_folder).is_dir():
            raise ValueError(f"Meme folder {self.meme_folder} doesn't exist")

    def get_random_meme(self):
        possible_memes = set(
            file
            for file in Path(self.meme_folder).iterdir()
            if file.is_file()
        )

        meme = random.choice(tuple(possible_memes - set(self.last_memes)))
        self.last_memes.append(meme)

        if len(self.last_memes) > 10:
            self.last_memes.pop(0)

        return meme

    async def start(self):
        await self.cron(self.post_meme, self.schedule)

    async def post_meme(self):
        while True:
            try:
                meme = self.get_random_meme()
                await self.post_image(meme)
                break
            except Exception as e:
                self.logger.error(f"Error when posting a meme, trying again: {e}")

        self.logger.info(f"Posted a meme: {meme}")