import pygame
import pygame.font
import random
import sys
import os
from multiprocessing import Process, Pipe
import flet as ft

global_wrong_word_list = []
global_correct_num = 0
global_wrong_num = 0

# Main game loop
def main(launch_selected_list, launch_vocab, launch_defenition, difficulty, conn):
     
    # Initialize Pygame
    pygame.init()

    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    GREEN = (0, 255, 0)
    GREY = (200,200,200)

    # Create the screen
    screen = pygame.display.set_mode()
    pygame.display.set_caption("Vocab Helping Game -- Game")

    # Screen dimensions
    SCREEN_WIDTH = screen.get_width()
    SCREEN_HEIGHT = screen.get_height()

    #load the images
    current_directory = os.getcwd() # Get the current working directory
    print(f"Current directory: {current_directory}")

    # Import the image files
    file_names = ['Space Ship.png','Bomb.png','missile.png','Explode1.png','Explode2.png','Explode.png','Black sky.png', "Controller.png"] 
    planes = []
    for i in range(len(file_names)): 
        file_path = os.path.join(current_directory, "res/Images", file_names[i]) # Construct the file paths
        if os.path.exists(file_path):
            print(f"File found: {file_path}")
            file_names[i] = pygame.image.load(file_path)
            planes.append(file_names[i])
        else:
            print(f"Image file \"{file_names[i]}\" is missing")
            pygame.quit()
            sys.exit()
    Background = pygame.transform.scale(file_names[len(file_names)-2],(SCREEN_WIDTH,SCREEN_HEIGHT))
    controll = pygame.transform.scale(file_names[len(file_names)-1],(SCREEN_WIDTH-40,SCREEN_HEIGHT//4))

    # planes.pop(len(planes)-1) # Not to include the background
    # planes.pop(len(planes)-2)

    file_path_current = os.path.join(current_directory,"res/font/HYXingHeJianDui45U.ttf")
    if os.path.exists(file_path_current):
        print(f"File found: {file_path_current}")
    else:
        print(f"Font file \"{file_names[i]}\" is missing")
        pygame.quit()
        sys.exit()
        
    Audio_names = ['res/Audio/bgm.mp3','res/Audio/BombMissed.mp3','res/Audio/EnemyShipExplode.mp3', 'res/Audio/MissileHit.mp3', 'res/Audio/MissileLaunch.mp3', 'res/Audio/Success.mp3', 'res/Audio/win.mp3', 'res/Audio/lose.mp3'] # name of excel documsnets
    Audio_Path = [] # file path
    for i in range(len(Audio_names)): 
        Audio_Path_current = os.path.join(current_directory, Audio_names[i]) # Construct the file paths
        if os.path.exists(Audio_Path_current):
            print(f"File found: {Audio_Path_current}")
            Audio_Path.append(Audio_Path_current)
        else:
            print(f"Vocab Audio file \"{Audio_names[i]}\" is missing") 
            pygame.quit()
            sys.exit()
        
    # Load the Audio
    bgm = pygame.mixer.Sound(Audio_names[0])
    BombMissed = pygame.mixer.Sound(Audio_names[1])
    EnemyShipExplode = pygame.mixer.Sound(Audio_names[2])
    MissileHit = pygame.mixer.Sound(Audio_names[3])
    MissileLaunch = pygame.mixer.Sound(Audio_names[4])   
    success = pygame.mixer.Sound(Audio_names[5])
    win = pygame.mixer.Sound(Audio_names[6])
    lose = pygame.mixer.Sound(Audio_names[7])

    #text box attributes
    font = pygame.font.Font(None, 40)
    input_box = pygame.Rect(300, 250, 200, 50)
    color_inactive = pygame.Color('black')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = False
    text = ''  # Text inside the box

    # Tutorial text attributes (Will be deleted)
    # Tfont = pygame.font.Font(None, 25)
    # def display_multiline_text(screen, text, x, y, line_height, font, color):
    #     """Displays multi-line text on the screen."""
    #     lines = text.splitlines()  # Split the text into lines
    #     for i, line in enumerate(lines):
    #         # Render each line of text
    #         text_surface = font.render(line, True, (200,200,250))
    #         # Position the line on the screen
    #         screen.blit(text_surface, (x, y + i * line_height))
    # Ttext = (
    #     "Instructions:            \n"
    #     "Enter the vocab that matches the definition on \n"
    #     "each bomb to stop it from falling down! "
    # )

    def linechange(text):
        original_string = text
        for i in range(len(text)):
            if i % 5 == 0 and i != 0:
                part1 = original_string[:i]
                part2 = original_string[i:] 
                original_string = part1 + "\n" + part2
        new_string = original_string
        return new_string

    # Clock for controlling frame rate
    clock = pygame.time.Clock()

    # List to store all characters
    characters = []
    bomb = []
    missile = []

    # Special attributes
    Reverse = 0 # Will be deleted
    tick = 0
    Char = 0
    listnum = 0
    damage = 0
    energy = 0
    winning = False

    # Class enemy aircraft
    class EnemyCraft:
        # Initiallizing data
        def __init__(self, x, y, w, h, difficulty, VocabList, Meaning, position):
            # Basic coordinates & size
            self.x = x
            self.y = y
            self.w = w
            self.h = h
            
            # Attributes
            self.type = planes[0] # Currently only the space craft will sever as the apperience of enemy plane
            self.dx = 20 # Random horizontal speed
            self.tick = 0 # A special attribute to measure the time that the aircraft appears
            self.num = 0 # The number of bombs that the plane had thrown
            self.bombing = False # The enemy plane is not bombing at first
            self.difficulty = difficulty # difficulty
            self.position = position # It's position in the list
            
            # Creating it's own list
            self.list1 = VocabList 
            self.list2 = Meaning
            self.vocabsituation = [1 for i in range(1,len(self.list1)+1)]
        
        # Movements of the enemy plane  
        def move(self):
            # enemy Plane entering
            if self.x <= 100:  
                if self.dx > 1 and self.tick % 9 == 0: # Slow down the clock tick
                    self.dx -= 1
                if Reverse == 1: 
                    self.x -= self.dx
                else:
                    self.x += self.dx
            # enemy Plane leaving     
            elif self.x >= 200: 
                self.bombing = False
                if tick % 5 == 0: # Slow down the clock tick
                    self.dx += 1
                if Reverse == 1: 
                    self.x -= self.dx
                else:
                    self.x += self.dx
            # enemy Plane staying & bombing vocabs     
            else:
                # if self.tick <= 2000*self.difficulty and self.tick >= 300:
                #     self.bombing = True
                # else:
                #     self.bombing = False
                if self.tick >= 600 and self.bombing == False: 
                    if Reverse == 1:
                        self.x -= self.dx
                    else:
                        self.x += self.dx
                else:
                    self.bombing = True
            self.tick += 1 # indipendently count ticks
        
        # Draw the apperance of the enemy plane on the window    
        def draw(self):
            font = pygame.font.Font(None, 200)
            Char = pygame.transform.scale(self.type, (self.w, self.h)) # Draw a character with a random scale
            if Reverse == 1:
                char1 = pygame.transform.flip(Char, True, False) #flip the character if Reversed
                screen.blit(char1,(self.x,self.y))
            else:
                screen.blit(Char,(self.x,self.y))
            if self.bombing == False and self.tick <= 180 and self.x > -1000:
                text = "Game Starts!"
                text_surface = font.render(text, True, GREEN)
                screen.blit(text_surface, (SCREEN_WIDTH//2 - 430, SCREEN_HEIGHT//2 - 70))
            elif self.bombing == False and self.x > 0:
                if winning == True:
                    text = "Game Ends!"
                    text_surface = font.render(text, True, GREEN)
                    screen.blit(text_surface, (SCREEN_WIDTH//2 - 430, SCREEN_HEIGHT//2 - 70))
                else:
                    text = "Game Over!"
                    text_surface = font.render(text, True, RED)
                    screen.blit(text_surface, (SCREEN_WIDTH//2 - 430, SCREEN_HEIGHT//2 - 70))
    
    # Make the attributes accessible     
        def xx(self):
            return self.x
        
        def yy(self): 
            return self.y
        
        def addnum(self):
            self.num += 1
            
        def selfnum(self):
            return self.num
        
        def isbombing(self):
            return self.bombing
        
        def stopbombing(self):
            self.bombing = False
        
        def bombrate(self):
            return 240/self.difficulty
        
        def list(self):
            return self.list1
        
        def meaninglist(self):
            return self.list2
        
        def situationlist(self):
            return self.vocabsituation
        
    # Class enemy bomb       
    class Bomb:
        # Initiallizing data
        def __init__(self, enemy, vocab, definition):  
            # Basic coordinates & size
            self.w = 270
            self.h = 450
            if isinstance(enemy, EnemyCraft):
                self.x = random.randint(enemy.x + 100, enemy.x + enemy.w - 300) # Ensure the bomb only appear at the bottom of the plane
                self.y = enemy.y
            else:
                raise TypeError("The argument must be an instance of EnemyCraft")
            
            # Attributes
            self.explode = pygame.transform.scale(file_names[len(file_names)-3],(self.h,self.h))
            self.type = planes[1] # The misile image
            self.dy = 1 # Random vertical speed  
            self.hit = False # If the bomb being hit(if the vocab is being matched correctly, currently false)
            self.vocab = vocab
            self.definition = definition # The def this bomb represents
            self.tick = 0
        
        # Movements of the enemy plane      
        def move(self):
            if self.hit == False: # Only move if the vocab is not matched
                self.y += self.dy   
        # Draw the bomb on the game window
        def draw(self):
            font = pygame.font.Font(file_path_current, 15) # Enables CHineese Display
            text = self.definition
            text_surface = font.render(text, True, BLACK)
            if self.hit == False: # Only move if the vocab is not matched
                Char = pygame.transform.scale(self.type, (self.w, self.h))
                screen.blit(Char,(self.x,self.y))
                for i in range(len(text)): # Enables multi-line display
                    if i % 9 == 0 and i != 0:
                        line = text[i-9:i]
                        text_surface = font.render(line, True, BLACK)
                        screen.blit(text_surface, (self.x + 65, self.y + (180) + i*2))
                    elif i == len(text)-1 and i % 9 != 0:
                        line = text[i-(i%9):]
                        text_surface = font.render(line, True, BLACK)
                        screen.blit(text_surface, (self.x + 65 , self.y + (180) + ((i//9)+1)*18))
                # screen.blit(text_surface, (self.x - (text_surface.get_width())//2 , self.y + (200)))
            else:
                self.dy = 0
                if self.tick <= 20:
                    screen.blit(self.explode,(self.x - (self.h-self.w)//2,self.y))
                self.tick += 1
                
        # Make the attributes accessible
        def hitting(self): 
            self.hit = True
            print(f'{self.definition}is being hit!')
            
        def ifhit(self):
            return self.hit
        
        def selfdefinition(self):
            return self.definition
        
        def selfvocab(self):
            return self.vocab   
        
        def xx(self):
            return self.x
        
        def yy(self): 
            return self.y
    class Missile:
        def __init__(self):
            self.x = random.randint(200, SCREEN_WIDTH-500)
            self.y = SCREEN_HEIGHT
            print(self.y)
            
            self.w = 270
            self.h = 450
            self.type = planes[2]
            self.explode = planes[4]
            self.dy = -5
            # self.hitting = False
            self.tick1 = 0
            self.tick = 0
            
        def move(self):
            if self.y >= 0:
                self.y += self.dy
            else:
                self.tick += 1
            if self.dy >= -20 and self.tick1 % 10 == 0:
                self.dy -= 1
            self.tick1 += 1
                
        def draw(self):
            if self.y >= 0:
                # Char = pygame.transform.scale(self.type, (self.w, self.h))
                
                screen.blit(self.type,(self.x,self.y))
            else:
                if self.tick <= 30:
                    # Char = pygame.transform.scale(self.explode, (self.w, self.h))
                    screen.blit(self.explode,(self.x,self.y))
        
        def yy(self):
            return self.y
        
        # def hit(self):
        #     self.hitting = True

             
    global_word_num = 0 
    


    music = 0
        
    
    # Enables muilti list input
    print(f"Launched game from{launch_selected_list}") 
    print(launch_vocab)
    print(launch_defenition)
    Difficulty = int(difficulty)
    enemy_health = 10*difficulty
    e_health = 10*difficulty
    
    
    # Make all the variables created before a global variable
    global Tfont, Ttext, global_wrong_word_list, global_correct_num, global_wrong_num
    running = True
    
    # Create Sound Channels
    channel1 = pygame.mixer.Channel(0)
    channel2 = pygame.mixer.Channel(1)
    channel3 = pygame.mixer.Channel(2) 
    channel4 = pygame.mixer.Channel(3)
    Bgm = pygame.mixer.Channel(4)
    Win = pygame.mixer.Channel(5)
    Lose = pygame.mixer.Channel(6)
    Success = pygame.mixer.Channel(7)
    
    # list for missed vocabs
    Wrong_word_list = []
    
    # Count for correst / wrong word
    correct_num = 0
    wrong_num = 0
    
    # The main gain loop
    while running:
        # Play the BGM
        if not Bgm.get_busy():
            Bgm.play(bgm)
        
        # Create the EnemyCraft    
        if tick % 60 == 0 and Char < len(launch_vocab):
            y = -150 + Char * 20
            w = 1300
            h = 500
            d = 1 # The difficulty was set to 1
            if Reverse == 0: 
                x = -1500
            else:
                x = SCREEN_WIDTH+160-w
                    
            characters.append(EnemyCraft(x, y, w, h, d, launch_vocab[Char], launch_defenition[Char], Char)) # Add a new character
            bomb.append([]) # Create a list to contain the bombs(vocab) for this plane character(the vocab list)
            # a = random.choice(characters[Char].meaninglist())
            # bomb[Char].append(Bomb(characters[Char], characters[Char].list()[characters[Char].meaninglist().index(a)], a)) # first add a bomb, or else the code will crash
            Char += 1 # The number of characters plus one after creating.
        
        # Moving Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # elif event.type == pygame.KEYDOWN:
            #     if event.key == pygame.K_m and active == False:  # "m" key to add a new character
            #         # The coordinaye, width, and height of the charactor
            #         y = -150
            #         w = 1300
            #         h = 500
            #         d = 2 # The difficulty was set to 1
            #         if Reverse == 0: 
            #             x = -1500
            #         else:
            #             x = SCREEN_WIDTH+160-w
                        
            #         characters.append(EnemyCraft(x, y, w, h, d, Vocab, Meaning)) # Add a new character
            #         bomb.append([]) # Create a list to contain the bombs(vocab) for this plane character(the vocab list)
            #         Char += 1 # The number of characters plus one after creating.
            #         bomb[Char-1].append(Bomb(characters[Char-1], random.choice(Vocab))) # first add a bomb, or else the code will crash
                    
            # Textbox event handling                      
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos): # Toggle the active state of the text box
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
                if Launch_button.collidepoint(event.pos) and Launch_active == True:
                    energy = 0
                    finish = False
                    # Launch the missiles
                    for i in range(5):
                        missile.append(Missile())
                        # Play the audio
                        channel1.play(MissileLaunch)   
            if event.type == pygame.KEYDOWN and active:
                if event.key == pygame.K_RETURN:  # Type in word on Enter
                    print(f"Player Input: {text}")
                    
                    # Check if the vocab entered match the definition
                    for i in range(Char):
                        if text in characters[i].list(): 
                            print('yes1') # The vocab is in the list imported
                            print(characters[i].situationlist())
                            if characters[i].situationlist()[characters[i].list().index(text)] == 2:
                                print('yes2') # The vocab is valid(is being drawn on the screen)
                                for j in range(len(bomb[i])):
                                    if bomb[i][j].selfvocab() == text:
                                        print('yes3') # The vocab is being matched by player input
                                        if energy < 5:
                                            energy += 1
                                        if damage > 0:
                                            damage -= 1
                                        bomb[i][j].hitting()
                                        characters[i].situationlist()[characters[i].list().index(text)] = 3
                                        Success.play(success)
                                        correct_num += 1
                                    # characters[i].situationlist()[characters[i].list().index(currentvocab)] = 3 # !!!! current vocab changed  
                    
                    text = ''  # Clear text after submission
                elif event.key == pygame.K_BACKSPACE:  # Remove last character by backspace
                    text = text[:-1]
                else:
                    text += event.unicode  # Add typed character into box
                    
        # Add the bombs for each character
        for i in range(Char):   # Manipulating the bombrate; COntrolling the bomb number; Ensure the statis is correct; Ensure there's no repeat vocabs
            if tick % characters[i].bombrate() == 0 and characters[i].isbombing() == True:
                # currentvocab = random.choice(characters[i-1].list()) 
                if len(bomb[i]) < len(characters[i].meaninglist()): # Ensure the number of bombs does not exceed the number of vocabs
                    repeat = True #Ensure there's no repeat vocabs
                    while repeat == True: 
                        currentvocab = random.choice(characters[i].meaninglist()) # add the defenition onto the bomb
                        if characters[i].situationlist()[characters[i].meaninglist().index(currentvocab)] == 1:
                            repeat = False
                            bomb[i].append(Bomb(characters[i],characters[i].list()[characters[i].meaninglist().index(currentvocab)],currentvocab)) # Add the bombs(display a vocab from the imported list each every second)
                            characters[i].addnum() # Record the quantitly of bombs
                    # change the situation of the vocab chosen: #"1" = not presented, "2" = presented, "3" = finished
                    characters[i].situationlist()[characters[i].meaninglist().index(currentvocab)] = 2 
                    print(currentvocab)
                    print(characters[i].situationlist()[characters[i].meaninglist().index(currentvocab)])
                else:
                    winning = True
                    for n in range(Char):
                        characters[n].stopbombing()
                    Win.play(win)
        
        for i in range(Char):           
            if characters[i].xx() >= 2000:
                running = False
        # Add to wrong word list if didn't match in time    
     
        for i in range(Char):
            for j in range(len(bomb[i])):
                if bomb[i][j].yy() >= SCREEN_HEIGHT - 300:
                    characters[i].situationlist()[characters[i].meaninglist().index(bomb[i][j].selfdefinition())] = 1 # !!! I used double equal last time ! ! ! ERROR
                    wrong_num += 1
                    if damage <= 15: # Decreace health bar if not matched (bomb reaches ground)
                        if 15 - damage + Difficulty >= 0:
                            damage += Difficulty
                        else:
                            damage += 15 - damage
                    if damage >= 15:
                        for n in range(Char):
                            characters[n].stopbombing()
                        Lose.play(lose)
                    
                    # Play the sound effect
                    channel2.play(BombMissed)
                    
                    Wrong_word_list.append(characters[i].list()[characters[i].meaninglist().index(bomb[i][j].selfdefinition())])
                    bomb[i].pop(j)
                    break
            #         print(characters[i].list(), len(bomb[i]))
            #         bomb[i][j] = 0
            # # print(y)
            # bomb[i] = [item for item in bomb[i] if item != 0] # Delete the bomb from bomb list, so it can be re-matched later
        
        # Decrease the Enemycraft's health
        for i in range(len(missile)):
            if missile[i].yy() <= -0:
                n = random.randint(1,5)
                if enemy_health - n >= 0:
                    enemy_health -= n
                else:
                    enemy_health = 0
                # Play the sound effect
                channel3.play(MissileHit)
                
                missile.pop(i)
                break
        
        # for i in missile:
        #     if i.yy() <= 0:
        #         i.hit()
         
        # test            
        if tick % 180 == 0:
            print(Wrong_word_list)
        
        
        
            
        # Clear the screen
        screen.blit(Background,(0,0))
        
        # Update and draw all characters
        for char in characters:
            char.move()
            char.draw()
            
        for bombs in bomb:
            for i in bombs:
                i.move()
                i.draw()
                
        for missiles in missile:
            missiles.move()
            missiles.draw()
        
        # Draw the controll table
        controll_frame = pygame.Color((50,50,50))
        #pygame.Rect(0, SCREEN_HEIGHT-(SCREEN_HEIGHT//4) - 20, SCREEN_WIDTH, (SCREEN_HEIGHT//4) + 20)
        pygame.draw.rect(screen, controll_frame, (0, SCREEN_HEIGHT-(SCREEN_HEIGHT//4) - 20, SCREEN_WIDTH, (SCREEN_HEIGHT//4) + 20))
        screen.blit(controll,(20,SCREEN_HEIGHT-(SCREEN_HEIGHT//4)))
        
        # Refreshing the text box
        input_box = pygame.Rect(SCREEN_WIDTH//2 - 100,((SCREEN_HEIGHT//5)*4) + 15, 200, 50)
        txt_surface = font.render(text, True, pygame.Color('white'))
        input_box.w = max(200, txt_surface.get_width() + 10)
        ccolor = pygame.Color(150, 150, 150)
        pygame.draw.rect(screen, ccolor, (input_box.x - 5, input_box.y - 5, input_box.w + 10, input_box.h+10))
        pygame.draw.rect(screen, color, input_box, 1)
        screen.blit(txt_surface, (input_box.x + 5, input_box.y + 10))
        
        # Draw the controll table
        pygame.draw.rect(screen, BLACK, (40, SCREEN_HEIGHT - SCREEN_HEIGHT//4 + 20, SCREEN_WIDTH//2 - 250, SCREEN_HEIGHT//5 - 45))
        pygame.draw.rect(screen, BLACK, (SCREEN_WIDTH - 40 - (SCREEN_WIDTH//2 - 250), SCREEN_HEIGHT - SCREEN_HEIGHT//4 + 20, SCREEN_WIDTH//2 - 250, SCREEN_HEIGHT//5 - 45))
        pygame.draw.rect(screen, GREY, (45, SCREEN_HEIGHT - SCREEN_HEIGHT//4 + 25, SCREEN_WIDTH//2 - 260, SCREEN_HEIGHT//5 - 55))
        
        # pygame.draw.rect(screen, GREY, (SCREEN_WIDTH - 40 - (SCREEN_WIDTH//2 - 255), SCREEN_HEIGHT - SCREEN_HEIGHT//4 + 25, SCREEN_WIDTH//2 - 260, SCREEN_HEIGHT//5 - 55))
        pygame.draw.rect(screen, (200,200,255), (SCREEN_WIDTH - 35 - (SCREEN_WIDTH//2 - 255), SCREEN_HEIGHT - SCREEN_HEIGHT//4 + 30, SCREEN_WIDTH//2 - 449, (SCREEN_HEIGHT//5 - 55)/2 - 10))
        for i in range(energy): # Energy bar
            pygame.draw.rect(screen, (255, 255, 0), (SCREEN_WIDTH - 35 - (SCREEN_WIDTH//2 - 255) + i*(SCREEN_WIDTH//2 - 450)//5, SCREEN_HEIGHT - SCREEN_HEIGHT//4 + 35, (SCREEN_WIDTH//2 - 270)//5 - 35, (SCREEN_HEIGHT//5 - 55)/2 - 20))
        
        pygame.draw.rect(screen, GREY, (SCREEN_WIDTH - 35 - (SCREEN_WIDTH//2 - 255), SCREEN_HEIGHT - SCREEN_HEIGHT//4 + 20 + (SCREEN_HEIGHT//5 - 55)/2 +10, SCREEN_WIDTH//2 - 270, (SCREEN_HEIGHT//5 - 55)/2 - 10))
        for i in range(15 - damage): # Health bar
            pygame.draw.rect(screen, GREEN, (SCREEN_WIDTH - 35 - (SCREEN_WIDTH//2 - 255) + i*(SCREEN_WIDTH//2 - 270)//15, SCREEN_HEIGHT - SCREEN_HEIGHT//4 + 20 + (SCREEN_HEIGHT//5 - 55)/2 +10, (SCREEN_WIDTH//2 - 270)//15 - 5, (SCREEN_HEIGHT//5 - 55)/2 - 10))
        
        # THe launch button    
        button_font = pygame.font.Font(None, 40)
        button_text = "Launch"
        Txt_surface = button_font.render(button_text, True, BLACK)
        Launch_button = pygame.Rect((SCREEN_WIDTH - 35 - (SCREEN_WIDTH//2 - 255) + SCREEN_WIDTH//2 - 449 + 10), (SCREEN_HEIGHT - SCREEN_HEIGHT//4 + 30), (SCREEN_WIDTH//2 - 260 - (SCREEN_WIDTH//2 - 449 + 20)), ((SCREEN_HEIGHT//5 - 55)/2 - 10))
        Launch_active = False
        if energy == 5:
            pygame.draw.rect(screen, (255,153,18), Launch_button)
            screen.blit(Txt_surface, ((SCREEN_WIDTH - 35 - (SCREEN_WIDTH//2 - 255) + SCREEN_WIDTH//2 - 449 + 10)+(SCREEN_WIDTH//2 - 260 - (SCREEN_WIDTH//2 - 449 + 20))//2 - 50, (SCREEN_HEIGHT - SCREEN_HEIGHT//4 + 30)+((SCREEN_HEIGHT//5 - 55)/2 - 10)//2 - 10))
            Launch_active = True
        else:
            pygame.draw.rect(screen, (128,128,128), Launch_button)
            screen.blit(Txt_surface, ((SCREEN_WIDTH - 35 - (SCREEN_WIDTH//2 - 255) + SCREEN_WIDTH//2 - 449 + 10)+(SCREEN_WIDTH//2 - 260 - (SCREEN_WIDTH//2 - 449 + 20))//2 - 50, (SCREEN_HEIGHT - SCREEN_HEIGHT//4 + 30)+((SCREEN_HEIGHT//5 - 55)/2 - 10)//2 - 10))
            Launch_active = False
            
        # Enemy Health
        if tick >= 180 and characters[len(characters)-1].isbombing() == True:
            pygame.draw.rect(screen, BLACK, (SCREEN_WIDTH//2 - 400, 30, 800, 80))
            textn = ",".join(launch_selected_list)
            fontn = pygame.font.Font(None, 40)
            txt_Surface = fontn.render(textn, True, WHITE)
            screen.blit(txt_Surface, (SCREEN_WIDTH//2 - 400 + 10, 40))
            
            for i in range(enemy_health):
                pygame.draw.rect(screen, (255,50,50), (SCREEN_WIDTH//2 - 400 + 10 + i*(795//e_health), 70, 795//e_health - 5, 30))
        if enemy_health <= 0:
            for i in range(Char):
                winning = True
                for n in range(Char):
                    characters[n].stopbombing()
                Win.play(win)
            
        
        # Refreshing the Tutorials
        Tfont = pygame.font.Font(None, 24)
        Ttext = (
            "WARNING !!! Instructions !!! WARNING           \n"
            "------------------------------------------------------------------------------------------\n"
            "Enter the special code(vocab) that matches the definition \n"
            "on each bomb to intercept it from falling down!\n"
            "------------------------------------------------------------------------------------------\n"
            "DONT LET THE BOMB FURTHER DESTORY THE CITY!"
        )
        
        lines = Ttext.splitlines()  # Split the text into lines
        for i, line in enumerate(lines):
            # Render each line of text
            text_surface = Tfont.render(line, True, (200,50,50))
            # Position the line on the screen
            screen.blit(text_surface, (50, 705 + i * 20))
        
        # display_multiline_text(screen, Ttext, 50, 700, 20, Tfont, 'Black')

        # Update the display
        pygame.display.flip()

        # Control frame rate
        clock.tick(60)
        tick += 1
        # print(tick)
    
    global_correct_num = correct_num
    global_wrong_num = wrong_num
    global_wrong_word_list = Wrong_word_list
    for i in characters:
        global_word_num += i.selfnum()
    Wrong_word_list.append(global_word_num)
    
    conn.send([Wrong_word_list, correct_num, wrong_num])
    conn.close()
    

# # # List to store all vocabs:
# Vocab = [['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']]
# Meaning = [['a1','b1','c1','d1','e1','f1','g1','h1','i1','j1','k1','l1','m1','n1','o1','p1','q1','r1','s1','t1','u1','v1','w1','x1','y1','z1']]
# main('hi',Vocab, Meaning, 5)

# Planned updates:
#1. Put all content into a function COMPLETED
#2. Re-render the boss HP bar to make it stick better

