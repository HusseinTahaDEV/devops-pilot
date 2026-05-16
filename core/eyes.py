"""
👁️ GhostEyes — Visual Awareness Module
Scans the screen for UI anchors before injecting prompts.
"""
import os
import time
import logging
import pyautogui

logger = logging.getLogger("ghost.eyes")


class GhostEyes:
    """Provides visual verification by scanning for UI element screenshots."""

    ANCHORS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "anchors")

    @staticmethod
    def wait_for_ui(image_name: str, timeout: int = 30):
        """
        Waits for a specific UI element to appear on screen.
        Returns the location Box if found, False otherwise.
        
        Place anchor screenshots in the /anchors/ folder.
        """
        # Check anchors folder first, then root folder
        image_path = os.path.join(GhostEyes.ANCHORS_DIR, image_name)
        if not os.path.exists(image_path):
            # Fallback to project root
            image_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), image_name)

        if not os.path.exists(image_path):
            logger.warning(f"Anchor '{image_name}' not found. Using Blind Mode.")
            return False

        logger.info(f"👁️ Scanning for {image_name} (timeout={timeout}s)...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                location = pyautogui.locateOnScreen(image_path, confidence=0.8)
                if location:
                    logger.info(f"👁️ CONFIRMED: {image_name} at {location}")
                    return location
            except Exception:
                pass
            time.sleep(1)

        logger.warning(f"👁️ Timed out scanning for {image_name}")
        return False

    @staticmethod
    def click_anchor(image_name: str, timeout: int = 15) -> bool:
        """Find an anchor image and click its center. Returns True on success."""
        location = GhostEyes.wait_for_ui(image_name, timeout)
        if location:
            center = pyautogui.center(location)
            pyautogui.click(center)
            logger.info(f"👁️ Clicked {image_name} at center {center}")
            return True
        return False
