import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Clase para representar a cada empresa
class Company:
    def __init__(self, name, ex_date, pay_date, dividend_percentage, amount, company_link=None, isin=None, ticket=None):
        self.name = name
        self.ex_date = ex_date
        self.pay_date = pay_date
        self.dividend_percentage = dividend_percentage
        self.amount = amount
        self.company_link = company_link
        self.isin = isin
        self.ticket = ticket

    def to_dict(self):
        """Convierte el objeto a un diccionario para fácil exportación a CSV"""
        return {
            "Security": self.name,
            "Ex-Date": self.ex_date,
            "Pay Date": self.pay_date,
            "Div.%": self.dividend_percentage,
            "Amount": self.amount,
            "Company Link": self.company_link,
            "ISIN": self.isin,
            "Ticket": self.ticket
        }

# Configuración de Selenium en modo headless
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Espera explícita
def wait_for_element(xpath, timeout=20):
    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
    except TimeoutException:
        print("Timeout: Element not found.")
        return None

# Función para extraer los detalles de la empresa
def extract_company_details(company_link):
    driver.get(company_link)
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Extraer ISIN (primer botón)
    isin_button = soup.find("button", class_="flex items-center rounded hover:shadow focus:shadow focus:outline-none focus-visible:ring focus-visible:ring-orange-400")
    isin = isin_button.find("span") if isin_button else None
    isin = isin.get_text(strip=True) if isin else 'N/A'

    # Extraer el ticket (segundo botón)
    ticket_buttons = soup.find_all("button", class_="flex items-center rounded hover:shadow focus:shadow focus:outline-none focus-visible:ring focus-visible:ring-orange-400")
    ticket = ticket_buttons[1].find("span") if len(ticket_buttons) > 1 else None
    ticket = ticket.get_text(strip=True) if ticket else 'N/A'

    # Print the company name found when opening the link
    #print(f"Company found: {company_link}")

    return isin, ticket

# Lista de meses para iterar
months = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december"
]

# Lista para almacenar los objetos de las empresas
companies = []

# Iterar sobre cada mes
for month in months:
    for day in range(1, 32):
        # Construir la URL para cada día
        day_str = str(day).zfill(2)  # Asegurarse de que el día tenga dos dígitos
        url = f"https://divvydiary.com/en/calendar/2025-{month}-{day_str}"

        # Intentar acceder al enlace
        print(f"Attempting to open: {url}")

        driver.get(url)

        # Esperar a que la página cargue y verificar si la tabla está presente
        table = wait_for_element("//table[@id='calendar']")

        if table:
            # Obtener el HTML de la página
            page_source = driver.page_source
            soup_show_all = BeautifulSoup(page_source, 'html.parser')

            # Buscar la tabla y extraer los datos
            rows = soup_show_all.find_all("tr")  # Usar BeautifulSoup para analizar el HTML

            for row in rows:
                cols = row.find_all("td")
                if len(cols) > 0:
                    # Extraer los valores de cada columna
                    security = cols[0].get_text(strip=True)
                    ex_date = cols[1].get_text(strip=True) if len(cols) > 1 else ''
                    pay_date = cols[2].get_text(strip=True) if len(cols) > 2 else ''
                    div_percentage = cols[3].get_text(strip=True) if len(cols) > 3 else ''
                    amount = cols[4].get_text(strip=True) if len(cols) > 4 else ''

                    # Obtener el enlace de la empresa
                    company_link_tag = cols[0].find('a', href=True)
                    company_link = f"https://divvydiary.com{company_link_tag['href']}" if company_link_tag else None

                    # Extraer ISIN y ticket
                    if company_link:
                        isin, ticket = extract_company_details(company_link)

                    # Crear un objeto de la clase Company
                    company = Company(security, ex_date, pay_date, div_percentage, amount, company_link, isin, ticket)
                    companies.append(company)
        else:
            print(f"No data found for {month.capitalize()} {day_str}, skipping...")

        # Esperar un tiempo para no hacer demasiadas solicitudes rápidas
        time.sleep(2)

# Escribir los datos en un archivo CSV
with open('companies_data_with_isin_and_ticket.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=["Security", "Ex-Date", "Pay Date", "Div.%", "Amount", "Company Link", "ISIN", "Ticket"])
    writer.writeheader()  # Escribir el encabezado del CSV
    for company in companies:
        writer.writerow(company.to_dict())  # Escribir cada fila de datos

print("Datos guardados en 'companies_data_with_isin_and_ticket.csv'")

driver.quit()
