import flet as ft
import scripts.FlashCard_v2 as FlashCard
import scripts.FileWork_v3 as fw
from scripts import Scheduler_v1 as scheduler

vocab_list = [
    ["whoever","""[pron.] 无论谁；…的那个人（或那些人）；…的任何人；不管什么人
[网络] 爱谁谁；究竟是谁；无论是谁""",""" [1] Claudia is right, I mean two days ago you were fighting with her and telling whoever wanted to listen that you were happy with Minmei.
[2] Whoever curses his father or his mother, his lamp shall be put out in deep darkness.
[3] We were in front of a bar and he ducked slightly, peering in, but whoever he was looking for did not seem to be there."""],
    ["argue","""[v.] 争论；争辩；争吵；论证
[网络] 辩论；说服；主张""","""[1] it seems useless for you to argue further with him.
[2] While gold supply is well understood, silver bulls and bears argue about just how much silver is out there.
[3] Sullivan sighed, but he did not argue. ""I think I'll miss you, Jonathan, "" was all he said."""],
    ["behalf","""[n.] 利益
[网络] 方面；支持；维护""","""[1] Isaac prayed to the Lord on behalf of his wife, because she was barren.
[2] You will also learn about our many operations on your behalf, to prevent the dark Ones from destroying you and Mother Earth.
[3] The United States is ready to join a global effort on behalf of new jobs and sustainable growth."""]]

class FlashCardSet(ft.Container):
    completed: bool
    index: int

    def __init__(self, vocab_list, index=1, completed=False, learning=False, list_path=None):
        super().__init__()

        self.list_path = list_path
        self.learning = learning
        self.cards = []
        for i, vocab in enumerate(vocab_list):
            word, definition, example = vocab[0], vocab[1], vocab[2]
            state = vocab[3] if len(vocab) >= 4 and isinstance(vocab[3], scheduler.CardState) else scheduler.default_card_state()
            card_view = FlashCard.FlashCard(i + 1, word, definition, example)
            self.cards.append({
                "word": word,
                "definition": definition,
                "example": example,
                "state": state,
                "view": card_view,
            })

        self.index = 0 if self.cards else -1
        self.feedback_text = ft.Text(value="", size=16)
        self.due_label = ft.Text(value="", size=18, weight=ft.FontWeight.BOLD)
        self.queue_label = ft.Text(value="", size=16)

        self.left_button = ft.FloatingActionButton(icon=ft.Icons.ARROW_LEFT, on_click=self.Last_Card)
        self.right_button = ft.FloatingActionButton(icon=ft.Icons.ARROW_RIGHT, on_click=self.Next_Card)

        self.again_button = ft.FilledButton(text="Again", style=ft.ButtonStyle(bgcolor={ft.ControlState.DEFAULT: ft.Colors.RED_200}), on_click=lambda e: self.apply_rating("again"))
        self.hard_button = ft.FilledButton(text="Hard", style=ft.ButtonStyle(bgcolor={ft.ControlState.DEFAULT: ft.Colors.ORANGE_200}), on_click=lambda e: self.apply_rating("hard"))
        self.good_button = ft.FilledButton(text="Good", style=ft.ButtonStyle(bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREEN_200}), on_click=lambda e: self.apply_rating("good"))
        self.easy_button = ft.FilledButton(text="Easy", style=ft.ButtonStyle(bgcolor={ft.ControlState.DEFAULT: ft.Colors.BLUE_200}), on_click=lambda e: self.apply_rating("easy"))

        self.card_container = ft.Container(content=None, expand=True)
        self.nav_row = ft.Row(
            controls=[
                self.left_button,
                self.card_container,
                self.right_button,
            ],
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        self.rating_row = ft.Row(
            controls=[
                self.again_button,
                self.hard_button,
                self.good_button,
                self.easy_button,
            ],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        )

        self.Display = ft.Container(
            content=ft.Column(
                controls=[
                    self.nav_row,
                    self.due_label,
                    self.queue_label,
                    self.feedback_text,
                    self.rating_row,
                ],
                expand=True,
                spacing=15,
            ),
            bgcolor=ft.Colors.GREY_200,
            border_radius=20,
            padding=20,
            expand=True,
        )

        self.expand = True
        self.content = self.Display
        self.bgcolor = ft.Colors.GREY_100
        self.border_radius = 20

        self.completed = completed
        self._rebuild_queue()
        self._show_card()

    def _rebuild_queue(self):
        if not self.cards:
            self.due_count = 0
            self.completed = True
            return

        now = scheduler.now_timestamp()
        self.cards.sort(key=lambda c: c["state"].due)
        for idx, card in enumerate(self.cards, start=1):
            card["view"].set_index(idx)
        self.due_count = sum(1 for card in self.cards if scheduler.is_due(card["state"], now))
        self.completed = self.due_count == 0 and len(self.cards) > 0
        if self.index < 0:
            self.index = 0
        elif self.index >= len(self.cards):
            self.index = len(self.cards) - 1

    def _show_card(self):
        if not self.cards:
            self.card_container.content = ft.Text("No cards available", size=24, weight=ft.FontWeight.BOLD)
            self._set_rating_enabled(False)
            self.due_label.value = ""
            self.feedback_text.value = ""
            self.Display.update()
            return

        self.card_container.content = self.cards[self.index]["view"]
        self._update_status_text()
        self._set_rating_enabled(self.due_count > 0)
        self.Display.update()

    def _set_rating_enabled(self, enabled: bool):
        for button in [self.again_button, self.hard_button, self.good_button, self.easy_button]:
            button.disabled = not enabled
            button.update()

    def _update_status_text(self):
        now = scheduler.now_timestamp()
        current_state = self.cards[self.index]["state"]
        current_word = self.cards[self.index]["word"]
        if self.due_count > 0 and scheduler.is_due(current_state, now):
            status = f"Review '{current_word}' — {scheduler.describe_due(current_state, now)}"
        elif self.due_count == 0:
            next_state = self.cards[0]["state"] if self.cards else None
            status = scheduler.next_review_message(next_state)
        else:
            status = f"Upcoming '{current_word}' — {scheduler.describe_due(current_state, now)}"

        self.due_label.value = status
        remaining = f"Remaining due today: {self.due_count}"
        self.queue_label.value = remaining
        self.due_label.update()
        self.queue_label.update()

    def _update_feedback(self, word: str, state: scheduler.CardState):
        message = f"Next review for '{word}' is {scheduler.describe_due(state)}"
        self.feedback_text.value = message + f" | Remaining due today: {self.due_count}"
        self.feedback_text.update()

    def Last_Card(self, e):
        if not self.cards:
            return
        if self.index > 0:
            self.index -= 1
            self._show_card()

    def Next_Card(self, e):
        if not self.cards:
            return
        if self.index < len(self.cards) - 1:
            self.index += 1
            self._show_card()

    def apply_rating(self, rating: str):
        if not self.cards or self.due_count == 0:
            return

        card = self.cards[self.index]
        new_state = scheduler.schedule(card["state"], rating)
        card["state"] = new_state
        word = card["word"]

        if self.list_path:
            fw.writeCardState(self.list_path, card["word"], new_state)

        self._rebuild_queue()
        self.index = 0 if self.cards else -1
        if self.cards:
            self._update_feedback(word, new_state)
        self._show_card()

    def getStatus(self):
        return self.completed

    def getLength(self):
        return len(self.cards)

    def getIndex(self):
        return self.index + 1 if self.cards else 0

    def setIndex(self, index):
        if not self.cards:
            self.index = -1
        else:
            self.index = max(0, min(len(self.cards) - 1, index - 1))
        self._show_card()

def main(page: ft.Page):
    page.title = "Flashcards"
    page.window.width = 1000
    page.window.height = 600
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    new_set = FlashCardSet(vocab_list)
    page.add(new_set)
    

if __name__ == "__main__":
    ft.app(target=main)
    
"""
1. Adjusted get/set index value by adding it by 1 (since inside the class it represents the index of list, but outside the class it represent the current page that you're on)

"""