import scrapy
from pymongo import MongoClient
from datetime import datetime
import os
from scrapy_splash import SplashRequest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pdb


class CanoasSpider(scrapy.Spider):
    name = "RS_canoas"
    base_url = "https://sistemas.canoas.rs.gov.br/domc/pesquisar"
    start_urls = [
        "https://sistemas.canoas.rs.gov.br/domc/pesquisar?publication_date=04%2F04%2F2024&publication_final_date=04%2F04%2F2024&publication_type=&title=&content="
    ]
    DOWNLOAD_DELAY = 0.25

    def start_requests(self):
        delta = '2024-04-04' #o delta já será formatado?
        format_init_date = datetime.strptime(delta, '%Y-%m-%d')
        init_date = datetime.strftime(format_init_date, '%d/%m/%Y')
        end_date = '04/04/2024'
        # end_date = datetime.today().strftime('%d/%m/%Y')
        # o end_Date está sendo preenchido com barra, que é o equivalente a %2F.
        # A url responde corretamente, mas talvez não seja adequado
        url = f'https://sistemas.canoas.rs.gov.br/domc/pesquisar?publication_date={init_date}&publication_final_date={end_date}&publication_type=&title=&content='
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        acts_selector = response.xpath('//div[@class="table-responsive"]/table/tbody/tr')

        for act in acts_selector:
            extract_date = act.xpath("./td/text()").extract_first()
            format_date = datetime.strptime(extract_date, '%d/%m/%Y').strftime('%Y-%m-%d')
            name = act.xpath("./td/following-sibling::td/text()").extract_first()
            edition = act.xpath('.//td[contains(text(), "Edição")]/text()').extract_first()
            acessar_botao = response.xpath('.//button[contains(text(), "Acessar")]')
            # script = """
            # function main(splash)
            #     assert(splash:go(splash.args.url))
            #     assert(splash:wait(0.5))
            #     local button_access = splash:select('.//button[contains(text(),"Acessar")]')
            #     assert(button_access:mouse_click())
            #     assert(splash:wait(1))
            #     local button_publication = splash:select('.//button[contains(text(),"Publicação")]')
            #     assert(button_publication:mouse_click())
            #     assert(splash:wait(2))
            #     return {
            #         url = splash:url(),
            #     }
            # end
            # """
            yield {
                'source_url': url_acesso,
                'date': format_date,
                'name': name,
                'edition': edition,
            }
            pdb.set_trace()
            # yield SplashRequest(
            #     url=response.url,
            #     meta=meta,
            #     callback=self.save_document,
            #     dont_filter=True,
            #     endpoint='execute',
            #     args={'lua_source': script}
            # )
            # try:
            #     source_id_initial = search_url.split('/')[-1]
            #     source_id = source_id_initial.replace('_', '').replace('.pdf', '')
            #     ##organizar melhor o source id, por exemplo, para extraordinario _, EX, SUP, etc
            # except:
            # sempre colocar ./


            # url = self.base_url + search_url
        #     yield scrapy.Request(url=url, meta=meta, callback=self.save_document)
        # if acts_selector:
        #     yield from self.next_page(response)

    # def button_click_selenium(self, url):
    #     # Configurando o WebDriver (neste exemplo, usando o Chrome)
    #     options = webdriver.ChromeOptions()
    #     options.add_argument('headless')  # Para execução em modo headless (sem interface gráfica)
    #     driver = webdriver.Chrome(options=options)
    #
    #     # Navegando para a página URL
    #     driver.get(url)
    #
    #     # Localizando e clicando no botão "Acessar"
    #     button_preview = WebDriverWait(driver, 10).until(
    #         EC.element_to_be_clickable((By.XPATH, '//button[contains(text(),"Acessar")]')))
    #     button_preview.click()
    #
    #     # Localizando e clicando no botão "Publicação"
    #     button_publication = WebDriverWait(driver, 10).until(
    #         EC.element_to_be_clickable((By.XPATH, '//button[contains(text(),"Publicação")]')))
    #     button_publication.click()
    #
    #     # Obtendo a URL da página resultante após o clique
    #     url_acesso = driver.current_url
    #
    #     # Fechando o WebDriver após o uso
    #     driver.quit()
    #
    #     return url_acesso

    #browser screen shot - pesquisar

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
        collections = bd['canoas']
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
        actual_page = int(response.xpath('//div[@class="paginator-default"]/ul//li[@class="active"]/span/text()').extract_first())
        next_page = actual_page + 1
        next_page_url = response.xpath(f"//div[@class='paginator-default']/ul//li//a[contains(@href,'&page={next_page}')]/@href").extract_first()
        if next_page_url:
            url = next_page_url
            yield scrapy.Request(url=url, callback=self.parse)

