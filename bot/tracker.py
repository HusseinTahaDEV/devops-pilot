"""
📊 GhostTracker — Deployment Logger
Tracks all deployments in a JSON file for /status and /projects commands.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from config import TRACKER_FILE, PROJECTS_ROOT

logger = logging.getLogger("ghost.tracker")


class GhostTracker:
    """Manages deployment history as a JSON log."""

    @staticmethod
    def _load() -> list[dict]:
        """Loads deployments from JSON file."""
        if TRACKER_FILE.exists():
            try:
                return json.loads(TRACKER_FILE.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, Exception):
                return []
        return []

    @staticmethod
    def _save(data: list[dict]):
        """Saves deployments to JSON file."""
        TRACKER_FILE.write_text(json.dumps(data, indent=2, default=str), encoding='utf-8')

    @staticmethod
    def log_deployment(name: str, template: str, status: str, model: str = None):
        """Logs a new deployment."""
        deployments = GhostTracker._load()
        entry = {
            "name": name,
            "template": template,
            "model": model or "default",
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "path": str(Path(PROJECTS_ROOT) / name),
        }
        deployments.append(entry)
        GhostTracker._save(deployments)
        logger.info(f"📊 Logged deployment: {name} ({template}) → {status}")

    @staticmethod
    def update_status(name: str, status: str):
        """Updates the status of the most recent deployment for a project."""
        deployments = GhostTracker._load()
        for d in reversed(deployments):
            if d["name"] == name:
                d["status"] = status
                break
        GhostTracker._save(deployments)

    @staticmethod
    def get_recent(count: int = 10) -> list[dict]:
        """Returns the most recent deployments."""
        deployments = GhostTracker._load()
        return deployments[-count:]

    @staticmethod
    def get_all_projects() -> list[dict]:
        """Lists all projects from the GhostProjects directory with deployment info."""
        projects = []
        if not PROJECTS_ROOT.exists():
            return projects

        deployments = {d["name"]: d for d in GhostTracker._load()}

        for folder in sorted(PROJECTS_ROOT.iterdir()):
            if folder.is_dir():
                deploy_info = deployments.get(folder.name, {})
                file_count = sum(1 for _ in folder.rglob('*') if _.is_file())
                projects.append({
                    "name": folder.name,
                    "path": str(folder),
                    "files": file_count,
                    "template": deploy_info.get("template", "unknown"),
                    "deployed": deploy_info.get("timestamp", "—"),
                    "status": deploy_info.get("status", "unknown"),
                })
        return projects

    @staticmethod
    def get_stats() -> dict:
        """Returns overall statistics."""
        deployments = GhostTracker._load()
        return {
            "total_deployments": len(deployments),
            "successful": sum(1 for d in deployments if d["status"] == "success"),
            "failed": sum(1 for d in deployments if d["status"] == "failed"),
            "templates_used": list(set(d["template"] for d in deployments)),
        }
