"""
📡 GhostHandlers — Telegram Command & Callback Handlers
V4: 20+ commands including /edit, /test, /fixbugs, and photo support.
"""
import os
import shutil
import asyncio
import logging
import subprocess
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from config import (
    ADMIN_ID, TEMPLATE_REGISTRY, PROJECTS_ROOT, DEFAULT_MODEL,
    MODEL_OPTIONS, IMAGES_DIR
)
from core.engine import GhostEngine
from core.driver import GhostDriver
from core.tester import GhostTester
from core.dbsetup import GhostDB
from core.deployer import GhostDeployer
from bot.tracker import GhostTracker
from bot.menus import (
    build_template_menu, build_confirm_menu, build_model_menu,
    build_help_sections, build_project_actions
)

logger = logging.getLogger("ghost.handlers")

# ── Mutable Model State (changeable via /model) ──
_active_model = DEFAULT_MODEL

# ── Security Decorator ──
def admin_only(func):
    """Decorator to restrict commands to ADMIN_ID only."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != ADMIN_ID:
            logger.warning(f"⛔ Unauthorized: {update.effective_user.id}")
            return
        return await func(update, context)
    return wrapper


# ══════════════════════════════════════════════
#  📋  INFORMATIONAL COMMANDS
# ══════════════════════════════════════════════

@admin_only
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message with command overview."""
    await update.message.reply_text(
        "👻 *GHOST PROTOCOL V4 — Online*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🚀 *Deploy Commands:*\n"
        "  /web `<name>` `<prompt>` — PHP/MySQL/Tailwind\n"
        "  /laravel `<name>` `<prompt>` — Laravel/Blade\n"
        "  /node `<name>` `<prompt>` — Node.js/Express\n"
        "  /next `<name>` `<prompt>` — Next.js/React\n"
        "  /mobile `<name>` `<prompt>` — Expo/React Native\n"
        "  /flutter `<name>` `<prompt>` — Flutter/Dart\n"
        "  /api `<name>` `<prompt>` — REST API\n"
        "  /desktop `<name>` `<prompt>` — Electron/React\n\n"
        "✏️ *Edit & Fix:*\n"
        "  /edit `<name>` `<instruction>` — Edit existing project\n"
        "  /test `<name>` — Run automated tests\n"
        "  /fixbugs `<name>` — Test + auto-fix issues\n\n"
        "📊 *Management:*\n"
        "  /templates — Browse all templates\n"
        "  /preview `<template>` — View template content\n"
        "  /projects — List projects (with edit buttons)\n"
        "  /status — Recent deployments\n"
        "  /stats — Deployment statistics\n"
        "  /config — Current configuration\n"
        "  /help — Detailed guide\n\n"
        "📸 *Image Support:*\n"
        "  Send a photo with caption:\n"
        "  `/web AppName description` — Uses photo as UI reference",
        parse_mode="Markdown"
    )


@admin_only
async def cmd_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Switch the AI model used in prompt headers."""
    global _active_model
    args = context.args

    if not args:
        options = "\n".join(f"  `{k}` → {v}" for k, v in MODEL_OPTIONS.items())
        await update.message.reply_text(
            f"🧠 *Current Model:* `{_active_model}`\n\n"
            f"*Available Models:*\n{options}\n\n"
            f"Usage: `/model opus` or `/model flash`",
            parse_mode="Markdown"
        )
        return

    choice = args[0].lower()
    if choice not in MODEL_OPTIONS:
        await update.message.reply_text(
            f"❌ Unknown model: `{choice}`\n"
            f"Available: {', '.join(f'`{k}`' for k in MODEL_OPTIONS.keys())}",
            parse_mode="Markdown"
        )
        return

    _active_model = MODEL_OPTIONS[choice]
    await update.message.reply_text(
        f"✅ Model switched to: `{_active_model}`\n"
        f"All future deploys/edits will use this model.",
        parse_mode="Markdown"
    )


@admin_only
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detailed help with examples."""
    await update.message.reply_text(
        "📖 *GHOST PROTOCOL V4 — Help Center*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎯 *How It Works:*\n"
        "1. Send a deploy command with project name and description\n"
        "2. Ghost creates folder, launches Antigravity, injects God Template\n"
        "3. AI builds the full production app\n"
        "4. Run /test to auto-test, /fixbugs to auto-fix issues\n\n"
        "📝 *Deploy Examples:*\n"
        "```\n/web PizzaDash Build a pizza restaurant dashboard\n```\n"
        "```\n/mobile FitTracker Fitness tracker with charts\n```\n\n"
        "✏️ *Edit Examples:*\n"
        "```\n/edit PizzaDash Add a delivery tracking page\n```\n"
        "```\n/edit FitTracker Fix the login button color\n```\n\n"
        "📸 *Image Support:*\n"
        "Send a photo to the bot with a command as caption:\n"
        "```\n/web MyApp Build this exact UI design\n```\n"
        "The image is saved to the project as a UI reference.\n\n"
        "🧪 *Testing:*\n"
        "`/test PizzaDash` — Runs syntax checks, structure validation\n"
        "`/fixbugs PizzaDash` — Tests + sends bug report back to AI",
        parse_mode="Markdown"
    )


@admin_only
async def cmd_templates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists all available templates with their status."""
    templates = GhostEngine.list_templates()
    lines = ["📋 *Available Templates:*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"]
    for t in templates:
        status = "✅" if t["exists"] else "❌ MISSING"
        lines.append(f"{t['label']}\n   /{t['command']} — {t['desc']}  {status}\n")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


@admin_only
async def cmd_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the raw content of a template."""
    args = context.args
    if not args:
        await update.message.reply_text(
            "Usage: /preview <template_name>\n"
            "Available: " + ", ".join(TEMPLATE_REGISTRY.keys())
        )
        return

    template_cmd = args[0].lower()
    template_file = GhostEngine.get_template_for_command(template_cmd)
    if not template_file:
        await update.message.reply_text(f"❌ Unknown template: {template_cmd}")
        return

    content = GhostEngine.preview_template(template_file)
    if content:
        if len(content) > 3900:
            content = content[:3900] + "\n\n... (truncated)"
        await update.message.reply_text(f"📄 *Template: {template_cmd}*\n\n```\n{content}\n```", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ Template file not found for: {template_cmd}")


@admin_only
async def cmd_projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists all projects with inline edit buttons."""
    projects = GhostTracker.get_all_projects()
    if not projects:
        await update.message.reply_text("📂 No projects found yet. Deploy your first one!")
        return

    lines = ["📂 *Ghost Projects:*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"]
    for p in projects:
        status_icon = "✅" if p["status"] == "success" else "❌" if p["status"] == "failed" else "❓"
        lines.append(
            f"{status_icon} *{p['name']}*\n"
            f"   📋 {p['template']} | 📄 {p['files']} files\n"
            f"   🕐 {p['deployed']}\n"
        )

    # Add inline buttons for each project
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    buttons = []
    for p in projects[:10]:  # Limit to 10 for button list
        buttons.append([
            InlineKeyboardButton(f"✏️ Edit {p['name']}", callback_data=f"editpick:{p['name']}"),
            InlineKeyboardButton(f"🧪 Test", callback_data=f"testpick:{p['name']}"),
            InlineKeyboardButton(f"📂 Open", callback_data=f"open:{p['name']}"),
        ])

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
    )


@admin_only
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows recent deployments."""
    recent = GhostTracker.get_recent(5)
    if not recent:
        await update.message.reply_text("📊 No deployments logged yet.")
        return

    lines = ["📊 *Recent Deployments:*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"]
    for d in reversed(recent):
        icon = "✅" if d["status"] == "success" else "❌"
        lines.append(f"{icon} *{d['name']}* — {d['template']} ({d['model']})\n   🕐 {d['timestamp']}\n")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


@admin_only
async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows deployment statistics."""
    stats = GhostTracker.get_stats()
    await update.message.reply_text(
        "📈 *Ghost Protocol Statistics:*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 Total Deployments: *{stats['total_deployments']}*\n"
        f"✅ Successful: *{stats['successful']}*\n"
        f"❌ Failed: *{stats['failed']}*\n"
        f"📋 Templates Used: {', '.join(stats['templates_used']) if stats['templates_used'] else 'None yet'}",
        parse_mode="Markdown"
    )


@admin_only
async def cmd_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows current configuration."""
    from config import ANTIGRAVITY_PATH, STABILIZE_WAIT, BLIND_MODE_WAIT, MYSQL_PATH
    await update.message.reply_text(
        "⚙️ *Current Configuration:*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🤖 Active Model: `{_active_model}`\n"
        f"📂 Projects Root: `{PROJECTS_ROOT}`\n"
        f"🔧 IDE Path: `{ANTIGRAVITY_PATH}`\n"
        f"🗄️ MySQL Path: `{MYSQL_PATH}`\n"
        f"⏱️ Stabilize Wait: `{STABILIZE_WAIT}s`\n"
        f"⏱️ Blind Mode Wait: `{BLIND_MODE_WAIT}s`\n"
        f"📋 Templates: `{len(TEMPLATE_REGISTRY)}` registered\n"
        f"🧠 Models: {', '.join(f'`{k}`' for k in MODEL_OPTIONS.keys())}",
        parse_mode="Markdown"
    )


# ══════════════════════════════════════════════
#  🚀  DEPLOYMENT COMMANDS
# ══════════════════════════════════════════════

async def _deploy_project(update: Update, context: ContextTypes.DEFAULT_TYPE,
                          template_cmd: str, ui_image_path: str = None):
    """Generic deployment handler used by all stack commands."""
    if update.effective_user.id != ADMIN_ID:
        return

    args = context.args
    if not args or len(args) < 2:
        await update.message.reply_text(
            f"⚠️ Usage: /{template_cmd} <ProjectName> <Description...>\n\n"
            f"Example:\n`/{template_cmd} MyApp Build a cool app with login and dashboard`",
            parse_mode="Markdown"
        )
        return

    name = args[0]
    user_desc = " ".join(args[1:])

    # Resolve template
    template_file = GhostEngine.get_template_for_command(template_cmd)
    if not template_file:
        await update.message.reply_text(f"❌ No template registered for: /{template_cmd}")
        return

    # Copy UI reference image to project folder if provided
    ui_ref = None
    if ui_image_path:
        project_path = Path(PROJECTS_ROOT) / name
        project_path.mkdir(parents=True, exist_ok=True)
        dest = project_path / "ui_reference.png"
        shutil.copy2(ui_image_path, dest)
        ui_ref = "ui_reference.png"
        logger.info(f"📸 UI reference saved to: {dest}")

    # Build the God Prompt
    full_prompt = GhostEngine.build_prompt(template_file, user_desc, model=_active_model, ui_ref=ui_ref)
    if not full_prompt:
        await update.message.reply_text("❌ Failed to load template file.")
        return

    template_label = TEMPLATE_REGISTRY[template_cmd]["label"]
    status_parts = [
        f"🚀 *Deploying: {name}*",
        f"📋 Template: {template_label}",
        f"🧠 Model: `{_active_model}`",
        f"📝 Prompt: _{user_desc[:100]}{'...' if len(user_desc) > 100 else ''}_",
    ]
    if ui_ref:
        status_parts.append("📸 UI Reference: attached")
    status_parts.append("\n⏳ Launching IDE...")

    await update.message.reply_text("\n".join(status_parts), parse_mode="Markdown")

    # Switch model in Antigravity UI before deploying
    await asyncio.to_thread(GhostDriver.switch_model, name, _active_model)

    # Run deployment in a thread to avoid blocking the bot
    result = await asyncio.to_thread(GhostDriver.deploy, name, full_prompt)

    if result["success"]:
        GhostTracker.log_deployment(name, template_cmd, "success", _active_model)
        await update.message.reply_text(
            f"✅ *{name}* deployed successfully!\n"
            f"📂 `{PROJECTS_ROOT}\\{name}`\n"
            f"The AI is now building your app. 🔥\n\n"
            f"When done, run:\n"
            f"`/test {name}` — Validate the build\n"
            f"`/fixbugs {name}` — Auto-fix any issues",
            parse_mode="Markdown"
        )
    else:
        GhostTracker.log_deployment(name, template_cmd, "failed", _active_model)
        await update.message.reply_text(
            f"❌ Deployment failed: {result['message']}\nCheck console logs.",
            parse_mode="Markdown"
        )


# ── Individual Stack Commands ──
@admin_only
async def cmd_web(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _deploy_project(update, context, "web")

@admin_only
async def cmd_laravel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _deploy_project(update, context, "laravel")

@admin_only
async def cmd_node(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _deploy_project(update, context, "node")

@admin_only
async def cmd_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _deploy_project(update, context, "next")

@admin_only
async def cmd_mobile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _deploy_project(update, context, "mobile")

@admin_only
async def cmd_flutter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _deploy_project(update, context, "flutter")

@admin_only
async def cmd_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _deploy_project(update, context, "api")

@admin_only
async def cmd_desktop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _deploy_project(update, context, "desktop")


# ══════════════════════════════════════════════
#  ✏️  EDIT COMMAND (Resume Existing Project)
# ══════════════════════════════════════════════

@admin_only
async def cmd_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Edit an existing project — reopens in Antigravity with same chat context."""
    args = context.args
    if not args or len(args) < 2:
        await update.message.reply_text(
            "⚠️ Usage: /edit <ProjectName> <Instruction...>\n\n"
            "Example:\n`/edit PizzaDash Add a delivery tracking page with GPS`",
            parse_mode="Markdown"
        )
        return

    name = args[0]
    instruction = " ".join(args[1:])

    # Check project exists
    project_path = Path(PROJECTS_ROOT) / name
    if not project_path.exists():
        # Fuzzy search
        existing = [p.name for p in PROJECTS_ROOT.iterdir() if p.is_dir()]
        suggestions = [p for p in existing if name.lower() in p.lower()]
        msg = f"❌ Project not found: `{name}`"
        if suggestions:
            msg += f"\n\nDid you mean: {', '.join(f'`{s}`' for s in suggestions[:5])}"
        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    await update.message.reply_text(
        f"✏️ *Editing: {name}*\n"
        f"📝 _{instruction[:100]}{'...' if len(instruction) > 100 else ''}_\n\n"
        f"⏳ Reopening IDE (same chat context)...",
        parse_mode="Markdown"
    )

    result = await asyncio.to_thread(GhostDriver.edit, name, instruction)

    if result["success"]:
        GhostTracker.log_deployment(name, "edit", "success", _active_model)
        await update.message.reply_text(
            f"✅ Edit sent to *{name}*!\n"
            f"AI is working on your changes. 🔧",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(f"❌ Edit failed: {result['message']}", parse_mode="Markdown")


# ══════════════════════════════════════════════
#  🧪  TESTING COMMANDS (Automated + AI Injection)
# ══════════════════════════════════════════════

@admin_only
async def cmd_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    2-step test pipeline:
    Step 1: Automated checks (syntax, structure, DB setup)
    Step 2: Single mega-prompt injected → AI tests + gap analysis + implements ALL gaps
    """
    args = context.args
    if not args:
        await update.message.reply_text(
            "⚠️ Usage: /test <ProjectName>\n\n"
            "Example: `/test PizzaDash`",
            parse_mode="Markdown"
        )
        return

    name = args[0]
    project_path = Path(PROJECTS_ROOT) / name
    if not project_path.exists():
        await update.message.reply_text(f"❌ Project not found: `{name}`", parse_mode="Markdown")
        return

    # ═══════════ STEP 1: Automated Checks ═══════════
    await update.message.reply_text(
        f"🧪 *STEP 1/2: Automated Checks*\n"
        f"Testing *{name}*...",
        parse_mode="Markdown"
    )

    report = await asyncio.to_thread(GhostTester.run, name)
    formatted = GhostTester.format_report(report)
    await update.message.reply_text(formatted, parse_mode="Markdown")

    # Auto DB setup if SQL files found
    sql_files = GhostDB.find_sql_files(name)
    if sql_files:
        await update.message.reply_text(
            f"🗄️ Found {len(sql_files)} SQL file(s). Setting up database...",
            parse_mode="Markdown"
        )
        db_result = await asyncio.to_thread(GhostDB.setup, name)
        if db_result["success"]:
            await update.message.reply_text(
                f"🗄️ ✅ DB setup complete!\n"
                f"📦 Database: `{name}`\n"
                f"📄 Files imported: {', '.join(db_result['files_imported'])}",
                parse_mode="Markdown"
            )
        elif db_result["errors"]:
            await update.message.reply_text(
                f"🗄️ ⚠️ DB setup had issues:\n" +
                "\n".join(f"  • {e}" for e in db_result["errors"]),
                parse_mode="Markdown"
            )

    stack = report.get("stack", "unknown")

    # ═══════════ STEP 2: Full Test + Gap + Implement (ONE SHOT) ═══════════
    await update.message.reply_text(
        f"🧪 *STEP 2/2: AI Full Test + Gap Analysis + Auto-Implement*\n"
        f"Injecting mega-prompt into Antigravity...\n"
        f"🧠 Model: `{_active_model}`\n\n"
        f"AI will:\n"
        f"  1️⃣ Test EVERY feature ({stack}-specific checks)\n"
        f"  2️⃣ Create `gap_analysis.md` with ALL gaps\n"
        f"  3️⃣ Implement ALL missing features\n\n"
        f"All in ONE shot — no waiting.",
        parse_mode="Markdown"
    )

    full_prompt = GhostTester.generate_full_test_prompt(name, stack)
    await asyncio.to_thread(GhostDriver.switch_model, name, _active_model)
    result = await asyncio.to_thread(GhostDriver.edit, name, full_prompt)

    if result["success"]:
        await update.message.reply_text(
            f"✅ Mega-prompt injected! AI is working. 🔥\n\n"
            f"When done, check:\n"
            f"`/screen {name}` — Screenshot progress\n"
            f"`/test {name}` — Run again\n"
            f"`/deploy {name}` — Deploy to staging",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"⚠️ Could not inject test prompt: {result['message']}",
            parse_mode="Markdown"
        )

# ══════════════════════════════════════════════
#  📸  SCREENSHOT COMMAND
# ══════════════════════════════════════════════

@admin_only
async def cmd_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Take a screenshot of the Antigravity window and send to Telegram."""
    args = context.args
    if not args:
        await update.message.reply_text(
            "⚠️ Usage: /screen <ProjectName>\n\n"
            "Example: `/screen PizzaDash`",
            parse_mode="Markdown"
        )
        return

    name = args[0]
    await update.message.reply_text(f"📸 Capturing *{name}*...", parse_mode="Markdown")

    screenshot_path = await asyncio.to_thread(GhostDriver.screenshot, name)

    if screenshot_path:
        try:
            with open(screenshot_path, 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=f"📸 Screenshot: {name}"
                )
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to send screenshot: {e}")
    else:
        await update.message.reply_text(
            "❌ Could not capture screenshot.\n"
            "Make sure Antigravity is open with this project."
        )

# ══════════════════════════════════════════════
#  🚀  DEPLOY COMMAND
# ══════════════════════════════════════════════

@admin_only
async def cmd_deploy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deploy project to staging server (dev.hussein.top) + inject deploy prep prompt."""
    args = context.args
    if not args:
        await update.message.reply_text(
            "⚠️ Usage: /deploy <ProjectName>\n\n"
            "Example: `/deploy PizzaDash`\n\n"
            "Copies project to staging → `dev.hussein.top/ProjectName`",
            parse_mode="Markdown"
        )
        return

    name = args[0]
    project_path = Path(PROJECTS_ROOT) / name
    if not project_path.exists():
        await update.message.reply_text(f"❌ Project not found: `{name}`", parse_mode="Markdown")
        return

    # Step 1: Inject deploy prep prompt into Antigravity
    stack = GhostTester.detect_stack(project_path)
    await update.message.reply_text(
        f"🚀 *Deploying {name} to staging*\n"
        f"📋 Stack: `{stack}`\n"
        f"🧠 Model: `{_active_model}`\n\n"
        f"Step 1: Prepping codebase via AI...\n"
        f"Step 2: SCP to `dev.hussein.top/{name}`",
        parse_mode="Markdown"
    )

    deploy_prompt = GhostDeployer.generate_deploy_prompt(name, stack)
    await asyncio.to_thread(GhostDriver.switch_model, name, _active_model)
    prep_result = await asyncio.to_thread(GhostDriver.edit, name, deploy_prompt)

    if prep_result["success"]:
        await update.message.reply_text(
            "✅ Deploy prep prompt injected — AI is preparing code.\n"
            "📦 Now copying files to staging server...",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"⚠️ Could not inject deploy prompt: {prep_result['message']}\n"
            "📦 Proceeding with file copy anyway...",
            parse_mode="Markdown"
        )

    # Step 2: SCP project to staging server
    deploy_result = await asyncio.to_thread(GhostDeployer.deploy_to_staging, name)

    if deploy_result["success"]:
        await update.message.reply_text(
            f"✅ *Deployed to staging!* 🔥\n\n"
            f"🌐 URL: `{deploy_result['url']}`\n"
            f"📂 Server path: `/home/ubuntu/staging/{name}`\n\n"
            f"Commands:\n"
            f"`/screen {name}` — Screenshot\n"
            f"`/test {name}` — Run tests\n"
            f"`/deploy {name}` — Re-deploy",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"❌ Deployment failed: {deploy_result['message']}",
            parse_mode="Markdown"
        )


@admin_only
async def cmd_fixbugs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test a project and auto-send bug report to Antigravity."""
    args = context.args
    if not args:
        await update.message.reply_text(
            "⚠️ Usage: /fixbugs <ProjectName>\n\n"
            "Example: `/fixbugs PizzaDash`",
            parse_mode="Markdown"
        )
        return

    name = args[0]
    project_path = Path(PROJECTS_ROOT) / name
    if not project_path.exists():
        await update.message.reply_text(f"❌ Project not found: `{name}`", parse_mode="Markdown")
        return

    await update.message.reply_text(f"🧪 Testing *{name}*...", parse_mode="Markdown")

    # Run tests
    report = await asyncio.to_thread(GhostTester.run, name)
    formatted = GhostTester.format_report(report)
    await update.message.reply_text(formatted, parse_mode="Markdown")

    # Generate bug prompt
    bug_prompt = GhostTester.generate_bug_prompt(report)
    if not bug_prompt:
        await update.message.reply_text("✅ No issues found! Project is healthy. 🎉", parse_mode="Markdown")
        return

    await update.message.reply_text(
        f"🐛 Issues found. Sending bug report to Antigravity...",
        parse_mode="Markdown"
    )

    # Send bug report via edit mode
    result = await asyncio.to_thread(GhostDriver.edit, name, bug_prompt)

    if result["success"]:
        await update.message.reply_text(
            f"🔧 Bug report sent to *{name}*!\n"
            f"AI is fixing the issues. Run `/test {name}` again after it finishes.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(f"❌ Failed to send bug report: {result['message']}", parse_mode="Markdown")


# ══════════════════════════════════════════════
#  📸  PHOTO HANDLER (UI Reference Images)
# ══════════════════════════════════════════════

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles photos sent to the bot. If caption starts with a command, treats as deploy + UI ref."""
    if update.effective_user.id != ADMIN_ID:
        return

    caption = update.message.caption or ""
    if not caption:
        await update.message.reply_text(
            "📸 Got your image! To use it as a UI reference, add a caption:\n"
            "`/web AppName Build this exact UI design`",
            parse_mode="Markdown"
        )
        return

    # Download the photo (highest resolution)
    photo = update.message.photo[-1]  # Largest size
    photo_file = await photo.get_file()

    # Ensure images directory exists
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    # Save to temp location
    temp_path = IMAGES_DIR / f"ui_ref_{photo.file_unique_id}.png"
    await photo_file.download_to_drive(str(temp_path))
    logger.info(f"📸 Downloaded UI reference: {temp_path}")

    # Parse the caption as a command
    parts = caption.strip().split()
    if not parts or not parts[0].startswith("/"):
        await update.message.reply_text(
            "📸 Image saved! But caption must start with a command.\n"
            "Example: `/web AppName Build this design`",
            parse_mode="Markdown"
        )
        return

    cmd = parts[0].lstrip("/").lower()
    if cmd not in TEMPLATE_REGISTRY and cmd != "edit":
        await update.message.reply_text(
            f"❌ Unknown command: /{cmd}\n"
            f"Available: {', '.join('/' + k for k in TEMPLATE_REGISTRY.keys())}",
            parse_mode="Markdown"
        )
        return

    # Set context args (skip the /command)
    context.args = parts[1:]

    if cmd == "edit":
        # For edit mode, copy image to project folder
        if len(parts) >= 3:
            project_name = parts[1]
            project_path = Path(PROJECTS_ROOT) / project_name
            if project_path.exists():
                dest = project_path / "ui_reference.png"
                shutil.copy2(str(temp_path), dest)
                # Add UI reference note to the edit instruction
                instruction = " ".join(parts[2:])
                instruction += "\n\n📸 A new UI reference image has been saved as 'ui_reference.png' in the project folder. Match this design."
                context.args = [project_name] + instruction.split()
        await cmd_edit(update, context)
    else:
        # Deploy with UI reference
        await _deploy_project(update, context, cmd, ui_image_path=str(temp_path))


# ══════════════════════════════════════════════
#  🎛️  CALLBACK QUERY HANDLERS (Inline Buttons)
# ══════════════════════════════════════════════

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all inline keyboard button presses."""
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    data = query.data

    if data == "cancel":
        await query.edit_message_text("❌ Cancelled.")
        return

    # ── Edit picker (from /projects inline buttons) ──
    if data.startswith("editpick:"):
        project_name = data.split(":", 1)[1]
        await query.edit_message_text(
            f"✏️ *Edit Mode: {project_name}*\n\n"
            f"Send your edit instruction:\n"
            f"`/edit {project_name} <your instruction here>`",
            parse_mode="Markdown"
        )
        return

    # ── Test picker (from /projects inline buttons) ──
    if data.startswith("testpick:"):
        project_name = data.split(":", 1)[1]
        await query.edit_message_text(f"🧪 Running tests on *{project_name}*...", parse_mode="Markdown")
        report = await asyncio.to_thread(GhostTester.run, project_name)
        formatted = GhostTester.format_report(report)
        await query.edit_message_text(formatted, parse_mode="Markdown")
        return

    # ── Help sections ──
    if data.startswith("help:"):
        section = data.split(":")[1]
        if section == "templates":
            templates = GhostEngine.list_templates()
            lines = ["📋 *Templates:*\n"]
            for t in templates:
                lines.append(f"{t['label']}\n  `/{t['command']}` — {t['desc']}\n")
            await query.edit_message_text("\n".join(lines), parse_mode="Markdown")

        elif section == "commands":
            await query.edit_message_text(
                "⚙️ *All Commands:*\n\n"
                "*Deploy:* /web /laravel /node /next /mobile /flutter /api /desktop\n"
                "*Edit:* /edit — Reopen project with instruction\n"
                "*Test:* /test — Run automated tests\n"
                "*Fix:* /fixbugs — Test + auto-fix issues\n"
                "*Info:* /templates /preview /projects /status /stats /config",
                parse_mode="Markdown"
            )

        elif section == "examples":
            await query.edit_message_text(
                "🎯 *Example Commands:*\n\n"
                "```\n/web PizzaDash Build a pizza dashboard\n```\n"
                "```\n/edit PizzaDash Add delivery tracking\n```\n"
                "```\n/test PizzaDash\n```\n"
                "```\n/fixbugs PizzaDash\n```",
                parse_mode="Markdown"
            )

    # ── Open folder ──
    elif data.startswith("open:"):
        project_name = data.split(":", 1)[1]
        project_path = str(PROJECTS_ROOT / project_name)
        try:
            subprocess.Popen(['explorer', project_path])
            await query.edit_message_text(f"📂 Opened: {project_name}")
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {e}")
