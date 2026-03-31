---
name: dageno-content-factory
description: >
  Use when the user wants to turn Dageno content opportunities into new SEO + GEO content assets.
  This skill starts from one Dageno prompt opportunity, inspects response detail and citation URLs,
  translates the prompt into keyword demand, classifies intention, and outputs a new-content brief or
  draft. It is designed for daily opportunity-driven content generation, not for updating existing pages.
metadata:
  author: GEO-SEO
  version: "0.3.0"
  homepage: https://github.com/GEO-SEO/dageno-mcp-growth-playbook
  primaryEnv: DAGENO_API_KEY
  tags:
    - dageno
    - seo
    - geo
    - content-factory
    - content-opportunity
    - response-gap
    - citation-intelligence
    - article-brief
  triggers:
    - "Dageno content opportunities"
    - "new content brief"
    - "response detail"
    - "citation URLs"
    - "brand gap"
    - "source gap"
    - "SEO GEO content blueprint"
  requires:
    env:
      - DAGENO_API_KEY
      - SEO_METRICS_API_URL
      - SEO_METRICS_API_KEY
      - JINA_API_KEY
      - FIRECRAWL_API_KEY
      - SERPAPI_API_KEY
    bins:
      - python3
---

# Dageno Content Factory

Use this skill to turn one Dageno content opportunity into one new content task.

## What This Skill Does

This workflow is built for daily new-content generation from Dageno.

It does not start from a blank keyword.
It does not start from an existing article inventory.

It starts from:

1. a Dageno content opportunity
2. the actual AI response behind that opportunity
3. the URLs AI cited while producing that response

Then it decides what **new** content should be created.

## Scope

This skill only handles:

- selecting a prompt opportunity
- diagnosing the answer gap
- analyzing cited sources
- translating the topic into SEO demand
- choosing a new content asset type
- outputting a brief or draft

This skill does not yet handle:

- existing-content refresh decisions
- post-publish monitoring loops
- content pruning or merge-back decisions

Those can be added later as a product extension.

## Best For

- teams writing new articles from Dageno opportunities every day
- agencies turning monitoring gaps into client content deliverables
- GEO operators who want AI-gap-driven content production
- Codex or ClawDBot setups that need one reusable content agent

## Required And Optional Connectors

Required:

- `DAGENO_API_KEY`

Optional:

- `SEO_METRICS_API_URL` and `SEO_METRICS_API_KEY`
- `JINA_API_KEY` or `FIRECRAWL_API_KEY`
- `SERPAPI_API_KEY` or user-provided SERP exports

If optional connectors are missing, continue with fallback logic.

Do not assume hidden search scraping or hidden page crawling.

## Core Logic

### Production unit

Do not treat each chat as one article.

Use this model:

- `prompt` = monitoring surface
- `response detail` = evidence of the gap
- `citation URLs` = evidence of what AI trusts
- `new content asset` = production output

### Demand model

Keep GEO and SEO demand separate:

- `observed_prompt_volume` = real seed prompt demand from Dageno
- `estimated_prompt_volume` = proxy demand for fanout prompts if needed
- `search_volume` = keyword demand from SEO connector
- `keyword_difficulty` = keyword competition from SEO connector

Do not label estimated fanout demand as if it were observed prompt volume.

### Intention model

Use Dageno-aligned intention categories:

- `Transactional`
- `Commercial`
- `Navigational`
- `Informational`

Preferred structure:

```json
{
  "intentions": [
    {
      "score": 86,
      "intention": "Commercial"
    }
  ]
}
```

## Execution Order

### 1. Select one prompt opportunity

Start from Dageno content opportunities and choose one prompt based on:

- priority
- brand gap
- source gap
- platform coverage

### 2. Read the response detail

Use `Get response detail by prompt`.

Analyze:

- what AI said
- what AI did not say
- which competitors were mentioned
- which claims, categories, or use cases were missing for the brand

This becomes the response-gap summary.

### 3. Read citation URLs

Use `List citation URLs`.

If page-fetch connectors exist, inspect the cited pages.
If not, use lightweight inference from URL, domain, title, and page type.

Analyze:

- what types of sources AI cited
- what content structures were favored
- what evidence style those sources used

This becomes the citation summary.

### 4. Add prompt-side demand

Retrieve the real `observed_prompt_volume` for the seed prompt when available.

If fanout prompts are added later:

- store them separately
- use `estimated_prompt_volume` only when direct prompt data is unavailable

### 5. Translate into SEO language

Use the model to:

- extract one `primary_keyword`
- expand a `keyword_cluster`

### 6. Add SEO metrics

When available, enrich the keyword cluster with:

- `search_volume`
- `keyword_difficulty`

If the connector is unavailable, continue with the keyword cluster and mark SEO metrics as pending.

### 7. Add intentions

Classify each keyword with Dageno-aligned intentions.

Derive one cluster-level `dominant_intention`.

### 8. Build the unified opportunity object

The decision object should include:

- prompt opportunity metadata
- response-gap evidence
- citation evidence
- prompt demand
- keyword demand
- keyword intentions

### 9. Make the new-content decision

At this stage, the only decision is:

- what new content should be created from this opportunity

Possible outputs:

- `Pillar`
- `Standard`
- `Lightweight`

### 10. Output the content blueprint

For the chosen asset, output:

- title
- H1
- H2/H3
- FAQ list
- citation-informed writing notes
- chunk plan
- schema recommendations

### 11. Optionally output a full draft

If requested, continue from blueprint to article draft.

## Output Format

When using this skill, prefer the following response structure:

1. `Selected Opportunity`
2. `Response Gap Summary`
3. `Citation Summary`
4. `Demand Summary`
5. `Recommended New Asset`
6. `SEO + GEO Blueprint`
7. `Optional Draft`

## Plan A / Plan B

### Plan A

Use when the user provides:

- Dageno API access
- SEO metrics connector
- Jina or Firecrawl
- optional SERP connector

### Plan B

If optional connectors are missing:

- still use Dageno content opportunities
- still use response detail
- still use citation URLs
- still translate the prompt into keywords
- still classify intentions
- skip full page crawling when needed
- skip SERP enrichment when needed
- still output a new-content blueprint

## Reference

For the repo-level workflow and data model, see:

- [`references/pipeline-spec.md`](references/pipeline-spec.md)
