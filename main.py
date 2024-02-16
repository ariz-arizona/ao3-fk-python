from interactions import Client, Intents, listen, slash_command, SlashContext, Embed
from interactions.api.events import CommandError

import traceback
import os

from dotenv import load_dotenv

from bs4 import BeautifulSoup
import requests

import random
import json

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

bot = Client(intents=Intents.DEFAULT)


@listen()  # this decorator tells snek that it needs to listen for the corresponding event, and run this coroutine
async def on_ready():
    # This event is called when the bot is ready to respond to commands
    print("Ready")
    print(f"This bot is owned by {bot.owner}")


@listen()
async def on_message_create(event):
    # This event is called when a message is sent in a channel the bot can see
    print(f"message received: {event.message.content}")


@listen(CommandError, disable_default_listeners=True)
async def on_command_error(event: CommandError):
    # tell the dispatcher that this replaces the default listener
    traceback.print_exception(event.error)
    if not event.ctx.responded:
        await event.ctx.send("Something went wrong.")


steps = [
    {
        "step": "season",
        "items": [
            {"name": "fk", "description": "Лето", "url": ""},
            {"name": "wtfk", "description": "Зима", "url": ""},
        ]
    },
    {
        "step": "type",
        "items": [
            {"name": "other", "description": "Визитка/Челлендж"},
            {"name": "img", "description": "Арт"},
            {"name": "txt", "description": "Текст"},
        ]
    },
    {
        "step": "rating",
        "items": [
            {"name": "gt", "description": "G - T"},
            {"name": "me", "description": "M - E"},
        ]
    }
]


@slash_command(name="random", description="Get Random Work")
async def my_command_function(ctx: SlashContext):
    txt = ["Получена команда RANDOM"]
    choice = {}
    message = await ctx.send('\n'.join(txt))

    for element in steps:
        items, step = element['items'], element['step']
        txt.append(f'{step}...')
        await message.edit(content='\n'.join(txt))

        item = random.choice(items)
        txt[-1] = f'{step} -> {item["description"]}'
        choice[step] = item["name"]
        await message.edit(content='\n'.join(txt))

    txt.append(f'get collections list')
    await message.edit(content='\n'.join(txt))

    with open("collections.json", "r") as f:
        data = json.load(f)

    collections = [d for d in data if d["season"] in choice["season"]
                    and choice["type"] in d["type"] and choice["rating"] in d["rating"]]
    choice["collection"] = random.choice(collections)

    txt[-1] = f'find collections: {len(collections)}'
    txt.append(f'random collection: {choice["collection"]["name"]}')
    await message.edit(content='\n'.join(txt))

    r = requests.get(
        f'https://archiveofourown.org/collections/{choice["collection"]["href"]}/works')
    soup = BeautifulSoup(r.content, 'html.parser')
    last_page = soup.select_one('.pagination li:nth-last-child(2) a')
    random_page = random.choice(list(range(1, int(last_page.getText())))) if last_page else 1

    r = requests.get(
        f'https://archiveofourown.org/collections/{choice["collection"]["href"]}/works?page={random_page}')
    soup = BeautifulSoup(r.content, 'html.parser')
    random_work = random.choice(soup.select(
        'li.work .heading > a:first-child'))

    txt.append(f'page: {random_page}, work: {random_work.getText()}')
    await message.edit(content='\n'.join(txt))

    r = requests.get(f"https://archiveofourown.org{random_work.get('href')}")
    soup = BeautifulSoup(r.content, 'html.parser')
    image = soup.select_one("#chapters img")
    textnode = soup.select_one('#chapters')
    
    embed = Embed(
        title=soup.select_one('h2.heading').getText(),
        description=textnode.text[0:100],
        url=f"https://archiveofourown.org{random_work.get('href')}",
        images=[image.get('src')] if choice["type"] in ["img", "other"] and image else []
    )
    await message.edit(embed=embed, content='')

bot.start(TOKEN)
