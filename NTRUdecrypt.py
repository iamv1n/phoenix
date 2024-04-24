from sympy import symbols, invert, poly, GF, Poly
from NTRUpy.NTRUutil import *
# from NTRUutil import *
import numpy as np


# generate keys
    # generate f, inverse of fmodp and fmodq, g, h
# inverse of fmodp and fmodq
# inverse of polynomial

class NTRUdecrypt:
    def __init__(self, N = 503, p = 3, q = 257, df = 61, dg = 20, dr = 18):
        self.N = N
        self.p = p
        self.q = q
        self.df = df
        self.dg = dg
        self.dr = dr
        
        self.f = np.zeros((self.N,), dtype = int)
        self.fp = np.zeros((self.N,), dtype = int)
        self.fq = np.zeros((self.N,), dtype = int)
        self.g = np.zeros((self.N,), dtype = int)
        self.h = np.zeros((self.N,), dtype = int)
        
        self.I = np.zeros((self.N+1,), dtype = int)
        self.I[self.N] = -1
        self.I[0] = 1

    # setting the values of f, p, q, df, dg, dr
    def setNpq(self, N = None, p = None, q = None, df = None, dg = None, dr = None):
        if N is not None:
            if (not isPrime(N)):
                raise ValueError("N must be a prime number")
            else:
                if df is None:
                    if self.df*2 >= N:
                        raise ValueError("Input df if too small than the default N")
                    else:
                        self.df = df
                if dg is None:
                    if self.dg*2 >= N:
                        raise ValueError("Input dg if too small than the default N")
                    else:
                        self.dg = dg
                if dr is None:
                    if self.dr*2 >= N:
                        raise ValueError("Input dr if too small than the default N")
                    else:
                        self.dr = dr
                self.N = N
                
                # setting the respective polynomial arrays
                self.f = np.zeros((self.N,), dtype = int)
                self.fp = np.zeros((self.N,), dtype = int)
                self.fq = np.zeros((self.N,), dtype = int)
                self.g = np.zeros((self.N,), dtype=int)
                self.h = np.zeros((self.N,), dtype=int)
                self.I = np.zeros((self.N+1,), dtype = int)
                self.I[self.N] = -1
                self.I[0] = 1
                
                
        if p is not None and q is not None:
            if (not isPrime(p) or not isPrime(q) or p*8>q or math.gcd(p, q) != 1):
                raise ValueError("Invalid values for p or q")
            else:
                self.p = p
                self.q = q
        if df is not None:
            if df*2 >= self.N:
                raise ValueError("Input df if too small than the N")
            else:
                self.df = df
        if dg is not None:
            if dg*2 >= self.N:
                raise ValueError("Input dg if too small than the N")
            else:
                self.dg = dg
        if dr is not None:
            if dr*2 >= self.N:
                raise ValueError("Input dr if too small than the N")
            else:
                self.dr = dr

    def invf(self, f, I, modulo):
        print("inside invf", modulo)
        print(len(I))
        x=symbols('x')
        ff=Poly(f, x)
        II=Poly(I, x)
        if(isPrime(modulo)):
            try:
                return np.array(poly(invert(ff.as_expr(), II.as_expr(), domain=GF(modulo,symmetric=False))).all_coeffs(), dtype=int)
            except:
                # print("not isPrime(modulo)")
                return np.array([])
        else:
            return np.array([])


    # generate polynomials f, g, fp, fq (Private Keys)
    def genfg(self):
        print("inside genfg")
        maxTries=100
        #  we don't care about invertability of g
        self.g = randPoly(self.N, self.dg)
        # for testing purposes we fix our parameters and check other values
        # self.g = np.array([-1, 0, 0, 0, 0, -1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, -1, 1, 0, 1, 0, 0, -1, 0, 0, 1, 0, 0, 0, 0, 1, -1, -1, -1, 0, -1, 0, 0, 0, 0, 0, 0, -1, 1, 1, 0, -1, 0, 1, 0, 0, 0, 1, 0, 0, 1, -1, 0, 1, 0, 0, 0, -1, 0, -1, 0, 0, 0, 0, 0, 0, 1, 0, 1, -1, 0, 0, 0, 0, 0, -1, 0, 0, 0, 1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, -1, 0, 0, -1, 0, 1, 0, -1, 0, 0, -1, 1, 0, 1, 0, 0, 0, 0, -1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, -1, 0, 0, 0, 0, 0, 1, 1, -1, 0, 1, -1, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, -1, 0, -1, 0, -1, 0, -1, 1, 0, 0, 0, 0, 0, -1, 0, 0, -1, 1, 0, 0, 0, -1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, -1, 0, 0, -1, -1, 0, 0, 0, 0, -1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, -1, 1, -1, 0, 0, 0, 0, 0, -1, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, -1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, -1, 0, 0, 0, 0, 0, 1, 0, 0, -1, 0, 0, 0, 0, 1, 1, 0, 0, -1, 1, 0, -1, 0, 0, 1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, -1, 0, 0, 0, 0, 0, 1, -1, 0, 0, 0, 1, -1, 0, 0, -1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, -1, 0, 0, 1, -1, 0, 0, 0, 1, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, -1, 0, 1, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, -1, 0, 0, 1, 0, -1, -1, 0, 0, -1, 0, -1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, -1, 0, -1, 0, -1, 1, -1, 0, 0], dtype=int)
        # we generate f until we find one that is invertible mod p and q
        
        temp_fq = np.zeros((self.N,), dtype = int)
        temp_fp = np.zeros((self.N,), dtype = int)
        for i in range(maxTries):
            temp_f = randPoly(self.N, self.df)
            # for testing purposes we fix our parameters and check other values
            # temp_f=np.array([0, 0, 0, 0, -1, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, -1, -1, 0, 0, 0, -1, 1, 0, 1, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 1, 0, 0, 0, 0, 0, 1, -1, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, -1, -1, 0, 1, 0, 0, 0, 0, -1, 0, 0, -1, 0, 0, 0, -1, -1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, -1, 0, -1, 0, -1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, -1, -1, 1, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, -1, 0, 0, 0, 0, -1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, -1, 0, 1, -1, 0, 0, 1, 0, 0, 0, 1, -1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, -1, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, -1, 0, 0, 1, 0, 0, 0, 1, 1, 0, -1, 0, 0, 0, 0, 0, -1, 0, -1, 0, 0, 0, 0, 1, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, -1, 0, 0, -1, 0, -1, -1, 0, -1, -1, -1, 0, 0, -1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, -1, 0, 0, 1, -1, 0, 0, 0, 1, 0, 0, 1, -1, 0, 0, 0, 0, -1, 1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, -1, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, -1, 0, 1, 0, 0, 0, 1, 0, 0, 0, -1, -1, 0, 1, -1, 0, 0, -1, 1, 0, 0, 0, 1, 0], dtype=int)
            temp_fp = self.invf(temp_f, self.I, self.p)
            temp_fq = self.invf(temp_f, self.I, self.q)
            print(f"temp_fp: {len(temp_fp)}\ttemp_fq: {len(temp_fq)}")
            if len(temp_fp) != 0 and len(temp_fq) != 0:
                self.f=temp_f
                self.fp=temp_fp
                self.fq=temp_fq
                if(len(self.fp) < self.N):
                    self.fp = np.concatenate([np.zeros(self.N-len(self.fp),dtype=int),self.fp])
                    # self.fp = np.concatenate((temp_fp, np.zeros((self.N-len(temp_fp),), dtype = int)))
                if (len(self.fq) < self.N):
                    self.fq = np.concatenate([np.zeros(self.N-len(self.fq),dtype=int),self.fq])
                    # self.fq = np.concatenate((temp_fq, np.zeros((self.N-len(temp_fq),), dtype = int)))
                break
    
    # generate polynomial h (Public Key)
    def genh(self):
        print("inside genh")
        x = symbols("x")
        self.h = np.array(Poly((Poly(self.p*self.fq,x).trunc(self.q)*Poly(self.g,x)).trunc(self.q)%Poly(self.I,x)).all_coeffs(), dtype=int)
        # print("h", arr2str(dec.h), len(dec.h), end="\n\n")

    # generate the keys
    def genKeys(self):
        self.genfg()
        self.genh()

    def Keys2Str(self):
        return f"f: {arr2str(self.f)}\nfp: {arr2str(self.fp)}\nfq: {arr2str(self.fq)}\ng: {arr2str(self.g)}", f"{arr2str(self.h)}"
    
    def decrypt(self, e):
        # x=symbols('x')
        # a = (Poly(Poly(self.f, x)*Poly(e, x), x)%Poly(self.I, x)).trunc(self.q)
        # b = a.trunc(self.p)
        # c = (Poly(Poly(self.fq, x)*Poly(b, x), x)%Poly(self.I, x)).trunc(self.p)
        
        x = symbols('x')
        a = ((Poly(self.f,x)*Poly(e,x))%Poly(self.I,x)).trunc(self.q)
        b = a.trunc(self.p)
        c = ((Poly(self.fp,x)*b)%Poly(self.I,x)).trunc(self.p)
        print(c)
        
        return np.array(c.all_coeffs(), dtype=int)
     
    def decryptString(self, Me):
        print("inside decryptString")
        Me = np.fromstring(Me, dtype=int, sep=' ')
        if(np.mod(len(Me), self.N) != 0):
            raise ValueError("Invalid length of Me")
        
        Marr = np.array([], dtype=int)
        # print(Me)
        for D in range(len(Me)//self.N):
            Marr = np.concatenate((Marr, padArray(self.decrypt(Me[D*self.N:(D+1)*self.N]), self.N)))
        
        print("Marr", arr2str(Marr), len(Marr), end="\n\n")
        self.M = bit2str(Marr)
        return self.M
    
if __name__ == "__main__":
    dec=NTRUdecrypt()
    dec.genfg()
    dec.genh()
    dec.decryptString(" -52 36 74 -53 -128 95 -26 63 2 35 108 -44 106 -90 -91 -10 -116 -44 -112 30 15 82 -126 3 -72 47 48 -48 75 -116 -27 113 45 21 -49 -44 42 34 -41 -83 12 -51 72 122 111 80 -83 -39 -9 78 64 67 119 -53 128 28 -41 -41 46 8 12 -43 -99 -95 -84 -98 51 -36 -28 5 -10 -35 0 -104 -36 -104 38 111 115 -47 12 -109 25 76 -118 32 22 53 17 117 -108 -26 -66 99 68 -12 99 68 65 -4 -89 45 44 -7 27 -98 103 19 111 74 82 -48 -68 121 -118 17 83 42 -66 91 7 -50 -53 22 15 84 16 57 0 -94 -56 -91 76 -98 -59 -20 85 77 -61 114 -122 72 -113 32 -72 84 122 72 -82 6 -43 89 101 94 -81 4 -127 -20 5 -55 -55 56 68 1 -76 -106 20 28 -53 74 34 -3 -22 -17 -84 114 -104 -28 40 -103 -32 -97 -95 125 -87 -105 28 107 -39 -46 128 -75 15 -9 124 4 75 -49 -9 -110 30 -33 -126 95 -89 108 -102 19 4 -11 -51 -36 89 -106 -75 74 -115 97 102 14 69 -84 -115 -86 108 38 -50 115 116 77 -67 -99 94 -24 -59 74 74 120 107 -9 -61 -87 53 -45 -107 -95 -6 -84 127 -117 -107 -69 13 2 -67 -106 79 36 -34 -108 -102 76 52 -66 -45 -123 10 -112 3 32 -28 -64 -126 -27 -61 112 -76 -5 -25 127 80 123 -92 39 -104 -2 18 -94 34 -18 -8 -80 57 -121 99 26 38 -20 120 -50 -91 -84 -83 18 71 32 19 4 -21 22 -41 -48 104 43 -79 41 91 -52 72 3 -98 -110 -73 108 72 115 5 -55 100 8 103 3 61 48 -20 36 78 10 -124 -103 -15 -102 -52 -103 -79 115 50 -28 65 -86 6 97 36 -5 16 38 51 56 16 59 -44 -68 -63 23 -24 -90 -118 -64 -74 13 -91 -58 104 -113 -92 -61 -106 126 -29 -47 127 -59 123 -126 -89 -99 35 118 -42 -96 -53 55 105 -97 -99 85 54 -6 -94 99 -61 -118 -126 -90 0 -72 -53 42 77 120 11 -113 110 -101 47 84 -102 84 -77 -114 -78 -128 -12 -87 20 -13 -42 -22 82 84 -19 -67 69 99 95 106 -46 -116 -52 108 86 103 114 23 24 -39 50 58 -44 43 -101 -119 7 88 99 -38 -70 53 57 -44 15 57 106 16 124 56 100 -45 5 -24 50 68 -98 9 -100 79 -42 -28 51 -99 109 26 46 86 125 -106 -103 -7 -63 120 99 -35 113 -92 -12 -40 84 82 -3 108 -67 102 -46 ")
    print(dec.M)