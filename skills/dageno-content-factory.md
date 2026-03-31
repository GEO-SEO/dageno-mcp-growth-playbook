---
name: dageno-content-factory
description: >
  Use when the user wants to turn Dageno content opportunities, prompts, citations, and SEO metrics
  into a structured SEO + GEO content workflow. Triggers include building a content factory,
  prioritizing Dageno opportunities, combining prompt demand with keyword demand, analyzing citation
  URLs, deciding whether topics should be merged or split, creating content briefs, or packaging GEO
  chunks and schema guidance. Designed for teams using Dageno as the opportunity source and optional
  SEO, page-fetch, and SERP connectors as enrichment layers.
metadata:
  author: GEO-SEO
  version: "0.2.0"
  homepage: https://github.com/GEO-SEO/dageno-mcp-growth-playbook
  primaryEnv: DAGENO_API_KEY
  tags:
    - dageno
    - seo
    - geo
    - content-factory
    - prompt-intelligence
    - citation-intelligence
    - keyword-research
    - content-briefs
  triggers:
    - "Dageno content opportunities"
    - "GEO content factory"
    - "SEO GEO content plan"
    - "prompt demand"
    - "citation URLs"
    - "content brief"
    - "pillar or standard article"
    - "merge or split content"
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

Use this skill to turn a Dageno opportunity into a small, prioritized SEO + GEO content system.

## Overview

This workflow starts with one Dageno seed prompt and moves through five connected layers:

1. prompt-side demand
2. keyword-side demand
3. citation intelligence
4. optional SERP intelligence
5. content decision and packaging

The goal is not to write one article per term. The goal is to compress many signals into a few sensible content assets.

## Best For

- GEO and SEO operators building repeatable content workflows
- agencies turning Dageno exports into client deliverables
- founders validating which prompts deserve full content investment
- teams that want content briefs, FAQ structure, and chunk guidance instead of generic drafts

## Start With

```text
Use Dageno Content Factory to analyze our top content opportunities and recommend what to publish next.
```

```text
Take the highest-priority Dageno seed prompt and tell me whether it should become a pillar page, a standard article, or lightweight GEO coverage.
```

## Connector Rules

Required:

- `DAGENO_API_KEY`

Optional:

- `SEO_METRICS_API_URL` and `SEO_METRICS_API_KEY` for search volume and keyword difficulty
- `JINA_API_KEY` or `FIRECRAWL_API_KEY` for citation-page fetching
- `SERPAPI_API_KEY` or user-provided SERP exports for safe SERP enrichment

If optional connectors are missing:

- continue with Dageno opportunity data
- expand keywords with the model
- classify intentions with the model
- keep citation analysis lightweight if page fetching is unavailable
- skip or sample SERP work instead of hard-failing

Do not default to hidden Google scraping.

## Working Model

### Demand Layers

Treat prompt demand and search demand as separate systems:

- `observed_prompt_volume` is real Dageno prompt demand for the seed prompt
- `estimated_prompt_volume` is only a proxy for fanout prompts when no direct volume exists
- `search_volume` and `keyword_difficulty` come from the SEO connector

Never label estimated fanout demand as if it were observed prompt volume.

### Intention Model

Align keyword intentions to Dageno's categories:

- `Transactional`
- `Commercial`
- `Navigational`
- `Informational`

Use the Dageno-like structure:

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

### Decision Rule

Do not default to one article per query.

Instead:

- merge when intent and topic overlap are high
- split when the content need is clearly different
- use pillar pages for broad, high-demand clusters
- use standard articles for clear standalone opportunities
- use lightweight coverage for low-volume or experimental branches
- keep FAQ and standalone GEO chunks for narrow or extractable sub-questions

## Execution Order

### 1. Get the seed opportunity

- call the Dageno content-opportunity source
- capture `opportunity_id` and `seed_prompt`

### 2. Get observed prompt demand

- look up the seed prompt in Dageno prompt data
- store real `observed_prompt_volume` for the seed only

### 3. Translate the seed prompt into a keyword theme

- extract one `primary_keyword`
- expand a `keyword_candidates` list

### 4. Add SEO metrics

- fetch `search_volume` and `keyword_difficulty` when the connector exists
- if not available, keep the keyword cluster but mark metrics as pending

### 5. Add intentions

- classify each keyword with Dageno-aligned `intentions`
- derive one cluster-level `dominant_intention`

### 6. Add fanout prompts

- use a Dageno fanout connector when available
- otherwise keep a connector slot and do not fabricate observed prompt demand

For fanout prompts, use fields like:

- `estimated_prompt_volume`
- `volume_estimation_method`
- `volume_confidence`

### 7. Add citation URLs

- retrieve `List citation URLs`
- if page fetching is available, inspect cited pages
- otherwise infer from domain, title, URL shape, and page type hints

### 8. Run optional SERP enrichment

Plan A:

- use an approved SERP connector or pasted export

Plan B:

- skip or sample the SERP layer
- never block the full workflow on live Google retrieval

### 9. Build the unified opportunity object

Recommended shape:

```json
{
  "opportunity_id": "opp_001",
  "seed_prompt": "how to automate contract signing with ai",
  "prompt_candidates": [
    {
      "prompt": "how to automate contract signing with ai",
      "role": "seed",
      "observed_prompt_volume": 820
    },
    {
      "prompt": "how to send contracts with ai",
      "role": "fanout",
      "observed_prompt_volume": null,
      "estimated_prompt_volume": 180,
      "volume_estimation_method": "keyword_proxy",
      "volume_confidence": "low"
    }
  ],
  "keyword_candidates": [
    {
      "keyword": "ai contract automation",
      "role": "primary",
      "search_volume": 1200,
      "keyword_difficulty": 28,
      "intentions": [
        {
          "score": 86,
          "intention": "Commercial"
        }
      ]
    }
  ],
  "citation_urls": [
    "https://example.com/guide"
  ],
  "aggregates": {
    "seed_prompt_volume": 820,
    "combined_prompt_demand_score": 1000,
    "total_search_volume": 1200,
    "dominant_intention": "Commercial",
    "primary_keyword": "ai contract automation"
  }
}
```

### 10. Decide the content asset shape

Choose among:

- pillar article
- standard article
- lightweight article
- FAQ block
- GEO chunk pack

### 11. Output a blueprint, not just notes

For each asset, produce:

- recommended title
- H1
- H2/H3 structure
- FAQ list
- evidence requirements
- citation-informed writing notes
- GEO chunk guidance
- schema guidance

## Output Style

When the user asks for a recommendation or a plan, structure the answer like this:

1. `Opportunity Summary`
2. `Demand Summary`
3. `Citation And SERP Signals`
4. `Recommended Asset Decisions`
5. `Content Blueprint`
6. `GEO Packaging Notes`

## Reference

For the full repo-level workflow and connector model, see:

- [`references/pipeline-spec.md`](references/pipeline-spec.md)
