import os
import json
import re
import requests
from dotenv import load_dotenv

# Load .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

VALID_CATEGORIES = [
    'Headphones and Earbuds',
    'Smartphones',
    'Laptops',
    'Smartwatches',
    'Speakers',
    'Keyboards and Mice',
    'Monitors'
]

def get_api_key():
    """Retrieve Gemini API key from environment, supporting flexible formats."""
    key = os.environ.get('GEMINI_API_KEY')
    if not key and os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('GEMINI_API_KEY'):
                    # handle =, :, or -
                    parts = re.split(r'[=:\-]\s*', line, maxsplit=1)
                    if len(parts) > 1:
                        key = parts[1].strip(' "\'')
    return key

def call_gemini(prompt, response_json=True, timeout=12):
    """Call Google Gemini REST API using models supporting generateContent."""
    api_key = get_api_key()
    if not api_key:
        return None

    # Priority model order
    models = ['gemini-3.1-flash-lite', 'gemini-3.5-flash-lite', 'gemini-3.8-flash']
    headers = {'Content-Type': 'application/json'}
    payload = {
        'contents': [{'parts': [{'text': prompt}]}]
    }
    if response_json:
        payload['generationConfig'] = {'response_mime_type': 'application/json'}

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                text = data['candidates'][0]['content']['parts'][0]['text']
                return text
        except Exception:
            continue
    return None

def fallback_extract_constraints(query):
    """Rule-based constraint extractor if Gemini API is unreachable."""
    q = query.lower()

    # Category matching
    cat = None
    if any(k in q for k in ['headphone', 'earbud', 'earphone', 'airpod', 'tws', 'audio']):
        cat = 'Headphones and Earbuds'
    elif any(k in q for k in ['phone', 'mobile', 'smartphone', 'iphone', 'galaxy', 'android']):
        cat = 'Smartphones'
    elif any(k in q for k in ['laptop', 'macbook', 'notebook', 'pc', 'vivobook', 'ideapad']):
        cat = 'Laptops'
    elif any(k in q for k in ['watch', 'smartwatch', 'fitness band', 'band']):
        cat = 'Smartwatches'
    elif any(k in q for k in ['speaker', 'soundbar', 'bluetooth speaker']):
        cat = 'Speakers'
    elif any(k in q for k in ['keyboard', 'mouse', 'mechanical keyboard']):
        cat = 'Keyboards and Mice'
    elif any(k in q for k in ['monitor', 'display', 'screen', 'curved monitor']):
        cat = 'Monitors'

    # Budget / Price extraction
    max_price = None
    min_price = None

    # Patterns like: under 3000, under rs 3000, below 25000, < 40000, under 50k
    m_under = re.search(r'(?:under|below|less than|<|within)\s*(?:rs\.?|inr|₹)?\s*(\d+(?:k)?)', q)
    if m_under:
        val_str = m_under.group(1).lower()
        if 'k' in val_str:
            max_price = int(float(val_str.replace('k', '')) * 1000)
        else:
            max_price = int(val_str)

    m_above = re.search(r'(?:above|more than|>|at least)\s*(?:rs\.?|inr|₹)?\s*(\d+(?:k)?)', q)
    if m_above:
        val_str = m_above.group(1).lower()
        if 'k' in val_str:
            min_price = int(float(val_str.replace('k', '')) * 1000)
        else:
            min_price = int(val_str)

    # Preferences
    prefs = {}
    if 'wireless' in q or 'bluetooth' in q:
        prefs['wireless'] = True
    if 'wired' in q:
        prefs['wireless'] = False
    if 'battery' in q:
        prefs['battery_focused'] = True
    if 'anc' in q or 'noise cancellation' in q:
        prefs['noise_cancellation'] = True
    if 'gaming' in q:
        prefs['gaming'] = True
    if 'programming' in q or 'coding' in q:
        prefs['programming'] = True
    if 'camera' in q:
        prefs['camera'] = True

    m_ram = re.search(r'(\d+)\s*gb\s*ram', q)
    if m_ram:
        prefs['min_ram_gb'] = int(m_ram.group(1))

    return {
        'category': cat,
        'max_price': max_price,
        'min_price': min_price,
        'preferences': prefs
    }

def extract_constraints_with_gemini(query):
    """Extract structured shopping constraints using Gemini."""
    prompt = f"""You are an AI Shopping Assistant for an electronics e-commerce store.
Convert the following customer search query into clean, structured JSON constraints.

Customer Query: "{query}"

Available Categories (MUST match one of these exactly, or null if general):
- Headphones and Earbuds
- Smartphones
- Laptops
- Smartwatches
- Speakers
- Keyboards and Mice
- Monitors

Return JSON adhering strictly to this schema:
{{
  "category": "category name or null",
  "max_price": integer_in_inr_or_null,
  "min_price": integer_in_inr_or_null,
  "preferences": {{
    "brand": "brand name or null",
    "wireless": true_false_or_null,
    "battery_life": "extracted preference or null",
    "min_ram_gb": integer_or_null,
    "features": ["list", "of", "keywords"]
  }}
}}
Do NOT invent constraints that the user did not ask for. If something is unspecified, set it to null."""

    try:
        raw_text = call_gemini(prompt, response_json=True, timeout=12)
        if raw_text:
            data = json.loads(raw_text)
            # Validate category
            cat = data.get('category')
            if cat not in VALID_CATEGORIES:
                # fuzzy match
                found = False
                if cat:
                    for vc in VALID_CATEGORIES:
                        if vc.lower() in cat.lower() or cat.lower() in vc.lower():
                            data['category'] = vc
                            found = True
                            break
                if not found:
                    data['category'] = None
            return data
    except Exception:
        pass

    # Safe fallback if API call fails
    return fallback_extract_constraints(query)

def generate_recommendation_explanations(query, ranked_products):
    """Generate concise, spec-grounded explanations for ranked products using Gemini."""
    if not ranked_products:
        return {}

    # Prepare product summaries for prompt
    items_info = []
    for p in ranked_products[:4]:
        items_info.append({
            'id': p['id'],
            'name': p['name'],
            'brand': p['brand'],
            'price': p['price'],
            'rating': p['rating'],
            'specifications': p.get('specifications', {})
        })

    prompt = f"""The customer submitted this shopping query: "{query}"

Here are the top ranked matching products from our catalogue:
{json.dumps(items_info, indent=2)}

For each product, write a 1 to 2 sentence explanation explaining specifically why it matches the customer's query.
Requirements:
1. Ground your explanation STRICTLY on the actual specifications and price provided above.
2. DO NOT invent fake specs, fake prices, or unsupported claims.
3. Return ONLY a JSON object mapping the product ID (as a string) to the explanation text.
Example format:
{{
  "1": "Matches your request for wireless headphones under ₹3000 with 70 hours battery life and comfortable on-ear fit.",
  "2": "Great budget true wireless alternative at ₹1299 featuring 42 hours total playback."
}}"""

    try:
        raw_text = call_gemini(prompt, response_json=True, timeout=12)
        if raw_text:
            explanations = json.loads(raw_text)
            # Normalize keys to int
            return {int(k): v for k, v in explanations.items() if str(k).isdigit()}
    except Exception:
        pass

    # Fallback explanation generator
    fallback_map = {}
    for p in ranked_products:
        specs = p.get('specifications', {})
        spec_highlights = []
        if 'battery_life' in specs:
            spec_highlights.append(f"{specs['battery_life']} battery life")
        if 'ram' in specs:
            spec_highlights.append(f"{specs['ram']} RAM")
        if 'noise_cancellation' in specs and 'ANC' in specs['noise_cancellation']:
            spec_highlights.append("Active Noise Cancellation")
        if 'display' in specs:
            spec_highlights.append(specs['display'])
        if 'camera' in specs:
            spec_highlights.append(specs['camera'])

        highlight_str = f" with {', '.join(spec_highlights[:2])}" if spec_highlights else ""
        fallback_map[p['id']] = (
            f"Recommended because it fits within your budget at ₹{p['price']:,} (Rated {p['rating']}★){highlight_str}."
        )

    return fallback_map

