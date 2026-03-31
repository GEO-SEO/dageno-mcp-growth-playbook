from __future__ import annotations

from difflib import get_close_matches
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Tuple

from .client import DagenoClient


def date_window(days: int) -> Tuple[str, str]:
    end_at = datetime.now(timezone.utc).replace(microsecond=0)
    start_at = end_at - timedelta(days=days)
    return (
        start_at.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        end_at.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
    )


def _fmt_number(value: Any, digits: int = 2) -> str:
    if value is None:
        return "-"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _normalize_gap_score(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    return numeric * 100 if 0 <= numeric <= 1 else numeric


def _fmt_gap(value: Any) -> str:
    normalized = _normalize_gap_score(value)
    if normalized == int(normalized):
        return f"{int(normalized)}%"
    return f"{normalized:.2f}%"


def _top(items: Iterable[Dict[str, Any]], key: str, limit: int) -> List[Dict[str, Any]]:
    return sorted(items, key=lambda item: item.get(key) or 0, reverse=True)[:limit]


def _normalize_text(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def _pick_best_content_opportunity(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    ranked = sorted(
        items,
        key=lambda item: (
            item.get("brandGap") or 0,
            item.get("sourceGap") or 0,
            item.get("totalResponseCount") or 0,
            item.get("totalSourceCount") or 0,
        ),
        reverse=True,
    )
    return ranked[0] if ranked else {}


def _find_prompt_match(
    prompt_items: List[Dict[str, Any]],
    *,
    prompt_id: str | None = None,
    prompt_text: str | None = None,
) -> Dict[str, Any]:
    if prompt_id:
        for item in prompt_items:
            if item.get("id") == prompt_id:
                return item

    normalized_map = {
        _normalize_text(item.get("prompt", "")): item for item in prompt_items if item.get("prompt")
    }
    if prompt_text:
        normalized = _normalize_text(prompt_text)
        if normalized in normalized_map:
            return normalized_map[normalized]
        matches = get_close_matches(normalized, list(normalized_map.keys()), n=1, cutoff=0.75)
        if matches:
            return normalized_map[matches[0]]

    return {}


def _choose_asset_type(
    *,
    prompt_volume: float | int | None,
    brand_gap: float | int | None,
    source_gap: float | int | None,
    response_count: float | int | None,
) -> str:
    pv = prompt_volume or 0
    bg = _normalize_gap_score(brand_gap)
    sg = _normalize_gap_score(source_gap)
    rc = response_count or 0
    if (bg >= 80 and sg >= 60) or (pv >= 20 and rc >= 20):
        return "Pillar"
    if bg >= 40 or sg >= 40 or rc >= 8 or pv >= 5:
        return "Standard"
    return "Lightweight"


def _format_intentions(intentions: List[Dict[str, Any]]) -> str:
    if not intentions:
        return "-"
    bits = []
    for item in intentions:
        intention = item.get("intention") or item.get("i") or "-"
        score = item.get("score")
        if score is None:
            score = item.get("s")
        bits.append(f"{intention} ({score})" if score is not None else intention)
    return ", ".join(bits)


def _response_preview(text: str, limit: int = 420) -> str:
    flat = " ".join((text or "").strip().split())
    return flat[:limit] + ("..." if len(flat) > limit else "")


def _summarize_mentions(detail: Dict[str, Any], limit: int = 5) -> List[str]:
    mentions = detail.get("mentions") or []
    lines: List[str] = []
    for item in mentions[:limit]:
        brand = item.get("brandName") or item.get("domain") or "-"
        domain = item.get("domain")
        position = item.get("position")
        sentiment = item.get("sentimentScore")
        extras = []
        if domain:
            extras.append(domain)
        if position is not None:
            extras.append(f"position {position}")
        if sentiment is not None:
            extras.append(f"sentiment {sentiment}")
        suffix = f" ({', '.join(extras)})" if extras else ""
        lines.append(f"- {brand}{suffix}")
    return lines


def _content_angles(selected: Dict[str, Any], detail: Dict[str, Any], citation_urls: List[Dict[str, Any]]) -> List[str]:
    angles: List[str] = []
    topic = selected.get("topic")
    if topic:
        angles.append(f"Define the topic clearly and claim category relevance around `{topic}`.")
    mentions = detail.get("mentions") or []
    competitor_mentions = [m for m in mentions if m.get("brandName")]
    if competitor_mentions:
        brands = ", ".join(
            sorted({m.get("brandName") for m in competitor_mentions if m.get("brandName")})
        )
        angles.append(f"Address competitor-framed expectations directly, especially against {brands}.")
    if citation_urls:
        page_types = [item.get("pageType") for item in citation_urls if item.get("pageType")]
        if page_types:
            types = ", ".join(sorted(set(page_types))[:3])
            angles.append(f"Mirror citation-friendly structure seen in cited sources, especially {types} pages.")
        else:
            angles.append("Use a citation-friendly structure: definition first, short sections, and source-backed claims.")
    if not angles:
        angles.append("Write a direct, definition-first article with strong evidence blocks and extractable subheadings.")
    return angles[:4]


def brand_snapshot(client: DagenoClient) -> str:
    payload = client.brand_info()["data"]
    socials = ", ".join(social["url"] for social in payload.get("socials", [])[:3]) or "-"
    return "\n".join(
        [
            "# Brand Snapshot",
            "",
            f"- Brand: `{payload.get('name', '-')}`",
            f"- Domain: `{payload.get('domain', '-')}`",
            f"- Website: `{payload.get('website', '-')}`",
            f"- Tagline: `{payload.get('tagline', '-')}`",
            f"- Socials: {socials}",
            "",
            "## Summary",
            "",
            payload.get("description", "-"),
        ]
    )


def topic_watchlist(client: DagenoClient, days: int = 30, limit: int = 5) -> str:
    start_at, end_at = date_window(days)
    items = client.topics(start_at, end_at, page_size=max(limit, 10))["data"]["items"]
    rows = _top(items, "visibility", limit)
    lines = [
        f"# Topic Watchlist ({days} days)",
        "",
        "| Topic | Visibility | Sentiment | Avg Position | Citation Rate | Volume |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in rows:
        lines.append(
            "| {topic} | {visibility} | {sentiment} | {avg_position} | {citation_rate} | {volume} |".format(
                topic=item.get("topic", "-"),
                visibility=_fmt_number(item.get("visibility")),
                sentiment=_fmt_number(item.get("sentiment")),
                avg_position=_fmt_number(item.get("avgPosition")),
                citation_rate=_fmt_number(item.get("citationRate")),
                volume=_fmt_number(item.get("volume")),
            )
        )
    return "\n".join(lines)


def prompt_gap_report(client: DagenoClient, days: int = 30, limit: int = 5) -> str:
    start_at, end_at = date_window(days)
    items = client.prompts(start_at, end_at, page_size=max(limit * 3, 15))["data"]["items"]
    ranked = sorted(
        items,
        key=lambda item: ((item.get("volume") or 0), (item.get("visibility") or 0), -1 * (item.get("citationRate") or 0)),
        reverse=True,
    )[:limit]
    lines = [
        f"# Prompt Gap Report ({days} days)",
        "",
        "| Prompt | Topic | Funnel | Visibility | Citation Rate | Volume |",
        "|---|---|---|---:|---:|---:|",
    ]
    for item in ranked:
        lines.append(
            "| {prompt} | {topic} | {funnel} | {visibility} | {citation_rate} | {volume} |".format(
                prompt=item.get("prompt", "-"),
                topic=item.get("topic", "-"),
                funnel=item.get("funnel", "-"),
                visibility=_fmt_number(item.get("visibility")),
                citation_rate=_fmt_number(item.get("citationRate")),
                volume=_fmt_number(item.get("volume")),
            )
        )
    return "\n".join(lines)


def citation_source_brief(client: DagenoClient, days: int = 30, limit: int = 5) -> str:
    start_at, end_at = date_window(days)
    domains = client.citation_domains(start_at, end_at, page_size=max(limit, 10))["data"]["items"]
    urls = client.citation_urls(start_at, end_at, page_size=max(limit, 10))["data"]["items"]

    lines = [
        f"# Citation Source Brief ({days} days)",
        "",
        "## Top Domains",
        "",
        "| Domain | Type | Citation Count | Citation Rate |",
        "|---|---|---:|---:|",
    ]
    for item in _top(domains, "citationCount", limit):
        lines.append(
            "| {domain} | {domain_type} | {citation_count} | {citation_rate} |".format(
                domain=item.get("domain", "-"),
                domain_type=item.get("domainType", "-"),
                citation_count=_fmt_number(item.get("citationCount")),
                citation_rate=_fmt_number(item.get("citationRate")),
            )
        )

    lines.extend(
        [
            "",
            "## Top URLs",
            "",
            "| URL | Domain | Citation Count | Page Type |",
            "|---|---|---:|---|",
        ]
    )
    for item in _top(urls, "citationCount", limit):
        lines.append(
            "| {url} | {domain} | {citation_count} | {page_type} |".format(
                url=item.get("url", "-"),
                domain=item.get("domain", "-"),
                citation_count=_fmt_number(item.get("citationCount")),
                page_type=item.get("pageType", "-"),
            )
        )
    return "\n".join(lines)


def content_opportunity_brief(client: DagenoClient, days: int = 30, limit: int = 5) -> str:
    start_at, end_at = date_window(days)
    items = client.content_opportunities(start_at, end_at, page_size=max(limit, 10))["data"]["items"]
    ranked = _top(items, "totalResponseCount", limit)
    lines = [
        f"# Content Opportunity Brief ({days} days)",
        "",
        "| Prompt | Topic | Brand Gap | Source Gap | Responses | Sources | Platforms |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for item in ranked:
        platforms = ", ".join(item.get("platforms", [])[:4])
        lines.append(
            "| {prompt} | {topic} | {brand_gap} | {source_gap} | {responses} | {sources} | {platforms} |".format(
                prompt=item.get("prompt", "-"),
                topic=item.get("topic", "-"),
                brand_gap=_fmt_number(item.get("brandGap")),
                source_gap=_fmt_number(item.get("sourceGap")),
                responses=_fmt_number(item.get("totalResponseCount")),
                sources=_fmt_number(item.get("totalSourceCount")),
                platforms=platforms or "-",
            )
        )
    return "\n".join(lines)


def backlink_opportunity_brief(client: DagenoClient, days: int = 30, limit: int = 5) -> str:
    start_at, end_at = date_window(days)
    items = client.backlink_opportunities(start_at, end_at, page_size=max(limit, 10))["data"]["items"]
    ranked = _top(items, "priority", limit)
    lines = [
        f"# Backlink Opportunity Brief ({days} days)",
        "",
        "| Domain | Type | Priority | Prompt Count | Chat Count |",
        "|---|---|---:|---:|---:|",
    ]
    for item in ranked:
        lines.append(
            "| {domain} | {domain_type} | {priority} | {prompt_count} | {chat_count} |".format(
                domain=item.get("domain", "-"),
                domain_type=item.get("domainType", "-"),
                priority=_fmt_number(item.get("priority")),
                prompt_count=_fmt_number(item.get("promptCount")),
                chat_count=_fmt_number(item.get("chatCount")),
            )
        )
    return "\n".join(lines)


def community_opportunity_brief(client: DagenoClient, days: int = 30, limit: int = 5) -> str:
    start_at, end_at = date_window(days)
    items = client.community_opportunities(start_at, end_at, page_size=max(limit, 10))["data"]["items"]
    ranked = _top(items, "priority", limit)
    lines = [
        f"# Community Opportunity Brief ({days} days)",
        "",
        "| Prompt | Domain | Type | Citations | Priority | Platforms |",
        "|---|---|---|---:|---:|---|",
    ]
    for item in ranked:
        lines.append(
            "| {prompt} | {domain} | {domain_type} | {citations} | {priority} | {platforms} |".format(
                prompt=item.get("prompt", "-"),
                domain=item.get("domain", "-"),
                domain_type=item.get("domainType", "-"),
                citations=_fmt_number(item.get("citations")),
                priority=_fmt_number(item.get("priority")),
                platforms=", ".join(item.get("platforms", [])[:4]) or "-",
            )
        )
    return "\n".join(lines)


def prompt_deep_dive(client: DagenoClient, prompt_id: str, days: int = 30, limit: int = 5) -> str:
    start_at, end_at = date_window(days)
    responses = client.prompt_responses(prompt_id, start_at, end_at, page_size=max(limit, 5))["data"]["items"]
    domains = client.prompt_citation_domains(prompt_id, start_at, end_at, page_size=max(limit, 5))["data"]["items"]
    urls = client.prompt_citation_urls(prompt_id, start_at, end_at, page_size=max(limit, 5))["data"]["items"]

    lines = [
        f"# Prompt Deep Dive: `{prompt_id}`",
        "",
        "## Recent Responses",
        "",
    ]
    for item in responses[:limit]:
        content = (item.get("contentMd") or "").strip().replace("\n", " ")
        lines.extend(
            [
                f"- Platform: `{item.get('platform', '-')}`",
                f"  Date: `{item.get('date', '-')}`",
                f"  Preview: {content[:220] or '-'}",
            ]
        )

    lines.extend(
        [
            "",
            "## Top Citation Domains",
            "",
            "| Domain | Citation Count | Citation Rate |",
            "|---|---:|---:|",
        ]
    )
    for item in _top(domains, "citationCount", limit):
        lines.append(
            "| {domain} | {citation_count} | {citation_rate} |".format(
                domain=item.get("domain", "-"),
                citation_count=_fmt_number(item.get("citationCount")),
                citation_rate=_fmt_number(item.get("citationRate")),
            )
        )

    lines.extend(
        [
            "",
            "## Top Citation URLs",
            "",
            "| URL | Domain | Citation Count |",
            "|---|---|---:|",
        ]
    )
    for item in _top(urls, "citationCount", limit):
        lines.append(
            "| {url} | {domain} | {citation_count} |".format(
                url=item.get("url", "-"),
                domain=item.get("domain", "-"),
                citation_count=_fmt_number(item.get("citationCount")),
            )
        )
    return "\n".join(lines)


def weekly_exec_brief(client: DagenoClient, days: int = 30, limit: int = 5) -> str:
    sections = [
        brand_snapshot(client),
        topic_watchlist(client, days=days, limit=limit),
        prompt_gap_report(client, days=days, limit=limit),
        citation_source_brief(client, days=days, limit=limit),
        content_opportunity_brief(client, days=days, limit=limit),
        backlink_opportunity_brief(client, days=days, limit=limit),
        community_opportunity_brief(client, days=days, limit=limit),
    ]
    return "\n\n".join(sections)


def new_content_brief(
    client: DagenoClient,
    days: int = 30,
    limit: int = 5,
    *,
    prompt_id: str | None = None,
    prompt_text: str | None = None,
) -> str:
    start_at, end_at = date_window(days)
    prompt_items = client.prompts(start_at, end_at, page_size=200)["data"]["items"]

    selected_prompt = _find_prompt_match(prompt_items, prompt_id=prompt_id, prompt_text=prompt_text)
    selected_prompt_id = selected_prompt.get("id") if selected_prompt else prompt_id

    if selected_prompt_id:
        opportunity_items = client.content_opportunities(
            start_at,
            end_at,
            page_size=max(limit * 5, 20),
            prompt_id=selected_prompt_id,
        )["data"]["items"]
        if not opportunity_items and selected_prompt.get("prompt"):
            all_items = client.content_opportunities(start_at, end_at, page_size=100)["data"]["items"]
            normalized = _normalize_text(selected_prompt.get("prompt", ""))
            opportunity_items = [
                item for item in all_items if _normalize_text(item.get("prompt", "")) == normalized
            ]
    else:
        opportunity_items = client.content_opportunities(start_at, end_at, page_size=100)["data"]["items"]

    if prompt_text and not selected_prompt:
        selected_prompt = _find_prompt_match(prompt_items, prompt_text=prompt_text)

    if not opportunity_items:
        return "# New Content Brief\n\nNo content opportunities were returned for the selected window."

    selected = _pick_best_content_opportunity(opportunity_items)
    if not selected_prompt:
        selected_prompt = _find_prompt_match(prompt_items, prompt_text=selected.get("prompt"))
        selected_prompt_id = selected_prompt.get("id") if selected_prompt else None

    responses: List[Dict[str, Any]] = []
    detail: Dict[str, Any] = {}
    citation_urls: List[Dict[str, Any]] = []
    if selected_prompt_id:
        responses = client.prompt_responses(selected_prompt_id, start_at, end_at, page_size=10)["data"]["items"]
        responses = sorted(responses, key=lambda item: item.get("createdAt") or item.get("date") or "", reverse=True)
        if responses and responses[0].get("id"):
            detail = client.prompt_response_detail(selected_prompt_id, responses[0]["id"]).get("data", {})
        citation_urls = client.prompt_citation_urls(selected_prompt_id, start_at, end_at, page_size=10)["data"]["items"]

    prompt_volume = (selected_prompt or {}).get("volume")
    intentions = (selected_prompt or {}).get("intentions") or []
    asset_type = _choose_asset_type(
        prompt_volume=prompt_volume,
        brand_gap=selected.get("brandGap"),
        source_gap=selected.get("sourceGap"),
        response_count=selected.get("totalResponseCount"),
    )

    lines = [
        f"# New Content Brief ({days} days)",
        "",
        "## Selected Opportunity",
        "",
        f"- Prompt: `{selected.get('prompt', '-')}`",
        f"- Topic: `{selected.get('topic', '-')}`",
        f"- Prompt ID: `{selected_prompt_id or '-'}`",
        f"- Brand Gap: `{_fmt_gap(selected.get('brandGap'))}`",
        f"- Source Gap: `{_fmt_gap(selected.get('sourceGap'))}`",
        f"- Responses: `{_fmt_number(selected.get('totalResponseCount'))}`",
        f"- Sources: `{_fmt_number(selected.get('totalSourceCount'))}`",
        f"- Platforms: {', '.join(selected.get('platforms', [])[:6]) or '-'}",
        "",
        "## Demand Summary",
        "",
        f"- Observed Prompt Volume: `{_fmt_number(prompt_volume)}`",
        f"- Intentions: {_format_intentions(intentions)}",
        "",
        "## Response Gap Summary",
        "",
    ]

    if detail:
        lines.extend(
            [
                f"- Platform: `{detail.get('platform', responses[0].get('platform') if responses else '-')}`",
                f"- Region: `{detail.get('region', responses[0].get('region') if responses else '-')}`",
                f"- Date: `{detail.get('date', responses[0].get('date') if responses else '-')}`",
                f"- Preview: {_response_preview(detail.get('contentMd', '')) or '-'}",
            ]
        )
        mention_lines = _summarize_mentions(detail)
        if mention_lines:
            lines.extend(["", "### Mentioned Brands", ""])
            lines.extend(mention_lines)
        if detail.get("sources"):
            lines.extend(["", f"- Sources in response detail: {', '.join(detail.get('sources', [])[:6])}"])
    else:
        lines.append("- Response detail unavailable. Check whether the selected prompt maps to a prompt ID in this date window.")

    lines.extend(["", "## Citation Summary", ""])
    if citation_urls:
        for item in _top(citation_urls, "citationCount", limit):
            lines.append(
                "- {url} ({domain}; citations {count}; page type {page_type})".format(
                    url=item.get("url", "-"),
                    domain=item.get("domain", "-"),
                    count=_fmt_number(item.get("citationCount")),
                    page_type=item.get("pageType", "-"),
                )
            )
    else:
        lines.append("- No prompt-level citation URLs returned for this window.")

    lines.extend(
        [
            "",
            "## Recommended New Asset",
            "",
            f"- Asset Type: `{asset_type}`",
            "- Reasoning:",
            f"  High-level gap signal comes from brand gap `{_fmt_gap(selected.get('brandGap'))}` and source gap `{_fmt_gap(selected.get('sourceGap'))}`.",
            f"  Demand signal comes from observed prompt volume `{_fmt_number(prompt_volume)}` and response count `{_fmt_number(selected.get('totalResponseCount'))}`.",
            "",
            "## Drafting Angles",
            "",
        ]
    )
    for angle in _content_angles(selected, detail, citation_urls):
        lines.append(f"- {angle}")

    lines.extend(
        [
            "",
            "## Suggested Blueprint",
            "",
            f"- Working Title: {selected.get('prompt', '-')}",
            f"- H1: {selected.get('prompt', '-')}",
            "- H2 ideas:",
            f"  What the topic means for `{selected.get('topic', '-')}`",
            "  Why current AI answers miss key brand-specific context",
            "  How teams should evaluate solutions or approaches",
            "  Implementation, evidence, or examples",
            "  FAQ",
        ]
    )

    return "\n".join(lines)
