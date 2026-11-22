import re
from pathlib import Path

from macuitest import cli

SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "macuitest"
SKILL_FILE = SKILL_DIR / "SKILL.md"
OPERATING_FILE = SKILL_DIR / "references" / "operating.md"


def _parse_frontmatter(text: str) -> dict[str, str | dict[str, str]]:
    """Parse the YAML frontmatter block of SKILL.md without external dependencies."""
    assert text.startswith("---\n"), "SKILL.md must start with YAML frontmatter"
    _, rest = text.split("---\n", 1)
    raw, _, _ = rest.partition("\n---\n")
    assert raw != rest, "SKILL.md frontmatter is missing a closing --- delimiter"

    fields: dict[str, str | dict[str, str]] = {}
    current_map: dict[str, str] | None = None
    for line in raw.splitlines():
        if not line.strip():
            continue
        if line.startswith("  "):
            assert current_map is not None, f"Unexpected indented line: {line!r}"
            key, value = _split_kv(line.strip())
            current_map[key] = value
        else:
            key, value = _split_kv(line)
            if value == "":
                current_map = {}
                fields[key] = current_map
            else:
                current_map = None
                fields[key] = value
    return fields


def _split_kv(line: str) -> tuple[str, str]:
    key, sep, raw_value = line.partition(":")
    assert sep == ":", f"Invalid frontmatter line: {line!r}"
    value = raw_value.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return key.strip(), value[1:-1]
    assert ": " not in value, f"Unquoted ': ' in frontmatter value for {key.strip()!r}"
    return key.strip(), value


def test_skill_frontmatter_follows_spec():
    fields = _parse_frontmatter(SKILL_FILE.read_text(encoding="utf-8"))

    name = fields["name"]
    assert isinstance(name, str)
    assert name == SKILL_DIR.name
    assert re.fullmatch(r"[a-z0-9-]+", name)
    assert len(name) <= 64

    description = fields["description"]
    assert isinstance(description, str)
    assert 0 < len(description) <= 1024

    compatibility = fields["compatibility"]
    assert isinstance(compatibility, str)
    assert 0 < len(compatibility) <= 500

    assert fields["license"] == "MIT"

    metadata = fields["metadata"]
    assert isinstance(metadata, dict)
    assert metadata.get("author")
    assert metadata.get("repository") == "https://github.com/andriykislitsyn/macuitest"


def test_skill_reference_files_exist():
    body = SKILL_FILE.read_text(encoding="utf-8")
    refs = re.findall(r"`(references/[a-zA-Z0-9._-]+\.md)`", body)

    assert refs, "SKILL.md should link to its reference files"
    for ref in refs:
        assert (SKILL_DIR / ref).is_file(), f"Missing skill reference file: {ref}"


def test_operating_reference_documents_every_cli_verb():
    content = OPERATING_FILE.read_text(encoding="utf-8")
    verbs = set(cli.VERBS) | set(cli.APP_VERBS)

    missing = sorted(verb for verb in verbs if f"| `{verb}` |" not in content)
    assert not missing, f"CLI verbs missing from references/operating.md: {missing}"
