#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

'''
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
'''

import interface as I
from credentials import bot_token
import logging

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''Send a message when the command /start is issued.'''
    user = update.effective_user
    context.user_data['private'] = update.effective_message.chat_id
    context.user_data['user'] = update.effective_user
    await update.message.reply_html(rf'你好 {user.mention_html()}，您已成功注册。')

async def start_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Please use /start in a private chat.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''Send a message when the command /help is issued.'''

async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    '''Send the alarm message.'''
    job = context.job
    await context.bot.send_message(job.chat_id, text=f'Beep! {job.data} seconds are over!')


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    '''Remove job with given name. Returns whether job was removed.'''
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def set_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''Add a job to the queue.'''
    chat_id = update.effective_message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds
        due = float(context.args[0])
        if due < 0:
            await update.effective_message.reply_text('Sorry we can not go back to future!')
            return

        job_removed = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_once(alarm, due, chat_id=chat_id, name=str(chat_id), data=due)

        text = 'Timer successfully set!'
        if job_removed:
            text += ' Old one was removed.'
        await update.effective_message.reply_text(text)

    except (IndexError, ValueError):
        await update.effective_message.reply_text('Usage: /set <seconds>')


async def unset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''Remove the job if the user changed their mind.'''
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = 'Timer successfully cancelled!' if job_removed else 'You have no active timer.'
    await update.message.reply_text(text)

group_chat_commands = {
    'newgame': I.newgame,
    'join': I.join,
    'quit': I.quit,
    'startgame': I.startgame,
}

private_chat_commands = {
    'start': start,
}

def main() -> None:
    '''Start the bot.'''
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(bot_token).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler(list(private_chat_commands.keys()), I.not_in_private_chat_alart, filters=~filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler(list(group_chat_commands.keys()), I.not_in_group_chat_alart, filters=~filters.ChatType.GROUPS))
    for k, v in private_chat_commands.items():
        application.add_handler(CommandHandler(k, v, filters=filters.ChatType.PRIVATE))
    for k, v in group_chat_commands.items():
        application.add_handler(CommandHandler(k, v, filters=filters.ChatType.GROUPS))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('set', set_timer))
    application.add_handler(CommandHandler('unset', unset))
    application.add_handler(CallbackQueryHandler(I.host_select_initial, '-'))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == '__main__':
    main()