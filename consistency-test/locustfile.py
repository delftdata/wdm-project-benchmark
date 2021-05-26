import pickle
import random
import logging
import json
import os
from typing import List, Union

from locust import HttpUser, SequentialTaskSet, task, constant
from locust.exception import StopUser

with open(os.path.join('..', 'urls.json')) as f:
    urls = json.load(f)
    ORDER_URL = urls['ORDER_URL']
    PAYMENT_URL = urls['PAYMENT_URL']
    STOCK_URL = urls['STOCK_URL']


def create_order(session):
    with session.client.post(f"{ORDER_URL}/orders/create/{session.user_id}", json={}, name="/orders/create/[user_id]",
                             catch_response=True) as response:
        try:
            session.order_id = response.json()['order_id']
        except json.JSONDecodeError:
            response.failure("SERVER ERROR")


def add_item_to_order(session, item_idx: int):
    with session.client.post(f"{ORDER_URL}/orders/addItem/{session.order_id}/{session.item_ids[item_idx]}",
                             name="/orders/addItem/[order_id]/[item_id]", json={}, catch_response=True) as response:
        if 400 <= response.status_code < 500:
            response.failure(response.text)
            raise StopUser()
        else:
            response.success()


def checkout_order(session):
    with session.client.post(f"{ORDER_URL}/orders/checkout/{session.order_id}", json={},
                             name="/orders/checkout/[order_id]", catch_response=True) as response:
        if 400 <= response.status_code < 500:
            logging.info(f"CHECKOUT | ORDER: {session.order_id} USER: {session.user_id} FAIL __OUR_LOG__")
            response.failure(response.text)
        else:
            logging.info(f"CHECKOUT | ORDER: {session.order_id} USER: {session.user_id} SUCCESS __OUR_LOG__")
            response.success()


def load_pickle_file(file_name: str) -> Union[List[str], str]:
    with open(file_name, 'rb') as pkl_file:
        var = pickle.load(pkl_file)
        return var


class ConsistencyTest(SequentialTaskSet):
    """
    Scenario where a user checks out an order with one item inside that an admin has added stock to before
    """

    order_id: str
    user_id: str
    user_ids: List[str]
    item_ids: List[str]

    def __init__(self, parent):
        super().__init__(parent)
        self.local_random = random.Random()
        self.user_ids = load_pickle_file('tmp/user_ids.pkl')
        tmp_item_ids = load_pickle_file('tmp/item_ids.pkl')
        self.item_ids = tmp_item_ids if type(tmp_item_ids) is list else [str(tmp_item_ids)]

    def on_start(self):
        self.user_id = str(self.local_random.choice(self.user_ids))
        self.order_id = ""

    def on_stop(self):
        self.user_id = str(self.local_random.choice(self.user_ids))
        self.order_id = ""

    @task
    def user_creates_order(self): create_order(self)

    @task
    def user_adds_item_to_order(self): add_item_to_order(self, 0)

    @task
    def user_checks_out_order(self): checkout_order(self)


class MicroservicesUser(HttpUser):
    tasks = {ConsistencyTest: 100}
    wait_time = constant(1)  # how much time a user waits (seconds) to run another SequentialTaskSet
