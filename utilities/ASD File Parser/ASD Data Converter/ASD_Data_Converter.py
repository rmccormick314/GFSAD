import pandas as pd
import _io as io
from os import listdir
from os.path import isfile, join

mypath = 'ASD_Data_8-18'

files = [f for f in listdir(mypath) if isfile(join(mypath, f))]
k = 0

final_df = pd.DataFrame();

for fil in files:

    data = str(fil)

    def file_len(filename):
        with open(mypath + "/" + filename) as f:
            for i, _ in enumerate(f):
                pass
        return i + 1

    f = open(mypath + "/" + data, 'r')

    LENGTH = file_len(data)

    LINES = [3, 6, 7, 11]
    LINES_DESC = {
        3 : "Description",
        6 : "Time & Date",
        7 : "Integration Time",
        11 : "Y Min / Max"
    }
    DATA_START = 41

    

    #data = f.read()
    i = 0
    j = 0
    DATA = []

    COLS = ['File / Sample', 'Time', 'Date']
    VALS = [fil]

    while i < LENGTH:
        line = f.readline()
        if (i in LINES):
            current = LINES_DESC[i]
            if (current == "Description"):
                #VALS.append(line)
                pass

            if (current == "Time & Date"):
                time = line[16:25]
                date = line[30:-1]

                VALS.append(time)
                VALS.append(date)

            if (current == "Integration Time"):
                inte_time = line[-1:-2]
                #DATA.append(inte_time)

        if (i > DATA_START):
            data_line = line.split('\t')
            data_line[1] = data_line[1].replace(" \n", "")

            COLS.append(data_line[0])
            VALS.append(data_line[1])

            j += 1

        i += 1

    COLS = pd.Series(COLS)
    VALS = pd.Series(VALS)

    if(k == 0):
        final_df = pd.concat([final_df, COLS], axis=1)
    final_df = pd.concat([final_df, VALS], axis=1)
    k += 1

final_df.reset_index(drop=True, inplace=True)
final_df = final_df.T

print(final_df)
final_df.to_csv('file1.csv', escapechar='\n')