import asyncio
import os
from dotenv import load_dotenv
from handlers.telegram_handler import TelegramHandler
from dataclasses import dataclass

@dataclass
class TestPost:
    uk_title: str
    uk_text: str
    url: str
    image_url: str = None  # Make image_url optional

async def test_telegram_sending():
    # Load environment variables
    load_dotenv()
    
    # Initialize the handler
    handler = TelegramHandler()
    
    # Get admin channels
    admin_channels = await handler.get_admin_channels()
    print(f"Found admin channels: {admin_channels}")
    
    # First test: Simple direct message
    print("\nTesting direct message sending...")
    for chat_id in admin_channels:
        success = await handler.send_message(
            chat_id=chat_id,
            text="🔍 Простий тест\n\nЦе просте тестове повідомлення для перевірки базової функціональності."
        )
        print(f"Direct message sent: {success}")
    
    # Second test: Full post with image
    print("\nTesting full post broadcast...")
    test_post = TestPost(
        uk_title="🔍 Тестове повідомлення",
        uk_text="Це тестове повідомлення для перевірки функціональності бота. "
               "Воно містить текст та посилання для повної перевірки можливостей надсилання.",
        url="https://www.bbc.com/news"
    )
    
    sent_count = await handler.broadcast_post(test_post)
    print(f"Successfully broadcast to {sent_count} channels")

if __name__ == "__main__":
    asyncio.run(test_telegram_sending()) 