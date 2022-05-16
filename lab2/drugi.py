# -*- coding: utf-8 -*-
"""
Created on Sun May 15 16:34:21 2022

@author: Filip
"""

from mpi4py import MPI
from board import Board

import sys
import time
import numpy as np

def evaluate(board, cpu_turn, last_change, depth):    
    game_over, winner = board.check_win(last_change)
    if game_over:
        if winner == 1:
            return 1
        elif winner == 2:
            return -1
    
    if depth == 0:
        return 0
    
    if cpu_turn:
        player = 'cpu'
    else:
        player = 'human'
        
    score_sum = 0.0
    all_losses, all_wins = True, True  
    depth -= 1
    for i in range(7):
        board.play_column(i, player)
        score = evaluate(board, not cpu_turn, i, depth)
        board.undo_column(i)
        
        if score > -1: all_losses = False
        if score != 1: all_wins = False
        if score == 1 and not cpu_turn: return 1
        if score == -1 and cpu_turn: return -1
        score_sum += score
    
    if all_wins: return 1
    if all_losses: return -1
    
    return score_sum / 7   

DATA = 1
REQUEST = 2
TASK = 3
RESULT = 4
WAIT = 5
END = 6

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.size

print('hello %d on %s' % (rank, MPI.Get_processor_name()))
comm.Barrier()

if rank == 0:
    board = Board()
    while True:
        print(board)    
        
        start_time = time.time()
            
        tasks = {}
        for cpu_move in range(7):
            for player_move in range(7):
                tasks[(cpu_move, player_move)] = None
                    
        # saljemo plocu ostalim procesima
        for x in range(1, size):
            msg = {'type':DATA, 'board':board}
            comm.send(msg, dest=x)
        
        active_workers = size - 1
        finished = False
        while not finished:
            status = MPI.Status()
            msg = comm.recv(source=MPI.ANY_SOURCE, status=status)
            source = status.Get_source()
            
            if msg['type'] == REQUEST:
                for task, result in tasks.items():
                    if result is None:
                        unfinished_task = task
                if unfinished_task is not None:
                    tasks[unfinished_task] = True
                    answer = {'type':TASK, 'task':task}
                    comm.send(answer, dest=source)
                else:
                    active_workers -= 1
                    if active_workers == 0:
                        finished = True
                    answer = {'vrsta':WAIT}
                    comm.send(answer, dest = source)
            
            if msg['type'] == RESULT:
                tasks[msg['task']] = msg['result']
                
        move_score = []
        for i in range(7):
            score_sum = 0
            for j in range(7):
                score_sum += tasks[(i, j)]
            move_score.append(score_sum / 7)
        
        best_move = 0
        best_score = -1
        for i in range(7):
            if move_score[i] > best_score:
                best_score = move_score[i]
                best_move = i
        
        end_time = time.time()
        
        for i in range(7):
            print('Kvaliteta poteza', i, 'je', move_score[i])
        print('Najbolji potez je', best_move)
        print('Vrijeme izračuna:', end_time - start_time, 'sekundi')
            
        board.play_column(best_move, 'cpu')
        print(board)
        game_over, winner = board.check_win(best_move)
        if game_over:
            print('CPU pobjedio')
            for i in range(active_workers):
                msg = {'type':END}
                comm.send(msg, dest=i)
                break  
        
        player_move = int(input('Unesite stupac koji želite odigrati:'))
        board.play_column(player_move, 'human')
        print(board)
        game_over, winner = board.check_win(best_move)
        if game_over:
            print('Igrač pobjedio')
            for i in range(active_workers):
                msg = {'type':END}
                comm.send(msg, dest=i)
                break
        
else:
    while True:
        msg = comm.recv(source=0)
        
        if msg['type'] == END:
            print('Proces', rank, 'završava s radom.')
            break
        
        if msg['type'] == DATA:
            print('Proces', rank, 'primio podatke.')
            board = msg['board']
            
        while True:
            # zahtjev za zadatkom
            msg = {'type':REQUEST}
            comm.send(msg, dest=0)
            
            response = comm.recv(source = 0)
            if response['type'] == WAIT:
                break
            elif response['type'] == TASK:
                task = response['task']
                
            board.play_column(task[0], player='cpu')
            game_over, winner = board.check_win(task[0])
            if game_over:
                result = 1
                board.undo_column(task[0])
                msg = {'type':RESULT, 'task':task, 'result':result}
                comm.send(msg, dest=0)
                continue
            
            board.play_column(task[1], player='human')
            game_over, winner = board.check_win(task[1])
            if game_over:
                result = -1
                board.undo_column(task[1])
                msg = {'type':RESULT, 'task':task, 'result':result}
                comm.send(msg, dest=0)
                continue
            
            result = evaluate(board, True, task[1], 6)
            
            board.undo_column(task[1])
            board.undo_column(task[0])
            
            msg = {'type':RESULT, 'task':task, 'result':result}
            comm.send(msg, dest=0)
            
        
        
        