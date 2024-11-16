from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable, Static


class StatusApp(App):
    BINDINGS = (
        Binding("j", "cursor_up_5", "Cursor up", show=False),
        Binding("k", "cursor_down_5", "Cursor down", show=False),
        Binding("h", "cursor_up_20", "Cursor up", show=False),
        Binding("l", "cursor_down_20", "Cursor down", show=False),
    )
    TABLE = DataTable()

    def action_cursor_up_20(self):
        for _ in range(4):
            self.action_cursor_up_5()

    def action_cursor_down_20(self):
        for _ in range(4):
            self.action_cursor_down_5()

    def action_cursor_up_5(self):
        for _ in range(5):
            self.TABLE.action_cursor_up()

    def action_cursor_down_5(self):
        for _ in range(5):
            self.TABLE.action_cursor_down()

    def __init__(self, headers, rows, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers = headers
        self.rows = rows

    def compose(self) -> ComposeResult:
        self.TABLE.add_columns(*self.headers)
        self.TABLE.add_rows(self.rows)
        self.TABLE.zebra_stripes = True
        self.TABLE.cursor_type = "row"
        with Static():
            yield self.TABLE

    async def _on_key(self, event: events.Key) -> None:
        if event.name == "escape":
            self.clear_notifications()
            self.exit()
