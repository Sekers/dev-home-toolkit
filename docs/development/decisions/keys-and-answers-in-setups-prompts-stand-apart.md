# Keys and answers in setup's prompts stand apart

**Decision:** wherever setup's console text names a key to type or an answer, it's in single
quotes, and green at a console that shows color, through `console.key`: such as `'a' to go through
them all`, `Type 'y' or 'n'.`, and `A 'yes' sets up dev-home's skills and rules there.` The hint
in brackets stays as it is, such as `[Y/n]`, and so does Enter, a key's name.

**Why:** a key that's a lone letter, or an answer used as a word, reads as part of the sentence:
in "a to go through them all", the a looks like the article (the developer, 2026-10-16). Quotes
set it apart everywhere: with `NO_COLOR`, in copied or logged text, and for people who can't
tell green apart. Terraform's "Only 'yes' will be accepted to approve." marks an answer the same
way. Green matches the menu's numbers, the other thing a person types there.

**Options set aside:**

- Capital letters: in a hint, the capital already marks what Enter gives, such as `[Y/n]`.
- Brackets: they already hold the hint, and a question's default, such as `[<default>]`.
- Color alone: lost with `NO_COLOR`, in copied text, and to people who can't tell green apart.
- Double quotes: they set a key apart no better, and weigh more in a line with several.

**Look again if:** setup's console text moves to a library that marks keys its own way.
