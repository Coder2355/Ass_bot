import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import API_ID, API_HASH, BOT_TOKEN

# Initialize the bot with API credentials from config
app = Client(
    "assignment_writer_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Dictionary to hold user data for different stages
user_data = {}

# Start message
@app.on_message(filters.command("start"))
async def start(client, message):
    start_text = (
        "👋 Welcome to the Assignment Writer Bot!\n\n"
        "📝 Send me the paragraph you want to write, and I'll help you create a customized assignment file. "
        "You can choose the paper size, ink color, and font style or even upload your handwriting!"
    )
    await message.reply_text(start_text)

# Receive the paragraph and prompt for paper size
@app.on_message(filters.text & ~filters.command("start"))
async def handle_paragraph(client, message):
    user_id = message.from_user.id
    user_data[user_id] = {"paragraph": message.text}  # Store the paragraph
    # Ask for paper size
    keyboard = [
        [InlineKeyboardButton("A4", callback_data="paper_A4"),
         InlineKeyboardButton("A3", callback_data="paper_A3"),
         InlineKeyboardButton("Rule", callback_data="paper_rule")]
    ]
    await message.reply_text("📄 Choose the paper size:", reply_markup=InlineKeyboardMarkup(keyboard))

# Handle paper size selection
@app.on_callback_query(filters.regex(r"^paper_"))
async def handle_paper_selection(client, callback_query):
    user_id = callback_query.from_user.id
    paper_size = callback_query.data.split("_")[1]
    user_data[user_id]["paper_size"] = paper_size  # Store selected paper size
    await callback_query.answer(f"Paper size {paper_size} selected.")

    # Ask for ink color
    keyboard = [
        [InlineKeyboardButton("Blue", callback_data="color_blue"),
         InlineKeyboardButton("Black", callback_data="color_black")]
    ]
    await callback_query.message.reply_text("✍️ Choose the ink color:", reply_markup=InlineKeyboardMarkup(keyboard))

# Handle color selection
@app.on_callback_query(filters.regex(r"^color_"))
async def handle_color_selection(client, callback_query):
    user_id = callback_query.from_user.id
    color = callback_query.data.split("_")[1]
    user_data[user_id]["color"] = color  # Store selected color
    await callback_query.answer(f"Ink color {color} selected.")

    # Ask for font style or handwriting upload
    keyboard = [
        [InlineKeyboardButton("Default Font", callback_data="font_default"),
         InlineKeyboardButton("Upload Handwriting", callback_data="font_upload")]
    ]
    await callback_query.message.reply_text("🎨 Choose the font style:", reply_markup=InlineKeyboardMarkup(keyboard))

# Handle font style selection or handwriting upload
@app.on_callback_query(filters.regex(r"^font_"))
async def handle_font_selection(client, callback_query):
    user_id = callback_query.from_user.id
    font_choice = callback_query.data.split("_")[1]

    if font_choice == "default":
        user_data[user_id]["font"] = "default"
        await callback_query.answer("Default font selected.")
        await process_assignment(client, callback_query.message, user_id)
    elif font_choice == "upload":
        user_data[user_id]["font"] = "handwriting"
        await callback_query.message.reply_text("📸 Please upload your handwriting as an image.")

# Handle handwriting image upload
@app.on_message(filters.photo)
async def handle_handwriting_upload(client, message):
    user_id = message.from_user.id
    if user_id in user_data and user_data[user_id].get("font") == "handwriting":
        file_path = await message.download()
        user_data[user_id]["handwriting_image"] = file_path  # Store the file path of handwriting
        await message.reply_text("Handwriting uploaded successfully.")
        await process_assignment(client, message, user_id)

# Process the final assignment and upload the file
async def process_assignment(client, message, user_id):
    paragraph = user_data[user_id]["paragraph"]
    paper_size = user_data[user_id]["paper_size"]
    color = user_data[user_id]["color"]
    font = user_data[user_id]["font"]

    # Simulate creating the assignment file (customization can be added here)
    if font == "default":
        # Generate assignment with default font
        assignment_file = f"{user_id}_assignment_default_font.txt"
    elif font == "handwriting":
        # Use uploaded handwriting image
        assignment_file = f"{user_id}_assignment_handwriting.txt"

    # Simulating file creation for demo purposes
    with open(assignment_file, "w") as f:
        f.write(f"Paper Size: {paper_size}\n")
        f.write(f"Ink Color: {color}\n")
        f.write(f"Font Style: {font}\n\n")
        f.write(paragraph)

    # Upload the generated file to the user
    await client.send_document(user_id, document=assignment_file, caption="Here is your assignment file!")

    # Clean up user data after the process
    del user_data[user_id]

# Run the bot
app.run()
