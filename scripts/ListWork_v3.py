import sys # Better system controll
import pandas as pd #Excel processing
import os
import random
import flet as ft

# Get the vocab list according to the folder path provided

def getLists(folder_path):
    Excel_names = [i for i in os.listdir(folder_path) if i.endswith('.xlsx')]

    # Move the general word book 'Complete List.xlsx' to the first place of the list 
    if 'Complete List.xlsx' in Excel_names:
        Excel_names.remove('Complete List.xlsx')
        Excel_names.insert(0, 'Complete List.xlsx')

    # Build up file path
    VocabListsPath = [] # file path
    for i in range(len(Excel_names)): 
        file_path_current = os.path.join(folder_path, Excel_names[i]) # Construct the file paths
        if os.path.exists(file_path_current):
            print(f"File found: {file_path_current}")
            VocabListsPath.append(file_path_current)
        else:
            print(f"Vocab List file \"{Excel_names[i]}\" is missing") 
            sys.exit()

    # Read the Excel file
    try: 
        data = []
        for i in range(len(VocabListsPath)):
            data.append(pd.read_excel(VocabListsPath[i]))
    except KeyError:
        print("Please ensure all file imported is readable excel file!")

    print("Importing data...")
    
    Vocab_lists = []

    # Add all the data into vocab lists, and add it into the list of vocab lists
    for i in range(len(data)):
        list = []
        for j in range(len(data[i]['Vocab:'])):
            if pd.isna(data[i].at[j, 'Vocab:']) == False: # Check if the cell is empty 
                card = [data[i]['Vocab:'][j],data[i]['Translation:'][j],data[i]['Example sentence:'][j]]
                list.append(card)
            else:
                break
        Vocab_lists.append(list)
    
    # Check if there's empty lists, and add sth into it if there is to prevent causing error later
    for i in range(len(Vocab_lists)):
        if is_list_empty(Vocab_lists[i]) == True:
            card = ["This vocab list is empty","N/A","N/A"]
            Vocab_lists[i].append(card)
    
    # # Return the list of vocab lists
    # return Vocab_lists

# Generate a vocab list from a previous list
def generateList(pre_list:list, list_num:int, list_length:int):
    
    print("Generating lists...")
    lists = []
    # Generate for "list num" times
    for _ in range(list_num):
        list = []
        # For each time generate "list_length" words
        for _ in range(list_length):
            while True:
                # Choose from the selected "pre_list"
                vocab = random.choice(pre_list)
                if vocab not in list:
                    list.append(vocab)
                    break
        lists.append(list)
    
    # Return the list of newly generated lists
    return lists

# Check if a list is empty
def is_list_empty(lst):
    return not lst  

# The function to add a divider with label
def labeled_divider(label: str):
        divider = ft.Row(
            controls=[
                ft.Text(label, size=16, color="grey", weight=ft.FontWeight.BOLD),
                ft.Container(content=ft.Divider(height=1, color="grey"),expand=True),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        return divider
    
"""
Stopped directly returning vocab list after reading files. Instead, the application will read from json.
"""