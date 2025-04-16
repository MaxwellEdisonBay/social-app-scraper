#!/usr/bin/env python
# test_telegram_bot.py
import os
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram.ext import Application, CallbackQueryHandler

from handlers.telegram_handler import TelegramHandler
from handlers.callback_handler import handle_callback
from common.models.models import Post

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_telegram_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_telegram_bot")

def create_test_post():
    """Create a test post with all fields"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    return Post(
        url=f"https://example.com/test_{timestamp}",
        title=f"Test post with translations - {timestamp}",
        desc=f"This is a test post with translations for testing the Telegram bot. This is test {timestamp}.",
        image_url=f"https://example.com/test_{timestamp}.jpg",
        created_at=datetime.now(),
        source="test",
        full_text=f"This is the full text of the test post. It contains multiple paragraphs.\n\n"
                  f"Paragraph 2: Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
                  f"Nullam auctor, nisl eget ultricies tidunt, nisl nisl aliquam nisl, "
                  f"eget aliquam nisl nisl eget nisl. This is test {timestamp}.\n\n"
                  f"Paragraph 3: Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
                  f"Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut "
                  f"aliquip ex ea commodo consequat. This is test {timestamp}.",
        uk_title=f"Тестовий пост з перекладами - {timestamp}",
        en_text=f"This is an improved English summary of the test post. It contains the main points of the article in a more readable format. This is test {timestamp}.",
        uk_text=f"Це покращений український переклад тестового поста. Він містить основні моменти статті в більш читабельному форматі. Це тест {timestamp}."
    )

async def test_telegram_handler():
    """Test the Telegram handler functionality"""
    logger.info("Starting test of Telegram handler")
    
    # Initialize the Telegram handler
    handler = TelegramHandler()
    
    if not handler.enabled:
        logger.warning("Telegram bot is not enabled. Please check your TELEGRAM_BOT_TOKEN.")
        return
    
    # Initialize the application with callback handler
    application = Application.builder().token(handler.token).build()
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Start the application
    await application.initialize()
    await application.start()
    
    # Create and send a test post
    test_post = create_test_post()
    logger.info(f"Created test post: {test_post.title}")
    
    # Test broadcasting with inline keyboard
    logger.info("Testing broadcasting with inline keyboard")
    sent_count = await handler.broadcast_post(test_post)
    logger.info(f"Sent post to {sent_count} subscribers")
    
    # Keep the application running to handle callbacks
    logger.info("Waiting for callback responses (30 seconds)...")
    await asyncio.sleep(30)
    
    # Stop the application
    await application.stop()
    await application.shutdown()
    
    logger.info("Test completed successfully")

class TestPost:
    """Simple class to simulate a post object"""
    def __init__(self, uk_title, uk_text, url, image_url=None):
        self.uk_title = uk_title
        self.uk_text = uk_text
        self.url = url
        self.image_url = image_url

async def test_telegram_bot():
    """Test the Telegram bot functionality"""
    # Initialize the handler
    handler = TelegramHandler()
    
    if not handler.enabled:
        print("Telegram bot is not enabled. Please check your TELEGRAM_BOT_TOKEN in .env file")
        return
    
    # Create test posts
    test_posts = [
        # Post with image
        TestPost(
            uk_title="Історія України",
            uk_text="Україна має багату та різноманітну історію, що сягає тисячоліть. Від Київської Русі до сучасної незалежної держави, "
                   "український народ пройшов довгий шлях боротьби за свободу та незалежність. Культурна спадщина України включає "
                   "унікальні традиції, мистецтво, літературу та архітектуру.",
            url="https://uk.wikipedia.org/wiki/Україна",
            image_url="https://i.imgur.com/dZAz8Fk.jpg"
        ),
        # Post without image but with rich preview
        TestPost(
            uk_title="Київ - столиця України",
            uk_text="Київ - одне з найстаріших міст Європи, столиця України, важливий культурний, науковий та промисловий центр. "
                   "Місто відоме своїми золотоверхими церквами, древніми монастирями та багатою історичною спадщиною. "
                   "Сучасний Київ - це динамічний мегаполіс, що стрімко розвивається.",
            url="https://uk.wikipedia.org/wiki/Київ"
        )
    ]
    
    # Get admin channels
    admin_channels = await handler.get_admin_channels()
    print(f"Found {len(admin_channels)} admin channels")
    
    if not admin_channels:
        print("No admin channels found. Please add the bot as an admin to at least one channel.")
        return
    
    # Test broadcasting posts
    for i, post in enumerate(test_posts, 1):
        print(f"\nTesting post {i}:")
        print(f"Title: {post.uk_title}")
        print(f"Has image: {'Yes' if post.image_url else 'No'}")
        print(f"URL: {post.url}")
        
        success_count = await handler.broadcast_post(post)
        print(f"Successfully sent to {success_count} channels")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_telegram_bot()) 