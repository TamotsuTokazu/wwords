from telegram import ForceReply, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, ExtBot, MessageHandler, filters
from telegram.constants import ParseMode

import words
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
        if context.chat_data['game']['state'] != -1:
            await update.message.reply_text('群聊中已有游戏在进行。')
            return
    return_message = await update.effective_message.reply_text('开始新游戏，请使用 /join 命令加入游戏。')
    context.chat_data['game'] = dict()
    context.chat_data['game']['state'] = 0
    context.chat_data['game']['id'] = return_message.id
    context.chat_data['game']['players'] = dict()

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'user' not in context.user_data:
        await update.effective_message.reply_text('你还未注册，请首先私聊此 bot 完成注册。')
    elif 'game' not in context.chat_data or context.chat_data['game']['state'] == -1:
        await update.message.reply_text('群聊没有正在进行的游戏，请使用 /newgame 开始新游戏。')
    else:
        if context.chat_data['game']['state'] != 0:
            await update.message.reply_text('游戏正在进行，无法加入。')
            return
        id = update.effective_user.id
        if id in context.chat_data['game']['players']:
            await update.message.reply_text('您已经在游戏中。')
        else:
            context.chat_data['game']['players'][id] = context.user_data
            await update.message.reply_html(rf'{update.effective_user.mention_html()} 加入了游戏，游戏内已有 {len(context.chat_data["game"]["players"])} 人。')

async def quit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'game' not in context.chat_data or context.chat_data['game']['state'] == -1:
        await update.message.reply_text('群聊没有正在进行的游戏，请使用 /newgame 开始新游戏。')
    else:
        if context.chat_data['game']['state'] != 0:
            await update.message.reply_text('游戏正在进行，无法退出。')
            return
        id = update.effective_user.id
        if id not in context.chat_data['game']['players']:
            await update.message.reply_text('您不在游戏中。')
        else:
            del context.chat_data['game']['players'][id]
            await update.message.reply_html(rf'{update.effective_user.mention_html()} 退出了游戏，游戏内已有 {len(context.chat_data["game"]["players"])} 人。')

async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'game' not in context.chat_data or context.chat_data['game']['state'] == -1:
        await update.message.reply_text('群聊没有正在进行的游戏，请使用 /newgame 开始新游戏。')
    else:
        game = context.chat_data['game']
        if game['state'] != 0:
            return
        game['state'] = 1
        game['chat'] = update.effective_message.chat_id
        players = list(game['players'].keys())
        n = len(players)
        logger.info(players)
        logger.info(n)
        if n < 3 and False:
            await update.message.reply_text('人数不足。')
        else:
            host = random.choice(players)
            game['host'] = host
            await update.message.reply_html(f'ゲームを始めよう！\n本局游戏的村长是：{game["players"][host]["user"].mention_html()}\n请从私聊中查看自己的身份。', quote=False)
            # TODO
            if n < 3:
                roles = [1] * n
            elif n < 7:
                roles = [1] * (n - 2) + [0] + [2]
            else:
                roles = [1] * (n - 3) + [0] * 2 + [2]
            random.shuffle(roles)
            roles = {p: r for p, r in zip(players, roles)}
            game['roles'] = roles
            roles_str = ['狼人', '平民', '先知']
            wolves = ' 和 '.join(game["players"][i]["user"].mention_html() for i in game['players'].keys() if game['roles'][i] == 0)
            for player, user_dict in game['players'].items():
                user_dict['game'] = game
                await context.bot.send_message(user_dict['user'].id, f'你在游戏中的身份是：{roles_str[roles[player]]}。')
                if roles[player] == 0:
                    await context.bot.send_message(user_dict['user'].id, f'本局游戏中的狼人是 {wolves}。', parse_mode=ParseMode.HTML)
            await update.message.reply_text('正在等待村长选择词语……', quote=False)
            # words = ['温迪', '枫原万叶']
            word_candidates = random.sample(words.xiaohongshu + words.regular, 5)
            buttons = [InlineKeyboardButton(s, callback_data=f'-{s}') for s in word_candidates]
            keyboard = InlineKeyboardMarkup.from_column(buttons)
            await context.bot.send_message(game['players'][host]['user'].id, '请从下列词语中选择一个。', reply_markup=keyboard)

option_str = ['是', '否', '?', '接近了', '差得远']
option_emoji = ['✔️', '❌', '❔', '', '']

async def host_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    game = context.user_data['game']
    if game['state'] == 1:
        game['state'] = 2
        game['word'] = query.data[1:]
        await query.edit_message_text(query.message.text + f'\n你已选择：{game["word"]}。')
        await context.bot.send_message(game['chat'], f'村长已选择词语。\n狼人和先知请在私聊中查看词语。')
        for player, user_dict in game['players'].items():
            if game['roles'][player] != 1:
                await context.bot.send_message(user_dict['user'].id, f'本局游戏的词语是：{game["word"]}。')

        game['history'] = await context.bot.send_message(game['chat'], f'这条消息中是本局游戏中的所有问答。')
        game['n_messages'] = 0
        players = list(game['players'].keys())
        players.remove(game['host'])
        random.shuffle(players)
        game['queue'] = players
        game['index'] = 0
        game['count'] = [40] * 2 + [15, 1, 1]
        await new_question(context.bot, game)

    await query.answer()

async def new_question(bot: ExtBot, game: dict) -> None:
    current = game['queue'][game['index']]
    game['questions'] = []
    game['question_contents'] = dict()
    if 'host_question' in game:
        del game['host_question']

    game['chat_question'] = await bot.send_message(game['chat'], f'请 {game["players"][current]["user"].mention_html()} 回复本条消息以提问。', parse_mode=ParseMode.HTML)

async def update_host_question(bot: ExtBot, game: dict) -> None:
    text = '\n'.join(game['question_contents'][id] for id in game['questions'])
    if 'host_question' in game:
        await game['host_question'].edit_text(text, reply_markup=game['host_question'].reply_markup)
    else:
        host = game['host']
        count = game['count']
        def f(i):
            return InlineKeyboardButton(f'{option_str[i]} ({count[i]})', callback_data=f'{i}')
        keyboard = InlineKeyboardMarkup([
            [f(0), f(1), f(2)],
            [f(3), f(4)],
            [InlineKeyboardButton('猜对了！', callback_data='+')],
            [InlineKeyboardButton('选项用完了……', callback_data='@')],
        ])
        game['host_question'] = await bot.send_message(game['players'][host]['user'].id, text, reply_markup=keyboard)

async def update_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'game' not in context.chat_data or context.chat_data['game']['state'] != 2:
        # await update.message.reply_text('4群聊没有正在进行的游戏，请使用 /newgame 开始新游戏。')
        return
    game = context.chat_data['game']
    if game['state'] != 2:
        return
    current = game['queue'][game['index']]
    try:
        reply_id = update.effective_message.reply_to_message.id
    except:
        return
    if update.effective_user.id == current and (reply_id == game['chat_question'].id or reply_id in game['questions']):
        message = update.effective_message
        if message.id not in game['questions']:
            game['questions'].append(message.id)
        game['question_contents'][message.id] = message.text
        await update_host_question(context.bot, game)

async def host_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    game = context.user_data['game']
    text = query.message.text
    if game['state'] == 2:
        r = int(query.data)
        if game['count'][r] <= 0:
            await query.answer()
            return
        await query.edit_message_text(text + f'\n你的回复：{option_str[r]}')
        game['count'][r] -= 1
        if r < 2:
            game['count'][1 - r] -= 1
        await context.bot.send_message(game['chat'], f'村长的回复：{option_str[r]}。', reply_to_message_id=game['questions'][-1])
        game['history'] = await game['history'].edit_text(game['history'].text + f'\n{game["n_messages"]:2} {text} {option_str[r]} {option_emoji[r]}')
        game["n_messages"] += 1

        game['index'] = (game['index'] + 1) % len(game['queue'])
        if sum(game['count']) == 0:
            await game_over_incorrect(context.bot, game)
        else:
            await new_question(context.bot, game)

    await query.answer()

async def game_over_correct(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    game = context.user_data['game']
    if game['state'] != 2:
        return
    query = update.callback_query
    await query.edit_message_text(query.message.text + f'\n你的回复：猜对了！')
    await context.bot.send_message(game['chat'], f'猜对了，词语是 {game["word"]}。', reply_to_message_id=game['questions'][-1])
    await query.answer()
    game['state'] = 3
    wolves = ' 和 '.join(game["players"][id]["user"].mention_html() for id in game['players'].keys() if game['roles'][id] == 0)

    game['candidates'] = [id for id in game['players'].keys() if game['roles'][id] != 0]
    game['voters'] = [id for id in game['players'].keys() if game['roles'][id] == 0]
    keyboard = voting_keyboard(game)
    game['voting'] = dict()

    game['vote_message'] = await context.bot.send_message(game['chat'], f'游戏中的狼人是 {wolves}，请你们在 1 分钟内找出先知，只需有一人指出先知即可。', reply_markup=keyboard, parse_mode=ParseMode.HTML)

async def game_over_incorrect_force(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        logger.info('here')
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(query.message.text + '\n选项用完了……')
    except:
        logger.info('excepted')
    if 'game' in context.chat_data and context.chat_data['game']['state'] == 2:
        await game_over_incorrect(context.bot, context.chat_data['game'])
    elif 'game' in context.user_data and context.user_data['game']['state'] == 2:
        await game_over_incorrect(context.bot, context.user_data['game'])

async def game_over_incorrect(bot: ExtBot, game: dict) -> None:
    logger.info('incorrect')
    await bot.send_message(game['chat'], f'很遗憾没有人猜出词语 {game["word"]}。')
    game['state'] = 4

    game['candidates'] = list(game['players'].keys())
    game['voters'] = [id for id in game['players'].keys() if game['roles'][id] != 0]
    keyboard = voting_keyboard(game)
    game['voting'] = dict()

    game['vote_message'] = await bot.send_message(game['chat'], f'所有人需要在 1 分钟内找出至少一个狼人。', reply_markup=keyboard)

def voting_keyboard(game: dict) -> None:
    return InlineKeyboardMarkup.from_column([InlineKeyboardButton(game['players'][id]['user'].full_name, callback_data=f'!{id}') for id in game['candidates']])

async def vote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    game = context.user_data['game']
    query = update.callback_query
    await query.answer()
    if game['state'] < 3:
        return
    if query.from_user.id not in game['voters']:
        return
    game['voting'][update.effective_user.id] = int(query.data[1:])

async def finish_vote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'game' not in context.chat_data or context.chat_data['game']['state'] < 3:
        return
    game = context.user_data['game']
    c = game['candidates']
    v = list(game['voting'].values())
    results = [v.count(id) for id in c]
    board = '\n'.join('%2d 票 %s' % (x, game["players"][id]["user"].full_name) for id, x in zip(c, results))
    await game['vote_message'].edit_text(f'投票结果：\n{board}')
    if game['state'] == 3:
        # success
        for i, r in game['roles'].items():
            if r == 2:
                id = i
        if results[c.index(id)] > 0:
            await context.bot.send_message(game['chat'], f'狼人成功找到了先知 {game["players"][id]["user"].mention_html()}。\n狼人获胜！', parse_mode=ParseMode.HTML)
        else:
            await context.bot.send_message(game['chat'], f'狼人没有找到先知 {game["players"][id]["user"].mention_html()}。\n村民获胜！', parse_mode=ParseMode.HTML)
    else:
        # fail
        x = max(results)
        wolves = ' 和 '.join(game["players"][i]["user"].mention_html() for i in game['players'].keys() if game['roles'][i] == 0)
        if results.count(x) > 1:
            await context.bot.send_message(game['chat'], f'怎么决定不了啊，就暂且认为狼人胜利了吧！\n狼人是 {wolves}。', parse_mode=ParseMode.HTML)
        else:
            id = c[results.index(x)]
            if game['roles'][id] == 0:
                await context.bot.send_message(game['chat'], f'狼人是 {wolves}，村民成功找到了狼人。\n村民获胜！', parse_mode=ParseMode.HTML)
            else:
                await context.bot.send_message(game['chat'], f'{game["players"][id]["user"].mention_html()} 不是狼人。\n狼人是 {wolves}。\n狼人获胜！', parse_mode=ParseMode.HTML)
    game['state'] = -1