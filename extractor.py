import re
import pdfplumber
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

pytesseract.pytesseract.tesseract_cmd = r'E:\Tesseract\tesseract.exe'
POPPLER_PATH = r'E:\poppler\Library\bin' 

def extraer_texto_archivo(ruta_archivo):
    extension = ruta_archivo.suffix.lower()
    texto = ""

    if extension == ".pdf":
        try:
            with pdfplumber.open(ruta_archivo) as pdf:
                for pagina in pdf.pages:
                    texto += (pagina.extract_text() or "") + "\n"
        except Exception:
            pass
        
        if not texto.strip():
            try:
                paginas_img = convert_from_path(ruta_archivo, poppler_path=POPPLER_PATH)
                for pag in paginas_img:
                    texto += pytesseract.image_to_string(pag, lang='spa') + "\n"
            except Exception as e:
                print(f"⚠️ Error al procesar PDF con OCR: {e}")

    elif extension in [".png", ".jpg", ".jpeg"]:
        img = Image.open(ruta_archivo)
        texto = pytesseract.image_to_string(img, lang='spa')

    return texto

def buscar_campos_clave(texto):
    """Extrae Fecha y Sucursal/Ubicación usando patrones afinados."""
    
    # Patrón de fecha en formato texto completo (ej: 13 DE JULIO DE 2022) o numérico (ej: 13/07/2022)
    patron_fecha_texto = r'\b(\d{1,2}\s+DE\s+[A-ZÁÉÍÓÚ]+\s+DE\s+\d{4})\b'
    patron_fecha_num = r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b'
    
    match_fecha = re.search(patron_fecha_texto, texto, re.IGNORECASE)
    if not match_fecha:
        match_fecha = re.search(patron_fecha_num, texto, re.IGNORECASE)

    # Patrón para sucursal, planta, municipio o unidad (ej: GRAL. ESCOBEDO, CAM BENITO JUAREZ, REGION 13)
    patron_sucursal = r'(?:sucursal|planta|sede|tienda|cam|gral\.)\s*:?\s*([a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s\.\,\-]+)'

    match_sucursal = re.search(patron_sucursal, texto, re.IGNORECASE)

    fecha_detectada = match_fecha.group(0).strip() if match_fecha else "NO DETECTADA"
    
    # Limpiamos el texto capturado para la sucursal (tomamos solo la primera línea)
    sucursal_detectada = "NO DETECTADA"
    if match_sucursal:
        linea_sucursal = match_sucursal.group(0).split('\n')[0].strip()
        sucursal_detectada = linea_sucursal

    return {
        "fecha": fecha_detectada,
        "sucursal": sucursal_detectada
    }

if __name__ == "__main__":
    from pathlib import Path
    
    archivo_prueba = Path("input_docs/Scan.pdf")
    if archivo_prueba.exists():
        texto = extraer_texto_archivo(archivo_prueba)
        resultados = buscar_campos_clave(texto)
        
        print(f"--- Análisis de {archivo_prueba.name} ---")
        print(f"📅 Fecha encontrada: {resultados['fecha']}")
        print(f"🏢 Sucursal / Entidad: {resultados['sucursal']}")