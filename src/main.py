import asyncio

from src.bot.globals import launch_bot
from src.bot.handlers import *


def main():
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s][%(levelname)s][%(name)s]: %(message)s",
                        datefmt="%d.%m.%y %H:%M:%S")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    launch_bot()


if __name__ == "__main__":
    main()
