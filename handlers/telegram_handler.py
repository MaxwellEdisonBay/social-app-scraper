import os
import logging
import re
from typing import Optional, List
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError

# Configure logging
logger = logging.getLogger("telegram_bot")

class TelegramHandler:
    """
    Handler for Telegram bot interactions using python-telegram-bot library.
    Manages sending messages to channels where the bot is an admin.
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
            
    def _clean_html(self, text: str) -> str:
        """
        Clean HTML from text to make it compatible with Telegram's HTML parser.
        
        Args:
            text (str): Text that might contain HTML.
            
        Returns:
            str: Cleaned text.
        """
        if not text:
            return ""
            
        # Replace common HTML tags with their content
        text = re.sub(r'<p>(.*?)</p>', r'\1\n\n', text, flags=re.DOTALL)
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'<b>(.*?)</b>', r'<b>\1</b>', text)
        text = re.sub(r'<i>(.*?)</i>', r'<i>\1</i>', text)
        text = re.sub(r'<u>(.*?)</u>', r'<u>\1</u>', text)
        text = re.sub(r'<s>(.*?)</s>', r'<s>\1</s>', text)
        text = re.sub(r'<a href="(.*?)">(.*?)</a>', r'<a href="\1">\2</a>', text)
        
        # Remove any other HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean up multiple newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text
            
    async def get_admin_channels(self) -> List[int]:
        """
        Get a list of chat IDs where the bot is an admin.
        
        Returns:
            List[int]: List of chat IDs where the bot is an admin.
        """
        if not self.enabled:
            logger.warning("Cannot get admin channels: Telegram bot is not enabled")
            return []
            
        try:
            # Get bot's information
            bot_info = await self.bot.get_me()
            # Get updates to find channels
            updates = await self.bot.get_updates()
            
            admin_channels = []
            for update in updates:
                if update.my_chat_member and update.my_chat_member.chat.type in ['channel', 'supergroup']:
                    if update.my_chat_member.new_chat_member.status in ['administrator', 'creator']:
                        admin_channels.append(update.my_chat_member.chat.id)
            
            return list(set(admin_channels))  # Remove duplicates
        except Exception as e:
            logger.error(f"Error getting admin channels: {e}")
            return []
            
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
            # Clean HTML from text
            cleaned_text = self._clean_html(text)
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=cleaned_text,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
            logger.info(f"Message sent to chat ID {chat_id}")
            return True
        except TelegramError as e:
            logger.error(f"Error sending message to chat ID {chat_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
            
    async def send_photo(self, chat_id: int, photo_url: str, caption: str, parse_mode: str = "HTML", reply_markup: Optional[InlineKeyboardMarkup] = None) -> bool:
        """
        Send a photo with caption to a specific chat ID.
        
        Args:
            chat_id (int): Telegram chat ID to send the photo to.
            photo_url (str): URL of the photo to send.
            caption (str): Caption for the photo.
            parse_mode (str): Parse mode for the caption (HTML, Markdown, etc.).
            reply_markup (InlineKeyboardMarkup, optional): Inline keyboard markup for the message.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.enabled:
            logger.warning("Cannot send photo: Telegram bot is not enabled")
            return False
            
        try:
            # Clean HTML from caption
            cleaned_caption = self._clean_html(caption)
            
            await self.bot.send_photo(
                chat_id=chat_id,
                photo=photo_url,
                caption=cleaned_caption,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
            logger.info(f"Photo sent to chat ID {chat_id}")
            return True
        except TelegramError as e:
            logger.error(f"Error sending photo to chat ID {chat_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            return False
            
    async def broadcast_post(self, post, source: str = "all", override_url: str = None) -> int:
        """
        Broadcast a post to all channels where the bot is an admin.
        
        Args:
            post: The post to broadcast.
            source (str): Source of the post (not used).
            override_url (str, optional): URL to use instead of post.url.
            
        Returns:
            int: Number of channels the post was sent to.
        """
        if not self.enabled:
            logger.warning("Cannot broadcast post: Telegram bot is not enabled")
            return 0
            
        admin_channels = await self.get_admin_channels()
        if not admin_channels:
            logger.warning("No admin channels found to broadcast to")
            return 0
            
        message = self._format_post_message(post)
        success_count = 0
        
        # Create inline keyboard with a button for the link
        # Use override_url if provided, otherwise use post.url
        url_to_use = override_url if override_url is not None else post.url
        keyboard = [
            [InlineKeyboardButton("Читати далі", url=url_to_use)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        for chat_id in admin_channels:
            # Try to send with image first if available
            if hasattr(post, 'image_url') and post.image_url:
                try:
                    if await self.send_photo(chat_id, post.image_url, message, reply_markup=reply_markup):
                        success_count += 1
                        continue
                except Exception as e:
                    logger.warning(f"Failed to send photo, falling back to text-only message: {e}")
            
            # Send text-only message (either no image or image failed)
            if await self.send_message(chat_id, message, reply_markup=reply_markup):
                success_count += 1
                
        logger.info(f"Broadcasted post to {success_count} channels")
        return success_count
        
    def _format_post_message(self, post) -> str:
        """
        Format a post as a Telegram message.
        
        Args:
            post: Post object to format.
            
        Returns:
            str: Formatted message.
        """
        # Define truncation limits
        TEXT_LIMIT = 500
        
        # Helper function to truncate text
        def truncate_text(text, limit):
            if not text:
                return ""
            if len(text) <= limit:
                return text
            return text[:limit] + "..."
        
        # Format the message according to requirements
        # Use the full Ukrainian title without truncation
        message = f"<b>{post.uk_title}</b>\n\n"
        
        # Add Ukrainian text
        if post.uk_text:
            message += f"{truncate_text(post.uk_text, TEXT_LIMIT)}\n\n"
            
        # Add link for preview (will be hidden by the button)
        message += f"<a href='{post.url}'>.</a>"
            
        return message 