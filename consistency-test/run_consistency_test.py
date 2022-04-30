import asyncio
import os
import shutil
import logging
from tempfile import gettempdir

from verify import verify_systems_consistency
from populate import populate_databases
from stress import stress

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s - %(asctime)s - %(name)s - %(message)s',
                    datefmt='%I:%M:%S')
logger = logging.getLogger("Consistency test")


# Create the tmp folder to store the logs, the users and the stock
logger.info("Creating tmp folder...")
tmp_folder_path: str = os.path.join(gettempdir(), 'wdm_consistency_test')

if os.path.isdir(tmp_folder_path):
    shutil.rmtree(tmp_folder_path)

os.mkdir(tmp_folder_path)
logger.info("tmp folder created")

# Populate the payment and stock databases
logger.info("Populating the databases...")
item_ids, user_ids = asyncio.run(populate_databases())
logger.info("Databases populated")

# Run the load test
logger.info("Starting the load test...")
asyncio.run(stress(item_ids, user_ids))
logger.info("Load test completed")

# Verify the systems' consistency
logger.info("Starting the consistency evaluation...")
asyncio.run(verify_systems_consistency(tmp_folder_path, item_ids, user_ids))
logger.info("Consistency evaluation completed")

if os.path.isdir(tmp_folder_path):
    shutil.rmtree(tmp_folder_path)
