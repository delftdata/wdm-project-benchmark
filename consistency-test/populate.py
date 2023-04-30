import asyncio
import json
import logging
import os
from typing import List

import aiohttp

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s - %(asctime)s - %(name)s - %(message)s',
                    datefmt='%I:%M:%S')
logger = logging.getLogger(__name__)

NUMBER_0F_ITEMS = 1
ITEM_STARTING_STOCK = 100
ITEM_PRICE = 1
NUMBER_OF_USERS = 1000
USER_STARTING_CREDIT = 1

with open(os.path.join('..', 'urls.json')) as f:
    urls = json.load(f)
    ORDER_URL = urls['ORDER_URL']
    PAYMENT_URL = urls['PAYMENT_URL']
    STOCK_URL = urls['STOCK_URL']


async def post_and_get_status(session, url):
    async with session.post(url) as resp:
        return resp.status


async def post_and_get_field(session, url, field):
    async with session.post(url) as resp:
        jsn = await resp.json()
        return jsn[field]


async def create_items(session, number_of_items: int, stock: int, price: int) -> List[str]:
    tasks = []
    # Create items
    for _ in range(number_of_items):
        create_item_url = f"{STOCK_URL}/stock/item/create/{price}"
        tasks.append(asyncio.ensure_future(post_and_get_field(session, create_item_url, 'item_id')))
    item_ids : List[str] = await asyncio.gather(*tasks)
    tasks = []
    # Add stock
    for item_id in item_ids:
        create_item_url = f"{STOCK_URL}/stock/add/{item_id}/{stock}"
        tasks.append(asyncio.ensure_future(post_and_get_status(session, create_item_url)))
    await asyncio.gather(*tasks)
    return item_ids


async def create_users(session, number_of_users: int, credit: int) -> List[str]:
    tasks = []
    # Create users
    for _ in range(number_of_users):
        create_user_url = f"{PAYMENT_URL}/payment/create_user"
        tasks.append(asyncio.ensure_future(post_and_get_field(session, create_user_url, 'user_id')))
    user_ids: List[str] = await asyncio.gather(*tasks)
    tasks = []
    # Add funds
    for user_id in user_ids:
        add_funds_url = f"{PAYMENT_URL}/payment/add_funds/{user_id}/{credit}"
        tasks.append(asyncio.ensure_future(post_and_get_status(session, add_funds_url)))
    await asyncio.gather(*tasks)
    return user_ids


async def populate_databases():
    async with aiohttp.ClientSession() as session:
        logger.info("Creating items ...")
        # create item with 100 stock
        item_ids: List[str] = await create_items(session, NUMBER_0F_ITEMS,
                                                 ITEM_STARTING_STOCK, ITEM_PRICE)
        logger.info("Items created")

        logger.info("Creating users ...")
        # create 1000 users
        user_ids: List[str] = await create_users(session, NUMBER_OF_USERS, USER_STARTING_CREDIT)
        logger.info("Users created")
    return item_ids, user_ids
