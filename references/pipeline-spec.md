# Dageno Content Factory Pipeline Spec

This reference keeps the full workflow in one place so the skill can stay concise.

## Goal

Turn one Dageno content opportunity into a prioritized SEO + GEO content blueprint.

## Data Principles

### 1. Prompt demand and search demand are different

- `observed_prompt_volume` is real Dageno prompt data for the seed prompt
- `estimated_prompt_volume` is a proxy for fanout prompts when real prompt volume is unavailable
- `search_volume` is SEO demand for keywords
- `keyword_difficulty` is SEO competition

### 2. Fanout prompt demand must be labeled honestly

Do not store estimated fanout demand in the same field as observed prompt demand.

Use:

- `observed_prompt_volume`
- `estimated_prompt_volume`
- `volume_estimation_method`
- `volume_confidence`

### 3. Intentions should follow Dageno categories

Use:

- `Transactional`
- `Commercial`
- `Navigational`
- `Informational`

Recommended object:

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

## Pipeline

### Step 1: intake

Input:

- `get_content_opportunities`

Output:

- `opportunity_id`
- `seed_prompt`

### Step 2: prompt-side demand

Input:

- seed prompt
- Dageno prompt dataset

Output:

- observed prompt demand for the seed prompt

### Step 3: keyword translation

Input:

- seed prompt

Output:

- primary keyword
- keyword cluster

### Step 4: SEO metrics

Input:

- keyword cluster
- SEO metrics connector

Output:

- search volume
- keyword difficulty

### Step 5: intentions

Input:

- keyword cluster

Output:

- keyword-level intentions
- cluster-level dominant intention

### Step 6: fanout

Input:

- seed prompt
- future Dageno fanout connector

Output:

- fanout prompts
- estimated demand only when direct observed prompt data is unavailable

### Step 7: citations

Input:

- prompt-level citation URLs

Output:

- citation URL list
- optional citation-page analysis

### Step 8: unified data layer

Combine:

- prompt candidates
- keyword candidates
- citation URLs
- cluster aggregates

### Step 9: citation intelligence

Preferred:

- fetch page content with Jina or Firecrawl

Fallback:

- analyze domain, title, URL structure, and known page type hints

Output:

- content-type signals
- extractability signals
- citation-informed writing recommendations

### Step 10: SERP intelligence

Plan A:

- use an approved SERP API or user-provided SERP export

Plan B:

- skip or sample SERP analysis

Output:

- ranking-page types
- PAA signals when available
- snippet or AI Overview hints when available

### Step 11: decision engine

Use:

- demand
- intention
- overlap
- citation evidence
- optional SERP evidence

To decide:

- pillar page
- standard article
- lightweight article
- FAQ block
- GEO chunk pack

### Step 12: blueprint generation

For each asset, output:

- title
- H1
- H2/H3 structure
- FAQ
- evidence requirements
- chunk packaging
- schema guidance

### Step 13: post-publish loop

Monitor:

- GSC
- AI citation behavior

Then decide whether to:

- keep merged
- split content
- add FAQs
- improve chunks

## Suggested Unified Data Model

```json
{
  "opportunity_id": "opp_001",
  "seed_prompt": "how to automate contract signing with ai",
  "source": "dageno:get_content_opportunities",
  "market": "global",
  "language": "en",
  "created_at": "2026-03-31T10:30:00+08:00",
  "prompt_candidates": [
    {
      "prompt": "how to automate contract signing with ai",
      "role": "seed",
      "observed_prompt_volume": 820,
      "estimated_prompt_volume": null,
      "volume_confidence": "high"
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
    },
    {
      "keyword": "contract signing automation",
      "role": "secondary",
      "search_volume": 700,
      "keyword_difficulty": 21,
      "intentions": [
        {
          "score": 74,
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
    "fanout_estimated_volume_total": 180,
    "combined_prompt_demand_score": 1000,
    "total_search_volume": 1900,
    "dominant_intention": "Commercial",
    "primary_keyword": "ai contract automation"
  }
}
```
