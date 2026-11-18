import os
import json
import re
from gemini_service import extract_constraints_with_gemini, generate_recommendation_explanations

CATALOG_PATH = os.path.join(os.path.dirname(__file__), 'products.json')

def load_products():
    """Load all products from static JSON catalogue."""
    if not os.path.exists(CATALOG_PATH):
        return []
    with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_product_by_id(product_id):
    """Retrieve a single product by its integer ID."""
    products = load_products()
    for p in products:
        if p['id'] == int(product_id):
            return p
    return None

def update_product_stock(product_id, qty_purchased):
    """Deduct purchased quantity from in-memory catalogue file."""
    products = load_products()
    for p in products:
        if p['id'] == int(product_id):
            p['stock'] = max(0, p['stock'] - int(qty_purchased))
            break
    with open(CATALOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2)

class RecommendationEngine:
    """
    Weighted scoring recommendation engine for AI Shopping System.
    Designed for SE Lab Viva demonstration:
    - Step 1: Constraint Filtering (Category, Mandatory Budget)
    - Step 2: Multi-Factor Scoring (Budget Efficiency 35%, Rating 25%, Feature Match 30%, Stock 10%)
    - Step 3: Ranking and Grounded Explanation
    """

    def __init__(self):
        self.products = load_products()

    def reload(self):
        self.products = load_products()

    def calculate_score(self, product, constraints, query_text):
        """
        Calculate a composite relevance score out of 100 points.
        """
        score = 0.0
        q_lower = query_text.lower()
        max_price = constraints.get('max_price')
        price = product.get('price', 0)
        rating = product.get('rating', 4.0)
        stock = product.get('stock', 0)
        specs = product.get('specifications', {})
        specs_str = json.dumps(specs).lower() + " " + product.get('description', '').lower()

        # 1. Budget Compatibility (35 Points Max)
        if max_price:
            if price <= max_price:
                # Ratio of price to budget (sweet spot: 60% to 100% of max_price)
                ratio = price / max_price
                if 0.5 <= ratio <= 1.0:
                    score += 35.0
                else:
                    score += 20.0 + (ratio * 15.0)
            else:
                return 0.0 # Strict constraint violated
        else:
            # Without explicit budget, award base 30 points
            score += 30.0

        # 2. Product Rating Score (25 Points Max)
        # Rating is out of 5.0
        score += (rating / 5.0) * 25.0

        # 3. Feature & Preference Matching (30 Points Max)
        feature_score = 0.0
        keywords = []

        # Extract meaningful query keywords
        tokens = re.findall(r'[a-zA-Z0-9\+]+', q_lower)
        stopwords = {'i', 'want', 'need', 'suggest', 'find', 'show', 'buy', 'good', 'best', 'the', 'a', 'an', 'under', 'below', 'for', 'with', 'at', 'least', 'rs', 'inr'}
        query_words = [t for t in tokens if t not in stopwords and not t.isdigit()]

        matched_words = 0
        for w in query_words:
            if w in specs_str or w in product['name'].lower() or w in product['brand'].lower():
                matched_words += 1

        if query_words:
            feature_score += min(20.0, (matched_words / len(query_words)) * 25.0)
        else:
            feature_score += 15.0

        # Preference bonus
        prefs = constraints.get('preferences', {})
        if isinstance(prefs, dict):
            # Wireless check
            if prefs.get('wireless') is True:
                if specs.get('wireless') is True or 'wireless' in specs_str or 'bluetooth' in specs_str:
                    feature_score += 5.0
            # Battery check
            if prefs.get('battery_life') or prefs.get('battery_focused'):
                if 'battery' in specs_str or 'hour' in specs_str or 'mah' in specs_str:
                    feature_score += 5.0
            # RAM check
            min_ram = prefs.get('min_ram_gb')
            if min_ram:
                ram_str = specs.get('ram', '')
                m_ram = re.search(r'(\d+)', ram_str)
                if m_ram and int(m_ram.group(1)) >= min_ram:
                    feature_score += 10.0

        score += min(30.0, feature_score)

        # 4. Stock Availability (10 Points Max)
        if stock > 0:
            score += 10.0
        else:
            score += 0.0

        return round(min(100.0, score), 1)

    def recommend(self, query_text):
        """
        Main pipeline:
        1. Extract constraints using Gemini
        2. Filter catalogue
        3. Score & rank
        4. Generate AI explanations
        """
        self.reload()

        # Step 1: Constraint Extraction
        constraints = extract_constraints_with_gemini(query_text)
        target_category = constraints.get('category')
        max_price = constraints.get('max_price')
        min_price = constraints.get('min_price')

        # Step 2: Filtering
        filtered = []
        for p in self.products:
            # Category filter (if extracted)
            if target_category and p['category'].lower() != target_category.lower():
                continue

            # Mandatory Price filters
            if max_price is not None and p['price'] > max_price:
                continue
            if min_price is not None and p['price'] < min_price:
                continue

            # In stock filter (prefer available products)
            if p.get('stock', 0) <= 0:
                continue

            filtered.append(p)

        # If strict category filter yielded 0 results, fall back to keyword search
        if not filtered:
            q_lower = query_text.lower()
            for p in self.products:
                if max_price is not None and p['price'] > max_price:
                    continue
                if p.get('stock', 0) <= 0:
                    continue
                # check if brand or category keyword is in query
                if p['category'].lower() in q_lower or p['brand'].lower() in q_lower:
                    filtered.append(p)

        # Step 3: Scoring & Ranking
        scored_products = []
        for p in filtered:
            item = dict(p)
            item['relevance_score'] = self.calculate_score(p, constraints, query_text)
            scored_products.append(item)

        # Sort descending by relevance score
        scored_products.sort(key=lambda x: x['relevance_score'], reverse=True)

        # Step 4: Generate Explanations for top results
        top_candidates = scored_products[:6]
        explanations = generate_recommendation_explanations(query_text, top_candidates)

        for p in top_candidates:
            p['ai_explanation'] = explanations.get(p['id'], "Matches your required category, budget and specifications.")

        return {
            'query': query_text,
            'constraints': constraints,
            'results': top_candidates,
            'total_matches': len(scored_products)
        }

