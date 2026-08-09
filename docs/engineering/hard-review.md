Quickstart:

```bash
npx skills add tticom/agy-skills --skill=hard-review
```

## What it does

`hard-review` performs the complete basic review and then classifies every
material test by data provenance. Changed domain tests that substitute
synthetic, mocked, generated, or data-free inputs for available real sources
are blocking; those categories never prove real-world correctness.

Approval requires genuine source data to reach the changed production seam,
an independent semantic oracle, personally executed private in-situ tests when
public CI skips them, and no production coupling to fixture names, paths,
hashes, coordinates, expected counts, or reference outputs.

The bundled fixture-coupling scanner catches obvious lexical leaks; the
reviewer must still inspect semantic and numeric coupling manually.
