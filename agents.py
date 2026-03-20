import requests
import os
import json
from google.genai import Client
from google.genai import types
from dotenv import load_dotenv

# 1. Load the Secret key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# 2. Initialize the New Gemini Client
if not api_key:
    print("❌ ERROR: No API Key found in .env!")
    client = None
else:
    print(f"✅ Key found: {api_key[:5]}...")
    client = Client(api_key=api_key)


class PersonaAgent:
    def __init__(self, brand_name="NSKdevpreneur Hub"):
        self.brand = brand_name

    def create_personas(self, product_brief):
        if not client:
            return "No Client"

        print(
            f"🚀 Sending prompt to Gemini (gemini-2.0-flash) for: {product_brief}")

        try:
            # We are using 'gemini-2.5-flash' - it's faster and newer!
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"Generate 3 buyer personas for {product_brief} as a JSON array."
            )

            print("📩 Response received!")
            return response.text
        except Exception as e:
            print(f"❌ API ERROR: {e}")
            return None


class CompetitorAgent:
    def __init__(self, brand_name="NSKdevpreneur Hub"):
        self.brand = brand_name
        self.search_key = os.getenv("SERPER_API_KEY")

    def search_market(self, query):
        """This function actually 'Googles' the product for real prices"""
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": f"{query} price South Africa shop"})
        headers = {
            'X-API-KEY': self.search_key,
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        return response.json()

    def research_competitors(self, product_brief):
        # 1. Get real web data first
        web_data = self.search_market(product_brief)
        snippets = [item.get('snippet', '')
                    for item in web_data.get('organic', [])[:3]]
        context = " ".join(snippets)

        # 2. Feed that real data to Gemini to analyze
        prompt = f"""
        Web Research Data: {context}
        Product: {product_brief}
        Based on the web research above, identify 3 real competitors.
        Return ONLY a JSON array with keys: "name", "price_range", "strengths", "link".
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash', contents=prompt)
        clean_json = response.text.replace(
            "```json", "").replace("```", "").strip()
        return json.loads(clean_json)


class PricingAgent:
    def __init__(self, brand_name="NSKdevpreneur Hub"):
        self.brand = brand_name

    def calculate_strategy(self, cost_price, target_margin, product_brief):
        try:
            # Simple math logic
            markup = cost_price / (1 - target_margin)

            # AI logic to justify the price
            prompt = f"Product: {product_brief}. Cost: R{cost_price}. Suggested Retail: R{markup}. Provide 3 psychological pricing tips for this specific product."
            response = client.models.generate_content(
                model='gemini-2.5-flash', contents=prompt)

            return {
                "suggested_price": round(markup, 2),
                "tips": response.text
            }
        except Exception as e:
            return {"error": str(e)}


class ImageAgent:
    def __init__(self):
        # Ensure 'client' is the one you initialized with your API key
        self.client = client

    def generate_sketch(self, product_brief):
        try:
            print(f"🎨 Nano Banana 2 is sketching: {product_brief}")
            # 2026 Standard Syntax
            response = self.client.models.generate_content(
                model='gemini-3.1-flash-image-preview',
                contents=[
                    f"A professional high-end studio product photo of {product_brief}, clean background, commercial lighting."],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"]
                )
            )
            # Find the image part in the response
            for part in response.parts:
                if part.inline_data:
                    return part.as_image()  # Returns a PIL Image
            return None
        except Exception as e:
            print(f"❌ Image Error: {e}")
            return None


if __name__ == "__main__":
    print("--- STARTING AGENT TEST ---")
    agent = PersonaAgent()
    result = agent.create_personas("Premium streetwear hoodies")
    print("\n--- FINAL RESULT ---")
    print(result)
