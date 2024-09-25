import os
from PIL import Image, ImageDraw, ImageFont
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Define your bot token and other configurations in config.py
from config import API_ID, API_HASH, BOT_TOKEN

app = Client("assignment_writer_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Dictionary to store user data during the process
user_data = {}

# Start command handler
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("Welcome to the Assignment Writer Bot! Please send me a paragraph to get started.")

# Paragraph handler
@app.on_message(filters.text & filters.command)
async def receive_paragraph(client, message):
    user_id = message.from_user.id
    paragraph = message.text
    user_data[user_id] = {"paragraph": paragraph}
    
    # Ask for paper size
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("A4", callback_data="paper_size:A4"),
         InlineKeyboardButton("A3", callback_data="paper_size:A3"),
         InlineKeyboardButton("Rule", callback_data="paper_size:Rule")]
    ])
    
    await message.reply("Choose paper size:", reply_markup=keyboard)

# Callback query handler for paper size, color, and font selection
@app.on_callback_query(filters.regex(r"^paper_size:(.+)"))
async def paper_size_selected(client, callback_query):
    user_id = callback_query.from_user.id
    paper_size = callback_query.data.split(":")[1]
    user_data[user_id]["paper_size"] = paper_size
    
    # Ask for ink color
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Blue", callback_data="color:blue"),
         InlineKeyboardButton("Black", callback_data="color:black")]
    ])
    
    await callback_query.message.reply("Choose ink color:", reply_markup=keyboard)

@app.on_callback_query(filters.regex(r"^color:(.+)"))
async def color_selected(client, callback_query):
    user_id = callback_query.from_user.id
    color = callback_query.data.split(":")[1]
    user_data[user_id]["color"] = color
    
    # Ask for font selection
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Default Font", callback_data="font:default"),
         InlineKeyboardButton("Upload Handwriting", callback_data="font:handwriting")]
    ])
    
    await callback_query.message.reply("Choose font style:", reply_markup=keyboard)

@app.on_callback_query(filters.regex(r"^font:(.+)"))
async def font_selected(client, callback_query):
    user_id = callback_query.from_user.id
    font_choice = callback_query.data.split(":")[1]
    user_data[user_id]["font"] = font_choice
    
    # If the user chooses handwriting, ask them to upload a font file
    if font_choice == "handwriting":
        await callback_query.message.reply("Please upload your handwriting font file (TTF format).")
    else:
        await process_assignment(client, callback_query.message, user_id)

# Handler for uploaded font file
@app.on_message(filters.document & filters.user(user_data.keys()))
async def receive_handwriting(client, message):
    user_id = message.from_user.id
    file = message.document
    
    # Ensure the user has selected the handwriting option
    if user_data.get(user_id, {}).get("font") == "handwriting":
        font_path = f"{user_id}_handwriting.ttf"
        await message.download(file_name=font_path)
        user_data[user_id]["handwriting_image"] = font_path
        
        await process_assignment(client, message, user_id)

# Process the final assignment and generate an image
async def process_assignment(client, message, user_id):
    paragraph = user_data[user_id]["paragraph"]
    paper_size = user_data[user_id]["paper_size"]
    color = user_data[user_id]["color"]
    font_choice = user_data[user_id]["font"]

    # Set up the A4 size (210mm x 297mm) in pixels for 300 DPI
    width, height = 2480, 3508  # A4 in pixels
    image = Image.new("RGB", (width, height), color="white")  # Create a white A4 image
    draw = ImageDraw.Draw(image)

    # Load default font or the uploaded handwriting font
    if font_choice == "default":
        try:
            font = ImageFont.truetype("arial.ttf", 40)  # Default font
        except IOError:
            font = ImageFont.load_default()  # Fallback if no TTF is available
    elif font_choice == "handwriting":
        font = ImageFont.truetype(user_data[user_id]["handwriting_image"], 40)  # Use uploaded handwriting

    # Set up text color based on user choice
    text_color = (0, 0, 255) if color == "blue" else (0, 0, 0)

    # Define text placement on the image
    margin = 100
    y_offset = 150
    max_width = width - 2 * margin  # Ensure text stays within the margins

    # Break text into lines to fit on A4
    lines = []
    words = paragraph.split(' ')
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        if draw.textsize(test_line, font=font)[0] < max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)

    # Draw text onto the image
    for line in lines:
        draw.text((margin, y_offset), line, font=font, fill=text_color)
        y_offset += draw.textsize(line, font=font)[1] + 10  # Line spacing

    # Save the image to a file
    image_file = f"{user_id}_assignment.png"
    image.save(image_file)

    # Upload the image file to the user
    await client.send_photo(user_id, image_file, caption="Here is your assignment with the chosen settings!")

    # Remove the image file from the local directory
    os.remove(image_file)

    # Clean up user data after the process
    del user_data[user_id]

if __name__ == "__main__":
    app.run()
