from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests

API_URL = "http://localhost:3000/importar"

def extrair_perfil_liquipedia(url_jogador):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    try:
        print(f"🕵️ Investigando perfil: {url_jogador}")
        driver.get(url_jogador)
        time.sleep(3) # Tempo para carregar a Wiki

        # 1. Captura de Nome com Suporte a Nomes Romanizados (Ex: Molodoy)
        try:
            nick = driver.find_element(By.ID, "firstHeading").text
            
            # Tenta primeiro o 'Romanized Name', se não achar, vai no 'Name'
            try:
                # Busca especificamente pelo nome ocidental
                xpath_roman = "//*[contains(text(), 'Romanized Name:')]/following-sibling::*"
                nome_completo = driver.find_element(By.XPATH, xpath_roman).text
            except:
                # Se não existir Romanized Name (caso dos BRs), pega o Name comum
                xpath_name = "//*[contains(text(), 'Name:')]/following-sibling::*"
                nome_completo = driver.find_element(By.XPATH, xpath_name).text

            # Formatação: Primeiro Nome "Nick" Último Sobrenome
            partes_nome = nome_completo.split()
            if len(partes_nome) >= 2:
                primeiro = partes_nome[0]
                ultimo = partes_nome[-1]
                nome_formatado = f'{primeiro} "{nick}" {ultimo}'
            else:
                nome_formatado = f'{nome_completo} "{nick}"'

        except Exception as e:
            print(f"⚠️ Erro no nome de {nick}: {e}")
            nome_formatado = nick
        
       # 2. Nacionalidade (Procura o texto 'Nationality:')
        try:
            nacionalidade = driver.find_element(By.XPATH, "//div[contains(@class, 'infobox-description') and text()='Nationality:']/following-sibling::div").text
            # Limpa se houver mais de uma ou espaços
            nacionalidade = nacionalidade.split(',')[0].strip() 
        except:
            nacionalidade = "Brasil"

   # 3. Função / Role (Busca por Texto Flexível)
        try:
            # Procuramos qualquer elemento que tenha o texto "Role:"
            # O ponto (.) no XPath busca em qualquer nível de profundidade
            xpath_role = "//*[normalize-space()='Role:']/following-sibling::*"
            
            elementos_encontrados = driver.find_elements(By.XPATH, xpath_role)
            
            if elementos_encontrados:
                # Pegamos o texto do primeiro elemento irmão que encontrar
                funcao_raw = elementos_encontrados[0].text
                
                # Se o .text falhar, tentamos o textContent via JS (para pegar links internos)
                if not funcao_raw:
                    funcao_raw = driver.execute_script("return arguments[0].textContent;", elementos_encontrados[0])
                
                # Limpeza: Transforma quebras de linha em vírgula e remove espaços extras
                funcao = ", ".join([f.strip() for f in funcao_raw.split('\n') if f.strip()])
            else:
                # Se não achou o "irmão", tenta buscar o pai (algumas tabelas são assim)
                funcao_raw = driver.find_element(By.XPATH, "//div[contains(@class, 'infobox-description') and contains(., 'Role')]/following-sibling::div").text
                funcao = funcao_raw.replace('\n', ', ')

        except Exception as e:
            # Se tudo falhar, em vez de "Pro Player", vamos deixar vazio para sabermos que falhou
            funcao = "Não Identificado"

        # 4. Idade e Nascimento
        try:
            nascimento_raw = driver.find_element(By.XPATH, "//div[contains(@class, 'infobox-description') and text()='Born:']/following-sibling::div").text
            # A Liquipedia escreve: "June 14, 1991 (age 34)" -> Vamos pegar só o número da idade
            idade = "".join(filter(str.isdigit, nascimento_raw.split("age")[1]))
        except:
            idade = "0"
# 5. Time Atual (Lógica para pegar o último item da imagem do Coldzera)
        try:
            # 1. Tenta o campo de time ativo (topo)
            xpath_team = "//*[contains(text(), 'Team:')]/following-sibling::*"
            time_nome = driver.find_element(By.XPATH, xpath_team).text.strip()
            
            if not time_nome or time_nome.lower() in ["none", "", "no team"]:
                print(f"🕵️ Campo principal vazio. Aguardando carregamento do History...")
                
                # ESPERA ATÉ 10 SEGUNDOS para o histórico aparecer
                wait = WebDriverWait(driver, 10)
                
                # Seletor focado na estrutura da imagem: o último link dentro da seção de histórico
                # Ele busca o TH que contém 'History', vai para o TD vizinho e pega o último link (A)
                seletor_ultimo_time = "//th[contains(text(), 'History')]/following-sibling::td//a[not(contains(@class, 'image'))]"
                
                elementos_times = wait.until(EC.presence_of_all_elements_located((By.XPATH, seletor_ultimo_time)))
                
                if elementos_times:
                    # O último da lista é o mais recente (ex: Fake do Biru)
                    time_nome = elementos_times[-1].text
                else:
                    time_nome = "Sem registro"

        except Exception as e:
            # TENTATIVA FINAL: Pega qualquer link azul dentro da caixa de histórico
            try:
                time_nome = driver.execute_script("""
                    let links = document.querySelectorAll('.infobox-history td a, .infobox-list li a');
                    return links.length > 0 ? links[links.length - 1].innerText : 'Sem registro';
                """)
            except:
                time_nome = "Sem registro"
                
        # 6. Status (Tradução completa da Liquipedia para o seu Banco)
        try:
            xpath_status = "//*[contains(text(), 'Status:')]/following-sibling::*"
            status_raw = driver.find_element(By.XPATH, xpath_status).text.lower()
            
            if "active" in status_raw:
                status_final = "Atuando"
            elif "retired" in status_raw:
                status_final = "Não Atuando"
            elif "inactive" in status_raw:
                status_final = "Inativo"
            elif "benched" in status_raw:
                status_final = "Banco de reserva"
            else:
                # Caso apareça algo novo (ex: Coaching), definimos um padrão
                status_final = "Não Atuando"
        except:
            status_final = "Não Atuando"

        print(f"✅ Dados Extraídos: {nome_formatado} | {nacionalidade} | {funcao} | {idade} anos | {time_nome} | {status_final}")

        payload = {
            "nome": nome_formatado,
            "time_atual": time_nome,
            "nacionalidade": nacionalidade,
            "funcao": funcao,
            "idade": idade,
            "Status": status_final,
        }

        res = requests.post(API_URL, json=payload)
        if res.status_code == 201:
            print(f"🚀 {nome_formatado} sincronizado no Supabase!")
        else:
            print(f"⚠️ Erro ao salvar {nome_formatado}: {res.text}")

    except Exception as e:
        print(f"❌ Erro no perfil {url_jogador}: {e}")
    
    finally:
        driver.quit()

# LISTA DE JOGADORES DA FURIA (Links diretos da Liquipedia)
links_liquipedia = [
    "https://liquipedia.net/counterstrike/Coldzera",
]

for link in links_liquipedia:
    extrair_perfil_liquipedia(link)
    time.sleep(2) # Pausa amigável para a Wiki não cansar de você