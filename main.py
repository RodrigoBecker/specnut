
import json
import yaml
import argparse
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import hashlib
import re
from dataclasses import dataclass, asdict
from enum import Enum


class DigestFormat(Enum):
    COMPACT = "compact"  # Máxima compressão
    DETAILED = "detailed"  # Menos comprimido
    MARKDOWN = "markdown"  # Legível + estruturado
    JSON = "json"  # Estruturado


@dataclass
class SpecMetadata:
    """Metadados do digest"""
    name: str
    version: str
    generated_at: str
    source_hash: str
    format_version: str = "1.0"
    total_tokens_original: int = 0
    total_tokens_digest: int = 0


class SpecDigestGenerator:
    """Gerador de digests ultra-compactos de specs"""

    def __init__(self, spec_path: str | Path):
        self.spec_path = Path(spec_path)
        self.spec_data = self._load_spec()
        self.source_hash = self._calculate_hash()

    def _load_spec(self) -> Dict[str, Any]:
        """Carrega spec de YAML ou JSON"""
        try:
            if self.spec_path.suffix in ['.yaml', '.yml']:
                with open(self.spec_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            elif self.spec_path.suffix == '.json':
                with open(self.spec_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                raise ValueError(f"Formato não suportado: {self.spec_path.suffix}")
        except Exception as e:
            raise RuntimeError(f"Erro ao carregar spec: {e}")

    def _calculate_hash(self) -> str:
        """Calcula hash do spec para detecção de mudanças"""
        spec_str = json.dumps(self.spec_data, sort_keys=True)
        return hashlib.md5(spec_str.encode()).hexdigest()[:8]

    def _abbreviate(self, text: str, max_length: int = 50) -> str:
        """Abrevia texto mantendo significado"""
        if len(text) <= max_length:
            return text

        # Remove stopwords comuns
        stopwords = ['the', 'a', 'an', 'and', 'or', 'to', 'of', 'in', 'on', 'at', 'by']
        words = text.split()
        abbrev_words = [w for w in words if w.lower() not in stopwords]

        result = ' '.join(abbrev_words)[:max_length]
        return result if result else text[:max_length]

    def _extract_endpoint_compact(self, endpoint: Dict) -> str:
        """Extrai endpoint em formato compacto"""
        method = endpoint.get('method', 'GET').upper()
        path = endpoint.get('path', endpoint.get('url', ''))
        description = endpoint.get('description', '')

        # Formato: METHOD /path → desc
        compact = f"{method} {path}"
        if description:
            compact += f" → {self._abbreviate(description, 30)}"

        return compact

    def _extract_schema_compact(self, schema: Dict) -> str:
        """Extrai schema em formato super compacto"""
        if not schema:
            return ""

        props = schema.get('properties', {})
        required = schema.get('required', [])

        # Formato: field:type (required fields com *)
        field_specs = []
        for field, config in props.items():
            field_type = config.get('type', '?')
            required_mark = "*" if field in required else ""
            field_specs.append(f"{field}:{field_type}{required_mark}")

        return f"[{', '.join(field_specs[:5])}{'...' if len(field_specs) > 5 else ''}]"

    def _process_endpoints(self, endpoints: List[Dict]) -> List[str]:
        """Processa lista de endpoints"""
        return [self._extract_endpoint_compact(ep) for ep in endpoints]

    def _process_schemas(self, schemas: Dict) -> Dict[str, str]:
        """Processa schemas em formato compacto"""
        return {
            name: self._extract_schema_compact(schema)
            for name, schema in schemas.items()
        }

    def generate_compact(self) -> Dict[str, Any]:
        """Gera digest em formato COMPACT (máxima compressão)"""
        digest = {
            "name": self.spec_data.get("name", "unnamed"),
            "version": self.spec_data.get("version", "0.0.0"),
        }

        # Endpoints
        if "endpoints" in self.spec_data:
            digest["endpoints"] = self._process_endpoints(
                self.spec_data["endpoints"]
            )

        # Schemas
        if "schemas" in self.spec_data:
            digest["schemas"] = self._process_schemas(
                self.spec_data["schemas"]
            )

        # Flows/Processos
        if "flows" in self.spec_data:
            digest["flows"] = [
                f"{f.get('id', 'unknown')}: {self._abbreviate(f.get('description', ''), 40)}"
                for f in self.spec_data["flows"]
            ]

        # Constraints/Rules
        if "constraints" in self.spec_data:
            digest["constraints"] = self.spec_data["constraints"]

        return digest

    def generate_detailed(self) -> Dict[str, Any]:
        """Gera digest DETAILED com mais contexto"""
        digest = self.generate_compact()

        # Adiciona contexto
        if "description" in self.spec_data:
            digest["description"] = self.spec_data["description"]

        if "tags" in self.spec_data:
            digest["tags"] = self.spec_data["tags"]

        if "auth" in self.spec_data:
            digest["auth"] = self.spec_data["auth"]

        return digest

    def generate_markdown(self) -> str:
        """Gera digest em formato Markdown legível"""
        lines = []

        # Header
        name = self.spec_data.get("name", "Spec")
        version = self.spec_data.get("version", "0.0.0")
        lines.append(f"# {name} v{version}\n")

        if "description" in self.spec_data:
            lines.append(f"{self.spec_data['description']}\n")

        # Endpoints
        if "endpoints" in self.spec_data:
            lines.append("## Endpoints")
            for endpoint in self.spec_data["endpoints"]:
                compact = self._extract_endpoint_compact(endpoint)
                lines.append(f"- {compact}")
            lines.append("")

        # Schemas
        if "schemas" in self.spec_data:
            lines.append("## Schemas")
            for name, schema in self.spec_data["schemas"].items():
                compact = self._extract_schema_compact(schema)
                lines.append(f"- **{name}**: {compact}")
            lines.append("")

        # Flows
        if "flows" in self.spec_data:
            lines.append("## Flows")
            for flow in self.spec_data["flows"]:
                flow_id = flow.get("id", "unknown")
                flow_desc = flow.get("description", "")
                lines.append(f"- **{flow_id}**: {flow_desc}")
            lines.append("")

        # Constraints
        if "constraints" in self.spec_data:
            lines.append("## Constraints")
            for constraint in self.spec_data["constraints"]:
                lines.append(f"- {constraint}")
            lines.append("")

        return "\n".join(lines)

    def generate(self, format_type: DigestFormat = DigestFormat.COMPACT) -> Any:
        """Interface principal para gerar digest"""
        if format_type == DigestFormat.COMPACT:
            return self.generate_compact()
        elif format_type == DigestFormat.DETAILED:
            return self.generate_detailed()
        elif format_type == DigestFormat.MARKDOWN:
            return self.generate_markdown()
        elif format_type == DigestFormat.JSON:
            return self.generate_compact()

    def get_metadata(self, digest: Dict) -> SpecMetadata:
        """Gera metadados do digest"""
        return SpecMetadata(
            name=self.spec_data.get("name", "unnamed"),
            version=self.spec_data.get("version", "0.0.0"),
            generated_at=datetime.now().isoformat(),
            source_hash=self.source_hash,
        )


class DigestCache:
    """Gerencia cache de digests para evitar reprocessamento"""

    def __init__(self, cache_dir: Path = Path(".spec_digest_cache")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)

    def get_cache_path(self, spec_path: Path, format_type: DigestFormat) -> Path:
        """Calcula caminho do cache"""
        spec_name = spec_path.stem
        return self.cache_dir / f"{spec_name}_{format_type.value}.json"

    def is_valid(self, spec_path: Path, format_type: DigestFormat) -> bool:
        """Verifica se cache é válido comparando hashes"""
        cache_path = self.get_cache_path(spec_path, format_type)
        if not cache_path.exists():
            return False

        try:
            generator = SpecDigestGenerator(spec_path)
            with open(cache_path, 'r') as f:
                cached = json.load(f)
            return cached.get("_hash") == generator.source_hash
        except:
            return False

    def save(self, spec_path: Path, format_type: DigestFormat, digest: Any, source_hash: str):
        """Salva digest em cache"""
        cache_path = self.get_cache_path(spec_path, format_type)

        if isinstance(digest, str):
            content = {"_hash": source_hash, "content": digest}
        else:
            content = {**digest, "_hash": source_hash}

        with open(cache_path, 'w') as f:
            json.dump(content, f, indent=2)

    def load(self, spec_path: Path, format_type: DigestFormat) -> Any:
        """Carrega digest do cache"""
        cache_path = self.get_cache_path(spec_path, format_type)
        with open(cache_path, 'r') as f:
            cached = json.load(f)
        cached.pop("_hash", None)
        return cached


def main():
    parser = argparse.ArgumentParser(
        description="Spec Digest CLI - Resumidor de especificações ultra-compacto",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Gera digest compacto
  spec-digest generate specs/api.yaml

  # Gera em formato markdown
  spec-digest generate specs/api.yaml -f markdown -o digest.md

  # Watch automático com rebuild
  spec-digest watch specs/
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Comando a executar")

    # Comando: generate
    gen_parser = subparsers.add_parser("generate", help="Gera digest de uma spec")
    gen_parser.add_argument("spec", help="Caminho do arquivo spec (YAML/JSON)")
    gen_parser.add_argument(
        "-f", "--format",
        choices=["compact", "detailed", "markdown", "json"],
        default="compact",
        help="Formato de saída (padrão: compact)"
    )
    gen_parser.add_argument(
        "-o", "--output",
        help="Arquivo de saída (opcional, padrão: stdout)"
    )
    gen_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Desabilita cache"
    )

    # Comando: watch
    watch_parser = subparsers.add_parser("watch", help="Monitora specs e regenera digests")
    watch_parser.add_argument("directory", help="Diretório com specs")
    watch_parser.add_argument(
        "-f", "--format",
        choices=["compact", "detailed", "markdown", "json"],
        default="compact",
        help="Formato de saída"
    )

    # Comando: multi
    multi_parser = subparsers.add_parser("multi", help="Gera digests de múltiplas specs")
    multi_parser.add_argument("specs", nargs="+", help="Arquivos specs")
    multi_parser.add_argument(
        "-f", "--format",
        choices=["compact", "detailed", "markdown", "json"],
        default="compact"
    )
    multi_parser.add_argument("-o", "--output-dir", help="Diretório de saída")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cache = DigestCache()

    try:
        if args.command == "generate":
            spec_path = Path(args.spec)
            if not spec_path.exists():
                print(f"❌ Spec não encontrada: {args.spec}")
                return

            format_type = DigestFormat(args.format)

            # Verifica cache
            if not args.no_cache and cache.is_valid(spec_path, format_type):
                print(f"📦 Usando cache para {spec_path.name}")
                digest = cache.load(spec_path, format_type)
            else:
                print(f"🔄 Gerando digest para {spec_path.name}...")
                generator = SpecDigestGenerator(spec_path)
                digest = generator.generate(format_type)
                cache.save(spec_path, format_type, digest, generator.source_hash)

            # Output
            if format_type == DigestFormat.MARKDOWN:
                output = digest
            else:
                output = json.dumps(digest, indent=2)

            if args.output:
                output_path = Path(args.output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w') as f:
                    f.write(output)
                print(f"✅ Digest salvo em: {args.output}")
            else:
                print(output)

        elif args.command == "multi":
            specs = [Path(s) for s in args.specs]
            format_type = DigestFormat(args.format)
            output_dir = Path(args.output_dir) if args.output_dir else Path("./digests")
            output_dir.mkdir(exist_ok=True)

            for spec_path in specs:
                if spec_path.is_dir():
                    specs.extend(spec_path.glob("*.{yaml,yml,json}"))
                    continue

                if not spec_path.exists():
                    print(f"⚠️  Spec não encontrada: {spec_path}")
                    continue

                print(f"🔄 {spec_path.name}...", end=" ")
                generator = SpecDigestGenerator(spec_path)
                digest = generator.generate(format_type)

                output_file = output_dir / f"{spec_path.stem}_digest.{format_type.value}"

                if format_type == DigestFormat.MARKDOWN:
                    content = digest
                else:
                    content = json.dumps(digest, indent=2)

                with open(output_file, 'w') as f:
                    f.write(content)
                print(f"✅")

            print(f"\n✅ Digests salvos em: {output_dir}")

    except Exception as e:
        print(f"❌ Erro: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
