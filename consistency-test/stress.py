import asyncio
import json
import logging
import os
import random
from tempfile import gettempdir

import aiohttp

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s - %(asctime)s - %(name)s - %(message)s',
                    datefmt='%I:%M:%S')
logger = logging.getLogger(__name__)

tmp_folder_path: str = os.path.join(gettempdir(), 'wdm_consistency_test')

NUMBER_OF_ORDERS = 1000

with open(os.path.join('..', 'urls.json')) as f:
    urls = json.load(f)
    ORDER_URL = urls['ORDER_URL']
    PAYMENT_URL = urls['PAYMENT_URL']
    STOCK_URL = urls['STOCK_URL']


async def create_order(session, url):
    async with session.post(url) as resp:
        jsn = await resp.json()
        return jsn['order_id']


async def post_and_get_status(session, url, checkout=None):
    async with session.post(url) as resp:
        if checkout:
            if 400 <= resp.status < 500:
                log = f"CHECKOUT | ORDER: {checkout[0]} USER: {checkout[1]} FAIL __OUR_LOG__\n"
                checkout[2].write(log)
            else:
                log = f"CHECKOUT | ORDER: {checkout[0]} USER: {checkout[1]} SUCCESS __OUR_LOG__\n"
                checkout[2].write(log)
        return resp.status


async def create_orders(session, item_ids, user_ids, number_of_orders):
    tasks = []
    # Create orders
    orders_user_id = []
    for _ in range(number_of_orders):
        user_id = random.choice(user_ids)
        orders_user_id.append(user_id)
        create_order_url = f"{ORDER_URL}/orders/create/{user_id}"
        tasks.append(asyncio.ensure_future(create_order(session, create_order_url)))
    order_ids = list(await asyncio.gather(*tasks))
    tasks = []
    # Add items
    for order_id in order_ids:
        item_id = random.choice(item_ids)
        create_item_url = f"{ORDER_URL}/orders/addItem/{order_id}/{item_id}/1"
        tasks.append(asyncio.ensure_future(post_and_get_status(session, create_item_url)))
    await asyncio.gather(*tasks)
    return order_ids, orders_user_id


async def perform_checkouts(session, order_ids, orders_user_id, log_file):
    tasks = []
    for i, order_id in enumerate(order_ids):
        url = f"{ORDER_URL}/orders/checkout/{order_id}"
        tasks.append(asyncio.ensure_future(post_and_get_status(session, url,
                                                               checkout=(order_id, orders_user_id[i], log_file))))
    order_responses = await asyncio.gather(*tasks)
    return order_responses


async def stress(item_ids, user_ids):
    async with aiohttp.ClientSession() as session:
        logger.info("Creating orders...")
        order_ids, orders_user_id = await create_orders(session, item_ids, user_ids, NUMBER_OF_ORDERS)
        logger.info("Orders created ...")
        logger.info("Running concurrent checkouts...")
        with open(f"{tmp_folder_path}/consistency-test.log", "w") as log_file:
            await perform_checkouts(session, order_ids, orders_user_id, log_file)
        logger.info("Concurrent checkouts finished...")
