import re
from pathlib import Path
from typing import Dict, List, Set

class CodeMetricsAnalyzer:
    """Analyzes Java source code to extract static metrics."""

    def analyze(self, source_path: Path) -> Dict[str, int]:
        if not source_path.exists():
            return {}

        with open(source_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.splitlines()

        metrics = {
            "sloc": 0,
            "cyclomatic_complexity": 1, # Base complexity is 1
            "internal_dependencies": 0,
            "external_dependencies": 0,
            "std_lib_dependencies": 0,
            "comment_lines": 0,
            "javadoc_lines": 0,
            "switch_conditions": 0,
            "static_calls": 0,
            "std_lib_calls": 0,
            "type_checks": 0,
            "null_checks": 0,
            "string_ops": 0,
            "primitive_conditions": 0,
            "collections_usage": 0
        }

        self._count_lines_and_comments(lines, metrics)
        self._analyze_complexity_and_branches(content, metrics)
        self._analyze_dependencies(lines, metrics)
        self._analyze_readability(content, metrics)

        return metrics

    def _count_lines_and_comments(self, lines: List[str], metrics: Dict[str, int]):
        in_block_comment = False
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Comments
            if in_block_comment:
                metrics["comment_lines"] += 1
                if "*/" in stripped:
                    in_block_comment = False
                continue
            
            if stripped.startswith("/*"):
                metrics["comment_lines"] += 1
                if "/**" in stripped:
                    metrics["javadoc_lines"] += 1
                if "*/" not in stripped:
                    in_block_comment = True
                continue
                
            if stripped.startswith("//"):
                metrics["comment_lines"] += 1
                continue

            # SLOC (if not a comment line)
            metrics["sloc"] += 1

    def _analyze_complexity_and_branches(self, content: str, metrics: Dict[str, int]):
        # Cyclomatic Complexity keywords
        complexity_patterns = [
            r'\bif\b', r'\bfor\b', r'\bwhile\b', r'\bcase\b', r'\bcatch\b', 
            r'&&', r'\|\|', r'\?'
        ]
        
        for pattern in complexity_patterns:
            count = len(re.findall(pattern, content))
            metrics["cyclomatic_complexity"] += count

        # Branch Types
        metrics["switch_conditions"] = len(re.findall(r'\bswitch\b', content))
        metrics["static_calls"] = len(re.findall(r'\b[A-Z][a-zA-Z0-9_]*\.[a-zA-Z0-9_]+\(', content))
        metrics["type_checks"] = len(re.findall(r'\binstanceof\b', content))
        metrics["null_checks"] = len(re.findall(r'==\s*null|!=\s*null', content))
        metrics["string_ops"] = len(re.findall(r'\.length\(\)|\.substring\(|\.indexOf\(|\.equals\(', content))
        
        # Primitive conditions (heuristic: simple comparisons not involving null)
        metrics["primitive_conditions"] = len(re.findall(r'[a-zA-Z0-9_]+\s*(==|!=|<|>|<=|>=)\s*[0-9]+', content))

        # Collections usage
        metrics["collections_usage"] = len(re.findall(r'\b(List|Set|Map|Collection|ArrayList|HashSet|HashMap)\b', content))

    def _analyze_dependencies(self, lines: List[str], metrics: Dict[str, int]):
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("import "):
                match = re.match(r'import\s+([a-zA-Z0-9_.]+);', stripped)
                if match:
                    pkg = match.group(1)
                    if pkg.startswith("java.") or pkg.startswith("javax."):
                        metrics["std_lib_dependencies"] += 1
                        metrics["std_lib_calls"] += 1 # Rough proxy for usage
                    elif pkg.startswith("org.junit") or pkg.startswith("org.evosuite"):
                        # Test dependencies, usually external but specific
                        metrics["external_dependencies"] += 1
                    else:
                        # Heuristic: if it matches the project package it's internal, else external
                        # Without project context, we'll assume common prefixes are external
                            # Default to internal for unknown, or we could refine this if we knew the project package
                            metrics["internal_dependencies"] += 1

    def _analyze_readability(self, content: str, metrics: Dict[str, int]):
        """
        Calculate simple readability metrics.
        - Identifier Length: Average length of identifiers
        - Nesting Depth: Max indentation level (proxy)
        """
        # Identifier Length
        # Find all words that look like identifiers
        identifiers = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content)
        # Filter out keywords
        keywords = {
            'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default', 'break', 'continue', 'return',
            'try', 'catch', 'finally', 'throw', 'throws', 'public', 'protected', 'private', 'static', 'final',
            'void', 'int', 'double', 'float', 'boolean', 'char', 'byte', 'short', 'long', 'class', 'interface',
            'enum', 'extends', 'implements', 'new', 'this', 'super', 'import', 'package', 'true', 'false', 'null'
        }
        identifiers = [id for id in identifiers if id not in keywords]
        
        if identifiers:
            avg_len = sum(len(id) for id in identifiers) / len(identifiers)
            metrics["avg_identifier_length"] = avg_len
        else:
            metrics["avg_identifier_length"] = 0

        # Nesting Depth (Proxy: max indentation / 4)
        max_indent = 0
        for line in content.splitlines():
            stripped = line.lstrip()
            if not stripped: continue
            indent = len(line) - len(stripped)
            max_indent = max(max_indent, indent)
            
        metrics["max_nesting_depth"] = max_indent // 4

