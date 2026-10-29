import os
import re
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp

# កត់ត្រា Logs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Token របស់អ្នក
BOT_TOKEN = "9238043978:AAGotoQ4wCYLklTJZMVRaLDz1fkG5ddytFo"

# Username របស់ Channel
CHANNEL_USERNAME = "@tiktokdonl"

# Regex សម្រាប់ត្រួតពិនិត្យ Link TikTok
TIKTOK_REGEX = r'(https?://(?:www\.|vt\.|vm\.)?tiktok\.com/[^\s]+)'

# មុខងារឆ្គងផ្ទៀងផ្ទាត់ថាតើ User បានចូល Channel ហើយឬនៅ
async def check_user_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception as e:
        logging.error(f"Error checking chat member: {e}")
        return False

# មុខងារផ្ញើសារប្រាប់ឱ្យចូលរួម Channel
async def send_subscription_required_message(update_or_query, user_name: str):
    keyboard = [
        [InlineKeyboardButton("📢 ចូលរួម Channel (Join)", url="https://t.me/tiktokdonl")],
        [InlineKeyboardButton("🔄 ពិនិត្យមើលម្ដងទៀត (Check)", callback_data='check_sub')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        f"❌ សួស្ដី {user_name}!\n\n"
        "⚠️ **សូមអភ័យទោស អ្នកមិនទាន់បានចូលរួមក្នុង Channel របស់យើងនៅឡើយទេ!**\n\n"
        "ដើម្បីអាចទាញយកវីដេអូពី TikTok តាមរយៈ Bot នេះបាន តម្រូវឱ្យអ្នកចូលរួមក្នុង Channel ជាមុនសិន៖\n"
        "👉 https://t.me/tiktokdonl\n\n"
        "បន្ទាប់ពីចូលរួមរួច សូមចុចប៊ូតុង **'ពិនិត្យមើលម្ដងទៀត'** ខាងក្រោមនេះ ដើម្បីដោះសោការទាញយក។"
    )

    if hasattr(update_or_query, 'message') and update_or_query.message:
        await update_or_query.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update_or_query.edit_message_text(text, reply_markup=reply_markup)

# មុខងារពេលចុច /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_name = user.first_name if user.first_name else "មិត្តភក្តិ"
    
    is_joined = await check_user_subscription(user.id, context)
    
    if not is_joined:
        await send_subscription_required_message(update, user_name)
    else:
        await update.message.reply_text(
            f"សួស្ដី {user_name}! 👋\n\n"
            "សូមស្វាគមន៍មកកាន់ TikTok Downloader Bot 🤖\n"
            "• ផ្ញើ Link វីដេអូ TikTok មកទីនេះដើម្បីទាញយកជាវីដេអូអមដោយព័ត៌មានលម្អិត!\n\n"
            "ឥឡូវនេះ អ្នកអាចផ្ញើ Link TikTok មកបានហើយ!"
        )

# មុខងារពេល User ចុចប៊ូតុងពិនិត្យการ Join
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    user_name = user.first_name if user.first_name else "មិត្តភក្តិ"
    
    if query.data == 'check_sub':
        is_joined = await check_user_subscription(user.id, context)
        
        if is_joined:
            await query.edit_message_text(
                f"✅ អរគុណ {user_name} ដែលបានចូលរួម Channel របស់យើង!\n\n"
                "ឥឡូវនេះអ្នកអាចផ្ញើ Link វីដេអូ TikTok មកទីនេះដើម្បីទាញយកបានធម្មតាហើយ។"
            )
        else:
            await send_subscription_required_message(query, user_name)

# មុខងារទទួលសារ និងទាញយកវីដេអូ
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_name = user.first_name if user.first_name else "មិត្តភក្តិ"
    
    is_joined = await check_user_subscription(user.id, context)
    if not is_joined:
        await send_subscription_required_message(update, user_name)
        return

    text = update.message.text
    match = re.search(TIKTOK_REGEX, text)
    
    if not match:
        await update.message.reply_text("សូមផ្ញើ Link TikTok ដែលត្រឹមត្រូវ!")
        return

    tiktok_url = match.group(0)
    
    status_msg = await update.message.reply_text("⏳ កំពុងទាញយកវីដេអូ សូមរង់ចាំបន្តិច...")

    file_path = None
    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(tiktok_url, download=True)
            file_path = ydl.prepare_filename(info)
            
            title = info.get('title', 'គ្មានចំណងជើង')
            uploader = info.get('uploader', info.get('creator', 'មិនស្គាល់ឈ្មោះ'))
            like_count = info.get('like_count', 0)

        # កែសម្រួលមិនដាក់សញ្ញា Markdown ដើម្បីការពារ Error
        caption = (
            f"📌 ចំណងជើង៖ {title}\n"
            f"👤 អ្នកបង្ហោះ៖ {uploader}\n"
            f"❤️ ចំនួនចូលចិត្ត៖ {like_count:,}\n\n"
            "🔗 ទាញយកតាមរយៈ Bot @TikTokdownload_ktybot"
        )

        with open(file_path, 'rb') as video:
            await context.bot.send_video(
                chat_id=update.message.chat_id,
                video=video,
                caption=caption
            )

        await status_msg.delete()

    except Exception as e:
        logging.error(f"Error downloading: {e}")
        await status_msg.edit_text("❌ មានបញ្ហាក្នុងការទាញយក! អាចមកពី Link ខុស ឬ Server TikTok មានការផ្លាស់ប្តូរ។")

    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("Bot ដំណើរការហើយ...")
    app.run_polling()