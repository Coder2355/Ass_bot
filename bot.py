from pyrogram import Client, filters
from PIL import Image
import pytesseract
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import Config

# Tesseract configuration
pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD

# Initialize Pyrogram Client with API ID and API hash
app = Client("assignment_bot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)

# Set up Telegram bot with Application class (v20+)
application = Application.builder().token(Config.BOT_TOKEN).build()

# Store temporary user data
user_data = {}

# Start command
async def start(update: Update, context):
    """Send a welcome message when the /start command is issued."""
    await update.message.reply_text(Config.START_MESSAGE)

# Analyze handwriting from photo
@app.on_message(filters._Photo)
async def analyze_handwriting(client, message):
    # Notify the user that their request is being processed
    await message.reply_text(Config.STATUS_MESSAGE)

    # Download the photo
    photo_path = await message.download()

    # Open the image and perform handwriting recognition (OCR)
    image = Image.open(photo_path)
    handwriting_text = pytesseract.image_to_string(image)

    # Set handwriting in user data and ask for a paragraph
    user_id = message.from_user.id
    user_data[user_id] = {"handwriting": handwriting_text}
    
    # Ask user to send a paragraph
    await message.reply_text("I've analyzed your handwriting. Now please send the paragraph you'd like to format.")

# Handle paragraph and display language options
@app.on_message(filters.Text)
async def handle_paragraph(client, message):
    user_id = message.from_user.id
    if user_id in user_data:
        user_data[user_id]["paragraph"] = message.text

        # Show language options (Tamil or English)
        keyboard = [
            [InlineKeyboardButton("Tamil", callback_data='language_tamil'),
             InlineKeyboardButton("English", callback_data='language_english')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text("Choose a language:", reply_markup=reply_markup)

# Handle language selection and display sheet options
async def handle_language(update: Update, context):
    query = update.callback_query
    user_id = query.from_user.id
    
    if query.data == 'language_tamil':
        user_data[user_id]["language"] = "Tamil"
    elif query.data == 'language_english':
        user_data[user_id]["language"] = "English"

    # Show sheet size options (A4 or others)
    keyboard = [
        [InlineKeyboardButton("A4", callback_data='sheet_a4'),
         InlineKeyboardButton("Other", callback_data='sheet_other')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("Choose sheet size:", reply_markup=reply_markup)

# Handle sheet size selection and display color options
async def handle_sheet_size(update: Update, context):
    query = update.callback_query
    user_id = query.from_user.id
    
    if query.data == 'sheet_a4':
        user_data[user_id]["sheet"] = "A4"
    elif query.data == 'sheet_other':
        user_data[user_id]["sheet"] = "Other"

    # Show color options (Blue or Black)
    keyboard = [
        [InlineKeyboardButton("Blue", callback_data='color_blue'),
         InlineKeyboardButton("Black", callback_data='color_black')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("Choose ink color:", reply_markup=reply_markup)

# Handle color selection and send output
async def handle_color(update: Update, context):
    query = update.callback_query
    user_id = query.from_user.id
    
    if query.data == 'color_blue':
        user_data[user_id]["color"] = "Blue"
    elif query.data == 'color_black':
        user_data[user_id]["color"] = "Black"

    # Send the final output
    handwriting = user_data[user_id]["handwriting"]
    paragraph = user_data[user_id]["paragraph"]
    language = user_data[user_id]["language"]
    sheet = user_data[user_id]["sheet"]
    color = user_data[user_id]["color"]

    output = (f"Handwriting Analyzed: {handwriting}\n"
              f"Paragraph: {paragraph}\n"
              f"Language: {language}\n"
              f"Sheet: {sheet}\n"
              f"Color: {color}\n")

    await query.message.reply_text(output)

# Register handlers
application.add_handler(CommandHandler('start', start))
application.add_handler(CallbackQueryHandler(handle_language, pattern='^language_'))
application.add_handler(CallbackQueryHandler(handle_sheet_size, pattern='^sheet_'))
application.add_handler(CallbackQueryHandler(handle_color, pattern='^color_'))

# Start the Pyrogram app
app.run()

# Start the Telegram bot
application.run_polling()
