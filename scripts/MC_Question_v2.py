import flet as ft
import random

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
[3] The United States is ready to join a global effort on behalf of new jobs and sustainable growth."""],
    ["Jack","""[n.] 利益
1eid09wdjaowo20fhj490ds""","""[1] fiodfsjciojciojowef behalf of his wife, because she was barren.
[2] You will also learn about our cfdwicjdiojojoiqw prevent the dark Ones from destroying you and Mother Earth.
[3] The United copwpowopslkpaokemmcl effort on behalf of new jobs and sustainable growth."""]
]

class MC_Question(ft.Container):
    def __init__(self, option_data:list, correct_ans:list, on_button_click=None):
        super().__init__()
        self.option_data = option_data
        self.correct_ans = correct_ans
        self.status:bool = None
        self.on_button_click= on_button_click
        
        self.question_display = ft.Container(
            expand=4,
            padding = 30,
            alignment = ft.alignment.center_left
        )
        self.choice_display = ft.Container(
            expand=7,
            padding = 20
        )
        self.content_display = ft.Column(
            controls=[
                self.question_display,
                self.choice_display
            ],
            expand=True,
        )
        self.pageframe = ft.Container(
            content=self.content_display,
            expand=True
        )
        
        self.content = self.pageframe
        self.alignment = ft.alignment.center
        self.expand = True
        self.bgcolor = ft.Colors.BLUE_100
        self.border_radius = 20
        
        self.display_options()
        self.display_question()
        
    def display_options(self):
        self.choices = ft.Column(
            controls=[
                ft.Row(
                    expand=True,
                    spacing=10
                ),
                ft.Row(
                    expand=True,
                    spacing=10
                )
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO
        )
        make_random(self.option_data)
        for i in range(len(self.option_data)):
            data = self.option_data[i][1]
            text = ft.Text(
                value=data, 
                expand=True, 
                weight=ft.FontWeight.BOLD,
                size=15
            )
            option_container = ft.Container(
                content=text,
                expand=True,
                padding = 20,
                border_radius = 20,
                bgcolor=ft.Colors.BLUE_200,
                alignment=ft.alignment.center_left,
                data=i,
                height = 130,
                # scroll=ft.ScrollMode.AUTO,
                on_click=self.check_result
            )
            self.choices.controls[i//2].controls.append(option_container)   
        self.choice_display.content = self.choices
        
        # container1 = self.choices.controls[0].controls[0]
        # container2 = self.choices.controls[0].controls[1]
        # container1.height = container2.height if container1.height < container2.height else container2.height = container1.height
        
        # container1 = self.choices.controls[1].controls[0]
        # container2 = self.choices.controls[1].controls[1]
        # container1.height = container2.height if container1.height < container2.height else container2.height = container1.height
        ...
        
    def display_question(self):
        data = self.correct_ans[0]
        print(data)
        self.question_display.content = ft.Text(
            value=data, 
            expand=True,
            size=60, 
            weight=ft.FontWeight.BOLD,
        )
    
    def check_result(self,e):
        index = e.control.data
        if self.option_data[index] == self.correct_ans:
            print("Yes!")
            self.choices.controls[index//2].controls[index % 2].bgcolor = ft.Colors.GREEN_200
            self.status = True
        else: 
            print("No!")
            correct_index = self.option_data.index(self.correct_ans)
            self.choices.controls[correct_index//2].controls[correct_index % 2].bgcolor = ft.Colors.GREEN_100
            self.choices.controls[index//2].controls[index % 2].bgcolor = ft.Colors.RED_200
            self.status = False
        
        for i in self.choices.controls:
            i.disabled = True
            
        self.content.update()
        
        if self.on_button_click:
            self.on_button_click(self.status)
    
    def getStatus(self):
        return self.status
    
    def getData(self):
        return self.correct_ans


def make_random(arr:list):
    for i in range(len(arr)):
        temp = arr[i]
        index = random.randint(0,len(arr)-1)
        arr[i] = arr[index]
        arr[index] = temp
            
    
def main(page:ft.Page):
    page.add(MC_Question(vocab_list,vocab_list[1]))
    page.update()

if __name__ == "__main__":
    ft.app(target=main)

"""
1. Enabled scroll
2. Change the display of options
3. Added the correct notification after you got wrong
"""