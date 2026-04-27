import scrapy
import logging
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

class IgshoppingcrawlerSpider(scrapy.Spider):
    name = 'igshopping' 
    
    # 1. Iniciamos a classe corretamente para o Scrapy aceitar
    def __init__(self, headless: bool = True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headless = headless
        
        # 2. Mantemos o self.df EXATAMENTE como a sua Pipeline espera encontrar
        self.df = {
            'shopping_administrator': [],
            'shopping_name': [],
            'shopping_site': [],
            'shopping_data_url': [],
            'store_name': [],
            'store_floor': [],
            'store_site': [],
            'store_phone': [],
            'store_type': [],
            'source_page': []
        }
        
        # 3. Configuramos e abrimos o Selenium apenas UMA vez aqui no início
        options = webdriver.FirefoxOptions()
        if self.headless:
            options.add_argument("--headless")
        
        options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0")
        
        self.driver = webdriver.Firefox(options=options)
        self.driver.set_window_size(1920, 1080)
        self.wait = WebDriverWait(self.driver, 10)

    def start_requests(self):
        shopping_administrator = 'IGSHOPPING'
        shopping_list = [
            {
                'shopping_name': 'Shopping Ariquemes',
                'shopping_site': 'https://www.igshopping.com.br/ariquemes',
                'shopping_data_url': 'https://www.igshopping.com.br/ariquemes/lojas'
            },
            {
                'shopping_name': 'Shopping Ji Paraná',
                'shopping_site': 'https://www.igshopping.com.br/ji-parana',
                'shopping_data_url': 'https://www.igshopping.com.br/ji-parana/lojas'
            },
            {
                'shopping_name': 'Shopping Porto Velho',
                'shopping_site': 'https://www.igshopping.com.br/porto-velho',
                'shopping_data_url': 'https://www.igshopping.com.br/porto-velho/lojas'
            },
            {
                'shopping_name': 'Shopping Rolim de Moura',
                'shopping_site': 'https://www.igshopping.com.br/rolim-de-moura',
                'shopping_data_url': 'https://www.igshopping.com.br/rolim-de-moura/lojas'
            },
            {
                'shopping_name': 'Shopping Jaru',
                'shopping_site': 'https://www.igshopping.com.br/jaru',
                'shopping_data_url': 'https://www.igshopping.com.br/jaru/lojas'
            }
        ]
        
        for shopping in shopping_list:
            yield scrapy.Request(
                url=shopping['shopping_data_url'], 
                meta={
                    'shopping_name': shopping['shopping_name'], 
                    'admin': shopping_administrator,
                    'shopping_site': shopping['shopping_site']
                },
                dont_filter=True
            )

    def parse(self, response):
        nome_shopping = response.meta['shopping_name']
        admin = response.meta['admin']
        site = response.meta['shopping_site']
        url = response.url
        
        logging.info(f"Processando: {nome_shopping}")
        
        try:
            self.driver.get(url)
            xpath = '//div[@class="grid grid-cols-2 w-full lg:grid-cols-3 place-content-center space-x-2"]/*'
            css_botao = "button.bg-primary.text-white.rounded-full"
            
            # Lógica de rolagem e clique do Selenium
            while True:
                try:
                    itens_antes_do_clique = len(self.driver.find_elements(By.XPATH, xpath))
                    botao = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_botao)))
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao)
                    
                    posicao_anterior = None
                    while True:
                        posicao_atual = botao.location['y']
                        if posicao_atual == posicao_anterior:
                            break 
                        posicao_anterior = posicao_atual
                        time.sleep(0.05)
                        
                    self.driver.execute_script("arguments[0].click();", botao)
                    logging.info(f"Botão 'carregar mais' clicado em {nome_shopping}...")
                    
                    self.wait.until(
                        lambda driver: len(driver.find_elements(By.XPATH, xpath)) > itens_antes_do_clique
                    )
                    
                except (TimeoutException, ElementClickInterceptedException):
                    logging.info(f"Todas as lojas carregadas para {nome_shopping}.")
                    break

            # Extração dos dados
            xpath_nome_loja = "//*[contains(@class, 'text-[#636363]') and contains(@class, 'font-bold')]"
            elementos = self.driver.find_elements(By.XPATH, xpath_nome_loja)

            for el in elementos:
                # 4. Inserimos no self.df para que a Pipeline possa ler depois
                self.df['shopping_administrator'].append(admin)
                self.df['shopping_name'].append(nome_shopping)
                self.df['shopping_site'].append(site)
                self.df['shopping_data_url'].append(url)
                self.df['store_name'].append(el.text.strip())
                self.df['store_floor'].append(None)
                self.df['store_site'].append(None)
                self.df['store_phone'].append(None)
                self.df['store_type'].append(None)
                self.df['source_page'].append('lojas')
                    
        except Exception as e:
            logging.error(f"Erro ao processar unidade {nome_shopping}: {e}")

    # 5. Fechamento seguro do navegador quando o Scrapy terminar de raspar tudo
    def closed(self, reason):
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()
            logging.info("Navegador Firefox fechado com sucesso. Iniciando Pipeline...")

            total_lojas = len(self.df['store_name'])
        logging.info(f"Rendimento total: {total_lojas} lojas raspadas em todos os shoppings. Iniciando envio para BigQuery...")