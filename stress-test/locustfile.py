import os.path
import random
import json
from typing import List


from locust import HttpUser, SequentialTaskSet, between, task

# replace the example urls and ports with the appropriate ones
with open(os.path.join('..', 'urls.json')) as f:
    urls = json.load(f)
    ORDER_URL = urls['ORDER_URL']
    PAYMENT_URL = urls['PAYMENT_URL']
    STOCK_URL = urls['STOCK_URL']


def create_item(session):
    price = random.uniform(1.0, 10.0)
    with session.client.post(f"{STOCK_URL}/stock/item/create/{price}", name="/stock/item/create/[price]",
                             catch_response=True) as response:
        try:
            item_id = response.json()['item_id']
        except json.JSONDecodeError:
            response.failure("SERVER ERROR")
        else:
            session.item_ids.append(item_id)


def add_stock(session, item_idx: int):
    stock_to_add = random.randint(100, 1000)
    session.client.post(f"{STOCK_URL}/stock/add/{session.item_ids[item_idx]}/{stock_to_add}",
                        name="/stock/add/[item_id]/[number]")


def create_user(session):
    with session.client.post(f"{PAYMENT_URL}/payment/create_user", name="/payment/create_user",
                             catch_response=True) as response:
        try:
            session.user_id = response.json()['user_id']
        except json.JSONDecodeError:
            response.failure("SERVER ERROR")


def add_balance_to_user(session):
    balance_to_add: float = random.uniform(10000.0, 100000.0)
    session.client.post(f"{PAYMENT_URL}/payment/add_funds/{session.user_id}/{balance_to_add}",
                        name="/payment/add_funds/[user_id]/[amount]")


def create_order(session):
    with session.client.post(f"{ORDER_URL}/orders/create/{session.user_id}", name="/orders/create/[user_id]",
                             catch_response=True) as response:
        try:
            session.order_id = response.json()['order_id']
        except json.JSONDecodeError:
            response.failure("SERVER ERROR")


def add_item_to_order(session, item_idx: int):
    with session.client.post(f"{ORDER_URL}/orders/addItem/{session.order_id}/{session.item_ids[item_idx]}",
                             name="/orders/addItem/[order_id]/[item_id]", catch_response=True) as response:
        if 400 <= response.status_code < 500:
            response.failure(response.text)
        else:
            response.success()


def remove_item_from_order(session, item_idx: int):
    with session.client.delete(f"{ORDER_URL}/orders/removeItem/{session.order_id}/{session.item_ids[item_idx]}",
                               name="/orders/removeItem/[order_id]/[item_id]", catch_response=True) as response:
        if 400 <= response.status_code < 500:
            response.failure(response.text)
        else:
            response.success()


def checkout_order(session):
    with session.client.post(f"{ORDER_URL}/orders/checkout/{session.order_id}", name="/orders/checkout/[order_id]",
                             catch_response=True) as response:
        if 400 <= response.status_code < 500:
            response.failure(response.text)
        else:
            response.success()


def checkout_order_that_is_supposed_to_fail(session, reason: int):
    with session.client.post(f"{ORDER_URL}/orders/checkout/{session.order_id}", name="/orders/checkout/[order_id]",
                             catch_response=True) as response:
        if 400 <= response.status_code < 500:
            response.success()
        else:
            if reason == 0:
                response.failure("This was supposed to fail: Not enough stock")
            else:
                response.failure("This was supposed to fail: Not enough credit")


def make_items_stock_zero(session, item_idx: int):
    with session.client.get(f"{STOCK_URL}/stock/find/{session.item_ids[item_idx]}", name="/stock/find/[item_id]",
                            catch_response=True) as response:
        try:
            stock_to_subtract = response.json()['stock']
        except json.JSONDecodeError:
            response.failure("SERVER ERROR")
        else:
            session.client.post(f"{STOCK_URL}/stock/subtract/{session.item_ids[item_idx]}/{stock_to_subtract}",
                                name="/stock/subtract/[item_id]/[number]")


class LoadTest1(SequentialTaskSet):
    """
    Scenario where a stock admin creates an item and adds stock to it
    """
    item_ids: List[str]

    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        self.item_ids = list()

    def on_stop(self):
        """ on_stop is called when the TaskSet is stopping """
        self.item_ids = list()

    @task
    def admin_creates_item(self): create_item(self)

    @task
    def admin_adds_stock_to_item(self): add_stock(self, 0)


class LoadTest2(SequentialTaskSet):
    """
    Scenario where a user checks out an order with one item inside that an admin has added stock to before
    """
    item_ids: List[str]
    user_id: str
    order_id: str

    def on_start(self):
        self.item_ids = list()
        self.user_id = ""
        self.order_id = ""

    def on_stop(self):
        self.item_ids = list()
        self.user_id = ""
        self.order_id = ""

    @task
    def admin_creates_item(self): create_item(self)

    @task
    def admin_adds_stock_to_item(self): add_stock(self, 0)

    @task
    def user_creates_account(self): create_user(self)

    @task
    def user_adds_balance(self): add_balance_to_user(self)

    @task
    def user_creates_order(self): create_order(self)

    @task
    def user_adds_item_to_order(self): add_item_to_order(self, 0)

    @task
    def user_checks_out_order(self): checkout_order(self)


class LoadTest3(SequentialTaskSet):
    """
    Scenario where a user checks out an order with two items inside that an admin has added stock to before
    """
    item_ids: List[str]
    user_id: str
    order_id: str

    def on_start(self):
        self.item_ids = list()
        self.user_id = ""
        self.order_id = ""

    def on_stop(self):
        self.item_ids = list()
        self.user_id = ""
        self.order_id = ""

    @task
    def admin_creates_item1(self): create_item(self)

    @task
    def admin_adds_stock_to_item1(self): add_stock(self, 0)

    @task
    def admin_creates_item2(self): create_item(self)

    @task
    def admin_adds_stock_to_item2(self): add_stock(self, 1)

    @task
    def user_creates_account(self): create_user(self)

    @task
    def user_adds_balance(self): add_balance_to_user(self)

    @task
    def user_creates_order(self): create_order(self)

    @task
    def user_adds_item1_to_order(self): add_item_to_order(self, 0)

    @task
    def user_adds_item2_to_order(self): add_item_to_order(self, 1)

    @task
    def user_checks_out_order(self): checkout_order(self)


class LoadTest4(SequentialTaskSet):
    """
    Scenario where a user adds an item to an order, regrets it and removes it and then adds it back and checks out
    """
    item_ids: List[str]
    user_id: str
    order_id: str

    def on_start(self):
        self.item_ids = list()
        self.user_id = ""
        self.order_id = ""

    def on_stop(self):
        self.item_ids = list()
        self.user_id = ""
        self.order_id = ""

    @task
    def admin_creates_item(self): create_item(self)

    @task
    def admin_adds_stock_to_item(self): add_stock(self, 0)

    @task
    def user_creates_account(self): create_user(self)

    @task
    def user_adds_balance(self): add_balance_to_user(self)

    @task
    def user_creates_order(self): create_order(self)

    @task
    def user_adds_item_to_order(self): add_item_to_order(self, 0)

    @task
    def user_removes_item_from_order(self): remove_item_from_order(self, 0)

    @task
    def user_adds_item_to_order_again(self): add_item_to_order(self, 0)

    @task
    def user_checks_out_order(self): checkout_order(self)


class LoadTest5(SequentialTaskSet):
    """
    Scenario that is supposed to fail because the second item does not have enough stock
    """
    item_ids: List[str]
    user_id: str
    order_id: str

    def on_start(self):
        self.item_ids = list()
        self.user_id = ""
        self.order_id = ""

    def on_stop(self):
        self.item_ids = list()
        self.user_id = ""
        self.order_id = ""

    @task
    def admin_creates_item1(self): create_item(self)

    @task
    def admin_adds_stock_to_item1(self): add_stock(self, 0)

    @task
    def admin_creates_item2(self): create_item(self)

    @task
    def admin_adds_stock_to_item2(self): add_stock(self, 1)

    @task
    def user_creates_account(self): create_user(self)

    @task
    def user_adds_balance(self): add_balance_to_user(self)

    @task
    def user_creates_order(self): create_order(self)

    @task
    def user_adds_item1_to_order(self): add_item_to_order(self, 0)

    @task
    def user_adds_item2_to_order(self): add_item_to_order(self, 1)

    @task
    def stock_admin_makes_item2s_stock_zero(self): make_items_stock_zero(self, 1)

    @task
    def user_checks_out_order(self): checkout_order_that_is_supposed_to_fail(self, 0)


class LoadTest6(SequentialTaskSet):
    """
    Scenario that is supposed to fail because the user does not have enough credit
    """
    item_ids: List[str]
    user_id: str
    order_id: str

    def on_start(self):
        self.item_ids = list()
        self.user_id = ""
        self.order_id = ""

    def on_stop(self):
        self.item_ids = list()
        self.user_id = ""
        self.order_id = ""

    @task
    def admin_creates_item(self): create_item(self)

    @task
    def admin_adds_stock_to_item(self): add_stock(self, 0)

    @task
    def user_creates_account(self): create_user(self)

    @task
    def user_creates_order(self): create_order(self)

    @task
    def user_adds_item_to_order(self): add_item_to_order(self, 0)

    @task
    def user_checks_out_order(self): checkout_order_that_is_supposed_to_fail(self, 1)


class MicroservicesUser(HttpUser):
    wait_time = between(1, 3)  # how much time a user waits (seconds) to run another TaskSequence
    # [SequentialTaskSet]: [weight of the SequentialTaskSet]
    tasks = {
        LoadTest1: 5,
        LoadTest2: 30,
        LoadTest3: 25,
        LoadTest4: 20,
        LoadTest5: 10,
        LoadTest6: 10
    }
