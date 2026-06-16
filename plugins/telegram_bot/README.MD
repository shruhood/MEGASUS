# Telegram Bot Plugin

Remote control MEGASUS via Telegram Bot API.

## Setup

1. Create a bot with @BotFather on Telegram
2. Get your bot token
3. Update config.json with your token
4. Restart MEGASUS

## Commands

- /m help - Show help
- /m info - Device info
- /m battery - Battery status
- /m apps - List user apps
- /m screenshot - Take screenshot
- /m shell CMD - Execute shell command
- /m devices - Device details
- /m dump - Full device dump

## Files

- plugin.py - Entrypoint and lifecycle
- telegram_client.py - Telegram Bot API wrapper
- adb_manager.py - ADB device management
- commands.py - Command handlers
- config.py - Config loading/validation
- config.json - Bot configuration
