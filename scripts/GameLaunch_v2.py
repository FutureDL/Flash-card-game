import os
import sys
import multiprocessing as mp
import flet as ft
import scripts.ListWork_v3 as lw
import scripts.Game as Game  

# A Class for displaying Launcher
class GameLaunch(ft.Container):
    def __init__(self, vocab_list:list, on_exit = None):
        super().__init__()
        
        # The Basic attributes
        self.vocab_list = vocab_list
        self.Wrong_word_list = []
        self.Correct_num = 0
        self.Wrong_num = 0
        
        # Title of the game
        self.title = ft.Text("Stop the bomb from falling by entering the correct vocab word!", size=28, weight=ft.FontWeight.BOLD)
        
        # Description & instructions
        description = ft.Text("""
--In the game, there'll be a plane on top of the screen contineuouslly dropping bombs. Your goal is to eliminate these bombs before they passed through the bottom of the screen. 
--In the middle of the screen, there's a small textbox where you could enter words then send by pressing "Enter". On each of the bombs dropped, there's a short piece of chineese translation describing one of the vocabularies from the lists you selected. To eliminate the bombs, simply enter the vocabulary that they are discribing. (Spelling counts!)
--You have 15 points of health, each unmatched bomb decrease part of your health according to the difficulty you choose, each matched bomb regenerate one of your health.
--Each matched bomb gains you 'energy', when the energy bar is full, you can launch missles to harm the bomb-dropping plane.
--Game ends when your health bar is emptied, or the bomb dropping plane's health bar is emptied, or you matched all the bombs succesfully.
After you completed the game or closed the gaming window, a gaming performance report will be automatically generated. On the report, you'll see your accuracy in percentage on matching vocabularies with it's definition. You'll also see all the vocabularies that you had missed.                            
                                """, size=14, color=ft.Colors.GREY)

        self.description = ft.Container(
            content=description,
            expand = True,
            padding=20
        )
        
        # Selecting difficulty
        self.difficulty = ft.Dropdown(
            label="Difficulty (Affecting Enemy HP / Damage)",
            value="5",
            options=[ft.dropdown.Option(str(i)) for i in range(1, 11)],
            width=220,
        )

        # Text under the button for representing Status
        self.status = ft.Text("", size=12, color=ft.Colors.GREY)

        # The button for start game
        self.start_button = ft.ElevatedButton(
            "Start Game",
            icon=ft.Icons.SPORTS_ESPORTS,
            on_click=self.on_start_click,
            width=220,
            height = 50,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=14)),
        )
        
        self.upper_area = ft.Row(
            controls=[
                ft.Text("Launching Game: The Bomb Crisis     ", size = 40, weight=ft.FontWeight.BOLD),
                ft.Button("Exit", width=150, height = 50, on_click=on_exit)
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            expand=1
        )
        
        self.middle_area = ft.Container(
            content = ft.Column(
                [
                    self.title,
                    self.description,
                    ft.Divider(height=12, color=ft.Colors.with_opacity(0.0, ft.Colors.BLACK)),
                    self.difficulty,
                    self.start_button,
                    self.status,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            bgcolor = ft.Colors.GREY_200,
            padding=20,
            border_radius=20,
            expand=8
        )
        
        # Container for displaying game results, initially empty
        self.result_display = ft.Container(expand = True, padding=10)
        self.result_display.visible = False
        
        self.content_display = ft.Column(
            controls=[
                self.upper_area,
                self.middle_area,
                self.result_display
            ],
            expand=True,
        )
        
        self.content = self.content_display
        self.bgcolor = ft.Colors.GREY_50
        self.padding=20
        # self.alignment=ft.alignment.center
        self.expand = True
    
    # The function for displaying result after the game
    def display_result(self, missed:int, total:int, missed_vocabs:list):
        self.upper_area.visible = False
        self.middle_area.visible = False
        self.result_display.visible = True
        
        # Container for title
        title = ft.Container(
            content=ft.Text(value=f"Results",size = 60, weight=ft.FontWeight.BOLD),
            expand= 3,
            alignment=ft.alignment.center_left,
            bgcolor=ft.Colors.YELLOW_200,
            padding=5
        )
        
        # Container for number of missed vocabularies
        missed_num = ft.Container(
            content=ft.Text(value=f"Words Missed: {missed}",size = 30, weight=ft.FontWeight.BOLD),
            expand= 2,
            alignment=ft.alignment.center_left,
            bgcolor=ft.Colors.YELLOW_50,
            padding=5
        )
        
        # Container for total amount of vocabularies encountered
        total_num = ft.Container(
            content=ft.Text(value=f"Words encountered: {total}",size = 30, weight=ft.FontWeight.BOLD),
            expand= 2,
            alignment=ft.alignment.center_left,
            bgcolor=ft.Colors.YELLOW_50,
            padding=5
        )
        
        # The display container for the missed vocabularies
        display = ft.Container(
            content=ft.Column(
                controls=[],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            expand=8,
            alignment=ft.alignment.center_left,
            padding=5
        )
        
        # The button for returning to launch page
        restart_button = ft.Button(
            "Restart",
            height = 50,
            width= 225,
            on_click= self.display_launch,
            
        )
        
        # Add seperate word containers into the display
        for i in range(len(missed_vocabs)):
            vocab = missed_vocabs[i]
            index_i,index_j = get_index(self.vocab_list, vocab)
            
            word = ft.Container(
                content = ft.Column(
                    controls=[
                        ft.Text(value = f"{i+1}. {self.vocab_list[index_i][index_j][0]}", size = 20, weight=ft.FontWeight.BOLD),
                        ft.Text(value = f"{self.vocab_list[index_i][index_j][1]}", size = 15)
                    ],
                    expand=True,
                ),
                expand=True,
                alignment=ft.alignment.center_left
            )
            display.content.controls.append(word)
            
        self.result_display.content = ft.Column(
                controls=[
                    title,
                    missed_num,
                    total_num,
                    lw.labeled_divider("Missed Vocabularies"),
                    display,
                    restart_button
                ],
            expand=5,
        )
        self.result_display.expand = True
        
        self.content.update()
       
    # The function to navigate from the result page to the launch page       
    def display_launch(self, e):
        self.upper_area.visible = True
        self.middle_area.visible = True
        self.result_display.visible = False
        
        self.status.value = ""
        self.content.update()

    # The function of starting the game when start button is pressed
    def on_start_click(self, e):
        self.start_button.disabled = True
        self.status.value = "Starting Game Process..."
        self.content.update()

        # Use "spawn" to start
        try:
            mp.set_start_method("spawn")
        except RuntimeError:
            pass

        # Start an independent proces
        self.launcher_conn, game_conn = mp.Pipe()
        
        # Transform the vocabulary list into format required by the game
        vocab, definition = [],[]
        for j in self.vocab_list:
            current_vocab = [i[0] for i in j]
            current_definition = [i[1] for i in j]
            vocab.append(current_vocab)
            definition.append(current_definition)
            
        # Start an independent process to prevent game from conflicting with flet
        p = mp.Process(
            target=launch_Game1_1BT_from_flet,
            args=(int(self.difficulty.value),game_conn,vocab, definition),
            daemon=False,  # Let game manage it's life cycle by iteslf
        )
        p.start()

        # Change the status
        self.status.value = "Game is Launched (Independent Window)。\nYou can minimize this window now。"
        self.start_button.disabled = False
        self.content.update()
        
        # Wait for recieve the gaming result and displaying it
        result_data = self.launcher_conn.recv()
        total = result_data[0].pop()
        self.display_result(result_data[2], total, result_data[0])

# The function for launching game that functions in an independent process
def launch_Game1_1BT_from_flet(difficulty: int = 3, conn = None, vocab = [], definition = []):
    """
    在独立进程中启动 PyGame1_1BT 游戏，避免与 Flet 事件循环冲突。
    """
    # The name for the list
    selected_list = ["Flet 启动"]

    Game.main(selected_list, vocab, definition, int(difficulty), conn)
    
# Function for obtaining the index for a given vocab in a 2D vocab list
def get_index(lst:list, var) -> tuple[int,int]:
    index = 0
    for i in lst:
        index1 = 0
        for j in i:
            if j[0] == var:
                return index,index1
            index1 += 1
        index += 1
        
    return -1,-1

def main(page: ft.Page):
    import FileWork_v3 as fw
    page.title = "FlashCardApp"
    page.window.width = 1100
    page.window.height = 780
    
    page.window.center()
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 30

    page.add(GameLaunch([fw.readFromJson("others/json/question_test.json")]))

if __name__ == "__main__":
    ft.app(target=main)
    
