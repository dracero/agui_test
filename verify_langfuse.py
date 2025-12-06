#!/usr/bin/env python3
"""
Script para verificar la configuración de Langfuse
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def verify_langfuse_config():
    print("🔍 Verificando configuración de Langfuse...\n")
    
    # Verificar variables de entorno
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    base_url = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
    
    print("📋 Variables de entorno:")
    print(f"  LANGFUSE_SECRET_KEY: {'✅ Configurada' if secret_key else '❌ No encontrada'}")
    print(f"  LANGFUSE_PUBLIC_KEY: {'✅ Configurada' if public_key else '❌ No encontrada'}")
    print(f"  LANGFUSE_BASE_URL: {base_url}\n")
    
    if not secret_key or not public_key:
        print("❌ Error: Faltan credenciales de Langfuse en el archivo .env")
        return False
    
    # Intentar importar y conectar con Langfuse
    try:
        import langfuse
        print("✅ Paquete langfuse importado correctamente\n")
        
        # Crear cliente
        client = langfuse.Langfuse(
            secret_key=secret_key,
            public_key=public_key,
            host=base_url
        )
        print("✅ Cliente de Langfuse creado exitosamente\n")
        
        # Crear un trace de prueba
        print("📝 Creando trace de prueba...")
        trace = client.trace(
            name="verification_test",
            user_id="test_user",
            metadata={"test": True}
        )
        print(f"✅ Trace de prueba creado: {trace.id}\n")
        
        # Flush para asegurar que se envía
        client.flush()
        print("✅ Datos enviados a Langfuse Cloud\n")
        
        print("=" * 60)
        print("✅ VERIFICACIÓN EXITOSA")
        print("=" * 60)
        print(f"\n🌐 Puedes ver el trace en: {base_url}")
        print("\nLangfuse está configurado correctamente y listo para usar.")
        print("Los agentes comenzarán a enviar traces automáticamente.\n")
        
        return True
        
    except ImportError:
        print("❌ Error: El paquete langfuse no está instalado")
        print("   Ejecuta: pip install langfuse>=2.0.0\n")
        return False
    except Exception as e:
        print(f"❌ Error al conectar con Langfuse: {e}\n")
        print("Verifica que las credenciales sean correctas y que tengas")
        print("conexión a internet.\n")
        return False

if __name__ == "__main__":
    success = verify_langfuse_config()
    exit(0 if success else 1)
