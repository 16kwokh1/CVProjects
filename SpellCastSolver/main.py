import re

def parser():

    print("3#A = Letter Multipler x 3 | 3@A = Word Multipler x 3")

    global grid 
    grid = []

    for i in range (5):
        line = input(f"Line {i+1}:")
        grid.append(line_parser(line))

# 3LA = Letter Multipler x3
# 3WA = Word Multipler x3
def line_parser(line_text):
    line = []

    length = len(line_text)
    i = 0
    while i < length: 
        letter = {
                    "letter" : "", 
                    "letter_multiplier" : 1,
                    "word_multiplier" : 1
                }

        if line_text[i].isdigit():

            multipler = int(line_text[i])
            multiplier_type = line_text[i+1]
            multiplier_letter = line_text[i+2]

            # 3#A = Letter Multipler x3
            if multiplier_type == "L":
                letter["letter"] = multiplier_letter
                letter["letter_multiplier"] = multipler
            # 3@A = Word Multipler x3
            elif multiplier_type == "W":
                letter["letter"] = multiplier_letter
                letter["word_multiplier"] = multipler

            i = i+3
        
        elif line_text[i].isalpha():
            
            letter["letter"] = line_text[i]
            
            i = i+1

        line.append(letter)

    return line

def print_grid():
    for i in grid:
        row = []
        for j in i:
            letter_dict = j
            letter = letter_dict["letter"]

            multiplier = ""
            if letter_dict["letter_multiplier"] > 1:
                multiplier = f"Lx{letter_dict['letter_multiplier']}"
            elif letter_dict["word_multiplier"] > 1:
                multiplier = f"Wx{letter_dict['word_multiplier']}"

            if multiplier != "":
                row_letter = f"{multiplier}:{letter}"
            else:
                row_letter = letter

            row.append(row_letter)
        print(" ".join(row))


# go in all 9 directions and slowly build up
    # check if word beginning contains word
    # check if word is the same

square_length = 5

#function traverses grid 
def traverse_grid():
    for i in range(square_length):
        for j in range(square_length):
            search_word(i,j,[])

highest_score = 0
highest_word = ""
def search_word(x,y, visited):
    
    if x < 0 or x > square_length-1 or y < 0 or y > square_length-1 or (x,y) in visited:
        return

    current = (x,y)
    visited.append(current)

    # global total
    # total += 1
    # print(f"{total}:{visited}")

    #check word using visited
    word = convert_path_word(visited)
    if not check_word(word):
        return

    search_word(x-1,y-1, visited.copy())
    search_word(x,y-1, visited.copy())
    search_word(x+1,y-1, visited.copy())
    search_word(x-1,y, visited.copy())
    search_word(x+1,y, visited.copy())
    search_word(x-1,y+1, visited.copy())
    search_word(x,y+1, visited.copy())
    search_word(x+1,y+1, visited.copy())


def convert_path_word(path):
    word = ""
    score = 0
    word_multiplier = 1

    for coord in path:
        x = coord[0]
        y = coord[1]

        letter_dict = grid[y][x]
        letter = letter_dict["letter"]
        word += letter
        score += scores[letter] * letter_dict["letter_multiplier"]

        if letter_dict["word_multiplier"] > 1:
            word_multiplier = letter_dict["word_multiplier"]

    score *= word_multiplier

    return (word, score)

def parse_dictionary():
    text_file = open("dictionary.txt", "r")
    global dictionary
    dictionary = text_file.read()
    # print(data)

def check_word(path):

    word = path[0]
    score = path[1]

    word.capitalize()
    regex = f"\\b{word}[A-Z]*\\b"
    match = re.search(regex, dictionary)

    if match: # subword

        if match.group(0) == word: # exact match
            
            global highest_score
            global highest_word
            if score > highest_score:
                highest_score = score
                highest_word = word

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

    start = time.time()

    parse_dictionary()
    traverse_grid()
    print(highest_score)
    print(highest_word)

    end = time.time()
    print(f"Execution time : {end - start}")

