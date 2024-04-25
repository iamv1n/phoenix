## Generate Inverses of $f$ over coefficient ring modulo $p$ and $q$
Use Bézout's Identity to generate the inverse:
if in the Bézout's identity: 

$$
(a.x) + (b.y) = gcd(a, b)
$$

we place 

$$
a.x = f(x).f'(x) \\
$$

$$
b.y = a(x).(x^N -1)
$$

such that the GCD is 1.

hence we get,

$$
f(x).f'(x) + a(x).(x^N -1) = 1 
$$

here we have 

$$
a(x).(x^N -1) = I
$$

where $I$ is the ideal of the Quotient Ring that we are working with.
As Ideal are congruent to 0 in a quotient Ring we may simply write:

$$
f(x).f'(x) = 1
$$

thus meaning $f'(x)$ is the inverse of $f(x)$.
> [!Note]
> To find inverse of the polynomial we have to use the Bézout's identity.
> Where the Euclidean algorithm will be used on $f(x)$ and $x^N - 1$ with $GCD = 1$ thus giving us the values for $f'(x)$ and $a(x)$