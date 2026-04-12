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
import subprocess
import re

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

REJEICAO_ESTRITA = [
    "tradução", "traduzir", "redator", "copywriting"
]

REJEICAO_SOFT = [
    "design", "logo", "logotipo", "identidade visual", "banner", "flyer", 
    "ilustração", "illustrator", "photoshop", "video", "edição"
]

TECNOLOGIAS_ALVO = [
    "next.js", "nextjs", "react", "python", "sql", "postgresql", "mysql", 
    "api", "backend", "fullstack", "node", "typescript", "fastapi", "django",
    "js", "next", "automation", "automação", "automações", "bot", "scraping", "ia", "ai", 
    "mvp", "saas", "agente", "scrap", "landing page", "landingpage", "desenvolvimento"
]

def get_chrome_main_version():
    """Tenta detectar a versão principal do Chrome instalada no sistema"""
    try:
        # Tenta no Windows via Registro
        if sys.platform == 'win32':
            import winreg
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                v, _ = winreg.QueryValueEx(key, "version")
                return int(v.split('.')[0])
            except:
                pass
        
        # Tenta via linha de comando (Linux/Mac/Windows)
        commands = [
            ["google-chrome", "--version"],
            ["google-chrome-stable", "--version"],
            ["chrome", "--version"],
            ["chromium", "--version"]
        ]
        
        for cmd in commands:
            try:
                output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()
                # Busca especificamente o número após "Chrome" ou "Google Chrome" ou "Chromium"
                # Ex: "Google Chrome 146.0.7680.0" -> encontra 146
                match = re.search(r'(?:Chrome|Google Chrome|Chromium)\s+(\d+)', output)
                if match:
                    return int(match.group(1))
            except:
                continue
    except Exception as e:
        print(f"⚠️ Erro ao detectar versão do Chrome: {e}")
    return None

def get_driver_options():
    """Retorna uma nova instância de ChromeOptions configurada"""
    options = uc.ChromeOptions()
    
    # Se estiver no GitHub Actions ou HEADLESS=true, roda em headless
    if os.getenv("GITHUB_ACTIONS") == "true" or os.getenv("HEADLESS") == "true":
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # User agent para evitar detecção básica
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    return options
                

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
    
    # 1. Filtro de Rejeição Estrita (Sempre bloqueia)
    for palavra in REJEICAO_ESTRITA:
        if re.search(rf"\b{re.escape(palavra.lower())}\b", texto):
            return False, []
    
    # 2. Busca de Tecnologia (Match Técnico)
    keywords_encontradas = []
    for tech in TECNOLOGIAS_ALVO:
        if re.search(rf"\b{re.escape(tech.lower())}\b", texto):
            keywords_encontradas.append(tech)
            
    # 3. Lógica de Decisão Final
    if keywords_encontradas:
        # Se tem tecnologia, ignoramos a "rejeição soft" (ex: design) e aceitamos
        return True, list(set(keywords_encontradas))
    
    # 4. Filtro de Rejeição Soft (Bloqueia se não houver tecnologia)
    for palavra in REJEICAO_SOFT:
        if re.search(rf"\b{re.escape(palavra.lower())}\b", texto):
            return False, []
            
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
    
    version_main = get_chrome_main_version()
    if version_main:
        print(f"✅ Utilizando Chrome v{version_main} detectado no sistema.")
    else:
        print("⚠️ Não foi possível detectar a versão do Chrome, deixando o UC decidir.")
    
    driver = None
    try:
        # Tentativa 1: Com versão detectada
        try:
            driver = uc.Chrome(options=get_driver_options(), version_main=version_main, use_subprocess=True)
        except Exception as e:
            print(f"❌ Erro ao iniciar driver com versão {version_main}: {e}")
            print("🔄 Tentando inicialização padrão com novas opções...")
            # Tentativa 2: Sem especificar versão e com NOVAS opções (evita RuntimeError)
            driver = uc.Chrome(options=get_driver_options(), use_subprocess=True)
            
    except Exception as e:
        print(f"🛑 Erro fatal ao iniciar o navegador: {e}")
        return
    
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
                            print(f"◽ [JÁ EXISTE] {titulo[:30]}")
                    else:
                        # print(f"❌ [IGNORADA] {titulo[:30]} - Motivo: Não contém keywords alvo.")
                        pass
                        
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