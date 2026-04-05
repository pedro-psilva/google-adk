# Discovery Notes

## Current Manual Process

Based on the sample files, the current workflow looks like this:

1. Read four sources: NEOPI-R, Profiler, career anchors, and cultural diagnosis.
2. Copy relevant paragraphs into an Excel-based report template.
3. Recreate or copy charts manually.
4. Rewrite the final language into a more corporate and respectful tone.
5. Check whether low and high indicators were actually reflected in the narrative.

The most automatable part is the drafting and QA layer. The meeting itself appears fixed and should stay outside the automation scope.

## Findings From The Sample Bundle

- The report workbook already has a stable structure with five tabs:
  - `Síntese`
  - `Dados gerais`
  - `Input Profiler`
  - `Imput âncora de Carreira`
  - `Input Cultura Organizacional`
- The final report follows a predictable section sequence:
  - identification
  - methodology
  - NEOPI-R
  - Profiler
  - career anchors
  - cultural diagnosis
  - conclusion bullets
- The conclusion is short and selective. It does not try to restate every source signal.
- The dedicated anchors and culture workbook contains the raw questionnaire outputs and summary tables.
- The Profiler extended PDF adds richer qualitative text than the short final report currently uses.
- A first-pass coverage check on the sample showed that the overall report covers the main required signals, but the conclusion leaves out several of them. In the sample, the conclusion misses the dominant Profiler style, both top anchors, both top cultures, and two NEO domains that were marked as relevant.
- The same coverage pass also surfaced possible overemphasis of medium signals, which matches the current complaint about the drafting step.

## Important Sample-Specific Risk

In the sample report workbook, the `Imput âncora de Carreira` sheet appears to have a row-order mismatch between the description text and the anchor label for `Estilo de Vida` and `Vontade de Servir`.

Implication:

- automation should not trust row order alone when pairing anchor descriptions to anchor names
- anchor descriptions should come from a canonical dictionary keyed by anchor name

## What Looks Deterministic

- locating the correct input files in a folder
- extracting identification fields
- reading Profiler percentages
- ranking career anchors by score
- ranking cultural preferences by score
- identifying NEO PI-R non-medium indicators from T scores
- populating report sections and charts from normalized data

## What Still Needs Human Review Or LLM Support

- turning raw indicators into polished organizational language
- deciding which indicators deserve emphasis in the final conclusion
- checking nuance and tone
- adjusting wording for context, audience, and sensitivity

## Best Automation Opportunities

1. Intake normalizer

Convert the file bundle into a single JSON payload with:

- person metadata
- NEO domains and facets with score bands
- Profiler dominant style and percentages
- top career anchors
- top cultural preferences
- report template sections

2. Coverage checker

Given the normalized JSON plus a drafted text, flag:

- relevant low or high indicators not reflected in the narrative
- medium indicators that were overemphasized
- anchor or culture mentions that do not match the actual ranking

3. Narrative drafter

Generate section drafts with constraints:

- respectful corporate language
- non-clinical tone
- preserve required indicators
- avoid unsupported claims

4. Document assembler

Populate Google Docs or Sheets with:

- normalized values
- approved text sections
- charts built from structured data

## Suggested Scope Boundary

The first MVP should automate data extraction, rule-based selection, and draft generation.

Do not start with:

- a fully autonomous final report
- PDF-perfect layout reproduction
- full meeting replacement

Start with a human-in-the-loop copilot that removes copying, ranking, checking, and first-draft effort.
