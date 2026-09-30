"""
Mithiin — Flask skeleton
------------------------
This is a starting structure for the real store. Right now everything
runs on MOCK_INVENTORY (fake data) so the site is fully clickable and
testable before the gemstore API and Stripe Connect are wired in.

TODO markers show exactly where real integration will plug in later.
"""

import os
from flask import Flask, render_template, abort
from dotenv import load_dotenv

load_dotenv()  # reads .env locally; on a real host, env vars come from that host's dashboard instead

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")

# TODO: replace with a real call to the gemstore API once we have the docs/key.
# For now this is fake data so we can build and test the site's layout and flow.
MOCK_INVENTORY = [
    {
        "id": 1,
        "name": "Round Brilliant, 1.20ct",
        "cut": "Round Brilliant",
        "carat": 1.20,
        "price": 4200,
        "stock": 3,
        "image": "https://via.placeholder.com/500x500.png?text=Diamond+1",
    },
    {
        "id": 2,
        "name": "Princess Cut, 0.90ct",
        "cut": "Princess",
        "carat": 0.90,
        "price": 2850,
        "stock": 1,
        "image": "https://via.placeholder.com/500x500.png?text=Diamond+2",
    },
    {
        "id": 3,
        "name": "Emerald Cut, 1.50ct",
        "cut": "Emerald",
        "carat": 1.50,
        "price": 5600,
        "stock": 0,
        "image": "https://via.placeholder.com/500x500.png?text=Diamond+3",
    },
]


def get_inventory():
    """TODO: swap this out for a real gemstore API call, e.g.:
    response = requests.get(GEMSTORE_API_URL + "/inventory", headers={"Authorization": f"Bearer {API_KEY}"})
    return response.json()
    """
    return MOCK_INVENTORY


def get_product(product_id):
    """TODO: swap for a real single-item API call once available."""
    return next((item for item in MOCK_INVENTORY if item["id"] == product_id), None)


@app.route("/")
def home():
    inventory = get_inventory()
    return render_template("index.html", inventory=inventory)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = get_product(product_id)
    if product is None:
        abort(404)
    return render_template("product.html", product=product)


@app.route("/checkout/<int:product_id>")
def checkout(product_id):
    product = get_product(product_id)
    if product is None:
        abort(404)
    # TODO: replace this stub with real Stripe Connect checkout session creation.
    # This is where the payment split between us and the gemstore gets set up.
    return render_template("checkout.html", product=product)


if __name__ == "__main__":
    app.run(debug=True)
