# Documentation Standards

## Core Philosophy: Write for Your Future Self
**Good docs** answer questions before they're asked.
**Think:** What would confuse me in 6 months?
**Goal:** New developers productive in <1 hour.

## README Structure
1. **What it is** - One sentence
2. **Quick example** - Show, don't tell
3. **Installation** - Copy-paste ready
4. **Usage** - Common commands
5. **Configuration** - Environment variables
6. **Reference** - Link to detailed docs

## CLI Documentation
```bash
# Commands should be self-documenting
asc subscriptions --help

# Include examples in help text
asc subscriptions pricing set --help
```

## Docstrings (Google Style)
```python
def set_subscription_price(
    subscription_id: str,
    price: Decimal,
    territories: list[str] | None = None,
) -> PricingResult:
    """Set the price for a subscription across territories.

    Args:
        subscription_id: The App Store Connect subscription ID.
        price: Price in USD (will be converted to price points).
        territories: List of territory codes, or None for all.

    Returns:
        PricingResult with success count and any errors.

    Raises:
        AuthenticationError: If credentials are invalid.
        APIError: If the API request fails.

    Example:
        >>> result = set_subscription_price("sub_123", Decimal("2.99"))
        >>> print(f"Updated {result.success_count} territories")
    """
```

## Code Comments
- **Explain "why"** not "what"
- **No obvious comments** - Let code speak
- **Document gotchas** - API quirks, edge cases

```python
# GOOD: Explains the why
# App Store Connect returns prices in milliunits (1000 = $1.00)
price_dollars = response["price"] / 1000

# BAD: States the obvious
# Divide by 1000
price_dollars = response["price"] / 1000
```

## API Reference
Document all CLI commands with:
- Purpose and use case
- Required and optional parameters
- Output format
- Examples

## Writing Tips
- **Start with why:** Context before details
- **Show, don't tell:** Examples > explanations
- **Progressive disclosure:** Simple first, then advanced
- **Be concise:** Respect reader's time

---
*Great docs make great developers. Write with empathy.*
