# Phoenix blog

Longer reads about lattice cryptography and about building this library.
They are meant to be read in order, but each stands alone.

1. [Why your encryption has an expiry date](01-why-post-quantum.md) —
   what quantum computers break, what they do not, and where lattices come in.
2. [NTRU by hand](02-ntru-by-hand.md) — the whole algorithm on seven
   coefficients, in a Python prompt, including what happens when you break
   the rules.
3. [From a maths trick to something you can use](03-from-textbook-to-usable.md) —
   three attacks on textbook NTRU and the layers that stop them.
4. [Rebuilding Phoenix](04-rebuilding-phoenix.md) — a post-mortem of the
   first version: twelve problems, and what each one teaches.

All code in these posts runs against the library as it is in this
repository. Reference material lives in the [docs](../docs/README.md).
