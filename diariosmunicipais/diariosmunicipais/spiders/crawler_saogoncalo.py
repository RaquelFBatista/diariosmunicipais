import scrapy
from pymongo import MongoClient
from datetime import datetime
import os

import pdb

class SaogoncaloSpider(scrapy.Spider):
    name = "RJ_sao_goncalo"
    base_url = "https://do.pmsg.rj.gov.br/"
    start_urls = [
        "https://do.pmsg.rj.gov.br/index?NumeroPagina=1&Termo=%20&DataInicial=2024-04-04&DataFinal=2024-04-04&PesquisarTermo=Pesquisar"
    ]

    def start_requests(self):
        delta = '2024-04-04'
        end_date = datetime.today().strftime('%Y-%m-%d')
        url = f'https://do.pmsg.rj.gov.br/index?NumeroPagina=1&Termo=%20&DataInicial={delta}&DataFinal={end_date}&PesquisarTermo=Pesquisar'
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        pdb.set_trace()
        diaries_selectors = response.xpath("//div[@class='container mt-1']/div[@class='card mb-3']")

        for diary in diaries_selectors:
            date_initial = diary.xpath(".//a/text()").extract_first()
            format_date = datetime.strptime(date_initial, '%d/%m/%Y').strftime('%Y-%m-%d')
            search_url = diary.xpath(".//a/@href").extract_first()
            try:
                source_id_initial = search_url.split('/')[-1]
                source_id = source_id_initial.replace('_', '').replace('.pdf', '')
                ##organizar melhor o source id, por exemplo, para extraordinario _, EX, SUP, etc
            except:
                pdb.set_trace()
            # sempre colocar ./
            meta = {
                'date': format_date,
                'source_id': source_id
            }
            url = self.base_url + search_url
            yield scrapy.Request(url=url, meta=meta, callback=self.save_document)
        if diaries_selectors:
            yield from self.next_page(response)

    def save_pdf(self, response):
        pdf_content = response.body
        source_id = response.meta.get('source_id')  # o resultado ID precisa ser formatado para EX(URL do pdf)
        name = f'{self.name}_{source_id}.pdf'
        folder_path = '../Documents'
        file_path = os.path.join(folder_path, name)
        with open(f'{name}', 'ab') as f:
            f.write(pdf_content)
            return file_path, name
        # salvar e retornar o file_path
        # quando houver páginas viradas, é importante deixar observação na planilha

    def save_document(self, response):
        client = MongoClient('localhost',27017)
        bd = client['executiveorder']
        collections = bd['saogoncalo']
        file_path = self.save_pdf(response)
        document = {
            'source': self.name,
            'date': response.meta.get('date'),
            'source_id': response.meta.get('source_id'), # REGEX colocar no formato EX2024...
            'url': response.url,     #
            'file_path': file_path
        }
        collections.insert_one(document)


    def next_page(self, response):
        actual_page = int(response.xpath("//div[@class='d-flex justify-content-center mt-1']//font/b/text()").extract_first())
        next_page = actual_page + 1
        next_page_url = response.xpath(f"//div[@class='d-flex justify-content-center mt-1']//a[contains(@href,'NumeroPagina={next_page}')]/@href").extract_first()
        if next_page_url:
            url = self.base_url + next_page_url
            yield scrapy.Request(url=url, callback=self.parse)

