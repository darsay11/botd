# exportar_bot_mt5.py
import os
import sys
import zipfile
import json
from pathlib import Path

# Configurar la ruta específica de tu proyecto MT5
RUTA_PROYECTO = r"C:\Users\ASUS\Documents\Bots\Binance\bot 2"

def verificar_proyecto_mt5():
    """Verifica características específicas de bot MT5"""
    print("🔍 Analizando proyecto MT5...")
    
    if not os.path.exists(RUTA_PROYECTO):
        print(f"❌ Error: No se encuentra la ruta: {RUTA_PROYECTO}")
        return False
    
    # Buscar indicadores de MT5
    indicadores_mt5 = []
    archivos_clave_mt5 = []
    
    for root, dirs, files in os.walk(RUTA_PROYECTO):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        contenido = f.read().lower()
                        # Buscar indicadores de MT5
                        if any(keyword in contenido for keyword in [
                            'mt5', 'metatrader', 'symbol_info', 'order_send',
                            'copy_rates_from', 'terminal_info', 'initialize',
                            'shutdown', 'symbols_get', 'account_info'
                        ]):
                            indicadores_mt5.append(os.path.relpath(filepath, RUTA_PROYECTO))
                            
                            if 'mt5' in contenido or 'metatrader' in contenido:
                                archivos_clave_mt5.append(os.path.relpath(filepath, RUTA_PROYECTO))
                except:
                    pass
    
    print(f"✅ Proyecto MT5 encontrado")
    if indicadores_mt5:
        print(f"📊 Archivos con código MT5: {len(indicadores_mt5)}")
    
    return True

def exportar_bot_mt5():
    """Exporta bot MT5 para análisis por IA"""
    
    os.chdir(RUTA_PROYECTO)
    
    output_files = {
        'zip': "bot_mt5_completo.zip",
        'txt': "bot_mt5_analisis.txt",
        'json': "mt5_config.json",
        'resumen': "resumen_mt5_chatgpt.txt"
    }
    
    print(f"\n🤖 Exportando Bot MT5...")
    
    # 1. Crear análisis específico
    crear_analisis_mt5(output_files['txt'])
    
    # 2. Crear configuración MT5
    crear_config_mt5(output_files['json'])
    
    # 3. Crear resumen para ChatGPT
    crear_resumen_chatgpt(output_files['resumen'])
    
    # 4. Crear ZIP (excluyendo datos grandes)
    crear_zip_mt5(output_files['zip'])
    
    print(f"\n✅ Exportación MT5 completada!")
    print(f"📁 Archivos creados en: {RUTA_PROYECTO}")
    
    # Mostrar resumen
    mostrar_resumen_exportacion()
    
    return output_files

def crear_analisis_mt5(output_file):
    """Crea análisis específico para bot MT5"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("🤖 BOT METATRADER 5 (MT5) - ANÁLISIS COMPLETO\n")
        f.write("="*80 + "\n\n")
        
        # Identificar componentes MT5
        f.write("🔍 COMPONENTES MT5 IDENTIFICADOS:\n")
        f.write("-"*40 + "\n")
        
        componentes = {
            'conexion': [],
            'estrategias': [],
            'ordenes': [],
            'datos': [],
            'utilidades': []
        }
        
        # Analizar archivos Python
        for root, dirs, files in os.walk(RUTA_PROYECTO):
            # Excluir directorios no deseados
            if 'venv' in root or '__pycache__' in root:
                continue
                
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, RUTA_PROYECTO)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as pf:
                            contenido = pf.read()
                            contenido_lower = contenido.lower()
                            
                            # Clasificar por funcionalidad
                            if any(keyword in contenido_lower for keyword in [
                                'mt5.initialize', 'mt5.shutdown', 'mt5.login'
                            ]):
                                componentes['conexion'].append(rel_path)
                                
                            elif any(keyword in contenido_lower for keyword in [
                                'order_send', 'mt5.order_send', 'mt5.orders_get'
                            ]):
                                componentes['ordenes'].append(rel_path)
                                
                            elif any(keyword in contenido_lower for keyword in [
                                'symbol_info', 'copy_rates', 'copy_ticks'
                            ]):
                                componentes['datos'].append(rel_path)
                                
                            elif 'class' in contenido_lower and 'strategy' in contenido_lower:
                                componentes['estrategias'].append(rel_path)
                            elif 'def' in contenido and ('strategy' in contenido_lower or 'signal' in contenido_lower):
                                componentes['estrategias'].append(rel_path)
                                
                    except:
                        pass
        
        # Escribir componentes encontrados
        for tipo, archivos in componentes.items():
            if archivos:
                f.write(f"\n📂 {tipo.upper()}:\n")
                for archivo in archivos[:5]:  # Mostrar primeros 5
                    f.write(f"   • {archivo}\n")
                if len(archivos) > 5:
                    f.write(f"   ... y {len(archivos)-5} más\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("📄 CÓDIGO PRINCIPAL MT5:\n")
        f.write("-"*40 + "\n\n")
        
        # Incluir código de archivos MT5 clave
        archivos_mt5_clave = []
        
        # Buscar archivos con lógica MT5
        for root, dirs, files in os.walk(RUTA_PROYECTO):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as pf:
                            if 'import mt5' in pf.read() or 'import MetaTrader5' in pf.read():
                                archivos_mt5_clave.append(filepath)
                    except:
                        pass
        
        # Escribir máximo 3 archivos principales
        for archivo in archivos_mt5_clave[:3]:
            rel_path = os.path.relpath(archivo, RUTA_PROYECTO)
            f.write(f"\n{'='*60}\n")
            f.write(f"ARCHIVO: {rel_path}\n")
            f.write(f"{'='*60}\n\n")
            
            try:
                with open(archivo, 'r', encoding='utf-8') as pf:
                    # Mostrar estructura, no todo el código
                    lineas = pf.readlines()
                    f.write(f"Total líneas: {len(lineas)}\n\n")
                    
                    # Mostrar imports
                    f.write("IMPORTS:\n")
                    for linea in lineas[:20]:
                        if 'import' in linea or 'from' in linea:
                            f.write(f"  {linea.rstrip()}\n")
                    
                    # Mostrar funciones/clases principales
                    f.write("\nDEFINICIONES PRINCIPALES:\n")
                    for linea in lineas:
                        linea_limpia = linea.strip()
                        if linea_limpia.startswith(('def ', 'class ', 'async def ')):
                            f.write(f"  {linea_limpia}\n")
                    
                    # Mostrar uso de MT5
                    f.write("\nLLAMADAS MT5 DESTACADAS:\n")
                    for linea in lineas:
                        if 'mt5.' in linea or 'MetaTrader5' in linea:
                            f.write(f"  {linea.strip()}\n")
                            
            except Exception as e:
                f.write(f"Error leyendo archivo: {e}\n")

def crear_config_mt5(output_file):
    """Extrae configuración MT5 del proyecto"""
    
    config = {
        "tipo_proyecto": "Bot MT5 Python",
        "estructura": {},
        "dependencias_mt5": [],
        "configuraciones": {}
    }
    
    # Buscar archivos de configuración
    config_files = []
    for root, dirs, files in os.walk(RUTA_PROYECTO):
        for file in files:
            if any(keyword in file.lower() for keyword in ['config', 'settings', '.env', '.ini']):
                config_files.append(os.path.join(root, file))
    
    # Analizar requirements.txt
    req_path = Path(RUTA_PROYECTO) / "requirements.txt"
    if req_path.exists():
        with open(req_path, 'r') as f:
            for linea in f:
                linea = linea.strip()
                if 'mt5' in linea.lower() or 'metatrader' in linea.lower():
                    config["dependencias_mt5"].append(linea)
    
    # Guardar JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def crear_resumen_chatgpt(output_file):
    """Crea resumen optimizado para ChatGPT"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("PROYECTO: Bot de Trading para MetaTrader 5 (MT5)\n")
        f.write("="*70 + "\n\n")
        
        f.write("DESCRIPCIÓN:\n")
        f.write("Bot de trading automatizado para MetaTrader 5 desarrollado en Python\n\n")
        
        f.write("ESTRUCTURA PRINCIPAL:\n")
        f.write("-"*40 + "\n")
        
        # Mostrar directorios principales
        for item in sorted(os.listdir(RUTA_PROYECTO)):
            item_path = os.path.join(RUTA_PROYECTO, item)
            if os.path.isdir(item_path):
                if not item.startswith(('.', '_')) and item not in ['venv', '__pycache__', 'logs']:
                    f.write(f"📁 {item}/\n")
        
        f.write("\nARCHIVOS CLAVE MT5:\n")
        f.write("-"*40 + "\n")
        
        # Buscar archivos con lógica MT5
        mt5_files = []
        for root, dirs, files in os.walk(RUTA_PROYECTO):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as pf:
                            if 'mt5' in pf.read() or 'MetaTrader5' in pf.read():
                                rel_path = os.path.relpath(filepath, RUTA_PROYECTO)
                                mt5_files.append(rel_path)
                    except:
                        pass
        
        for archivo in mt5_files[:10]:  # Primeros 10
            f.write(f"• {archivo}\n")
        
        f.write("\nDEPENDENCIAS PRINCIPALES:\n")
        f.write("-"*40 + "\n")
        
        # Leer requirements.txt si existe
        req_file = os.path.join(RUTA_PROYECTO, "requirements.txt")
        if os.path.exists(req_file):
            with open(req_file, 'r') as rf:
                for linea in rf:
                    linea = linea.strip()
                    if linea and not linea.startswith('#'):
                        f.write(f"{linea}\n")
        
        f.write("\nCÓDIGO DE CONEXIÓN MT5 (ejemplo):\n")
        f.write("-"*40 + "\n")
        
        # Buscar código de inicialización MT5
        for root, dirs, files in os.walk(RUTA_PROYECTO):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as pf:
                            contenido = pf.read()
                            if 'mt5.initialize(' in contenido:
                                f.write(f"\nArchivo: {os.path.relpath(filepath, RUTA_PROYECTO)}\n")
                                # Extraer líneas relevantes
                                lineas = contenido.split('\n')
                                for i, linea in enumerate(lineas):
                                    if 'mt5.' in linea or 'MetaTrader5' in linea:
                                        f.write(f"  {linea.strip()}\n")
                                break
                    except:
                        pass

def crear_zip_mt5(output_file):
    """Crea ZIP excluyendo datos innecesarios"""
    
    exclusiones = {
        '__pycache__', 'venv', '.env', '.git', '.vscode',
        '.idea', 'logs', 'reports', 'data', '__pycache__',
        '*.log', '*.csv', '*.xlsx', '*.pdf', '*.jpg', '*.png'
    }
    
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(RUTA_PROYECTO):
            # Filtrar directorios
            dirs[:] = [d for d in dirs if d not in exclusiones and not d.startswith('.')]
            
            for file in files:
                # Incluir solo archivos relevantes
                if any(file.endswith(ext) for ext in ['.py', '.txt', '.md', '.json', '.yml', '.yaml', '.ini', '.cfg']):
                    filepath = os.path.join(root, file)
                    arcname = os.path.relpath(filepath, RUTA_PROYECTO)
                    try:
                        zipf.write(filepath, arcname)
                    except:
                        pass

def mostrar_resumen_exportacion():
    """Muestra resumen de lo exportado"""
    
    print("\n" + "="*60)
    print("📋 RESUMEN DE EXPORTACIÓN MT5")
    print("="*60)
    
    archivos_exportados = [
        "bot_mt5_analisis.txt",    # Análisis completo
        "resumen_mt5_chatgpt.txt", # Para pegar en ChatGPT
        "mt5_config.json",         # Configuración
        "bot_mt5_completo.zip"     # Todo el código
    ]
    
    for archivo in archivos_exportados:
        ruta_completa = os.path.join(RUTA_PROYECTO, archivo)
        if os.path.exists(ruta_completa):
            tamaño_kb = os.path.getsize(ruta_completa) / 1024
            print(f"✓ {archivo:<25} {tamaño_kb:6.1f} KB")
    
    print("\n🎯 RECOMENDACIONES PARA USAR:")
    print("1. Para ChatGPT: Copia 'resumen_mt5_chatgpt.txt'")
    print("2. Para análisis profundo: Sube 'bot_mt5_completo.zip'")
    print("3. Para revisar estructura: Abre 'bot_mt5_analisis.txt'")

def main_mt5():
    """Menú principal para bot MT5"""
    
    print("="*60)
    print("🤖 EXPORTADOR BOT METATRADER 5 (MT5)")
    print("="*60)
    
    if not verificar_proyecto_mt5():
        print("\n❌ No se pudo verificar el proyecto MT5")
        sys.exit(1)
    
    print("\n📊 OPCIONES DE EXPORTACIÓN:")
    print("1. 📦 Exportación completa (recomendado)")
    print("2. 📝 Solo resumen para ChatGPT")
    print("3. 🔍 Ver estructura MT5 específica")
    print("4. 🚪 Salir")
    
    try:
        opcion = input("\nSelecciona [1/2/3/4]: ").strip()
        
        if opcion == '1':
            archivos = exportar_bot_mt5()
            
            print(f"\n📍 Los archivos están en: {RUTA_PROYECTO}")
            print("\n📤 Para ChatGPT/Claude:")
            print("   Opción A: Copia el contenido de 'resumen_mt5_chatgpt.txt'")
            print("   Opción B: Sube 'bot_mt5_completo.zip' a Claude.ai")
            
        elif opcion == '2':
            crear_resumen_chatgpt("resumen_mt5_chatgpt.txt")
            print(f"\n✅ Resumen creado: resumen_mt5_chatgpt.txt")
            
            # Mostrar contenido para copiar fácilmente
            print("\n📋 Contenido listo para copiar:")
            print("-"*40)
            with open("resumen_mt5_chatgpt.txt", 'r', encoding='utf-8') as f:
                print(f.read()[:2000])  # Primeros 2000 caracteres
            print("... [continúa en el archivo]")
            
        elif opcion == '3':
            print("\n🔍 Buscando componentes MT5...")
            
            # Buscar archivos con código MT5
            mt5_files = []
            for root, dirs, files in os.walk(RUTA_PROYECTO):
                for file in files:
                    if file.endswith('.py'):
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as pf:
                                contenido = pf.read()
                                if 'mt5' in contenido or 'MetaTrader5' in contenido:
                                    rel_path = os.path.relpath(filepath, RUTA_PROYECTO)
                                    mt5_files.append(rel_path)
                        except:
                            pass
            
            if mt5_files:
                print(f"\n📁 Archivos con código MT5 ({len(mt5_files)}):")
                for archivo in mt5_files[:15]:  # Mostrar primeros 15
                    print(f"  • {archivo}")
                if len(mt5_files) > 15:
                    print(f"  ... y {len(mt5_files)-15} más")
            else:
                print("⚠️  No se encontraron archivos con código MT5 específico")
                
        elif opcion == '4':
            print("👋 Saliendo...")
            sys.exit(0)
            
        else:
            print("❌ Opción no válida")
            
    except KeyboardInterrupt:
        print("\n\n👋 Operación cancelada")
        sys.exit(0)

if __name__ == "__main__":
    main_mt5()