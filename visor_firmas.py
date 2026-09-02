import json
import ollama
from pdf2image import convert_from_path
from PIL import Image

POPPLER_PATH = r'E:\poppler\Library\bin'

def obtener_imagen_documento(ruta_archivo):
    """Convierte la primera página del PDF a imagen en disco para enviarla a Ollama."""
    extension = ruta_archivo.suffix.lower()
    
    if extension == ".pdf":
        paginas = convert_from_path(ruta_archivo, first_page=1, last_page=1, poppler_path=POPPLER_PATH)
        temp_img_path = "temp_page.png"
        paginas[0].save(temp_img_path, "PNG")
        return temp_img_path
    elif extension in [".png", ".jpg", ".jpeg"]:
        return str(ruta_archivo)
    return None

def verificar_firma_con_ia(ruta_imagen):
    """Consulta al modelo de visión si existe una firma manuscrita presente."""
    prompt = """
    Analiza detalladamente esta imagen de documento oficial.
    Determina si existe alguna firma manuscrita (trazos de pluma/tinta hechos a mano) sobre el nombre de la persona, autoridad o sello.
    
    Responde ÚNICAMENTE en este formato JSON exacto sin texto adicional:
    {
      "firma_presente": true,
      "confianza": "alta"
    }
    Si NO hay firma escrita a mano, responde "firma_presente": false.
    """

    try:
        # Usamos moondream (o cambia a 'llava' si es el modelo que tienes descargado)
        respuesta = ollama.chat(
            model='moondream',
            messages=[{
                'role': 'user',
                'content': prompt,
                'images': [ruta_imagen]
            }]
        )

        contenido = respuesta['message']['content'].strip()
        # Limpieza básica por si el modelo devuelve markdown ```json
        if "```" in contenido:
            contenido = contenido.split("```")[1].replace("json", "").strip()
            
        datos = json.loads(contenido)
        return datos.get("firma_presente", False)

    except Exception as e:
        print(f"⚠️ Error al consultar IA visual: {e}")
        return False

if __name__ == "__main__":
    from pathlib import Path

    archivo_prueba = Path("input_docs/Scan.pdf")
    if archivo_prueba.exists():
        print(f"🔍 Convirtiendo {archivo_prueba.name} para análisis visual...")
        img_temp = obtener_imagen_documento(archivo_prueba)

        print("🤖 Analizando presencia de firma con Ollama...")
        tiene_firma = verificar_firma_con_ia(img_temp)

        print("\n--- Resultado de Validación Visual ---")
        if tiene_firma:
            print("✅ FIRMA DETECTADA: El documento contiene trazo/firma manuscrita.")
        else:
            print("❌ SIN FIRMA: No se detectó trazo manuscrito en el documento.")