import flet as ft
import scripts.MC_Question_v2 as Question
from scripts import fsrs_scheduler


class MC_Question_Set(ft.Container):
    def __init__(self, cards, on_exit=None):
        super().__init__()
        self.cards = cards
        self.on_exit = on_exit
        self.scheduler = fsrs_scheduler.FSRSScheduler()

        self.queue = fsrs_scheduler.filter_due_cards(self.cards, now=self.scheduler.now())
        self.completed_num = 0
        self.awaiting_rating = False
        self.last_answer_correct = None
        self.current_card = None
        self.current_question = None

        self.title = ft.Text(
            value="Practice",
            size=35,
            weight=ft.FontWeight.BOLD,
        )

        self.progress_bar = ft.ProgressBar(value=0, height=10, border_radius=5)

        self.exit_button = ft.FloatingActionButton(
            text="Exit",
            on_click=self.exit,
            width=100,
        )

        self.upper_area = ft.Container(
            expand=2,
            padding=20,
            border_radius=20,
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.AMBER_100,
            content=ft.Row(
                controls=[self.title, self.exit_button],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                expand=True,
                height=100,
            ),
        )

        self.feedback_text = ft.Text(value="", size=20)

        self.question_container = ft.Container(expand=True, alignment=ft.alignment.center)

        self.rating_panel = ft.Row(
            controls=[
                self._create_rating_button("Again", "again", ft.Colors.RED_200),
                self._create_rating_button("Hard", "hard", ft.Colors.ORANGE_200),
                self._create_rating_button("Good", "good", ft.Colors.BLUE_200),
                self._create_rating_button("Easy", "easy", ft.Colors.GREEN_200),
            ],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            visible=False,
            expand=True,
        )

        self.question_display = ft.Column(
            controls=[
                self.progress_bar,
                self.question_container,
                ft.Container(content=self.feedback_text, alignment=ft.alignment.center_left),
                self.rating_panel,
            ],
            expand=True,
            spacing=20,
        )

        self.middle_area = ft.Container(
            content=self.question_display,
            expand=13,
            alignment=ft.alignment.center,
        )

        self.content_display = ft.Column(
            controls=[self.upper_area, self.middle_area],
            expand=True,
        )

        self.pageframe = ft.Container(
            content=self.content_display,
            expand=True,
            padding=10,
        )

        self.content = self.pageframe
        self.alignment = ft.alignment.center
        self.expand = True
        self.border_radius = 20

        if not self.queue:
            self.feedback_text.value = "All selected cards are up to date!"
            self.progress_bar.value = 1.0
            self.question_container.content = ft.Text(
                "Nothing to review right now.",
                size=30,
                weight=ft.FontWeight.BOLD,
            )
            self.rating_panel.visible = False
        else:
            self._load_next_card()

    def _create_rating_button(self, label, rating, color):
        return ft.Container(
            expand=True,
            padding=10,
            content=ft.ElevatedButton(
                text=label,
                on_click=lambda e, r=rating: self._handle_rating(r),
                style=ft.ButtonStyle(bgcolor={ft.ControlState.DEFAULT: color}),
            ),
        )

    def _load_next_card(self):
        if not self.queue:
            self.current_card = None
            self._update_progress(include_current=False)
            self.exit()
            return

        self.current_card = self.queue.pop(0)
        options = fsrs_scheduler.pick_options(self.cards, self.current_card)
        self.current_question = Question.MC_Question(
            options,
            self.current_card.to_option(),
            self.recieve_question_status,
        )
        self.question_container.content = self.current_question
        self.feedback_text.value = ""
        self.feedback_text.color = ft.Colors.BLACK
        self.rating_panel.visible = False
        self.awaiting_rating = False
        self.last_answer_correct = None
        self._update_progress(include_current=True)
        self.content.update()

    def recieve_question_status(self, status):
        if self.current_card is None:
            return
        self.last_answer_correct = status
        if status:
            self.feedback_text.value = "Correct!"
            self.feedback_text.color = ft.Colors.GREEN_700
        else:
            self.feedback_text.value = "Try again or choose a rating to schedule."
            self.feedback_text.color = ft.Colors.RED_600
        self.rating_panel.visible = True
        self.awaiting_rating = True
        self._update_progress(include_current=True)
        self.content.update()

    def _handle_rating(self, rating):
        if not self.awaiting_rating or self.current_card is None:
            return

        self.scheduler.review(self.current_card, rating)
        fsrs_scheduler.save_cards([self.current_card])
        self.completed_num += 1
        self.awaiting_rating = False
        self.rating_panel.visible = False
        self.feedback_text.value = ""
        self.feedback_text.color = ft.Colors.BLACK

        current_card = self.current_card
        self.current_card = None
        self.current_question = None

        self._refresh_queue()
        self._update_progress(include_current=False)

        if not self.queue:
            self.exit()
        else:
            self._load_next_card()

        # Ensure the reviewed card's latest state is retained in memory.
        for card in self.cards:
            if card.word == current_card.word and card.path == current_card.path:
                card.state = current_card.state
                break

    def _refresh_queue(self):
        self.queue = fsrs_scheduler.filter_due_cards(self.cards, now=self.scheduler.now())

    def _update_progress(self, include_current: bool):
        remaining = len(self.queue)
        if include_current and self.current_card is not None:
            remaining += 1
        total = self.completed_num + remaining
        if total == 0:
            self.progress_bar.value = 1.0
        else:
            self.progress_bar.value = self.completed_num / total

    def exit(self, e=None):
        fsrs_scheduler.save_cards(self.cards)
        if self.on_exit:
            self.on_exit("1")


def main(page: ft.Page):
    page.title = "FlashCardApp"
    page.window.width = 1100
    page.window.height = 780
    page.window.center()
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 30

    cards = [
        fsrs_scheduler.Card(word="alpha", definition="Definition A", example="Example sentence A", path=""),
        fsrs_scheduler.Card(word="beta", definition="Definition B", example="Example sentence B", path=""),
        fsrs_scheduler.Card(word="gamma", definition="Definition C", example="Example sentence C", path=""),
        fsrs_scheduler.Card(word="delta", definition="Definition D", example="Example sentence D", path=""),
    ]
    page.add(MC_Question_Set(cards))
    page.update()


if __name__ == "__main__":
    ft.app(target=main)