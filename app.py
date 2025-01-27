import os
import shutil
from pdf2image import convert_from_path
import pytesseract
from PyPDF2 import PdfReader, PdfWriter

# Ruta al ejecutable de Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Configura las rutas principales
carpeta_principal = r"C:\Users\dafep\Documents\prueba facturación\24 DE ENERO"
ruta_documentos = os.path.join(carpeta_principal, "ESPECIALIZADA", "documentos.pdf")
carpeta_especializada = os.path.join(carpeta_principal, "ESPECIALIZADA")
carpeta_no_identificados = r"C:\Users\dafep\Documents\prueba facturación\24 DE ENERO\ESPECIALIZADA\Sin identificar"

# Crea carpeta para no identificados si no existe
if not os.path.exists(carpeta_no_identificados):
    os.makedirs(carpeta_no_identificados)

# Crea carpetas temporales para manejar archivos
carpeta_temp = "temp_pages"
if not os.path.exists(carpeta_temp):
    os.makedirs(carpeta_temp)


def buscar_identificacion(texto):
    """Busca el número de identificación en el texto, probando CC, RC y TI."""
    identificadores = ["Identificación: CC", "Identificación: RC", "Identificación: TI", ": CC", "Número de documento"]
    for iden in identificadores:
        if iden in texto:
            try:
                return texto.split(f"{iden} ")[1].split()[0], iden
            except IndexError:
                continue  # Si el formato no es válido, pasa al siguiente identificador
    return None, None  # Si no se encuentra ningún identificador



# Divide el PDF en páginas individuales
def dividir_pdf(ruta_pdf, carpeta_destino):
    # Lee el archivo PDF
    pdf = PdfReader(ruta_pdf)
    
    # Divide cada página en un archivo PDF separado
    for i, pagina in enumerate(pdf.pages):
        escritor = PdfWriter()
        escritor.add_page(pagina)
        
        # Define la ruta del archivo PDF individual
        ruta_salida = os.path.join(carpeta_destino, f"pagina_{i + 1}.pdf")
        
        # Escribe el archivo PDF individual
        with open(ruta_salida, "wb") as salida_pdf:
            escritor.write(salida_pdf)

# Extrae texto de un archivo PDF escaneado
def extraer_texto(pdf_path):
    # Convierte la página PDF en una imagen
    images = convert_from_path(pdf_path, dpi=300, poppler_path=r'poppler-24.08.0\Library\bin')
    texto_completo = ""
    for image in images:
        texto_completo += pytesseract.image_to_string(image, lang="spa")
    return texto_completo

# Procesa cada página del PDF
def procesar_documentos():
    dividir_pdf(ruta_documentos, carpeta_temp)
    documentos = os.listdir(carpeta_temp)
    facturas = {}
    no_identificados = []  # Archivos no relacionados con facturas o pacientes

    for documento in documentos:
        ruta_doc = os.path.join(carpeta_temp, documento)
        texto = extraer_texto(ruta_doc)
        asociado = False
        
        try:
            # Buscar facturas electrónicas
            if "FACTURA ELECTRÓNICA DE VENTA N" in texto:
                if "Factura Electrónica de venta:" in texto:
                    try:
                        codigo_factura = texto.split("Factura Electrónica de venta:")[1].split()[0]
                    except IndexError:
                        #print(f"Error: No se pudo extraer el código de factura en el archivo {ruta_doc}. Verifica el formato.")
                        continue
                elif "Factura Electrónica de venta;" in texto:
                    codigo_factura = texto.split("Factura Electrónica de venta;")[1].split()[0]
                else:
                    print(f"Error: El texto no contiene 'Factura Electrónica de venta:' en el archivo {ruta_doc}")
                    print(f"Contenido del texto para {ruta_doc}:\n{texto}")
                    continue

                print(ruta_doc)
                print(codigo_factura)
                identificacion, tipo_identificacion = buscar_identificacion(texto)
                if identificacion is None:
                    print(f"Error: No se encontró identificación en el archivo {ruta_doc}")
                    continue  # Salta al siguiente documento
                print(identificacion)
                # Registra la factura encontrada
                facturas[codigo_factura] = {"identificacion": identificacion, "archivos": [ruta_doc]}
                asociado = True
            else:
                # Buscar documentos asociados a un paciente
                for codigo, datos in facturas.items():
                    if datos["identificacion"] in texto:
                        datos["archivos"].append(ruta_doc)
                        asociado = True
                        break
        except Exception as e:
            print(f"Error procesando el archivo {ruta_doc}: {e}")
        
        # Si no se pudo asociar el documento, añadirlo a la lista de no identificados
        if not asociado:
            no_identificados.append(ruta_doc)
            #print(ruta_doc)
            #print(f"Contenido del texto para {ruta_doc}:\n{texto}")
    
    return facturas, no_identificados

# Mover los archivos a las carpetas correspondientes
def organizar_archivos(facturas, no_identificados):
    # Organizar facturas
    for codigo, datos in facturas.items():
        identificacion = datos["identificacion"]
        archivos = datos["archivos"]
        
        # Buscar carpeta de EPS correspondiente
        for eps_carpeta in os.listdir(carpeta_especializada):
            ruta_eps = os.path.join(carpeta_especializada, eps_carpeta)
            if os.path.isdir(ruta_eps):
                # Busca carpeta que contenga el código de la factura
                carpeta_factura = next(
                    (carpeta for carpeta in os.listdir(ruta_eps) if codigo in carpeta),
                    None
                )
                if carpeta_factura:
                    ruta_factura = os.path.join(ruta_eps, carpeta_factura)
                    if not os.path.exists(ruta_factura):
                        os.makedirs(ruta_factura)
                    
                    # Mover los archivos a la carpeta
                    for archivo in archivos:
                        shutil.move(archivo, os.path.join(ruta_factura, os.path.basename(archivo)))
                    
                    # Crear archivo .txt con la identificación del cliente
                    ruta_txt = os.path.join(ruta_factura, f"{identificacion}.txt")
                    with open(ruta_txt, "w") as txt_file:
                        txt_file.write(f"Número de identificación: {identificacion}")
    
    # Mover archivos no identificados
    for archivo in no_identificados:
        shutil.move(archivo, os.path.join(carpeta_no_identificados, os.path.basename(archivo)))

# Ejecutar el flujo
dividir_pdf(ruta_documentos, carpeta_temp)
facturas_procesadas, no_identificados = procesar_documentos()
#print(facturas_procesadas)
#print(no_identificados)
organizar_archivos(facturas_procesadas, no_identificados)

# Limpieza
shutil.rmtree(carpeta_temp)
print("Organización completada.")
