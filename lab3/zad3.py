import numpy as np
import math
from time import time
import pyopencl as cl

def slijedni(scalefactor, numiter):
    print("Pozvan slijedni CFD algoritam.\n")
    tolerance, error, bnorm = 0.0, 0.0, 0.0
    bbase, hbase, wbase, mbase, nbase = 10, 15, 5, 32, 32
    checkerr = 0

    if tolerance >= 0.0:
        checkerr = 1

    if not checkerr:
        print("Scale Factor =", scalefactor, "broj iteracija =", numiter, "\n")
    else:
        print("Scale Factor =", scalefactor, "broj iteracija =", numiter, "tolerancija =", tolerance, "\n")

    printfreq = numiter / 10

    b = bbase * scalefactor
    h = hbase * scalefactor
    w = wbase * scalefactor
    m = mbase * scalefactor
    n = nbase * scalefactor

    # inic. polja
    psi = np.zeros(((m + 2) * (n + 2)), dtype=np.float32)
    psitmp = np.zeros(((m + 2) * (n + 2)), dtype=np.float32)

    for i in range(b + 1, b + w):
        psi[i * (m + 2) + 0] = i - b

    for i in range(b + w, m + 1):
        psi[i * (m + 2) + 0] = w

    for j in range(1, h + 1):
        psi[(m + 1) * (m + 2) + j] = w

    for j in range(h + 1, h + w):
        psi[(m + 1) * (m + 2) + j] = w - j + h

    for i in range(0, m + 2):
        for j in range(0, n + 2):
            bnorm += psi[i * (m + 2) + j] * psi[i * (m + 2) + j]

    bnorm = math.sqrt(bnorm)

    print("\nGlavna petlja...\n\n")
    start_time = time()

    for iter in range(1, numiter + 1):

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                psitmp[i * (m + 2) + j] = 0.25 * (psi[(i - 1) * (m + 2) + j] + psi[(i + 1) * (m + 2) + j] + psi[i * (m + 2) + j - 1] + psi[i * (m + 2) + j + 1])

        if checkerr or iter == numiter:
            deltasq = 0
            for i in range(1, m + 1):
                for j in range(1, n + 1):
                    tmp = psitmp[i * (m + 2) + j] - psi[i * (m + 2) + j]
                    deltasq += tmp * tmp
            error = math.sqrt(deltasq)
            error = error / bnorm

        if checkerr:
            if (error < tolerance):
                print("Konvergirao na iteraciji", iter)
                break

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                psi[i * (m + 2) + j] = psitmp[i * (m + 2) + j]

        if (iter % printfreq == 0):
            if not checkerr:
                print("Završena iteracija", iter)
            else:
                print("Završena iteracija", iter, "error = ", error)

    total_time = time() - start_time
    iter_time = total_time / numiter

    print("\ngotovo\n")
    print("Nakon", numiter, "iteracija, pogreška je ", error)
    print(numiter, "iteracija izvodilo se", total_time, "sekundi")
    print("To je", iter_time, "sekundi po iteraciji")

def paralelni(scalefactor, numiter):
    print("Pozvan paralelni CFD algoritam.\n")
    # G = int(input("Unesite broj jezgri za paralelno izvođenje:"))
    tolerance, error, bnorm = 0.0, 0.0, 0.0
    bbase, hbase, wbase, mbase, nbase = 10, 15, 5, 32, 32
    checkerr = 0

    if tolerance >= 0.0:
        checkerr = 1

    if not checkerr:
        print("Scale Factor =", scalefactor, "broj iteracija =", numiter, "\n")
    else:
        print("Scale Factor =", scalefactor, "broj iteracija =", numiter, "tolerancija =", tolerance, "\n")

    printfreq = numiter / 10

    b = bbase * scalefactor
    h = hbase * scalefactor
    w = wbase * scalefactor
    m = mbase * scalefactor
    n = nbase * scalefactor

    # koristimo jezgri koliko ima zadataka
    G = m * m
    print("Za paralelno izvođenje koristit će se", G, "jezgri")

    # inic. polja
    psi = np.zeros(((m + 2) * (n + 2)), dtype=np.float32)
    psinew = np.empty(((m + 2) * (n + 2)), dtype=np.float32)

    for i in range(b + 1, b + w):
        psi[i * (m + 2) + 0] = i - b

    for i in range(b + w, m + 1):
        psi[i * (m + 2) + 0] = w

    for j in range(1, h + 1):
        psi[(m + 1) * (m + 2) + j] = w

    for j in range(h + 1, h + w):
        psi[(m + 1) * (m + 2) + j] = w - j + h

    for i in range(0, m + 2):
        for j in range(0, n + 2):
            bnorm += psi[i * (m + 2) + j] * psi[i * (m + 2) + j]

    bnorm = math.sqrt(bnorm)

    code = """
        __kernel void cfd(
            __global float* psi,
            __global float* psinew,                
            const unsigned int m,   
            const unsigned int psi_len
            )
        {
            int gid = get_global_id(0) + 1;
            int g = get_global_size(0); 
            
            int i = (int) (gid / m) + 1;
            int j = gid % m;
            /* printf("Ja sam jezgra %d od %d, moj i je %d a j je %d\\n", gid, g, i, j); */
            psinew[i * (m + 2) + j] = 0.25 * (psi[(i - 1) * (m + 2) + j] + psi[(i + 1) * (m + 2) + j] + psi[i * (m + 2) + j - 1] + psi[i * (m + 2) + j + 1]);   
        }
        """

    print("\nGlavna petlja...\n\n")
    start_time = time()

    context = cl.create_some_context()
    queue = cl.CommandQueue(context)
    program = cl.Program(context, code).build()

    for iter in range(1, numiter + 1):
        buffer_psi = cl.Buffer(context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=psi)
        buffer_psinew = cl.Buffer(context, cl.mem_flags.READ_WRITE, psinew.nbytes)
        psi_len = np.int32(len(psi))
        m_np = np.int32(m)

        program.cfd(queue, (G,), None, buffer_psi, buffer_psinew, m_np, psi_len)
        queue.finish()
        cl.enqueue_copy(queue, psinew, buffer_psinew)

        if checkerr or iter == numiter:
            deltasq = 0
            for i in range(1, m + 1):
                for j in range(1, n + 1):
                    tmp = psinew[i * (m + 2) + j] - psi[i * (m + 2) + j]
                    deltasq += tmp * tmp
            error = math.sqrt(deltasq)
            error = error / bnorm

        if checkerr:
            if (error < tolerance):
                print("Konvergirao na iteraciji", iter)
                break

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                psi[i * (m + 2) + j] = psinew[i * (m + 2) + j]

        if (iter % printfreq == 0):
            if not checkerr:
                print("Završena iteracija", iter)
            else:
                print("Završena iteracija", iter, "error = ", error)

    total_time = time() - start_time
    iter_time = total_time / numiter

    print("\ngotovo\n")
    print("Nakon", numiter, "iteracija, pogreška je ", error)
    print(numiter, "iteracija izvodilo se", total_time, "sekundi")
    print("To je", iter_time, "sekundi po iteraciji")

if __name__ == '__main__':
    scalefactor = int(input("Unesite scalefactor:"))
    numiter = int(input("Unesite broj iteracija:"))
    slijedni(scalefactor, numiter)
    paralelni(scalefactor, numiter)