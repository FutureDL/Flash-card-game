import flet as ft
import scripts.FlashCardSet_v5 as CardSet
import time
import os
import scripts.ListWork_v3 as lw
import scripts.FileWork_v3 as fw
import scripts.MC_Question_Set_v3 as QuestionSet
import scripts.fsrs_scheduler as srs
import scripts.GameLaunch_v2 as GameLaunch

class MainPage(ft.Container):
    def __init__(self, page:ft.Page):
        super().__init__()
        # Title of the APP
        self.title = ft.Container(
            content=ft.Text(value="Select a list to start with...", size=60, weight=ft.FontWeight.BOLD),
            bgcolor=ft.Colors.AMBER_100,
            padding=10,
            border_radius=20,
            expand=True
        )
        
        self.page = page
        
        # To first initalize the area for displaying lists, so it can be used in the displayList() function
        self.list_area = ft.Column(controls=[])
        
        # Whether in a list
        self.listopen = False
        self.last_refresh = 0
        
        # Whether tickbox opened
        self.selectmode = False
        
        # Variables used when a list is opened:
        self.current_index = 0
        
        # Amount of lists already generated
        self.generated_num = 0
        
        
        # Button for adding list
        self.add_button = ft.FloatingActionButton(
            text="Add New List",
            icon=ft.Icons.ADD, 
            width=180, 
            height=100, 
            bgcolor=ft.Colors.ORANGE_300, 
            on_click = self.to_import_page
        )
        
        # Search bar
        self.search_bar = ft.TextField(
            hint_text="Enter the name of the list", 
            value="",
            label="Search for Vocab lists",
            on_change=self.searchList,
            min_lines=2, 
            max_lines=5
        )
        
        # Search result
        self.search_results = ft.Column(controls=[])
        
        # display the top area(greeting & add button)
        self.top_display = ft.Container(
            content=ft.Row(
                controls=[
                    self.title, 
                    self.add_button
                ],
                alignment=ft.MainAxisAlignment.CENTER
            ), 
            alignment=ft.alignment.top_center
        )
        
        # Create the area for displaying games(currently no function)
        self.game_area = ft.Container(
            expand=3,
            padding=20,
            bgcolor=ft.Colors.GREY_200,
            border_radius=20,
            content = ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text("Practice \nWith Question", size=30, weight=ft.FontWeight.BOLD,text_align=ft.TextAlign.CENTER),
                        expand=True,
                        border_radius=20,
                        bgcolor=ft.Colors.GREY_50,
                        alignment = ft.alignment.center,
                        on_click=self.start_practice
                    ),
                    ft.Container(
                        content=ft.Text("Start a \nGame", size=30, weight=ft.FontWeight.BOLD),
                        expand=True,
                        border_radius=20,
                        bgcolor=ft.Colors.GREY_50,
                        alignment = ft.alignment.center,
                        on_click=self.start_game
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                expand=True,
                spacing=20
            )
        )
        
        # Create the area for displaying vocabularies(initially with no lists)
        self.vocab_area = ft.Container(
            content=ft.Column(
                controls=[
                    self.search_bar,
                    lw.labeled_divider("Current Lists:"),
                ],
                expand=True,
            ),
            expand = 7,
            bgcolor=ft.Colors.GREY_100,
            padding= 20,
            border_radius= 20
        )
        
        # Creat the content area
        self.content_display = ft.Container(
            content=ft.Row(
                controls=[
                    # Left game area
                    self.game_area,
                    # Right vocab lists area
                    self.vocab_area
                ]
            ), 
            expand=True,
            alignment=ft.alignment.top_center
        )
        
        # Add the lists to the page
        current_directory = os.getcwd()# Get the current working directory
        print(f"Current directory: {current_directory}")

        # folder_path = os.path.join(current_directory,"res/Vocab List") # Find the vocabulary excel documents
        
        self.Vocab_lists = []
        self.Vocab_lists_info = []
        self.Vocab_List_Paths = fw.getFileName()
        
        # Add the Complete WordBook
        self.WordBookname = 'res/ListBook/WordBook.json'
        self.Vocab_List_Paths.insert(0,self.WordBookname)
        
        self.displayLists(self.Vocab_List_Paths)
        
        # Add the page for import (initially invisible)
        import_text = ft.Container(
            content=ft.Text(value="Add a list from...", size=60, weight=ft.FontWeight.BOLD),
            bgcolor=ft.Colors.AMBER_100,
            padding=10,
            border_radius=20
        )
        generate_button = ft.FloatingActionButton(text="Generate From existing Lists", expand=True, on_click=self.generate_from_list)
        import_button = ft.FloatingActionButton(text="Import list", expand=True)
        
        quit_button = ft.FloatingActionButton(text="Return to home", on_click=self.return_to_home, expand=True)
        
        self.import_page = ft.Container(
            content = ft.Column(
                controls=[
                    import_text,
                    ft.Row(controls=[generate_button]),
                    ft.Row(controls=[import_button]),
                    ft.Row(controls=[quit_button])
                ],
                alignment=ft.MainAxisAlignment.CENTER
            ), 
            expand= True,
            padding= 50,
            bgcolor=ft.Colors.ORANGE_100,
            visible = False
        )
        
        
        # the final display for the main page
        self.mainpage = ft.Column(
                controls=[
                    self.top_display,
                    self.content_display,
                    self.import_page
                ]
            )
        
        self.content = self.mainpage
        self.expand = True
        self.on_hover = self.refreshStatus
    
    # The functions for the buttons for the import page
    def to_import_page(self, e):
        self.import_page.visible = True
        self.top_display.visible = False
        self.content_display.visible = False
        self.mainpage.update()
        
    def return_to_home(self, e):
        self.import_page.visible = False
        self.top_display.visible = True
        self.content_display.visible = True
        self.mainpage.update()
    
    
    # Function for generating new lists from a previous list through the generate button
    # (Currently, it can only generate from the complete book list)
    # (In testing stage, the length is locked at 20, the number of lists generated is locked at 2)
    def generate_from_list(self,e):
        generate_num = 2
        generate_length = 20
        
        # Use the generate list function in the ListWork tool file
        # vocab_list = fw.readFromJson(self.Vocab_list_names[0])
        print(self.Vocab_lists[0])
        new_lists = lw.generateList(self.Vocab_lists[0],generate_num,generate_length)
        # Add the new lists into the list for Vocab lists.
        for i in range(len(new_lists)):
            self.generated_num += 1
            while(True):
                path = f"res/Vocab List/Generated_list_{self.generated_num}.json"
                if fw.checkExist(path):
                    self.generated_num += 1
                else:
                    self.Vocab_lists.append(new_lists[i])
                    fw.writeIntoJson(new_lists[i], path)
                    self.Vocab_List_Paths.append(path)
                    break
                
        self.displayLists(self.Vocab_List_Paths) #1 Originally self.displayList(self.Vocab_Lists)
        
        # Return to the home page
        self.import_page.visible = False
        self.top_display.visible = True
        self.content_display.visible = True
        self.mainpage.update()
        
    ## New:
    # The function for starting practice
    def start_practice(self, e):
        if self.selectmode == False:
            self.selectmode = True
            # Prevent from pressing start game at same time
            self.game_area.content.controls[1].disabled = True
            # Show the tickboxes
            for i in self.list_area.controls:
                i.content.controls[0].visible = True
                i.content.controls[2].disabled = True
            print("Selection mode enabled")
        else:
            # enable start game button
            self.game_area.content.controls[1].disabled = False
            
            # recieve the selected options
            selected_names = []
            selected_paths = []
            for index, item in enumerate(self.list_area.controls):
                if item.content.controls[0].value:
                    selected_names.append(item.content.controls[1].content.value)
                    if index < len(self.Vocab_List_Paths):
                        selected_paths.append(self.Vocab_List_Paths[index])
            print(selected_names)

            # hide the tickboxes
            self.selectmode = False
            for i in self.list_area.controls:
                i.content.controls[0].value = False
                i.content.controls[0].visible = False
                i.content.controls[2].disabled = False
            print("Selection mode disabled")

            # Start the practice if there's any list selected
            if selected_paths:
                cards = srs.load_cards(selected_paths)
                if not cards:
                    self._show_message("The selected lists do not contain any cards.")
                else:
                    due_cards = srs.filter_due_cards(cards)
                    if not due_cards:
                        self._show_message("No cards are due for review right now.")
                    else:
                        # hide the components in the main page
                        for i in self.mainpage.controls:
                            i.visible = False

                        # Show the the question page
                        self.mainpage.controls.append(
                            QuestionSet.MC_Question_Set(cards, on_exit=self.end_practice)
                        )

        self.content.update()
        ...

    # The function for ending practice
    def end_practice(self,msg):
        # remove the practice page
        self.mainpage.controls.pop()
        
        # Make the first page visable
        for i, component in enumerate(self.mainpage.controls):
            component.visible = True if i <= 1 else False
        self.content.update()
        print("Practice closed!")

    def _show_message(self, text: str):
        self.page.snack_bar = ft.SnackBar(ft.Text(text))
        self.page.snack_bar.open = True
        self.page.update()
    
    
    ## New:
    # Function for ending game
    def end_game(self, msg):
        self.mainpage.controls.pop()
        
        for i, component in enumerate(self.mainpage.controls):
            component.visible = True if i <= 1 else False
        self.content.update()
        print("Game Closed!")
    
    # Function for starting the game from the game button 
    def start_game(self, e):
        if self.selectmode == False:
            self.selectmode = True
            # Prevent from pressing start practice at same time
            self.game_area.content.controls[0].disabled = True
            # Show the tickboxes
            for i in self.list_area.controls:
                i.content.controls[0].visible = True
                i.content.controls[2].disabled = True
            print("Selection mode enabled")
        else:
            # enable start practice button
            self.game_area.content.controls[0].disabled = False
            
            # recieve the selected options
            selected = []
            for i in self.list_area.controls:
                if i.content.controls[0].value:
                    selected.append(i.content.controls[1].content.value)
            print(selected)
            
            # hide the tickboxes
            self.selectmode = False
            for i in self.list_area.controls:
                i.content.controls[0].value = False
                i.content.controls[0].visible = False
                i.content.controls[2].disabled = False
            print("Selection mode disabled")
            
            # Start the practice if there's any list selected
            if selected != []:
                # Add individual lists to the big list
                vocab_lists = []
                for i in selected:
                    if i == 'WordBook':
                        list = fw.readFromJson(f"res/ListBook/{i}.json")[0]
                    else:
                        list = fw.readFromJson(f"res/Vocab List/{i}.json")[0]
                    vocab_lists.append(list)
                
                # hide the components in the main page
                for i in self.mainpage.controls:
                    i.visible = False
                
                # Show the the question page
                self.mainpage.controls.append(GameLaunch.GameLaunch(vocab_lists, on_exit=self.end_practice))
            
        self.content.update()
        ...
        
    # Function for displaying the loaded lists in the vocab area
    def displayLists(self, Vocab_List_Names:list):
        self.Vocab_List_Paths = Vocab_List_Names
        if self.list_area in self.vocab_area.content.controls:
            self.vocab_area.content.controls.remove(self.list_area)

        self.list_area = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[],
            expand=True, 
            spacing=10  
        )
        
        self.Vocab_lists = []
        # Add the areas for lists
        for i in range(len(Vocab_List_Names)):
            # Obtain the vocabularies & information in each list
            vocab_list, info = fw.readFromJson(Vocab_List_Names[i])
            button_text = "Continue" if info[3] == True else "Start"
            button_text = "Review" if info[2] == True else button_text
            
            button_color = ft.Colors.YELLOW_100 if info[3] == True else ft.Colors.ORANGE_100
            button_color = ft.Colors.GREEN_100 if info[2] == True else button_color
            
            # Thee button to start studying the list
            button = ft.Container(content=ft.FloatingActionButton(
                text=f"{button_text}" if i != 0 else "Read", 
                data=i, 
                on_click=self.open_list, 
                bgcolor=button_color if i != 0 else ft.Colors.BLUE_200, 
                width= 100,
                height= 50
            ))
            
            # The text before container(the list name)
            name = info[0]
            list_name =  ft.Container(
                content=ft.Text(value=name, size=25),
                bgcolor=ft.Colors.BLUE_50 if i != 0 else ft.Colors.GREEN_200,
                padding=10,
                border_radius=20,
                expand=8 # takes up 8/10 of the length of the column
            )
            
            # The container area for each list
            list = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Checkbox(),
                        list_name,
                        button
                    ],
                ), 
            )
            list.content.controls[0].visible = False
            
            # Add the list to the display area
            self.list_area.controls.append(list)
            
            # Add the list content coresspondingly to the vocab list
            # Add the information of the list correspondingly
            self.Vocab_lists.append(vocab_list)
            self.Vocab_lists_info.append(info)
        
        # Add to the main content container
        self.vocab_area.content.controls.append(self.list_area)
    
    def searchList(self, e):
        # Clear the search result area
        self.search_results.controls.clear()
        
        # Transform request into lower case
        search_request = self.search_bar.value.lower()
        
        # If there is search request...
        if search_request:
            # CHange the divider's label
            self.vocab_area.content.controls[1]=lw.labeled_divider(f"Results of '{search_request}':")
            
            # Clear the vocab area
            self.vocab_area.content.controls.pop()
            results = []
            
            # Find which list's name match
            for i in self.list_area.controls:
                if search_request.lower() in i.content.controls[1].content.value.lower():
                    results.append(i)
            
            # Add the matched lists into search result   
            for i in results:
                self.search_results.controls.append(i)
            
            # Add search result into content display container
            self.vocab_area.content.controls.append(self.search_results)
        else: 
            # CHange the divider's label
            self.vocab_area.content.controls[1]=lw.labeled_divider("Current Lists: ")
            
            # Clear the vocab area
            self.vocab_area.content.controls.pop()
            
            # Add the original list area into the content display container
            self.vocab_area.content.controls.append(self.list_area)
        self.update()
    
    # Function for opening a list through the "start" button
    def open_list(self, e):
        self.listopen = True # Indicate that a list is opened
        self.mainpage.controls = []
        
        # Find the vocab list that needs to be displayed
        # if(e.control.data == 0):
        #     path = "res/ListBook"
        # else:
        #     path = "res/Vocab List"
            
        vocab_list, info = fw.readFromJson(self.Vocab_List_Paths[e.control.data])
        
        print(vocab_list)
        # self.Vocab_lists.append(vocab_list)
        print("yay")
        self.current_set = CardSet.FlashCardSet(vocab_list, info[1], info[2], info[3])
        self.current_set_name = self.Vocab_List_Paths[e.control.data]
        print("yay")
        self.mainpage.controls.append(self.current_set)
        
        # Add the control buttons
        self.list_control_buttons = ft.Row(
            controls=[
                ft.FloatingActionButton(text="Return to home", on_click=self.close_list, expand=True),
                ft.FloatingActionButton(text="Finish List", on_click=self.close_list, expand=True)
            ]
        )
        
        # Disable the finish button if list is not completed first
        if(self.current_set.getStatus() != True):
            self.list_control_buttons.controls[1].disabled = True
            
        # Change the attribute for learning
        fw.writeListInfo(self.current_set_name, learning=True)
            
        self.mainpage.controls.append(self.list_control_buttons)
        self.content.update()
    
    def refreshStatus(self,e):
        # Prevent too much refresh
        now = time.time()
        if now - self.last_refresh > 0.1:
            if(self.listopen == True): # Check the indication
                # Check if the user have reached the last page(以后会用文件记录数据，目前数据无法保存)
                if(self.current_set.getIndex() == self.current_set.getLength() or self.current_set.getStatus() == True):
                    # If yes enables the "finish" button
                    print(self.current_set.getIndex()," ", self.current_set.getLength())
                    self.list_control_buttons.controls[1].disabled = False
                    # Also alter the "Completed attribute" in flashcard set
                    fw.writeListInfo(self.current_set_name, completed=True)
                    
                else:
                    self.list_control_buttons.controls[1].disabled = True
                self.content.update()
            self.last_refresh = now
    
    # Closing the opened list
    def close_list(self,e):
        fw.writeListInfo(self.current_set_name, currentNum=self.current_set.getIndex())
        
        # Return to home page
        self.listopen == False
        self.mainpage.controls = []
        self.mainpage.controls.append(self.top_display)
        self.mainpage.controls.append(self.content_display)
        self.mainpage.controls.append(self.import_page)
        self.displayLists(self.Vocab_List_Paths)
        self.content.update()


def main(page: ft.Page):
    page.title = "FlashCardApp"
    page.window.width = 1100
    page.window.height = 780
    page.window.center()
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 30
    
    page.add(MainPage(page))

if __name__ == "__main__":
    ft.app(target=main)

# Adjusted the Code:

