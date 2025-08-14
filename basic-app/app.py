from shiny import reactive, render, ui
from shiny.express import input
import pandas as pd

ui.panel_title("Find a Job")

ui.input_action_button("refresh", "Refresh sheet")


CSV_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "157-BXoh1_PivN28bHrDkKbwS7lnp7nknlud-d7GoQxA"
    "/export?format=csv&gid=0"
)

def load_sheet():
    return pd.read_csv(CSV_URL)

@reactive.calc
def sheet_df():
    input.refresh()               # trigger on button click
    reactive.invalidate_later(60) # and auto-refresh every 60s
    return load_sheet()

@render.table
def sheet_preview():
    return sheet_df()
