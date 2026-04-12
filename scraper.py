import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sqlite3
import time
import random
import os
import requests
import sys
from datetime import datetime
from dotenv import load_dotenv

# Forǜa UTF-8 no terminal para evitar erros de emoji no Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Carrega configurações
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GEMINI_KEY = os.getenv("GEMINI_KEY")
DB_PATH = "vagas.db"

PALAVRAS_REJEITADAS = [
    "design", "logo", "logotipo", "tradução", "traduzir", "identidade visual", 
    "banner", "flyer", "ilustração", "illustrator", "photoshop", "cana", "video", 
    "edição", "redator", "copywriting", "social media", "vendas", "marketing"
]

TECNOLOGIAS_ALVO = [
    "next.js", "nextjs", "react", "python", "sql", "postgresql", "mysql", 
    "api", "backend", "fullstack", "node", "typescript", "fastapi", "django",
    "js", "next", "automation", "automação", "bot", "scraping", "ia", "ai", 
    "mvp", "saas", "agente", "scrap"
]

def enviar_telegram(titulo, link, orcamento, descricao, keywords):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("⚠️ Telegram não configurado no .env")
        return False
        
    keyword_str = ", ".join(keywords) if keywords else "N/A"
    
    mensagem = f"🚀 *NOVA VAGA ENCONTRADA!*\n\n"
    mensagem += f"📌 *Título:* {titulo}\n"
    mensagem += f"💰 *Orçamento:* {orcamento}\n"
    mensagem += f"⚡ *Match Técnico:* `{keyword_str}`\n\n"
    mensagem += f"📝 *Resumo:* {descricao[:250]}...\n\n"
    mensagem += f"🔗 [Ver Vaga no Workana]({link})"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    
    try:
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro ao enviar Telegram: {e}")
        return False

def enviar_alerta(mensagem_texto):
    """Envia um alerta genérico (ex: erros) para o Telegram"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem_texto}
    try:
        requests.post(url, json=payload)
    except:
        pass

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vagas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT,
            descricao TEXT,
            orcamento TEXT,
            link TEXT UNIQUE,
            data_coleta TEXT,
            notificada INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    return conn

def ja_existe(conn, link):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM vagas WHERE link = ?", (link,))
    return cursor.fetchone()[0] > 0

def salvar_vaga(conn, titulo, descricao, orcamento, link, keywords):
    if not ja_existe(conn, link):
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO vagas (titulo, descricao, orcamento, link, data_coleta, notificada)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (titulo, descricao, orcamento, link, datetime.now().isoformat()))
        conn.commit()
        
        # Como é uma vaga nova, enviamos para o Telegram imediatamente
        enviar_telegram(titulo, link, orcamento, descricao, keywords)
        return True
    return False

def validar_vaga(titulo, descricao):
    texto = (str(titulo) + " " + str(descricao)).lower()
    
    # Filtro de rejeição (Design, tradução, etc)
    for palavra in PALAVRAS_REJEITADAS:
        if palavra in texto:
            return False, []
    
    # Filtro de interesse (Stack)
    keywords_encontradas = []
    for tech in TECNOLOGIAS_ALVO:
        if tech in texto:
            keywords_encontradas.append(tech)
            
    if keywords_encontradas:
        return True, list(set(keywords_encontradas)) # Remove duplicatas
    
    return False, []

def expandir_descricao(driver, job):
    """Tenta clicar no botão 'Ver mais' (expander) para pegar a descrição completa"""
    try:
        expander = job.find_element(By.CSS_SELECTOR, ".expander")
        driver.execute_script("arguments[0].click();", expander)
        # Espera um pouco para a expansão acontecer
        time.sleep(0.5)
        return True
    except:
        return False

def scrape_workana(paginas=3):
    conn = init_db()
    
    options = uc.ChromeOptions()
    
    # Modo Headless obrigatório em ambiente de CI (GitHub Actions)
    if os.getenv('GITHUB_ACTIONS') == 'true' or os.getenv('HEADLESS') == 'true':
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = uc.Chrome(options=options)
    
    vagas_encontradas = 0
    
    try:
        for pagina in range(1, paginas + 1):
            url = f"https://www.workana.com/jobs?category=it-programming&language=pt&sort=created_desc&page={pagina}"
            print(f"\n🔍 Acessando pǭgina {pagina} (TI e Programaçǜo)...")
            driver.get(url)
            time.sleep(random.uniform(4, 7))
            
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".project-item"))
                )
            except:
                print(f"⚠️ Tempo esgotado ou nenhuma vaga encontrada na pǭgina {pagina}")
                continue
            
            jobs = driver.find_elements(By.CSS_SELECTOR, ".project-item")
            print(f"📦 Analisando {len(jobs)} jobs...")
            
            for job in jobs:
                try:
                    # Tǭtulo e Link
                    titulo_elem = job.find_element(By.CSS_SELECTOR, ".project-title a")
                    titulo = titulo_elem.text.strip()
                    link = titulo_elem.get_attribute("href")
                    
                    # Orǜamento
                    try:
                        orcamento = job.find_element(By.CSS_SELECTOR, ".budget").text.strip()
                    except:
                        orcamento = "A consultar"
                        
                    # Expansǜo para Descriǜo Completa
                    expandir_descricao(driver, job)
                    
                    # Descriǜo (tenta pegar o texto após expansão)
                    try:
                        descricao = job.find_element(By.CSS_SELECTOR, ".project-details").text.strip()
                    except:
                        descricao = "Sem descriǜo disponǭvel"
                    
                    # Processamento
                    is_valida, keywords = validar_vaga(titulo, descricao)
                    
                    if is_valida:
                        if salvar_vaga(conn, titulo, descricao, orcamento, link, keywords):
                            print(f"✅ [ACEITA] {titulo[:60]} - Keywords: {', '.join(keywords)}")
                            vagas_encontradas += 1
                        else:
                            # print(f"◽ Jǭ processada: {titulo[:30]}")
                            pass
                    else:
                        print(f"❌ [IGNORADA] {titulo[:30]} - Motivo: Não contém keywords alvo.")
                        
                except Exception as e:
                    # print(f"Erro ao processar item: {e}")
                    continue
                    
            time.sleep(random.uniform(2, 5))
            
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass
        conn.close()
        print(f"\n✨ Processamento finalizado. Total de novas vagas: {vagas_encontradas}")

if __name__ == "__main__":
    scrape_workana(paginas=3)