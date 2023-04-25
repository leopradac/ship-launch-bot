#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

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

from when_did_the_rocket_launch.main import execute

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

reply_keyboard = [["Yes", "No"]]
custom_keyboard = ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Launched?"
        )
SHIP = range(1)


def update_running_frames(update, context, frames):
    payload = {
        update.effective_chat.id: {
            "running_frames": frames,  # rename current frames variable for initial frames
        }
    }
    context.bot_data.update(payload)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user."""
    instance, initial_frames, image, _, _ = execute()
    await update.message.reply_photo(image['data'])

    update_running_frames(update, context, initial_frames)

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

    launched = True if update.message.text.lower() == 'yes' else False
    bot_data = context.bot_data[update.effective_chat.id]
    running_frames = bot_data['running_frames']
    cur_instance, updated_frames, image, was_found, index = execute(None, launched, running_frames)
    update_running_frames(update, context, updated_frames)

    if not was_found:
        await update.message.reply_photo(image['data'])

        await update.message.reply_text(
            "I see! now this one, "
            "launched or not yet? Send /cancel if you don't want to continue.",
            reply_markup=custom_keyboard,
        )

        return SHIP
    else:
        await update.message.reply_text(
            f"Finished, {index}. Use /start to play again."
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
    TOKEN = os.environ['TOKEN']
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
