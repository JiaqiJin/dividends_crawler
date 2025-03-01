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
    "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"
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
            company_link = company_tag["href"] if company_tag else None  # Guardamos el enlace de la empresa
            data.append({
                "Company": company,
                "Ex-Date": ex_date,
                "Pay Date": pay_date,
                "Div.%": div_percent,
                "Amount": amount,
                "Company Link": company_link  # Añadimos el enlace de la empresa
            })
    return data

# --- 3. Función para extraer los detalles del ISIN y símbolo de la empresa ---
def extraer_detalles_empresa(soup):
    # Extraer ISIN y símbolo de la empresa
    isin = None
    symbol = None
    company_details_div = soup.find("div", class_="mr-2 mt-1 flex flex-wrap items-center gap-x-2 text-sm font-light text-gray-500 dark:text-gray-300")
    if company_details_div:
        buttons = company_details_div.find_all("button")
        if len(buttons) >= 2:
            isin = buttons[0].get_text(strip=True)  # El primer botón tiene el ISIN
            symbol = buttons[1].get_text(strip=True)  # El segundo botón tiene el símbolo
    return isin, symbol

# --- 4. Extraer dividendos de todos los meses ---
data_by_month = []

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

        # --- Ahora, interactuamos con cada empresa que tiene su enlace ---
        for div in interactive_dividends:
            company_link = div.get("Company Link")
            if company_link:
                full_company_url = company_link if company_link.startswith("http") else "https://divvydiary.com" + company_link
                print(f"    ➡️ Abriendo página de la empresa: {full_company_url}")
                driver.get(full_company_url)
                time.sleep(5)  # Espera a que cargue la página de la empresa
                company_html = driver.page_source
                soup_company = BeautifulSoup(company_html, "html.parser")
                
                # Extraer detalles de la empresa (ISIN y símbolo)
                isin, symbol = extraer_detalles_empresa(soup_company)
                print(f"    📌 ISIN: {isin}, Symbol: {symbol}, Company: {div['Company']}")
                
                # Mostrar el nombre de la empresa, ISIN y símbolo
                print(f"    🚀 Empresa: {div['Company']}, ISIN: {isin}, Símbolo: {symbol}")

                # Guardar los datos adicionales (ISIN y símbolo) en el DataFrame
                for dividend in interactive_dividends:
                    dividend["ISIN"] = isin
                    dividend["Symbol"] = symbol

    # Crear DataFrame para el mes y ordenar por Ex-Date
    df = pd.DataFrame(dividends, columns=["Company", "Ex-Date", "Pay Date", "Div.%", "Amount", "ISIN", "Symbol"])
    
    if not df.empty:
        df["Ex-Date"] = pd.to_datetime(df["Ex-Date"], format="%d/%m/%Y", errors="coerce")
        df = df.sort_values(by="Ex-Date")
        df["Ex-Date"] = df["Ex-Date"].dt.strftime("%d/%m/%Y")  # Formatear nuevamente la fecha
        data_by_month.append(df)  # Guardar DataFrame por mes

driver.quit()

# --- 5. Guardar en un solo archivo Excel con una hoja por cada mes ---
if data_by_month:
    with pd.ExcelWriter("dividends_2025.xlsx", engine="openpyxl") as writer:
        for idx, df in enumerate(data_by_month):
            sheet_name = f"Month_{idx+1}"  # Usar nombre dinámico para la hoja
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    print("\n✅ Todos los datos han sido guardados en 'dividends_2025.xlsx' con una hoja por cada mes.")
else:
    print("\n❌ No se encontraron datos para guardar.")
