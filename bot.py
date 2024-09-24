from pyrogram import Client, filters
from PIL import Image
import pytesseract
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from config import Config
import pytesseract

# Initialize Pyrogram Client
app = Client("assignment_bot")


# Initialize Tesseract
pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD

# Initialize your bot using the token from config
TOKEN = Config.BOT_TOKEN
updater = Updater(TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Store temporary user data
user_data = {}

# Analyze handwriting from photo
@app.on_message(filters.photo)
async def analyze_handwriting(client, message):
    # Download the photo
    photo_path = await message.download()

    # Open the image and perform handwriting recognition (OCR)
    image = Image.open(photo_path)
    handwriting_text = pytesseract.image_to_string(image)

    # Set handwriting in user data and ask for paragraph
    user_id = message.from_user.id
    user_data[user_id] = {"handwriting": handwriting_text}
    
    # Ask user to send a paragraph
    await message.reply_text("I've analyzed your handwriting. Now please send the paragraph you'd like to format.")

# Handle paragraph and display language options
@app.on_message(filters.text)
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
def handle_language(update: Update, context):
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
    query.message.reply_text("Choose sheet size:", reply_markup=reply_markup)

# Handle sheet size selection and display color options
def handle_sheet_size(update: Update, context):
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
    query.message.reply_text("Choose ink color:", reply_markup=reply_markup)

# Handle color selection and send output
def handle_color(update: Update, context):
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

    query.message.reply_text(output)

# Register callback query handlers
dispatcher.add_handler(CallbackQueryHandler(handle_language, pattern='^language_'))
dispatcher.add_handler(CallbackQueryHandler(handle_sheet_size, pattern='^sheet_'))
dispatcher.add_handler(CallbackQueryHandler(handle_color, pattern='^color_'))

# Start the Pyrogram app
app.run()

# Start the Telegram bot
updater.start_polling()
