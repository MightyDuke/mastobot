import asyncio
import tempfile
import os
import uuid
from contextlib import asynccontextmanager
from mastobot import Service

class Mega(Service):
    @property
    def __common_arguments(self):
        return "-u", self.username, "-p", self.password, "--reload"

    async def ls(self, path):
        process = await asyncio.create_subprocess_exec(
            "megals", *self.__common_arguments, "-R",
            f"/Root{path}",
            stdout=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return [file.lstrip("/Root") for file in stdout.decode().splitlines()]

    @asynccontextmanager
    async def get(self, path):
        file_name = os.path.join(tempfile.gettempdir(), uuid.uuid4().hex)

        process = await asyncio.create_subprocess_exec(
            "megaget", *self.__common_arguments,
            "--path", file_name,
            f"/Root{path}",
            stdout=asyncio.subprocess.PIPE
        )

        await process.wait()

        try:
            yield file_name
        finally:
            os.unlink(file_name)
