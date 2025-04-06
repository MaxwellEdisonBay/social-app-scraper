#!/usr/bin/env python
# telegram_bot.py
import os
import logging
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from handlers.telegram_handler import TelegramHandler

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("telegram_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("telegram_bot")

class TelegramBot:
    """
    Telegram bot for managing subscribers and handling commands using python-telegram-bot.
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the Telegram bot.
        
        Args:
            token (str, optional): Telegram bot token. If not provided, will try to get from environment.
        """
        self.handler = TelegramHandler(token=token)
        if not self.handler.enabled:
            logger.error("Telegram bot is not enabled. Please provide a valid token.")
            return
            
        self.token = self.handler.token
        self.application = Application.builder().token(self.token).build()
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("subscribe", self.subscribe_command))
        self.application.add_handler(CommandHandler("unsubscribe", self.unsubscribe_command))
        self.application.add_handler(CommandHandler("list", self.list_command))
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /start command."""
        await self.send_welcome_message(update.effective_chat.id)
        
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /help command."""
        await self.send_help_message(update.effective_chat.id)
        
    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /subscribe command."""
        chat_id = update.effective_chat.id
        source = context.args[0] if context.args else "all"
        
        if self.handler.add_subscriber(chat_id, source):
            await self.handler.send_message(
                chat_id,
                f"You have been subscribed to {source} news updates."
            )
        else:
            await self.handler.send_message(
                chat_id,
                "Failed to subscribe. Please try again later."
            )
            
    async def unsubscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /unsubscribe command."""
        chat_id = update.effective_chat.id
        source = context.args[0] if context.args else "all"
        
        if self.handler.remove_subscriber(chat_id, source):
            await self.handler.send_message(
                chat_id,
                f"You have been unsubscribed from {source} news updates."
            )
        else:
            await self.handler.send_message(
                chat_id,
                f"You were not subscribed to {source} news updates."
            )
            
    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /list command."""
        chat_id = update.effective_chat.id
        subscriptions = []
        
        for source, subscribers in self.handler.subscribers.items():
            if chat_id in subscribers:
                subscriptions.append(source)
                
        if subscriptions:
            message = "Your current subscriptions:\n\n"
            for source in subscriptions:
                message += f"- {source}\n"
        else:
            message = "You are not subscribed to any news updates."
            
        await this.handler.send_message(chat_id, message)
        
    async def send_welcome_message(self, chat_id: int) -> None:
        """
        Send a welcome message.
        
        Args:
            chat_id (int): Telegram chat ID.
        """
        message = (
            "Welcome to the Ukrainian News Bot! 🇺🇦\n\n"
            "This bot provides news about Ukraine and related topics.\n\n"
            "Use /subscribe to subscribe to news updates.\n"
            "Use /help to see all available commands."
        )
        await this.handler.send_message(chat_id, message)
        
    async def send_help_message(self, chat_id: int) -> None:
        """
        Send a help message.
        
        Args:
            chat_id (int): Telegram chat ID.
        """
        message = (
            "Available commands:\n\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/subscribe [source] - Subscribe to news updates (optional: specify source)\n"
            "/unsubscribe [source] - Unsubscribe from news updates (optional: specify source)\n"
            "/list - List your current subscriptions"
        )
        await this.handler.send_message(chat_id, message)
        
    def run(self) -> None:
        """Run the bot."""
        if not self.handler.enabled:
            logger.error("Telegram bot is not enabled. Please provide a valid token.")
            return
            
        logger.info("Starting Telegram bot")
        
        try:
            self.application.run_polling()
        except KeyboardInterrupt:
            logger.info("Telegram bot stopped by user")
        except Exception as e:
            logger.error(f"Error running Telegram bot: {e}")
            
if __name__ == "__main__":
    # Get token from environment or command line
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # Create and run the bot
    bot = TelegramBot(token=token)
    bot.run() 