import flet as ft
import scripts.FlashCardApp_v13 as MainPage


def main(page: ft.Page):
    page.title = "FlashCardApp"
    page.window.width = 1100
    page.window.height = 780
    page.window.center()
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 30
    
    page.add(MainPage.MainPage(page))

if __name__ == "__main__":
    ft.app(target=main)