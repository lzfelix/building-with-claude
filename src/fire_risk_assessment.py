import base64
import glob

from anthropic import Anthropic
import dotenv

from helpers import prompt

INSTRUCTIONS = """
Analyze the attached image of a property with these specific steps:

1. Residence identification: Locate the primary residence on the property by looking for:
   - The largest roofed structure
   - Typical residential features (driveway connection, regular geometry)
   - Distinction from other structures (garages, sheds, pools)

2. Tree overhang analysis: Examine all trees near the primary residence:
   - Identify any trees whose canopy extends directly over any portion of the roof
   - Estimate the percentage of roof covered by overhanging branches (0-25%, 25-50%, 50-75%, 75%+)
   - Note particularly dense areas of overhang

3. Fire risk assessment: For any overhanging trees, evaluate:
   - Potential wildfire vulnerability (ember catch points, continuous fuel paths to structure)
   - Proximity to chimneys, vents, or other roof openings if visible
   - Areas where branches create a "bridge" between wildland vegetation and the structure

4. Defensible space identification: Assess the property's overall vegetative structure:
   - Identify if trees connect to form a continuous canopy over or near the home
   - Note any obvious fuel ladders (vegetation that can carry fire from ground to tree to roof)

5. House structure vulnerability: Look for any visible vulnerabilities in the home's exterior:
   - Wooden siding, especially if dry or weathered
   - Roof materials that may be more flammable (e.g., wood shake)
   - Lack of visible fire-resistant features (e.g., metal roof, stone facade)

6. Fire risk rating: Based on your analysis, assign a Fire Risk Rating from 1-4:
   - Rating 1 (Low Risk): No tree branches overhanging the roof, good defensible space around the home
   - Rating 2 (Moderate Risk): Minimal overhang (<25% of roof), some separation between tree canopies
   - Rating 3 (High Risk): Significant overhang (25-50% of roof), connected tree canopies, multiple vulnerability points
   - Rating 4 (Severe Risk): Extensive overhang (>50% of roof), dense vegetation against structure

For each item above (1-5), write one sentence summarizing your findings, with your final response being the numerical rating.
"""


def load_img_as_base64(image_path: str) -> str:
    with open(image_path, "rb") as img_file:
        return base64.standard_b64encode(img_file.read()).decode("utf-8")


def assess_fire_risk(image_jpg_base64: str, client: Anthropic) -> str:
    prompts = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_jpg_base64
                    }
                },
                {
                    "type": "text",
                    "text": INSTRUCTIONS
                }
            ]
        },
    ]

    response = prompt.multi_block_prompt(
        client,
        prompts,
        model="claude-haiku-4-5"
    )
    return response.content[0].text


if __name__ == "__main__":
    dotenv.load_dotenv("config.env")
    client = Anthropic()

    # iterate over the .jpg in ./resources/image_processing
    for img in glob.glob("./resources/image_processing/*.jpg"):
        img_base64 = load_img_as_base64(img)
        risk_rating = assess_fire_risk(img_base64, client)

        print("-" * 50)
        print(f"Image: {img}")
        print(f"Fire risk assessment report:\n{risk_rating}")
        print("=" * 50)
        print("\n\n")
