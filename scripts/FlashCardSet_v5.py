import flet as ft
from typing import Callable, List, Optional, Sequence

import scripts.FlashCard_v2 as FlashCard
from scripts.card_state import CardState
from scripts import review_service


class FlashCardSet(ft.Container):
    completed: bool
    index: int

    def __init__(
        self,
        cards: Sequence[CardState],
        index: int = 1,
        completed: bool = False,
        learning: bool = False,
        on_grade: Optional[Callable[[CardState, str], None]] = None,
    ) -> None:
        super().__init__()

        self.card_states: List[CardState] = list(cards)
        if not self.card_states:
            raise ValueError("FlashCardSet requires at least one CardState instance")

        self.flashcards = [
            FlashCard.FlashCard(i + 1, card_state)
            for i, card_state in enumerate(self.card_states)
        ]

        self.index = max(0, min(len(self.flashcards) - 1, index - 1))
        self.current_card = self.flashcards[self.index]
        self.on_grade = on_grade

        self.completed = completed
        self.learning = learning

        self.left_button = ft.FloatingActionButton(
            icon=ft.Icons.ARROW_LEFT, on_click=self.Last_Card
        )
        self.right_button = ft.FloatingActionButton(
            icon=ft.Icons.ARROW_RIGHT, on_click=self.Next_Card
        )

        self.grade_buttons = ft.Row(
            controls=[
                ft.ElevatedButton("Again", on_click=lambda e: self._handle_grade("again")),
                ft.ElevatedButton("Hard", on_click=lambda e: self._handle_grade("hard")),
                ft.ElevatedButton("Good", on_click=lambda e: self._handle_grade("good")),
                ft.ElevatedButton("Easy", on_click=lambda e: self._handle_grade("easy")),
            ],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        )

        self.Display = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self.left_button,
                            ft.Container(content=self.current_card, expand=True),
                            self.right_button,
                        ],
                        expand=True,
                    ),
                    self.grade_buttons,
                ],
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor = ft.Colors.GREY_200,
            border_radius = 20,
            padding = 10,
            expand=True
        )
        self.expand = True
        self.content = self.Display
        
        self.bgcolor = ft.Colors.GREY_100
        self.border_radius = 20
        # self.padding = 10
        
    def Last_Card(self, e):
        new_index = self.index - 1
        if new_index >= 0:
            self.index = new_index
            self.current_card = self.flashcards[self.index]
            self.Display.content.controls[1].content = self.current_card
            self.Display.update()

    def Next_Card(self, e):
        new_index = self.index + 1
        if new_index < len(self.flashcards):
            self.index = new_index
            self.current_card = self.flashcards[self.index]
            self.Display.content.controls[1].content = self.current_card
            self.Display.update()
        else:
            self.completed = True
            
    def getStatus(self):
        if(self.getLength() == self.getIndex()):
            self.completed = True
        return self.completed

    def getLength(self):
        return len(self.flashcards)

    def getIndex(self):
        return self.index + 1

    def setIndex(self, index):
        self.index = max(0, min(len(self.flashcards) - 1, index - 1))
        self.current_card = self.flashcards[self.index]
        self.Display.content.controls[1].content = self.current_card
        self.Display.update()

    # ------------------------------------------------------------------
    # Accessors for FSRS scheduling attributes
    # ------------------------------------------------------------------
    def _resolve_state(self, index: Optional[int] = None) -> CardState:
        if index is None:
            index = self.index
        return self.card_states[index]

    def get_stability(self, index: Optional[int] = None) -> float:
        return self._resolve_state(index).stability

    def set_stability(self, value: float, index: Optional[int] = None) -> None:
        self._resolve_state(index).stability = value

    def get_difficulty(self, index: Optional[int] = None) -> float:
        return self._resolve_state(index).difficulty

    def set_difficulty(self, value: float, index: Optional[int] = None) -> None:
        self._resolve_state(index).difficulty = value

    def get_due(self, index: Optional[int] = None):
        return self._resolve_state(index).due

    def set_due(self, value, index: Optional[int] = None) -> None:
        self._resolve_state(index).due = value

    def get_last_review(self, index: Optional[int] = None):
        return self._resolve_state(index).last_review

    def set_last_review(self, value, index: Optional[int] = None) -> None:
        self._resolve_state(index).last_review = value

    def get_lapses(self, index: Optional[int] = None) -> int:
        return self._resolve_state(index).lapses

    def set_lapses(self, value: int, index: Optional[int] = None) -> None:
        self._resolve_state(index).lapses = value

    def get_repetitions(self, index: Optional[int] = None) -> int:
        return self._resolve_state(index).repetitions

    def set_repetitions(self, value: int, index: Optional[int] = None) -> None:
        self._resolve_state(index).repetitions = value

    def get_card_state(self, index: Optional[int] = None) -> CardState:
        return self._resolve_state(index)

    def _handle_grade(self, grade: str) -> None:
        card_state = self.get_card_state()
        if self.on_grade is not None:
            self.on_grade(card_state, grade)
        else:
            review_service.submit_grade_sync(card_state, grade)

def main(page: ft.Page):
    page.title = "Flashcards"
    page.window.width = 1000
    page.window.height = 600
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    sample_cards = [
        CardState.from_components(
            "whoever",
            """[pron.] 无论谁；…的那个人；…的任何人；不管什么人""",
            """[1] Claudia is right...""",
        ),
        CardState.from_components(
            "argue",
            """[v.] 争论；争辩；争吵；论证""",
            """[1] It seems useless for you to argue further with him.""",
        ),
    ]

    new_set = FlashCardSet(sample_cards, index=1, completed=False, learning=False)
    page.add(new_set)


if __name__ == "__main__":
    ft.app(target=main)