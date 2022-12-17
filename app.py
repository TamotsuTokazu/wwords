#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position

import interface as I
from credentials import bot_token
from persistence import MyPersistence
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
    context.user_data['user'] = update.effective_user
    await update.message.reply_html(rf'你好 {user.mention_html()}，您已成功注册。')

group_chat_commands = {
    'newgame': I.newgame,
    'join': I.join,
    'quit': I.quit,
    'startgame': I.startgame,
    'finish': I.finish_vote_force,
    'stop': I.game_over_incorrect_force
}

private_chat_commands = {
    'start': start,
}

def main() -> None:
    '''Start the bot.'''
    # Create the Application and pass it your bot's token.
    my_persistence = MyPersistence('data.txt')
    application = Application.builder().token(bot_token).persistence(persistence=my_persistence).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler(list(private_chat_commands.keys()), I.not_in_private_chat_alart, filters=~filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler(list(group_chat_commands.keys()), I.not_in_group_chat_alart, filters=~filters.ChatType.GROUPS))
    for k, v in private_chat_commands.items():
        application.add_handler(CommandHandler(k, v, filters=filters.ChatType.PRIVATE))
    for k, v in group_chat_commands.items():
        application.add_handler(CommandHandler(k, v, filters=filters.ChatType.GROUPS))
    application.add_handler(CallbackQueryHandler(I.host_select, '-'))
    application.add_handler(CallbackQueryHandler(I.host_answer, '[0-4]'))
    application.add_handler(CallbackQueryHandler(I.game_over_correct, '\+'))
    application.add_handler(CallbackQueryHandler(I.game_over_incorrect_force, '@'))
    application.add_handler(CallbackQueryHandler(I.vote, '!'))
    application.add_handler(MessageHandler(filters.ChatType.GROUPS, I.update_question))
    application.add_handler(MessageHandler(~filters.ChatType.GROUPS, I.not_in_group_chat_alart))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == '__main__':
    main()