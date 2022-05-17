# -*- coding: utf-8 -*-
"""
Created on Mon May 16 18:51:30 2022

@author: Filip
"""

from mpi4py import MPI
from board import Board

import sys
import time

def evaluate(board, cpu_turn, last_change, depth):    
    game_over, winner = board.check_win(last_change)
    if game_over:
        if not cpu_turn:
            return 1
        elif cpu_turn:
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
            msg = {'type':'data', 'board':board}
            comm.send(msg, dest=x)
        
        active_workers = size - 1
        finished = False
        while not finished:
            status = MPI.Status()
            msg = comm.recv(source=MPI.ANY_SOURCE, status=status)
            source = status.Get_source()
            
            if msg['type'] == 'request':
                unfinished_task = None
                for task, result in tasks.items():
                    if result is None:
                        unfinished_task = task
                        break
                if unfinished_task is not None:
                    tasks[unfinished_task] = True
                    answer = {'type':'task', 'task':task}
                else:
                    answer = {'type':'wait'}
                    active_workers -= 1
                    if active_workers == 0:
                        finished = True
                comm.send(answer, dest=source)
            
            if msg['type'] == 'result':
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
            print('Move quality for move', i, 'is', move_score[i], flush=True)
        print('The best move is', best_move, flush=True)
        print('Calculation time:', end_time - start_time, 'seconds', flush=True)
            
        board.play_column(best_move, 'cpu')
        game_over, winner = board.check_win(best_move)
        print(board)
        if game_over:
            print('CPU won', flush=True)
            for i in range(7):
                msg = {'type':'end'}
                comm.send(msg, dest=i)
            sys.exit()
        
        player_move = int(input('Enter your move:'))
        board.play_column(player_move, 'human')
        print(board)
        game_over, winner = board.check_win(player_move)
        if game_over:
            print('You won!', flush=True)
            for i in range(7):
                msg = {'type':'end'}
                comm.send(msg, dest=i)
            sys.exit()
            
else:
    while True:
        msg = comm.recv(source=0)
        
        if msg['type'] == 'end':
            sys.exit()
            
        if msg['type'] == 'data':
            board = msg['board']
            
        while True:
            # zahtjev za zadatkom
            msg = {'type':'request'}
            comm.send(msg, dest=0)
            
            response = comm.recv(source = 0)
            if response['type'] == 'wait':
                break
            elif response['type'] == 'task':
                task = response['task']
            board.play_column(task[0], player='cpu')
            game_over, winner = board.check_win(task[0])
            if game_over:
                result = 1
                board.undo_column(task[0])
                msg = {'type':'result', 'task':task, 'result':result}
                comm.send(msg, dest=0)
                continue
            
            board.play_column(task[1], player='human')
            game_over, winner = board.check_win(task[1])
            if game_over:
                result = -1
                board.undo_column(task[1])
                msg = {'type':'result', 'task':task, 'result':result}
                comm.send(msg, dest=0)
                continue
            
            result = evaluate(board, True, task[1], 5)
            
            board.undo_column(task[1])
            board.undo_column(task[0])
            
            msg = {'type':'result', 'task':task, 'result':result}
            comm.send(msg, dest=0)