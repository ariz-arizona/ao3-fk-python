import re

from interactions import Client, Intents, listen, slash_command, SlashContext, Embed, FlatUIColors
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
        "step": "year",
        "items": [
            {"name": "2020", "description": "2020", "season": ["fk"]},
            {"name": "2021", "description": "2021", "season": ["fk", "wtfk"]},
            {"name": "2022", "description": "2022", "season": ["fk", "wtfk"]},
            {"name": "2023", "description": "2023", "season": ["fk", "wtfk"]},
            {"name": "2024", "description": "2024", "season": ["fk"]},
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
    try:
        txt = ["Получена команда RANDOM"]
        choice = {}
        message = await ctx.send('\n'.join(txt))

        for element in steps:
            items, step = element['items'], element['step']
            txt.append(f'{step}...')
            await message.edit(content='\n'.join(txt))

            item = random.choice(
                [i for i in items if choice["season"] in i["season"]] if step == "year" else items)
            txt[-1] = f'{step} -> {item["description"]}'
            choice[step] = item["name"]
            await message.edit(content='\n'.join(txt))

        txt.append(f'get collections list')
        await message.edit(content='\n'.join(txt))

        with open("collections.json", "r") as f:
            data = json.load(f)

        collections = [d for d in data if
                       d["season"] in choice["season"]
                       and choice["type"] in d["type"]
                       and choice["rating"] in d["rating"]
                       and choice["year"] in d["year"]
                       ]
        if not len(collections):
            txt.append('Коллекций по этим параметрам не найдено')
            await message.edit(content='\n'.join(txt))
            return

        choice["collection"] = random.choice(collections)

        txt[-1] = f'find collections: {len(collections)}'
        txt.append(f'random collection: {choice["collection"]["name"]}')
        await message.edit(content='\n'.join(txt))

        works_url = f'https://archiveofourown.org/collections/{choice["collection"]["href"]}/works'
        works_query = []
        if choice['rating'] == 'gt':
            works_query = [
                "exclude_work_search[rating_ids][]=12",
                "exclude_work_search[rating_ids][]=13"
            ]
        elif choice['rating'] == 'me':
            works_query = [
                "exclude_work_search[rating_ids][]=10",
                "exclude_work_search[rating_ids][]=11"
            ]

        r = requests.get(f"{works_url}?{'&'.join(works_query)}")
        soup = BeautifulSoup(r.content, 'html.parser')
        last_page = soup.select_one('.pagination li:nth-last-child(2) a')
        random_page = random.choice(
            list(range(1, int(last_page.getText())))) if last_page else 1

        works_query.append(f"page={random_page}")
        r = requests.get(f"{works_url}?{'&'.join(works_query)}")
        soup = BeautifulSoup(r.content, 'html.parser')
        random_work = random.choice(soup.select(
            'li.work .heading > a:first-child'))

        txt.append(f'page: {random_page}, work: {random_work.getText()}')
        await message.edit(content='\n'.join(txt))

        r = requests.get(
            f"https://archiveofourown.org{random_work.get('href')}?view_full_work=true&view_adult=true")
        soup = BeautifulSoup(r.content, 'html.parser')

        image = soup.select_one("#chapters img")
        textnode = re.sub(
            r"\n+", '\n', soup.select_one('#chapters').text, flags=re.MULTILINE).strip()
        rating = soup.select_one('.rating li a').getText().lower()
        ratingColors = {
            "explicit": FlatUIColors.ALIZARIN,
            "mature": FlatUIColors.CLOUDS,
            "teen and up audiences": FlatUIColors.SUNFLOWER,
            "general audiences": FlatUIColors.EMERLAND,
            "not rated": FlatUIColors.SILVER
        }
        freeform = [item.getText() for item in soup.select('.freeform li a')] or ['no freeform tags']
        character = [item.getText() for item in soup.select('.character li a')] or ['no character tags']
        fandom = [item.getText() for item in soup.select('.fandom li a')] or ['no fandom tags']
        category = [item.getText() for item in soup.select('.category li a')] or ['no category tags']

        embed = Embed(
            title=soup.select_one('h2.heading').getText(),
            description=' '.join(textnode.split(' ')[0:100]),
            url=f"https://archiveofourown.org{random_work.get('href')}",
            images=[image.get('src')] if choice["type"] in [
                "img", "other"] and image else [],
            color=ratingColors[rating],
            fields=[
                {"name": 'category', "value": ', '.join(category)},
                {"name": 'fandom', "value": ', '.join(fandom)},
                {"name": 'character', "value": ', '.join(character)},
                {"name": 'freeform', "value": ', '.join(freeform)},
                {"name": 'collection', "value": choice["collection"]["name"]}
            ]
        )
        await message.edit(embed=embed, content='')
    except Exception as e:
        raise e


bot.start(TOKEN)
