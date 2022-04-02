# -*- coding: utf-8 -*-
"""
Created on Thu Mar 31 18:21:17 2022

@author: Filip
"""

import random
import time
from mpi4py import MPI

class Filozof():
    def __init__(self, i, n):
        self.i = i
        
        if i == 0:
            self.susjedi = (n - 1, i + 1)
            self.vilice = {'L' : 'Prljava', 'D' : 'Prljava'}
            
        elif(i != 0 and i != n - 1):
            self.susjedi = (i - 1, i + 1)
            self.vilice = {'L' : 'Nema', 'D' : 'Prljava'}
        
        else:
            self.susjedi = (i - 1, 0)
            self.vilice = {'L' : 'Nema', 'D' : 'Nema'}
            
        self.broj_vilica = self.izracunaj_broj_vilica()
        
    def start(self):
        while(True):
            # mislim i citam zahtjeve
            print(i, i * '    ' + 'Mislim...', flush=True)
            vrijeme = random.randint(2, 6)
            for sekunde in range(vrijeme):
                # provjeravam je li lijevi susjed trazio vilicu, ako je prljava, saljem mu je
                probe = comm.iprobe(source=self.susjedi[0])
                if probe:
                    msg = comm.recv(source=self.susjedi[0])
                    if msg == 'Trazim vilicu' and self.vilice['L'] == 'Prljava':
                        self.vilice['L'] = 'Nema'
                        comm.send('Saljem vilicu', dest=self.susjedi[0], tag=0)
                        self.broj_vilica = self.izracunaj_broj_vilica()
                        
                # provjeravam je li desni susjed trazio vilicu, ako je prljava, saljem mu je   
                probe = comm.iprobe(source=self.susjedi[1])
                if probe:
                    msg = comm.recv(source=self.susjedi[1])
                    if msg == 'Trazim vilicu' and self.vilice['D'] == 'Prljava':
                        self.vilice['D'] = 'Nema'
                        comm.send('Saljem vilicu', dest=self.susjedi[1], tag=1)
                        self.broj_vilica = self.izracunaj_broj_vilica()
                time.sleep(1)
                    
            # provjeravam imam li obje vilice, ako ne, saljem zahtjeve pa cekam odgovore dok ne dobijem obje vilice
            if(self.broj_vilica != 2):
                if self.broj_vilica == 0:
                    print(i, i * '    ' + 'Trazim vilicu', flush=True)
                    comm.send('Trazim vilicu', dest=self.susjedi[0], tag=2)
                    print(i, i * '    ' + 'Trazim vilicu', flush=True)
                    comm.send('Trazim vilicu', dest=self.susjedi[1], tag=2)
                    time.sleep(1)
                elif self.broj_vilica == 1:
                    if(self.vilice['L'] == 'Nema'):
                        print(i, i * '    ' + 'Trazim vilicu', flush=True)
                        comm.send('Trazim vilicu', dest=self.susjedi[0], tag=2)
                    elif(self.vilice['D'] == 'Nema'):
                        print(i, i * '    ' + 'Trazim vilicu', flush=True)
                        comm.send('Trazim vilicu', dest=self.susjedi[1], tag=2)
                
                while(self.broj_vilica != 2):
                    # provjeravam je li lijevi susjed nesto poslao
                    probe = comm.iprobe(source=self.susjedi[0])
                    if probe:
                        msg = comm.recv()
                        if msg == 'Saljem vilicu':
                            self.vilice['L'] = 'Cista'
                            self.broj_vilica = self.izracunaj_broj_vilica() 
                        elif msg == 'Trazim vilicu':
                            if self.vilice['L'] == 'Prljava':
                                self.vilice['L'] == 'Nema'
                                comm.send('Saljem vilicu', dest=self.susjedi[0], tag=0)
                                self.broj_vilica == self.izracunaj_broj_vilica()
                        
                    # provjeravam je li desni susjed nesto poslao
                    probe = comm.iprobe(source=self.susjedi[1])
                    if probe:
                        msg = comm.recv()
                        if msg == 'Saljem vilicu':
                            self.vilice['D'] = 'Cista'
                            self.broj_vilica = self.izracunaj_broj_vilica()
                        elif msg == 'Trazim vilicu':
                            if self.vilice['D'] == 'Prljava':
                                self.vilice['D'] == 'Nema'
                                comm.send('Saljem vilicu', dest=self.susjedi[1], tag=1)
                                self.broj_vilica == self.izracunaj_broj_vilica()
                
            # jedem i vilice mi postaju prljave
            print(i, i * '    ' + 'Jedem...', flush=True)
            time.sleep(random.randint(2, 6))
            self.vilice = {'L' : 'Prljava', 'D' : 'Prljava'}
            
      
    def izracunaj_broj_vilica(self):
        broj = 2
        if self.vilice['L'] == 'Nema':
            broj -= 1
        if self.vilice['D'] == 'Nema':
            broj -= 1
        return broj
            
comm = MPI.COMM_WORLD
i = comm.Get_rank()
n = comm.Get_size()
filozof = Filozof(i, n)
filozof.start()