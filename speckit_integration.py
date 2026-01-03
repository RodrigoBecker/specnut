import json
from pathlib import Path
from typing import Optional
from main import SpecDigestGenerator, DigestFormat, DigestCache


class SpecKitDigestIntegration:
    """Integra Spec Digest ao Spec Kit para otimizar constituições"""

    def __init__(self, spec_kit_root: Path = Path(".")):
        self.root = spec_kit_root
        self.specs_dir = spec_kit_root / "specs"
        self.digests_dir = spec_kit_root / ".digests"
        self.cache = DigestCache(spec_kit_root / ".spec_digest_cache")

        self.digests_dir.mkdir(exist_ok=True)

    def build_constitution_digest(self) -> dict:
        """
        Constrói um digest consolidado de toda constituição.
        Útil para incluir em prompts de IA de forma ultra-otimizada.
        """
        constitution_digest = {
            "specs": {},
            "summary": {}
        }

        # Processa cada spec no diretório
        for spec_file in self.specs_dir.glob("*.{yaml,yml,json}"):
            spec_name = spec_file.stem

            try:
                generator = SpecDigestGenerator(spec_file)
                digest = generator.generate(DigestFormat.COMPACT)

                constitution_digest["specs"][spec_name] = digest

                # Calcula tokens economizados
                import json as json_lib
                original_size = len(json_lib.dumps(generator.spec_data).split())
                digest_size = len(json_lib.dumps(digest).split())
                economy = ((original_size - digest_size) / original_size) * 100

                constitution_digest["summary"][spec_name] = {
                    "original_words": original_size,
                    "digest_words": digest_size,
                    "compression": f"{economy:.1f}%"
                }

            except Exception as e:
                print(f"⚠️  Erro ao processar {spec_file}: {e}")

        return constitution_digest

    def generate_constitution_prompt(self) -> str:
        """
        Gera um prompt otimizado com toda a constituição em formato compacto.
        Pronto para incluir em requisições de IA.
        """
        digest = self.build_constitution_digest()

        prompt = """# SISTEMA SPECIFICATION DIGEST
## Especificação ultra-compacta do sistema para otimização de tokens

"""
        for spec_name, spec_data in digest["specs"].items():
            prompt += f"\n### {spec_name}\n"
            prompt += f"```json\n{json.dumps(spec_data, indent=2)}\n```\n"

        # Adiciona summary de economia
        prompt += "\n## RESUMO DE COMPRESSÃO\n"
        for spec_name, stats in digest["summary"].items():
            prompt += f"- **{spec_name}**: {stats['compression']} comprimido\n"

        return prompt

    def generate_ai_context(self, context_type: str = "task") -> str:
        """
        Gera contexto otimizado para diferentes tipos de tarefas de IA.

        Types:
        - task: Para tarefas de desenvolvimento
        - review: Para code review com contexto
        - debug: Para debugging com especificação
        - document: Para documentação automática
        """
        digest = self.build_constitution_digest()

        if context_type == "task":
            return self._context_task(digest)
        elif context_type == "review":
            return self._context_review(digest)
        elif context_type == "debug":
            return self._context_debug(digest)
        elif context_type == "document":
            return self._context_document(digest)

    def _context_task(self, digest: dict) -> str:
        """Contexto para tarefas de desenvolvimento"""
        lines = [
            "# SPECIFICATION CONTEXT FOR DEVELOPMENT TASK",
            "",
            "Use este digest como referência para entender o sistema:",
            ""
        ]

        for spec_name, spec_data in digest["specs"].items():
            lines.append(f"## {spec_name}")

            if "endpoints" in spec_data:
                lines.append("**Endpoints disponíveis:**")
                for endpoint in spec_data["endpoints"][:3]:  # Top 3
                    lines.append(f"- {endpoint}")
                if len(spec_data["endpoints"]) > 3:
                    lines.append(f"- ... e mais {len(spec_data['endpoints']) - 3}")
                lines.append("")

            if "schemas" in spec_data:
                lines.append("**Modelos de dados:**")
                for schema_name, schema_def in spec_data["schemas"].items():
                    lines.append(f"- {schema_name}: {schema_def}")
                lines.append("")

        return "\n".join(lines)

    def _context_review(self, digest: dict) -> str:
        """Contexto para code review"""
        lines = [
            "# CODE REVIEW CONTEXT",
            "",
            "Revise o código contra esta especificação:",
            ""
        ]

        for spec_name, spec_data in digest["specs"].items():
            lines.append(f"## {spec_name} - Validação")

            if "constraints" in spec_data:
                lines.append("**Regras a validar:**")
                for constraint in spec_data.get("constraints", [])[:5]:
                    if isinstance(constraint, dict):
                        lines.append(f"- {list(constraint.values())[0]}")
                    else:
                        lines.append(f"- {constraint}")

        return "\n".join(lines)

    def _context_debug(self, digest: dict) -> str:
        """Contexto para debugging"""
        lines = [
            "# DEBUG CONTEXT",
            "",
            "Referência rápida para debugging:",
            ""
        ]

        for spec_name, spec_data in digest["specs"].items():
            lines.append(f"## {spec_name}")

            if "flows" in spec_data:
                lines.append("**Fluxos esperados:**")
                for flow in spec_data["flows"][:2]:
                    lines.append(f"- {flow}")
                lines.append("")

            if "schemas" in spec_data:
                lines.append("**Estruturas de dados:**")
                for schema_name, schema_def in spec_data["schemas"].items():
                    lines.append(f"- {schema_name}: {schema_def}")

        return "\n".join(lines)

    def _context_document(self, digest: dict) -> str:
        """Contexto para documentação automática"""
        lines = [
            "# SYSTEM DOCUMENTATION",
            "",
        ]

        for spec_name, spec_data in digest["specs"].items():
            version = spec_data.get("version", "1.0.0")
            lines.append(f"## {spec_name} (v{version})")
            lines.append("")

            if "endpoints" in spec_data:
                lines.append("### API Endpoints")
                for endpoint in spec_data["endpoints"]:
                    lines.append(f"- {endpoint}")
                lines.append("")

            if "schemas" in spec_data:
                lines.append("### Data Models")
                for schema_name, schema_def in spec_data["schemas"].items():
                    lines.append(f"- **{schema_name}**: {schema_def}")
                lines.append("")

        return "\n".join(lines)

    def save_digests(self, format_type: DigestFormat = DigestFormat.COMPACT):
        """Salva todos os digests em arquivos"""
        for spec_file in self.specs_dir.glob("*.{yaml,yml,json}"):
            try:
                generator = SpecDigestGenerator(spec_file)
                digest = generator.generate(format_type)

                output_file = self.digests_dir / f"{spec_file.stem}_digest.json"
                with open(output_file, 'w') as f:
                    json.dump(digest, f, indent=2)

                print(f"✅ {spec_file.stem}")
            except Exception as e:
                print(f"❌ {spec_file.stem}: {e}")

    def get_digest_stats(self) -> dict:
        """Retorna estatísticas de compressão"""
        stats = {
            "total_specs": 0,
            "total_compression": 0,
            "average_compression": 0,
            "estimated_token_savings": 0
        }

        compressions = []

        for spec_file in self.specs_dir.glob("*.{yaml,yml,json}"):
            try:
                generator = SpecDigestGenerator(spec_file)
                original_size = len(json.dumps(generator.spec_data).split())
                digest = generator.generate(DigestFormat.COMPACT)
                digest_size = len(json.dumps(digest).split())

                compression = ((original_size - digest_size) / original_size) * 100
                compressions.append(compression)

                stats["total_specs"] += 1
                stats["estimated_token_savings"] += original_size - digest_size

            except:
                pass

        if compressions:
            stats["average_compression"] = sum(compressions) / len(compressions)
            stats["total_compression"] = sum(compressions)

        return stats


# Exemplo de uso
if __name__ == "__main__":
    # Inicializa integração
    integration = SpecKitDigestIntegration(Path("."))

    # 1. Gera digests de todas as specs
    print("🔄 Gerando digests...")
    integration.save_digests()

    # 2. Gera contexto para IA
    print("\n📝 Contexto otimizado para tarefas:")
    task_context = integration.generate_ai_context("task")
    print(task_context[:500] + "...")

    # 3. Mostra estatísticas
    print("\n📊 Estatísticas:")
    stats = integration.get_digest_stats()
    print(f"  Total de specs: {stats['total_specs']}")
    print(f"  Compressão média: {stats['average_compression']:.1f}%")
    print(f"  Tokens economizados: {stats['estimated_token_savings']}")

    # 4. Salva constitution prompt
    print("\n💾 Salvando constitution prompt...")
    constitution = integration.generate_constitution_prompt()
    with open(".constitution_digest.md", "w") as f:
        f.write(constitution)
    print("✅ Salvo em .constitution_digest.md")
