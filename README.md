# AI-Powered Shopping System
### College Software Engineering Laboratory Project (Semester 5)

An end-to-end, functional, and minimalist AI Shopping Assistant built with Python Flask, HTML5/CSS3/Vanilla JavaScript, and Google Gemini API. This project demonstrates practical software engineering principles corresponding directly to **UML Experiments 5–10**.

---

## 1. Project Overview & Features

- **Natural Language Shopping Search**: Customers enter natural conversational queries (e.g., *"I want wireless headphones under ₹3000 with good battery life"*).
- **Gemini Structured Constraint Extraction**: Gemini parses the conversational input and returns structured JSON defining category, maximum price, minimum price, and feature preferences.
- **50-Product Static JSON Catalogue**: Exactly 50 electronics products across 7 categories (Headphones, Smartphones, Laptops, Smartwatches, Speakers, Keyboards & Mice, Monitors) with category-specific technical specifications.
- **Multi-Factor Recommendation Engine**: Python weighted scoring engine that filters mandatory constraints, calculates relevance match percentages (0–100%), and ranks products.
- **Grounded AI Explanations**: Gemini generates concise 1–2 sentence explanations justifying each recommendation based strictly on actual catalog specifications.
- **Category-Aware Product Comparison**: Select 2 or 3 products to view side-by-side spec comparison tables and key differences.
- **Shopping Cart & Simulated Checkout**: Add/remove items, update quantities, enforce stock limits, and execute checkout with auto-generated order IDs and memory stock deduction.
- **Live Order State Tracking**: Tracks placed orders and their states (`Confirmed`, `Shipped`, `Delivered`).

---

## 2. Alignment with SE Lab Experiments (5–10)

| Experiment | UML Diagram | Implementation in Project |
|---|---|---|
| **Experiment 5** | **Use Case Diagram** | User workflows: Search products, view AI recommendations, view explanations, compare products, manage cart, checkout, and track orders. |
| **Experiment 6** | **Activity Diagram** | Complete shopping workflow: Query &rarr; Constraint Extraction &rarr; Filtering &rarr; Ranking &rarr; Explanation &rarr; Cart &rarr; Checkout &rarr; Confirmation. |
| **Experiment 7** | **State-Chart Diagram** | Product States (`Available`, `Reserved`, `Out of Stock`, `Archived`) & Order States (`Placed`, `Confirmed`, `Shipped`, `Delivered`). |
| **Experiment 8** | **Sequence Diagram** | Chronological message sequence: `Customer` &rarr; `WebClient` &rarr; `QueryProcessor` &rarr; `ProductCatalog` &rarr; `RelevanceRanker` &rarr; `PaymentGateway`. |
| **Experiment 9** | **Collaboration Diagram** | Structural communication links between WebClient, Gemini AI service, product store, and checkout. |
| **Experiment 10** | **Class & Object Diagram** | Core domain entities: `Customer`, `Product`, `AIQuery`, `RecommendationEngine`, `Order`, `OrderItem`, `Payment`. |

---

## 3. Technology Stack

- **Frontend**: HTML5, CSS3 (Custom Responsive Minimalist Design), Vanilla JavaScript.
- **Backend**: Python 3.10+ / Flask.
- **AI Model**: Google Gemini API (`gemini-3.1-flash-lite` / `gemini-3.5-flash-lite`).
- **Data Storage**: Static JSON file (`products.json`), Python dictionaries, and Flask browser sessions (Zero database / No SQL).

---

## 4. Project Structure

```text
SELAB/project/
│
├── app.py                     # Flask web server, route handlers & session management
├── gemini_service.py          # Gemini API integration & constraint extraction
├── recommendation_engine.py   # Multi-factor ranking engine & JSON data loader
├── products.json              # 50 electronics products catalogue
├── requirements.txt           # Python dependencies (Flask, python-dotenv, requests, google-generativeai)
├── .env                       # API key configuration (contains GEMINI_API_KEY)
├── .env.example               # Example template for API key setup
├── .gitignore                 # Excluded files and secret keys
├── README.md                  # Comprehensive project documentation
│
├── templates/                 # Jinja2 HTML templates
│   ├── layout.html            # Base navigation bar, flashes and footer
│   ├── index.html             # Homepage, hero search box, chips and categories
│   ├── recommendations.html   # AI constraint summary and ranked product cards
│   ├── compare.html           # Side-by-side product comparison table
│   ├── cart.html              # Shopping cart view and item quantity controls
│   ├── checkout.html          # Delivery and payment simulation form
│   ├── confirmation.html      # Order confirmation and itemized receipt
│   └── orders.html            # Order tracking and state machine lifecycle
│
└── static/                    # Frontend static assets
    ├── css/
    │   └── style.css          # Modern minimalist responsive stylesheet
    └── js/
        └── script.js          # Search chips and product comparison selection logic
```

---

## 5. Setup & Installation

### Step 1: Install Dependencies
Open PowerShell or Terminal in the project directory:
```bash
cd SELAB/project
pip install -r requirements.txt
```

### Step 2: Configure Gemini API Key
The `.env` file should contain your Gemini API key:
```env
GEMINI_API_KEY="your_api_key_here"
```

### Step 3: Run the Application
```bash
python app.py
```
Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 6. How the Recommendation Algorithm Works (For Viva)

The `RecommendationEngine` evaluates each candidate product using a **100-Point Weighted Scoring Model**:

$$\text{Total Score} = \text{Budget Score (35 pts)} + \text{Rating Score (25 pts)} + \text{Feature Score (30 pts)} + \text{Stock Score (10 pts)}$$

1. **Mandatory Filtering**:
   - If the user specifies a category, only products in that category are evaluated.
   - If a budget is specified (e.g. ₹3,000), any product with $\text{Price} > \text{Budget}$ is strictly eliminated.
2. **Budget Score (Max 35 Points)**:
   - Evaluates budget compatibility. Products utilizing 50%–100% of the customer's budget receive the highest value-for-money score.
3. **Rating Score (Max 25 Points)**:
   - Calculated as: $(\text{Rating} / 5.0) \times 25$.
4. **Feature & Specification Matching (Max 30 Points)**:
   - Analyzes technical specifications (battery life, wireless/wired, RAM, display, noise cancellation) against query keywords and extracted preferences.
5. **Stock Score (Max 10 Points)**:
   - In-stock items receive full availability points.

---

## 7. Example Queries to Test

Try these sample queries during your demonstration:

1. **Budget Headphones**:
   > *"I want wireless headphones under ₹3000 with good battery life"*
2. **Programming Laptop**:
   > *"Suggest a laptop for programming with at least 16GB RAM"*
3. **Mid-Range Smartphone**:
   > *"Find a smartphone under ₹20000 with a good camera"*
4. **Fitness Smartwatch**:
   > *"I need a smartwatch with fitness tracking"*
5. **High-Refresh Gaming Monitor**:
   > *"Show me a gaming monitor under ₹15000 with 165Hz refresh rate"*

