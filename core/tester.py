"""
🧪 GhostTester — Automated Testing Pipeline
Runs tests against built projects and generates reports.
"""
import os
import subprocess
import logging
import json
import time
from pathlib import Path
from datetime import datetime
from config import PROJECTS_ROOT, PHP_PATH

logger = logging.getLogger("ghost.tester")


class GhostTester:
    """Runs automated tests on projects and generates reports."""

    @staticmethod
    def detect_stack(project_path: Path) -> str:
        """Detects the project stack by examining files."""
        if (project_path / "package.json").exists():
            pkg = json.loads((project_path / "package.json").read_text(encoding='utf-8'))
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "next" in deps:
                return "nextjs"
            if "react-native" in deps or "expo" in deps:
                return "expo"
            if "electron" in deps:
                return "electron"
            if "express" in deps:
                return "node"
            return "node"
        if (project_path / "composer.json").exists():
            return "laravel"
        if (project_path / "pubspec.yaml").exists():
            return "flutter"
        # Check for PHP files
        php_files = list(project_path.rglob("*.php"))
        if php_files:
            return "php"
        return "unknown"

    @staticmethod
    def test_php(project_path: Path) -> dict:
        """Tests a PHP project: syntax check all files, check for schema.sql."""
        report = {"stack": "php", "tests": [], "passed": 0, "failed": 0, "warnings": []}

        # Syntax check all PHP files
        php_files = list(project_path.rglob("*.php"))
        report["tests"].append({
            "name": "PHP Files Found",
            "status": "pass" if php_files else "fail",
            "detail": f"{len(php_files)} PHP files"
        })

        syntax_errors = []
        for php_file in php_files:
            try:
                proc = subprocess.run(
                    [PHP_PATH, "-l", str(php_file)],
                    capture_output=True, text=True, timeout=10
                )
                if proc.returncode != 0:
                    syntax_errors.append(f"{php_file.name}: {proc.stdout.strip()}")
            except FileNotFoundError:
                report["warnings"].append("PHP CLI not found. Cannot syntax check.")
                break
            except Exception as e:
                syntax_errors.append(f"{php_file.name}: {e}")

        if syntax_errors:
            report["tests"].append({
                "name": "PHP Syntax Check",
                "status": "fail",
                "detail": "\n".join(syntax_errors[:10])
            })
            report["failed"] += 1
        else:
            report["tests"].append({
                "name": "PHP Syntax Check",
                "status": "pass",
                "detail": f"All {len(php_files)} files clean"
            })
            report["passed"] += 1

        # Check for config.php
        has_config = (project_path / "config.php").exists()
        report["tests"].append({
            "name": "config.php exists",
            "status": "pass" if has_config else "warn",
            "detail": "Found" if has_config else "Missing — DB connection may fail"
        })
        if has_config:
            report["passed"] += 1

        # Check for schema.sql
        sql_files = list(project_path.rglob("*.sql"))
        report["tests"].append({
            "name": "SQL Schema",
            "status": "pass" if sql_files else "warn",
            "detail": f"{len(sql_files)} SQL files found" if sql_files else "No schema.sql found"
        })
        if sql_files:
            report["passed"] += 1

        # Check for required structure
        for check_dir in ["engines", "includes", "assets"]:
            exists = (project_path / check_dir).exists()
            report["tests"].append({
                "name": f"/{check_dir}/ directory",
                "status": "pass" if exists else "warn",
                "detail": "Present" if exists else "Missing"
            })
            if exists:
                report["passed"] += 1

        return report

    @staticmethod
    def test_node(project_path: Path) -> dict:
        """Tests a Node.js project: check packages, run npm test if available."""
        report = {"stack": "node", "tests": [], "passed": 0, "failed": 0, "warnings": []}

        # Check package.json
        pkg_path = project_path / "package.json"
        if pkg_path.exists():
            report["tests"].append({"name": "package.json", "status": "pass", "detail": "Found"})
            report["passed"] += 1
            
            pkg = json.loads(pkg_path.read_text(encoding='utf-8'))
            
            # Check for test script
            scripts = pkg.get("scripts", {})
            has_test = "test" in scripts and "no test" not in scripts.get("test", "")
            report["tests"].append({
                "name": "Test script defined",
                "status": "pass" if has_test else "warn",
                "detail": scripts.get("test", "Not defined")
            })

            # Check node_modules
            has_modules = (project_path / "node_modules").exists()
            report["tests"].append({
                "name": "node_modules installed",
                "status": "pass" if has_modules else "warn",
                "detail": "Present" if has_modules else "Run npm install first"
            })

            # If test script exists AND node_modules exists, run tests
            if has_test and has_modules:
                try:
                    proc = subprocess.run(
                        ["npm", "test"],
                        cwd=str(project_path),
                        capture_output=True, text=True, timeout=60,
                        shell=True
                    )
                    report["tests"].append({
                        "name": "npm test",
                        "status": "pass" if proc.returncode == 0 else "fail",
                        "detail": proc.stdout[-500:] if proc.stdout else proc.stderr[-500:]
                    })
                    if proc.returncode == 0:
                        report["passed"] += 1
                    else:
                        report["failed"] += 1
                except subprocess.TimeoutExpired:
                    report["tests"].append({
                        "name": "npm test",
                        "status": "warn",
                        "detail": "Test execution timed out (60s)"
                    })
        else:
            report["tests"].append({"name": "package.json", "status": "fail", "detail": "Missing"})
            report["failed"] += 1

        # Check for server.js or index.js or app.js
        entry_files = ["server.js", "index.js", "app.js", "src/index.js"]
        found_entry = any((project_path / f).exists() for f in entry_files)
        report["tests"].append({
            "name": "Entry point",
            "status": "pass" if found_entry else "warn",
            "detail": "Found" if found_entry else "No standard entry point found"
        })
        if found_entry:
            report["passed"] += 1

        return report

    @staticmethod
    def test_mobile(project_path: Path) -> dict:
        """Tests a React Native/Expo project."""
        report = {"stack": "expo", "tests": [], "passed": 0, "failed": 0, "warnings": []}

        # Check app.json
        app_json = project_path / "app.json"
        report["tests"].append({
            "name": "app.json",
            "status": "pass" if app_json.exists() else "fail",
            "detail": "Found" if app_json.exists() else "Missing"
        })
        if app_json.exists():
            report["passed"] += 1
        else:
            report["failed"] += 1

        # Check App.js
        app_entry = (project_path / "App.js").exists() or (project_path / "App.tsx").exists()
        report["tests"].append({
            "name": "App entry point",
            "status": "pass" if app_entry else "fail",
            "detail": "Found" if app_entry else "Missing"
        })

        # Check src/ structure
        for check_dir in ["src/screens", "src/components", "src/navigation"]:
            exists = (project_path / check_dir).exists()
            report["tests"].append({
                "name": f"{check_dir}/",
                "status": "pass" if exists else "warn",
                "detail": "Present" if exists else "Missing"
            })
            if exists:
                report["passed"] += 1

        # Run expo doctor if available
        if (project_path / "node_modules").exists():
            try:
                proc = subprocess.run(
                    ["npx", "expo", "doctor"],
                    cwd=str(project_path),
                    capture_output=True, text=True, timeout=30,
                    shell=True
                )
                report["tests"].append({
                    "name": "expo doctor",
                    "status": "pass" if proc.returncode == 0 else "warn",
                    "detail": proc.stdout[-300:] if proc.stdout else "No output"
                })
            except Exception:
                report["warnings"].append("Could not run expo doctor")

        return report

    @staticmethod
    def test_flutter(project_path: Path) -> dict:
        """Tests a Flutter project."""
        report = {"stack": "flutter", "tests": [], "passed": 0, "failed": 0, "warnings": []}

        pubspec = project_path / "pubspec.yaml"
        report["tests"].append({
            "name": "pubspec.yaml",
            "status": "pass" if pubspec.exists() else "fail",
            "detail": "Found" if pubspec.exists() else "Missing"
        })
        if pubspec.exists():
            report["passed"] += 1

        main_dart = project_path / "lib" / "main.dart"
        report["tests"].append({
            "name": "lib/main.dart",
            "status": "pass" if main_dart.exists() else "fail",
            "detail": "Found" if main_dart.exists() else "Missing"
        })

        # Check structure
        for check_dir in ["lib/screens", "lib/models", "lib/services"]:
            exists = (project_path / check_dir).exists()
            report["tests"].append({
                "name": f"{check_dir}/",
                "status": "pass" if exists else "warn",
                "detail": "Present" if exists else "Missing"
            })
            if exists:
                report["passed"] += 1

        # Flutter analyze
        try:
            proc = subprocess.run(
                ["flutter", "analyze"],
                cwd=str(project_path),
                capture_output=True, text=True, timeout=60
            )
            report["tests"].append({
                "name": "flutter analyze",
                "status": "pass" if proc.returncode == 0 else "warn",
                "detail": proc.stdout[-300:] if proc.stdout else proc.stderr[-300:]
            })
        except Exception:
            report["warnings"].append("Flutter CLI not available")

        return report

    @staticmethod
    def run(project_name: str) -> dict:
        """
        Main test runner. Detects stack and runs appropriate tests.
        Returns a full test report.
        """
        project_path = Path(PROJECTS_ROOT) / project_name
        if not project_path.exists():
            return {"success": False, "message": f"Project not found: {project_name}"}

        stack = GhostTester.detect_stack(project_path)
        logger.info(f"🧪 Detected stack: {stack} for {project_name}")

        # Route to correct tester
        testers = {
            "php": GhostTester.test_php,
            "node": GhostTester.test_node,
            "nextjs": GhostTester.test_node,
            "expo": GhostTester.test_mobile,
            "electron": GhostTester.test_node,
            "laravel": GhostTester.test_php,
            "flutter": GhostTester.test_flutter,
        }

        tester = testers.get(stack)
        if not tester:
            return {
                "success": False,
                "message": f"No tester available for stack: {stack}",
                "stack": stack
            }

        report = tester(project_path)
        report["project"] = project_name
        report["timestamp"] = datetime.now().isoformat()

        # Count totals
        total = len(report["tests"])
        passed = sum(1 for t in report["tests"] if t["status"] == "pass")
        failed = sum(1 for t in report["tests"] if t["status"] == "fail")
        warned = sum(1 for t in report["tests"] if t["status"] == "warn")

        report["summary"] = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "warnings": warned,
            "health": "🟢 HEALTHY" if failed == 0 else "🔴 ISSUES FOUND" if failed > 2 else "🟡 MINOR ISSUES"
        }

        logger.info(f"🧪 Test complete: {passed}/{total} passed, {failed} failed, {warned} warnings")
        return report

    @staticmethod
    def format_report(report: dict) -> str:
        """Formats a test report into a readable Telegram message."""
        if "message" in report and not report.get("tests"):
            return f"❌ {report['message']}"

        summary = report.get("summary", {})
        lines = [
            f"🧪 *Test Report: {report['project']}*",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"📋 Stack: `{report.get('stack', 'unknown')}`",
            f"🏥 Health: {summary.get('health', '?')}",
            f"✅ Passed: {summary.get('passed', 0)} | ❌ Failed: {summary.get('failed', 0)} | ⚠️ Warnings: {summary.get('warnings', 0)}",
            "",
            "*Details:*",
        ]

        for t in report.get("tests", []):
            icon = {"pass": "✅", "fail": "❌", "warn": "⚠️"}.get(t["status"], "❓")
            lines.append(f"{icon} {t['name']}")
            if t["status"] != "pass" and t.get("detail"):
                # Truncate long details
                detail = t["detail"][:150]
                lines.append(f"   _{detail}_")

        if report.get("warnings"):
            lines.append("\n*⚠️ Warnings:*")
            for w in report["warnings"]:
                lines.append(f"  • {w}")

        return "\n".join(lines)

    @staticmethod
    def generate_bug_prompt(report: dict) -> str | None:
        """
        Generates a prompt to send back to Antigravity to fix issues.
        Returns None if no issues found.
        """
        failures = [t for t in report.get("tests", []) if t["status"] == "fail"]
        warnings = [t for t in report.get("tests", []) if t["status"] == "warn"]

        if not failures and not warnings:
            return None

        lines = [
            "AUTOMATED TEST RESULTS — FIX THESE ISSUES:",
            "",
            f"Project: {report.get('project', 'unknown')}",
            f"Stack: {report.get('stack', 'unknown')}",
            "",
        ]

        if failures:
            lines.append("❌ CRITICAL FAILURES (Must Fix):")
            for f in failures:
                lines.append(f"  - {f['name']}: {f.get('detail', 'No details')}")
            lines.append("")

        if warnings:
            lines.append("⚠️ WARNINGS (Should Fix):")
            for w in warnings:
                lines.append(f"  - {w['name']}: {w.get('detail', 'No details')}")
            lines.append("")

        lines.append("Fix ALL issues above. Do not explain, just fix the code.")
        return "\n".join(lines)

    # ══════════════════════════════════════════════
    #  FULL TEST + GAP ANALYSIS + IMPLEMENT (ONE SHOT)
    # ══════════════════════════════════════════════

    @staticmethod
    def generate_full_test_prompt(project_name: str, stack: str) -> str:
        """
        Single mega-prompt: live test + gap analysis + implement ALL gaps.
        Template-specific — tailored tests for each stack type.
        """
        stack_tests = {
            "php": (
                "## PHP / MySQL Full-Stack Tests\n"
                "1. Open EVERY .php file — verify no Fatal/Parse/Warning errors\n"
                "2. Test ALL MySQL queries: INSERT, SELECT, UPDATE, DELETE on every table\n"
                "3. Test EVERY form: login, register, CRUD forms, search\n"
                "4. Verify sessions: login → protected route → logout → redirect\n"
                "5. Test ALL AJAX/fetch calls — verify JSON responses\n"
                "6. Verify config.php DB credentials\n"
                "7. Test file uploads if present\n"
                "8. Verify engines/ architecture — all engines return valid data\n"
                "9. Test pagination, search, filters, sorting on listings\n"
                "10. Verify all includes/requires resolve\n"
                "11. Test with empty database — graceful handling\n"
                "12. Test admin vs user role separation\n"
            ),
            "laravel": (
                "## Laravel Full-Stack Tests\n"
                "1. Run `php artisan migrate --force` — all migrations pass\n"
                "2. Run `php artisan db:seed` — seeders execute cleanly\n"
                "3. Test EVERY route in routes/web.php and routes/api.php\n"
                "4. Verify ALL controllers: index, create, store, show, edit, update, destroy\n"
                "5. Test Blade views — no undefined vars, proper @extends/@section\n"
                "6. Test middleware — auth, admin, guest guards\n"
                "7. Verify Eloquent relationships — hasMany, belongsTo, etc.\n"
                "8. Test form validation — required, unique, email format\n"
                "9. Verify CSRF tokens on all forms\n"
                "10. Test API endpoints with JSON responses and status codes\n"
                "11. Check .env matches database config\n"
                "12. Test queues and scheduled tasks if present\n"
            ),
            "node": (
                "## Node.js / Express Full-Stack Tests\n"
                "1. Start server — verify correct port, no errors\n"
                "2. Test EVERY endpoint: GET, POST, PUT, PATCH, DELETE\n"
                "3. Verify JWT/session auth — login, token refresh, logout\n"
                "4. Test middleware chain — auth, validation, error handling, CORS\n"
                "5. Test ALL database queries\n"
                "6. Verify request body validation on POST/PUT\n"
                "7. Test error responses — 400, 401, 403, 404, 500 with JSON\n"
                "8. Verify env vars loaded correctly\n"
                "9. Test rate limiting if present\n"
                "10. Verify proper error logging\n"
                "11. Test with invalid/missing request params\n"
                "12. Check for SQL injection in raw queries\n"
            ),
            "nextjs": (
                "## Next.js Full-Stack Tests\n"
                "1. Verify ALL pages render — SSR and client-side\n"
                "2. Test EVERY API route in app/api/ or pages/api/\n"
                "3. Verify Server vs Client Components correct\n"
                "4. Test form submissions — client-side and server actions\n"
                "5. Verify auth flow — login, register, protected page redirect\n"
                "6. Test DB ops via Prisma/Drizzle ORM\n"
                "7. Verify loading.tsx, error.tsx, not-found.tsx\n"
                "8. Test client navigation — Link, useRouter\n"
                "9. Verify .env.local variables\n"
                "10. Test metadata on every page\n"
                "11. Verify middleware.ts protects routes\n"
                "12. Test dynamic routes with valid/invalid params\n"
            ),
            "expo": (
                "## React Native / Expo Tests\n"
                "1. Verify App.js/App.tsx renders without crash\n"
                "2. Test ALL screen navigation — stack, tabs, drawer\n"
                "3. Verify EVERY API call — URL, headers, body\n"
                "4. Test all form inputs — validation, submission, errors\n"
                "5. Verify AsyncStorage/SecureStore operations\n"
                "6. Test auth flow — login, token storage, auto-login, logout\n"
                "7. Verify image loading — local and remote\n"
                "8. Test pull-to-refresh, infinite scroll, loading\n"
                "9. Check app.json — name, slug, permissions\n"
                "10. Verify error boundaries and fallback screens\n"
                "11. Test deep linking if configured\n"
                "12. Verify icons and fonts load\n"
            ),
            "flutter": (
                "## Flutter / Dart Tests\n"
                "1. Run `flutter analyze` — fix ALL warnings\n"
                "2. Verify main.dart builds without errors\n"
                "3. Test ALL screen navigation routes\n"
                "4. Verify state management — Provider/Bloc/Riverpod\n"
                "5. Test ALL API service calls\n"
                "6. Test form validation and submission\n"
                "7. Verify SharedPreferences/Hive operations\n"
                "8. Test auth flow — login, token persist, logout\n"
                "9. Check pubspec.yaml dependencies\n"
                "10. Test widget rendering on different sizes\n"
                "11. Verify HTTP error handling\n"
                "12. Test image assets and custom fonts\n"
            ),
            "api": (
                "## REST API Tests\n"
                "1. Test EVERY endpoint — correct HTTP methods\n"
                "2. Verify JWT auth — generate, validate, refresh, revoke\n"
                "3. Test CRUD on EVERY resource: POST, GET, GET/:id, PUT, DELETE\n"
                "4. Verify request validation — required, types, constraints\n"
                "5. Test error responses — 400, 401, 404, 500\n"
                "6. Verify pagination — page, limit, total count\n"
                "7. Test search and filter query params\n"
                "8. Verify response format consistency\n"
                "9. Test rate limiting\n"
                "10. Verify Swagger/OpenAPI accuracy\n"
                "11. Test with malformed JSON bodies\n"
                "12. Verify CORS headers\n"
            ),
            "electron": (
                "## Electron / Desktop Tests\n"
                "1. Verify app launches — main process no errors\n"
                "2. Test ALL IPC channels — main ↔ renderer\n"
                "3. Verify ALL windows open/resize/close\n"
                "4. Test menu bar — all items trigger correct actions\n"
                "5. Test system tray — icon, context menu, click\n"
                "6. Verify file system operations — read/write/dialog\n"
                "7. Test all React/Vue renderer components\n"
                "8. Verify auto-updater config\n"
                "9. Test keyboard shortcuts\n"
                "10. Verify window state persistence\n"
                "11. Test notifications\n"
                "12. Verify CSP and webPreferences security\n"
            ),
        }

        specific = stack_tests.get(stack, stack_tests.get("node", ""))

        return (
            f"{'='*60}\n"
            f"🧪 GHOST PROTOCOL — FULL APPLICATION TEST & COMPLETION\n"
            f"{'='*60}\n"
            f"Project: {project_name} | Stack: {stack}\n\n"
            f"This is a 3-STEP process. Complete ALL steps IN ORDER.\n"
            f"Do NOT stop after Step 1. You MUST do all 3 steps.\n\n"
            f"{'━'*60}\n"
            f"STEP 1: LIVE TEST — Test EVERYTHING\n"
            f"{'━'*60}\n\n"
            f"Actually run/verify each item. Do NOT say 'looks fine'.\n\n"
            f"{specific}\n"
            f"### General Tests (ALL stacks)\n"
            f"- Test auth: login valid/invalid, register, logout, protected routes\n"
            f"- Test EVERY CRUD entity: create, read, list, update, delete\n"
            f"- Test error handling: 404 page, invalid input, empty states\n"
            f"- Test UI: responsive layout, all links work, images load\n"
            f"- Fix ANY bug you find IMMEDIATELY.\n\n"
            f"{'━'*60}\n"
            f"STEP 2: GAP ANALYSIS — Create gap_analysis.md\n"
            f"{'━'*60}\n\n"
            f"Create `gap_analysis.md` in project root. Mark each as:\n"
            f"  ❌ MISSING — not implemented\n"
            f"  ⚠️ INCOMPLETE — partially done\n"
            f"  🐛 BROKEN — has bugs\n\n"
            f"Categories: Auth & Roles | Database & Models | API Endpoints |\n"
            f"CRUD per entity | Frontend UI | Security | Error Handling | Config\n\n"
            f"Format: Category | Description | Priority (HIGH/MED/LOW)\n"
            f"Be BRUTALLY honest. Miss nothing.\n\n"
            f"{'━'*60}\n"
            f"STEP 3: IMPLEMENT ALL GAPS\n"
            f"{'━'*60}\n\n"
            f"Read gap_analysis.md. IMPLEMENT EVERY GAP:\n"
            f"  1. HIGH priority first, then MED, then LOW\n"
            f"  2. Write REAL code, not stubs\n"
            f"  3. Create new files if needed\n"
            f"  4. Update schema.sql if needed\n"
            f"  5. Test after implementing\n"
            f"  6. Mark completed items ✅ in gap_analysis.md\n\n"
            f"START NOW. All 3 steps. No shortcuts.\n"
        )

