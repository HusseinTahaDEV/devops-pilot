"""
🗄️ GhostDB — Automatic Database Setup
Scans project for SQL files and imports them via XAMPP MySQL.
"""
import os
import subprocess
import logging
from pathlib import Path
from config import PROJECTS_ROOT, MYSQL_PATH, MYSQL_USER, MYSQL_PASS

logger = logging.getLogger("ghost.dbsetup")


class GhostDB:
    """Handles automatic MySQL database creation and schema import."""

    @staticmethod
    def find_sql_files(project_name: str) -> list[Path]:
        """Scans a project folder for .sql files."""
        project_path = Path(PROJECTS_ROOT) / project_name
        if not project_path.exists():
            return []
        sql_files = list(project_path.rglob("*.sql"))
        logger.info(f"🗄️ Found {len(sql_files)} SQL files in {project_name}")
        return sql_files

    @staticmethod
    def create_database(db_name: str) -> dict:
        """Drops and recreates a MySQL database for clean imports."""
        result = {"success": False, "message": ""}
        
        # Sanitize db_name (only allow alphanumeric and underscores)
        safe_name = "".join(c if c.isalnum() or c == '_' else '_' for c in db_name)
        
        create_sql = f"DROP DATABASE IF EXISTS `{safe_name}`; CREATE DATABASE `{safe_name}`;"
        try:
            cmd = [MYSQL_PATH, f"-u{MYSQL_USER}"]
            if MYSQL_PASS:
                cmd.append(f"-p{MYSQL_PASS}")
            cmd.extend(["-e", create_sql])
            
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if proc.returncode == 0:
                result["success"] = True
                result["message"] = f"Database `{safe_name}` created/verified."
                logger.info(f"🗄️ {result['message']}")
            else:
                result["message"] = f"MySQL error: {proc.stderr.strip()}"
                logger.error(f"🗄️ {result['message']}")
        except FileNotFoundError:
            result["message"] = f"MySQL not found at: {MYSQL_PATH}"
            logger.error(f"🗄️ {result['message']}")
        except subprocess.TimeoutExpired:
            result["message"] = "MySQL command timed out."
            logger.error(f"🗄️ {result['message']}")
        except Exception as e:
            result["message"] = f"DB creation error: {e}"
            logger.error(f"🗄️ {result['message']}")
        
        return result

    @staticmethod
    def import_sql(project_name: str, sql_file: Path) -> dict:
        """Imports a SQL file into the project's database."""
        result = {"success": False, "message": ""}
        
        safe_name = "".join(c if c.isalnum() or c == '_' else '_' for c in project_name)
        
        try:
            cmd = [MYSQL_PATH, f"-u{MYSQL_USER}"]
            if MYSQL_PASS:
                cmd.append(f"-p{MYSQL_PASS}")
            cmd.append(safe_name)
            
            with open(sql_file, 'r', encoding='utf-8') as f:
                proc = subprocess.run(cmd, stdin=f, capture_output=True, text=True, timeout=30)
            
            if proc.returncode == 0:
                result["success"] = True
                result["message"] = f"Imported {sql_file.name} into `{safe_name}`."
                logger.info(f"🗄️ {result['message']}")
            else:
                result["message"] = f"Import error: {proc.stderr.strip()}"
                logger.error(f"🗄️ {result['message']}")
        except Exception as e:
            result["message"] = f"SQL import error: {e}"
            logger.error(f"🗄️ {result['message']}")
        
        return result

    @staticmethod
    def setup(project_name: str) -> dict:
        """
        Full DB setup pipeline:
        1. Find SQL files
        2. Create database
        3. Import each SQL file
        Returns aggregated result.
        """
        report = {
            "success": False,
            "db_created": False,
            "files_imported": [],
            "errors": [],
            "message": ""
        }

        # 1. Find SQL files
        sql_files = GhostDB.find_sql_files(project_name)
        if not sql_files:
            report["message"] = "No SQL files found in project."
            logger.info(f"🗄️ {report['message']}")
            return report

        # 2. Create database
        db_result = GhostDB.create_database(project_name)
        report["db_created"] = db_result["success"]
        if not db_result["success"]:
            report["errors"].append(db_result["message"])
            report["message"] = db_result["message"]
            return report

        # 3. Import SQL files (prioritize schema.sql first)
        sql_files.sort(key=lambda f: (0 if f.name == "schema.sql" else 1, f.name))
        
        for sql_file in sql_files:
            imp_result = GhostDB.import_sql(project_name, sql_file)
            if imp_result["success"]:
                report["files_imported"].append(sql_file.name)
            else:
                report["errors"].append(f"{sql_file.name}: {imp_result['message']}")

        report["success"] = len(report["errors"]) == 0
        report["message"] = (
            f"DB setup complete: {len(report['files_imported'])} files imported"
            + (f", {len(report['errors'])} errors" if report["errors"] else "")
        )
        logger.info(f"🗄️ {report['message']}")
        return report
