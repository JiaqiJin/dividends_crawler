import re
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Configuración de Selenium en modo headless
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# --- 1. Abrir la página principal ---
base_url = "https://divvydiary.com/en/calendar"
driver.get(base_url)
time.sleep(8)  # Espera para que se carguen los datos dinámicos

main_html = driver.page_source
soup_main = BeautifulSoup(main_html, "html.parser")

# --- 2. Buscar los enlaces interactivos ---
# Como el texto del enlace incluye elementos hijos (por ejemplo, <time>), usamos get_text() para obtener el texto combinado.
interactive_links = []
for a in soup_main.find_all("a"):
    text = a.get_text(" ", strip=True)
    if "Show all" in text and "dividends on" in text:
        interactive_links.append(a)

print(f"Se encontraron {len(interactive_links)} enlaces interactivos:")
for link in interactive_links:
    link_text = link.get_text(" ", strip=True)
    href = link.get("href")
    print(f"{link_text} -> {href}")

# --- 3. Función para extraer dividendos de una página (estructura similar en cada día) ---
def extraer_dividendos(soup):
    data = []
    # Patrones para extraer datos
    date_pattern = re.compile(r"\d{2}/\d{2}/\d{4}")
    percent_pattern = re.compile(r"\d+\.\d+%")
    amount_pattern = re.compile(r"(CA\$|€|£|DKK|KWD|THB|NOK|₹|HK\$|R\$|\$)\s?\d{1,3}(?:[,.]?\d{1,3})*(?:\.\d{1,2})?")
    
    # Buscar cabeceras de día (ej. "Saturday 1 February 2025")
    day_headers = []
    for tag in soup.find_all(True):
        text = tag.get_text(strip=True)
        if re.match(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+\d{1,2}\s+\w+\s+\d{4}$", text):
            day_headers.append(tag)
    
    for header in day_headers:
        siblings = header.find_next_siblings()
        for sib in siblings:
            sib_text = sib.get_text(" ", strip=True)
            # Si encontramos otra cabecera de día, detenemos el procesamiento del grupo
            if re.match(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+\d{1,2}\s+\w+\s+\d{4}$", sib_text):
                break
            
            # Extraer fechas (se espera que aparezcan al menos dos: Ex-Date y Pay Date)
            dates = date_pattern.findall(sib_text)
            if len(dates) >= 2:
                ex_date, pay_date = dates[:2]
            else:
                ex_date, pay_date = "N/A", "N/A"
            
            div_percent_match = percent_pattern.search(sib_text)
            div_percent = div_percent_match.group(0) if div_percent_match else "N/A"
            
            amt_match = amount_pattern.search(sib_text)
            amount = amt_match.group(0) if amt_match else "N/A"
            
            # Se asume que el nombre de la empresa es el texto antes de la primera fecha
            company = sib_text.split(ex_date)[0].strip()
            if company:
                data.append({
                    "Company": company,
                    "Ex-Date": ex_date,
                    "Pay Date": pay_date,
                    "Div.%": div_percent,
                    "Amount": amount
                })
    return data

# --- 4. Extraer dividendos de los enlaces interactivos ---
all_dividends = []

for link in interactive_links:
    href = link.get("href")
    full_url = href if href.startswith("http") else "https://divvydiary.com" + href
    print("Abriendo enlace interactivo:", full_url)
    driver.get(full_url)
    time.sleep(5)  # Espera a que se cargue la página interactiva
    page_html = driver.page_source
    soup_page = BeautifulSoup(page_html, "html.parser")
    
    dividends = extraer_dividendos(soup_page)
    print(f"  Dividendos extraídos: {len(dividends)}")
    all_dividends.extend(dividends)

driver.quit()

# --- 5. Guardar los datos en un CSV ---
df = pd.DataFrame(all_dividends, columns=["Company", "Ex-Date", "Pay Date", "Div.%", "Amount"])
df.to_csv("dividends_full_calendar.csv", index=False)
print("Datos guardados en 'dividends_full_calendar.csv'")
