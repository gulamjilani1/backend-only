# Import Flask and required libraries
from flask import Flask, request, jsonify, send_file
from flask_login import LoginManager, login_required
from models import db, User, Customer, Item, Invoice, InvoiceItem
from auth import auth_bp
from weasyprint import HTML
import tempfile


# Create Flask application
app = Flask(__name__)
app.secret_key = "your-secret-key"  # Needed for Flask-Login sessions

# Init login manager
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.get_or_none(int(user_id))

# Register auth blueprint
app.register_blueprint(auth_bp, url_prefix="/auth")


# ---------------- Root API Info ----------------
@app.route('/')
def home():
    return jsonify({
        "message": "Invoice App API",
        "endpoints": {
            # Customers
            "GET /customers": "List all customers",
            "POST /customers": "Create a new customer",
            "PUT /customers/<id>": "Update customer",
            "DELETE /customers/<id>": "Delete customer",

            # Items
            "GET /items": "List all items",
            "POST /items": "Create a new item",
            "PUT /items/<id>": "Update item",
            "DELETE /items/<id>": "Delete item",

            # Invoices
            "GET /invoices": "List all invoices",
            "POST /invoices": "Create a new invoice",
            "PUT /invoices/<id>": "Update invoice",
            "DELETE /invoices/<id>": "Delete invoice",
            "GET /invoices/<id>/pdf": "Download invoice PDF",

            # Auth
            "POST /auth/login": "Login with username & password",
            "POST /auth/logout": "Logout current user",
            "GET /auth/profile": "View logged in user profile"
        }
    })


# ---------------- Customer CRUD ----------------
@app.route("/customers", methods=["GET"])
def list_customers():
    return jsonify([{"id": c.id, "name": c.name, "email": c.email, "phone": c.phone} for c in Customer.select()])


@app.route("/customers", methods=["POST"])
def create_customer():
    data = request.json
    c = Customer.create(name=data["name"], email=data["email"], phone=data["phone"])
    return jsonify({"id": c.id, "name": c.name, "email": c.email, "phone": c.phone})


@app.route("/customers/<int:customer_id>", methods=["PUT"])
def update_customer(customer_id):
    c = Customer.get_or_none(customer_id)
    if not c:
        return jsonify({"error": "Customer not found"}), 404
    data = request.json
    c.name = data.get("name", c.name)
    c.email = data.get("email", c.email)
    c.phone = data.get("phone", c.phone)
    c.save()
    return jsonify({"message": "Customer updated", "id": c.id})


@app.route("/customers/<int:customer_id>", methods=["DELETE"])
def delete_customer(customer_id):
    c = Customer.get_or_none(customer_id)
    if not c:
        return jsonify({"error": "Customer not found"}), 404
    c.delete_instance()
    return jsonify({"message": "Customer deleted"})


# ---------------- Item CRUD ----------------
@app.route("/items", methods=["GET"])
def list_items():
    return jsonify([{"id": i.id, "name": i.name, "price": i.price} for i in Item.select()])


@app.route("/items", methods=["POST"])
def create_item():
    data = request.json
    i = Item.create(name=data["name"], price=data["price"])
    return jsonify({"id": i.id, "name": i.name, "price": i.price})


@app.route("/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    i = Item.get_or_none(item_id)
    if not i:
        return jsonify({"error": "Item not found"}), 404
    data = request.json
    i.name = data.get("name", i.name)
    i.price = data.get("price", i.price)
    i.save()
    return jsonify({"message": "Item updated", "id": i.id})


@app.route("/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    i = Item.get_or_none(item_id)
    if not i:
        return jsonify({"error": "Item not found"}), 404
    i.delete_instance()
    return jsonify({"message": "Item deleted"})


# ---------------- Invoice CRUD ----------------
@app.route("/invoices", methods=["GET"])
def list_invoices():
    return jsonify([{"id": inv.id, "customer": inv.customer.name, "total": inv.total} for inv in Invoice.select()])


@app.route("/invoices", methods=["POST"])
def create_invoice():
    data = request.json
    cust = Customer.get_or_none(data.get("customer_id"))
    if not cust:
        return jsonify({"error": "Customer not found"}), 404

    inv = Invoice.create(customer=cust, total=0)
    total = 0
    for it in data.get("items", []):
        item = Item.get_or_none(it["item_id"])
        if item:
            from models import InvoiceItem
            InvoiceItem.create(invoice=inv, item=item.id, quantity=it["quantity"])
            total += item.price * it["quantity"]

    inv.total = total
    inv.save()
    return jsonify({"id": inv.id, "total": inv.total})


@app.route("/invoices/<int:invoice_id>", methods=["PUT"])
def update_invoice(invoice_id):
    from models import InvoiceItem
    inv = Invoice.get_or_none(invoice_id)
    if not inv:
        return jsonify({"error": "Invoice not found"}), 404

    data = request.json
    if "customer_id" in data:
        cust = Customer.get_or_none(data["customer_id"])
        if not cust:
            return jsonify({"error": "Customer not found"}), 404
        inv.customer = cust

    if "items" in data:
        InvoiceItem.delete().where(InvoiceItem.invoice == inv).execute()
        total = 0
        for it in data["items"]:
            item = Item.get_or_none(it["item_id"])
            if item:
                InvoiceItem.create(invoice=inv, item=item.id, quantity=it["quantity"])
                total += item.price * it["quantity"]
        inv.total = total

    inv.save()
    return jsonify({"message": "Invoice updated", "id": inv.id})


@app.route("/invoices/<int:invoice_id>", methods=["DELETE"])
def delete_invoice(invoice_id):
    from models import InvoiceItem
    inv = Invoice.get_or_none(invoice_id)
    if not inv:
        return jsonify({"error": "Invoice not found"}), 404
    InvoiceItem.delete().where(InvoiceItem.invoice == inv).execute()
    inv.delete_instance()
    return jsonify({"message": "Invoice deleted"})


# ---------------- PDF Generation ----------------
@app.route("/invoices/<int:invoice_id>/pdf", methods=["GET"])
def invoice_pdf(invoice_id):
    from models import InvoiceItem
    inv = Invoice.get_or_none(invoice_id)
    if not inv:
        return jsonify({"error": "Invoice not found"}), 404

    items = InvoiceItem.select().where(InvoiceItem.invoice == inv)
    html_content = f"""
    <h1>Invoice #{inv.id}</h1>
    <p>Customer: {inv.customer.name}</p>
    <p>Total: {inv.total}</p>
    <h3>Items</h3>
    <ul>
    """
    for it in items:
        item_obj = Item.get_or_none(it.item)
        if item_obj:
            html_content += f"<li>{item_obj.name} - {it.quantity} x {item_obj.price}</li>"
    html_content += "</ul>"

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    HTML(string=html_content).write_pdf(temp.name)

    return send_file(temp.name, as_attachment=True, download_name=f"invoice_{inv.id}.pdf")


# Run App
if __name__ == "__main__":
    app.run(debug=True)
