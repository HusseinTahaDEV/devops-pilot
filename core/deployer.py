"""
🚀 GhostDeployer — Staging Deployment Pipeline
SCP project files to production server staging container.
"""
import subprocess
import logging
from pathlib import Path
from config import PROJECTS_ROOT, STAGING_HOST, STAGING_USER, STAGING_PATH, STAGING_URL

logger = logging.getLogger("ghost.deployer")


class GhostDeployer:
    """Handles deployment of projects to staging server."""

    @staticmethod
    def deploy_to_staging(project_name: str) -> dict:
        """
        Copies project files to the staging server via SCP.
        Returns dict with success status and details.
        """
        result = {"success": False, "message": "", "url": ""}
        project_path = Path(PROJECTS_ROOT) / project_name

        if not project_path.exists():
            result["message"] = f"Project not found: {project_name}"
            return result

        # Create project subdirectory on staging server
        remote_dir = f"{STAGING_PATH}/{project_name}"
        try:
            # Create remote dir
            subprocess.run(
                ["ssh", STAGING_HOST, f"mkdir -p {remote_dir}"],
                capture_output=True, text=True, timeout=15
            )
            logger.info(f"📁 Created remote dir: {remote_dir}")

            # SCP project files (recursive)
            proc = subprocess.run(
                ["scp", "-r", f"{project_path}/.", f"{STAGING_HOST}:{remote_dir}/"],
                capture_output=True, text=True, timeout=120
            )

            if proc.returncode == 0:
                result["success"] = True
                result["url"] = f"{STAGING_URL}/{project_name}"
                result["message"] = f"Deployed to {result['url']}"
                logger.info(f"✅ Deployed {project_name} to staging: {result['url']}")
            else:
                result["message"] = f"SCP failed: {proc.stderr[:200]}"
                logger.error(f"❌ SCP failed: {proc.stderr[:200]}")

        except subprocess.TimeoutExpired:
            result["message"] = "Deployment timed out (120s)"
            logger.error("❌ SCP timed out")
        except Exception as e:
            result["message"] = f"Deployment error: {e}"
            logger.error(f"❌ Deploy error: {e}")

        return result

    @staticmethod
    def generate_deploy_prompt(project_name: str, stack: str) -> str:
        """
        Generates a prompt with REAL server details and SCP/SSH commands.
        The AI will know exactly how to deploy and configure on the server.
        """
        stack_instructions = {
            "php": (
                "## PHP-Specific Config for Staging\n"
                "1. Update config.php database credentials:\n"
                "   - host: 'localhost'\n"
                "   - user: 'root'\n"
                "   - pass: '' (empty)\n"
                "   - dbname: same as project name\n"
                "2. Create .htaccess with: RewriteEngine On, RewriteBase /\n"
                "3. Replace ALL absolute URLs with relative ones\n"
                "4. Replace ALL hardcoded localhost with relative paths\n"
                "5. Verify includes/requires use relative paths\n"
            ),
            "laravel": (
                "## Laravel-Specific Config for Staging\n"
                "1. Update .env:\n"
                f"   - APP_URL=https://dev.hussein.top/{project_name}\n"
                "   - DB_HOST=localhost\n"
                f"   - DB_DATABASE={project_name}\n"
                "   - DB_USERNAME=root, DB_PASSWORD=(empty)\n"
                "2. Run on server: cd /home/ubuntu/staging/" + project_name + " && composer install --no-dev\n"
                "3. Run: php artisan migrate --force && php artisan db:seed\n"
                "4. Run: php artisan config:cache && php artisan route:cache\n"
            ),
            "node": (
                "## Node.js-Specific Config for Staging\n"
                "1. Update .env: PORT=3000, NODE_ENV=production, DB_HOST=localhost\n"
                "2. Run on server: cd /home/ubuntu/staging/" + project_name + " && npm install --production\n"
                "3. Run: npm run build (if build script exists)\n"
                "4. Start with: npm start or node server.js\n"
            ),
            "nextjs": (
                "## Next.js-Specific Config for Staging\n"
                f"1. Update .env.local: NEXTAUTH_URL=https://dev.hussein.top/{project_name}\n"
                "2. Run on server: cd /home/ubuntu/staging/" + project_name + " && npm install && npm run build\n"
                "3. Start with: npm start\n"
            ),
        }

        specific = stack_instructions.get(stack, stack_instructions.get("php", ""))

        return (
            f"{'='*60}\n"
            f"🚀 GHOST PROTOCOL — DEPLOY TO STAGING SERVER\n"
            f"{'='*60}\n"
            f"Project: {project_name} | Stack: {stack}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"SERVER DETAILS (PRODUCTION AWS)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"SSH:        ssh aws-prod (alias configured)\n"
            f"User:       ubuntu\n"
            f"OS:         Ubuntu 24.04\n"
            f"Web Root:   /home/ubuntu/staging/{project_name}/\n"
            f"Container:  ghost-staging (PHP 8.2 + Apache, port 9091)\n"
            f"URL:        https://dev.hussein.top/{project_name}\n"
            f"Tunnel:     Cloudflare (cloudflared → localhost:9091)\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"DEPLOYMENT STEPS — DO ALL OF THESE\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"STEP 1: PREPARE CODE FOR PRODUCTION\n"
            f"- Remove ALL debug output (console.log, var_dump, print_r, dd())\n"
            f"- Remove ALL hardcoded 'localhost' and '127.0.0.1' URLs\n"
            f"- Make ALL URLs relative (no http://localhost:xxxx)\n"
            f"- Secure credentials in .env or config (not hardcoded)\n"
            f"- Ensure error pages exist (404, 500)\n"
            f"- Update database config for production (see stack-specific below)\n\n"
            f"{specific}\n"
            f"STEP 2: COPY FILES TO SERVER\n"
            f"Run these commands from the project directory:\n"
            f"```\n"
            f"# Create project folder on server\n"
            f"ssh aws-prod \"mkdir -p /home/ubuntu/staging/{project_name}\"\n\n"
            f"# Copy ALL project files to server\n"
            f"scp -r ./* aws-prod:/home/ubuntu/staging/{project_name}/\n"
            f"```\n\n"
            f"STEP 3: IMPORT DATABASE ON SERVER (if SQL exists)\n"
            f"```\n"
            f"# SSH into server\n"
            f"ssh aws-prod\n\n"
            f"# Create database and import schema\n"
            f"sudo docker exec ghost-staging bash -c \"\n"
            f"  apt-get update && apt-get install -y default-mysql-client\n"
            f"  mysql -h host.docker.internal -u root -e 'CREATE DATABASE IF NOT EXISTS {project_name}'\n"
            f"  mysql -h host.docker.internal -u root {project_name} < /var/www/html/{project_name}/schema.sql\n"
            f"\"\n"
            f"```\n\n"
            f"STEP 4: VERIFY\n"
            f"- Visit https://dev.hussein.top/{project_name}\n"
            f"- Test login/register\n"
            f"- Test CRUD operations\n"
            f"- Check for console errors\n\n"
            f"⚠️ IMPORTANT: The /home/ubuntu/staging/ directory is the Docker\n"
            f"volume mount. Files placed there appear at /var/www/html/ inside\n"
            f"the container. Apache serves from there automatically.\n\n"
            f"DO ALL STEPS NOW. Prepare code, copy, and verify.\n"
        )

