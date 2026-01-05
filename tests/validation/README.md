# API Validation

Tools for validating that the simulation server accurately matches Apple's App Store Connect API.

## Purpose

The simulation server must match Apple's API as closely as possible. This directory contains scripts that:

1. **Compare responses** - Call both real API and simulation, compare results
2. **Document discrepancies** - Log any differences found
3. **Guide fixes** - Help identify what needs updating in the simulation

## Usage

### Prerequisites

1. Configure ASC credentials:
   ```bash
   export ASC_ISSUER_ID="your-issuer-id"
   export ASC_KEY_ID="your-key-id"
   export ASC_PRIVATE_KEY_PATH="~/.asc/AuthKey_XXXXX.p8"
   ```

2. Ensure Whisper app exists in App Store Connect with bundle ID `live.yooz.whisper`

### Run Comparison

```bash
# From project root
python tests/validation/compare_api_responses.py
```

This will:
- Call real API for Whisper app
- Call simulation with same data
- Compare response structures
- Report discrepancies
- Save results to `comparison_results.json`

## What's Compared

### Structure
- JSON:API format (data, type, id, attributes, relationships)
- Response keys and nesting
- Data types for all fields
- Array lengths

### Content (value matching)
- Attribute values (where applicable)
- Relationship structure
- Error responses and codes

### Ignored Fields
- IDs (different between real and simulated data)
- Timestamps (createdDate, etc.)
- Links (pagination URLs may differ)

## Interpreting Results

### PASS
Response structure matches exactly. Simulation is accurate.

### FAIL
Discrepancies found. Review the output:

```json
{
  "endpoint": "GET /apps/{id}/subscriptionGroups",
  "status": "FAIL",
  "discrepancies": [
    "group.attributes.referenceName: Value mismatch (real='Premium', sim='Whisper Pro')"
  ]
}
```

This shows:
- **Path**: `group.attributes.referenceName`
- **Issue**: Value mismatch
- **Real API**: `"Premium"`
- **Simulation**: `"Whisper Pro"`

### Common Discrepancy Types

1. **Missing in simulation** - Real API has field that simulation doesn't
2. **Extra in simulation** - Simulation has field not in real API
3. **Type mismatch** - Field has different type (e.g., string vs int)
4. **Value mismatch** - Values differ (may be OK if it's test data)

## Fixing Discrepancies

1. **Structure issues** - Update `tests/simulation/responses.py` or route handlers
2. **Validation issues** - Update `tests/simulation/validators.py`
3. **State issues** - Update `tests/simulation/state.py`
4. **Test data** - Update fixtures in `tests/simulation/fixtures/`

## Next Steps

After running validation:

1. Review `comparison_results.json`
2. For each discrepancy:
   - Determine if it's a real issue or test data difference
   - Update simulation if needed
   - Document in `.context/simulation_audit.md`
3. Re-run validation to confirm fixes
4. Commit changes with reference to validation results

## Reference

See `.context/simulation_audit.md` for known issues and validation status.
