import random
from mastobot import Module

class FolderMemes(Module):
    def __init__(self, mastobot):
        super().__init__(mastobot)
        self.last_memes = []

    async def get_random_meme(self):
        possible_memes = await self.mega.ls(self.meme_folder)

        meme = random.choice(tuple(set(possible_memes) - set(self.last_memes)))
        self.last_memes.append(meme)

        if len(self.last_memes) > 10:
            self.last_memes.pop(0)

        return meme

    async def start(self):
        await self.cron(self.post_meme, self.schedule)

    async def post_meme(self):
        while True:
            try:
                meme = await self.get_random_meme()

                async with self.mega.get(meme) as file:
                    await self.post_image(file)

                break
            except Exception as e:
                self.logger.error(f"Error when posting a meme, trying again: {e}")

        self.logger.info(f"Posted a meme: {meme}")