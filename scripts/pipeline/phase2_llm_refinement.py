#!/usr/bin/env python3
"""
PASO 2: Refinamiento con LLM

Toma los tests de T_base y los refina con LLM para crear T_refined.

Este script soporta múltiples adapters:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- HuggingFace (CodeGemma, CodeLlama, StarCoder, etc.)
- Local (Ollama, LM Studio)

Uso:
  python phase2_llm_refinement.py --adapter openai
  python phase2_llm_refinement.py --adapter huggingface --model "user/codegemma-finetuned"
  python phase2_llm_refinement.py --adapter anthropic
"""

import json
from pathlib import Path
from typing import Optional, Dict
import time
import argparse
import shutil


# ============================================================================
# ADAPTERS LLM
# ============================================================================

class BaseLLMAdapter:
    """Interfaz base para todos los adapters."""
    
    def __init__(self, model: str, **kwargs):
        self.model = model
        self.kwargs = kwargs
    
    def generate(self, prompt: str) -> Dict:
        """Genera respuesta del LLM."""
        raise NotImplementedError


class OpenAIAdapter(BaseLLMAdapter):
    """Adapter para OpenAI (GPT-4, GPT-3.5)."""
    
    def __init__(self, model: str = "gpt-4", **kwargs):
        super().__init__(model, **kwargs)
        try:
            import openai
            self.client = openai.OpenAI()  # Lee de OPENAI_API_KEY env
        except ImportError:
            raise RuntimeError("pip install openai")
    
    def generate(self, prompt: str) -> Dict:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.kwargs.get('temperature', 0.2),
                max_tokens=self.kwargs.get('max_tokens', 4000)
            )
            
            return {
                "success": True,
                "code": response.choices[0].message.content,
                "tokens": response.usage.total_tokens
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class AnthropicAdapter(BaseLLMAdapter):
    """Adapter para Anthropic (Claude)."""
    
    def __init__(self, model: str = "claude-3-sonnet-20240229", **kwargs):
        super().__init__(model, **kwargs)
        try:
            import anthropic
            self.client = anthropic.Anthropic()  # Lee de ANTHROPIC_API_KEY env
        except ImportError:
            raise RuntimeError("pip install anthropic")
    
    def generate(self, prompt: str) -> Dict:
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.kwargs.get('max_tokens', 4000),
                messages=[{"role": "user", "content": prompt}]
            )
            
            return {
                "success": True,
                "code": response.content[0].text,
                "tokens": response.usage.input_tokens + response.usage.output_tokens
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class HuggingFaceAdapter(BaseLLMAdapter):
    """
    Adapter para modelos de HuggingFace.
    Soporta CodeGemma, CodeLlama, StarCoder, etc.
    
    Uso:
      HuggingFaceAdapter("codellama/CodeLlama-7b-Instruct-hf")
      HuggingFaceAdapter("google/codegemma-7b-it")
      HuggingFaceAdapter("user/codegemma-finetuned")  # Tu modelo finetuneado
    """
    
    def __init__(self, model: str, **kwargs):
        super().__init__(model, **kwargs)
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            print(f"🔄 Cargando modelo de HuggingFace: {model}")
            
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.tokenizer = AutoTokenizer.from_pretrained(model)
            self.model_hf = AutoModelForCausalLM.from_pretrained(
                model,
                device_map="auto",
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                **kwargs
            )
            
            print(f"✅ Modelo cargado en {self.device}")
            
        except ImportError:
            raise RuntimeError("pip install transformers torch")
    
    def generate(self, prompt: str) -> Dict:
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            
            outputs = self.model_hf.generate(
                **inputs,
                max_new_tokens=self.kwargs.get('max_tokens', 2048),
                temperature=self.kwargs.get('temperature', 0.2),
                do_sample=True,
                top_p=0.95,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            generated = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extraer solo la respuesta (después del prompt)
            if prompt in generated:
                code = generated[len(prompt):].strip()
            else:
                code = generated
            
            return {
                "success": True,
                "code": code,
                "tokens": len(inputs['input_ids'][0]) + len(outputs[0])
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class OllamaAdapter(BaseLLMAdapter):
    """
    Adapter para Ollama (LLMs locales).
    
    Uso:
      OllamaAdapter("codellama:13b")
      OllamaAdapter("deepseek-coder:6.7b")
    """
    
    def __init__(self, model: str = "codellama:13b", **kwargs):
        super().__init__(model, **kwargs)
        self.base_url = kwargs.get('base_url', 'http://localhost:11434')
    
    def generate(self, prompt: str) -> Dict:
        try:
            import requests
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.kwargs.get('temperature', 0.2),
                        "num_predict": self.kwargs.get('max_tokens', 2048)
                    }
                }
            )
            
            result = response.json()
            
            return {
                "success": True,
                "code": result['response'],
                "tokens": result.get('eval_count', 0)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class OpenRouterAdapter(BaseLLMAdapter):
    """
    Adapter para OpenRouter (acceso a múltiples modelos).
    
    OpenRouter te da acceso a GPT-4, Claude, Llama, Gemini, etc. con una sola API key.
    
    Uso:
      OpenRouterAdapter("anthropic/claude-3-sonnet")
      OpenRouterAdapter("google/gemini-pro-1.5")
      OpenRouterAdapter("meta-llama/llama-3-70b-instruct")
      OpenRouterAdapter("deepseek/deepseek-coder-33b-instruct")
    
    Setup:
      export OPENROUTER_API_KEY="sk-or-..."
    
    Ver modelos disponibles: https://openrouter.ai/models
    """
    
    def __init__(self, model: str = "meta-llama/llama-3-8b-instruct", **kwargs):
        super().__init__(model, **kwargs)
        try:
            import os
            self.api_key = os.getenv('OPENROUTER_API_KEY')
            if not self.api_key:
                raise RuntimeError("Set OPENROUTER_API_KEY environment variable")
        except ImportError:
            raise RuntimeError("pip install requests")
    
    def generate(self, prompt: str) -> Dict:
        try:
            import requests
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://github.com/croko22/pfc3_tesis",  # Opcional
                    "X-Title": "Test Refinement Research"  # Opcional
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": self.kwargs.get('temperature', 0.2),
                    "max_tokens": self.kwargs.get('max_tokens', 8000)  # AUMENTADO para no cortar código
                }
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
            
            result = response.json()
            
            return {
                "success": True,
                "code": result['choices'][0]['message']['content'],
                "tokens": result['usage']['total_tokens']
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================================
# LLM REFINER
# ============================================================================

class LLMRefiner:
    """
    Clase para refinar tests con LLM.
    Soporta múltiples adapters.
    """
    
    def __init__(self, adapter: str = "openrouter", model: str = None, **kwargs):
        """
        Args:
            adapter: "openrouter", "openai", "anthropic", "huggingface", "ollama"
            model: Nombre del modelo específico
            **kwargs: Parámetros adicionales para el adapter
        """
        
        # Guardar configuración
        self.adapter_name = adapter
        self.model_name = model
        
        # Crear adapter
        if adapter == "openrouter":
            model = model or "meta-llama/llama-3-8b-instruct"  # Default GRATIS
            self.adapter = OpenRouterAdapter(model, **kwargs)
            
        elif adapter == "openai":
            model = model or "gpt-4"
            self.adapter = OpenAIAdapter(model, **kwargs)
            
        elif adapter == "anthropic":
            model = model or "claude-3-sonnet-20240229"
            self.adapter = AnthropicAdapter(model, **kwargs)
            
        elif adapter == "huggingface":
            if not model:
                raise ValueError("Debes especificar --model para HuggingFace")
            self.adapter = HuggingFaceAdapter(model, **kwargs)
            
        elif adapter == "ollama":
            model = model or "codellama:13b"
            self.adapter = OllamaAdapter(model, **kwargs)
            
        else:
            raise ValueError(f"Adapter desconocido: {adapter}")
        
        # Guardar modelo final (puede ser diferente si se usó default)
        self.model_name = model
        
        print(f"✅ LLM Adapter: {adapter} ({model})")
    
    def build_prompt(self, test_code: str, sut_code: Optional[str] = None) -> str:
        """
        Construye el prompt para el LLM.
        Este es TU "secret sauce" - el prompt engineering.
        """
        
        prompt = f"""You are an expert software testing engineer specializing in test refactoring.
Refine this EvoSuite-generated test to be CONCISE, CLEAN, and READABLE.

ORIGINAL TEST:
```java
{test_code}
```

"""
        
        if sut_code:
            prompt += f"""
SYSTEM UNDER TEST:
```java
{sut_code}
```

"""
        
        prompt += """
CRITICAL REFACTORING RULES:

1. **ELIMINATE REDUNDANCY**:
   - Remove duplicate assertions (e.g., checking same thing before and after method call)
   - Remove obvious assertions (e.g., assertNotNull after new Object())
   - Remove state checks that don't relate to test purpose
   
   BAD (redundant):
   ```java
   Object obj = new Object();
   assertNotNull(obj);  // ← DELETE: obviously not null
   assertTrue(obj.isSomething());
   assertNotNull(obj);  // ← DELETE: duplicate
   ```
   
   GOOD (concise):
   ```java
   Object obj = new Object();
   assertTrue(obj.isSomething());
   ```

2. **USE MEANINGFUL NAMES**:
   - Replace var0, var1 → calculator, result, expected
   - Rename test methods: test0 → testAddReturnsSum
   
3. **REMOVE IRRELEVANT ASSERTIONS**:
   - Focus ONLY on behavior being tested
   - Delete: focus-related, layout-related checks (unless that's what test is for)
   - Keep: business logic, exceptions, return values
   
   BAD (too many irrelevant checks):
   ```java
   GUI gui = new GUI();
   assertTrue(gui.getFocusTraversalKeysEnabled());  // ← DELETE
   assertFalse(gui.isFocusCycleRoot());             // ← DELETE
   assertFalse(gui.isFocusTraversalPolicySet());    // ← DELETE
   gui.someMethod();
   assertTrue(gui.getFocusTraversalKeysEnabled());  // ← DELETE
   ```
   
   GOOD (only test what matters):
   ```java
   GUI gui = new GUI();
   gui.someMethod();
   // Test actual behavior, not default GUI state
   ```

4. **ADD DESCRIPTIVE COMMENTS** (optional):
   - Only if test intent is not obvious
   - Explain WHAT is tested, not HOW
   
5. **PRESERVE BEHAVIOR**:
   - Keep same @Test methods
   - Keep same expected exceptions (try/catch blocks)
   - Don't change test logic, only clean it up
   - KEEP all imports (especially org.evosuite.runtime.*)
   - KEEP @RunWith annotation and scaffolding class extension

BEFORE/AFTER EXAMPLE:

BEFORE (EvoSuite verbose):
```java
@Test
public void test0() throws Throwable {
    jgaapGUI gui0 = new jgaapGUI();
    assertNotNull(gui0);
    assertTrue(gui0.getFocusTraversalKeysEnabled());
    assertFalse(gui0.isFocusCycleRoot());
    assertFalse(gui0.isFocusTraversalPolicySet());
    
    ActionMap map0 = gui0.getActionMap();
    assertNotNull(map0);
    assertTrue(gui0.getFocusTraversalKeysEnabled());
    assertFalse(gui0.isFocusCycleRoot());
    
    ActionEvent event0 = new ActionEvent(map0, 0, "demo");
    assertEquals(0, event0.getID());
    assertEquals("demo", event0.getActionCommand());
    
    gui0.actionPerformed(event0);
    assertEquals(0, event0.getID());
    assertEquals("demo", event0.getActionCommand());
}
```

AFTER (refined):
```java
@Test
public void testActionPerformedWithDemoCommand() throws Throwable {
    jgaapGUI gui = new jgaapGUI();
    ActionMap actionMap = gui.getActionMap();
    ActionEvent event = new ActionEvent(actionMap, 0, "demo");
    
    // Test that demo action is handled without exceptions
    gui.actionPerformed(event);
    
    assertEquals("Action command should be preserved", "demo", event.getActionCommand());
}
```

OUTPUT FORMAT:
Return ONLY the complete refined Java test class code.
DO NOT include:
- Markdown fences (```java or ```)
- Explanations before or after the code
- Comments like "Here is the refined class"
- Any text that is not Java code

Your response must START with either:
- import statements, OR
- @RunWith annotation, OR
- package declaration

Example of CORRECT output format:
import org.junit.Test;
import static org.junit.Assert.*;

@RunWith(EvoRunner.class)
public class MyTest_ESTest {
    @Test
    public void testSomething() {
        // test code
    }
}

INCORRECT output (DO NOT DO THIS):
Here is the refined code:
```java
import org.junit.Test;
...
```

START YOUR RESPONSE IMMEDIATELY WITH JAVA CODE."""
        
        return prompt
    
    def clean_llm_output(self, code: str) -> str:
        """
        Limpia el output del LLM, eliminando markdown y texto extra.
        
        Los LLMs a veces ignoran las instrucciones y agregan:
        - "Here is the refined code:"
        - ```java ... ```
        - Explicaciones después del código
        """
        
        # Eliminar líneas antes del código Java
        lines = code.split('\n')
        
        # Buscar el inicio del código Java (primera línea que empieza con import, package, o @)
        start_idx = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('import ') or \
               stripped.startswith('package ') or \
               stripped.startswith('@') or \
               stripped.startswith('public ') or \
               stripped.startswith('class '):
                start_idx = i
                break
        
        # Eliminar markdown fences
        if start_idx > 0:
            # Hay texto antes - probablemente "Here is..." o "```java"
            lines = lines[start_idx:]
        
        # Eliminar ``` al inicio si quedó
        if lines and lines[0].strip().startswith('```'):
            lines = lines[1:]
        
        # Buscar el final (última línea con código real)
        end_idx = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            stripped = lines[i].strip()
            if stripped and not stripped.startswith('```') and stripped != 'java':
                end_idx = i + 1
                break
        
        lines = lines[:end_idx]
        
        # Reconstruir
        cleaned = '\n'.join(lines)
        
        return cleaned
    
    def refine_test(self, test_code: str, sut_code: Optional[str] = None) -> dict:
        """
        Refina un test usando LLM.
        
        Returns:
            dict con 'refined_code', 'success', etc.
        """
        
        prompt = self.build_prompt(test_code, sut_code)
        
        # Llamar al adapter
        result = self.adapter.generate(prompt)
        
        if result['success']:
            # Limpiar output (eliminar markdown, texto extra)
            cleaned_code = self.clean_llm_output(result['code'])
            
            return {
                "success": True,
                "refined_code": cleaned_code,
                "tokens_used": result.get('tokens', 0),
                "model": self.model_name
            }
        else:
            return {
                "success": False,
                "error": result.get('error', 'Unknown error')
            }


def load_test_file(test_path: Path) -> str:
    """Lee un archivo de test."""
    with open(test_path, 'r') as f:
        return f.read()


def main():
    """
    FASE 2: Refinamiento con LLM
    """
    
    # Argumentos CLI
    parser = argparse.ArgumentParser(description="Fase 2: Refinamiento con LLM")
    parser.add_argument(
        "--adapter",
        choices=["openrouter", "openai", "anthropic", "huggingface", "ollama"],
        default="openrouter",
        help="Adapter LLM a usar (default: openrouter)"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Modelo específico (ej: anthropic/claude-3-sonnet, google/gemini-pro-1.5)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Temperatura para generación (0.0-1.0)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=4000,
        help="Máximo de tokens a generar"
    )
    
    args = parser.parse_args()
    
    print("="*80)
    print("FASE 2: REFINAMIENTO CON LLM (T_base → T_refined)")
    print("="*80)
    print()
    
    # Cargar resultados de Fase 1
    baseline_results_file = Path("generated_tests/baseline/T_base_results.json")
    
    if not baseline_results_file.exists():
        print("❌ No se encuentra T_base_results.json")
        print("   Ejecuta primero: python phase1_generate_baseline.py")
        return 1
    
    with open(baseline_results_file) as f:
        baseline_results = json.load(f)
    
    # Filtrar solo exitosos
    successful = [r for r in baseline_results if r.get('success')]
    print(f"📊 Tests en T_base: {len(successful)}")
    print()
    
    # Inicializar LLM refiner con adapter especificado
    try:
        refiner = LLMRefiner(
            adapter=args.adapter,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens
        )
    except Exception as e:
        print(f"❌ Error inicializando LLM adapter: {e}")
        return 1
    
    # Procesar cada test
    refined_results = []
    success_count = 0
    
    for i, baseline in enumerate(successful, 1):
        project = baseline['project']
        class_name = baseline['class']
        
        print(f"\n[{i}/{len(successful)}] {class_name}")
        print("-" * 60)
        
        # Leer test files de T_base
        for test_file_path in baseline.get('test_files', []):
            test_path = Path(test_file_path)
            
            if not test_path.exists():
                print(f"⚠️  Test no encontrado: {test_path}")
                continue
            
            print(f"📄 {test_path.name}")
            
            # Leer código del test
            test_code = load_test_file(test_path)
            
            # TODO: Opcionalmente cargar el SUT (Subject Under Test)
            # sut_code = load_sut(project, class_name)
            sut_code = None
            
            # Refinar con LLM
            result = refiner.refine_test(test_code, sut_code)
            
            if result['success']:
                # Guardar test refinado
                refined_dir = Path("generated_tests/refined") / project / class_name.replace(".", "_")
                refined_dir.mkdir(parents=True, exist_ok=True)
                
                refined_path = refined_dir / test_path.name
                with open(refined_path, 'w') as f:
                    f.write(result['refined_code'])
                
                # Copiar archivos scaffolding del baseline
                baseline_dir = test_path.parent
                for scaff_file in baseline_dir.rglob("*_scaffolding.java"):
                    # Copiar manteniendo estructura de paquetes
                    rel_path = scaff_file.relative_to(baseline_dir)
                    dest_scaff = refined_dir / rel_path
                    dest_scaff.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(scaff_file, dest_scaff)
                
                print(f"   ✅ Refinado y guardado")
                success_count += 1
                
                refined_results.append({
                    "project": project,
                    "class": class_name,
                    "original_file": str(test_path),
                    "refined_file": str(refined_path),
                    "success": True,
                    "tokens_used": result.get('tokens_used', 0)
                })
            else:
                print(f"   ❌ Error: {result.get('error')}")
                refined_results.append({
                    "project": project,
                    "class": class_name,
                    "original_file": str(test_path),
                    "success": False,
                    "error": result.get('error')
                })
    
    # Guardar resultados
    output_file = Path("generated_tests/refined/T_refined_results.json")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(refined_results, f, indent=2)
    
    # Resumen
    print("\n" + "="*80)
    print("RESUMEN - FASE 2")
    print("="*80)
    print(f"Tests procesados: {len(successful)}")
    print(f"Refinados exitosamente: {success_count}")
    print(f"\n📁 Tests refinados en: generated_tests/refined/")
    print(f"📄 Resultados en: {output_file}")
    print("\n✅ T_refined generado. Listo para FASE 3 (Verificación).")
    print("="*80)


if __name__ == "__main__":
    import sys
    sys.exit(main())
