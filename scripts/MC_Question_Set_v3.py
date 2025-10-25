import flet as ft
import random
import scripts.MC_Question_v2 as Question
import time
import sys

class MC_Question_Set(ft.Container):
    def __init__(self,vocab_list,on_exit = None):
        super().__init__()
        self.vocab_list = vocab_list
        self.on_exit = on_exit
        
        self.total_num = len(vocab_list)
        self.completed_num = 0
        
        make_random(self.vocab_list)
        
        self.question_list = []
        
        self.next_button = ft.FloatingActionButton(
            text="Next",
            on_click=self.next,
            width= 100
        )
        self.next_button.visible = False
        
        self.title = ft.Text(
            value="Practice: Questions                      ",
            size=35, 
            weight=ft.FontWeight.BOLD,
        )
        
        self.progress_bar = ft.ProgressBar(value=0, height=10,border_radius=5)
        
        self.exit_button = ft.FloatingActionButton(
            text="Exit",
            on_click=self.exit,
            width=100
        )
        
        self.upper_area = ft.Container(
            expand=2,
            padding=20,
            border_radius=20,
            alignment = ft.alignment.center,
            bgcolor=ft.Colors.AMBER_100,
            content = ft.Row(
                controls=[
                    self.title,
                    self.exit_button
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                expand=True,
                height = 100
            )
        )
        
        self.question_display = ft.Column(
            controls=[]
        )
        
        self.middle_area = ft.Container(
            content=self.question_display,
            expand=13,
            alignment = ft.alignment.center
        )
        
        self.content_display = ft.Column(
            controls=[
                self.upper_area,
                self.middle_area,
            ],
            expand=True
        )
        self.pageframe = ft.Container(
            content=self.content_display,
            expand=True,
            padding= 10
        )
        
        self.content = self.pageframe
        self.alignment = ft.alignment.center
        self.expand = True
        # self.bgcolor = ft.Colors.BLUE_100
        self.border_radius = 20
        
        self.init_questions()
        self.display_question()
        
    def init_questions(self):
        for i in self.vocab_list:
            option_data = get_random_choices(self.vocab_list, i)
            self.question_list.append(Question.MC_Question(option_data, i, self.recieve_question_status))
    
    def display_question(self):
        self.question_display.controls = []
        self.question_display.controls.append(self.progress_bar)
        self.question_display.controls.append(self.question_list[0])
        self.question_display.controls.append(
            ft.Container(
                content = self.next_button, 
                height = 50,
                alignment = ft.alignment.center_right,
            )
        )
        
    def add_question(self, lst:list):
        for i in lst:
            option_data = get_random_choices(self.vocab_list, i)
            self.question_list.append(Question.MC_Question(option_data, i, self.recieve_question_status))
        
    def recieve_question_status(self, status):
        if status == True:
            time.sleep(1)
            self.completed_num += 1
            self.next_question()
        else:
            data = self.question_list[0].getData()
            self.add_question([data])
            self.next_button.visible = True
            self.completed_num += 1
            self.total_num += 1
            self.content.update()
        
    def next(self, e):
        self.next_button.visible = False
        self.next_question()
        
    def next_question(self):
        self.update_progress()
        # Check if the last question is reached
        if len(self.question_list) == 1:
            time.sleep(1)
            self.exit()
        else:
            self.question_list.pop(0)
            self.display_question()
            self.content.update()
        
    def update_progress(self):
        self.progress_bar.value = self.completed_num/self.total_num
        self.content.update()  

    def exit(self, e = None):
        print("Practic exit!")
        self.on_exit("1")
        
  
def get_random_choices(lst:list, element:int):
    import copy
    newLst = copy.deepcopy(lst)
    newLst.remove(element)
    for i in range(len(newLst)):
        temp = newLst[i]
        index = random.randint(0,len(newLst)-1)
        newLst[i] = newLst[index]
        newLst[index] = temp
    newLst.insert(random.randint(0,3),element)
    return newLst[:4]  

def make_random(arr:list):
    for i in range(len(arr)):
        temp = arr[i]
        index = random.randint(0,len(arr)-1)
        arr[i] = arr[index]
        arr[index] = temp
        


def main(page:ft.Page):
    page.title = "FlashCardApp"
    page.window.width = 1100
    page.window.height = 780
    page.window.center()
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 30
    
    import FileWork_v3 as fw
    vocab_list = fw.readFromJson("others/json/question_test.json")
    page.add(MC_Question_Set(vocab_list[:5]))
    page.update()

if __name__ == "__main__":
    ft.app(target=main)
    
"""
1. Recieve the function from the app.
2. Organized the function "next question".
3. Updated the functions. Added ways of handling when all the questions are finished.
"""