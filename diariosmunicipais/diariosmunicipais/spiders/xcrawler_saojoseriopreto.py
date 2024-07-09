import scrapy
from pymongo import MongoClient
from scrapy import Request
import datetime
import os
import pdb

class SaojoseriopretoSpider(scrapy.Spider):
    name = "SP_saojoseriopreto"
    # base_url = ""
    start_urls = [
        'https://www.riopreto.sp.gov.br/DiarioOficial/Diario.action'
    ]

    def start_requests(self):
        url = 'https://www.riopreto.sp.gov.br/DiarioOficial/Diario.action'
        delta = '04/04/2024'
        start_date = {'data': delta}
        headers = {
            "authority": "www.riopreto.sp.gov.br",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "max-age=0",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.riopreto.sp.gov.br",
            "sec-ch-ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Google Chrome\";v=\"122\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Linux\"",
            "sec-fetch-dest": "iframe",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

        body = 'diario.dataPublicacao=04%2F04%2F2024&diario.palavraChave=&Diario%21listar.action=Buscar'

        yield scrapy.FormRequest(
            url=url,
            formdata=start_date,
            method='POST',
            dont_filter=True,
            headers=headers,
            body=body,
            callback=self.parse
        )
    def parse(self, response):
        pdb.set_trace()
        acts = response.xpath()

    #     for diary in acts:
    #         date_initial = diary.xpath(".//a/text()").extract_first()
    #         format_date = datetime.strptime(date_initial, '%d/%m/%Y').strftime('%Y-%m-%d')
    #         search_url = diary.xpath(".//a/@href").extract_first()
    #         try:
    #             source_id_initial = search_url.split('/')[-1]
    #             source_id = source_id_initial.replace('_', '').replace('.pdf', '')
    #             ##organizar melhor o source id, por exemplo, para extraordinario _, EX, SUP, etc
    #         except:
    #             pdb.set_trace()
    #         # sempre colocar ./
    #         meta = {
    #             'date': format_date,
    #             'source_id': source_id
    #         }
    #         url = self.base_url + search_url
    #         yield scrapy.Request(url=url, meta=meta, callback=self.save_document)
    #     # if diaries_selectors:
    #     #     yield from self.next_page(response)
    #
    # def save_pdf(self, response):
    #     pdf_content = response.body
    #     source_id = response.meta.get('source_id')  # o resultado ID precisa ser formatado para EX(URL do pdf)
    #     name = f'{self.name}_{source_id}.pdf'
    #     folder_path = '../SP_saojoseriopreto/Documents'
    #     file_path = os.path.join(folder_path, name)
    #     with open(f'{name}', 'ab') as f:
    #         f.write(pdf_content)
    #         return file_path, name
    #     # salvar e retornar o file_path
    #     # quando houver páginas viradas, é importante deixar observação na planilha
    #
    # def save_document(self, response):
    #     client = MongoClient('localhost',27017)
    #     bd = client['executiveorder']
    #     collections = bd['saogoncalo']
    #     file_path = self.save_pdf(response)
    #     document = {
    #         'source': self.name,
    #         'date': response.meta.get('date'),
    #         'source_id': response.meta.get('source_id'), # REGEX colocar no formato EX2024...
    #         'url': response.url,     #
    #         'file_path': file_path
    #     }
    #     collections.insert_one(document)
    #
    #
    # def next_page(self, response):
    #     actual_page = int(response.xpath("//div[@class='d-flex justify-content-center mt-1']//font/b/text()").extract_first())
    #     next_page = actual_page + 1
    #     next_page_url = response.xpath(f"//div[@class='d-flex justify-content-center mt-1']//a[contains(@href,'NumeroPagina={next_page}')]/@href").extract_first()
    #     if next_page_url:
    #         url = self.base_url + next_page_url
    #         yield scrapy.Request(url=url, callback=self.parse)
    #
