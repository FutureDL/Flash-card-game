import flet as ft
import scripts.FlashCard_v2 as FlashCard
import scripts.FileWork_v3 as fw

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
    completed:bool
    index:int
    
    def __init__(self, vocab_list, index, completed, learning):
        super().__init__()
        self.flashcards = []
        for i in range(len(vocab_list)):
            vocab = FlashCard.FlashCard(i+1, vocab_list[i][0], vocab_list[i][1], vocab_list[i][2])
            self.flashcards.append(vocab)
        
        self.index = index - 1
        self.current_card = self.flashcards[self.index]
        
        self.completed = completed
        self.learning = learning
        
        self.left_button = ft.FloatingActionButton(icon=ft.Icons.ARROW_LEFT, on_click= self.Last_Card)
        self.right_button = ft.FloatingActionButton(icon=ft.Icons.ARROW_RIGHT, on_click= self.Next_Card)
        
        self.Display = ft.Container(
            content=ft.Row(
                controls=[
                    self.left_button,
                    ft.Container(content = self.current_card,expand=True),
                    self.right_button
                ],expand=True
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
        try:
            self.current_card = self.flashcards[self.index - 1]
            self.index -= 1
            self.Display.content.controls[1].content = self.current_card
            self.Display.update()
        except IndexError:
            pass
        
    def Next_Card(self, e):
        try:
            self.current_card = self.flashcards[self.index + 1]
            self.index += 1
            self.Display.content.controls[1].content = self.current_card
            self.Display.update()
        except IndexError:
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
        self.index = index - 1

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