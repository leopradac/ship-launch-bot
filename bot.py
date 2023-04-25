#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
"""
Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import os
import logging

# noinspection PyPackageRequirements
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
# noinspection PyPackageRequirements
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import constants
from when_did_the_rocket_launch.main import execute

TOKEN = os.environ['TOKEN']
# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

reply_keyboard = [["Yes", "No"]]
custom_keyboard = ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Launched?"
        )
SHIP = 0


def update_frames_range(update, context, frames):
    payload = {
        update.effective_chat.id: {
            "frames_range": frames,  # rename current frames variable for initial frames
        }
    }
    context.bot_data.update(payload)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user."""
    result = execute()
    await update.message.reply_photo(result['image']['data'])

    update_frames_range(update, context, result['frames_range'])

    await update.message.reply_text(
        "Hi! My name is Launch Time Guesser Bot. I will hold a conversation with you. "
        "Send /cancel to stop talking to me.\n\n"
        "Would you say at this image the ship has already launched?",
        reply_markup=custom_keyboard,
    )

    return SHIP


async def ship(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info("Selection of %s: %s", user.first_name, update.message.text)

    launched = True if update.message.text.lower() == constants.YES else False
    bot_data = context.bot_data[update.effective_chat.id]
    frames_range = bot_data['frames_range']
    result = execute(None, launched, frames_range)
    update_frames_range(update, context, result['frames_range'])

    if not result['finished']:
        await update.message.reply_photo(result['image']['data'])

        await update.message.reply_text(
            "I see! now this one, "
            "launched or not yet? Send /cancel if you don't want to continue.",
            reply_markup=custom_keyboard,
        )

        return SHIP
    else:
        await update.message.reply_photo(result['image']['data'])
        await update.message.reply_text(
            f"Finished, {result['index']}. Use /start to play again."
        )
        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day. Type /start to restart it.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SHIP: [MessageHandler(filters.Regex("^(Yes|No)$"), ship)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
