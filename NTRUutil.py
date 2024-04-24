from sympy import symbols, invert, poly, GF
import numpy as np
import math

# generate random numbers
# generate bits from a string

def isPrime(num):
    if num > 1:
        for i in range(2, int(math.sqrt(num))):
            if (num % i) == 0:
                return False
        else:
            return True
    else:
        return False    

def randPoly(N, df):
    if 2*df>=N:
        raise ValueError("df is too large")
    else:
        f = np.zeros((N,), dtype = int)
        for i in range((2*df)-1):
            if(i<df):
                f[i] = 1
            else:
                f[i] = -1
        np.random.shuffle(f)
        return f

def arr2str(L):
    return " ".join(str(x) for x in L)

def str2bit(s):
    # return np.array(list(bin(int.from_bytes(s.encode(),"big")))[2:], dtype=int)
    return np.array(list(bin(int.from_bytes(str(s).encode(),"big")))[2:],dtype=int)

def padArray(a, N):
    return np.pad(a, (N-len(a), 0))


def bit2str(bi):
    S = padArray(bi,len(bi)+np.mod(len(bi),8))
    
    # Convert the input binary array to a string and remove any spaces
    S = arr2str(bi)
    S = S.replace(" ", "")

    # Then take each 8 bit section on its own, starting from last bits (to avoid issues
    # that can arrise from padding the front of the array with 0's)
    charOut = ""
    print(S)
    # return
    for i in range(len(S)//8):
        # print(i*8)
        if i==0:
            charb = S[len(S)-8:]
        else:
            charb = S[-(i+1)*8:-i*8]
        charb   = int(charb,2)
        charOut = charb.to_bytes((charb.bit_length()+7)//8,"big").decode("utf-8",errors="ignore") + charOut
    return charOut


