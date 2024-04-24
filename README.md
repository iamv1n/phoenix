# PHOENIX
Phoenix represents a significant advancement in encryption technology, particularly in the context of post-quantum computing challenges. Leveraging the principles of NTRU lattice-based cryptography, Phoenix offers a resilient framework for securing digital communications in an era where traditional encryption methods may be vulnerable to quantum attacks. Its innovative approach ensures robust protection against evolving threats, making it a promising solution for safeguarding sensitive information in a rapidly changing digital landscape. 

## Table of contents 
- [What is NTRU?](#what-is-ntru)
- [Usage of this Python Module](#module-usage)
- [Docs](#other-docs)
	- [Algorithm](./Docs/NTRU%20Algorithm.md)
	- [Mathematical Requirements](./Docs/Required%20Mathematics%20for%20NTRU.md)


## What is NTRU?
[NTRU](https://en.wikipedia.org/wiki/NTRU), short for Nth degree TRUncated polynomial, is a lattice-based cryptographic algorithm used for public-key encryption and key exchange. Unlike traditional public-key algorithms such as RSA or ECC, which rely on the difficulty of factoring large numbers or solving elliptic curve discrete logarithm problems, NTRU's security is based on the mathematical properties of lattice problems. These problems are believed to be resistant to attacks from both classical and quantum computers. NTRU offers advantages such as fast key generation, small key sizes, and efficient performance, making it a compelling choice for post-quantum cryptography applications.


## Need for a different (Post-Quantum) Cryptographic System.
The need for post-quantum cryptographic systems arises from the threat posed by quantum computers to conventional encryption methods. Quantum computers could efficiently break widely-used algorithms like RSA and ECC, compromising data security. Post-quantum cryptography, based on principles resistant to quantum attacks, offers a crucial solution. Transitioning to these systems ensures data security against evolving quantum computing capabilities, safeguarding sensitive information in the long term.


### Problem
The emergence of [Shor's Algorithm](https://en.wikipedia.org/wiki/Shor%27s_algorithm#:~:text=%22Shor's%20algorithm%22%20usually%20refers%20to,of%20the%20hidden%20subgroup%20problem.) signals the dawn of quantum computing, challenging the security of established encryption techniques like RSA and ECC through its rapid factorization of large integers. The imperative for post-quantum cryptography intensifies as organizations seek to safeguard sensitive data. Crafting effective solutions demands addressing complexities in resilience, efficiency, and compatibility, necessitating interdisciplinary collaboration.

### Solution

The solution is to come up with a different Cryptographic System which is based on either a different NP-Hard Problem or a completely different mathematical paradigm which maps the plain-text to the cipher-text in a manner which is not traceable.
## Module Usage
TBC
## Other Docs
- [NTRU Algorithm](./Docs/NTRU%20Algorithm.md)
	- Key-Generation
	- Encryption
	- Decryption

## Contributing
Contributions are welcome! If you'd like to contribute to this project, please follow these steps:

1. Fork this repository.
2. Create a new branch (git checkout -b feature)
3. Make your changes.
4. Commit your changes (git commit -am 'Add new feature')
5. Push to the branch (git push origin feature)
6. Create a new Pull Request.

## Support
If you encounter any issues or have questions about this project, feel free to [contact me](mailto:mail@vineet.site) or [open an issue](https://github.com/iamv1n/phoenix/issues/new).

## License
This project is licensed under the [GNU General Public License v3.0](./LICENSE). You are free to use and modify this project as needed.