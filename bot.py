import os
import sys
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from deep_translator import GoogleTranslator

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token from environment variable
def get_token():
    """Get bot token from environment variables."""
    token = os.environ.get('BOT_TOKEN')
    if not token:
        token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("❌ No BOT_TOKEN found in environment variables!")
        logger.error("Please add BOT_TOKEN to your Railway Variables.")
        sys.exit(1)
    return token

TOKEN = get_token()
logger.info("✅ Bot token loaded successfully!")

# Store user preferences (in-memory, resets on bot restart)
user_languages = {}

# Popular languages for quick selection
POPULAR_LANGUAGES = {
    'en': '🇬🇧 English',
    'es': '🇪🇸 Spanish',
    'fr': '🇫🇷 French',
    'de': '🇩🇪 German',
    'it': '🇮🇹 Italian',
    'pt': '🇵🇹 Portuguese',
    'ru': '🇷🇺 Russian',
    'zh-CN': '🇨🇳 Chinese',
    'ja': '🇯🇵 Japanese',
    'ar': '🇸🇦 Arabic',
    'hi': '🇮🇳 Hindi',
    'ko': '🇰🇷 Korean',
    'nl': '🇳🇱 Dutch',
    'tr': '🇹🇷 Turkish',
    'vi': '🇻🇳 Vietnamese',
    'el': '🇬🇷 Greek',
    'pl': '🇵🇱 Polish',
    'uk': '🇺🇦 Ukrainian',
    'he': '🇮🇱 Hebrew',
    'th': '🇹🇭 Thai'
}

# Helper Functions
def build_language_keyboard() -> InlineKeyboardMarkup:
    """Builds an inline keyboard for language selection."""
    keyboard = []
    row = []
    for lang_code, lang_name in POPULAR_LANGUAGES.items():
        row.append(InlineKeyboardButton(lang_name, callback_data=f"lang_{lang_code}"))
        if len(row) == 2:  # 2 buttons per row
            keyboard.append(row)
            row = []
    if row:  # Add remaining buttons
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="lang_cancel")])
    return InlineKeyboardMarkup(keyboard)

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message."""
    user = update.effective_user
    welcome_text = f"""
🌍 **Welcome to LangSwaapBot, {user.first_name}!**

I translate text between multiple languages instantly.

**How to use:**
1️⃣ Use /lang to choose your target language
2️⃣ Send me any text message
3️⃣ I'll translate it instantly!

**Commands:**
/start - Show this welcome message
/lang - Choose target language
/help - Show all commands
/settings - View your current settings

**Supported languages:** 20+ languages including English, Spanish, French, German, Chinese, Arabic, Hindi, Japanese, Korean, and more!

💡 **Tip:** Your language preference is saved for future translations!
"""
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message."""
    help_text = """
📖 **How to use LangSwaapBot:**

1️⃣ Use /lang to select your target language
2️⃣ Send me any text message
3️⃣ I'll translate it to your chosen language!

**Commands:**
/start - Welcome message
/lang - Choose target language
/settings - View your current settings
/help - Show this help message

**Supported Languages:**
English, Spanish, French, German, Italian, Portuguese, Russian, Chinese, Japanese, Arabic, Hindi, Korean, Dutch, Turkish, Vietnamese, Greek, Polish, Ukrainian, Hebrew, Thai, and more!

💡 **Pro tip:** Your language choice is remembered for your session!
"""
    await update.message.reply_text(help_text)

async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show language selection menu."""
    keyboard = build_language_keyboard()
    await update.message.reply_text(
        "🌐 **Select your target language:**\n\nChoose the language you want to translate into.",
        reply_markup=keyboard
    )

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user settings."""
    user_id = update.effective_user.id
    current_lang = user_languages.get(user_id, 'en')
    lang_name = POPULAR_LANGUAGES.get(current_lang, 'English')
    
    await update.message.reply_text(
        f"⚙️ **Your Settings:**\n\n"
        f"🌐 Target Language: {lang_name}\n\n"
        f"Use /lang to change your target language."
    )

# Callback Handler for Buttons
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles language selection from inline buttons."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if query.data == "lang_cancel":
        await query.edit_message_text("❌ Language selection cancelled.")
        return
    
    # Extract language code
    lang_code = query.data.replace("lang_", "")
    if lang_code in POPULAR_LANGUAGES:
        user_languages[user_id] = lang_code
        lang_name = POPULAR_LANGUAGES[lang_code]
        
        await query.edit_message_text(
            f"✅ **Target language set to: {lang_name}**\n\n"
            f"Now send me any text to translate!"
        )
        logger.info(f"User {user_id} set language to {lang_code}")

# Core Translation Logic
async def translate_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Translate user message to their selected language."""
    user_text = update.message.text
    user_id = update.effective_user.id
    
    # Get user's target language or default to English
    target_language = user_languages.get(user_id, 'en')
    target_name = POPULAR_LANGUAGES.get(target_language, target_language)
    
    try:
        # Show typing indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Translate using deep-translator
        translator = GoogleTranslator(target=target_language)
        translated_text = translator.translate(user_text)
        
        # Format and send response
        response = (
            f"🔤 **Original:**\n{user_text}\n\n"
            f"🌐 **Translation ({target_name}):**\n{translated_text}"
        )
        
        await update.message.reply_text(response, parse_mode="Markdown")
        logger.info(f'Translation successful for user {user_id} to {target_language}')
        
    except Exception as e:
        logger.error(f'Translation error for user {user_id}: {str(e)}')
        await update.message.reply_text(
            "❌ **Translation error.** Please try again.\n\n"
            "Make sure your text is valid and try a different language."
        )

# Main Function
def main() -> None:
    """Start the bot."""
    try:
        # Create Application
        application = Application.builder().token(TOKEN).build()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("lang", lang_command))
        application.add_handler(CommandHandler("settings", settings_command))
        
        # Add callback handler for inline buttons
        application.add_handler(CallbackQueryHandler(button_callback))
        
        # Add message handler for text messages (not commands)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_message))
        
        # Start the Bot
        logger.info("🚀 LangSwaapBot started successfully!")
        logger.info("🌍 Press Ctrl+C to stop.")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
