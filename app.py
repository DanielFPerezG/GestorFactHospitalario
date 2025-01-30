import os
import shutil
from organizar import dividir_pdf, procesar_documentos, organizar_archivos

# Configura las rutas principales
carpeta_principal = r"C:\Users\dafep\Documents\prueba facturación\24 DE ENERO"
carpeta_temp = "temp_pages"

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



