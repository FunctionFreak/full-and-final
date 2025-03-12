import asyncio
from config.settings import load_settings
from terminal.interface import TerminalInterface

async def main():
    settings = load_settings()
    interface = TerminalInterface(settings)
    await interface.start()

if __name__ == "__main__":
    asyncio.run(main())
