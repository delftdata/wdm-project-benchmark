import pickle
import json
import logging
import os
from typing import Union, List

import requests
from multiprocessing.pool import ThreadPool
from itertools import repeat

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s - %(asctime)s - %(name)s - %(message)s',
                    datefmt='%I:%M:%S')
logger = logging.getLogger(__name__)
NUMBER_0F_ITEMS = 100
NUMBER_OF_USERS = 1000

with open(os.path.join('..', 'urls.json')) as f:
    urls = json.load(f)
    ORDER_URL = urls['ORDER_URL']
    PAYMENT_URL = urls['PAYMENT_URL']
    STOCK_URL = urls['STOCK_URL']


def create_user_offline(balance: int) -> str:
    user_id = requests.post(f"{PAYMENT_URL}/payment/create_user", json={}).json()['user_id']
    requests.post(f"{PAYMENT_URL}/payment/add_funds/{user_id}/{balance}", json={})
    return str(user_id)


def create_item_offline(stock_to_add: int, price: int = 1) -> str:
    __item_id = requests.post(f"{STOCK_URL}/stock/item/create/{price}", json={}).json()['item_id']
    requests.post(f"{STOCK_URL}/stock/add/{__item_id}/{stock_to_add}", json={})
    return str(__item_id)


def create_items_offline(number_of_items: int, stock: int = 1) -> List[str]:
    with ThreadPool(10) as pool:
        __item_ids = list(pool.map(create_item_offline, repeat(stock, number_of_items)))
    return __item_ids


def create_users_offline(number_of_users: int, credit: int = 1) -> List[str]:
    with ThreadPool(10) as pool:
        __user_ids = list(pool.map(create_user_offline, repeat(credit, number_of_users)))
    return __user_ids


def write_pickle(file_name: str, var: Union[List[str], str]):
    with open(file_name, 'wb') as output:
        pickle.dump(var, output, pickle.HIGHEST_PROTOCOL)


def populate_databases():
    logger.info("Creating items ...")
    item_id = create_item_offline(NUMBER_0F_ITEMS)  # create item with 100 stock
    write_pickle('tmp/item_ids.pkl', item_id)
    logger.info("Items created")

    logger.info("Creating users ...")
    user_ids = create_users_offline(NUMBER_OF_USERS)  # create 1000 users
    write_pickle('tmp/user_ids.pkl', user_ids)
    logger.info("Users created")
