import asyncio

import telegram

with open("/Users/kashnitskiyy/scrt/ods_jobs_dump_bot") as f:
    TOKEN = f.read().strip()


async def main():
    bot = telegram.Bot(TOKEN)
    async with bot:
        print(await bot.get_me())


# async def main():
#    bot = telegram.Bot(TOKEN)
#    async with bot:
#        print((await bot.get_updates())[0])

# async def main():
#     bot = telegram.Bot(TOKEN)
#     async with bot:
#         await bot.send_message(text='Hi John!', chat_id=297791890)

if __name__ == "__main__":
    asyncio.run(main())
