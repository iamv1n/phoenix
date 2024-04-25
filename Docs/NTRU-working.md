# The NTRU Cryptosystem

The NTRU cryptosystem was developed in 1996 by Hoffstein, Pipher, and Silverman. NTRU is a public key cryptosystem not based on factorization or discrete logarithm problems. NTRU is based on the shortest vector problem in a lattice. The NTRU public key cryptosystem is one of the fastest known public key cryptosystems. NTRU works in the ring of truncated polynomials

$$ R_q = \mathbb{Z}_q[X] / (X^N - 1) $$

where $N$ is a fixed positive integer and $b{Z}_q$ denotes the ring of integers modulo $q$. In this ring, a polynomial $f$ can be written as

$$ f = (f_0, f_1, \ldots, f_{N-1}) = \sum_{k=0}^{N-1} f_k X^k $$

The addition of two polynomials $f = (f_0, f_1, \ldots, f_{N-1})$ and $g = (g_0, g_1, \ldots, g_{N-1})$ is defined as pairwise addition of the coefficients of the same degree, that is

$$ f + g = (f_0 + g_0, f_1 + g_1, \ldots, f_{N-1} + g_{N-1}) $$

The multiplication of two polynomials $f$ and $g$ is given by a convolution multiplication as follows

$$ f \star g = h = (h_0, h_1, \ldots, h_{N-1}), \text{ where } h_k = \sum_{i + j \equiv k \mod N} f_i g_j $$

As an example, let us compute

$$ (x^4 + 2x^3 + 3) \star (x^4 + 3x^2 + x + 2) = x^8 + 2x^7 + 3x^6 + 7x^5 + 7x^4 + 4x^3 + 9x^2 + 3x + 6 $$

In the polynomial ring $\mathbb{Z}_3[X] / (X^5 - 1)$, it can be written as

$$ x^3 + 2x^2 + 3x + 7 + 7x^4 + 4x^3 + 9x^2 + 3x + 6 = x^4 + 2x^3 + 2x^2 + 1 $$

For a given positive integer $d$, define the set

$$ B(d) = \left \{ \sum_{k=0}^{N-1} f_k X^k : f_i = 0 \text{ or } 1, \sum_{k=0}^{N-1} f_k = d \right \} $$


In NTRU, the parameters are chosen as follows:

- $N$ is a sufficiently large prime,
- $p$ and $q$ are relatively prime numbers such that $q$ is much larger than $p$.
- $d_f$, $d_g$, and $d_r$ are integers such that the polynomials from which the private keys are selected are from the set $B(d_f)$ and $B(d_g)$.
- The set $B(d_r)$ contains the polynomials from which the blinding value used during encryption is selected.

 - $Z_p[X] / (X^N - 1)$
is the plaintext space.


# Key Generation in NTRU Cryptosystem

To generate keys in the NTRU cryptosystem:

1. **Choose Polynomials**:
   - Randomly select a polynomial $f$ from the set $B(d_f)$ such that $f$ has an inverse modulo $p$ and $q$. To Generate and Check if $f$ inverse modulo $p$ and $q$ exits we use [Bezouts Identity](./Generate_poly_Inverse.md).
   - Set $f_p \equiv f^{-1} \pmod{p}$ and $f_q \equiv f^{-1} \pmod{q}$.
   - Randomly choose a polynomial $g$ from the set $B(d_g)$.

2. **Compute $h$**:
   - Compute $h \equiv g \star f_q \pmod{q}$.

3. **Generate Keys**:
   - Public Key: $(N, h)$
   - Private Key: $(f, f_p)$


# Encryption in NTRU Cryptosystem

To encrypt a message in the NTRU cryptosystem:

1. **Message Representation**:
   - Represent the message as a polynomial $m$ from the plaintext space.

2. **Choose Blinding Polynomial**:
   - Randomly choose a polynomial $r \in B(d_r)$.

3. **Encrypt Message**:
   - Encrypt $m$ using the following rule:
    $e \equiv p \star r \star h + m \pmod{q}$


<br>

# Decryption Steps in NTRU Cryptosystem

To decrypt a ciphertext in the NTRU cryptosystem, follow these steps:

1. **Compute $a$**:
   - Compute $a \equiv f \star e \pmod{q}$.

2. **Transform $a$**:
   - Transform $a$ to a polynomial with coefficients in the interval $[-q/2, q/2]$.

3. **Compute $m$**:
   - Compute $m \equiv f_p \star a \pmod{p}$.




<hr>
<br>

To check the computation and understand why the decryption procedure works, let's break down the steps:

We have:

$$
\begin{align*}
a &\equiv f \star e \pmod{q} \\
&\equiv f \star (p \star r \star h + m) \pmod{q} \\
&\equiv p \star r \star g \star f \star f_q + f \star m \pmod{q} \\
&\equiv p \star r \star g + f \star m \pmod{q}.
\end{align*}
$$

We obtain that:

$$
\begin{align*}
f_p \star a \pmod{p} &\equiv (p \star r \star g + f \star m) \star f_p \pmod{p} \\
&\equiv m \pmod{p}.
\end{align*}
$$

## Example of NTRU Cryptosystem

To illustrate the NTRU encryption/decryption, let's consider an example with:

- $N = 7$
- $p = 3$
- $q = 41$
- $f = X^6 - X^4 + X^3 + X^2 - 1$
- $g = X^6 + X^4 - X^2 - X$
- $m = -X^5 + X^3 + X^2 - X + 1$
- $r = X^6 - X^5 + X - 1$

Here, we get:

- $f_p = X^6 + 2X^5 + X^3 + X^2 + X + 1$
- $f_q = 8X^6 + 26X^5 + 31X^4 + 21X^3 + 40X^2 + 2X + 37$
- $h = 19X^6 + 38X^5 + 6X^4 + 32X^3 + 24X^2 + 37X + 8$
- $e = 31X^6 + 19X^5 + 4X^4 + 2X^3 + 40X^2 + 3X + 25$.

This computation demonstrates the encryption and decryption process in the NTRU cryptosystem.


<!-- ## Lattice-Based Attack on NTRU

The public key satisfies:

$$
h \equiv g \star f_q \pmod{q}
$$

Hence, we have that:

$$
f \star h \equiv g \pmod{q}
$$

Consider the lattice defined by:

$$
\Lambda = \{(F_1, F_2) \in \mathbb{R}_q \times \mathbb{R}_q : F_1 \star h \equiv F_2 \pmod{q}\}
$$

Obviously, $(f, g) \in \Lambda$. The relation $f \star h \equiv g \pmod{q}$ can be written as:

$$
f \star h - u \star q = g
$$

for some $u \in \mathbb{R}_q$. The above equation is the same as:

$$
\begin{pmatrix}
f_0 & f_1 & \cdots & f_{N-1} & g_0 & g_1 & \cdots & g_{N-1} \\
\end{pmatrix}
=
\begin{pmatrix}
1 & 0 & \cdots & 0 & 0 & 0 & \cdots & 0 \\
0 & 1 & \cdots & 0 & 0 & 0 & \cdots & 0 \\
\vdots & \vdots & \ddots & \vdots & \vdots & \vdots & \ddots & \vdots \\
0 & 0 & \cdots & 1 & 0 & 0 & \cdots & 0 \\
0 & 0 & \cdots & 0 & h_0 & h_1 & \cdots & h_{N-1} \\
h_0 & h_1 & \cdots & h_{N-1} & q & 0 & \cdots & 0 \\
0 & 0 & \cdots & 0 & h_{N-1} & h_0 & \cdots & h_{N-2} \\
0 & q & \cdots & 0 & 0 & 0 & \cdots & 0 \\
\end{pmatrix}
\begin{pmatrix}
f_0 & f_1 & \cdots & f_{N-1} \\
-g_0 & -g_1 & \cdots & -g_{N-1} \\
\end{pmatrix}
$$

Let us remark that the coefficients of the polynomials $f$ and $g$ are small; therefore, $(f, g)$ is a short vector in the lattice $\Lambda$. That is, the LLL-algorithm can be applied. Let us apply the above ideas in the case of the example we considered.
 -->
