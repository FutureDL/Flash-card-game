import json
import sys # Better system controll
import pandas as pd #Excel processing
import os

from scripts import Scheduler_v1 as scheduler

current_directory = os.getcwd()# Get the current working directory
print(f"Current directory: {current_directory}")

def importFromExcel(path):
    folder_path = os.path.join(current_directory, "YourLists") # Find the vocabulary excel documents
    Excel_names = [i for i in os.listdir(folder_path) if i.endswith('.xlsx')]

    # Move the general word book 'Complete List.xlsx' to the first place of the list 
    # if 'Complete List.xlsx' in Excel_names:
    #     Excel_names.remove('Complete List.xlsx')
    #     Excel_names.insert(0, 'Complete List.xlsx')

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
    
    # Add the vocab lists
    for i in range(len(Vocab_lists)):
        writeIntoJson(Vocab_lists[i], f"res/Vocab List/{Excel_names[i]}.json")
        print("name:",Excel_names[i])
    
    return Excel_names


def is_list_empty(lst):
    return not lst  

def writeIntoJson(vocab_list:list, path:str):
    if checkExist(path) == False:
        vocab = {}
        for i in vocab_list:
            if len(i) >= 4 and isinstance(i[3], scheduler.CardState):
                state_dict = i[3].to_dict()
            else:
                state_dict = scheduler.default_card_state().to_dict()
            vocab[i[0]] = {
                "definition:":i[1],
                "example:":i[2],
                "fsrs_state": state_dict,
            }
            
        list = path.split("/") 
        vocab["XXX"] = {
            "Name":os.path.splitext(list[len(list)-1])[0],
            "CurrentNum":1,
            "Completed":False,
            "Learning":False,
        }
        
        # with open(f"others/json/test1.json", "w") as f:
        #     json.dump(vocab, f, indent=4)
                
        with open(path, "w",encoding='utf-8') as f:
            json.dump(vocab, f, indent=4)

def readFromJson(path):
    if checkExist(path):
        listInfo = None
        with open(path, "r", encoding='utf-8') as f:
            loaded_vocab = json.load(f)

        # Print nicely
        vocab_list = []
        dirty = False
        for word, info in loaded_vocab.items():
            if word != "XXX":
                state = scheduler.card_state_from_dict(info.get('fsrs_state'))
                if 'fsrs_state' not in info:
                    info['fsrs_state'] = state.to_dict()
                    dirty = True
                vocab = [word, info['definition:'], info['example:'], state]
                vocab_list.append(vocab)
            else:
                listInfo = [info['Name'], info['CurrentNum'], info['Completed'], info['Learning']]
        if dirty:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(loaded_vocab, f, indent=4)
        if listInfo == None:
            return vocab_list
        else:
            return vocab_list, listInfo
    
def getListInfo(path):
    if checkExist(path):
        return readFromJson(path)[1]
    
def writeListInfo(path, name:str = None, currentNum:int = None, completed:bool = None, learning:bool = None):
    with open(path, 'r+', encoding='utf-8') as f:
        data = json.load(f)
        data["XXX"]['Name'] = name if name != None else data["XXX"]['Name']
        data["XXX"]['CurrentNum'] = currentNum if currentNum != None else data["XXX"]['CurrentNum']
        data["XXX"]['Completed'] = completed if completed != None else data["XXX"]['Completed']
        data["XXX"]['Learning'] = learning if learning != None else data["XXX"]['Learning']
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()


def writeCardState(path: str, vocab: str, state: scheduler.CardState):
    with open(path, 'r+', encoding='utf-8') as f:
        data = json.load(f)
        if vocab not in data:
            raise KeyError(f"'{vocab}' not found in {path}")
        data[vocab]['fsrs_state'] = state.to_dict()
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
        
def checkExist(path) -> bool:
    filepath = path
    if os.path.exists(filepath):
        print("File exists")
        return True
    else:
        print("File does not exist ")
        return False

def getFileName():
    # Get all file and folder names
    folder_path = "res/Vocab List" # Find the vocabulary excel documents
    
    # Filter to include only files
    # files = [f for f in all_items if os.path.isfile(os.path.join(folder_path, f))]
    
    files = [
        os.path.join(folder_path, f)  # take only the name, not the extension
        for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f))
    ]
    
    # if 'Complete List.xlsx' in files:
    #     files.remove('Complete List.xlsx')
    #     files.insert(0, 'Complete List.xlsx')
    if 'res/Vocab List/.DS_Store' in files:
        files.remove('res/Vocab List/.DS_Store')
    return files

importFromExcel("YourLists")
# writeListInfo("others/json/","testList")


# vocab_list = [
#     ["whoever","""[pron.] 无论谁；…的那个人（或那些人）；…的任何人；不管什么人
# [网络] 爱谁谁；究竟是谁；无论是谁""",""" [1] Claudia is right, I mean two days ago you were fighting with her and telling whoever wanted to listen that you were happy with Minmei.
# [2] Whoever curses his father or his mother, his lamp shall be put out in deep darkness.
# [3] We were in front of a bar and he ducked slightly, peering in, but whoever he was looking for did not seem to be there."""],
#     ["argue","""[v.] 争论；争辩；争吵；论证
# [网络] 辩论；说服；主张""","""[1] it seems useless for you to argue further with him.
# [2] While gold supply is well understood, silver bulls and bears argue about just how much silver is out there.
# [3] Sullivan sighed, but he did not argue. ""I think I'll miss you, Jonathan, "" was all he said."""],
#     ["behalf","""[n.] 利益
# [网络] 方面；支持；维护""","""[1] Isaac prayed to the Lord on behalf of his wife, because she was barren.
# [2] You will also learn about our many operations on your behalf, to prevent the dark Ones from destroying you and Mother Earth.
# [3] The United States is ready to join a global effort on behalf of new jobs and sustainable growth."""]]


# writeIntoJson(vocab_list, "others/json/hahha.json")
# print(readFromJson("others/json/hahha.json"))
# print(getListInfo("others/json/hahha.json"))

# writeListInfo("others/json/hahha.json", "jack", 3,False)
print(getFileName())




# Stored basic list data in json file
# Added list info at line 102. [name(str), CurrentNum(int), Completed(bool), Learning(bool)]