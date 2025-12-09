# exportar_bot_binance.py
import os
import sys
import zipfile
import json
from pathlib import Path

# Configurar la ruta específica de tu proyecto
RUTA_PROYECTO = r"C:\Users\ASUS\Documents\Bots\Binance\bot 2"

def verificar_estructura():
    """Verifica que la estructura del proyecto exista"""
    print("🔍 Verificando estructura del proyecto...")
    
    if not os.path.exists(RUTA_PROYECTO):
        print(f"❌ Error: No se encuentra la ruta: {RUTA_PROYECTO}")
        print("Por favor, verifica que el directorio existe")
        return False
    
    print(f"✅ Proyecto encontrado en: {RUTA_PROYECTO}")
    
    # Listar directorios principales
    print("\n📂 Directorios encontrados:")
    for item in os.listdir(RUTA_PROYECTO):
        item_path = os.path.join(RUTA_PROYECTO, item)
        if os.path.isdir(item_path):
            print(f"  - {item}/")
    
    return True

def exportar_proyecto_completo():
    """Exporta todo el proyecto para análisis por IA"""
    
    os.chdir(RUTA_PROYECTO)  # Cambiar al directorio del proyecto
    
    output_zip = "bot_binance_completo.zip"
    output_txt = "bot_binance_para_ia.txt"
    output_json = "proyecto_estructura.json"
    
    print(f"\n📦 Creando exportación completa...")
    print(f"   ZIP: {output_zip}")
    print(f"   TXT: {output_txt}")
    print(f"   JSON: {output_json}")
    
    # 1. Crear archivo JSON con estructura
    crear_json_estructura(output_json)
    
    # 2. Crear archivo TXT para IA
    crear_archivo_ia(output_txt)
    
    # 3. Crear ZIP
    crear_zip_completo(output_zip)
    
    print(f"\n✅ Exportación completada exitosamente!")
    print(f"📁 Archivos creados en: {RUTA_PROYECTO}")
    
    return True

def crear_json_estructura(output_file):
    """Crea un JSON con la estructura del proyecto"""
    estructura = {
        "nombre_proyecto": "Bot Binance Trading",
        "ruta": RUTA_PROYECTO,
        "directorios": {},
        "archivos_principales": [],
        "estadisticas": {}
    }
    
    # Contadores
    total_py = 0
    total_archivos = 0
    
    # Analizar directorios importantes
    dirs_importantes = ['bot', 'strategies', 'core', 'configs', 'data', 'execution', 'risk', 'ui']
    
    for dir_name in dirs_importantes:
        dir_path = Path(RUTA_PROYECTO) / dir_name
        if dir_path.exists():
            archivos_py = list(dir_path.rglob("*.py"))
            estructura["directorios"][dir_name] = {
                "archivos_python": len(archivos_py),
                "archivos": [f.name for f in archivos_py[:10]]  # Primeros 10
            }
            total_py += len(archivos_py)
    
    # Archivos principales
    archivos_clave = ['main.py', 'requirements.txt', 'README.md']
    for archivo in archivos_clave:
        archivo_path = Path(RUTA_PROYECTO) / archivo
        if archivo_path.exists():
            estructura["archivos_principales"].append(archivo)
    
    # Estadísticas
    estructura["estadisticas"] = {
        "total_archivos_python": total_py,
        "directorios_importantes": len(estructura["directorios"])
    }
    
    # Guardar JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(estructura, f, indent=2, ensure_ascii=False)
    
    return estructura

def crear_archivo_ia(output_file):
    """Crea un archivo de texto optimizado para IA"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("🤖 PROYECTO BOT BINANCE TRADING - ANÁLISIS COMPLETO\n")
        f.write("="*80 + "\n\n")
        
        f.write("📍 RUTA DEL PROYECTO:\n")
        f.write(f"{RUTA_PROYECTO}\n\n")
        
        f.write("📁 ESTRUCTURA PRINCIPAL:\n")
        f.write("-"*40 + "\n")
        
        # Mostrar árbol simplificado
        for item in sorted(os.listdir(RUTA_PROYECTO)):
            item_path = os.path.join(RUTA_PROYECTO, item)
            if os.path.isdir(item_path):
                if not item.startswith(('.', '_')) and item not in ['venv', 'logs', '__pycache__']:
                    f.write(f"📂 {item}/\n")
                    
                    # Archivos Python en este directorio
                    try:
                        for root, dirs, files in os.walk(item_path):
                            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
                            for file in files:
                                if file.endswith('.py'):
                                    rel_path = os.path.relpath(os.path.join(root, file), RUTA_PROYECTO)
                                    f.write(f"   └── 📄 {rel_path}\n")
                    except:
                        pass
        
        f.write("\n📄 ARCHIVOS CLAVE:\n")
        f.write("-"*40 + "\n")
        
        # Analizar archivos importantes
        archivos_analizar = [
            'main.py',
            'requirements.txt',
            'README.md'
        ]
        
        for archivo in archivos_analizar:
            archivo_path = Path(RUTA_PROYECTO) / archivo
            if archivo_path.exists():
                f.write(f"\n🔸 {archivo}:\n")
                try:
                    with open(archivo_path, 'r', encoding='utf-8') as af:
                        contenido = af.read()
                        if archivo.endswith('.py'):
                            # Para Python, mostrar estructura
                            lineas = contenido.split('\n')
                            f.write(f"   Líneas: {len(lineas)}\n")
                            # Mostrar imports y definiciones principales
                            for linea in lineas[:50]:  # Primeras 50 líneas
                                if linea.strip().startswith(('import ', 'from ', 'def ', 'class ', 'async def ')):
                                    f.write(f"   {linea.strip()}\n")
                        else:
                            # Para otros archivos, mostrar contenido completo
                            f.write(contenido[:1000] + "\n")  # Primeros 1000 caracteres
                except Exception as e:
                    f.write(f"   Error leyendo archivo: {e}\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("📦 DEPENDENCIAS (requirements.txt):\n")
        f.write("-"*40 + "\n")
        
        req_path = Path(RUTA_PROYECTO) / "requirements.txt"
        if req_path.exists():
            with open(req_path, 'r') as rf:
                for linea in rf:
                    f.write(f"• {linea.strip()}\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("🧩 CÓDIGO PRINCIPAL:\n")
        f.write("-"*40 + "\n\n")
        
        # Incluir código de archivos Python principales
        archivos_py_principales = [
            'main.py',
            'bot/__init__.py',
            'strategies/main_strategy.py',
            'core/engine.py',
            'configs/settings.py'
        ]
        
        for archivo_rel in archivos_py_principales:
            archivo_path = Path(RUTA_PROYECTO) / archivo_rel
            if archivo_path.exists():
                f.write(f"\n{'='*60}\n")
                f.write(f"ARCHIVO: {archivo_rel}\n")
                f.write(f"{'='*60}\n\n")
                try:
                    with open(archivo_path, 'r', encoding='utf-8') as pf:
                        f.write(pf.read())
                    f.write("\n")
                except:
                    f.write("(No se pudo leer el archivo)\n")

def crear_zip_completo(output_file):
    """Crea un ZIP con todo el proyecto"""
    
    exclusiones = {
        '__pycache__', 'venv', '.env', '.git', '.vscode',
        '.idea', 'logs', 'reports', 'tests_backup',
        '*.pyc', '*.pyo', '*.pyd', '.DS_Store'
    }
    
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(RUTA_PROYECTO):
            # Filtrar directorios excluidos
            dirs[:] = [
                d for d in dirs 
                if d not in exclusiones 
                and not d.startswith('.')
                and not d.startswith('_')
            ]
            
            for file in files:
                # Excluir por extensión
                if any(file.endswith(ext) for ext in ['.pyc', '.pyo', '.pyd', '.log']):
                    continue
                
                # Incluir archivos relevantes
                if any(file.endswith(ext) for ext in ['.py', '.txt', '.md', '.json', '.yml', '.yaml', '.ini', '.cfg', '.env']):
                    filepath = os.path.join(root, file)
                    arcname = os.path.relpath(filepath, RUTA_PROYECTO)
                    try:
                        zipf.write(filepath, arcname)
                    except Exception as e:
                        print(f"  ⚠️  No se pudo agregar: {filepath} - {e}")

def crear_resumen_rapido():
    """Crea un resumen rápido para pegar en ChatGPT"""
    
    resumen_path = os.path.join(RUTA_PROYECTO, "resumen_rapido.txt")
    
    with open(resumen_path, 'w', encoding='utf-8') as f:
        f.write("PROYECTO: Bot Binance Trading\n")
        f.write(f"RUTA: {RUTA_PROYECTO}\n\n")
        
        f.write("ESTRUCTURA:\n")
        for item in sorted(os.listdir(RUTA_PROYECTO)):
            if os.path.isdir(os.path.join(RUTA_PROYECTO, item)):
                if not item.startswith(('.', '_')) and item not in ['venv', '__pycache__']:
                    f.write(f"├── {item}/\n")
        
        f.write("\nARCHIVOS PRINCIPALES:\n")
        for archivo in ['main.py', 'requirements.txt', 'README.md']:
            if os.path.exists(os.path.join(RUTA_PROYECTO, archivo)):
                f.write(f"• {archivo}\n")
        
        f.write("\nREQUIREMENTS.TXT:\n")
        req_file = os.path.join(RUTA_PROYECTO, "requirements.txt")
        if os.path.exists(req_file):
            with open(req_file, 'r') as rf:
                f.write(rf.read())
    
    print(f"📝 Resumen rápido creado: {resumen_path}")
    return resumen_path

def main():
    """Función principal"""
    
    print("="*60)
    print("🤖 EXPORTADOR DE PROYECTO BINANCE TRADING")
    print("="*60)
    
    # Verificar que el proyecto existe
    if not verificar_estructura():
        sys.exit(1)
    
    print("\nSelecciona una opción:")
    print("1. 📦 Exportación completa (ZIP + TXT + JSON)")
    print("2. 📝 Solo resumen rápido para ChatGPT")
    print("3. 🔍 Ver estructura del proyecto")
    print("4. 🚪 Salir")
    
    try:
        opcion = input("\nOpción [1/2/3/4]: ").strip()
        
        if opcion == '1':
            exportar_proyecto_completo()
            
            # Mostrar ubicación de archivos
            print(f"\n📍 Archivos creados en:")
            print(f"   {RUTA_PROYECTO}")
            print(f"\n📤 Puedes subir 'bot_binance_completo.zip' a ChatGPT o Claude")
            print(f"📋 O copiar el contenido de 'bot_binance_para_ia.txt'")
            
        elif opcion == '2':
            resumen = crear_resumen_rapido()
            print(f"\n✅ Resumen creado: {resumen}")
            print("\n📋 Copia y pega este contenido en ChatGPT:")
            print("-"*40)
            with open(resumen, 'r', encoding='utf-8') as f:
                print(f.read())
                
        elif opcion == '3':
            print("\n📂 Estructura del proyecto:")
            print("-"*40)
            for item in sorted(os.listdir(RUTA_PROYECTO)):
                item_path = os.path.join(RUTA_PROYECTO, item)
                if os.path.isdir(item_path):
                    tipo = "📂"
                else:
                    tipo = "📄"
                print(f"{tipo} {item}")
            
        elif opcion == '4':
            print("👋 Saliendo...")
            sys.exit(0)
            
        else:
            print("❌ Opción no válida")
            
    except KeyboardInterrupt:
        print("\n\n👋 Operación cancelada por el usuario")
        sys.exit(0)

if __name__ == "__main__":
    main()