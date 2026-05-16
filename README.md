# 👻 DevOps Pilot

**AI-orchestrated development framework that turns a Telegram message into a deployed application.**

DevOps Pilot bridges the gap between an idea and a working, deployed project. Send a command via Telegram, and the system generates code using AI agents, runs automated tests, sets up databases, and deploys to a staging server — all without touching an IDE.

---

## How It Works

```
Telegram Command → AI Orchestrator → Code Generation → Auto Testing → AWS Deployment
```

1. **`ghost.py`** — Telegram bot listener. Parses commands like `/web PizzaDash Build a pizza ordering dashboard`.
2. **`core/engine.py`** — Prompts Claude/Gemini with the selected template and user requirements.
3. **`core/driver.py`** — Controls the AI IDE to write, iterate, and refine the generated code.
4. **`core/tester.py`** — Validates syntax (PHP lint, Node build, Python checks) and feeds errors back to the AI for self-correction.
5. **`core/dbsetup.py`** — Auto-generates and executes `schema.sql` for MySQL-backed projects.
6. **`core/deployer.py`** — Packages and deploys the final build to an AWS EC2 staging server via SSH.

## Supported Templates

| Template | Stack | File |
|---|---|---|
| PHP Pro | PHP 8 + MySQL + Tailwind | `web_php_pro.txt` |
| Laravel | Laravel + Blade + MySQL | `web_laravel.txt` |
| Node.js | Express + EJS | `web_node.txt` |
| Next.js | React + Next.js 14 | `web_nextjs.txt` |
| Expo | React Native (Expo) | `mobile_expo.txt` |
| Expo Pro | Expo + Firebase + Navigation | `mobile_expo_pro.txt` |
| Flutter | Dart + Flutter | `mobile_flutter.txt` |
| REST API | Express + JWT + Prisma | `api_rest.txt` |
| Electron | Electron + React | `desktop_electron.txt` |

## Tech Stack

- **Runtime:** Python 3.11
- **Bot:** Telegram Bot API (python-telegram-bot)
- **AI Models:** Claude Opus, Gemini 2.5 Pro
- **Infra:** AWS EC2, MySQL, SSH
- **Testing:** PHP linting, Node build validation, automated error-feedback loops

## Typical Workflow

```
User sends: /expo Tadwerak Build a recycling app with wallet and e-commerce
→ AI generates 30+ screens in React Native
→ Tester validates Expo build
→ Deployer pushes to AWS staging
→ Total time: ~25 minutes
```

> **Note:** `config.py` is excluded from this repository as it contains API keys and server credentials.
