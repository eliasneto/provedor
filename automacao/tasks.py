import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

from .models import Automacao
from provedor.models import Provedor

def automacao_google_provedores(tarefa_id, file_path):
    # Configuração do Navegador (Headless para rodar no seu Ubuntu/Docker)
    chrome_options = Options()
    # chrome_options.add_argument("--headless") # Descomente para rodar sem abrir a janela
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        df = pd.read_excel(file_path)
        tarefa = Automacao.objects.get(id=tarefa_id)

        for index, row in df.iterrows():
            # Verificação de interrupção manual
            tarefa.refresh_from_db()
            if tarefa.status != 'executando':
                break

            nome_pesquisa = row['nome']
            print(f"Pesquisando: {nome_pesquisa}")

            # 1. Acessa o Google
            driver.get("https://www.google.com")
            search_box = driver.find_element(By.NAME, "q")
            search_box.send_keys(f"provedor de internet {nome_pesquisa} site oficial")
            search_box.send_keys(Keys.ENTER)
            time.sleep(2)

            # 2. Pega o primeiro link (tentativa de site oficial)
            primeiro_link = driver.find_element(By.CSS_SELECTOR, "h3").find_element(By.XPATH, "..").get_attribute("href")

            # 3. Salva no módulo de Provedores
            Provedor.objects.get_or_create(
                nome=nome_pesquisa,
                defaults={
                    'url_site': primeiro_link,
                    'cidade': row.get('cidade', 'Itaitinga'), # Padrão Itaitinga
                    'estado': row.get('estado', 'CE')
                }
            )
            
            print(f"Sucesso: {nome_pesquisa} cadastrado com o site {primeiro_link}")
            time.sleep(1)

        tarefa.status = 'concluido'
        tarefa.save()

    except Exception as e:
        print(f"Erro: {e}")
        tarefa = Automacao.objects.get(id=tarefa_id)
        tarefa.status = 'falha'
        tarefa.save()
    
    finally:
        driver.quit()

# Registro da nova automação
REGISTRY = {
    'busca_google_provedores': automacao_google_provedores,
}