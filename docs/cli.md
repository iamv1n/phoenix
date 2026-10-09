# Command line

Installing Phoenix adds a `phoenix` command (also available as
`python -m phoenix`).

```console
$ phoenix --help
usage: phoenix [-h] [--version] {keygen,encrypt,decrypt,info,params,playground} ...
```

Every command exits with status 0 on success and 1 on failure, printing
`phoenix: error: …` to standard error.

## `phoenix keygen`

```console
$ phoenix keygen -o alice
public key:  alice.pub
private key: alice.key  (keep this secret)
```

| Option | Meaning |
| --- | --- |
| `-o, --out NAME` | Write `NAME.pub` and `NAME.key` (default `phoenix`) |
| `-p, --params SET` | Parameter set (default `phoenix677`) |
| `-f, --force` | Overwrite existing files |

Both files are PEM-style text. The private key is created with mode `0600`.
Without `--force`, `keygen` refuses to overwrite either file, so you cannot
destroy a key by re-running a command from your history.

## `phoenix encrypt`

```console
$ phoenix encrypt -k alice.pub -i note.txt -o note.phx
```

| Option | Meaning |
| --- | --- |
| `-k, --key FILE` | Recipient's public key (required) |
| `-i, --input FILE` | Plaintext; `-` or omitted reads standard input |
| `-o, --output FILE` | Destination; `-` or omitted writes standard output |
| `-a, --armor` | Write base64 text instead of binary |
| `--aad TEXT` | Associated data to authenticate alongside the message |

The whole input is read into memory and sealed as one message.

## `phoenix decrypt`

```console
$ phoenix decrypt -k alice.key -i note.phx
meet me at the old bridge
```

| Option | Meaning |
| --- | --- |
| `-k, --key FILE` | Your private key (required) |
| `-i, --input FILE` | Sealed message, binary or armored (detected automatically) |
| `-o, --output FILE` | Destination; defaults to standard output |
| `--aad TEXT` | The associated data given when encrypting |

Nothing is written unless the message authenticates:

```console
$ phoenix decrypt -k alice.key -i note.phx --aad wrong
phoenix: error: message authentication failed
$ phoenix decrypt -k alice.pub -i note.phx
phoenix: error: expected a phoenix private key, got a phoenix public key
```

## Pipes

`encrypt` and `decrypt` default to standard input and output, so they compose:

```console
$ tar cz project/ | phoenix encrypt -k alice.pub > project.tgz.phx
$ phoenix decrypt -k alice.key < project.tgz.phx | tar xz
$ echo hi | phoenix encrypt -k alice.pub --armor
-----BEGIN PHOENIX MESSAGE-----
UEhOWAEDAqUDAAAIAAB/AH8Afysum8M2jo2tREb8iputqGK7qZhPHJjD3G7PHeNjG7xkP1R5WdG9
...
```

## `phoenix info`

Describes a key or sealed message without needing any key:

```console
$ phoenix info note.phx
type:       sealed message
parameters: phoenix677 (N=677, p=3, q=2048, df=127, dg=127, dr=127)
size:       992 bytes
plaintext:  26 bytes
```

Note what this shows: the plaintext *length* is visible to anyone holding the
ciphertext. Pad your messages if their length is sensitive.

## `phoenix params`

```console
$ phoenix params
name            N  p     q   df   dg   dr  pk bytes  ct bytes
phoenix509    509  3  2048  127  127  127       719       700
phoenix677    677  3  2048  127  127  127       950       931  (default)
phoenix821    821  3  4096  255  255  255      1251      1232
toy             7  3    41    2    2    2        25         6
```

## `phoenix playground`

Starts the local web [playground](playground.md).

| Option | Meaning |
| --- | --- |
| `--port N` | Port to listen on (default 8765) |
| `--no-browser` | Do not open a browser window |
