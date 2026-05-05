from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests

# URL da sua API Node.js
API_URL = "http://localhost:3000/importar"

def extrair_perfil_liquipedia(url_jogador):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    try:
        driver.get(url_jogador)
        time.sleep(3)

        # 1. Nick e Nome (Mantendo sua lógica original)
        nick = driver.find_element(By.ID, "firstHeading").text
        try:
            xpath_name = "//*[contains(text(), 'Name:') or contains(text(), 'Romanized Name:')]/following-sibling::*"
            nome_completo = driver.find_element(By.XPATH, xpath_name).text
            partes = nome_completo.split()
            nome_formatado = f'{partes[0]} "{nick}" {partes[-1]}' if len(partes) >= 2 else f'{nome_completo} "{nick}"'
        except:
            nome_formatado = nick

        # 2. Nacionalidade (Texto exato para o banco)
        try:
            nacionalidade = driver.find_element(By.XPATH, "//div[contains(@class, 'infobox-description') and text()='Nationality:']/following-sibling::div").text
            nacionalidade = nacionalidade.split(',')[0].strip()
        except:
            nacionalidade = "Brasil"

        # 3. Time Atual
        try:
            xpath_team = "//*[contains(text(), 'Team:')]/following-sibling::*"
            time_nome = driver.find_element(By.XPATH, xpath_team).text.strip()
        except:
            time_nome = "Sem registro"

        # 4. FUNÇÃO (CORREÇÃO DEFINITIVA PARA MÚLTIPLAS ROLES)
        try:
            # Procuramos a DIV que é irmã da descrição 'Role:'
            xpath_role = "//div[contains(@class, 'infobox-description') and contains(text(), 'Role')]/following-sibling::div"
            role_element = driver.find_element(By.XPATH, xpath_role)
            
            # innerText pega o texto visível de todos os elementos filhos
            texto_roles = role_element.get_attribute("innerText").strip()
            
            # Limpa as quebras de linha e transforma em vírgula: "In-game leader, AWPer"
            funcao = ", ".join([f.strip() for f in texto_roles.split('\n') if f.strip()])
            
            if not funcao:
                funcao = "Pro Player"
        except:
            funcao = "Pro Player"

        # 5. Idade (Correção do NameError)
        idade = 0  # Definimos um valor padrão inicial
        try:
            # Busca a div que contém a data de nascimento e idade
            nascimento_xpath = "//div[contains(@class, 'infobox-description') and text()='Born:']/following-sibling::div"
            nascimento_texto = driver.find_element(By.XPATH, nascimento_xpath).text
            
            # Tenta extrair apenas os números após a palavra 'age'
            if "age" in nascimento_texto:
                partes_idade = nascimento_texto.split("age")[1]
                idade_limpa = "".join(filter(str.isdigit, partes_idade))
                if idade_limpa:
                    idade = int(idade_limpa)
        except Exception as e:
            print(f"⚠️ Não foi possível capturar a idade: {e}")
            idade = 0 # Garante que a variável exista mesmo em caso de erro

        # 6. MONTAGEM DO PAYLOAD (Agora a 'idade' sempre estará definida)
        payload = {
            "nome": nome_formatado,
            "funcao": funcao,
            "idade": int(idade),
            "status": "Atuando",
            "pais_nome": nacionalidade, # Certifique-se que isso envia "Brazil"
            "link": url_jogador
        }

        res = requests.post(API_URL, json=payload)
        print(f"🚀 {nome_formatado} enviado! Função: {funcao}")

    finally:
        driver.quit()

# Lista de teste
links_liquipedia = ["https://liquipedia.net/counterstrike/FalleN"]

for link in links_liquipedia:
    extrair_perfil_liquipedia(link)
    time.sleep(2)