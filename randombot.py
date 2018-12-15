import asyncio
import html
import logging
import os
import random
import time

from telethon import TelegramClient, events, utils
from telethon.tl.custom import Button
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChannelBannedRights

logging.basicConfig(level=logging.INFO)

try:
    API_ID = os.environ['TG_API_ID']
    API_HASH = os.environ['TG_API_HASH']
    TOKEN = os.environ['TG_TOKEN']
except KeyError as e:
    print(e.args[0], 'missing from environment variables')
    exit(0)

NAME = TOKEN.split(':')[0]
GROUP = "telethonofftopic"
DELAY = 24 * 60 * 60
RIGHTS = ChannelBannedRights(
    until_date=None,
    view_messages=True
)

client = TelegramClient(NAME, API_ID, API_HASH).start(
    bot_token=TOKEN)
client.flood_sleep_threshold = 24 * 60 * 60

clicked = False
chosen = None


async def kick_user():
    global chosen, clicked
    clicked = False
    kick_time = int(time.time()) + DELAY
    users = await client.get_participants(GROUP)
    chosen = random.choice(users)
    chosen.name = html.escape(utils.get_display_name(chosen))
    buttons = Button.inline('click me to stay', b'alive')
    await client.send_message(GROUP,
                              "<a href='tg://user?id={}'>{} : you have 1 day to click on this button or you will be"
                              " automatically kicked</a>".format(
                                  chosen.id, chosen.name),
                              buttons=buttons, parse_mode="html")
    while True:
        await asyncio.sleep(1)
        if clicked:
            await asyncio.sleep(kick_time - int(time.time()))
            asyncio.ensure_future(kick_user())
            return
        if int(time.time()) >= kick_time:
            try:
                await client.send_message(GROUP,
                                          "<a href='tg://user?id={}'>{} was kicked for being inactive</a>".format(
                                              chosen.id, chosen.name),
                                          parse_mode='html')
                await client(EditBannedRequest(GROUP, chosen.id, RIGHTS))

            except Exception as e:
                print(e)
            asyncio.ensure_future(kick_user())
            return


async def main_func():
    asyncio.ensure_future(kick_user())


@client.on(events.CallbackQuery)
async def save_him(event: events.CallbackQuery.Event):
    global chosen, clicked
    if event.original_update.user_id == chosen.id:
        await event.answer("Congrats you are saved", 0)
        clicked = True
        await event.edit("<a href='tg://user?id={}'>Congrats {} you made it !</a>".format(
            chosen.id, chosen.name),
            parse_mode="html")
    else:
        await event.answer("Who are you again ? ", 0)


asyncio.get_event_loop().run_until_complete(main_func())
client.run_until_disconnected()
