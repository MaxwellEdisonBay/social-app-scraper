import os
import logging
from typing import Optional
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError

# Configure logging
logger = logging.getLogger("telegram_bot")

class TelegramHandler:
    """
    Handler for Telegram bot interactions using python-telegram-bot library.
    Manages sending messages to a hardcoded chat ID.
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the Telegram handler.
        
        Args:
            token (str, optional): Telegram bot token. If not provided, will try to get from environment.
        """
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            logger.warning("No Telegram bot token provided. Bot functionality will be disabled.")
            self.enabled = False
            self.bot = None
        else:
            self.enabled = True
            self.bot = Bot(token=self.token)
            
    async def send_message(self, chat_id: int, text: str, parse_mode: str = "HTML", reply_markup: Optional[InlineKeyboardMarkup] = None) -> bool:
        """
        Send a message to a specific chat ID.
        
        Args:
            chat_id (int): Telegram chat ID to send the message to.
            text (str): Message text.
            parse_mode (str): Parse mode for the message (HTML, Markdown, etc.).
            reply_markup (InlineKeyboardMarkup, optional): Inline keyboard markup for the message.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.enabled:
            logger.warning("Cannot send message: Telegram bot is not enabled")
            return False
            
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
            logger.info(f"Message sent to {chat_id}")
            return True
        except TelegramError as e:
            logger.error(f"Error sending message to {chat_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
            
    async def broadcast_post(self, post, source: str = "all") -> int:
        """
        Broadcast a post to the hardcoded chat ID.
        
        Args:
            post: The post to broadcast.
            source (str): Not used anymore, kept for compatibility.
            
        Returns:
            int: Number of subscribers the post was sent to (always 1 or 0).
        """
        if not self.enabled:
            logger.warning("Cannot broadcast post: Telegram bot is not enabled")
            return 0
            
        # Hardcoded chat ID
        chat_id = 364795443
        message = self._format_post_message(post)
        
        # Only add approve button if URL is short enough (less than 64 bytes)
        reply_markup = None
        if len(post.url) < 64:
            keyboard = [
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"approve_{post.url}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        
        if await self.send_message(chat_id, message, reply_markup=reply_markup):
            logger.info(f"Broadcasted post to chat ID {chat_id}")
            return 1
        return 0
        
    def _format_post_message(self, post) -> str:
        """
        Format a post as a Telegram message.
        
        Args:
            post: Post object to format.
            
        Returns:
            str: Formatted message.
        """
        # Define truncation limits for different parts
        TITLE_LIMIT = 100
        DESC_LIMIT = 200
        SUMMARY_LIMIT = 500
        
        # Helper function to truncate text and convert HTML to plain text
        def truncate_and_clean(text, limit):
            if not text:
                return ""
            # Convert HTML to plain text using a simple regex
            import re
            text = re.sub('<[^<]+?>', '', text)
            
            # Clean up multiple newlines
            text = re.sub(r'\n\s*\n', '\n\n', text)
            
            # Truncate after cleaning
            if len(text) <= limit:
                return text
            return text[:limit] + "..."
        
        # Start with the title
        message = f"<b>{truncate_and_clean(post.title, TITLE_LIMIT)}</b>\n\n"
        
        # Add Ukrainian title if available
        if post.uk_title:
            message += f"<b>Українською:</b> {truncate_and_clean(post.uk_title, TITLE_LIMIT)}\n\n"
            
        # Add description
        if post.desc:
            message += f"{truncate_and_clean(post.desc, DESC_LIMIT)}\n\n"
            
        # Add English text if available
        if post.en_text:
            message += f"<b>English Summary:</b>\n{truncate_and_clean(post.en_text, SUMMARY_LIMIT)}\n\n"
            
        # Add Ukrainian text if available
        if post.uk_text:
            message += f"<b>Український переклад:</b>\n{truncate_and_clean(post.uk_text, SUMMARY_LIMIT)}\n\n"
            
        # Add source and link
        message += f"<b>Source:</b> {post.source}\n"
        message += f"<a href='{post.url}'>Read more</a>"
        
        # Final check to ensure the entire message is within Telegram's limit (4096 characters)
        if len(message) > 4000:  # Leave some room for HTML tags
            message = message[:4000] + "...\n\n[Message truncated]"
            
        return message 