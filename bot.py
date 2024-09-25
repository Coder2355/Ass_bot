import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image, ImageDraw, ImageFont
import config

app = Client("AssignmentBot", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)

user_data = {}

# Start command
@app.on_message(filters.command(["start"]))
async def start(client, message):
    await message.reply(
        "Welcome to the Assignment Writer Bot! Please send me a paragraph to get started.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Get Started", callback_data="get_started")]
        ])
    )

# Process the paragraph
@app.on_message(filters.text & ~filters.command(["start"]))  # Ensure we process only text messages that are not commands
async def receive_paragraph(client, message):
    user_id = message.from_user.id
    user_data[user_id] = {"paragraph": message.text}
    
    await message.reply(
        "Choose the paper size:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("A4", callback_data="A4"), InlineKeyboardButton("A3", callback_data="A3")],
            [InlineKeyboardButton("Rule", callback_data="Rule")]
        ])
    )

# Handle callback queries for paper size, color, and font
@app.on_callback_query()
async def handle_callback(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    if data in ["A4", "A3", "Rule"]:
        user_data[user_id]["paper_size"] = data
        await callback_query.message.reply(
            "Choose the ink color:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Blue", callback_data="Blue"), InlineKeyboardButton("Black", callback_data="Black")]
            ])
        )
    elif data in ["Blue", "Black"]:
        user_data[user_id]["color"] = data
        await callback_query.message.reply(
            "Choose a font style:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Default Font", callback_data="default_font")],
                [InlineKeyboardButton("Upload Your Handwriting", callback_data="handwriting")]
            ])
        )
    elif data == "default_font":
        user_data[user_id]["font"] = "default"
        await process_assignment(client, callback_query.message, user_id)
    elif data == "handwriting":
        user_data[user_id]["font"] = "handwriting"
        await callback_query.message.reply("Please upload your handwriting as a document (image or font file).")

# Handle document upload for handwriting
@app.on_message(filters.document & filters.user(list(user_data.keys())))
async def receive_handwriting(client, message):
    user_id = message.from_user.id
    file = message.document
    
    # Ensure the user has selected the handwriting option
    if user_data.get(user_id, {}).get("font") == "handwriting":
        font_path = f"{user_id}_handwriting.ttf"
        await message.download(file_name=font_path)
        user_data[user_id]["handwriting_image"] = font_path
        
        await process_assignment(client, message, user_id)

# Process and generate the final image with the paragraph
async def process_assignment(client, message, user_id):
    data = user_data[user_id]
    
    paragraph = data["paragraph"]
    paper_size = data.get("paper_size", "A4")
    color = data.get("color", "Black")
    font_style = data.get("font", "default")
    
    # Set up paper dimensions based on selection
    if paper_size == "A4":
        image_size = (1240, 1754)
    elif paper_size == "A3":
        image_size = (1754, 2480)
    else:  # Rule
        image_size = (1240, 1754)  # Defaulting to A4 for Rule

    # Create the image
    image = Image.new("RGB", image_size, "white")
    draw = ImageDraw.Draw(image)

    # Set font style
    if font_style == "default":
        font = ImageFont.load_default()
    elif font_style == "handwriting":
        font_path = user_data[user_id]["handwriting_image"]
        font = ImageFont.truetype(font_path, 30)  # Adjust font size as needed
    
    # Set text color
    color_code = "blue" if color == "Blue" else "black"

    # Write the paragraph to the image
    margin = 50
    offset = 50
    for line in paragraph.split('\n'):
        draw.text((margin, offset), line, font=font, fill=color_code)
        offset += font.getsize(line)[1] + 15  # Line spacing

    # Save the image as a file
    output_image_path = f"{user_id}_assignment.png"
    image.save(output_image_path)

    # Send the image
    await message.reply_photo(photo=output_image_path, caption="Here is your assignment!")
    
    # Clean up by removing the saved image and font
    if os.path.exists(output_image_path):
        os.remove(output_image_path)
    if font_style == "handwriting" and os.path.exists(user_data[user_id]["handwriting_image"]):
        os.remove(user_data[user_id]["handwriting_image"])

# Start the bot
app.run()
