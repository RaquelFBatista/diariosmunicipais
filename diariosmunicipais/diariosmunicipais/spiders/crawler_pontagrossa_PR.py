import scrapy
from pymongo import MongoClient
from datetime import datetime
import os
import re
import pdb

class SaogoncaloSpider(scrapy.Spider):
    name = "PR_pontagrossa"
    delta = '2024-04-04'
    base_url = "https://www.pontagrossa.pr.gov.br/"
    start_urls = [
        "https://www.pontagrossa.pr.gov.br/diario-oficial"
    ]


    def start_requests(self):
        url = f'https://www.pontagrossa.pr.gov.br/diario-oficial'
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        diaries_selectors = response.xpath('//div[@class="view-content"]//div[@class="field-items"]//tbody/tr')
        for diary in diaries_selectors:
            date_initial = diary.xpath('.//div[@align="left"]/text()[2]').get() #mudar esse índice
            if date_initial:
                date_str = date_initial.strip().replace('em ', '')
                date = date_str.split(' - ')[0]
                format_date = datetime.strptime(date, '%d/%m/%Y')
                final_date = datetime.strftime(format_date, '%Y-%m-%d')
                if final_date >= self.delta:
                    publication_date = final_date
                    edition = diary.xpath('.//a/@title').re_first(r'ed-?(\d+)')
                    search_url = diary.xpath('.//span/a/@href').get()
                    meta = {
                        'publication_date': final_date,   #VER
                        'source_id': edition,
                    }
                    url = search_url
                    yield scrapy.Request(url=url, meta=meta, callback=self.save_document)

    def save_pdf(self, response):
        pdf_content = response.body
        source_id = response.meta.get('source_id')  # o resultado ID precisa ser formatado para EX(URL do pdf)
        name = f'{self.name}_{source_id}.pdf'
        folder_path = os.path.join(os.path.dirname(__file__), '..', '..', 'Documents')
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        file_path = os.path.join(folder_path, name)
        with open(file_path, 'wb') as f:
            f.write(pdf_content)
            return file_path
        # salvar e retornar o file_path
        # quando houver páginas viradas, é importante deixar observação na planilha

    def save_document(self, response):
        client = MongoClient('localhost',27017)
        bd = client['executiveorder']
        collections = bd['pontagrossa']
        file_path = self.save_pdf(response)
        document = {
            'source': self.name,
            'date': response.meta.get('publication_date'),
            'source_id': response.meta.get('source_id'),
            'url': response.url,
            'file_path': file_path
        }
        collections.insert_one(document)
        return document
