import asyncio
import re
import os
import json
import logging
from typing import Union, List, Dict, Tuple

import aiohttp

from populate import NUMBER_0F_ITEMS, ITEM_STARTING_STOCK, ITEM_PRICE, NUMBER_OF_USERS, USER_STARTING_CREDIT


CORRECT_USER_STATE = (NUMBER_OF_USERS * USER_STARTING_CREDIT) - (NUMBER_0F_ITEMS * ITEM_STARTING_STOCK * ITEM_PRICE)

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s - %(asctime)s - %(name)s - %(message)s',
                    datefmt='%I:%M:%S')
logger = logging.getLogger(__name__)

with open(os.path.join('..', 'urls.json')) as f:
    urls = json.load(f)
    ORDER_URL = urls['ORDER_URL']
    PAYMENT_URL = urls['PAYMENT_URL']
    STOCK_URL = urls['STOCK_URL']


async def get_and_get_field(session, url, field, key):
    async with session.get(url) as resp:
        jsn = await resp.json()
        return key, jsn[field]


async def get_user_credit_dict(session, user_id_list: List[str]) -> Dict[str, int]:
    tasks = []
    # Get credit
    for user_id in user_id_list:
        create_item_url = f"{PAYMENT_URL}/payment/find_user/{user_id}"
        tasks.append(asyncio.ensure_future(get_and_get_field(session, create_item_url, 'credit', user_id)))
    user_id_credit: List[Tuple[str, int]] = await asyncio.gather(*tasks)
    return dict(user_id_credit)


async def get_item_stock_dict(session, item_id_list: Union[List[str], str]) -> Dict[str, int]:
    tasks = []
    # Get stock
    for item_id in item_id_list:
        create_item_url = f"{STOCK_URL}/stock/find/{item_id}"
        tasks.append(asyncio.ensure_future(get_and_get_field(session, create_item_url, 'stock', item_id)))
    item_id_stock: List[Tuple[str, int]] = await asyncio.gather(*tasks)
    return dict(item_id_stock)


def get_prior_user_state(user_ids):
    user_state = dict()
    for user_id in user_ids:
        user_state[str(user_id)] = USER_STARTING_CREDIT
    return user_state


def parse_log(tmp_dir, prior_user_state: Dict[str, int]):
    i = 0
    with open(f'{tmp_dir}/consistency-test.log', 'r') as log_file:
        log_file = log_file.readlines()
        for log in log_file:
            if log.endswith('__OUR_LOG__\n'):
                m = re.search('ORDER: (.*) USER: (.*) (.*) __OUR_LOG__', log)
                user_id = str(m.group(2))
                status = m.group(3)
                if status == 'SUCCESS':
                    i += 1
                    prior_user_state[user_id] = prior_user_state[user_id] - ITEM_PRICE
    logger.info(f"Stock service inconsistencies in the logs: {i - (NUMBER_0F_ITEMS * ITEM_STARTING_STOCK)}")
    return prior_user_state


async def verify_systems_consistency(tmp_dir: str, item_ids, user_ids):
    pus: dict = parse_log(tmp_dir, get_prior_user_state(user_ids))
    async with aiohttp.ClientSession() as session:
        uic: dict = await get_user_credit_dict(session, user_ids)
        iis: dict = await get_item_stock_dict(session, item_ids)
    server_side_items_bought: int = (NUMBER_0F_ITEMS * ITEM_STARTING_STOCK) - list(iis.values())[0]
    logger.info(f"Stock service inconsistencies in the database: "
                f"{server_side_items_bought - (NUMBER_0F_ITEMS * ITEM_STARTING_STOCK)}")
    logged_user_credit: int = sum(pus.values())
    logger.info(f"Payment service inconsistencies in the logs: {abs(CORRECT_USER_STATE - logged_user_credit)}")
    server_side_user_credit: int = sum(list(uic.values()))
    logger.info(f"Payment service inconsistencies in the database: {abs(CORRECT_USER_STATE - server_side_user_credit)}")
