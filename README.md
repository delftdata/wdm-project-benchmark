# Instructions
## Running locust
* Install python 3.6 or greater
* Install locust using either:
    * pip: `pip install locustio==0.14.6`
    * conda: `conda install locust`
* Change the urls and ports in lines 8-11 in `locustfile.py` to correspond to your own
* Open terminal and navigate to the `locustfile.py` folder
* Run script: `locust -f locustfile.py --host=""`
* Go to `http://localhost:8089/`
## Using the Locust UI
Fill in an appropriate number of users that you want to test with. 
With our locust file each user will make one request between 1 and 15 seconds (you can change that in line 347).
The hatch rate is how many users will spawn per second (locust suggests that you should use less than 100).
Leave the host field empty it will automatically find the right one (it corresponds to the locust master host). 