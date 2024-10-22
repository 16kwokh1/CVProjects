import re
import multiprocessing as mp

def parser():

    print("3LA = Letter Multipler x 3 | 3WA = Word Multipler x 3")

    global grid
    grid = ""

    for i in range (5):
        line = input(f"Line {i+1}:")
        grid += line_parser(line)

# 3LA = Letter Multipler x3
# 3WA = Word Multipler x3

# string is recorded as 31L - 3xLetter | 1xWord | Letter L
def line_parser(line_text):
    line = ""

    length = len(line_text)
    i = 0
    while i < length: 

        if line_text[i].isdigit():

            multipler = line_text[i]
            multiplier_type = line_text[i+1]
            letter = line_text[i+2].capitalize()

            # 3#A = Letter Multipler x3
            if multiplier_type == "L" or multiplier_type == "l":
                line += multipler
                line += "1"
                line += letter
            # 3@A = Word Multipler x3
            elif multiplier_type == "W" or multiplier_type == "w":
                line += "1"
                line += multipler
                line += letter

            i += 3
        
        elif line_text[i].isalpha():
            
            letter = line_text[i].capitalize()

            line += "1"
            line += "1"
            line += letter
            
            i += 1

    return line

def print_grid():

    max = len(grid)
    i = 0
    row = []
    while i < max:
        
        letter_multiplier = int(grid[i])
        word_multiplier = int(grid[i+1])
        letter = grid[i+2]

        row_letter = ""

        if letter_multiplier > 1:
            row_letter = f"Lx{letter_multiplier}:{letter}"
        elif word_multiplier > 1:
            row_letter = f"Wx{word_multiplier}:{letter}"
        else:
            row_letter = f"{letter}"

        row.append(row_letter)

        if len(row) % 5 == 0:
            print(" ".join(row))
            row = []

        i += 3

# go in all 9 directions and slowly build up
    # check if word beginning contains word
    # check if word is the same

square_length = 5

#function traverses grid 
def traverse_grid():

    process_list = []
    shared_grid = mp.RawArray("c", grid.encode('UTF-8'))
    highest_score = mp.Queue()

    for i in range(square_length):
        for j in range(square_length):
            process_list.append(mp.Process(target=search_word, args=(i,j,[], shared_grid, dictionary, highest_score)))

    for i in process_list:
        i.start()    

    score = 0
    word = ""
    while not check_finished(process_list):

        while not highest_score.empty():
            current = highest_score.get()
            current_word = current[0]
            current_score = current[1]

            if current_score > score:
                score = current_score
                word = current_word
                (f"{word} : {score}")

    print()
    print(f"HIGHEST | {word} ({score})")

def check_finished(processes):
    for proc in processes:
        proc.join(timeout=0)
        if proc.is_alive():
            return False
    return True
    
def search_word(x,y, visited, shared_grid, shared_dictionary, highest_score):
    
    if x < 0 or x > square_length-1 or y < 0 or y > square_length-1 or (x,y) in visited:
        return

    current = (x,y)
    visited.append(current)

    #check word using visited
    word = convert_path_word(visited, shared_grid)
    # print(word)
    if not check_word(word, shared_dictionary, highest_score):
        return

    search_word(x-1,y-1, visited.copy(), shared_grid, shared_dictionary, highest_score)
    search_word(x,y-1, visited.copy(), shared_grid, shared_dictionary, highest_score)
    search_word(x+1,y-1, visited.copy(), shared_grid, shared_dictionary, highest_score)
    search_word(x-1,y, visited.copy(), shared_grid, shared_dictionary, highest_score)
    search_word(x+1,y, visited.copy(), shared_grid, shared_dictionary, highest_score)
    search_word(x-1,y+1, visited.copy(), shared_grid, shared_dictionary, highest_score)
    search_word(x,y+1, visited.copy(), shared_grid, shared_dictionary, highest_score)
    search_word(x+1,y+1, visited.copy(), shared_grid, shared_dictionary, highest_score)


def convert_path_word(path, shared_grid):
    word = ""
    score = 0
    word_multiplier = 1

    for coord in path:
        x = coord[0]
        y = coord[1]

        i = (y*square_length+x)*3

        letter_m = int(shared_grid[i])
        word_m = int(shared_grid[i+1])
        letter = shared_grid[i+2].decode('UTF-8')

        # print(f"{letter_m} {word_m} {letter}")

        word += letter
        score += scores[letter] * letter_m

        if word_m > 1:
            word_multiplier = word_m

    score *= word_multiplier

    return (word, score)

def parse_dictionary():
    text_file = open("dictionary.txt", "r")
    global dictionary
    dictionary = text_file.read()
    # print(data)

def check_word(path, shared_dictionary, highest_score):

    word = path[0]
    score = path[1]

    word.capitalize()
    regex = f"\\b{word}[A-Z]*\\b"
    match = re.search(regex, shared_dictionary)

    if match: # subword

        if match.group(0) == word: # exact match
            
            # print(path)
            highest_score.put(path)

        return True
    else:
        return False

scores = {
    "A" : 1,
    "B" : 4,
    "C" : 5,
    "D" : 3,
    "E" : 1,
    "F" : 5,
    "G" : 3,
    "H" : 4,
    "I" : 1,
    "J" : 7,
    "K" : 6,
    "L" : 3,
    "M" : 4,
    "N" : 2,
    "O" : 1,
    "P" : 4,
    "Q" : 8,
    "R" : 2,
    "S" : 2,
    "T" : 2,
    "U" : 4,
    "V" : 5,
    "W" : 5,
    "X" : 7,
    "Y" : 4,
    "Z" : 8,
}

        


import time
if __name__ == '__main__':


    #    print(calculate_score("TEKKEN"))

    parser()
    print_grid()

    shared_grid = mp.RawArray("c", grid.encode('UTF-8'))

    start = time.time()

    parse_dictionary()
    traverse_grid()

    end = time.time()
    print(f"Execution time : {end - start}")

