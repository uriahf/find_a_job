import os
from pathlib import Path
from shiny import reactive
from shiny.express import input, render, ui
from chatlas import ChatGoogle
import pandas as pd
from dotenv import load_dotenv
from faicons import icon_svg

# Get the directory containing app.py
app_dir = Path(__file__).parent
env_path = app_dir / '.env'

# Load environment variables with explicit path
load_dotenv(env_path)

# Theme setup 
theme = ui.Theme().add_defaults(
    primary="#4A90E2",  # Professional blue
    secondary="#45B7AF",  # Teal accent
    success="#72994E",  # Green for positive messaging
    light="#F5F7FA",  # Light background
)

api_key = os.getenv("GOOGLE_API_KEY")


# Chat client setup with a fun personality
chat_client = ChatGoogle(
    api_key=api_key,
    system_prompt="""You are a friendly and witty job search assistant named JobBot. 
    You can analyze job listings and provide advice to job seekers.
    Keep your responses professional but inject appropriate humor and enthusiasm.
    Occasionally use relevant emojis to make your messages more engaging.
    When suggesting roles, be encouraging and highlight the positive aspects.

    When asked to find or filter jobs, always return a SQL query in a code block at the end
    of your message. For example:
    ```sql
    SELECT * FROM jobs WHERE title LIKE '%engineer%'
    ```
    """
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
ui.page_opts(
    title="JobBot - Your AI Job Search Assistant",
    theme=theme,
    fillable=True,
    class_="bg-light"
)

# Header with fun welcome message
with ui.card():
    with ui.card_header(class_="bg-primary text-white d-flex align-items-center gap-2"):
        ui.tags.i(class_="fa-solid fa-robot")
        "JobBot - Your AI Career Companion"

with ui.layout_columns(col_widths=[8, 4]):
    # Main panel - Job Listings
    with ui.card():
        with ui.card_header(class_="d-flex justify-content-between align-items-center"):
            ui.h4("Available Positions")
            ui.input_action_button(
                "refresh", 
                "Refresh",
                class_="btn-secondary",
                icon=icon_svg("arrow-rotate-right")
            )
        @render.data_frame
        def sheet_preview():
            return render.DataGrid(
                sheet_df(),
                height="700px",
                width="100%",
                filters=True,
                selection_mode="row",
            )
    
    # Chat sidebar
    with ui.card(class_="h-100"):
        with ui.card_header(class_="bg-secondary text-white"):
            "Chat with JobBot"
        chat = ui.Chat("chat")
        chat.ui(
            messages=[
                """👋 Hello! I'm JobBot, your friendly AI job search assistant! 
               
                What would you like to know? 🤔"""
            ],
            height="650px",
            placeholder="Ask me about the job listings...",
            content_type="html"
        )

# ---- Server ----
current_query = reactive.value("")

@reactive.calc
def sheet_df() -> pd.DataFrame:
    input.refresh()
    reactive.invalidate_later(60)
    df = load_sheet()
    
    # If there's a query, filter the dataframe
    if current_query():
        try:
            return df.query(current_query())
        except Exception:
            return df
    return df

import re

@chat.on_user_submit
async def handle_chat(message: str):
    df = load_sheet()
    prompt = f"""Given these job listings:\n\n{df.to_string()}\n\nUser question: {message}
    
    Remember to include a pandas query string in a code block if this is a search request."""
    
    response = await chat_client.stream_async(prompt)
    collected_text = ""
    
    async def stream_wrapper():
        nonlocal collected_text
        async for chunk in response:
            collected_text += chunk
            yield chunk
            
        # After streaming completes, check for SQL and update filter
        matches = re.findall(r'```(?:sql)?\n(.+?)\n```', collected_text, re.DOTALL)
        if matches:
            sql = matches[-1].strip()
            # Remove the SELECT and WHERE clauses
            query = sql.replace('SELECT * FROM jobs WHERE ', '')
            
            # Handle LIKE patterns
            if 'LIKE' in query:
                # Extract the column name and search term
                match = re.search(r"(\w+)\s+LIKE\s+'%([^%]+)%'", query)
                if match:
                    column, search_term = match.groups()
                    # Convert to pandas string contains
                    query = f"{column}.str.contains('{search_term}', case=False, na=False)"
            current_query.set(query)
    
    await chat.append_message_stream(stream_wrapper())