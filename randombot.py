import asyncio
import datetime
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

client = TelegramClient(NAME, API_ID, API_HASH).start(
    bot_token=TOKEN)
client.flood_sleep_threshold = 24 * 60 * 60

clicked = asyncio.Event()
chosen = None


async def kick_users():
    global chosen
    while True:
        clicked.clear()
        users = await client.get_participants(GROUP)
        chosen = random.choice(users)
        chosen.name = html.escape(utils.get_display_name(chosen))
        start = time.time()
        try:
            await kick_user()
        except Exception as e:
            print(e)
        took = time.time() - start
        wait_after_clicked = 8 * 60 * 60 - took
        if wait_after_clicked > 0:
            await asyncio.sleep(DELAY - took)


async def kick_user():
    await client.send_message(
        GROUP,
        "<a href='tg://user?id={}'>{}: you have 1 day to click this button or"
        " you will be automatically kicked</a>".format(chosen.id, chosen.name),
        buttons=Button.inline('click me to stay', b'alive'), parse_mode="html"
    )
    try:
        await asyncio.wait_for(clicked.wait(), DELAY)
    except asyncio.TimeoutError:
        await client.send_message(
            GROUP,
            "<a href='tg://user?id={}'>{} was kicked for being inactive</a>"
            .format(chosen.id, chosen.name), parse_mode='html'
        )
        await client(EditBannedRequest(GROUP, chosen.id, ChannelBannedRights(
            until_date=datetime.timedelta(minutes=1),
            view_messages=True
        )))


@client.on(events.CallbackQuery)
async def save_him(event: events.CallbackQuery.Event):
    if event.sender_id == chosen.id:
        await event.answer("Congrats you are saved", 0)
        clicked.set()
        await event.edit(
            "<a href='tg://user?id={}'>Congrats {} you made it!</a>".format(
            chosen.id, chosen.name), parse_mode="html")
    else:
        await event.answer("Who are you again?", 0)


loop = asyncio.get_event_loop()
loop.create_task(kick_users())
client.run_until_disconnected()
