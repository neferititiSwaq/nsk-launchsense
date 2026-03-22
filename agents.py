import requests
import os
import json
import re  # Added for text cleaning
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


def clean_json_response(text):
    """
    Strips away any markdown backticks or conversational text 
    to extract only the JSON array or object.
    """
    try:
        # Find the first '[' or '{' and the last ']' or '}'
        start_idx = re.search(r'[\[\{]', text).start()
        end_idx = text.rfind(text[start_idx].replace(
            '[', ']').replace('{', '}')) + 1
        return text[start_idx:end_idx]
    except:
        # Fallback: just strip common markdown tags
        return text.replace("```json", "").replace("```", "").strip()


class PersonaAgent:
    def __init__(self, brand_name="NSKdevpreneur Hub"):
        self.brand = brand_name

    def create_personas(self, product_brief):
        if not client:
            return "No Client"

        print(f"🚀 Sending prompt to Gemini for: {product_brief}")

        # LAYER 1: Stricter Prompting
        prompt = f"""
        GENERATE ONLY A VALID JSON ARRAY. NO CONVERSATION. NO PREAMBLE.
        Product: {product_brief}
        Return exactly 3 buyer personas as a JSON array. 
        Each object must have these keys: "name", "occupation", "goals", "pain_points", "quote".
        """

        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            print("📩 Response received!")

            # LAYER 2: Defensive Cleaning
            return clean_json_response(response.text)
        except Exception as e:
            print(f"❌ API ERROR: {e}")
            return None


class CompetitorAgent:
    def __init__(self, brand_name="NSKdevpreneur Hub"):
        self.brand = brand_name
        # Use .get() to avoid crashing if the key is missing in Secrets
        self.search_key = os.getenv("SERPER_API_KEY")

    def search_market(self, query):
        """This function actually 'Googles' the product for real prices"""
        if not self.search_key:
            return {"organic": []}  # Return empty if no key

        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": f"{query} price South Africa"})
        headers = {
            'X-API-KEY': self.search_key,
            'Content-Type': 'application/json'
        }
        try:
            response = requests.request(
                "POST", url, headers=headers, data=payload)
            return response.json()
        except:
            return {"organic": []}

    def research_competitors(self, product_brief):
        # FIX: Ensure we use self.search_market
        web_data = self.search_market(product_brief)

        # Defensive check for web_data structure
        organic_results = web_data.get('organic', [])
        snippets = [item.get('snippet', '') for item in organic_results[:3]]
        context = " ".join(
            snippets) if snippets else "No local web data found."

        prompt = f"""
        Web Research Data: {context}
        Product: {product_brief}
        Based on the data, identify 3 real competitors in South Africa. 
        Return ONLY a JSON array with keys: "name", "price_range", "strengths", "link".
        """
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            # Use the cleaning function we built!
            cleaned = clean_json_response(response.text)
            return json.loads(cleaned)
        except Exception as e:
            print(f"❌ Competitor Error: {e}")
            # Return a fallback list so the app doesn't crash
            return [{"name": "Generic Competitor", "price_range": "R500-R1000", "strengths": "Market Presence", "link": "#"}]


class PricingAgent:
    def __init__(self, brand_name="NSKdevpreneur Hub"):
        self.brand = brand_name

    def calculate_strategy(self, cost_price, target_margin, product_brief):
        try:
            markup = cost_price / (1 - target_margin)
            prompt = f"Product: {product_brief}. Cost: R{cost_price}. Suggested Retail: R{markup}. Provide 3 psychological pricing tips for this specific product in the South African market."

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )

            return {
                "suggested_price": round(markup, 2),
                "tips": response.text
            }
        except Exception as e:
            return {"error": str(e)}


class ImageAgent:
    def __init__(self):
        self.client = client

    def generate_sketch(self, product_brief):
        try:
            print(f"🎨 Nano Banana 2 is sketching: {product_brief}")
            response = self.client.models.generate_content(
                model='gemini-3.1-flash-image-preview',
                contents=[
                    f"A professional high-end studio product photo of {product_brief}, clean background, commercial lighting."],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"]
                )
            )
            for part in response.parts:
                if part.inline_data:
                    return part.as_image()
            return None
        except Exception as e:
            print(f"❌ Image Error: {e}")
            return None
