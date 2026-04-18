# Fire Risk Assessment

This demo explores Claude's vision capabilities by implementing a single-turn image analysis agent that evaluates wildfire risk from aerial or street-level photographs of residential properties.

## What the script does

`src/fire_risk_assessment.py` iterates over every `.jpg` in `resources/image_processing/`, encodes each image as a base64 string, and sends it to `claude-haiku-4-5` alongside a structured inspection prompt. The model is asked to work through six sequential steps: identify the primary residence, assess tree canopy overhang, evaluate wildfire vulnerability, map fuel ladders, inspect structural materials, and finally assign a numeric risk rating from 1 (low) to 4 (severe). The response for each image is printed to stdout.

The prompt is deliberately linear: each step narrows the model's attention before the next one builds on it, which reduces the chance of a vague or unfocused assessment.

## Current limitations

The script is intentionally minimal. It makes one API call per image with no memory of previous images, no structured output parsing, and no validation that the model's final line is actually a number. Results are ephemeral — nothing is persisted between runs.

## Sample outputs

### brazilian-house.jpg

> 1. **Residence Identification**: The primary residence is the white-painted, single-story structure with the corrugated metal roof in the lower portion of the image, distinguished from the deteriorated multi-story building above it by its maintained appearance and residential features.
>
> 2. **Tree Overhang Analysis**: No trees are visible with canopies extending over the roof of the primary residence; the property appears to lack significant tree coverage directly above the structure, with an estimated 0% roof overhang from tree branches.
>
> 3. **Fire Risk Assessment**: The absence of overhanging trees eliminates immediate concerns about ember catch points or continuous fuel paths from vegetation to the roof, though the proximity of the deteriorated upper structure could present adjacent fire spread risks.
>
> 4. **Defensible Space Identification**: The property demonstrates relatively clear defensible space immediately around the primary residence with no obvious continuous canopy connections or fuel ladders directly threatening the home, though the close proximity to the upper building limits overall spacing.
>
> 5. **House Structure Vulnerability**: The primary residence exhibits moderate vulnerability with white-painted surfaces (likely stucco or plaster) and what appears to be a corrugated metal roof that is more fire-resistant than wood shake, though wooden doors and window frames are visible and the structure's proximity to the deteriorated upper building presents an indirect risk.
>
> **Fire Risk Rating: 2 (Moderate Risk)**
>
> The rating reflects minimal direct tree-related fire hazards but acknowledges moderate concern due to the adjacent deteriorated structure and the home's mixed construction materials with some combustible elements.

### cabin.jpg

> 1. **Residence Identification**: The primary residence is a distinctive A-frame cabin with dark siding, prominent golden/yellow trim framing, and a peaked roof with a large front gable, clearly the only residential structure visible on the property.
>
> 2. **Tree Overhang Analysis**: Approximately 40-50% of the roof is directly overhung by mature tree canopies, with particularly dense coverage over the central and rear portions of the structure, and branches extending very close to the roof line in multiple locations.
>
> 3. **Fire Risk Assessment**: The overhanging trees create significant ember catch points and establish a continuous fuel path from the surrounding forest canopy directly to the roof; the proximity of dense branches to roof openings (visible vents and chimney) represents a notable vulnerability for ember intrusion.
>
> 4. **Defensible Space Identification**: The property exhibits minimal defensible space with trees forming a nearly continuous canopy immediately adjacent to the structure and vegetation ladders visible where shrubs and lower branches connect ground-level fuel to tree crowns that reach the roof level.
>
> 5. **House Structure Vulnerability**: The residence features wooden siding and what appears to be a composition/asphalt shingle roof with significant exposed wooden architectural elements (trim, railings, and gable detailing) that are typical fire-vulnerable materials, with no visible fire-resistant cladding or metal roofing.
>
> **Fire Risk Rating: 3 (High Risk)**

## How it could be extended

**Structured output.** Replacing the free-text response with a JSON schema (using `response_format` or a tool call) would let downstream code extract the numeric rating and per-step summaries reliably, without fragile string parsing.

**Batch processing with the Files API.** For large property portfolios, uploading images once via the Anthropic Files API and referencing them by file ID avoids re-encoding and re-uploading the same bytes on every evaluation pass.

**Multi-image context.** Sending multiple views of the same property (front, rear, satellite) in a single multi-block message would give the model a fuller picture before it commits to a rating, reducing false positives from partial occlusion.

**Confidence and uncertainty.** The prompt could ask the model to flag low-confidence assessments — for example, when image resolution is too low to determine roof material — so that a human reviewer is called in only where needed.

**Comparison over time.** Storing ratings in a database and re-evaluating the same address after vegetation changes (seasonal growth, tree removal) would turn a one-shot tool into a longitudinal monitoring system.

**Finer risk taxonomy.** The current 1–4 scale is coarse. Adding sub-scores per inspection step would let insurers or fire departments prioritize which specific hazard to address rather than treating a property as a single undifferentiated risk level.
