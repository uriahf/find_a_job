import os
from pathlib import Path
from shiny import reactive
from shiny.express import input, render, ui
from chatlas import ChatGoogle
import pandas as pd
from dotenv import load_dotenv

# Get the directory containing app.py
app_dir = Path(__file__).parent
env_path = app_dir / '.env'

# Load environment variables with explicit path
load_dotenv(env_path)

# Theme setup
THEME = ui.Theme.from_brand(__file__)

api_key = os.getenv("GOOGLE_API_KEY")


# Chat client setup
chat_client = ChatGoogle(
    api_key=api_key,
    system_prompt="You are a helpful job search assistant. You can analyze job listings and provide advice to job seekers."
)

# ---- Data Loading ----
CSV_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "157-BXoh1_PivN28bHrDkKbwS7lnp7nknlud-d7GoQxA"
    "/export?format=csv&gid=0"
)

def load_sheet() -> pd.DataFrame:
    return pd.read_csv(CSV_URL)

# ---- UI ----
ui.page_opts(title="Find a Job", theme=THEME)

with ui.layout_columns(col_widths=[8, 4]):
    # Main panel
    with ui.card():
        ui.input_action_button("refresh", "Refresh sheet")
        @render.table
        def sheet_preview():
            return sheet_df()
    
    # Chat sidebar
    with ui.card():
        chat = ui.Chat("chat")
        chat.ui(
            messages=["Hi! I can help you analyze job listings. What would you like to know?"],
            height="600px"
        )

# ---- Server ----
@reactive.calc
def sheet_df() -> pd.DataFrame:
    input.refresh()
    reactive.invalidate_later(60)
    return load_sheet()

@chat.on_user_submit
async def handle_chat(message: str):
    df = sheet_df()
    prompt = f"Given these job listings:\n\n{df.to_string()}\n\nUser question: {message}"
    response = await chat_client.stream_async(prompt)
    await chat.append_message_stream(response)