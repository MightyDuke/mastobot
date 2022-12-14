import asyncio
import tempfile
import os
import shutil
from contextlib import asynccontextmanager

class Mega:
    @property
    def __common_arguments(self):
        return "-u", self.config.username, "-p", self.config.password

    def start(self):
        for command in "megals", "megaget":
            if shutil.which(command) is None:
                raise FileNotFoundError(f"Missing command: {command}. Please install megatools.")

    async def ls(self, path):
        process = await asyncio.create_subprocess_exec(
            "megals", *self.__common_arguments, 
            os.path.join("/Root", path.removeprefix("/")),
            stdout=asyncio.subprocess.PIPE
        )
        stdout, _ = await process.communicate()

        return [file.removeprefix("/Root") for file in stdout.decode().splitlines()]

    @asynccontextmanager
    async def get(self, path):
        file_name = tempfile.mktemp()

        process = await asyncio.create_subprocess_exec(
            "megaget", *self.__common_arguments,
            "--path", file_name,
            os.path.join("/Root", path.removeprefix("/")),
            stdout=asyncio.subprocess.PIPE
        )

        await process.wait()

        try:
            with open(file_name, "rb") as opened_file:
                yield opened_file
        finally:
            os.unlink(file_name)
