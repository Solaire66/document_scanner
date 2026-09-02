import os
import re
import json
import shutil
from pathlib import Path
import pdfplumber
import pytesseract
import pandas as pd
import ollama
from PIL import Image
from pdf2image import convert_from_path

# Rutas del entorno Windows
pytesseract.pytesseract.tesseract_cmd = r'E:\Tesseract\tesseract.exe'
POPPLER_PATH = r'E:\poppler\Library\bin'

# Estructura de carpetas del proyecto
BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "input_docs"
PROCESSED_DIR = BASE_DIR / "processed_docs"
FLAGGED_DIR = BASE_DIR / "flagged_docs"
REPORTS_DIR = BASE_DIR / "reports"

def extraer_texto(ruta_archivo):
    """Extrae texto mediante pdfplumber u OCR."""
    ext = ruta_archivo.suffix.lower()
    texto = ""

    if ext == ".pdf":
        try:
            with pdfplumber.open(ruta_archivo) as pdf:
                for pag in pdf.pages:
                    texto += (pag.extract_text() or "") + "\n"
        except Exception:
            pass

        if not texto.strip():
            try:
                paginas = convert_from_path(ruta_archivo, poppler_path=POPPLER_PATH)
                for pag in paginas:
                    texto += pytesseract.image_to_string(pag, lang='spa') + "\n"
            except Exception as e:
                print(f"  ⚠️ Error en OCR del archivo {ruta_archivo.name}: {e}")

    elif ext in [".png", ".jpg", ".jpeg"]:
        img = Image.open(ruta_archivo)
        texto = pytesseract.image_to_string(img, lang='spa')

    return texto

def buscar_campos_clave(texto):
    """Extrae la fecha y sucursal/entidad."""
    patron_fecha_texto = r'\b(\d{1,2}\s+DE\s+[A-ZÁÉÍÓÚ]+\s+DE\s+\d{4})\b'
    patron_fecha_num = r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b'
    
    match_fecha = re.search(patron_fecha_texto, texto, re.IGNORECASE) or re.search(patron_fecha_num, texto, re.IGNORECASE)
    
    patron_sucursal = r'(?:sucursal|planta|sede|tienda|cam|gral\.)\s*:?\s*([a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s\.\,\-]+)'
    match_sucursal = re.search(patron_sucursal, texto, re.IGNORECASE)

    fecha = match_fecha.group(0).strip() if match_fecha else None
    sucursal = match_sucursal.group(0).split('\n')[0].strip() if match_sucursal else None

    return fecha, sucursal

def verificar_firma(ruta_archivo):
    """Verifica la presencia de trazos manuscritos/firmas en el documento."""
    ext = ruta_archivo.suffix.lower()
    img_path = str(ruta_archivo)
    temp_created = False

    if ext == ".pdf":
        try:
            paginas = convert_from_path(ruta_archivo, first_page=1, last_page=1, poppler_path=POPPLER_PATH)
            img_path = str(BASE_DIR / "temp_eval.png")
            paginas[0].save(img_path, "PNG")
            temp_created = True
        except Exception:
            return False

    # Prompt optimizado para cualquier tipo de cargo o formato de firma
    prompt = """
    Examina la parte inferior de este documento oficial.
    ¿Existe alguna firma manuscrita, rúbrica o trazo hecho a mano con pluma/tinta sobre o cerca de los nombres, cargos o sellos?
    
    Responde ÚNICAMENTE con este JSON exacto:
    {"firma_presente": true}
    
    Si el documento está completamente impreso y NO tiene ninguna firma escrita a mano, responde:
    {"firma_presente": false}
    """

    try:
        res = ollama.chat(
            model='moondream',
            messages=[{'role': 'user', 'content': prompt, 'images': [img_path]}]
        )
        content = res['message']['content'].strip()
        if "```" in content:
            content = content.split("```")[1].replace("json", "").strip()
        data = json.loads(content)
        tiene_firma = data.get("firma_presente", False)
    except Exception:
        tiene_firma = False

    if temp_created and os.path.exists(img_path):
        os.remove(img_path)

    return tiene_firma

def ejecutar_auditoria():
    """Ejecuta el pipeline completo de auditoría sobre la carpeta input_docs."""
    archivos = [f for f in INPUT_DIR.iterdir() if f.is_file() and f.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg"}]
    
    if not archivos:
        print("📂 No se encontraron documentos pendientes en 'input_docs/'.")
        return

    print(f"🚀 Iniciando auditoría masiva de {len(archivos)} documento(s)...\n")
    resultados = []

    for idx, doc in enumerate(archivos, 1):
        print(f"[{idx}/{len(archivos)}] Procesando: {doc.name}")
        
        # 1. OCR y Regex
        texto = extraer_texto(doc)
        fecha, sucursal = buscar_campos_clave(texto)
        
        # 2. IA Visual
        tiene_firma = verificar_firma(doc)
        
        # 3. Criterio de Aprobación
        es_valido = bool(fecha and sucursal and tiene_firma)
        estado = "APROBADO" if es_valido else "RECHAZADO"

        # 4. Mover Archivo según resultado
        destino = PROCESSED_DIR / doc.name if es_valido else FLAGGED_DIR / doc.name
        shutil.move(str(doc), str(destino))

        # 5. Registro para Reporte
        resultados.append({
            "Archivo": doc.name,
            "Estado": estado,
            "Fecha Detectada": fecha or "FALTANTE",
            "Sucursal / Entidad": sucursal or "FALTANTE",
            "Firma Manuscrita": "DETECTADA" if tiene_firma else "FALTANTE",
            "Ruta Almacenamiento": str(destino)
        })

    # 6. Generar Reporte Excel
    df = pd.DataFrame(resultados)
    reporte_path = REPORTS_DIR / "Reporte_Auditoria_Final.xlsx"
    df.to_excel(reporte_path, index=False)

    print("\n" + "="*50)
    print("✅ AUDITORÍA FINALIZADA CON ÉXITO")
    print(f"📊 Reporte Excel generado en: {reporte_path}")
    print(f"📁 Aprobados (Mover a Processed): {len(df[df['Estado'] == 'APROBADO'])}")
    print(f"⚠️ Rechazados (Mover a Flagged): {len(df[df['Estado'] == 'RECHAZADO'])}")
    print("="*50)

if __name__ == "__main__":
    for d in [INPUT_DIR, PROCESSED_DIR, FLAGGED_DIR, REPORTS_DIR]:
        d.mkdir(exist_ok=True)
    ejecutar_auditoria()