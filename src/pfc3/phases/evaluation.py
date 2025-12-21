import json
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional
from ..core.config import cfg
from ..core.loader import loader
from ..core.runner import runner
from ..utils.code_metrics import CodeMetricsAnalyzer

class EvaluationPhase:
    """Phase 4: Evaluate metrics."""
    
    def __init__(self):
        self.code_analyzer = CodeMetricsAnalyzer()
    
    def run(self) -> Dict:
        valid_file = cfg.base_dir / "generated_tests/validated/T_valid_results.json"
        if not valid_file.exists():
            print("❌ T_valid not found")
            return {"success": False}
            
        with open(valid_file) as f:
            valid_results = json.load(f)
            
        verified = [r for r in valid_results if r.get('verified')]
        metrics = []
        
        print(f"Phase 4: Evaluating {len(verified)} tests")
        
        for i, item in enumerate(verified, 1):
            project_name = item['project']
            class_name = item['class']
            
            print(f"[{i}/{len(verified)}] {class_name}")
            
            project = loader.get_project(project_name)
            if not project: continue
            sut_jar = project.jar_files[0]
            
            refined_path = Path(item['refined_file'])
            
            # Measure
            m = self._measure_metrics(refined_path, sut_jar, class_name, project.path)
            metrics.append({
                "project": project_name,
                "class": class_name,
                **m
            })
            
        # Save
        out_file = cfg.base_dir / "evaluation_results/final_evaluation.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, 'w') as f:
            json.dump(metrics, f, indent=2)
            
        return {"success": True, "count": len(metrics)}
        
    def _measure_metrics(self, test_path: Path, sut_jar: Path, class_name: str, project_path: Path) -> Dict:
        metrics = {
            "compilation_rate": 1.0, # If we are here, it compiled in validation phase
            "line_coverage": 0.0,
            "branch_coverage": 0.0,
            "mutation_score": 0.0,
            "failure_reproduction_rate": 0.0 # Placeholder, hard to measure without known bugs
        }

        # 1. Code Metrics (CUT)
        # Try to find source file
        source_file = self._find_source_file(project_path, class_name)
        if source_file:
            code_metrics = self.code_analyzer.analyze(source_file)
            metrics.update(code_metrics)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            
            # Find scaffolding (Required for compilation)
            scaffolding = list(test_path.parent.glob("*_scaffolding.java"))
            files_to_compile = [test_path] + scaffolding
            
            # Compile Test + Scaffolding
            cp = f"{sut_jar}:{cfg.junit_jar}:{cfg.evosuite_jar}:{cfg.hamcrest_jar}:{test_path.parent}"
            res = runner.run_javac(cp, files_to_compile, out_dir)
            if res.returncode != 0:
                print(f"  ❌ Compilation Error: {res.stderr[:200]}...") # Log first 200 chars
                metrics["compilation_rate"] = 0.0
                return metrics

            test_class = class_name + "_ESTest"
            
            # 2. Coverage (JaCoCo)
            exec_file = out_dir / "jacoco.exec"
            # We need the SUT classes in a directory for JaCoCo report, or we can point to the JAR?
            # JaCoCo report needs class files. JAR is fine.
            # But we also need source files for source highlighting, though strictly for metrics XML is enough without source.
            
            # Offline Instrumentation Strategy
            # 1. Extract SUT classes
            classes_dir = out_dir / "classes"
            classes_dir.mkdir()
            runner.run_cmd(["unzip", "-q", str(sut_jar), "-d", str(classes_dir)])
            
            # 2. Instrument classes
            instr_dir = out_dir / "instr"
            instr_dir.mkdir()
            res_instr = runner.instrument_classes(classes_dir, instr_dir)
            if res_instr.returncode != 0:
                print(f"❌ Instrumentation failed: {res_instr.stderr}")
            
            # 3. Prepare classpath for execution
            # Order: Instrumented Classes -> Original Classes (resources) -> Test Classes -> Dependencies -> Agent JAR (required for offline)
            run_cp = f"{instr_dir}:{classes_dir}:{out_dir}:{cfg.junit_jar}:{cfg.evosuite_jar}:{cfg.hamcrest_jar}:{cfg.jacoco_agent_jar}"
            
            # 4. Run Test
            exec_file = out_dir / "jacoco.exec"
            res_run = runner.run_with_jacoco_offline(run_cp, test_class, exec_file)
            
            if res_run.returncode != 0:
                 print(f"❌ Test execution failed: {res_run.stderr}")
                 # Debug stdout too
                 print(f"Stdout: {res_run.stdout[:200]}...")
            
            if exec_file.exists():
                report_dir = out_dir / "report"
                report_dir.mkdir()
                
                # 5. Report (using original classes)
                res_rep = runner.generate_jacoco_report(exec_file, classes_dir, project_path, report_dir)
                if res_rep.returncode != 0:
                    print(f"❌ Report gen failed: {res_rep.stderr}")
                
                xml_file = report_dir / "jacoco.xml"
                if xml_file.exists():
                    cov = self._parse_jacoco(xml_file, class_name)

            # 3. Mutation (PIT)
            # PIT needs source dirs to show code, but for metrics maybe not strictly required if we just want numbers?
            # Actually PIT usually requires source dirs to locate the code to mutate if we want line numbers, 
            # but it operates on bytecode.
            pit_report_dir = out_dir / "pit_report"
            
            # Classpath for PIT: SUT + Test + JUnit + Hamcrest
            pit_cp = f"{out_dir}:{sut_jar}:{cfg.junit_jar}:{cfg.evosuite_jar}:{cfg.hamcrest_jar}"
            
            # We assume source dir is 'src/main/java' or similar if we can find it, else project root
            src_dir = str(project_path)
            if (project_path / "src/main/java").exists():
                src_dir = str(project_path / "src/main/java")
                
            runner.run_pitest(
                pit_cp,
                class_name,
                test_class,
                src_dir,
                pit_report_dir
            )
            
            # Parse PIT report (mutations.xml)
            # PIT creates a subdir with timestamp or just index.html? 
            # CLI outputFormats XML creates mutations.xml in the report dir.
            pit_xml = pit_report_dir / "mutations.xml"
            if pit_xml.exists():
                metrics["mutation_score"] = self._parse_pit(pit_xml)

        return metrics

    def _find_source_file(self, project_path: Path, class_name: str) -> Optional[Path]:
        # Convert package.Class to package/Class.java
        rel_path = class_name.replace('.', '/') + ".java"
        
        # Search common source roots
        common_roots = ["src/main/java", "src", "source", "."]
        for root in common_roots:
            p = project_path / root / rel_path
            if p.exists():
                return p
        
        # Fallback: glob search
        matches = list(project_path.rglob(f"{class_name.split('.')[-1]}.java"))
        if matches:
            return matches[0]
            
        return None

    def _parse_jacoco(self, xml_file: Path, target_class: str) -> Dict[str, float]:
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Convert target.class.Name to target/class/Name
            target_path = target_class.replace('.', '/')
            
            counters = {"LINE": {"covered": 0, "missed": 0}, "BRANCH": {"covered": 0, "missed": 0}}
            found = False
            
            # Find specific class element
            # Structure: package > class > counter
            for cls_node in root.findall(".//class"):
                name = cls_node.get("name")
                
                # Check for exact match or inner class match (e.g. Class$1)
                if name == target_path or name.startswith(target_path + "$"):
                    found = True
                    for counter in cls_node.findall("counter"):
                        type_ = counter.get("type")
                        if type_ not in counters:
                            counters[type_] = {"covered": 0, "missed": 0}
                        
                        counters[type_]["covered"] += int(counter.get("covered", 0))
                        counters[type_]["missed"] += int(counter.get("missed", 0))
            
            if not found:
                 # Debug: list available to see why we missed
                 available = [c.get("name") for c in root.findall(".//class")]
                 print(f"⚠️  JaCoCo mismatch: Expected '{target_path}', Found: {available[:5]}...")
            
            def calc(c):
                total = c["covered"] + c["missed"]
                return (c["covered"] / total * 100) if total > 0 else 0.0
            
            # Use INSTRUCTION if LINE is missing (common in release builds)
            line_cov = calc(counters.get("LINE", {"covered": 0, "missed": 0}))
            instr_cov = calc(counters.get("INSTRUCTION", {"covered": 0, "missed": 0}))
            
            # Prefer LINE, but take INSTRUCTION if LINE is 0 and INSTRUCTION > 0
            final_cov = line_cov if line_cov > 0 else instr_cov
            
            return {
                "line_coverage": final_cov,
                "branch_coverage": calc(counters.get("BRANCH", {"covered": 0, "missed": 0})),
                "instruction_coverage": instr_cov,
                "method_coverage": calc(counters.get("METHOD", {"covered": 0, "missed": 0}))
            }
        except Exception as e:
            print(f"Error parsing JaCoCo: {e}")
            return {}

    def _parse_pit(self, xml_file: Path) -> float:
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            mutations = root.findall("mutation")
            total = len(mutations)
            killed = sum(1 for m in mutations if m.get("status") == "KILLED")
            
            return (killed / total * 100) if total > 0 else 0.0
        except Exception as e:
            print(f"Error parsing PIT: {e}")
            return 0.0
