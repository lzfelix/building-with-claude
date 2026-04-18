# Fire Risk Assessment

This demo explores Claude's vision capabilities by implementing a single-turn image analysis agent that evaluates wildfire risk from aerial or street-level photographs of residential properties.

## What the script does

`src/fire_risk_assessment.py` iterates over every `.jpg` in `resources/image_processing/`, encodes each image as a base64 string, and sends it to `claude-haiku-4-5` alongside a structured inspection prompt. The model is asked to work through six sequential steps: identify the primary residence, assess tree canopy overhang, evaluate wildfire vulnerability, map fuel ladders, inspect structural materials, and finally assign a numeric risk rating from 1 (low) to 4 (severe). The response for each image is printed to stdout.

The prompt is deliberately linear: each step narrows the model's attention before the next one builds on it, which reduces the chance of a vague or unfocused assessment.

## Current limitations

The script is intentionally minimal. It makes one API call per image with no memory of previous images, no structured output parsing, and no validation that the model's final line is actually a number. Results are ephemeral — nothing is persisted between runs.

## How it could be extended

**Structured output.** Replacing the free-text response with a JSON schema (using `response_format` or a tool call) would let downstream code extract the numeric rating and per-step summaries reliably, without fragile string parsing.

**Batch processing with the Files API.** For large property portfolios, uploading images once via the Anthropic Files API and referencing them by file ID avoids re-encoding and re-uploading the same bytes on every evaluation pass.

**Multi-image context.** Sending multiple views of the same property (front, rear, satellite) in a single multi-block message would give the model a fuller picture before it commits to a rating, reducing false positives from partial occlusion.

**Confidence and uncertainty.** The prompt could ask the model to flag low-confidence assessments — for example, when image resolution is too low to determine roof material — so that a human reviewer is called in only where needed.

**Comparison over time.** Storing ratings in a database and re-evaluating the same address after vegetation changes (seasonal growth, tree removal) would turn a one-shot tool into a longitudinal monitoring system.

**Finer risk taxonomy.** The current 1–4 scale is coarse. Adding sub-scores per inspection step would let insurers or fire departments prioritize which specific hazard to address rather than treating a property as a single undifferentiated risk level.
