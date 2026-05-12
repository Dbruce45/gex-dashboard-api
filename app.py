import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from flashalpha import FlashAlpha

st.set_page_config(page_title="GEX Dashboard (FlashAlpha API)", layout="wide")
st.title("🚀 GEX Dashboard — FlashAlpha API")
st.markdown("**5 requests/day limit • Expiration fixed to May 15, 2026**")

# Ticker input
ticker = st.text_input("Enter Ticker (SPX, SPY, QQQ, AAPL, TSLA, etc.)", value="SPX").upper().strip()

# Fixed expiration
EXPIRATION = "2026-05-15"

st.info(f"📅 Using fixed expiration: **May 15, 2026** (this Friday) — saves 1 API call per day")

# API Key from secrets
api_key = st.secrets.get("FLASHALPHA_KEY")
if not api_key:
    st.error("⚠️ Please add your FlashAlpha API key in Streamlit Secrets (FLASHALPHA_KEY)")
    st.stop()

fa = FlashAlpha(api_key)

if st.button("📊 Load GEX Data", type="primary"):
    with st.spinner(f"Fetching GEX for {ticker} (May 15, 2026)..."):
        try:
            # Single API call with fixed expiration
            gex_data = fa.gex(ticker, expiration=EXPIRATION)
            
            # Extract data
            net_gex = gex_data.get('net_gex', 0) / 1_000_000_000
            gamma_flip = gex_data.get('gamma_flip')
            spot = gex_data.get('spot_price') or gex_data.get('underlying_price')
            
            # GEX by strike
            gex_by_strike = gex_data.get('gex_by_strike', {})
            if isinstance(gex_by_strike, list):
                # Convert list of dicts to pandas Series
                gex_dict = {item['strike']: item['net_gex'] for item in gex_by_strike}
                gex_by_strike = pd.Series(gex_dict)
            
            # Call Wall & Put Wall
            call_wall = gex_by_strike[gex_by_strike > 0].idxmax() if any(gex_by_strike > 0) else None
            put_wall = gex_by_strike[gex_by_strike < 0].idxmin() if any(gex_by_strike < 0) else None
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Net GEX", f"${net_gex:,.2f}B", 
                        delta="Positive = Stabilizing" if net_gex > 0 else "Negative = Volatile")
            col2.metric("Call Wall", f"{call_wall:.0f}" if call_wall else "N/A")
            col3.metric("Put Wall", f"{put_wall:.0f}" if put_wall else "N/A")
            col4.metric("Gamma Flip", f"{gamma_flip:.0f}" if gamma_flip else "N/A")
            
            # Modern Plotly Chart
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=gex_by_strike.index,
                y=gex_by_strike.values,
                marker_color=['green' if val > 0 else 'red' for val in gex_by_strike.values],
                opacity=0.85,
                name="GEX by Strike"
            ))
            
            if spot:
                fig.add_vline(x=spot, line_dash="dash", line_color="yellow", annotation_text="CURRENT PRICE")
            if gamma_flip:
                fig.add_vline(x=gamma_flip, line_dash="dot", line_color="white", annotation_text=f"GAMMA FLIP ({gamma_flip:.0f})")
            
            if call_wall:
                fig.add_annotation(x=call_wall, y=gex_by_strike.max()*0.9, text="CALL WALL", showarrow=True, arrowhead=2)
            if put_wall:
                fig.add_annotation(x=put_wall, y=gex_by_strike.min()*0.9, text="PUT WALL", showarrow=True, arrowhead=2)
            
            fig.update_layout(
                title=f"GEX Profile — {ticker} | May 15, 2026 | Net GEX ${net_gex:,.2f}B",
                xaxis_title="Strike Price",
                yaxis_title="GEX ($ notional per 1% move)",
                template="plotly_dark",
                height=600,
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.success(f"✅ {ticker} (May 15, 2026) loaded successfully!")
            st.caption("⚠️ This used 1 of your 5 daily API requests")
            
        except Exception as e:
            st.error(f"Error: {e}")
            st.info("💡 Tip: Free tier supports single-expiry GEX. Make sure the expiration date is valid for this ticker.")

else:
    st.info("👆 Click 'Load GEX Data' to fetch from FlashAlpha API (uses 1 request)")
    st.caption("Fixed expiration = May 15, 2026 (this Friday) — saves 1 API call per day")