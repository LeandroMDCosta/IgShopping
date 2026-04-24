import scrapy
import logging
import os
from urllib import response
import pandas as pd
import time
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
git 


class IgshoppingcrawlerSpider(scrapy.Spider):
    name = 'igshopping' 
    
    df = {'shopping_administrator': [],
          'shopping_name': [],
          'shopping_site': [],
          'shopping_data_url': [],
          'store_name': [],
          'store_floor': [],
          'store_site': [],
          'store_phone': [],
          'store_type': [],
          'source_page': []}
    
    def start_requests(self):
        shopping_list = []
        shopping_administrator = 'IGSHOPPING'


        shopping_list.append(
                {'shopping_administrator': shopping_administrator,
                'shopping_name': 'Shopping Ariquemes',
                'shopping_site': 'https://www.igshopping.com.br/ariquemes',
                'shopping_data_url': 'https://www.igshopping.com.br/ariquemes/lojas'
                }
        )
        shopping_list.append(
            {'shopping_administrator': shopping_administrator,
             'shopping_name': 'Shopping Ji Paraná',
             'shopping_site': 'https://www.igshopping.com.br/ji-parana',
             'shopping_data_url': 'https://www.igshopping.com.br/ji-parana/lojas'
             }
        )

        shopping_list.append(
            {'shopping_administrator': shopping_administrator,
             'shopping_name': 'Shopping Porto Velho',
             'shopping_site': 'https://www.igshopping.com.br/porto-velho',
             'shopping_data_url': 'https://www.igshopping.com.br/porto-velho/lojas'
             }
        )

        shopping_list.append(
            {'shopping_administrator': shopping_administrator,
             'shopping_name': 'Shopping Rolim de Moura',
             'shopping_site': 'https://www.igshopping.com.br/rolim-de-moura',
             'shopping_data_url': 'https://www.igshopping.com.br/rolim-de-moura/lojas'
             }
        )

        shopping_list.append(
            {'shopping_administrator': shopping_administrator,
             'shopping_name': 'Shopping Jaru',
             'shopping_site': 'https://www.igshopping.com.br/jaru',
             'shopping_data_url': 'https://www.igshopping.com.br/jaru/lojas'
             }
        )
        
        for shopping in shopping_list:
            yield scrapy.Request(url=shopping['shopping_data_url'], meta=shopping)

    def parse(self, response):


        def __init__(self, headless: bool = True):
            self.headless = headless
            self.driver = None
            self.wait = None

        def __enter__(self):
            options = webdriver.FirefoxOptions()
            if self.headless:
                options.add_argument("--headless")
            
            options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0")
            
            self.driver = webdriver.Firefox(options=options)
            self.driver.set_window_size(1920, 1080)
            self.wait = WebDriverWait(self.driver, 10)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.driver:
                self.driver.quit()

        def carregar_e_extrair(self, url: str, nome_shopping: str) -> List[Dict]:
            logging.info(f"Processando: {nome_shopping}")
            
            try:
                self.driver.get(url)
                xpath = '//div[@class="grid grid-cols-2 w-full lg:grid-cols-3 place-content-center space-x-2"]/*'
                css_botao = "button.bg-primary.text-white.rounded-full"
                
                while True:
                    try:
                        itens_antes_do_clique = len(self.driver.find_elements(By.XPATH, xpath))
                        botao = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_botao)))
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao)
                        posicao_anterior = None
                        while True:
                            posicao_atual = botao.location['y']
                            if posicao_atual == posicao_anterior:
                             break # O botão parou de se mover, o scroll terminou!
                            posicao_anterior = posicao_atual
                            time.sleep(0.05) # Pausa de apenas 50ms para a próxima checagem
                        self.driver.execute_script("arguments[0].click();", botao)
                        
                        logging.info(f"Botão 'carregar mais' clicado em {nome_shopping}...")
                        self.wait.until(
                        lambda driver: len(driver.find_elements(By.XPATH, xpath)) > itens_antes_do_clique
                        )
                        
                    except (TimeoutException, ElementClickInterceptedException):
                    
                        logging.info(f"Todas as lojas carregadas para {nome_shopping}.")
                        break
                

                xpath_nome_loja = "//*[contains(@class, 'text-[#636363]') and contains(@class, 'font-bold')]"
                elementos = self.driver.find_elements(By.XPATH, xpath_nome_loja)
            
                
                for el in elementos:
                    self.df['shopping_administrator'].append('IGSHOPPING')
                    self.df['shopping_name'].append(nome_shopping)
                    self.df['shopping_site'].append(url.replace('/lojas', ''))
                    self.df['shopping_data_url'].append(url)
                    self.df['store_name'].append(el.text.strip())
                    self.df['store_floor'].append(None)
                    self.df['store_site'].append(None)
                    self.df['store_phone'].append(None)
                    self.df['store_type'].append(None)
                    self.df['source_page'].append('lojas')
                        
            except Exception as e:
                logging.error(f"Erro ao processar unidade {nome_shopping}: {e}")
            
