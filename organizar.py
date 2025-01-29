import os
import shutil
from pdf2image import convert_from_path
import pytesseract
from PyPDF2 import PdfReader, PdfWriter

# Ruta al ejecutable de Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Configura la ruta de Poppler
poppler_path = r'poppler-24.08.0\\Library\\bin'


def buscar_identificacion(texto):
    """Busca el número de identificación en el texto, probando CC, RC y TI."""
    identificadores = ["Identificación: CC", "Identificación: RC", "Identificación: TI", 
                       'Identificacion CC', ": CC", "Número de documento", 'IDENTIDAD:']
    for iden in identificadores:
        if iden in texto:
            try:
                return texto.split(f"{iden} ")[1].split()[0], iden
            except IndexError:
                continue  
    return None, None  


def dividir_pdf(ruta_pdf, carpeta_destino):
    """Divide un PDF en páginas individuales."""
    pdf = PdfReader(ruta_pdf)
    for i, pagina in enumerate(pdf.pages):
        escritor = PdfWriter()
        escritor.add_page(pagina)
        ruta_salida = os.path.join(carpeta_destino, f"pagina_{i + 1}.pdf")
        with open(ruta_salida, "wb") as salida_pdf:
            escritor.write(salida_pdf)


def extraer_texto(pdf_path):
    """Extrae texto de un archivo PDF escaneado usando OCR."""
    images = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)
    texto_completo = ""
    for image in images:
        texto_completo += pytesseract.image_to_string(image, lang="spa")
    return texto_completo


def procesar_documentos(ruta_documentos, carpeta_temp):
    """Procesa cada página del PDF y extrae facturas e identificaciones."""
    dividir_pdf(ruta_documentos, carpeta_temp)
    documentos = os.listdir(carpeta_temp)
    facturas = {}
    no_identificados = []

    for documento in documentos:
        ruta_doc = os.path.join(carpeta_temp, documento)
        texto = extraer_texto(ruta_doc)
        asociado = False

        try:
            if "FACTURA ELECTRÓNICA DE VENTA N" in texto:
                codigo_factura = None
                for clave in ["Factura Electrónica de venta:", "Factura Electrónica de venta;"]:
                    if clave in texto:
                        codigo_factura = texto.split(clave)[1].split()[0]
                        break

                if not codigo_factura:
                    continue  

                identificacion, _ = buscar_identificacion(texto)
                if identificacion is None:
                    continue  

                facturas[codigo_factura] = {"identificacion": identificacion, "archivos": [ruta_doc]}
                asociado = True
            else:
                for codigo, datos in facturas.items():
                    if datos["identificacion"] in texto:
                        datos["archivos"].append(ruta_doc)
                        asociado = True
                        break
        except Exception as e:
            print(f"Error procesando el archivo {ruta_doc}: {e}")

        if not asociado:
            no_identificados.append(ruta_doc)

    return facturas, no_identificados


def organizar_archivos(facturas, no_identificados, carpeta_area, carpeta_no_identificados):
    """Organiza los archivos de facturas en las carpetas correspondientes."""
    for codigo, datos in facturas.items():
        identificacion = datos["identificacion"]
        archivos = datos["archivos"]
        carpeta_factura_encontrada = False  

        for eps_carpeta in os.listdir(carpeta_area):
            ruta_eps = os.path.join(carpeta_area, eps_carpeta)
            if os.path.isdir(ruta_eps):
                carpeta_factura = next(
                    (carpeta for carpeta in os.listdir(ruta_eps) if codigo in carpeta),
                    None
                )
                if carpeta_factura:
                    carpeta_factura_encontrada = True
                    ruta_factura = os.path.join(ruta_eps, carpeta_factura)
                    if not os.path.exists(ruta_factura):
                        os.makedirs(ruta_factura)

                    for archivo in archivos:
                        shutil.move(archivo, os.path.join(ruta_factura, os.path.basename(archivo)))

                    ruta_txt = os.path.join(ruta_factura, f"{identificacion}.txt")
                    with open(ruta_txt, "w") as txt_file:
                        txt_file.write(f"Número de identificación: {identificacion}")
                    break  

        if not carpeta_factura_encontrada:
            ruta_factura_no_identificada = os.path.join(carpeta_no_identificados, f"Factura_{codigo}")
            if not os.path.exists(ruta_factura_no_identificada):
                os.makedirs(ruta_factura_no_identificada)

            for archivo in archivos:
                shutil.move(archivo, os.path.join(ruta_factura_no_identificada, os.path.basename(archivo)))

            ruta_txt = os.path.join(ruta_factura_no_identificada, f"{identificacion}.txt")
            with open(ruta_txt, "w") as txt_file:
                txt_file.write(f"Número de identificación: {identificacion}")

    for archivo in no_identificados:
        shutil.move(archivo, os.path.join(carpeta_no_identificados, os.path.basename(archivo)))
