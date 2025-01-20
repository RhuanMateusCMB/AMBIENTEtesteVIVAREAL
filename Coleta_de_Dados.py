# Bibliotecas para interface web
import streamlit as st
import streamlit.components.v1 as components
import schedule

# Bibliotecas para manipulação de dados
import pandas as pd

# Enviar email
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from base64 import urlsafe_b64encode
from email.mime.text import MIMEText
import base64
import os
import pickle
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Bibliotecas Selenium para web scraping
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Bibliotecas utilitárias
import time
import random
from datetime import datetime, timedelta
import logging
from typing import Optional, List, Dict
from dataclasses import dataclass
from supabase import create_client

# Configuração da página Streamlit
st.set_page_config(
    page_title="CMB - Capital",
    page_icon="🏗️",
    layout="wide"
)

# Estilo CSS personalizado
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        height: 3em;
        font-size: 20px;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    /* Estilo para botão de submit */
    .stButton>button {
        background-color: #FF4B4B !important;
        color: white !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        border-radius: 5px !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        background-color: #FF3333 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
    }
    </style>
    """, unsafe_allow_html=True)

@dataclass
class ConfiguracaoScraper:
    tempo_espera: int = 8
    pausa_rolagem: int = 2
    espera_carregamento: int = 4
    url_base: str = "https://www.vivareal.com.br/venda/ceara/eusebio/lote-terreno_residencial/#onde=,Cear%C3%A1,Eus%C3%A9bio,,,,,city,BR%3ECeara%3ENULL%3EEusebio,-14.791623,-39.283324,&itl_id=1000183&itl_name=vivareal_-_botao-cta_buscar_to_vivareal_resultado-pesquisa"
    tentativas_max: int = 3

class SupabaseManager:
    def __init__(self):
        self.url = st.secrets["SUPABASE_URL"]
        self.key = st.secrets["SUPABASE_KEY"]
        self.supabase = create_client(self.url, self.key)

    def inserir_dados(self, df):
        result = self.supabase.table('teste').select('id').order('id.desc').limit(1).execute()
        ultimo_id = result.data[0]['id'] if result.data else 0
        
        df['id'] = df['id'].apply(lambda x: x + ultimo_id)
        df['data_coleta'] = pd.to_datetime(df['data_coleta']).dt.strftime('%Y-%m-%d')
        
        registros = df.to_dict('records')
        self.supabase.table('teste').insert(registros).execute()

class ScraperVivaReal:
    def __init__(self, config: ConfiguracaoScraper):
        self.config = config
        self.logger = self._configurar_logger()

    @staticmethod
    def _configurar_logger() -> logging.Logger:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)

    def _get_random_user_agent(self):
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36'
        ]
        return random.choice(user_agents)

    def _configurar_navegador(self) -> webdriver.Chrome:
        try:
            opcoes_chrome = Options()
            opcoes_chrome.add_argument('--headless=new')
            opcoes_chrome.add_argument('--no-sandbox')
            opcoes_chrome.add_argument('--disable-dev-shm-usage')
            opcoes_chrome.add_argument('--window-size=1920,1080')
            opcoes_chrome.add_argument('--disable-blink-features=AutomationControlled')
            opcoes_chrome.add_argument('--enable-javascript')
            
            user_agent = self._get_random_user_agent()
            opcoes_chrome.add_argument(f'--user-agent={user_agent}')
            opcoes_chrome.add_argument('--accept-language=pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7')
            opcoes_chrome.add_argument('--accept=text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8')
            
            opcoes_chrome.add_argument('--disable-notifications')
            opcoes_chrome.add_argument('--disable-popup-blocking')
            opcoes_chrome.add_argument('--disable-extensions')
            opcoes_chrome.add_argument('--disable-gpu')
            
            service = Service("/usr/bin/chromedriver")
            navegador = webdriver.Chrome(service=service, options=opcoes_chrome)
            
            navegador.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": user_agent,
                "platform": "Windows NT 10.0; Win64; x64"
            })
            
            navegador.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            navegador.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt']})")
            navegador.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            
            return navegador
        except Exception as e:
            self.logger.error(f"Erro ao configurar navegador: {str(e)}")
            return None

    def _verificar_pagina_carregada(self, navegador: webdriver.Chrome) -> bool:
        try:
            return navegador.execute_script("return document.readyState") == "complete"
        except Exception:
            return False

    def _capturar_localizacao(self, navegador: webdriver.Chrome) -> tuple:
        try:
            time.sleep(self.config.espera_carregamento)

            try:
                localizacao_elemento = WebDriverWait(navegador, self.config.tempo_espera).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.search-input-location'))
                )
                texto_localizacao = localizacao_elemento.text.strip()
                if texto_localizacao:
                    partes = texto_localizacao.split(' - ')
                    if len(partes) == 2:
                        return partes[0], partes[1].strip()
            except Exception:
                pass
    
            url_parts = navegador.current_url.split('/')
            for i, part in enumerate(url_parts):
                if part == 'ceara':
                    return 'Eusébio', 'CE'
                    
            return 'Eusébio', 'CE'
    
        except Exception as e:
            self.logger.error(f"Erro ao capturar localização: {str(e)}")
            return 'Eusébio', 'CE'

    def _rolar_pagina(self, navegador: webdriver.Chrome) -> None:
        try:
            altura_total = navegador.execute_script("return document.body.scrollHeight")
            altura_atual = 0
            passo = altura_total / 4
            
            for _ in range(4):
                altura_atual += passo
                navegador.execute_script(f"window.scrollTo(0, {altura_atual});")
                time.sleep(random.uniform(0.5, 1.0))
                
            navegador.execute_script(f"window.scrollTo(0, {altura_total - 200});")
            time.sleep(1)
        except Exception as e:
            self.logger.error(f"Erro ao rolar página: {str(e)}")

    def _extrair_dados_imovel(self, imovel: webdriver.remote.webelement.WebElement,
                    id_global: int, pagina: int) -> Optional[Dict]:
        try:
            wait = WebDriverWait(imovel, 10)
            
            try:
                preco_elemento = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="price"]'))
                )
                preco_texto = preco_elemento.text
            except Exception as e:
                self.logger.warning(f"Erro ao extrair preço: {e}")
                return None

            try:
                area_elemento = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'span[class*="detail-area"]'))
                )
                area_texto = area_elemento.text
            except Exception as e:
                self.logger.warning(f"Erro ao extrair área: {e}")
                return None

            def converter_preco(texto: str) -> float:
                try:
                    numero = texto.replace('R$', '').replace('.', '').replace(',', '.').strip()
                    return float(numero)
                except (ValueError, AttributeError):
                    return 0.0

            def converter_area(texto: str) -> float:
                try:
                    numero = texto.replace('m²', '').replace(',', '.').strip()
                    return float(numero)
                except (ValueError, AttributeError):
                    return 0.0

            preco = converter_preco(preco_texto)
            area = converter_area(area_texto)
            preco_m2 = round(preco / area, 2) if area > 0 else 0.0

            try:
                titulo = imovel.find_element(By.CSS_SELECTOR, 'span.property-card__title').text
            except Exception:
                titulo = "Título não disponível"

            try:
                endereco = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'span[class*="address"]'))
                ).text
            except Exception:
                endereco = "Endereço não disponível"

            try:
                link = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'a[class*="property-card__content-link"]'))
                ).get_attribute('href')
            except Exception:
                link = ""

            if preco == 0 or area == 0:
                self.logger.warning(f"Dados incompletos para imóvel ID {id_global}: Preço={preco}, Área={area}")
                return None

            return {
                'id': id_global,
                'titulo': titulo,
                'endereco': endereco,
                'area_m2': area,
                'preco_real': preco,
                'preco_m2': preco_m2,
                'link': link,
                'pagina': pagina,
                'data_coleta': datetime.now().strftime("%Y-%m-%d"),
                'estado': '',
                'localidade': ''
            }

        except Exception as e:
            self.logger.error(f"Erro ao extrair dados: {str(e)}")
            return None

    def _encontrar_botao_proxima(self, espera: WebDriverWait) -> Optional[webdriver.remote.webelement.WebElement]:
        seletores = [
            "//button[contains(., 'Próxima página')]",
            "//a[contains(., 'Próxima página')]",
            "//button[@title='Próxima página']",
            "//a[@title='Próxima página']"
        ]

        for seletor in seletores:
            try:
                return espera.until(EC.element_to_be_clickable((By.XPATH, seletor)))
            except:
                continue
        return None

    def coletar_dados(self, num_paginas: int = 1) -> Optional[pd.DataFrame]:
        navegador = None
        todos_dados: List[Dict] = []
        id_global = 0
        progresso = st.progress(0)
        status = st.empty()
    
        try:
            self.logger.info("Iniciando coleta de dados...")
            navegador = self._configurar_navegador()
            if navegador is None:
                st.error("Não foi possível inicializar o navegador")
                return None
    
            espera = WebDriverWait(navegador, self.config.tempo_espera)
            navegador.get(self.config.url_base)
            self.logger.info("Navegador acessou a URL com sucesso")
            
            for _ in range(30):
                if self._verificar_pagina_carregada(navegador):
                    break
                time.sleep(1)
            
            try:
                lista_resultados = espera.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.results-list'))
                )
                self.logger.info("Lista de resultados encontrada")
            except Exception as e:
                self.logger.error("Não foi possível encontrar a lista de resultados")
                return None

            localidade, estado = self._capturar_localizacao(navegador)
            if not localidade or not estado:
                st.error("Não foi possível capturar a localização")
                return None

            for pagina in range(1, num_paginas + 1):
                try:
                    status.text(f"⏳ Processando página {pagina}/{num_paginas}")
                    progresso.progress(pagina / num_paginas)
                    self.logger.info(f"Processando página {pagina}")
                    
                    pausa = random.uniform(1, 3)
                    time.sleep(pausa)
                    
                    time.sleep(self.config.espera_carregamento)
                    self._rolar_pagina(navegador)

                    imoveis = None
                    for tentativa in range(3):
                        try:
                            imoveis = espera.until(EC.presence_of_all_elements_located(
                                (By.CSS_SELECTOR, 'div.results-list article')
                            ))
                            if imoveis:
                                break
                            time.sleep(5)
                        except Exception:
                            if tentativa == 2:
                                raise
                            time.sleep(5)
                            continue

                    if not imoveis:
                        self.logger.warning(f"Sem imóveis na página {pagina}")
                        break

                    for imovel in imoveis:
                        id_global += 1
                        if dados := self._extrair_dados_imovel(imovel, id_global, pagina):
                            dados['estado'] = estado
                            dados['localidade'] = localidade
                            todos_dados.append(dados)

                    if pagina < num_paginas:
                        botao_proxima = self._encontrar_botao_proxima(espera)
                        if not botao_proxima:
                            break
                        navegador.execute_script("arguments[0].click();", botao_proxima)
                        time.sleep(2)

                except Exception as e:
                    self.logger.error(f"Erro na página {pagina}: {str(e)}")
                    continue

            return pd.DataFrame(todos_dados) if todos_dados else None

        except Exception as e:
            self.logger.error(f"Erro crítico: {str(e)}")
            st.error(f"Erro durante a coleta: {str(e)}")
            return None

        finally:
            if navegador:
                try:
                    navegador.quit()
                except Exception as e:
                    self.logger.error(f"Erro ao fechar navegador: {str(e)}")

def gerar_token():
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    creds = None
    
    credentials_dict = json.loads(st.secrets["GMAIL_CREDENTIALS"])
    
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(
                credentials_dict, 
                SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds

def enviar_email(total_dados):
   """Envia email usando Gmail API"""
   try:
       creds = gerar_token()
       service = build('gmail', 'v1', credentials=creds)
       
       mensagem = MIMEText(f'Coleta finalizada. Total de {total_dados} registros coletados.')
       mensagem['to'] = 'rhuan.apple27@gmail.com'
       mensagem['subject'] = f'Coleta de Dados - {datetime.now().strftime("%d/%m/%Y")}'
       
       raw = base64.urlsafe_b64encode(mensagem.as_bytes()).decode()
       
       try:
           service.users().messages().send(userId='me', body={'raw': raw}).execute()
           logging.info("Email enviado com sucesso")
       except Exception as e:
           logging.error(f"Erro ao enviar email: {str(e)}")
           
   except Exception as e:
       logging.error(f"Erro na configuração do email: {str(e)}")

def scheduled_job():
   try:
       config = ConfiguracaoScraper()
       scraper = ScraperVivaReal(config)
       df = scraper.coletar_dados()
       if df is not None:
           db = SupabaseManager()
           db.inserir_dados(df)
           total_dados = len(df)
           enviar_email(total_dados)
           st.success("Coleta automática concluída")
           return True
       return False
   except Exception as e:
       logging.error(f"Erro na coleta: {str(e)}")
       return False

def main():
    try:
        st.title("🏗️ Coleta Informações Gerais Terrenos - Eusebio, CE")
        
        st.markdown("""
        <div style='text-align: center; padding: 1rem 0;'>
            <p style='font-size: 1.2em; color: #666;'>
                Coleta de dados de terrenos à venda em Eusébio, Ceará
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("""
        ℹ️ **Informações sobre a coleta:**
        - Serão coletadas 1 páginas de resultados
        - Apenas terrenos em Eusébio/CE
        """)
        
        if st.button("🚀 Iniciar Coleta", type="primary", use_container_width=True):
           with st.spinner("Iniciando coleta de dados..."):
               config = ConfiguracaoScraper()
               scraper = ScraperVivaReal(config)
               df = scraper.coletar_dados()
               
               if df is not None:
                   try:
                       db = SupabaseManager()
                       db.inserir_dados(df)
                       total_dados = len(df)
                       enviar_email(total_dados)
                       st.success("✅ Dados coletados e salvos com sucesso!")
                       st.balloons()
                   except Exception as e:
                       st.error(f"Erro ao salvar no banco: {str(e)}")
       
    except Exception as e:
       st.error(f"❌ Erro inesperado: {str(e)}")

if __name__ == "__main__":
    main()
