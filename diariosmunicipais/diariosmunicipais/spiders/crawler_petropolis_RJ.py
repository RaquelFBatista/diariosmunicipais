import scrapy
from pymongo import MongoClient
from datetime import datetime
import os
import re
import pdb

class PetropolisSpider(scrapy.Spider):
    name = "RJ_petropolis"
    base_url = "https://www.petropolis.rj.gov.br"
    delta = '2024-04-04'
    start_urls = [
        "https://www.petropolis.rj.gov.br/pmp/index.php/servicos-cidadao/diario-oficial/category/300"
    ]

    def start_requests(self):
        url = f'https://www.petropolis.rj.gov.br/pmp/index.php/servicos-cidadao/diario-oficial/category/300'
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        diaries_selectors = response.xpath('//div[@class="table-responsive"]/table[@class="table table-striped table-hover tabela-do"]/tbody/tr')

        for diary in diaries_selectors:
            full_text = diary.xpath ('//*[@id="sp-component"]/div/div[2]/div[5]/table/tbody/tr[1]/td[1]/p/strong/text()[2]').get()
            if full_text:
                date_part = full_text.split()[0]
                format_date = datetime.strptime(date_part, '%d/%m/%Y').strftime('%Y-%m-%d')
            else:
                date_initial = diary.xpath('//*[@id="sp-component"]/div/div[2]/div[5]/table/tbody/tr[1]/td[1]/p/strong[2]').get()
                format_date = datetime.strptime(date_initial, '%d/%m/%Y').strftime('%Y-%m-%d')
            if format_date >= self.delta:
                edition = diary.xpath('.//td/p/strong[contains(text(), "N.º")]/text()').get()
                edition_format = edition.replace('N.º ', '')
                source_id = edition_format
                search_url = diary.xpath(".//a/@href").extract_first()
                meta = {
                    'date': format_date,
                    'edition': edition_format,
                    'source_id': source_id
                }
                url = self.base_url + search_url
                yield scrapy.Request(url=url, meta=meta, callback=self.save_document)
            #if diaries_selectors:
                #yield from self.next_month

    def save_pdf(self, response):
        pdf_content = response.body
        source_id = response.meta.get('source_id')
        name = f'{self.name}_{source_id}.pdf'
        documents_folder = os.path.join(os.path.dirname(__file__), '..', '..', 'Documents')
        folder_path = os.path.join(documents_folder, self.name)
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
        collections = bd['petropolis_RJ']
        file_path = self.save_pdf(response)
        document = {
            'source': self.name,
            'date': response.meta.get('date'),
            'source_id': response.meta.get('source_id'), # REGEX colocar no formato EX2024...
            'url': response.url,     #
            'file_path': file_path
        }
        collections.insert_one(document)
        return document

    def next_month(self):
        id_month_construction = 1
        month_initial = 300
        month = month_initial + id_month_construction
        url = f'https://www.petropolis.rj.gov.br/pmp/index.php/servicos-cidadao/diario-oficial/category/{month}'
        if url:
            yield scrapy.Request(url=url, callback=self.parse)
