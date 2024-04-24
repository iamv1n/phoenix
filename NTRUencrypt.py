from sympy import symbols, invert, Poly, GF
from NTRUpy.NTRUutil import *
# from NTRUutil import *
import numpy as np

class NTRUencrypt:
    def __init__(self, N = 503, p = 3, q = 257, dr = 18):
        self.N = N
        self.p = p
        self.q = q
        self.dr = dr
        
        
        self.h = np.zeros((self.N,), dtype = int)
        self.m = np.zeros((self.N,), dtype = int)
        self.e = np.zeros((self.N,), dtype = int)
        self.r = np.zeros((self.N,), dtype = int)
        
        self.I = np.zeros((self.N+1,), dtype = int)
        self.I[self.N] = -1
        self.I[0] = 1
        
        self.hasKey = False
        
        self.Me = self.cipherText = None
    
    def setKey(self, pub):
        if len(pub)>self.N:
            raise ValueError("pub is too large")
        else:
            self.h = pub
            self.hasKey = True

    def setKeyFromStr(self, pub):
        pub.replace("\n", "")
        pub = pub.replace("  ", " ")
        pub = pub.replace("   ", " ")
        pub = pub.replace("    ", " ")
        pub = np.fromstring(pub, dtype=int, sep=" ")
        print(pub)
        self.setKey(np.array(pub, dtype=int))
        print("\n\n"+arr2str(self.h)+"\n\n")
    
    def genr(self):
        self.r = randPoly(self.N, self.dr)
    
    def encrypt(self, m=None):
        if not self.hasKey:
            raise ValueError("No key is set")
        if m is not None:
            if len(m)>self.N:
                raise ValueError("m is too large")
            self.m = m
        x=symbols('x')
        self.e = np.array((((Poly(Poly(self.r, x)*Poly(self.h, x), x).trunc(self.q)+Poly(self.m, x))%Poly(self.I, x)).trunc(self.q)).all_coeffs(), dtype=int)
        self.e = padArray(self.e, self.N)
        return self.e

    
    def encryptString(self, M):
        if not self.hasKey:
            raise ValueError("No key is set")
        # M="Hello world"
        bM = str2bit(M)
        bM = padArray(bM, len(bM) + (self.N - np.mod(len(bM), self.N)))
        self.Me=""
        for i in range(len(bM)//self.N):
            self.genr()
            self.m = bM[i*self.N:(i+1)*self.N]
            self.encrypt()
            self.Me += arr2str(self.e) + " "
        print(f"encrypted message is {self.Me}")
            

        
if __name__=="__main__":
    s="s"
    e=NTRUencrypt()
    e.setKeyFromStr("""-40 -72 -43 17 -150 97 -54 -33 19 -103 0 34 147 -31 -55 -154 108 -137 -86 67 -37 -126 7 -207 -213 110 -27 96 -47 -98 124 75 -155 -122 -157 -58 72 8 -27 50 -101 40 84 3 -32 -146 -23 -167 -55 129 -24 -140 -138 -181 -126 35 -28 -80 50 196 -182 22 -86 -56 -11 -120 -14 56 79 76 -99 17 -43 96 -60 -239 -21 28 -4 102 29 62 -60 -107 -59 -59 10 110 145 -92 161 -67 -23 140 56 49 9 163 -31 43 -66 -75 183 -70 -25 76 -95 -52 -113 184 112 83 114 -204 -42 64 163 51 82 -96 197 41 -100 223 -172 -161 -106 -120 4 29 -231 191 -6 10 78 -7 63 64 -16 -33 -28 -16 7 -151 -63 113 -128 -31 50 92 -143 -24 109 92 49 58 -71 -204 240 110 58 -148 13 -217 40 104 -20 123 -24 32 124 -60 242 -31 -29 -70 225 92 -116 131 6 48 -241 -170 30 198 -4 -132 -32 -29 -48 36 30 143 124 -3 142 128 -21 -28 -51 -96 -155 15 -128 15 -181 -59 -71 103 -25 -26 -59 133 62 -45 226 -161 198 25 16 53 -128 -174 -18 20 -141 108 77 -113 -48 145 -60 -91 -88 -84 -41 60 35 -12 -65 181 64 89 -60 -13 -64 171 -112 -184 27 -48 24 54 -123 170 -26 41 10 48 222 67 -12 -209 78 99 -49 -35 -25 49 -53 -9 -132 3 73 83 -119 91 103 -46 -25 -43 -157 141 -113 22 86 36 156 -168 142 96 -164 -61 -8 -141 -68 19 -28 -157 -64 -11 -182 13 103 -87 -171 -20 185 97 -133 190 -15 -10 68 33 118 -89 72 46 56 181 -94 38 86 169 -7 12 73 45 -106 -224 -5 105 -178 -73 -2 35 -7 -70 17 171 111 95 -80 -92 168 130 89 -94 -45 -1 -25 -10 154 -95 50 -71 9 -44 75 109 47 -106 79 86 -111 66 -169 -102 57 -92 -41 120 -193 189 -32 -132 -166 -85 -109 122 -92 61 44 -80 -122 -177 -245 -224 26 128 20 202 63 -161 -77 72 1 1 -56 53 -140 -39 177 -112 160 12 48 -58 -129 130 -49 12 27 -6 174 -81 46 -88 126 31 -134 -162 145 -67 -46 -48 171 -159 201 -84 -43 -82 84 -99 100 29 -2 -36 87 -15 113 150 -2 -158 51 62 -18 23 -120 90 -98 -102 -172 166 -19 -82 -10 -55 221 70 79 72 153 63 60 -145 72 -51 -16 -69 -9 -11 109 -107 137 65 13 -11 61 -179 6 230 156 -169 75 -15 -75 -197 -143 -88 -60 238 70 -127 58 -24 -142 64 105 -46 -63 """)
    e.encryptString("Hello world")