# bot.py
import os
import json
import logging
import asyncio
from datetime import datetime, date
from dotenv import load_dotenv
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from mega import Mega  # pip install mega.py

# Load environment variables
load_dotenv()

# ========== CONFIGURATION ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MEGA_EMAIL = os.getenv("MEGA_EMAIL")
MEGA_PASSWORD = os.getenv("MEGA_PASSWORD")

if not all([BOT_TOKEN, GEMINI_API_KEY, MEGA_EMAIL, MEGA_PASSWORD]):
    raise ValueError("Missing required environment variables. Check .env file.")

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== MEGA STORAGE CLASS ==========
class MegaStorage:
    def __init__(self, email, password):
        self.mega = Mega()
        self.email = email
        self.password = password
        self._login()

    def _login(self):
        """Login to Mega and store session."""
        try:
            self.mega_session = self.mega.login(self.email, self.password)
            logger.info("Mega login successful")
        except Exception as e:
            logger.error(f"Mega login failed: {e}")
            raise

    def _get_user_folder(self, user_id):
        """Get or create folder for a specific user."""
        # Find root folder
        root = self.mega_session.find("")
        # Look for "telegram_bot" folder, create if not exists
        telegram_folder = None
        for node in root:
            if node['name'] == "telegram_bot" and node['type'] == 1:  # type 1 = folder
                telegram_folder = node
                break
        if not telegram_folder:
            telegram_folder = self.mega_session.create_folder("telegram_bot")
            logger.info("Created telegram_bot folder")
        # Now find user folder inside telegram_bot
        user_folder_name = f"user_{user_id}"
        user_folder = None
        for node in self.mega_session.get_files_in_node(telegram_folder):
            if node['name'] == user_folder_name and node['type'] == 1:
                user_folder = node
                break
        if not user_folder:
            user_folder = self.mega_session.create_folder(user_folder_name, parent=telegram_folder['h'])
            logger.info(f"Created folder for user {user_id}")
        return user_folder

    def _get_data_path(self, user_id, data_type):
        """Return file name for a data type (tasks, marks)."""
        return f"{data_type}.json"

    def read_json(self, user_id, data_type):
        """Read JSON data from Mega."""
        user_folder = self._get_user_folder(user_id)
        file_name = self._get_data_path(user_id, data_type)
        # Search for file in user folder
        files = self.mega_session.get_files_in_node(user_folder)
        for f in files:
            if f['name'] == file_name and f['type'] == 0:  # type 0 = file
                try:
                    # Download file content into memory
                    data = self.mega_session.download(f)
                    return json.loads(data.decode('utf-8'))
                except Exception as e:
                    logger.error(f"Error reading {file_name}: {e}")
                    return None
        # File not found, return empty structure
        if data_type == "tasks":
            return []
        elif data_type == "marks":
            return []
        return None

    def write_json(self, user_id, data_type, data):
        """Write JSON data to Mega."""
        user_folder = self._get_user_folder(user_id)
        file_name = self._get_data_path(user_id, data_type)
        # Check if file exists
        files = self.mega_session.get_files_in_node(user_folder)
        existing_node = None
        for f in files:
            if f['name'] == file_name and f['type'] == 0:
                existing_node = f
                break
        # Convert data to JSON string
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        if existing_node:
            # Delete existing file and upload new
            self.mega_session.delete(existing_node['h'])
        # Upload new file
        self.mega_session.upload(
            (json_str.encode('utf-8'), file_name),
            dest=user_folder['h']
        )
        logger.info(f"Written {file_name} for user {user_id}")

    def upload_file(self, user_id, file_path, file_name=None):
        """Upload a local file to user's folder."""
        user_folder = self._get_user_folder(user_id)
        if not file_name:
            file_name = os.path.basename(file_path)
        # We'll upload from disk
        try:
            self.mega_session.upload(file_path, dest=user_folder['h'])
            logger.info(f"Uploaded {file_name} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return False

    def download_file(self, user_id, file_name):
        """Download a file from user's folder (returns bytes)."""
        user_folder = self._get_user_folder(user_id)
        files = self.mega_session.get_files_in_node(user_folder)
        for f in files:
            if f['name'] == file_name and f['type'] == 0:
                return self.mega_session.download(f)
        return None

# Initialize storage
storage = MegaStorage(MEGA_EMAIL, MEGA_PASSWORD)

# ========== CONVERSATION STATES ==========
SUBJECT_SELECTION, MARKS_INPUT = range(2)
TASK_DESCRIPTION = 3
GEMINI_QUERY = 4
STORE_PAPER = 5

# ========== HELPER FUNCTIONS ==========
def main_menu_keyboard():
    """Create the main menu inline keyboard."""
    keyboard = [
        [InlineKeyboardButton("➕ New Task", callback_data="new_task")],
        [InlineKeyboardButton("📅 Today Tasks", callback_data="today_tasks")],
        [InlineKeyboardButton("📝 Add Marks", callback_data="add_marks")],
        [InlineKeyboardButton("🤖 Ask Gemini", callback_data="ask_gemini")],
        [InlineKeyboardButton("📊 Marks Analyze", callback_data="marks_analyze")],
        [InlineKeyboardButton("📁 Store Paper", callback_data="store_paper")],
        [InlineKeyboardButton("🎥 Video Lesson", callback_data="video_lesson")],
    ]
    return InlineKeyboardMarkup(keyboard)

def subject_keyboard():
    """Keyboard for subject selection."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧬 Biology", callback_data="subject_bio"),
         InlineKeyboardButton("📐 Mathematics", callback_data="subject_maths"),
         InlineKeyboardButton("⚗️ Chemistry", callback_data="subject_chemistry")]
    ])

def get_subject_name(callback_data):
    """Map callback data to subject name."""
    mapping = {
        "subject_bio": "Biology",
        "subject_maths": "Mathematics",
        "subject_chemistry": "Chemistry"
    }
    return mapping.get(callback_data)

# ========== DATABASE OPERATIONS (via Mega) ==========
def get_user_tasks(user_id):
    tasks = storage.read_json(user_id, "tasks")
    return tasks if tasks is not None else []

def save_user_tasks(user_id, tasks):
    storage.write_json(user_id, "tasks", tasks)

def get_user_marks(user_id):
    marks = storage.read_json(user_id, "marks")
    return marks if marks is not None else []

def save_user_marks(user_id, marks):
    storage.write_json(user_id, "marks", marks)

# ========== HANDLERS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message and main menu."""
    user = update.effective_user
    await update.message.reply_text(
        f"🌟 *නමස්කාර {user.first_name}!* 🌟\n\n"
        f"මම ඔබගේ පුද්ගලික පාඩම් සහායක බොට් වෙමි.\n"
        f"පහත බොත්තම් භාවිතා කර ඔබට අවශ්‍ය සේවාව තෝරාගන්න.",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *උපකාරක පණිවිඩය*\n\n"
        "• /start - ප්‍රධාන මෙනුව විවෘත කරන්න\n"
        "• /help - මෙම පණිවිඩය පෙන්වන්න\n\n"
        "ප්‍රශ්න ඇත්නම් බොට් සාදන්නා අමතන්න.",
        parse_mode="Markdown"
    )

# ---- New Task conversation ----
async def new_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "✏️ *අලුත් කර්තව්‍යයක් ඇතුළත් කරන්න:*\n\n"
        "කර්තව්‍යයේ විස්තරය ලියන්න (උදා: පාඩම් කරන්න 3-5 පරිච්ඡේදය)",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]),
        parse_mode="Markdown"
    )
    return TASK_DESCRIPTION

async def task_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    task_text = update.message.text.strip()
    if not task_text:
        await update.message.reply_text("❌ කර්තව්‍යය හිස් විය නොහැක. නැවත උත්සාහ කරන්න.")
        return TASK_DESCRIPTION

    tasks = get_user_tasks(user.id)
    tasks.append({
        "task": task_text,
        "date": date.today().isoformat(),
        "status": "pending"
    })
    save_user_tasks(user.id, tasks)

    await update.message.reply_text(
        f"✅ *කර්තව්‍යය සාර්ථකව සුරැකිණි!*\n\n"
        f"📌 `{task_text}`",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# ---- Today Tasks ----
async def today_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    tasks = get_user_tasks(user.id)
    today_str = date.today().isoformat()
    today_tasks = [t for t in tasks if t["date"] == today_str]

    if today_tasks:
        task_list = "\n".join([f"• {t['task']}" for t in today_tasks])
        text = f"📅 *අද ({date.today().strftime('%Y-%m-%d')}) කර්තව්‍ය:*\n\n{task_list}"
    else:
        text = "📭 *අද සඳහා කර්තව්‍ය නොමැත.*\n\nනව කර්තව්‍යයක් එක් කිරීමට `➕ New Task` බොත්තම ඔබන්න."

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard())

# ---- Add Marks conversation ----
async def add_marks_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📝 *ලකුණු එකතු කිරීම*\n\n"
        "පළමුව විෂය තෝරන්න:",
        reply_markup=subject_keyboard(),
        parse_mode="Markdown"
    )
    return SUBJECT_SELECTION

async def subject_selection_for_marks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    subject = get_subject_name(data)
    if subject:
        context.user_data["marks_subject"] = subject
        await query.edit_message_text(
            f"📚 *විෂය:* {subject}\n\n"
            f"✏️ ලබාගත් ලකුණු ඇතුළත් කරන්න (0-100):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]),
            parse_mode="Markdown"
        )
        return MARKS_INPUT
    else:
        await query.edit_message_text("❌ වලංගු විෂයක් තෝරන්න.")
        return ConversationHandler.END

async def marks_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    subject = context.user_data.get("marks_subject")
    if not subject:
        await update.message.reply_text("⚠️ දෝෂයක් ඇතිවිය. කරුණාකර නැවත /start ඔබන්න.")
        return ConversationHandler.END

    try:
        marks = int(update.message.text.strip())
        if marks < 0 or marks > 100:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ කරුණාකර ලකුණු 0-100 අතර අංකයක් ඇතුළත් කරන්න.")
        return MARKS_INPUT

    # Save mark
    marks_list = get_user_marks(user.id)
    marks_list.append({
        "subject": subject,
        "marks": marks,
        "date": date.today().isoformat()
    })
    save_user_marks(user.id, marks_list)

    await update.message.reply_text(
        f"✅ *ලකුණු සාර්ථකව සුරැකිණි!*\n\n"
        f"📊 {subject}: {marks}\n"
        f"📅 දිනය: {date.today().strftime('%Y-%m-%d')}",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )
    context.user_data.pop("marks_subject", None)
    return ConversationHandler.END

# ---- Ask Gemini conversation ----
async def ask_gemini_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🤖 *Gemini AI සමඟ කතා කරන්න*\n\n"
        "ඔබගේ ප්‍රශ්නය හෝ ගැටලුව පහතින් ටයිප් කරන්න:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]),
        parse_mode="Markdown"
    )
    return GEMINI_QUERY

async def gemini_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()
    if not user_message:
        await update.message.reply_text("❌ කරුණාකර ප්‍රශ්නයක් ඇතුළත් කරන්න.")
        return GEMINI_QUERY

    await update.message.chat.send_action(action="typing")
    try:
        response = gemini_model.generate_content(user_message)
        reply = response.text
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        reply = "⚠️ සමාවන්න, දැනට පිළිතුරු දිය නොහැක. පසුව නැවත උත්සාහ කරන්න."

    await update.message.reply_text(
        f"🤖 *Gemini:*\n{reply}",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    return ConversationHandler.END

# ---- Marks Analyze ----
async def marks_analyze_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["analyze_mode"] = True
    await query.edit_message_text(
        "📊 *ලකුණු විශ්ලේෂණය*\n\n"
        "විශ්ලේෂණය කිරීමට විෂය තෝරන්න:",
        reply_markup=subject_keyboard(),
        parse_mode="Markdown"
    )
    # We'll handle the subject selection in a generic subject handler

async def analyze_marks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle subject selection for marks analyze."""
    query = update.callback_query
    await query.answer()
    data = query.data
    subject = get_subject_name(data)
    if not subject:
        await query.edit_message_text("❌ වලංගු විෂයක් තෝරන්න.", reply_markup=main_menu_keyboard())
        return ConversationHandler.END

    user = update.effective_user
    marks_list = get_user_marks(user.id)
    subject_marks = [m for m in marks_list if m["subject"] == subject]
    if not subject_marks:
        await query.edit_message_text(
            f"❌ *{subject}* සඳහා ලකුණු දත්ත නොමැත.\n\n"
            f"කරුණාකර පළමුව 'Add Marks' මගින් ලකුණු එකතු කරන්න.",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )
        context.user_data.pop("analyze_mode", None)
        return ConversationHandler.END

    # Prepare data for Gemini
    marks_text = "\n".join([f"දිනය: {m['date']}, ලකුණු: {m['marks']}" for m in subject_marks[-10:]])
    prompt = f"""
    ඔබ සිංහලෙන් පිළිතුරු දෙන්න. පහත දත්ත මත පදනම්ව විශ්ලේෂණයක් සහ උපදෙස් ලබා දෙන්න.
    විෂය: {subject}
    දත්ත:
    {marks_text}

    මෙම ශිෂ්‍යයාගේ ප්‍රගතිය ගැන විශ්ලේෂණය කර, දුර්වල කරුණු හඳුනාගෙන, වැඩිදියුණු කිරීමට ප්‍රායෝගික උපදෙස් දෙන්න. 
    ලකුණු වැඩිදියුණු කර ගැනීමට ක්‍රම යෝජනා කරන්න.
    """

    await query.edit_message_text("🔄 දත්ත විශ්ලේෂණය කරමින්... කරුණාකර රැඳී සිටින්න.")
    try:
        response = gemini_model.generate_content(prompt)
        analysis = response.text
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        analysis = "⚠️ සමාවන්න, දත්ත විශ්ලේෂණය කිරීමේදී දෝෂයක් ඇති විය."

    await query.edit_message_text(
        f"📊 *{subject} විශ්ලේෂණය*\n\n{analysis}",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    context.user_data.pop("analyze_mode", None)
    return ConversationHandler.END

# ---- Store Paper (file upload) ----
async def store_paper_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📁 *කඩදාසි ගොනුව යවන්න*\n\n"
        "PDF, රූප (JPEG, PNG) හෝ ඕනෑම ගොනු වර්ගයක් යැවිය හැක.\n\n"
        "ගොනුව යැවීමෙන් පසු එය ඔබගේ වලාකුළු ගබඩාවේ සුරකිනු ඇත.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]),
        parse_mode="Markdown"
    )
    return STORE_PAPER

async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    document = None
    file_name = None
    if update.message.document:
        document = update.message.document
        file_name = document.file_name
    elif update.message.photo:
        # Get largest photo
        document = update.message.photo[-1]
        file_name = f"photo_{user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
    else:
        await update.message.reply_text("❌ කරුණාකර PDF හෝ රූප ගොනුවක් යවන්න.")
        return STORE_PAPER

    # Download file locally
    new_file = await context.bot.get_file(document.file_id)
    os.makedirs("temp", exist_ok=True)
    temp_path = os.path.join("temp", file_name)
    await new_file.download_to_drive(temp_path)

    # Upload to Mega
    success = storage.upload_file(user.id, temp_path, file_name)
    os.remove(temp_path)  # Clean up

    if success:
        await update.message.reply_text(
            f"✅ *ගොනුව සාර්ථකව සුරැකිණි!*\n\n"
            f"📄 නම: `{file_name}`\n"
            f"☁️ ගබඩාව: Mega.nz",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ ගොනුව උඩුගත කිරීම අසාර්ථකයි. පසුව නැවත උත්සාහ කරන්න.",
            reply_markup=main_menu_keyboard()
        )
    return ConversationHandler.END

# ---- Video Lessons ----
async def video_lesson_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["video_lesson"] = True
    await query.edit_message_text(
        "🎥 *වීඩියෝ පාඩම්*\n\n"
        "පාඩම් බැලීමට විෂය තෝරන්න:",
        reply_markup=subject_keyboard(),
        parse_mode="Markdown"
    )

async def send_video_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle subject selection for video lessons."""
    query = update.callback_query
    await query.answer()
    data = query.data
    subject = get_subject_name(data)
    # Hardcoded links (you can replace with actual stored links)
    links = {
        "Biology": "https://www.youtube.com/playlist?list=PL_...",
        "Mathematics": "https://www.youtube.com/playlist?list=PL_...",
        "Chemistry": "https://www.youtube.com/playlist?list=PL_..."
    }
    link = links.get(subject, "https://www.youtube.com/results?search_query=ඉගෙනුම")
    await query.edit_message_text(
        f"🎬 *{subject} වීඩියෝ පාඩම්*\n\n"
        f"[Click here to watch]({link})\n\n"
        f"වැඩි විස්තර සඳහා යූටියුබ් එකේ 'ඉගෙනුම' ලෙස සෙවීම කරන්න.",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    context.user_data.pop("video_lesson", None)
    return ConversationHandler.END

# ---- Back to main menu ----
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🏠 *ප්‍රධාන මෙනුව*",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    # Clear any state
    context.user_data.clear()
    return ConversationHandler.END

# ---- Generic subject handler (for analyze and video lessons) ----
async def generic_subject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route subject selections based on context flags."""
    if context.user_data.get("analyze_mode"):
        return await analyze_marks(update, context)
    elif context.user_data.get("video_lesson"):
        return await send_video_lesson(update, context)
    else:
        # This should not happen, but fallback to add marks if needed
        return await subject_selection_for_marks(update, context)

# ========== MAIN APPLICATION ==========
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Conversation handlers
    new_task_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(new_task_start, pattern="^new_task$")],
        states={TASK_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_description)]},
        fallbacks=[CallbackQueryHandler(back_to_main, pattern="^back_to_main$")],
    )

    add_marks_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_marks_start, pattern="^add_marks$")],
        states={
            SUBJECT_SELECTION: [CallbackQueryHandler(subject_selection_for_marks, pattern="^subject_")],
            MARKS_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, marks_input)],
        },
        fallbacks=[CallbackQueryHandler(back_to_main, pattern="^back_to_main$")],
    )

    ask_gemini_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_gemini_start, pattern="^ask_gemini$")],
        states={GEMINI_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, gemini_query)]},
        fallbacks=[CallbackQueryHandler(back_to_main, pattern="^back_to_main$")],
    )

    store_paper_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(store_paper_start, pattern="^store_paper$")],
        states={STORE_PAPER: [MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file_upload)]},
        fallbacks=[CallbackQueryHandler(back_to_main, pattern="^back_to_main$")],
    )

    # Direct handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(today_tasks, pattern="^today_tasks$"))
    application.add_handler(CallbackQueryHandler(marks_analyze_start, pattern="^marks_analyze$"))
    application.add_handler(CallbackQueryHandler(video_lesson_start, pattern="^video_lesson$"))
    application.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_to_main$"))
    # Subject selection handler (for analyze and video lessons)
    application.add_handler(CallbackQueryHandler(generic_subject_handler, pattern="^subject_"))

    # Add conversation handlers
    application.add_handler(new_task_conv)
    application.add_handler(add_marks_conv)
    application.add_handler(ask_gemini_conv)
    application.add_handler(store_paper_conv)

    # Start bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
