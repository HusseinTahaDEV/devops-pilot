"""
👻 GHOST PROTOCOL V4 — Command & Control Center
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A Telegram-controlled AI Development Framework.
Deploy full-stack apps from your phone. One command. Zero friction.

V4 Features:
  - Edit existing projects (resume chat context)
  - Production-grade enforcement on all templates
  - Auto MySQL/DB setup from schema.sql
  - Automated testing with bug reporting back to AI
  - Image attachments for UI reference

Usage:
    python ghost.py
"""
import os
import sys
import logging
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters
)

# ── Ensure project root is in Python path ──
sys.path.insert(0, os.path.dirname(__file__))

from config import TELEGRAM_TOKEN, PROJECTS_ROOT, IMAGES_DIR
from bot.handlers import (
    cmd_start, cmd_help, cmd_model,
    cmd_templates, cmd_preview,
    cmd_projects, cmd_status, cmd_stats, cmd_config,
    cmd_web, cmd_laravel, cmd_node, cmd_next,
    cmd_mobile, cmd_flutter, cmd_api, cmd_desktop,
    cmd_edit, cmd_test, cmd_fixbugs, cmd_screen, cmd_deploy,
    photo_handler, callback_handler,
)

# ── Logging ──
logging.basicConfig(
    format='%(asctime)s [%(name)s] %(levelname)s — %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("ghost")


def main():
    """Initialize and run Ghost Protocol V4."""
    # Ensure directories exist
    PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    # Banner
    print("╔══════════════════════════════════════════════╗")
    print("║  👻  GHOST PROTOCOL V4                       ║")
    print("║  AI Development Command & Control Center      ║")
    print("║  Edit • Test • Fix • Deploy • Repeat          ║")
    print("╚══════════════════════════════════════════════╝")
    print()
    print(f"  📂 Projects: {PROJECTS_ROOT}")
    print(f"  📋 Templates: 8 registered + Production Enforcer")
    print(f"  🧪 Tester: Active")
    print(f"  📸 Image Support: Active")
    print()

    # Define the command list for the menu
    commands = [
        ("start", "Start Ghost Protocol"),
        ("help", "Show detailed help"),
        ("web", "Deploy PHP/MySQL app"),
        ("laravel", "Deploy Laravel app"),
        ("node", "Deploy Node.js app"),
        ("next", "Deploy Next.js app"),
        ("mobile", "Deploy Expo/React Native app"),
        ("flutter", "Deploy Flutter app"),
        ("api", "Deploy REST API"),
        ("desktop", "Deploy Electron app"),
        ("edit", "Edit existing project"),
        ("test", "Run automated tests"),
        ("fixbugs", "Test & auto-fix bugs"),
        ("model", "Switch AI model"),
        ("screen", "Screenshot Antigravity window"),
        ("deploy", "Deploy to staging server"),
        ("templates", "List templates"),
        ("projects", "List projects"),
        ("status", "Show recent deployments"),
        ("stats", "Show statistics"),
        ("config", "Show configuration"),
    ]

    async def post_init(application):
        """Register commands with Telegram on startup."""
        await application.bot.set_my_commands(commands)
        logger.info("✅ Telegram commands registered.")

    # Build the Telegram app with post_init
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    # ── Informational Commands ──
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("templates", cmd_templates))
    app.add_handler(CommandHandler("preview", cmd_preview))
    app.add_handler(CommandHandler("projects", cmd_projects))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("config", cmd_config))

    # ── Deployment Commands ──
    app.add_handler(CommandHandler("web", cmd_web))
    app.add_handler(CommandHandler("laravel", cmd_laravel))
    app.add_handler(CommandHandler("node", cmd_node))
    app.add_handler(CommandHandler("next", cmd_next))
    app.add_handler(CommandHandler("mobile", cmd_mobile))
    app.add_handler(CommandHandler("flutter", cmd_flutter))
    app.add_handler(CommandHandler("api", cmd_api))
    app.add_handler(CommandHandler("desktop", cmd_desktop))

    # ── Edit, Testing & Model Commands ──
    app.add_handler(CommandHandler("edit", cmd_edit))
    app.add_handler(CommandHandler("test", cmd_test))
    app.add_handler(CommandHandler("model", cmd_model))
    app.add_handler(CommandHandler("screen", cmd_screen))
    app.add_handler(CommandHandler("deploy", cmd_deploy))
    app.add_handler(CommandHandler("fixbugs", cmd_fixbugs))

    # ── Photo Handler (UI References) ──
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    # ── Inline Button Callbacks ──
    app.add_handler(CallbackQueryHandler(callback_handler))

    print("  👻 GHOST PROTOCOL V4 LISTENING...")
    print("  Send /start to your Telegram bot to begin.\n")
    app.run_polling()


if __name__ == '__main__':
    main()
