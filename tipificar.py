import os
import json
from pdf2image import convert_from_path
import pytesseract
from PyPDF2 import PdfReader, PdfWriter


from config import NIT_HOSPITAL
# Ruta al ejecutable de Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Configura la ruta de Poppler
poppler_path = r'Recursos\poppler-24.08.0\\Library\\bin'

# Cargar reglas desde un archivo JSON
def load_eps_rules(json_file):
    try:
        with open(json_file, 'r', encoding='utf-8') as file:
            eps_rules = json.load(file)
        return eps_rules
    except Exception as e:
        print(f"Error al cargar el archivo de reglas: {e}")
        return {}

# Ruta del archivo JSON con las reglas
EPS_RULES_FILE = "reglas.json"

# Cargar las reglas al inicio
EPS_RULES = load_eps_rules(EPS_RULES_FILE)

# Extraer texto de un PDF escaneado usando OCR
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        images = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)
        for image in images:
            text += pytesseract.image_to_string(image, lang="spa") + "\n"
    except Exception as e:
        print(f"Error al procesar {pdf_path}: {e}")
    return text.strip()

# Identificar tipo de documento
def identify_document_type(text, eps_rules):
    for doc_type, keywords in eps_rules.get("keywords", {}).items():
        if any(keyword in text for keyword in keywords):
            print(f"Identificado como '{doc_type}' basado en palabras clave en el texto.")
            return doc_type
    print("No se identificó tipo de documento.")
    return None

# Extraer código de factura
def extract_invoice_code(text):
    for key in ["Factura Electrónica de venta:", "Factura Electrónica de venta;"]:
        if key in text:
            try:
                return text.split(key)[1].split()[0]
            except IndexError:
                pass
    return None

# Procesar una carpeta de factura
def process_invoice_folder(folder_path, eps_name):
    eps_rules = EPS_RULES.get(eps_name)
    if not eps_rules:
        print(f"EPS no reconocida: {eps_name}")
        return
    
    docs_by_type = {}
    codigo_factura = None
    respaldo_folder = os.path.join(folder_path, "respaldo")
    os.makedirs(respaldo_folder, exist_ok=True)
    
    for file in os.listdir(folder_path):
        if file.endswith(".pdf"):
            print(f"Procesando archivo: {file}")
            pdf_path = os.path.join(folder_path, file)
            text = extract_text_from_pdf(pdf_path)
            #print(f"Texto extraído de {file}:\n{text[:500]}")
            doc_type = identify_document_type(text, eps_rules)
            
            if doc_type:
                docs_by_type.setdefault(doc_type, []).append(pdf_path)
                #print(f"Archivo: {file} - Tipo identificado: {doc_type}")
            
            if not codigo_factura:
                codigo_factura = extract_invoice_code(text)
    
    if not codigo_factura:
        print(f"No se encontró código de factura en {folder_path}")
        return
    
    archivos_utilizados = set()
    # Generar PDFs combinados
    for combo in eps_rules.get("combinations", []):
        output_pdf_name = combo["name"].replace("{codigo_factura}", codigo_factura)
        output_pdf_name = output_pdf_name.replace("{NIT_hospital}", NIT_HOSPITAL)
        output_path = os.path.join(folder_path, output_pdf_name)

        print(f"Generando PDF: {output_pdf_name} con documentos: {combo['documents']}")

        writer = PdfWriter()
        for doc_type in combo["documents"]:
            for pdf in docs_by_type.get(doc_type, []):
                archivos_utilizados.add(pdf)
                reader = PdfReader(pdf)
                for page in reader.pages:
                    writer.add_page(page)
        
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        print(f"Generado: {output_pdf_name}")

    # Mover archivos utilizados a la carpeta de respaldo
    for file_path in archivos_utilizados:
        file_name = os.path.basename(file_path)
        new_path = os.path.join(respaldo_folder, file_name)
        os.rename(file_path, new_path)
        print(f"Movido a respaldo: {file_name}")

# Recorrer estructura de carpetas
def process_main_folder(main_folder):
    for service in os.listdir(main_folder):
        service_path = os.path.join(main_folder, service)
        if os.path.isdir(service_path):
            for eps in os.listdir(service_path):
                eps_path = os.path.join(service_path, eps)
                if os.path.isdir(eps_path):
                    for invoice in os.listdir(eps_path):
                        invoice_path = os.path.join(eps_path, invoice)
                        if os.path.isdir(invoice_path):
                            print("#################################################" + invoice_path)
                            process_invoice_folder(invoice_path, eps)

# Ejecutar proceso
MAIN_FOLDER = r"C:\Users\dafep\Documents\prueba facturación\24 DE ENERO"
process_main_folder(MAIN_FOLDER)


# Carpeta específica que quieres analizar
#TEST_FOLDER = r"C:\Users\dafep\Documents\prueba facturación\24 DE ENERO\ESPECIALIZADA\NUEVA EPS\FEH484580"

# Nombre de la EPS correspondiente a esa carpeta
#EPS_NAME = "NUEVA EPS"

# Procesar solo esa carpeta
#process_invoice_folder(TEST_FOLDER, EPS_NAME)
