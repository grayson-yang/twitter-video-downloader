#!/usr/bin/env python

from pathlib import Path

class FileLinesAccess:

    def __init__(self, file):
        self.file = file
        self.lines = self.readLines(file)


    def readLines(self, file):
        lines = []
        Path(file).touch()
        with open(Path(file), 'r') as f1:
            lines = f1.readlines()
        for i in range(0, len(lines)):
            lines[i] = lines[i].rstrip('\n')
        return lines


    def saveLines(self, lines):
        save2disk = False
        newlines = []
        for line in lines:
            if line not in self.lines:
                save2disk = True
                self.lines.append(line)
                newlines.append(line + '\n')
        if save2disk is True:
            with open(self.file, 'a') as f:
                f.writelines('\n')
                f.writelines(newlines)
