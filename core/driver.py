"""
🔧 GhostDriver — Automation Core (The "Hands")
Manages window focus, app launching, and prompt injection.
"""
import os
import time
import subprocess
import ctypes
import ctypes.wintypes
import logging
import pyautogui
import pyperclip
from pathlib import Path

from config import (
    ANTIGRAVITY_PATH, PROJECTS_ROOT,
    STABILIZE_WAIT, BLIND_MODE_WAIT, CHAT_OPEN_WAIT,
    PASTE_WAIT, WINDOW_SCAN_TIMEOUT
)
from core.eyes import GhostEyes

logger = logging.getLogger("ghost.driver")


class GhostDriver:
    """Handles all GUI automation: launching, focusing, and injecting."""

    @staticmethod
    def force_focus(window_title_part: str) -> bool:
        """Finds a window by title substring and forces it to the foreground."""
        user32 = ctypes.windll.user32
        found_hwnd = None

        def callback(hwnd, _):
            nonlocal found_hwnd
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                if window_title_part.lower() in buff.value.lower():
                    found_hwnd = hwnd
                    return False
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
        user32.EnumWindows(WNDENUMPROC(callback), 0)

        if found_hwnd:
            try:
                if user32.IsIconic(found_hwnd):
                    user32.ShowWindow(found_hwnd, 9)  # SW_RESTORE

                user32.SetForegroundWindow(found_hwnd)

                # Click center of window to guarantee focus
                rect = ctypes.wintypes.RECT()
                user32.GetWindowRect(found_hwnd, ctypes.byref(rect))
                cx = rect.left + (rect.right - rect.left) // 2
                cy = rect.top + (rect.bottom - rect.top) // 2
                time.sleep(0.2)
                pyautogui.click(cx, cy)
                return True
            except Exception as e:
                logger.error(f"Focus failed: {e}")
                return False
        return False

    @staticmethod
    def deploy(project_name: str, full_prompt: str) -> dict:
        """
        Full deployment pipeline:
        1. Create project folder
        2. Launch Antigravity
        3. Wait for window
        4. Dismiss trust dialog
        5. Open chat & inject prompt

        Returns dict with 'success' bool and 'message' string.
        """
        result = {"success": False, "message": ""}

        # ── 1. Create Folder ──
        project_path = Path(PROJECTS_ROOT) / project_name
        if not project_path.exists():
            try:
                os.makedirs(project_path)
                logger.info(f"📂 Created: {project_path}")
            except Exception as e:
                result["message"] = f"Failed to create directory: {e}"
                logger.error(result["message"])
                return result

        # ── 2. Launch App ──
        try:
            subprocess.Popen([ANTIGRAVITY_PATH, str(project_path)])
            logger.info(f"🚀 Launched Antigravity → {project_name}")
        except FileNotFoundError:
            result["message"] = "Antigravity executable not found!"
            logger.error(result["message"])
            return result

        # ── 3. Wait for Window ──
        logger.info(f"🔍 Scanning for window (max {WINDOW_SCAN_TIMEOUT}s)...")
        window_found = False
        for _ in range(WINDOW_SCAN_TIMEOUT):
            time.sleep(1)
            if GhostDriver.force_focus(project_name):
                window_found = True
                logger.info("✅ Window found and focused.")
                break

        if not window_found:
            result["message"] = "Timed out waiting for IDE window."
            logger.error(result["message"])
            return result

        # ── 4. Breach Sequence (Trust Dialog) ──
        logger.info(f"⏳ Stabilizing ({STABILIZE_WAIT}s)...")
        time.sleep(STABILIZE_WAIT)
        GhostDriver.force_focus(project_name)
        pyautogui.press('enter')
        logger.info("🔓 Sent ENTER to dismiss trust dialog.")

        # ── 5. Wait for Chat Interface ──
        logger.info("💬 Waiting for Chat Interface...")
        visual_ok = GhostEyes.wait_for_ui("chat_bar.png", timeout=15)

        if visual_ok:
            center = pyautogui.center(visual_ok)
            pyautogui.click(center)
            logger.info("👁️ Visual Mode: Clicked chat bar.")
        else:
            logger.info(f"🔇 Blind Mode: Waiting {BLIND_MODE_WAIT}s...")
            time.sleep(BLIND_MODE_WAIT)
            GhostDriver.force_focus(project_name)

        # ── 6. Inject Prompt ──
        logger.info("💉 Injecting prompt...")
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(CHAT_OPEN_WAIT)

        pyperclip.copy(full_prompt)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(PASTE_WAIT)
        pyautogui.press('enter')
        logger.info("✅ Prompt injected and sent.")

        result["success"] = True
        result["message"] = f"Deployed {project_name} successfully."
        return result

    @staticmethod
    def edit(project_name: str, edit_prompt: str) -> dict:
        """
        Edit mode: Re-opens an existing project in Antigravity.
        Since the folder is already trusted, it resumes the existing chat context.
        Skips folder creation and trust dialog.
        """
        result = {"success": False, "message": ""}

        project_path = Path(PROJECTS_ROOT) / project_name
        if not project_path.exists():
            result["message"] = f"Project not found: {project_name}"
            logger.error(result["message"])
            return result

        # ── 1. Launch Antigravity with existing folder ──
        try:
            subprocess.Popen([ANTIGRAVITY_PATH, str(project_path)])
            logger.info(f"✏️ Reopened Antigravity → {project_name}")
        except FileNotFoundError:
            result["message"] = "Antigravity executable not found!"
            logger.error(result["message"])
            return result

        # ── 2. Wait for Window ──
        logger.info(f"🔍 Scanning for window (max {WINDOW_SCAN_TIMEOUT}s)...")
        window_found = False
        for _ in range(WINDOW_SCAN_TIMEOUT):
            time.sleep(1)
            if GhostDriver.force_focus(project_name):
                window_found = True
                logger.info("✅ Window found and focused.")
                break

        if not window_found:
            result["message"] = "Timed out waiting for IDE window."
            logger.error(result["message"])
            return result

        # ── 3. Skip trust dialog — already trusted ──
        logger.info(f"⏳ Stabilizing ({STABILIZE_WAIT}s)...")
        time.sleep(STABILIZE_WAIT)
        GhostDriver.force_focus(project_name)

        # ── 4. Open Chat & Inject Edit Prompt ──
        logger.info("💬 Opening chat for edit injection...")
        visual_ok = GhostEyes.wait_for_ui("chat_bar.png", timeout=15)

        if visual_ok:
            center = pyautogui.center(visual_ok)
            pyautogui.click(center)
            logger.info("👁️ Visual Mode: Clicked chat bar.")
        else:
            logger.info(f"🔇 Blind Mode: Waiting {BLIND_MODE_WAIT}s...")
            time.sleep(BLIND_MODE_WAIT)
            GhostDriver.force_focus(project_name)

        pyautogui.hotkey('ctrl', 'l')
        time.sleep(CHAT_OPEN_WAIT)

        pyperclip.copy(edit_prompt)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(PASTE_WAIT)
        pyautogui.press('enter')
        logger.info("✅ Edit prompt injected and sent.")

        result["success"] = True
        result["message"] = f"Edit sent to {project_name} successfully."
        return result

    @staticmethod
    def screenshot(project_name: str) -> str | None:
        """
        Takes a screenshot of the Antigravity window.
        Returns the path to the saved image, or None on failure.
        """
        from config import IMAGES_DIR
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)

        # Focus the window first
        if not GhostDriver.force_focus(project_name):
            # Try with "Antigravity" as fallback
            if not GhostDriver.force_focus("Antigravity"):
                logger.error("❌ No Antigravity window found for screenshot.")
                return None

        time.sleep(0.5)  # Let focus settle

        # Get window rect for region capture
        user32 = ctypes.windll.user32
        found_hwnd = None

        def callback(hwnd, _):
            nonlocal found_hwnd
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                if project_name.lower() in buff.value.lower() or "antigravity" in buff.value.lower():
                    found_hwnd = hwnd
                    return False
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
        user32.EnumWindows(WNDENUMPROC(callback), 0)

        if found_hwnd:
            rect = ctypes.wintypes.RECT()
            user32.GetWindowRect(found_hwnd, ctypes.byref(rect))
            region = (rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)
            screenshot = pyautogui.screenshot(region=region)
        else:
            # Full screen fallback
            screenshot = pyautogui.screenshot()

        save_path = str(IMAGES_DIR / f"screen_{project_name}.png")
        screenshot.save(save_path)
        logger.info(f"📸 Screenshot saved: {save_path}")
        return save_path

    @staticmethod
    def switch_model(project_name: str, model_name: str) -> bool:
        """
        Switches the AI model in Antigravity's UI.
        Uses Command Palette approach: Ctrl+Shift+P → type model command.
        Returns True on success.
        """
        # Focus the window
        if not GhostDriver.force_focus(project_name):
            if not GhostDriver.force_focus("Antigravity"):
                logger.warning("⚠️ Could not focus Antigravity for model switch.")
                return False

        time.sleep(0.5)

        # Open Command Palette
        pyautogui.hotkey('ctrl', 'shift', 'p')
        time.sleep(0.8)

        # Type model selection command
        pyautogui.typewrite("Change Model", interval=0.03)
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(0.5)

        # Type the model name to filter/select it
        pyautogui.typewrite(model_name, interval=0.03)
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(0.3)

        # Close any remaining palette with Escape
        pyautogui.press('escape')

        logger.info(f"🧠 Model switch attempted: {model_name}")
        return True

