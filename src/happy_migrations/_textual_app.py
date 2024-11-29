from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable, Static, Footer


class StatusApp(App):
    BINDINGS = (
        Binding("esc", "exit", "Exit"),
        Binding("h", "cursor_up_20", "Up 20", show=False),
        Binding("j", "cursor_up_5", "Up 5", show=False),
        Binding("k", "cursor_down_5", "Down 5", show=False),
        Binding("l", "cursor_down_20", "Down 20", show=False),
        Binding("c", "toggle_cursor", "Toggle Cursor", show=False),
    )

    def action_exit(self):
        self.exit()

    def action_toggle_cursor(self) -> None:
        self.table.show_cursor = not self.table.show_cursor

    def action_cursor_up_20(self):
        for _ in range(4):
            self.action_cursor_up_5()

    def action_cursor_down_20(self):
        for _ in range(4):
            self.action_cursor_down_5()

    def action_cursor_up_5(self):
        for _ in range(5):
            self.table.action_cursor_up()

    def action_cursor_down_5(self):
        for _ in range(5):
            self.table.action_cursor_down()

    def __init__(self, headers, rows, theme, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Table data
        self.headers = headers
        self.rows = rows
        # Widgets
        self.table = DataTable()
        self.footer = Footer()
        self.wrapper = Static()
        # Setting up
        self.table.zebra_stripes = True
        self.table.cursor_type = "row"
        self.table.show_cursor = False
        self.footer.show_command_palette = False
        self.theme = theme

    def compose(self) -> ComposeResult:
        self.table.add_columns(*self.headers)
        self.table.add_rows(self.rows)
        with self.wrapper:
            yield self.table
        yield self.footer

    async def _on_key(self, event: events.Key) -> None:
        if event.name == "escape":
            self.clear_notifications()
            self.exit()
