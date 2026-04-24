import logging
import os
import pandas as pd
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

# Configuração global de logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class IGShoppingScraper:
    
    def __init__(self, headless: bool = True):
        self.url = "https://www.igshopping.com.br/"
        self.headless = headless
        self.driver = None
        self.wait = None

    def __enter__(self):
        self._setup_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            self.driver.quit()
            logging.info("Browser finalizado.")

    def _setup_driver(self):
        options = webdriver.FirefoxOptions()
        if self.headless:
            options.add_argument("--headless")
        
        options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0")
        
        self.driver = webdriver.Firefox(options=options)
        self.driver.set_window_size(1920, 1080)
        self.wait = WebDriverWait(self.driver, 15)

    def get_shoppings_links(self) -> List[Dict]:
        logging.info("Buscando links das unidades...")
        self.driver.get(self.url)
        links_data = []
        lojas = self.driver.find_elements(By.CSS_SELECTOR, "div.flex.flex-wrap.justify-center a")

        for loja in lojas:
            try:
                url = loja.get_attribute("href")
                nome = loja.text.strip() or url.split('/')[-1].replace('-', ' ').title()
                
                if url and "igshopping" in url:
                    links_data.append({"nome": nome, "url": url})
            except Exception as e:
                logging.warning(f"Erro ao ler link: {e}")
        
        return list({v['url']: v for v in links_data}.values())
    
    
def save_to_csv(dados: List[Dict], filename: str = "IgShoppings.csv"):
    if not dados:
        logging.warning("Sem dados para salvar.")
        return
    
    diretorio = os.path.dirname(os.path.abspath(__file__))
    caminho_completo = os.path.join(diretorio, filename)
    
    df = pd.DataFrame(dados)
    df = df.drop_duplicates(subset=['nome'])
    df.to_csv(caminho_completo, index=False, encoding='utf-8-sig')
    logging.info(f"Arquivo salvo com sucesso em: {caminho_completo}")

if __name__ == "__main__":
    with IGShoppingScraper (headless=True) as scraper:
        resultado = scraper.get_shoppings_links()

    if resultado:
        print(f"\n--- SUCESSO ---")
        print(f"Total de lojas extraídas: {len(resultado)}")
        save_to_csv(resultado)
    else:
        print("\nErro: Nenhum dado foi coletado.")