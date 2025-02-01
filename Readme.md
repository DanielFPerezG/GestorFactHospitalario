# 📌 Organizador y Tipificación de Archivos de Facturación Hospitalaria

## 📝 Descripción
Este proyecto automatiza la gestión de archivos de facturación hospitalaria. Se encarga de:

- Dividir los documentos escaneados en pdfs individuales y organizarlos en sus respectivas carpetas.
- Identificar facturas en archivos PDF y extraer información relevante.
- Agrupar documentos relacionados (facturas, autorizaciones, órdenes) en sus respectivas carpetas y renombrarlos según los requerimientos de la EPS.

## 🚀 Instalación y Configuración
### 1️⃣ Prerrequisitos
Antes de ejecutar el código, asegúrate de tener instalado:
- Python 3.8+
- Crear un entorno virtual e instalar las dependencias necesarias:
  ```bash
  python3 -m venv env

  pip install -r requirements.txt
  ```

### 2️⃣ Clonar el repositorio
```bash
git clone https://github.com/DanielFPerezG/GestorFactHospitalario.git
cd GestorFactHospitalario
```

### 3️⃣ Configurar Variables de Entorno
Crea un archivo `.env` en la raíz del proyecto y define el NIT del hospital:
```ini
NIT_HOSPITAL=123456789
```

## 📂 Estructura de archivos esperada
```
📁 FECHA DE FACTURACIÓN/
│-- 📂 SERVICIOS OFRECIDOS   # Cada carpeta es un servicio como "LABORATORIO, ESPECIALIZADA, PYM, ETC"
│-- |-- 📂 EPS/              # Una carpeta por cada EPS a la que se le prestó servicio.
│-- |-- |-- 📂 FACTURA/      # Una carpeta para cada factura vinculada a la EPS, donde se almacenarán los archivos correspondientes. Esta carpeta debe tener el código de la factura en el nombre.
│-- |-- 📄 documentos.pdf    # PDF con todos los archivos escaneados de dicho servicio.
```

## ⚙️ Funcionamiento
1. **Organizador**:
   - Divide los documentos escaneados del archivo "documentos.pdf" en un PDF por página.
   - Extrae el código de factura y el número de documento del paciente, agrupa los archivos relacionados por código de factura y documento.
   - Busca una carpeta cuyo título contenga el código de la factura y traslada los documentos relacionados a su interior.

2. **Tipificación**:
   - Identifica el tipo de documento de cada uno de los archivos de la carpeta facturada. Ejemplo: "Factura, Recibo, Autorización, Validador"
   - Dependiendo de los requerimientos de cada EPS, agrupa los archivos en diferentes PDF.
   - Crea una carpeta dentro de la carpeta de factura llamada "Respaldo", donde almacena los documentos agrupados.
   - Renombra documentos según las normativas de cada EPS.

## ▶️ Ejecución
Para procesar los archivos, ejecuta en la terminal:
```bash
.\env\Scripts\python organizar.py
.\env\Scripts\python tipificacion.py
```

## 📌 Recomendaciones
- Se recomienda ejecutar primero el archivo `organizador.py`.
- Si algún documento no es trasladado correctamente a su carpeta por temas de calidad de imagen u otros, este se trasladará a la carpeta `Sin identificar`, que se creará dentro de la carpeta principal.
- Si el organizador reconoce una factura y agrupa archivos por dicha factura, pero no existe una carpeta que contenga el nombre de la misma, se creará una carpeta con el nombre de la factura dentro de la carpeta `Sin identificar`.
- Una vez organizados los archivos no identificados, se recomienda cambiar el nombre de estos archivos por el tipo de documento que son. Si el organizador no logró identificarlos, `tipificacion.py` tampoco lo hará.
- Si el código no identifica el tipo de documento por su contenido, intentará hacerlo por el nombre del archivo. Por ello, debes renombrar los archivos en mayúsculas con el tipo de documento que representan. Ejemplo: `AUTORIZACION, FACTURA, VALIDADOR, RECIBO, HISTORIA, ORDEN, REPORTE IMAGENOLOGIA, REPORTE LABORATORIO`.

## 📌 Casos de uso

### Caso 1
**Escenario:** Ya tienes las carpetas creadas para cada una de las facturas dentro de sus correspondientes servicios y EPS. Tienes los documentos escaneados agrupados en un PDF llamado `documentos.pdf` dentro de cada servicio.

**Pasos:**
1. Corre `organizador.py`.
2. Verifica los archivos que no se pudieron organizar correctamente y muévelos a sus carpetas correspondientes.
3. Cambia el nombre de los archivos no identificados.
4. Corre `tipificacion.py`.

### Caso 2
**Escenario:** No has creado las carpetas de cada una de las facturas. 

**Pasos:**
1. Crea las carpetas de cada especialidad que facturaste cada día.
2. Escanea los documentos de cada especialidad en su correspondiente archivo "documentos.pdf" y agregalo en la carpeta de cada especialidad.
1. Corre `organizador.py`.
2. El organizador creará la carpeta `Sin identificar` dentro de cada una de las especialidades,dentro se crearan las carpetas de las facturas reconocidas.
3. Crea las carpetas de las EPS e ingresa sus correspondientes carpetas de factura antes de proceder a correr `tipificacion.py`.

## 📧 Contacto
Si tienes dudas o sugerencias, contáctame en danielperezgalindo@gmail.com.