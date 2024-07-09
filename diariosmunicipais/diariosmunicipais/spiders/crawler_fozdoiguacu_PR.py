import base64

import scrapy
from pymongo import MongoClient
from datetime import datetime
import os
import json

import pdb


class DiarioItem(scrapy.Item):
    source_id = scrapy.Field
    nr_publicacao = scrapy.Field()
    dia = scrapy.Field()
    mes = scrapy.Field()
    ano = scrapy.Field()
    conteudo = scrapy.Field()


class FozdoIguacuSpider(scrapy.Spider):
    name = "PR_fozdoiguacu"
    delta = '2024-04-04'
    base_url = "https://www5.pmfi.pr.gov.br/"
    start_urls = [
        "https://sistemas.pmfi.pr.gov.br/RP/SMTIAPI/ApiSite/Prefeitura/ListarDiarioOficial?v=2024423141416&nr_publicao=&conteudo=&dia=&mes=null&ano=&pagina=0&quantidade=50&_=1716484456143"
    ]

    def start_requests(self):
        page = 0
        url = f'https://sistemas.pmfi.pr.gov.br/RP/SMTIAPI/ApiSite/Prefeitura/ListarDiarioOficial?v=2024423141416&nr_publicao=&conteudo=&dia=&mes=null&ano=&pagina={page}&quantidade=40&_=1716484456143'
        yield scrapy.Request(url, callback=self.parse, meta={'page': page})

    def page_url(self, page):
        return f'https://sistemas.pmfi.pr.gov.br/RP/SMTIAPI/ApiSite/Prefeitura/ListarDiarioOficial?v=2024423141416&nr_publicao=&conteudo=&dia=&mes=null&ano=&pagina={page}&quantidade=40&_=1716484456143'

    def parse(self, response):
        data = json.loads(response.body)
        diary_list = data.get('DiarioList', [])
        delta_date = datetime.strptime(self.delta, '%Y-%m-%d')
        new_pages = False
        for diary in diary_list:
            year = diary.get('ano')
            month = diary.get('mes')
            day = diary.get('dia')
            date_str = f'{year}-{month:02d}-{day:02d}'
            diary_date = datetime.strptime(date_str, '%Y-%m-%d')
            if diary_date >= delta_date:
                new_pages = True
                meta = {
                    'source_id': diary.get('id'),
                    'nr_publicacao': diary.get('nr_publicacao'),
                    'dia': day,
                    'mes': month,
                    'ano': year,
                    'conteudo': diary.get('conteudo'),
                    'diary_date': date_str

                }
                pdf = f"https://sistemas.pmfi.pr.gov.br/RP/SMTIAPI/ApiSite/Prefeitura/infDadosDiario?v=20245314212&id={meta['source_id']}&_=1717435262260"
                if pdf:
                    yield scrapy.Request(pdf, meta=meta, callback=self.save_document)
        if new_pages:
            page = response.meta['page'] + 1
            next_page_url = self.page_url(page)
            yield scrapy.Request(next_page_url, callback=self.parse, meta={'page': page})

    def save_pdf(self, response):
        dict_string = response.body.decode('utf-8')
        dict_string = dict_string.replace("'", '"')
        python_dict = json.loads(dict_string)
        diaries_list = python_dict.get('DiarioList')
        if diaries_list:
            pdf_content = diaries_list[0].get('pdf')
            pdf_content = base64.b64decode(pdf_content)
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
        collections = bd['fozdoiguacu']
        file_path = self.save_pdf(response)
        document = {
            'source': self.name,
            'date': response.meta.get('diary_date'),
            'source_id': response.meta.get('source_id'), # REGEX colocar no formato EX2024...
            'url': response.url,     #
            'file_path': file_path
        }
        collections.insert_one(document)
        return document
