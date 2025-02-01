import os
import shutil
from pdf2image import convert_from_path
import pytesseract
from PyPDF2 import PdfReader, PdfWriter
import re

from dotenv import load_dotenv

#Leer variables de entorno
load_dotenv()


# Configura las rutas principales

# Obtener el valor de la variable de entorno
carpeta_principal = os.getenv("MAIN_FOLDER")
carpeta_temp = "temp_pages"


# Ruta al ejecutable de Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Configura la ruta de Poppler
poppler_path = r'Recursos\poppler-24.08.0\\Library\\bin'

def buscar_identificacion(texto):
    """Busca el número de identificación en el texto, probando CC, RC y TI."""
    identificadores = ["Identificación: CC", "Identificación: RC", "Identificacion RC", "Identificación: TI", 
                       'Identificacion CC']
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
    archivos_usuario = {}
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

                if identificacion not in archivos_usuario:
                    archivos_usuario[identificacion] = []
                
                facturas[codigo_factura] = {"identificacion": identificacion, "archivos": [ruta_doc]}
                asociado = True
            else:
                # Verifica si el archivo contiene alguna identificación ya detectada
                for identificacion in archivos_usuario.keys():
                    if identificacion in texto:
                        archivos_usuario[identificacion].append(ruta_doc)
                        asociado = True
                        break  # Si encuentra una coincidencia, no sigue buscando
        except Exception as e:
            print(f"Error procesando el archivo {ruta_doc}: {e}")

        if not asociado:
            print(f"Archivo no identificado: {ruta_doc}")
            print(f"\n{texto}")
            no_identificados.append(ruta_doc)

    return facturas, archivos_usuario, no_identificados


def organizar_archivos(facturas, archivos_usuario, no_identificados, carpeta_area, carpeta_no_identificados):
    usuario_facturas = {}
    for codigo, datos in facturas.items():
        usuario_facturas.setdefault(datos["identificacion"], []).append(codigo)

    for codigo, datos in facturas.items():
        identificacion = datos["identificacion"]
        archivos_factura = datos["archivos"]
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
                    os.makedirs(ruta_factura, exist_ok=True)
                    
                    for archivo in archivos_factura:
                        shutil.move(archivo, os.path.join(ruta_factura, os.path.basename(archivo)))
                    
                    ruta_txt = os.path.join(ruta_factura, f"{identificacion}.txt")
                    with open(ruta_txt, "w") as txt_file:
                        txt_file.write(f"Número de identificación: {identificacion}")
                    break  

        if not carpeta_factura_encontrada:
            ruta_factura_no_identificada = os.path.join(carpeta_no_identificados, f"Factura_{codigo}")
            os.makedirs(ruta_factura_no_identificada, exist_ok=True)
            for archivo in archivos_factura:
                shutil.move(archivo, os.path.join(ruta_factura_no_identificada, os.path.basename(archivo)))
            ruta_txt = os.path.join(ruta_factura_no_identificada, f"{identificacion}.txt")
            with open(ruta_txt, "w") as txt_file:
                txt_file.write(f"Número de identificación: {identificacion}")

    for identificacion, archivos in archivos_usuario.items():
        if identificacion in usuario_facturas:
            for codigo_factura in usuario_facturas[identificacion]:
                for eps_carpeta in os.listdir(carpeta_area):
                    ruta_eps = os.path.join(carpeta_area, eps_carpeta)
                    if os.path.isdir(ruta_eps):
                        carpeta_factura = next(
                            (carpeta for carpeta in os.listdir(ruta_eps) if codigo_factura in carpeta),
                            None
                        )
                        if carpeta_factura:
                            ruta_factura = os.path.join(ruta_eps, carpeta_factura)
                            os.makedirs(ruta_factura, exist_ok=True)
                            for archivo in archivos:
                                shutil.copy(archivo, os.path.join(ruta_factura, os.path.basename(archivo)))
    
    for archivo in no_identificados:
        shutil.move(archivo, os.path.join(carpeta_no_identificados, os.path.basename(archivo)))


# Ejecutar el flujo para todas las áreas
areas = [area for area in os.listdir(carpeta_principal) if os.path.isdir(os.path.join(carpeta_principal, area))]

for area in areas:
    carpeta_area = os.path.join(carpeta_principal, area)
    carpeta_no_identificados = os.path.join(carpeta_area, "Sin identificar")

    if not os.path.exists(carpeta_no_identificados):
        os.makedirs(carpeta_no_identificados)

    if not os.path.exists(carpeta_temp):
        os.makedirs(carpeta_temp)

    ruta_documentos = os.path.join(carpeta_area, "documentos.pdf")

    if os.path.exists(ruta_documentos):
        facturas_procesadas, archivos_usuario, no_identificados = procesar_documentos(ruta_documentos, carpeta_temp)
        organizar_archivos(facturas_procesadas, archivos_usuario, no_identificados, carpeta_area, carpeta_no_identificados)
        
        shutil.rmtree(carpeta_temp)

print("Organización completada para todas las áreas.")
