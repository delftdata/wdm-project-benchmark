import pickle
import re
import os
import json
import requests
import logging
from multiprocessing.pool import ThreadPool
from typing import Union, List, Dict, Tuple

from populate import NUMBER_0F_ITEMS

CORRECT_USER_STATE = 900

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s - %(asctime)s - %(name)s - %(message)s',
                    datefmt='%I:%M:%S')
logger = logging.getLogger(__name__)

with open(os.path.join('..', 'urls.json')) as f:
    urls = json.load(f)
    ORDER_URL = urls['ORDER_URL']
    PAYMENT_URL = urls['PAYMENT_URL']
    STOCK_URL = urls['STOCK_URL']


def load_pickle_file(file_name: str) -> Union[List[str], str]:
    with open(file_name, 'rb') as pkl_file:
        var = pickle.load(pkl_file)
        return var


def get_user_credit(user_id: str) -> Tuple[str, int]:
    credit = int(requests.get(f"{PAYMENT_URL}/payment/find_user/{user_id}", json={}).json()['credit'])
    return user_id, credit


def get_user_credit_dict(user_id_list: List[str]) -> Dict[str, int]:
    with ThreadPool(10) as pool:
        user_id_credit = dict(pool.map(get_user_credit, user_id_list))
    return user_id_credit


def get_item_stock(item_id: str) -> Tuple[str, int]:
    stock = int(requests.get(f"{STOCK_URL}/stock/find/{item_id}", json={}).json()['stock'])
    return item_id, stock


def get_item_stock_dict(item_id_list: Union[List[str], str]) -> Dict[str, int]:
    if type(item_id_list) is list:
        with ThreadPool(10) as pool:
            item_id_stock = dict(pool.map(get_item_stock, item_id_list))
    else:
        item_id_stock = dict([get_item_stock(item_id_list)])
    return item_id_stock


def get_prior_user_state():
    user_state = dict()
    for user_id in load_pickle_file('tmp/user_ids.pkl'):
        user_state[str(user_id)] = 1
    return user_state


def parse_log(prior_user_state: Dict[str, int]):
    i = 0
    with open('tmp/consistency-test.log', 'r') as log_file:
        log_file = log_file.readlines()
        for log in log_file:
            if log.endswith('__OUR_LOG__\n'):
                m = re.search('ORDER: (.*) USER: (.*) (.*) __OUR_LOG__', log)
                user_id = str(m.group(2))
                status = m.group(3)
                if status == 'SUCCESS':
                    i += 1
                    if prior_user_state[user_id] == 0:
                        logger.info("NEGATIVE")
                    prior_user_state[user_id] = prior_user_state[user_id] - 1
    logger.info(f"Stock service inconsistencies in the logs: {i - NUMBER_0F_ITEMS}")
    return prior_user_state


def verify_systems_consistency():
    pus: dict = parse_log(get_prior_user_state())
    uic: dict = get_user_credit_dict(load_pickle_file('tmp/user_ids.pkl'))
    iis: dict = get_item_stock_dict(load_pickle_file('tmp/item_ids.pkl'))
    server_side_items_bought: int = 100 - list(iis.values())[0]
    logger.info(f"Stock service inconsistencies in the database: {server_side_items_bought - NUMBER_0F_ITEMS}")
    logged_user_credit: int = sum(pus.values())
    logger.info(f"Payment service inconsistencies in the logs: {abs(CORRECT_USER_STATE - logged_user_credit)}")
    server_side_user_credit: int = sum(list(uic.values()))
    logger.info(f"Payment service inconsistencies in the database: {abs(CORRECT_USER_STATE - server_side_user_credit)}")
