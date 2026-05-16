"""
🎛️ GhostMenus — Telegram Inline Keyboard Builders
V4: Added edit, test, and project action buttons.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import TEMPLATE_REGISTRY


def build_template_menu() -> InlineKeyboardMarkup:
    """Builds an inline keyboard with all available templates."""
    buttons = []
    for cmd, meta in TEMPLATE_REGISTRY.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"{meta['label']}",
                callback_data=f"tpl:{cmd}"
            )
        ])
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
    return InlineKeyboardMarkup(buttons)


def build_confirm_menu(project_name: str, template_cmd: str) -> InlineKeyboardMarkup:
    """Builds a confirmation dialog before deployment."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Deploy Now", callback_data=f"deploy:{template_cmd}:{project_name}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel"),
        ]
    ])


def build_model_menu() -> InlineKeyboardMarkup:
    """Builds a model selection menu."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ Flash (Fast)", callback_data="model:flash")],
        [InlineKeyboardButton("🧠 Pro (Smart)", callback_data="model:pro")],
    ])


def build_project_actions(project_name: str) -> InlineKeyboardMarkup:
    """Full action buttons for a specific project — edit, test, fixbugs, open."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✏️ Edit", callback_data=f"editpick:{project_name}"),
            InlineKeyboardButton("🧪 Test", callback_data=f"testpick:{project_name}"),
        ],
        [
            InlineKeyboardButton("🐛 Fix Bugs", callback_data=f"fixpick:{project_name}"),
            InlineKeyboardButton("📂 Open Folder", callback_data=f"open:{project_name}"),
        ],
    ])


def build_help_sections() -> InlineKeyboardMarkup:
    """Navigation buttons for the help menu."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Templates", callback_data="help:templates")],
        [InlineKeyboardButton("⚙️ Commands", callback_data="help:commands")],
        [InlineKeyboardButton("🎯 Examples", callback_data="help:examples")],
    ])
