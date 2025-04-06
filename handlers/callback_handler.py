import logging
from telegram import Update
from telegram.ext import ContextTypes

# Configure logging
logger = logging.getLogger("callback_handler")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback queries from inline keyboard buttons.
    Currently only handles the approve action.
    
    Args:
        update (Update): The update containing the callback query.
        context (ContextTypes.DEFAULT_TYPE): The context of the callback.
    """
    query = update.callback_query
    await query.answer()  # Answer the callback query to remove the loading state
    
    # Extract the action and data from the callback data
    action, data = query.data.split('_', 1)
    
    if action == "approve":
        # Log the approval
        logger.info(f"Post approved: {data}")
        # Update the message to show it's been approved
        await query.edit_message_text(
            text=query.message.text + "\n\n✅ Approved",
            parse_mode="HTML"
        )
    else:
        logger.warning(f"Unknown callback action: {action}") 