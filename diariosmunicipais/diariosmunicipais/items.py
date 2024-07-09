

import scrapy
from scrapy import Item
from scrapy import Field


class DiariesItem(Item):
    date = Field()
    diary = Field()
