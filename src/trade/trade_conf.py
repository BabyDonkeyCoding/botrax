"""Trade specific configuration"""
import random
import time

NEXT_SHOP_SELL = int(time.time()) + random.randint(3600, 7200)
NEXT_AH_SELL = int(time.time()) + random.randint(3600, 7200)
MAX_NO_SELL_AGE = int(3600 * 24 * 14)
MAX_OFFER_AGE = int(3600 * 24 * 250)
MAX_SOLD_AGE = int(3600 * 24 * 300)
MAX_SOLD_ITEMS = int(15)
