import streamlit as st
import json
import os
from fpdf import FPDF
from dotenv import load_dotenv
import urllib.parse

# Load environment variables
load_dotenv()
OWNER_NUMBER = os.getenv("OWNER_WHATSAPP_NUMBER")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8501")  # deployment URL

# Load menu
with open("menu.json", "r") as f:
    menu_json = json.load(f)

categories = list(menu_json.keys())
num_categories = len(categories)

st.set_page_config(page_title="The Kopi spot Order", page_icon="🍴", layout="centered")

# Table number
query_params = st.experimental_get_query_params()
table_number = query_params.get("table", [None])[0]
if not table_number:
    table_number = st.text_input("Enter your table number:", placeholder="e.g. 4")

if not OWNER_NUMBER:
    st.warning("Set OWNER_WHATSAPP_NUMBER in .env file to enable WhatsApp messaging.")

if table_number and OWNER_NUMBER:

    st.subheader(f"Table: {table_number}")
    st.info("Explore more dishes by going to the arrow →")

    # Initialize or get current category index in session state
    if "category_index" not in st.session_state:
        st.session_state.category_index = 0

    # Navigation buttons for categories
    col_prev, col_next = st.columns([1, 1])
    with col_prev:
        if st.button("← Previous"):
            if st.session_state.category_index > 0:
                st.session_state.category_index -= 1
    with col_next:
        if st.button("Next →"):
            if st.session_state.category_index < num_categories - 1:
                st.session_state.category_index += 1

    current_category = categories[st.session_state.category_index]
    st.markdown(f"### {current_category}")

    # Initialize order in session state if not present
    if 'order' not in st.session_state:
        st.session_state.order = []

    # Show menu items of current category only
    for item in menu_json[current_category]:
        col1, col2 = st.columns([4, 1])
        with col1:
            selected = st.checkbox(f"{item['name']} - Rs. {item['price']}", key=f"item_{item['id']}")
        with col2:
            qty = st.number_input(f"Qty (for {item['name']})", min_value=0, max_value=10, value=0, key=f"qty_{item['id']}")

        if selected and qty > 0:
            # Add or update item in order
            if not any(d['id'] == item['id'] for d in st.session_state.order):
                st.session_state.order.append({
                    "id": item['id'], "name": item['name'], "price": item['price'], "quantity": qty
                })
            else:
                for d in st.session_state.order:
                    if d['id'] == item['id']:
                        d['quantity'] = qty
        else:
            # If unchecked or qty=0, remove from order if exists
            st.session_state.order = [d for d in st.session_state.order if d['id'] != item['id']]

    total_amount = sum(i["price"] * i["quantity"] for i in st.session_state.order)

    if st.session_state.order:
        st.write("### Order Summary")
        for itm in st.session_state.order:
            st.write(f"- {itm['quantity']} x {itm['name']} @ Rs. {itm['price']}")
        st.write(f"**Total: Rs. {total_amount}**")
    else:
        st.info("No items selected yet.")

    # Customer details
    st.subheader("Enter Your Details for Receipt")
    name = st.text_input("Name")
    date = st.date_input("Order Date")

    def generate_pdf_receipt(name, order, total, date):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_fill_color(245, 245, 245)
        pdf.rect(5, 5, 200, 287, 'F')
        pdf.set_font("Arial", 'B', 18)
        pdf.set_text_color(0, 102, 204)
        pdf.cell(0, 20, "Payment Receipt", ln=True, align='C')
        pdf.set_font("Arial", '', 14)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(10)
        pdf.cell(50, 10, "Name:", 0, 0)
        pdf.cell(100, 10, name, 0, 1)
        pdf.cell(50, 10, "Order Date:", 0, 0)
        pdf.cell(100, 10, str(date), 0, 1)
        pdf.cell(50, 10, "Amount Paid:", 0, 0)
        pdf.cell(100, 10, f"Rs. {total}", 0, 1)
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Order Details:", ln=True)
        pdf.set_font("Arial", '', 12)
        for item in order:
            pdf.multi_cell(0, 10, f"- {item['quantity']} x {item['name']} @ Rs. {item['price']}")
        pdf.ln(10)
        pdf.set_font("Arial", 'I', 12)
        pdf.cell(0, 10, "Thank you for ordering from Safe-zone!", ln=True)
        return pdf.output(dest='S').encode('latin-1')

    if st.button("Generate Receipt & Send to Owner"):
        if not name:
            st.error("Please enter your name.")
        elif not st.session_state.order:
            st.error("Please select at least one item.")
        else:
            receipt_pdf = generate_pdf_receipt(name, st.session_state.order, total_amount, date)

            # Compose message for owner
            order_summary = "\n".join([f"{d['quantity']}x {d['name']}" for d in st.session_state.order])
            message_owner = (
                f"New Order!\n"
                f"Table: {table_number}\n"
                f"Name: {name}\n"
                f"Details:\n{order_summary}\n"
                f"Total: Rs. {total_amount}"
            )
            encoded_message = urllib.parse.quote(message_owner)
            whatsapp_link = f"https://wa.me/{OWNER_NUMBER}?text={encoded_message}"

            # Download PDF receipt
            st.download_button(
                "Download Receipt PDF",
                data=receipt_pdf,
                file_name="receipt.pdf",
                mime="application/pdf"
            )

            # Show WhatsApp link for owner
            st.markdown(f"[Send order to Owner on WhatsApp 📲]({whatsapp_link})", unsafe_allow_html=True)

else:
    st.warning("Please enter table number and ensure OWNER_WHATSAPP_NUMBER is set in .env.")

# Note: QR code generation button removed to hide from users.
# You can handle QR code generation separately in a standalone script.

# Hide style
st.markdown(
    """
    <style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>
    """,
    unsafe_allow_html=True
)
