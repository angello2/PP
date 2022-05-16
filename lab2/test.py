# -*- coding: utf-8 -*-
"""
Created on Mon May 16 18:51:30 2022

@author: Filip
"""

from mpi4py import MPI
from board import Board

import sys
import time
import numpy as np

DATA = 1
REQUEST = 2
TASK = 3
RESULT = 4
WAIT = 5
END = 6

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

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.size

print('Started process', rank, flush=True)
comm.Barrier()

if rank == 0:
    board = Board()
    while True:
        print('Current board state:\n', board, flush=True)
        print()
        
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
                unfinished_task = None
                for task, result in tasks.items():
                    if result is None:
                        unfinished_task = task
                        break
                if unfinished_task is not None:
                    print('master found unfinished task:', unfinished_task[0], unfinished_task[1], flush=True)
                    tasks[unfinished_task] = True
                    print('Updated tasks:', tasks)
                    answer = {'type':TASK, 'task':task}
                else:
                    answer = {'vrsta':WAIT}
                    active_workers -= 1
                    if active_workers == 0:
                        finished = True
                comm.send(answer, dest=source)
            
            if msg['type'] == RESULT:
                print('Master primio rezultat za task', msg['task'], ' = ', msg['result'])
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
            print('Move quality of move', i, 'is', move_score[i], flush=True)
        print('The best move is', best_move, flush=True)
        print('Calculation time:', end_time - start_time, 'seconds', flush=True)
            
        board.play_column(best_move, 'cpu')
        print(board)
        game_over, winner = board.check_win(best_move)
        if game_over:
            print('CPU won', flush=True)
            for i in range(active_workers):
                msg = {'type':END}
                comm.send(msg, dest=i)
                break  
        
        player_move = int(input('Enter your move:'))
        board.play_column(player_move, 'human')
        game_over, winner = board.check_win(best_move)
        if game_over:
            print('You won!', flush=True)
            for i in range(active_workers):
                msg = {'type':END}
                comm.send(msg, dest=i)
                break
            
else:
    while True:
        msg = comm.recv(source=0)
        
        if msg['type'] == END:
            print('Process', rank, 'has no more work.', flush=True)
            break
        
        if msg['type'] == DATA:
            print('Process', rank, 'received data.', flush=True)
            board = msg['board']
            
        while True:
            # zahtjev za zadatkom
            msg = {'type':REQUEST}
            comm.send(msg, dest=0)
            print('Process', rank, 'sent request for work.', flush=True)
            
            response = comm.recv(source = 0)
            print('Process', rank, 'received response.', flush=True)
            if response['type'] == WAIT:
                break
            elif response['type'] == TASK:
                task = response['task']
                
            print('Process', rank, 'is doing task:(' +  str(task[0]) + ',' + str(task[1]) + ')', flush=True)
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
            
            result = evaluate(board, True, task[1], 5)
            print('Process', rank, 'got result for evaluate:', result, flush=True)
            
            board.undo_column(task[1])
            board.undo_column(task[0])
            
            msg = {'type':RESULT, 'task':task, 'result':result}
            comm.send(msg, dest=0)