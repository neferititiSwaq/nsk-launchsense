import streamlit as st
from fpdf import FPDF
import pandas as pd
import json
from agents import PersonaAgent, CompetitorAgent, PricingAgent, ImageAgent

# 1. Page Configuration
st.set_page_config(page_title="NSK LaunchSense", page_icon="🚀", layout="wide")

st.title("🚀 NSKdevpreneur Hub: LaunchSense")
st.markdown("---")

# Initialize Session State
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = None
if 'product_img' not in st.session_state:
    st.session_state.product_img = None

# 2. Sidebar for Financial Settings
st.sidebar.header("💰 Financial Strategy")
cost_price = st.sidebar.number_input(
    "Unit Cost Price (R)", min_value=0.0, value=150.0)
target_margin = st.sidebar.slider("Target Profit Margin (%)", 10, 80, 40) / 100

# 3. Main User Input
product_brief = st.text_area(
    "What are we launching today?",
    placeholder="e.g., Solar-powered backpack for hikers in South Africa...",
    height=100
)

# 4. The Main Action
if st.button("🚀 Run Full Launch Analysis"):
    if product_brief:
        with st.spinner("NSK AI Agents are strategizing..."):
            # Initialize Agents
            p_agent = PersonaAgent()
            c_agent = CompetitorAgent()
            pr_agent = PricingAgent()

            # Layer 1: Personas
            raw_p = p_agent.create_personas(product_brief)

            # Layer 2: Competitors
            comps = c_agent.research_competitors(product_brief)

            # Layer 3: Pricing
            price_strat = pr_agent.calculate_strategy(
                cost_price, target_margin, product_brief)

            # Store results in Session State with error handling for JSON
            try:
                st.session_state.analysis_data = {
                    "personas": json.loads(raw_p),
                    "competitors": comps,
                    "pricing": price_strat,
                    "brief": product_brief
                }
                # Reset image for new analysis
                st.session_state.product_img = None
            except Exception as e:
                st.error(
                    "AI returned a complex format. Please try running the analysis again.")
                st.expander("Debug Details").write(raw_p)
    else:
        st.warning("Please describe your product first.")

# 5. Display Results
if st.session_state.analysis_data:
    data = st.session_state.analysis_data

    # ROW 1: Image and Personas
    col_img, col_per = st.columns([1, 2])

    with col_img:
        st.subheader("🖼️ Visual Concept")
        if st.session_state.product_img is None:
            if st.button("🎨 Generate AI Concept Sketch"):
                i_agent = ImageAgent()
                with st.spinner("Nano Banana 2 is sketching..."):
                    result = i_agent.generate_sketch(data["brief"])
                    if result:
                        st.session_state.product_img = result
                        st.rerun()
                    else:
                        st.error("Wait 60 seconds! Quota cooling down.")
        else:
            st.image(st.session_state.product_img, use_container_width=True)
            if st.button("🗑️ Reset Image"):
                st.session_state.product_img = None
                st.rerun()

    with col_per:
        st.subheader("👥 Target Personas")
        st.table(pd.DataFrame(data["personas"]))

    st.markdown("---")

    # ROW 2: Competitors and Pricing
    col_comp, col_price = st.columns(2)

    with col_comp:
        st.subheader("🕵️ Competitor Landscape")
        st.table(pd.DataFrame(data["competitors"]))

    with col_price:
        st.subheader("📈 Pricing Strategy")
        strat = data["pricing"]
        st.metric("Suggested Retail Price", f"R{strat['suggested_price']}")
        st.info(strat['tips'])

    # 6. PDF Export Logic
    st.markdown("---")
    if st.button("📄 Generate Executive Report"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 20)
        pdf.cell(200, 20, txt="NSK LaunchSense: Strategic Report",
                 ln=True, align='C')

        # Financials
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="1. Financial Summary", ln=True)
        pdf.set_font("Arial", '', 12)
        pdf.multi_cell(0, 10, txt=f"Product: {data['brief']}")
        pdf.cell(
            200, 10, txt=f"Unit Cost: R{cost_price} | Retail: R{strat['suggested_price']}", ln=True)

        # Personas
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="2. Target Personas", ln=True)
        pdf.set_font("Arial", '', 10)
        for p in data["personas"]:
            name = p.get('name', 'Valued Customer')
            quote = p.get('quote', p.get('goals', 'Ready for adventure'))
            pdf.multi_cell(0, 10, txt=f"- {name}: {quote[:100]}...")

        # Competitors
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="3. Competitor Landscape", ln=True)
        pdf.set_font("Arial", '', 10)
        for c in data["competitors"]:
            pdf.cell(0, 10, txt=f"- {c['name']} ({c['price_range']})", ln=True)

        pdf_output = pdf.output(dest='S').encode('latin-1', 'ignore')
        st.download_button(
            label="📥 Download Professional PDF",
            data=pdf_output,
            file_name="NSK_Launch_Report.pdf",
            mime="application/pdf"
        )
