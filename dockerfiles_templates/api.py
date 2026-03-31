"""Reusable API for reading and filtering templates.yml."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import ruamel.yaml
from jsonschema import Draft202012Validator, FormatChecker


yaml = ruamel.yaml.YAML()
yaml.preserve_quotes = True


def parse_platform(raw: str) -> tuple[str, str, str | None]:
    """Parse Docker platform text into (os, arch, variant)."""
    raw = (raw or "").strip().lower().replace("-", "/")
    parts = [p for p in raw.split("/") if p]
    if len(parts) == 1:
        return "linux", parts[0], None
    if len(parts) == 2:
        return parts[0], parts[1], None
    return parts[0], parts[1], "/".join(parts[2:])


def canonical_platform(raw: str) -> str:
    """Normalize a platform string to os/arch[/variant]."""
    os_name, arch, variant = parse_platform(raw)
    return f"{os_name}/{arch}" + (f"/{variant}" if variant else "")


def platforms_support(platforms: list[str] | str, want: str) -> bool:
    """Return True when any allowed platform matches ``want``."""
    want_os, want_arch, want_var = parse_platform(want)
    entries = platforms if isinstance(platforms, list) else str(platforms).split(",")
    for raw in entries:
        p_os, p_arch, p_var = parse_platform(str(raw).strip())
        if (p_os, p_arch) != (want_os, want_arch):
            continue
        if p_var is None:
            return True
        if want_var == p_var:
            return True
    return False


def filter_targets_by_platform(
    targets: list[dict], platform: str | None = None
) -> list[dict]:
    """Filter target definitions by platform support."""
    if not platform:
        return list(targets or [])
    want = canonical_platform(platform)
    output = []
    for target in targets or []:
        if platforms_support(target.get("platforms", []), want):
            output.append(target)
    return output


def eol_is_past(value) -> bool:
    """Return True if EOL date is today or in the past."""
    if value in (None, "", False):
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, date):
        return value <= date.today()
    return date.fromisoformat(str(value)) <= date.today()


class Templates:
    """Accessor and validator for templates.yml."""

    def __init__(
        self,
        templates_path: str | Path = "templates.yml",
        schema_path: str | Path | None = None,
        settings: dict | None = None,
    ) -> None:
        """Load templates.yml and validate it against the schema.

        Args:
            templates_path: Path to templates configuration YAML.
            schema_path: Optional override path to JSON schema file.
            settings: Optional pre-loaded templates settings dictionary.
        """
        self._templates_path = Path(templates_path)
        self._schema_path = (
            Path(schema_path)
            if schema_path
            else Path(__file__).resolve().parents[1]
            / "schema"
            / "templates.schema.json"
        )
        if settings is None:
            with self._templates_path.open("r", encoding="utf-8") as file:
                self._settings = yaml.load(file) or {}
        else:
            self._settings = settings or {}
        self.validate_settings()
        self._entries = self._settings["dockerfiles"]
        self.validate_uniqueness()
        self._entry_by_key = {
            (entry["family"], entry["name"]): entry for entry in self._entries
        }

    @classmethod
    def from_dict(
        cls,
        settings: dict,
        schema_path: str | Path | None = None,
    ) -> "Templates":
        """Build a Templates instance from an in-memory settings dictionary."""
        return cls(
            templates_path="<in-memory>",
            schema_path=schema_path,
            settings=settings,
        )

    def validate_settings(self) -> None:
        """Validate settings against JSON schema."""
        with self._schema_path.open("r", encoding="utf-8") as file:
            schema = json.load(file)

        validator = Draft202012Validator(
            schema, format_checker=FormatChecker()
        )
        errors = sorted(
            validator.iter_errors(self._settings),
            key=lambda item: list(item.absolute_path),
        )
        if errors:
            first_error = errors[0]
            path = ".".join(str(p) for p in first_error.absolute_path)
            path = path if path else "<root>"
            raise ValueError(
                f"templates.yml failed schema validation at "
                f"'{path}': {first_error.message}"
            )

    def validate_uniqueness(self) -> None:
        """Validate uniqueness of (family, name)."""
        seen = set()
        for item in self._entries:
            key = (item["family"], item["name"])
            if key in seen:
                raise ValueError(
                    "templates.yml has duplicate dockerfile entry "
                    f"for family={item['family']} name={item['name']}"
                )
            seen.add(key)

    @staticmethod
    def eol_date(entry: dict) -> date | None:
        """Return parsed EOL date for an entry, if present."""
        value = entry.get("eol")
        if value in [None, ""]:
            return None
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))

    def is_past_eol(self, entry: dict) -> bool:
        """Return True if entry's EOL date is today or in the past."""
        end_of_life = self.eol_date(entry)
        if not end_of_life:
            return False
        return end_of_life <= date.today()

    def raw(self) -> list:
        """Get raw template entries."""
        return self._entries

    def entries(
        self,
        family: str = "",
        eol: bool = False,
        platform: str | None = None,
    ) -> list:
        """Get filtered entries."""
        output = []
        for entry in self._entries:
            if family and entry["family"] != family:
                continue
            if not eol and self.is_past_eol(entry):
                continue
            if platform and not self.targets_for_platform(entry, platform):
                continue
            output.append(entry)
        return output

    def get_entry(self, family: str, name: str, eol: bool = False) -> dict | None:
        """Get one entry by (family, name), honoring EOL filter rules."""
        entry = self._entry_by_key.get((family, name))
        if entry is None:
            return None
        if not eol and self.is_past_eol(entry):
            return None
        return entry

    def targets_for_platform(
        self, entry: dict, platform: str | None = None
    ) -> list[dict]:
        """Get entry targets filtered by platform support."""
        return filter_targets_by_platform(entry.get("targets") or [], platform)

    def grouped(self, eol: bool = False) -> dict:
        """Get entries grouped by family."""
        output = {}
        for entry in self.entries(eol=eol):
            family = entry["family"]
            output.setdefault(family, [])
            output[family].append(entry)
        return output

    def dockerfile_settings(self, eol: bool = False) -> dict:
        """Get dockerfile generation settings."""
        dockerfiles = []
        for entry in self.entries(eol=eol):
            settings = entry.copy()
            family = settings["family"]
            name = settings["name"]
            settings["template_file"] = f"{family}.dockerfile.jinja"
            settings["out_file"] = f"{family}/{name}.Dockerfile"
            dockerfiles.append(settings)
        return dockerfiles

    def dockercompose_settings(self, eol: bool = False) -> dict:
        """Get docker compose generation settings."""
        docker_compose_files = []
        for entry in self.entries(family="gz", eol=eol):
            if "nvidia" in entry["base_image"]:
                continue
            distro = entry.copy()
            name = distro["name"]
            family = distro["family"]
            distro["compose_file"] = f"{family}.docker-compose.yml.jinja"
            distro["compose_out_file"] = (
                f"docker-compose/{family}/{name}-docker-compose.yml"
            )
            docker_compose_files.append(distro)
        return docker_compose_files

    def images(self, eol: bool = False) -> dict:
        """Get nested dict of images and targets as [family][name]."""
        image_list = {}
        for dockerfile in self.entries(eol=eol):
            family = dockerfile["family"]
            name = dockerfile["name"]
            targets = [target["target"] for target in dockerfile["targets"]]
            image_list.setdefault(family, {})
            image_list[family][name] = {
                "repository": family,
                "name": name,
                "targets": targets,
            }
        return image_list

    def image_tokens(self, eol: bool = False) -> list[str]:
        """Get CLI image tokens as ``family-name``."""
        output = []
        for dockerfile in self.entries(eol=eol):
            output.append(f"{dockerfile['family']}-{dockerfile['name']}")
        return output

    def image_definition(self, token: str, eol: bool = False) -> dict:
        """Resolve a ``family-name`` token to image definition."""
        family, separator, name = token.partition("-")
        if not separator:
            raise KeyError(f"Invalid image token '{token}', expected family-name")

        image_map = self.images(eol=eol)
        if family not in image_map or name not in image_map[family]:
            raise KeyError(f"Unknown image token '{token}'")
        return image_map[family][name]

    def workflow_names(self, eol: bool = False) -> list:
        """List workflow docker image entries."""
        output = []
        for entry in self.entries(eol=eol):
            tag = entry["name"]
            for target in entry["targets"]:
                item = {
                    "label": entry["family"],
                    "tag": tag,
                    "target": target["target"],
                    "platforms": ",".join(target["platforms"]),
                }
                output.append(item)
        return output

    def task_names(self, eol: bool = False) -> list:
        """List image task names."""
        return self.image_tokens(eol=eol)

    def repo_names(self) -> list:
        """List unique repository family names."""
        names = []
        for entry in self._entries:
            family = entry["family"]
            if family not in names:
                names.append(family)
        return names
