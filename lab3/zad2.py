import pyopencl as cl
import numpy as np
from time import time

if __name__ == '__main__':
    code = """
    __kernel void pi(
        __global int* niz,
        __global float* mypi,       
        const unsigned int niz_len
        )
    {
        int gid = get_global_id(0);
        int g = get_global_size(0);
        int broj_zadataka = (int) ceil((float) niz_len / g);
        if (gid < niz_len)
        {
            float h = 1.0 / (float) niz_len;
            for(int zad = 0; zad < broj_zadataka; zad++){
                if(gid * broj_zadataka + zad >= niz_len) break;
                int i = niz[gid * broj_zadataka + zad];
                float x = h * ((float) i - 0.5);
                mypi[gid * broj_zadataka + zad] = 4.0 / (1.0 + x * x);
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
    mypi = np.empty((N,), dtype='float32')

    buffer_niz = cl.Buffer(context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=niz)
    buffer_pi = cl.Buffer(context, cl.mem_flags.READ_WRITE, mypi.nbytes)

    start_time = time()
    # paralelni dio
    program.pi(queue, (G,), None, buffer_niz, buffer_pi, niz_len)
    queue.finish()
    cl.enqueue_copy(queue, mypi, buffer_pi)
    # kraj paralelnog dijela
    run_time = time() - start_time

    # ovaj dio je u glavnom programu jer atomic_add ne podrzava float
    sum = 0.0
    for x in mypi:
        sum += x

    sum /= N

    print('Aproksimacija Pi za N =', N, ':', sum)
    print('Rješenje dobiveno u', run_time, 'sekundi')