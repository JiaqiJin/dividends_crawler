import pandas as pd
from yahooquery import search

class DividendParser:
    def __init__(self, file_path):
        """
        Inicializa el parser con el archivo XLSX.
        :param file_path: Ruta del archivo XLSX.
        """
        self.file_path = file_path
        self.df = None  # DataFrame para almacenar la última hoja

    def load_last_sheet(self):
        """
        Carga solo la última hoja del archivo XLSX.
        """
        xls = pd.ExcelFile(self.file_path)
        last_sheet_name = xls.sheet_names[-1]  # Obtiene el nombre de la última hoja
        self.df = pd.read_excel(xls, sheet_name=last_sheet_name)
        print(f"✅ Última hoja cargada: {last_sheet_name}")

    def search_ticker(self, company_name):
        """
        Busca el ticker en Yahoo Finance si faltan ISIN o Symbol.
        :param company_name: Nombre de la empresa.
        :return: Symbol si se encuentra, sino None.
        """
        try:
            results = search(company_name)
            if "quotes" in results and results["quotes"]:
                for quote in results["quotes"]:
                    symbol = quote.get("symbol", "N/A")
                    print(f"🔍 Ticker encontrado: {symbol}")  # Imprimir solo el ticker
                    return symbol
        except Exception as e:
            print(f"⚠️ Error buscando {company_name}: {e}")
        return None

    def extract_data(self):
        """
        Extrae y limpia los datos de la última hoja, completando ISIN o Symbol si están vacíos.
        :return: DataFrame con los datos procesados.
        """
        if self.df is None or self.df.empty:
            print("⚠️ No hay datos en la última hoja.")
            return pd.DataFrame()

        # Completamos ISIN o Symbol si están vacíos
        for index, row in self.df.iterrows():
            if pd.isna(row.get("ISIN")) or pd.isna(row.get("Symbol")):  # Si ISIN o Symbol están vacíos
                ticker = self.search_ticker(row["Company"])
                if ticker:
                    self.df.at[index, "Symbol"] = ticker
                    self.df.at[index, "ISIN"] = ticker  # Eliminar "Ticker-based: " y solo guardar el ticker

        # Eliminar filas duplicadas basadas en los campos claves
        self.df = self.df.drop_duplicates(subset=["Company", "Ex-Date", "Pay Date", "Div.%", "Amount", "ISIN", "Symbol"])

        return self.df[['Company', 'Ex-Date', 'Pay Date', 'Div.%', 'Amount', 'ISIN', 'Symbol']]

    def save_to_csv(self, output_file):
        """
        Guarda los datos extraídos en un archivo CSV.
        :param output_file: Nombre del archivo CSV de salida.
        """
        extracted_data = self.extract_data()
        if not extracted_data.empty:
            extracted_data.to_csv(output_file, index=False)
            print(f"✅ Datos guardados en {output_file}")
        else:
            print("⚠️ No se encontraron datos para guardar.")

# ----------------------------
# 📌 Ejemplo de uso:
# ----------------------------

if __name__ == "__main__":
    parser = DividendParser("dividendos.xlsx")  # Reemplaza con tu archivo real
    parser.load_last_sheet()
    data = parser.extract_data()
    print(data.head())  # Muestra los primeros registros
    parser.save_to_csv("dividendos_ultimo_mes.csv")
