#!/usr/bin/env python3
"""
Script de prueba para verificar que los adapters LLM funcionan correctamente.

Uso:
  python scripts/testing/test_llm_adapters.py --adapter openai
  python scripts/testing/test_llm_adapters.py --adapter huggingface --model "google/codegemma-7b-it"
"""

import sys
from pathlib import Path

# Añadir el directorio pipeline al path para importar
sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline"))

from phase2_llm_refinement import (
    OpenRouterAdapter,
    OpenAIAdapter, 
    AnthropicAdapter, 
    HuggingFaceAdapter, 
    OllamaAdapter
)
import argparse


# Test simple de Java
SIMPLE_TEST_CODE = """
public class CalculatorTest {
    @Test
    public void test0() {
        Calculator var0 = new Calculator();
        int var1 = var0.add(2, 3);
        assertNotNull(var0);
    }
}
"""


def test_adapter(adapter_name: str, model: str = None):
    """Prueba un adapter con un test simple."""
    
    print(f"\n{'='*70}")
    print(f"Probando Adapter: {adapter_name.upper()}")
    print(f"{'='*70}\n")
    
    try:
        # Crear adapter
        if adapter_name == "openrouter":
            model = model or "deepseek/deepseek-coder"
            adapter = OpenRouterAdapter(model, temperature=0.2, max_tokens=500)
            
        elif adapter_name == "openai":
            model = model or "gpt-3.5-turbo"  # Usar GPT-3.5 para tests (más barato)
            adapter = OpenAIAdapter(model, temperature=0.2, max_tokens=1000)
            
        elif adapter_name == "anthropic":
            model = model or "claude-3-haiku-20240307"  # Usar Haiku para tests (más barato)
            adapter = AnthropicAdapter(model, temperature=0.2, max_tokens=1000)
            
        elif adapter_name == "huggingface":
            if not model:
                print("❌ Debes especificar --model para HuggingFace")
                print("   Ejemplo: --model 'google/codegemma-2b'")
                return False
            adapter = HuggingFaceAdapter(model, temperature=0.2, max_tokens=500)
            
        elif adapter_name == "ollama":
            model = model or "codellama:7b"
            adapter = OllamaAdapter(model, temperature=0.2, max_tokens=1000)
            
        else:
            print(f"❌ Adapter desconocido: {adapter_name}")
            return False
        
        print(f"✅ Adapter inicializado: {model}\n")
        
        # Prompt simple
        prompt = f"""Refina este test Java para que sea más legible:

{SIMPLE_TEST_CODE}

Instrucciones:
1. Usa nombres de variable descriptivos
2. Añade una aserción más específica
3. Retorna SOLO el código refinado, sin explicaciones.
"""
        
        print("🔄 Generando refinamiento...")
        print("-" * 70)
        
        result = adapter.generate(prompt)
        
        if result['success']:
            print("✅ GENERACIÓN EXITOSA")
            print("-" * 70)
            print("\nCódigo generado:")
            print("-" * 70)
            print(result['code'][:500])  # Primeros 500 chars
            if len(result['code']) > 500:
                print("\n... (truncado)")
            print("-" * 70)
            print(f"\n📊 Tokens usados: {result.get('tokens', 'N/A')}")
            print("\n✅ El adapter funciona correctamente!")
            return True
        else:
            print(f"❌ ERROR: {result.get('error')}")
            return False
            
    except ImportError as e:
        print(f"❌ Falta librería: {e}")
        print(f"\n💡 Instala con:")
        if adapter_name == "openai":
            print("   pip install openai")
        elif adapter_name == "anthropic":
            print("   pip install anthropic")
        elif adapter_name == "huggingface":
            print("   pip install transformers torch accelerate")
        elif adapter_name == "ollama":
            print("   pip install requests")
        return False
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description="Prueba adapters LLM")
    parser.add_argument(
        "--adapter",
        choices=["openrouter", "openai", "anthropic", "huggingface", "ollama"],
        required=True,
        help="Adapter a probar"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Modelo específico (opcional)"
    )
    
    args = parser.parse_args()
    
    success = test_adapter(args.adapter, args.model)
    
    print(f"\n{'='*70}")
    if success:
        print("✅ TEST EXITOSO - El adapter está listo para usar")
        print(f"\n💡 Ahora puedes ejecutar:")
        print(f"   python scripts/pipeline/phase2_llm_refinement.py \\")
        print(f"     --adapter {args.adapter}", end="")
        if args.model:
            print(f" \\")
            print(f"     --model '{args.model}'")
        else:
            print()
    else:
        print("❌ TEST FALLIDO - Revisa los errores arriba")
    print(f"{'='*70}\n")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
