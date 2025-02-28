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

# --- 1. Generar las URLs de cada mes ---
base_url = "https://divvydiary.com/en/calendar/2025-"
months = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december"
]
month_urls = {month: base_url + month for month in months}

# --- 2. Función para extraer dividendos de una página "Show all" ---
def extraer_dividendos_showall(soup):
    rows = soup.find_all("tr", class_=re.compile("group"))
    data = []
    for row in rows:
        tds = row.find_all("td")
        if len(tds) >= 5:
            company_tag = tds[0].find("a", class_=re.compile("truncate"))
            company = company_tag.get_text(strip=True) if company_tag else tds[0].get_text(" ", strip=True)
            ex_date = tds[1].get_text(strip=True)
            pay_date = tds[2].get_text(strip=True)
            div_percent = tds[3].get_text(strip=True)
            amount = tds[4].get_text(strip=True)
            data.append({
                "Company": company,
                "Ex-Date": ex_date,
                "Pay Date": pay_date,
                "Div.%": div_percent,
                "Amount": amount
            })
    return data

# --- 3. Extraer dividendos de todos los meses ---
data_by_month = {}

for month, month_url in month_urls.items():
    print(f"\n📅 Procesando mes: {month.capitalize()} ({month_url})")
    driver.get(month_url)
    time.sleep(8)  # Espera a que se carguen los datos dinámicos
    main_html = driver.page_source
    soup_main = BeautifulSoup(main_html, "html.parser")

    # --- Buscar los enlaces interactivos ("Show all ... dividends") ---
    interactive_links = []
    for a in soup_main.find_all("a"):
        text = a.get_text(" ", strip=True)
        if "Show all" in text and "dividends on" in text:
            interactive_links.append(a)

    print(f"  🔍 Se encontraron {len(interactive_links)} enlaces interactivos.")

    # --- Extraer dividendos de la página principal del mes ---
    dividends = extraer_dividendos_showall(soup_main)
    print(f"  ✅ Dividendos extraídos en la página principal: {len(dividends)}")
    
    # --- Extraer dividendos de cada página interactiva ---
    for link in interactive_links:
        href = link.get("href")
        full_url = href if href.startswith("http") else "https://divvydiary.com" + href
        print(f"  🔗 Abriendo enlace interactivo: {full_url}")
        driver.get(full_url)
        time.sleep(5)
        page_html = driver.page_source
        soup_page = BeautifulSoup(page_html, "html.parser")
        interactive_dividends = extraer_dividendos_showall(soup_page)
        print(f"    ➕ Dividendos extraídos de esta página: {len(interactive_dividends)}")
        dividends.extend(interactive_dividends)

    # Crear DataFrame para el mes y ordenar por Ex-Date
    df = pd.DataFrame(dividends, columns=["Company", "Ex-Date", "Pay Date", "Div.%", "Amount"])
    
    if not df.empty:
        df["Ex-Date"] = pd.to_datetime(df["Ex-Date"], format="%d/%m/%Y", errors="coerce")
        df = df.sort_values(by="Ex-Date")
        df["Ex-Date"] = df["Ex-Date"].dt.strftime("%d/%m/%Y")  # Formatear nuevamente la fecha
        data_by_month[month.capitalize()] = df  # Guardar DataFrame por mes

driver.quit()

# --- 4. Guardar en un solo archivo Excel con una hoja por cada mes ---
if data_by_month:
    with pd.ExcelWriter("dividends_2025.xlsx", engine="openpyxl") as writer:
        for month, df in data_by_month.items():
            df.to_excel(writer, sheet_name=month, index=False)
    print("\n✅ Todos los datos han sido guardados en 'dividends_2025.xlsx' con una hoja por cada mes.")
else:
    print("\n❌ No se encontraron datos para guardar.")
