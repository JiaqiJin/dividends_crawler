import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import pandas as pd

# Configuración de Selenium en modo headless
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
url = "https://divvydiary.com/en/calendar"
driver.get(url)
time.sleep(8)  # Espera para que se carguen los datos dinámicos

html = driver.page_source
driver.quit()

soup = BeautifulSoup(html, "html.parser")

# Expresión regular para detectar Amount con diferentes monedas y formatos
amount_pattern = re.compile(
    r"(CA\$|€|£|DKK|KWD|THB|NOK|₹|HK\$|R\$|\$)\s?\d{1,3}(?:[,.]?\d{1,3})*(?:\.\d{1,2})?"
)

# Detectar las fechas Ex-Date y Pay-Date en formato dd/mm/yyyy
date_pattern = re.compile(r"\d{2}/\d{2}/\d{4}")
percent_pattern = re.compile(r"\d+\.\d+%")  # Para Div.%

# Buscar todos los elementos que sean cabeceras de día
day_headers = []
for tag in soup.find_all(True):
    text = tag.get_text(strip=True)
    if re.match(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+\d{1,2}\s+\w+\s+\d{4}$", text):
        day_headers.append(tag)

print(f"Se encontraron {len(day_headers)} cabeceras de día.")

# Recorrer cada grupo (día) y extraer la información de dividendos
data = []
for header in day_headers:
    current_day = header.get_text(strip=True)
    siblings = header.find_next_siblings()
    for sib in siblings:
        sib_text = sib.get_text(" ", strip=True)
        if re.match(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+\d{1,2}\s+\w+\s+\d{4}$", sib_text):
            break

        # Buscar fechas en la fila (Ex-Date y Pay-Date)
        date_matches = date_pattern.findall(sib_text)
        div_percent_match = percent_pattern.search(sib_text)
        amount_match = amount_pattern.search(sib_text)

        if len(date_matches) >= 2:
            ex_date, pay_date = date_matches[:2]
            div_percent = div_percent_match.group(0) if div_percent_match else "N/A"
            amount = amount_match.group(0) if amount_match else "N/A"

            # Se asume que el nombre de la empresa es el texto antes del Ex-Date
            company = sib_text.split(ex_date)[0].strip()

            if company:
                data.append({
                    "Company": company,
                    "Ex-Date": ex_date,
                    "Pay Date": pay_date,
                    "Div.%": div_percent,
                    "Amount": amount
                })

# Crear DataFrame y ordenar por Ex-Date
df = pd.DataFrame(data, columns=["Company", "Ex-Date", "Pay Date", "Div.%", "Amount"])

# Guardar en CSV
df.to_csv("companies_dividends.csv", index=False)
print("Datos guardados en 'companies_dividends.csv'")
