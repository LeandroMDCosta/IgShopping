import logging
import os
import pandas as pd
import time
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from BuscarUrl import IGShoppingScraper

# Configuração de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class IGStoresExtractor:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.wait = None

    def __enter__(self):
        options = webdriver.FirefoxOptions()
        if self.headless:
            options.add_argument("--headless")
        
        # User-agent para evitar bloqueios e garantir comportamento de browser real
        options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0")
        
        self.driver = webdriver.Firefox(options=options)
        self.driver.set_window_size(1920, 1080)
        self.wait = WebDriverWait(self.driver, 10)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            self.driver.quit()

    def carregar_e_extrair(self, url: str, nome_shopping: str) -> List[Dict]:
        lojas_da_unidade = []
        logging.info(f"Processando: {nome_shopping}")
        
        try:
            self.driver.get(url)
            
            # --- LOOP PARA CLICAR EM "CARREGAR MAIS" ---
            while True:
                try:
                    css_botao = "button.bg-primary.text-white.rounded-full"
                    botao = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_botao)))
                    
                    # Rola até o botão e clica via JavaScript para evitar erros de sobreposição
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao)
                    time.sleep(1) 
                    self.driver.execute_script("arguments[0].click();", botao)
                    
                    logging.info(f"Botão 'Ver mais' clicado em {nome_shopping}...")
                    time.sleep(2) # Espera as novas lojas carregarem no DOM
                    
                except (TimeoutException, ElementClickInterceptedException):
                    # Se o botão não for encontrado ou não for mais clicável, saímos do loop
                    logging.info(f"Todas as lojas carregadas para {nome_shopping}.")
                    break

            xpath_nome_loja = "//*[contains(@class, 'text-[#636363]') and contains(@class, 'font-bold')]"
            elementos = self.driver.find_elements(By.XPATH, xpath_nome_loja)
           
            
            for el in elementos:
                nome_loja = el.text.strip()
                if nome_loja:
                    lojas_da_unidade.append({
                        "shopping": nome_shopping,
                        "loja": nome_loja
                    })
                    
        except Exception as e:
            logging.error(f"Erro ao processar unidade {nome_shopping}: {e}")
            
        return lojas_da_unidade

def main():
    input_csv = "IgShoppings.csv" # Arquivo gerado na Parte 1
    output_csv = "lojas_finais_ig.csv"
    logging.info("--- PASSO 1: Atualizando a lista de shoppings ---")
    with IGShoppingScraper(headless=True) as scraper_links:
        novos_links = scraper_links.get_shoppings_links()

        if novos_links:
            # Salva por cima do CSV antigo, garantindo dados novos
            df_novos = pd.DataFrame(novos_links)
            df_novos.to_csv(input_csv, index=False, encoding='utf-8-sig')
            logging.info("Lista de shoppings atualizada com sucesso no CSV!")
        else:
            logging.error("Aviso: Falha ao buscar novos links. Tentando usar o CSV antigo.")

    logging.info("\n--- PASSO 2: Iniciando a extração das lojas ---")

    if not os.path.exists(input_csv):
        logging.error(f"Arquivo {input_csv} não encontrado!")
        return

    df_shoppings = pd.read_csv(input_csv)
    # Garante que as colunas existem (ajuste se os nomes no seu CSV forem diferentes)
    # Se o seu CSV usa 'nome' e 'url', o código abaixo funciona perfeitamente.
    
    dados_totais = []

    with IGStoresExtractor(headless=True) as scraper:
        for _, row in df_shoppings.iterrows():
            url_base = str(row['url']).strip()
            if url_base.endswith('/'):
               url_base = url_base[:-1]
            url_lojas = f"{url_base}/lojas"
            resultado = scraper.carregar_e_extrair(url_lojas, row['nome'])
            dados_totais.extend(resultado)

    if dados_totais:
        df_final = pd.DataFrame(dados_totais)
        # Remove duplicatas que podem surgir no carregamento dinâmico
        df_final = df_final.drop_duplicates()
        df_final.to_csv(output_csv, index=False, encoding='utf-8-sig')
        logging.info(f"Sucesso! {len(df_final)} lojas extraídas e salvas em {output_csv}")
    else:
        logging.warning("Nenhum dado foi extraído.")

if __name__ == "__main__":
    main()