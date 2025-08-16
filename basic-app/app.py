from shiny import App, reactive, render, ui
import pandas as pd

# ---- UI ----
# If your Shiny version supports theming on core pages, this will work.
# Otherwise it will be ignored; the app still runs fine.
THEME = ui.Theme.from_brand(__file__)


app_ui = ui.page_fluid(
    ui.panel_title("Find a Job"),
    ui.input_action_button("refresh", "Refresh sheet"),
    ui.card(ui.output_table("sheet_preview")),
    theme=THEME,  # safe even if THEME is None
)

# ---- Server ----
CSV_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "157-BXoh1_PivN28bHrDkKbwS7lnp7nknlud-d7GoQxA"
    "/export?format=csv&gid=0"
)

def load_sheet() -> pd.DataFrame:
    return pd.read_csv(CSV_URL)

def server(input, output, session):
    @reactive.calc
    def sheet_df() -> pd.DataFrame:
        # Depend on the button and auto-refresh every 60s
        input.refresh()
        reactive.invalidate_later(60)
        return load_sheet()

    @output
    @render.table
    def sheet_preview():
        return sheet_df()

app = App(app_ui, server)
