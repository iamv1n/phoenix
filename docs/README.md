# Phoenix documentation

| If you want to… | Read |
| --- | --- |
| Encrypt something in five minutes | [Quickstart](quickstart.md) |
| Click around instead of writing code | [Playground](playground.md) |
| Use Phoenix from a shell | [Command line](cli.md) |
| Look up a function | [API reference](api.md) |
| Learn the algebra NTRU needs | [Mathematical background](math.md) |
| Understand NTRU itself, with a worked example | [The NTRU algorithm](algorithm.md) |
| See how raw NTRU becomes safe-to-use encryption | [KEM and sealing](kem-and-sealing.md) |
| Know what Phoenix does and does not protect against | [Security](security.md) |
| Parse a key or message yourself | [File formats](formats.md) |

Longer, more narrative pieces live in the [blog](../blog/README.md), and
every snippet in these pages has a runnable twin in [`examples/`](../examples).

> **Phoenix is a learning project.** It is unaudited and not constant time.
> Read [Security](security.md) before using it for anything that matters.

## Rendering the maths

Formulas are written as `$inline$` and as display blocks fenced by `$$` on
their own lines. That renders as-is on GitHub, in the VS Code Markdown
preview, and in any site generator with a maths plugin (MkDocs with
`pymdownx.arithmatex`, Docusaurus with `remark-math`, markdown-it with
KaTeX).

For a plain HTML page, load MathJax and tell it that single dollars delimit
inline maths:

```html
<script>
  MathJax = { tex: { inlineMath: [["$", "$"]], displayMath: [["$$", "$$"]] } };
</script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
```

The formulas stick to a subset of LaTeX that no Markdown parser mangles (no
`\,`, `\{`, `\\` and so on). `python tools/check_math.py` enforces it.
