```
Kindle refer to original and official sources as this document is liable and prone to have errors.
```
## Ideals
Ideals are the Sub-rings with the following properties:
- Closed under addition
> [!Tip]
> $a,b ∈ I$
>
> $a+b ∈ I$
- Has the zero element.
> [!Tip]
> $0 ∈ I$
- absorbed under multiplication :
> [!Tip]
> $a ∈ I$
>
> $r ∈ R$ //where  R is the ring on which we have the Ideal I
>
> $ar, ra ∈ R$
4
## Coset
- #### Group
Given an element a of *G*, the **left cosets** of I in G are the sets obtained by adding each element of *I* by a fixed element a of *G* (where a is the left factor). In symbols these are,
> [!Tip]
> for I ≤ G
>
> $\bar{a} = a * I  = { a * x | x ∈ I }$

> [!caution]
> The operation performed here depends on the on the operation in the group, which in the above block is multiplication but can also be addition.
- #### Ring
The difference in cosets for Group and for Ring is mainly only the operation performed between a and ever element of I.
> [!Tip]
> TBC
## Principle Ideal
Principle ideal is a value operating on  all the elements of a  Commutative Ring.
> [!Tip]
> Let R be a commutative Ring and a∈R
> \<a\> = aR = { ra | r ∈ R }

> [!caution]
> Not to be confused with cosets as cosets are for Groups and Principal Ideal is for Rings.
> **There are other differences too which shall not be overlooked**

## Quotient Rings
Quotient Ring of R/I is a set of all the cosets such that
> [!Tip]
> R/I = {a̅} = { a * I : a ∈ R } = { { a \* x :  a ∈ I } : x ∈ R }
### Tip Explanation
Quotient out a Ring by an ideal means considering all elements in the Ring that are equivalent to each other modulo ideal's representative.
> [!Note]
> for Z[ x ] , I = { x<sup>N</sup> - 1 }
> I → all the multiples of x<sup>N</sup> - 1
> 
> Where,
> (Z[ x ]/I) → All the Elements of Z[ x ] which are equivalent on modulo a(x) \* (x<sup>N</sup> - 1) : a(x) \* (x<sup>N</sup> - 1) ∈ I
> [!Important] note
>  Each of these modulo classes are represented using the modulo (say f(x) in (Z[ x ]/I))
>
> ∴ Each class represented by f(x) satisfies :
> f(x) + a(x) \* (x<sup>N</sup> - 1) : f(x) = modulo ( a(x) \* (x<sup>N</sup> - 1) ), a(x) \* (x<sup>N</sup> - 1) ∈ I 
### Looking at the Properties of a ring held by This Quotient Ring
1. for any f(x), g(x) ∈ (Z[ x ]/I) 


## Polynomial Rings

## Euclidean Domain & Algorithm
Its contains:
- **Ring:** A commutative ring with an additional structure
- **Euclidean Function:** a function that maps all the members of the ring to non-negative integers or zero and satisfies the following:
	- Existence: This is also known as Euclidean Division Property
		```
		∀: a, b ∈ R | b ≠ 0
		∃: q, r ∈ R
		∋: a = bq + r | r=0 or f(r) < f(b)
		```
	- Monotonicity: The Euclidean function is non-negative and strictly decreasing, meaning that the Euclidean function of any element is strictly greater than the Euclidean function of any element obtained by applying the Euclidean Division Property
## Bézout Identity
The gcd of any two numbers a and b can be represented as follows:

$$
(a.x) + (b.y) = gcd(a, b)
$$

we can find the values of $x$ and $y$ by backward substituting the steps in the Euclidean algorithm for GCD.
