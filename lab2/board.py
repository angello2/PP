# -*- coding: utf-8 -*-
"""
Created on Sun May 15 20:31:16 2022

@author: Filip
"""
import numpy as np

class Board:
    def __init__(self, width=7, height=6, file_path=None):
        self.width = width
        self.height = height
        if file_path is None:
            self.board = np.zeros((height, width)).astype(dtype='int')
        else:
            f = open(file_path)
            rows = list()
            for line in f.readlines():
                elements = line.replace('\n', '').split(' ')
                row = np.array(elements)
                rows.append(row)
            self.board = np.vstack(rows).astype(dtype='int')
        
    def __str__(self):
        return str(self.board)
        
    def play_column(self, column, player):
        if self.board[0][column] != 0:          
            return
        i = self.height - 1
        while i >= 0:
            if self.board[i][column] == 0:
                if player == 'human':
                    self.board[i][column] = 2
                elif player == 'cpu':            
                    self.board[i][column] = 1
                break
            i -= 1
    
    def undo_column(self, column):
        i = 0
        while self.board[i][column] == 0 and i < self.height - 1:
            i += 1
        if i < self.height:
            self.board[i][column] = 0
            
    def move_legal(self, column):
        if self.board[0][column] != 0:
            return False
        else:
            return True
        
    def check_win(self, last_change):
        # last change je stupac u kojem je zadnje igran potez
        i = 0
        while self.board[i][last_change] == 0 and i < self.height - 1:
            i += 1
        row = i
        column = last_change
        last_player = self.board[row, column]
        
        # provjeravamo prvo ima li 4 istih zaredom u stupcu
        token_list = list()
        for i in range(row, self.height):
            token_list.append(self.board[i, column])
        if self.find_four(token_list):
            return True, last_player
            
        # provjeravamo redak
        token_list = list()
        for j in range(0, self.width):
            token_list.append(self.board[row, j])
        if self.find_four(token_list):
            return True, last_player
        
        # provjeravamo /
        token_list = list()
        token_list.append(self.board[row, column])
        for i in range(1, self.height - row):
            # ovo je dijagonala prema dolje lijevo
            if row + i < self.height and column - i >= 0:
                token_list.append(self.board[row + i, column - i])
        for i in range(1, self.width - column):
            # prema gore desno
            if row - i >= 0 and column + i < self.width:
                token_list.append(self.board[row - i, column + i])
        if self.find_four(token_list):
            return True, last_player
            
        # provjeravamo \
        token_list = list()
        token_list.append(self.board[row, column])
        for i in range(1, np.abs(0 - row) + 1):
            # ovo je dijagonala prema gore lijevo
            if row - i >= 0 and column - i >= 0:
                token_list.append(self.board[row - i, column - i])
        
        for i in range(1, self.width - column):
            # prema dolje desno
            if row + i < self.height and column + i < self.width:
                token_list.append(self.board[row + i, column + i])
        if self.find_four(token_list):
            return True, last_player
        
        return False, 0
            
    def find_four(self, token_list):
        if len(token_list) < 4:
            return False        
        counter = 1
        for i in range(1, len(token_list)):
            if token_list[i] == 1 or token_list[i] == 2:
                if token_list[i] == token_list[i - 1]:
                    counter += 1
                else:
                    counter = 1
                if counter == 4:
                    return True                    
            
        return False