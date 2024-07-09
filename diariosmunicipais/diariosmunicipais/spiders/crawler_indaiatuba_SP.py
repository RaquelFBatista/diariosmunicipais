import pdb
import scrapy
from datetime import datetime
import os
from re import match
from pymongo import MongoClient


class CrawlerIndaiatubaPySpider(scrapy.Spider):
    name = "SP_indaiatuba"
    base_url = 'https://www.indaiatuba.sp.gov.br'
    start_urls = ["https://www.indaiatuba.sp.gov.br/relacoes-institucionais/imprensa-oficial/edicoes/"]

    def start_requests(self):
        delta = '04/04/2024'
        end_date = datetime.today().strftime('%d/%m/%Y')
        url = f'https://www.indaiatuba.sp.gov.br/relacoes-institucionais/imprensa-oficial/edicoes/'
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.indaiatuba.sp.gov.br",
            "Referer": "https://www.indaiatuba.sp.gov.br/relacoes-institucionais/imprensa-oficial/edicoes/",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "sec-ch-ua": "\"Chromium\";v=\"124\", \"Google Chrome\";v=\"124\", \"Not-A.Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Linux\""
        }

        cookies = {
            "fc": "15/5/2024",
            "PHPSESSID": "1unigt8hs4o6eojujd1rmmsa23",
            "lc": "16/5/2024"
        }

        body = f'i_edicaoinicial=&i_edicaofinal=&i_datainicial={delta}&i_datafinal={end_date}&env=1&br_submit=Pesquisar'

        yield scrapy.FormRequest(
            url=url,
            method='POST',
            dont_filter=True,
            cookies=cookies,
            headers=headers,
            body=body,
            callback=self.parse
        )

    def parse(self, response):
        diaries_selectors = response.xpath('//div[@class="col-mb-12"]//div[@id="texto_pagina"]/ul/li')

        for diary in diaries_selectors:
            edition_date = diary.xpath(".//a/text()").extract_first()
            init_date = diary.xpath(".//a/text()").extract_first()
            if init_date:
                edition_number = init_date.split('Edição N.º ')[1].split(' ')[0]
                publication_date = init_date.split('Publicada em ')[1]
            format_date = datetime.strptime(publication_date, '%d/%m/%Y').strftime('%Y-%m-%d')
            search_url = diary.xpath(".//a/@href").extract_first()
            url = self.base_url + search_url
            source_id = search_url.strip('/').split('/')[-1].replace('.pdf', '').replace('_', '').strip()
            # organizar melhor o source id, por exemplo, para extraordinario _, EX, SUP, etc
            # sempre colocar ./
            meta = {
                'date': format_date,
                'source_id': source_id,
                'edition': edition_number,
                'url': url
            }
            yield scrapy.Request(url=url, meta=meta, callback=self.save_document)

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
        client = MongoClient('localhost', 27017)
        bd = client['executiveorder']
        collections = bd['indaiatuba']
        file_path = self.save_pdf(response)
        document = {
            'source': self.name,
            'date': response.meta.get('date'),
            'source_id': response.meta.get('source_id'),  # REGEX colocar no formato EX2024...
            'url': response.url,  #
            'file_path': file_path
        }
        collections.insert_one(document)

