# Instructions


## Setup 
* Install python 3.8 or greater (tested with 3.12 on Linux)
* Install the required packages using: `pip install -r requirements.txt`
* Change the URLs and ports in the `urls.json` file with your own (currently set to the Gateway of the provided template)


> Note: For Windows users you might also need to install pywin32


## Consistency Test

In the provided consistency test we first populate the databases with 1 item with 100 stock that costs 1 credit 
and 1000 users that have 1 credit. 

Then we concurrently send 1000 checkouts of 1 item with random user/item combinations.
If everything goes well only ~10% of the checkouts will succeed, and the expected state should be 0 stock in the item 
items and 100 credits subtracted across different users.  

Finally, the measurements are done in two phases:
1) Using logs to see whether the service sent the correct message to the clients
2) Querying the database to see if the actual state remained consistent

### Running
* Run script `run_consistency_test.py`

### Interpreting Results

Wait for the script to finish and check how many inconsistencies you have in both the payment and stock services


## Stress Test

To run the stress test you have to:

1) Open a terminal and navigate to the `stress-test` folder.

2) Run the `init_orders.py` to initialize the databases with the following data:

```txt
NUMBER_0F_ITEMS = 100_000
ITEM_STARTING_STOCK = 1_000_000
ITEM_PRICE = 1
NUMBER_OF_USERS = 100_000
USER_STARTING_CREDIT = 1_000_000
NUMBER_OF_ORDERS = 100_000
```

3) Run script: `locust -f locustfile.py --host="localhost"`

> Note: you can also set the --processes flag to increase the amount of locust worker processes.

4) Go to `http://localhost:8089/` to use the Locust.io UI.


To change the weight (task frequency) of the provided scenarios you can change the weights in the `tasks` definition (line 358)
With our locust file each user will make one request between 1 and 15 seconds (you can change that in line 356).

> You can also create your own scenarios as you like (https://docs.locust.io/en/stable/writing-a-locustfile.html)


### Using the Locust UI
Fill in an appropriate number of users that you want to test with. 
The hatch rate is how many users will spawn per second 
(locust suggests that you should use less than 100 in local mode). 

### Stress Test With Kubernetes 

If you want to scale the `stress-test` to a Kubernetes clust you can follow the guide from 
Google's [Distributed load testing using Google Kubernetes Engine](https://cloud.google.com/architecture/distributed-load-testing-using-gke)
and [original repo](https://github.com/GoogleCloudPlatform/distributed-load-testing-using-kubernetes). 
