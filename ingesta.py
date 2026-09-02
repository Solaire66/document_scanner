import os
from pathlib import Path

# Definición de rutas del proyecto
BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "input_docs"
PROCESSED_DIR = BASE_DIR / "processed_docs"
FLAGGED_DIR = BASE_DIR / "flagged_docs"
REPORTS_DIR = BASE_DIR / "reports"

# Extensiones soportadas
EXTENSIONES_PERMITIDAS = {".pdf", ".png", ".jpg", ".jpeg"}

def verificar_estructura():
    """Crea las carpetas del proyecto si no existen."""
    for directorio in [INPUT_DIR, PROCESSED_DIR, FLAGGED_DIR, REPORTS_DIR]:
        directorio.mkdir(exist_ok=True)
    print("✅ Estructura de carpetas verificada.")

def listar_documentos_pendientes():
    """Obtiene la lista de documentos en la carpeta input_docs."""
    archivos = [
        f for f in INPUT_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in EXTENSIONES_PERMITIDAS
    ]
    return archivos

if __name__ == "__main__":
    verificar_estructura()
    pendientes = listar_documentos_pendientes()
    print(f"📄 Se encontraron {len(pendientes)} documentos listos para auditar en '{INPUT_DIR.name}':")
    for doc in pendientes:
        print(f"  - {doc.name}")