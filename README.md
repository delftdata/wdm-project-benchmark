# Instructions

## Setup 
* Install python 3.6 or greater (tested with 3.9)
* Install the required packages using: `pip install -r requirements.txt`
* Change the URLs and ports in the `urls.json` file with your own

````
Note: For Windows users you might also need to install pywin32
````

## Stress Test

In the provided stress test we have created 6 scenarios:

1) A stock admin creates an item and adds stock to it

2) A user checks out an order with one item inside that an admin has added stock to before

3) A user checks out an order with two items inside that an admin has added stock to before

4) A user adds an item to an order, regrets it and removes it and then adds it back and checks out

5) Scenario that is supposed to fail because the second item does not have enough stock

6) Scenario that is supposed to fail because the user does not have enough credit

To change the weight (task frequency) of the provided scenarios you can change the weights in the `tasks` definition (line 358)
With our locust file each user will make one request between 1 and 15 seconds (you can change that in line 356).

```
YOU CAN ALSO CREATE YOUR OWN SCENARIOS AS YOU LIKE
```

### Running
* Open terminal and navigate to the `locustfile.py` folder
* Run script: `locust -f locustfile.py --host="localhost"`
* Go to `http://localhost:8089/`


### Using the Locust UI
Fill in an appropriate number of users that you want to test with. 
The hatch rate is how many users will spawn per second 
(locust suggests that you should use less than 100 in local mode). 


## Consistency Test

In the provided consistency test we first populate the databases with 100 items with 1 stock that costs 1 credit 
and 1000 users that have 1 credit. 

Then we concurrently send 1000 checkouts of 1 item with random user/item combinations.
The probabilities say that only 10% of the checkouts will succeed, and the expected state should be 0 stock across all 
items and 100 credits subtracted from different users.  

Finally, the measurements are done in two phases:
1) Using logs to see whether the service sent the correct message to the clients
2) Querying the database to see if the actual state remained consistent

### Running
* Run script `run_consistency_test.py`

### Interpreting Results

Wait for the script to finish and check how many inconsistencies you have in both the payment and stock services