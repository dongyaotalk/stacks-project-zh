# Translation render directories

`template/` is the only hand-maintained directory here. It is a smoke-test book
for the complete Springer template and does not contain official translation.

Other direct child directories are generated render outputs for model lanes or
the canonical `reviewed` lane. They are ignored by Git and must be rebuilt from
`translation-data/` plus `config/models.yml`; they are not translation memory or
the source of truth.

A generated directory contains:

- `metadata.tex`: display name, provenance, status, and notice;
- `contents.tex`: ordered `\input` list of rendered chapters;
- `chapters/`: book-native chapter files beginning with `\chapter`;
- optional `frontmatter.tex`, `appendices.tex`, `backmatter.tex`, and `images/`.

Shared project front matter, bibliography, index, cover, and Stacks macros stay
outside generated model directories. Never repair a translation by editing the
generated TeX; fix structured data or the renderer and rebuild it.
