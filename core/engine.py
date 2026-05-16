"""
🧠 GhostEngine — Template Engine & Prompt Builder
Discovers templates, assembles prompts, and manages model preferences.
"""
import logging
from pathlib import Path
from config import TEMPLATES_DIR, TEMPLATE_REGISTRY, DEFAULT_MODEL, MODEL_OPTIONS

logger = logging.getLogger("ghost.engine")


class GhostEngine:
    """Handles template discovery, loading, and prompt assembly."""

    @staticmethod
    def list_templates() -> list[dict]:
        """Returns a list of all registered templates with metadata."""
        templates = []
        for cmd, meta in TEMPLATE_REGISTRY.items():
            file_path = TEMPLATES_DIR / f"{meta['file']}.txt"
            exists = file_path.exists()
            templates.append({
                "command": cmd,
                "label": meta["label"],
                "desc": meta["desc"],
                "file": meta["file"],
                "exists": exists,
                "path": str(file_path),
            })
        return templates

    @staticmethod
    def load_template(template_file: str) -> str | None:
        """Loads a template file by name (without .txt extension)."""
        try:
            file_path = TEMPLATES_DIR / f"{template_file}.txt"
            if file_path.exists():
                return file_path.read_text(encoding='utf-8')
            else:
                logger.error(f"Template not found: {template_file}")
                return None
        except Exception as e:
            logger.error(f"Error loading template {template_file}: {e}")
            return None

    @staticmethod
    def load_token_saver() -> str:
        """Loads the shared token-saver instructions."""
        saver_path = TEMPLATES_DIR / "_token_saver.txt"
        if saver_path.exists():
            return "\n\n" + saver_path.read_text(encoding='utf-8')
        return ""

    @staticmethod
    def load_production_enforcer() -> str:
        """Loads the production-grade enforcement instructions."""
        enforcer_path = TEMPLATES_DIR / "_production_enforcer.txt"
        if enforcer_path.exists():
            return "\n\n" + enforcer_path.read_text(encoding='utf-8')
        return ""

    @staticmethod
    def get_template_for_command(command: str) -> str | None:
        """Gets the template file name for a given command."""
        entry = TEMPLATE_REGISTRY.get(command)
        if entry:
            return entry["file"]
        return None

    @staticmethod
    def build_prompt(template_file: str, user_prompt: str, model: str = None, ui_ref: str = None) -> str | None:
        """
        Assembles the full "God Prompt":
        1. Model header (informational)
        2. Template body (with {prompt} replaced)
        3. UI reference note (if image provided)
        4. Production enforcer
        5. Token saver footer
        """
        template_content = GhostEngine.load_template(template_file)
        if not template_content:
            return None

        # Replace the {prompt} placeholder
        body = template_content.replace("{prompt}", user_prompt)

        # Prepend model preference
        model_name = model or DEFAULT_MODEL
        header = f"[MODEL PREFERENCE: {model_name}]\n\n"

        # UI reference image note
        ui_note = ""
        if ui_ref:
            ui_note = (
                f"\n\n📸 UI REFERENCE IMAGE:\n"
                f"A UI reference image has been saved to the project folder as '{ui_ref}'.\n"
                f"Use this image as the design target. Match the layout, colors, and style shown.\n"
            )

        # Append production enforcer + token saver
        enforcer = GhostEngine.load_production_enforcer()
        footer = GhostEngine.load_token_saver()

        full_prompt = header + body + ui_note + enforcer + footer
        logger.info(f"📝 Prompt assembled: {len(full_prompt)} chars, model={model_name}")
        return full_prompt

    @staticmethod
    def preview_template(template_file: str) -> str | None:
        """Returns the raw template content for previewing."""
        return GhostEngine.load_template(template_file)

    @staticmethod
    def resolve_model(model_key: str = None) -> str:
        """Resolves a model shorthand (flash/pro) to a full model name."""
        if model_key and model_key.lower() in MODEL_OPTIONS:
            return MODEL_OPTIONS[model_key.lower()]
        return DEFAULT_MODEL
