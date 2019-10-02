import tkinter as tk
from tkinter import filedialog

# labels have a colon (':') after them when defined.
# Instruction types:
#  label: instr Data1 Data2  # usual instruction
#  label: .BYTE Data         # store Data in current memroy cell and call it 'label'
#  label: .DEF Data          # define 'label' to be the data value (without storage)

# Comments start with a semi-colon (';') and go until end of line.

# When referenced in an instruction, a label can be modified by adding or
# substracting a number to it (without spaces).
# For example, one can write:
#start:
#   copylr	0 label+2
#   copylr	4 statusReg
#label:
#   copylr  0 255
# It will assemble as:
# [start:] 0
#    0 (00000000) 00000011   3 copylr
#    1 (00000001) 00000000   0 0
#    2 (00000010) 00001000   8 8
#    3 (00000011) 00000011   3 copylr
#    4 (00000100) 00000100   4 4
#    5 (00000101) 11111100 252 252
# [label:] 6
#    6 (00000110) 00000011   3 copylr
#    7 (00000111) 00000000   0 0
#    8 (00001000) 11111111 255 255
# *** Label table ***
# 	  statusReg    252
# 	  start 		 0
# 	  label 		 6

# Full table of instructions: it's a dictionnary
# where instructions are the keys and the values are
# a tuple of binary code, integer value of code and number of operands for instructions
# 'inst' => ('binary code', integer value of code, number of operand)

instr2binary = {
    'halt'    : ('00000000', 0, 0),
    'nop'     : ('00000001', 1, 0),
    'speed'   : ('00000010', 2, 1),
    'copylr'  : ('00000011', 3, 2),
    'copyla'  : ('00000100', 4, 1),
    'copyar'  : ('00000101', 5, 1),
    'copyra'  : ('00000110', 6, 1),
    'copyrr'  : ('00000111', 7, 2),
    'addla'   : ('00001000', 8, 1),
    'addra'   : ('00001001', 9, 1),
    'subla'   : ('00001010', 10, 1),
    'subra'   : ('00001011', 11, 1),
    'andla'   : ('00001100', 12, 1),
    'andra'   : ('00001101', 13, 1),
    'orla'    : ('00001110', 14, 1),
    'orra'    : ('00001111', 15, 1),
    'xorla'   : ('00010000', 16, 1),
    'xorra'   : ('00010001', 17, 1),
    'decr'    : ('00010010', 18, 1),
    'incr'    : ('00010011', 19, 1),
    'decrjz'  : ('00010100', 20, 1),
    'incrjz'  : ('00010101', 21, 1),
    'shiftrl' : ('00010110', 22, 1),
    'shiftrr' : ('00010111', 23, 1),
    'cbr'     : ('00011000', 24, 2),
    'sbr'     : ('00011001', 25, 2),
    'bcrsc'   : ('00011010', 26, 2),
    'bcrss'   : ('00011011', 27, 2),
    'jump'    : ('00011100', 28, 1),
    'call'    : ('00011101', 29, 1),
    'retla'   : ('00011110', 30, 1),
    'return'  : ('00011111', 31, 0),
    'addrpc'  : ('00100000', 32, 1),
    'initsp'  : ('00100001', 33, 0),
    'randa'   : ('00100010', 34, 0),
    '.byte'   : (None, None, 1),
    }


# get currentLine

# global variables used to process line
labelTable = {}
inverseLabelTable = {}
PC = 0
lineNumber = 1

def error(str, line):
    print("ERROR(line ", lineNumber, ") <", line, ">: ", str, sep='')


def removeComments(currentLine):
    if ';' in currentLine:
        index = currentLine.find(';')
        currentLine = currentLine[:index]
    return currentLine.strip()

def ProcessLine(currentLine):
    # remove comments and spaces
    currentLine = removeComments(currentLine)

    if len(currentLine) == 0: # A blank line
        return {}

    # Otherwise extract label, instruction and data
    lineDict = {}
    splitLine = currentLine.split()

    if ':' in splitLine[0]: # there is a label
        lineDict['label'] = splitLine.pop(0)[:-1] # remove trailing :
        # get current address
        if lineDict['label'] in labelTable:
            error(currentLine, "Multiple label definition.")
        else:
            labelTable[lineDict['label']] = PC
            inverseLabelTable[PC] = lineDict['label']

    if len(splitLine) > 0: # still something on line
        lineDict['instr'] = splitLine.pop(0).lower()
        lineDict['data'] = splitLine # will be [] or ['3'] or ['lab', '3']...

        # If .DEF used, label must have data value, not PC
        if lineDict['instr'] == ".def":
            if 'label' not in lineDict: # no label with .DEF
                error(currentLine, "no label on .DEF line")
                return {}
            if len(lineDict['data']) != 1: # incorrect data with .DEF
                error(currentLine, "only one data allowed on .DEF line")
                return {}
            else: # get value from data
                labelTable[lineDict['label']] = int(lineDict['data'][0])
    return lineDict

def readFile(filename):
    global lineNumber, PC
    # Reading the file
    fullPgm = []
    f = open(filename, "r")
    line = f.readline()
    while (line != ""):
        lineDict = ProcessLine(line)
        lineDict['fullLine']=line.strip()
        if lineDict and 'instr' in lineDict and lineDict['instr'] != ".def":
            # there is an instruction and it's not .DEF
            if lineDict['instr'] == ".byte":
                PC += 1
            else:
                PC += 1 + len(lineDict['data'])
            fullPgm.append(lineDict)
        line = f.readline()
        lineNumber += 1
    f.close()
    return fullPgm


# A data is given. It may be a label ('loop') or a label +/- a number
# ('loop+12'). This function computes the final value.
def findLabelValue(data, line):
    if '+' in data:
        index = data.find('+')
        label = data[:index]
        value = int(data[index+1:])
    elif '-' in data:
        index = data.find('-')
        label = data[:index]
        value = -int(data[index+1:])
    else:
        label = data
        value = 0
    if not label in labelTable:
        error("unknown label", line['fullLine'])
        return -1
    else:
        return labelTable[label] + value

# now replace label with value
def replaceLabelWithValue(fullPgm):
    for line in fullPgm:
        for i in range(len(line['data'])):
            data = line['data'][i]
            if not data.isdigit(): # it's a label
                line['data'][i] = findLabelValue(data, line)



# Show file dialog
root = tk.Tk()
root.withdraw()
filename = filedialog.askopenfilename()
root.update()
root.destroy()
print("\n")


fullPgm = readFile(filename)
replaceLabelWithValue(fullPgm)


# Now translate full program in binary

PC = 0
for lineDict in fullPgm:
    if PC in inverseLabelTable:
        print('[',inverseLabelTable[PC],':] ', PC, sep='')
    if lineDict['instr'] not in instr2binary:
        error("unknown instruction", lineDict['fullLine'])
    else:
        binaryCode = instr2binary[lineDict['instr']][0]
        binaryValue = instr2binary[lineDict['instr']][1]
        numberOperands = instr2binary[lineDict['instr']][2]
        if binaryCode != None: # A .BYTE directive has no instruction to translate
            print('{:>3} ({:08b}) {} {:>3} {}'.format(PC, PC, binaryCode, binaryValue, lineDict['instr']), end="")
            PC += 1
            if 'label' in lineDict:
                print ("  [" + lineDict['label'] + "]")
            else:
                print("")
        if numberOperands != len(lineDict['data']):
            error("wrong number of operands", lineDict['fullLine'])
        else:
            for data in lineDict['data']:
                print('{:>3} ({:08b}) {:08b} {:>3} {}'.format(PC, PC, int(data), int(data), data), end="")
                PC += 1
                if 'label' in lineDict:
                    print ("  [" + lineDict['label'] + "]")
                else:
                    print("")

print("*** Label table ***")
for label in labelTable:
    print("\t", label, "\t\t", labelTable[label])







