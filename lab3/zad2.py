import pyopencl as cl
import numpy as np
from time import time

if __name__ == '__main__':
    code = """
    __kernel void pi(
        __global int* niz,        
        __global int* broj_prim,
        const unsigned int niz_len
        )
    {
        int gid = get_global_id(0);
        int g = get_global_size(0);
        int broj_zadataka = (int) ceil((float) niz_len / g);
        if (gid == 0) {
            broj_prim[0] = 0;
        }
        if (gid < niz_len)
        {
            for(int zad = 0; zad < broj_zadataka; zad++){
                int prim = 1;
                if(gid * broj_zadataka + zad >= niz_len) break;
                int n = niz[gid * broj_zadataka + zad];
                if (n == 1) {
                    prim = 0;
                }
                if(!(n == 2 || n == 3)) {
                    int m = n/2;  
                    for(int i = 2; i <= m; i++)  
                    {  
                        if(n % i == 0)  
                        {  
                            prim = 0;
                            break;  
                        }  
                    }  
                }
                atomic_add(broj_prim, prim);
            }
        }     
    }
    """

    context = cl.create_some_context()
    queue = cl.CommandQueue(context)
    program = cl.Program(context, code).build()

    N = int(input('Unesite broj elemenata niza:'))
    G = int(input('Unesite G:'))

    niz = np.arange(1, N + 1, 1, dtype='int32')
    niz_len = np.int32(len(niz))
    broj_prim = np.empty((1), dtype='int32')

    buffer_niz = cl.Buffer(context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=niz)
    buffer_broj_prim = cl.Buffer(context, cl.mem_flags.READ_WRITE, broj_prim.nbytes)

    start_time = time()
    # paralelni dio
    program.prim(queue, (G,L), None, buffer_niz, buffer_broj_prim, niz_len)
    queue.finish()
    cl.enqueue_copy(queue, broj_prim, buffer_broj_prim)
    # kraj paralelnog dijela
    run_time = time() - start_time

    print('Broj prim brojeva u prvih', N, 'brojeva: ', broj_prim)
    print('Rješenje pronađeno u', run_time, 'sekundi')