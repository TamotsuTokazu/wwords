from telegram import ForceReply, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import random
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

async def not_in_group_chat_alart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text('请在群聊中使用此命令。')

async def not_in_private_chat_alart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text('请在私聊中使用此命令。')

async def newgame(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'game' in context.chat_data:
        await update.message.reply_text('群聊中已有游戏在进行。')
    else:
        return_message = await update.effective_message.reply_text('开始新游戏，请使用 /join 命令加入游戏。')
        context.chat_data['game'] = dict()
        context.chat_data['game']['id'] = return_message.id
        context.chat_data['game']['players'] = dict()

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'private' not in context.user_data:
        await update.effective_message.reply_text('你还未注册，请首先私聊此 bot 完成注册。')
    elif 'game' not in context.chat_data:
        await update.message.reply_text('群聊没有正在进行的游戏，请使用 /newgame 开始新游戏。')
    else:
        id = update.effective_user.id
        if id in context.chat_data['game']['players']:
            await update.message.reply_text('您已经在游戏中。')
        else:
            context.chat_data['game']['players'][id] = context.user_data
            await update.message.reply_html(rf'{update.effective_user.mention_html()} 加入了游戏，游戏内已有 {len(context.chat_data["game"]["players"])} 人。')

async def quit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'game' not in context.chat_data:
        await update.message.reply_text('群聊没有正在进行的游戏，请使用 /newgame 开始新游戏。')
    else:
        id = update.effective_user.id
        if id not in context.chat_data['game']['players']:
            await update.message.reply_text('您不在游戏中。')
        else:
            del context.chat_data['game']['players'][id]
            await update.message.reply_html(rf'{update.effective_user.mention_html()} 退出了游戏，游戏内已有 {len(context.chat_data["game"]["players"])} 人。')

async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'game' not in context.chat_data:
        await update.message.reply_text('群聊没有正在进行的游戏，请使用 /newgame 开始新游戏。')
    else:
        game = context.chat_data['game']
        game['chat'] = update.effective_message.chat_id
        players = list(game['players'].keys())
        n = len(players)
        logger.info(players)
        logger.info(n)
        if n < 4 and False:
            await update.message.reply_text('人数不足。')
        else:
            host = random.choice(players)
            game['host'] = host
            await update.message.reply_html(f'ゲームを始めよう！\n本局游戏的村长是：{update.effective_user.mention_html()}\n请从私聊中查看自己的身份。', quote=False)
            for player, user_dict in game['players'].items():
                user_dict['game'] = game
                await context.bot.send_message(user_dict['private'], '您在游戏中。')
            await update.message.reply_text('正在等待村长选择词语……', quote=False)
            words = ['温迪', '枫原万叶']
            buttons = [InlineKeyboardButton(s, callback_data=f'-{s}') for s in words]
            keyboard = InlineKeyboardMarkup.from_column(buttons)
            await context.bot.send_message(game['players'][host]['private'], '请从下列词语中选择一个。', reply_markup=keyboard)

async def host_select_initial(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    game = context.user_data['game']
    if 'word' not in game:
        game['word'] = query.data[1:]
        await query.answer()
        await query.edit_message_text(query.message.text + f'\n你已选择：{game["word"]}。')
        await context.bot.send_message(game['chat'], '村长已选择词语。')

