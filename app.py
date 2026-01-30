# ============================================================================
# NYZTrade LIVE GEX/DEX Dashboard - FULL ENHANCED VERSION
# Countdown Timer + Hedge Pressure + VANNA + CHARM + GEX Overlay
# ============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import norm
from datetime import datetime, timedelta
import pytz
import requests
import time
from dataclasses import dataclass
from typing import Optional, Dict, List
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="NYZTrade LIVE Enhanced",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# STYLING
# ============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Space+Grotesk:wght@400;700&display=swap');
    
    header[data-testid="stHeader"] a[href*="github"] { display: none !important; }
    
    :root {
        --bg-primary: #0a0e17;
        --accent-green: #10b981;
        --accent-red: #ef4444;
        --accent-blue: #3b82f6;
    }
    
    .stApp {
        background: linear-gradient(135deg, var(--bg-primary) 0%, #0f172a 50%, var(--bg-primary) 100%);
    }
    
    .main-header {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
        border: 1px solid #2d3748;
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
    }
    
    .metric-card {
        background: #1a2332;
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 20px;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        background: #232f42;
        transform: translateY(-2px);
    }
    
    .metric-card.positive { border-left: 4px solid var(--accent-green); }
    .metric-card.negative { border-left: 4px solid var(--accent-red); }
    .metric-card.neutral { border-left: 4px solid #f59e0b; }
    
    .signal-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: 20px;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        font-size: 0.85rem;
    }
    
    .signal-badge.bullish {
        background: rgba(16, 185, 129, 0.15);
        color: var(--accent-green);
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .signal-badge.bearish {
        background: rgba(239, 68, 68, 0.15);
        color: var(--accent-red);
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    .live-indicator {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 20px;
        animation: pulse 2s ease-in-out infinite;
    }
    
    .live-dot {
        width: 8px;
        height: 8px;
        background: var(--accent-red);
        border-radius: 50%;
        animation: blink 1s ease-in-out infinite;
    }
    
    .telegram-indicator {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        background: rgba(34, 139, 230, 0.1);
        border: 1px solid rgba(34, 139, 230, 0.3);
        border-radius: 20px;
    }
    
    .countdown-box {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(251, 191, 36, 0.1));
        border: 2px solid rgba(245, 158, 11, 0.4);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        margin: 16px 0;
    }
    
    .countdown-timer {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.5rem;
        font-weight: 700;
        color: #f59e0b;
        letter-spacing: 0.1em;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class DhanConfig:
    client_id: str = "1100480354"
    access_token: str = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY5Nzc0MzIyLCJhcHBfaWQiOiJjOTNkM2UwOSIsImlhdCI6MTc2OTY4NzkyMiwidG9rZW5Db25zdW1lclR5cGUiOiJBUFAiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMDQ4MDM1NCJ9.VuTq2uSDzTWelLiXUFIjf2xTfbytZeKvASQAUAWKk3jeXPy6xSo_-853lpUJPU8cdzmvQgkBs1pDNpgLxmkn-g"

@dataclass
class TelegramConfig:
    bot_token: str = "YOUR_BOT_TOKEN_HERE"  # ← Edit this
    chat_id: str = "YOUR_CHAT_ID_HERE"      # ← Edit this
    enabled: bool = True

TELEGRAM_CONFIG = TelegramConfig()

DHAN_SECURITY_IDS = {
    "NIFTY": 13, "BANKNIFTY": 25, "FINNIFTY": 27, "MIDCPNIFTY": 442
}

SYMBOL_CONFIG = {
    "NIFTY": {"contract_size": 25, "strike_interval": 50},
    "BANKNIFTY": {"contract_size": 15, "strike_interval": 100},
    "FINNIFTY": {"contract_size": 40, "strike_interval": 50},
    "MIDCPNIFTY": {"contract_size": 75, "strike_interval": 25},
}

IST = pytz.timezone('Asia/Kolkata')

# ============================================================================
# TELEGRAM BOT
# ============================================================================

class TelegramSender:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, text: str) -> bool:
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {"chat_id": self.chat_id, "text": text, "parse_mode": "HTML"}
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def send_photo(self, image_bytes: bytes, caption: str = "") -> bool:
        try:
            url = f"{self.base_url}/sendPhoto"
            files = {'photo': ('chart.png', image_bytes, 'image/png')}
            data = {'chat_id': self.chat_id, 'caption': caption, 'parse_mode': 'HTML'}
            response = requests.post(url, files=files, data=data, timeout=30)
            return response.status_code == 200
        except:
            return False
    
    def test_connection(self) -> bool:
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            return response.status_code == 200 and response.json().get('ok', False)
        except:
            return False

# ============================================================================
# BLACK-SCHOLES CALCULATOR
# ============================================================================

class BlackScholesCalculator:
    @staticmethod
    def calculate_d1(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0:
            return 0
        return (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma * np.sqrt(T))
    
    @staticmethod
    def calculate_d2(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0:
            return 0
        d1 = BlackScholesCalculator.calculate_d1(S, K, T, r, sigma)
        return d1 - sigma * np.sqrt(T)
    
    @staticmethod
    def calculate_gamma(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return 0
        try:
            d1 = BlackScholesCalculator.calculate_d1(S, K, T, r, sigma)
            return norm.pdf(d1) / (S * sigma * np.sqrt(T))
        except:
            return 0
    
    @staticmethod
    def calculate_call_delta(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return 0
        try:
            d1 = BlackScholesCalculator.calculate_d1(S, K, T, r, sigma)
            return norm.cdf(d1)
        except:
            return 0
    
    @staticmethod
    def calculate_put_delta(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return 0
        try:
            d1 = BlackScholesCalculator.calculate_d1(S, K, T, r, sigma)
            return norm.cdf(d1) - 1
        except:
            return 0
    
    @staticmethod
    def calculate_vanna(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return 0
        try:
            d1 = BlackScholesCalculator.calculate_d1(S, K, T, r, sigma)
            d2 = BlackScholesCalculator.calculate_d2(S, K, T, r, sigma)
            return -norm.pdf(d1) * d2 / sigma
        except:
            return 0
    
    @staticmethod
    def calculate_charm(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return 0
        try:
            d1 = BlackScholesCalculator.calculate_d1(S, K, T, r, sigma)
            d2 = BlackScholesCalculator.calculate_d2(S, K, T, r, sigma)
            return -norm.pdf(d1) * (2*r*T - d2*sigma*np.sqrt(T)) / (2*T*sigma*np.sqrt(T))
        except:
            return 0

# ============================================================================
# GAMMA FLIP ZONE CALCULATOR
# ============================================================================

def identify_gamma_flip_zones(df: pd.DataFrame, spot_price: float) -> List[Dict]:
    df_sorted = df.sort_values('strike').reset_index(drop=True)
    flip_zones = []
    
    for i in range(len(df_sorted) - 1):
        current_gex = df_sorted.iloc[i]['net_gex']
        next_gex = df_sorted.iloc[i + 1]['net_gex']
        current_strike = df_sorted.iloc[i]['strike']
        next_strike = df_sorted.iloc[i + 1]['strike']
        
        if (current_gex > 0 and next_gex < 0) or (current_gex < 0 and next_gex > 0):
            flip_strike = current_strike + (next_strike - current_strike) * (abs(current_gex) / (abs(current_gex) + abs(next_gex)))
            
            if spot_price < flip_strike:
                if current_gex > 0:
                    direction, arrow, color = "upward", "↑", "#ef4444"
                else:
                    direction, arrow, color = "downward", "↓", "#10b981"
            else:
                if current_gex < 0:
                    direction, arrow, color = "downward", "↓", "#10b981"
                else:
                    direction, arrow, color = "upward", "↑", "#ef4444"
            
            flip_zones.append({
                'strike': flip_strike,
                'lower_strike': current_strike,
                'upper_strike': next_strike,
                'direction': direction,
                'arrow': arrow,
                'color': color,
                'flip_type': 'Positive→Negative' if current_gex > 0 else 'Negative→Positive'
            })
    
    return flip_zones

# ============================================================================
# DHAN LIVE FETCHER
# ============================================================================

class DhanLiveFetcher:
    def __init__(self, config: DhanConfig):
        self.config = config
        self.headers = {
            'access-token': config.access_token,
            'client-id': config.client_id,
            'Content-Type': 'application/json'
        }
        self.base_url = "https://api.dhan.co/v2"
        self.bs_calc = BlackScholesCalculator()
        self.risk_free_rate = 0.07
    
    def fetch_rolling_option_current(self, symbol: str, strike_type: str, option_type: str,
                                     expiry_code: int = 1, expiry_flag: str = "WEEK"):
        """Fetch current data using rolling API"""
        try:
            security_id = DHAN_SECURITY_IDS.get(symbol, 13)
            
            today = datetime.now(IST).date()
            from_date = (today - timedelta(days=1)).strftime('%Y-%m-%d')
            to_date = today.strftime('%Y-%m-%d')
            
            payload = {
                "exchangeSegment": "NSE_FNO",
                "interval": "1",
                "securityId": security_id,
                "instrument": "OPTIDX",
                "expiryFlag": expiry_flag,
                "expiryCode": expiry_code,
                "strike": strike_type,
                "drvOptionType": option_type,
                "requiredData": ["open", "high", "low", "close", "volume", "oi", "iv", "strike", "spot"],
                "fromDate": from_date,
                "toDate": to_date
            }
            
            response = requests.post(
                f"{self.base_url}/charts/rollingoption",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('data', {})
            return None
            
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return None
    
    def process_live_data(self, symbol: str, strikes: List[str], 
                         expiry_code: int = 1, expiry_flag: str = "WEEK"):
        """Process LIVE data"""
        config = SYMBOL_CONFIG.get(symbol, SYMBOL_CONFIG["NIFTY"])
        contract_size = config["contract_size"]
        
        st.info(f"🔍 Fetching LIVE data for {symbol}...")
        
        all_data = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_steps = len(strikes) * 2
        current_step = 0
        
        spot_prices = []
        
        for strike_type in strikes:
            status_text.text(f"📡 Fetching {strike_type}...")
            
            # Fetch CALL
            call_data = self.fetch_rolling_option_current(
                symbol, strike_type, "CALL", expiry_code, expiry_flag
            )
            current_step += 1
            progress_bar.progress(current_step / total_steps)
            
            # Fetch PUT
            put_data = self.fetch_rolling_option_current(
                symbol, strike_type, "PUT", expiry_code, expiry_flag
            )
            current_step += 1
            progress_bar.progress(current_step / total_steps)
            
            if not call_data or not put_data:
                st.warning(f"⚠️ No data for {strike_type}")
                time.sleep(0.5)
                continue
            
            ce_data = call_data.get('ce', {})
            pe_data = put_data.get('pe', {})
            
            if not ce_data:
                st.warning(f"⚠️ Empty CE data for {strike_type}")
                continue
            
            timestamps = ce_data.get('timestamp', [])
            if not timestamps:
                continue
            
            # Use LAST timestamp
            idx = -1
            ts = timestamps[idx]
            
            dt_utc = datetime.fromtimestamp(ts, tz=pytz.UTC)
            dt_ist = dt_utc.astimezone(IST)
            
            spot_price = ce_data.get('spot', [0])[idx] if idx < len(ce_data.get('spot', [])) else 0
            strike_price = ce_data.get('strike', [0])[idx] if idx < len(ce_data.get('strike', [])) else 0
            
            if spot_price > 0:
                spot_prices.append(spot_price)
            
            if spot_price == 0 or strike_price == 0:
                st.warning(f"⚠️ Zero values for {strike_type}")
                continue
            
            call_oi = ce_data.get('oi', [0])[idx] if idx < len(ce_data.get('oi', [])) else 0
            put_oi = pe_data.get('oi', [0])[idx] if idx < len(pe_data.get('oi', [])) else 0
            call_volume = ce_data.get('volume', [0])[idx] if idx < len(ce_data.get('volume', [])) else 0
            put_volume = pe_data.get('volume', [0])[idx] if idx < len(pe_data.get('volume', [])) else 0
            call_iv = ce_data.get('iv', [15])[idx] if idx < len(ce_data.get('iv', [])) else 15
            put_iv = pe_data.get('iv', [15])[idx] if idx < len(pe_data.get('iv', [])) else 15
            
            # Calculate Greeks
            time_to_expiry = 7 / 365
            call_iv_dec = call_iv / 100 if call_iv > 1 else call_iv
            put_iv_dec = put_iv / 100 if put_iv > 1 else put_iv
            
            call_gamma = self.bs_calc.calculate_gamma(spot_price, strike_price, time_to_expiry, self.risk_free_rate, call_iv_dec)
            put_gamma = self.bs_calc.calculate_gamma(spot_price, strike_price, time_to_expiry, self.risk_free_rate, put_iv_dec)
            call_delta = self.bs_calc.calculate_call_delta(spot_price, strike_price, time_to_expiry, self.risk_free_rate, call_iv_dec)
            put_delta = self.bs_calc.calculate_put_delta(spot_price, strike_price, time_to_expiry, self.risk_free_rate, put_iv_dec)
            call_vanna = self.bs_calc.calculate_vanna(spot_price, strike_price, time_to_expiry, self.risk_free_rate, call_iv_dec)
            put_vanna = self.bs_calc.calculate_vanna(spot_price, strike_price, time_to_expiry, self.risk_free_rate, put_iv_dec)
            call_charm = self.bs_calc.calculate_charm(spot_price, strike_price, time_to_expiry, self.risk_free_rate, call_iv_dec)
            put_charm = self.bs_calc.calculate_charm(spot_price, strike_price, time_to_expiry, self.risk_free_rate, put_iv_dec)
            
            # Calculate exposures
            call_gex = (call_oi * call_gamma * spot_price**2 * contract_size) / 1e9
            put_gex = -(put_oi * put_gamma * spot_price**2 * contract_size) / 1e9
            call_dex = (call_oi * call_delta * spot_price * contract_size) / 1e9
            put_dex = (put_oi * put_delta * spot_price * contract_size) / 1e9
            call_vanna_exp = (call_oi * call_vanna * spot_price * contract_size) / 1e9
            put_vanna_exp = (put_oi * put_vanna * spot_price * contract_size) / 1e9
            call_charm_exp = (call_oi * call_charm * spot_price * contract_size) / 1e9
            put_charm_exp = (put_oi * put_charm * spot_price * contract_size) / 1e9
            
            all_data.append({
                'timestamp': dt_ist,
                'time': dt_ist.strftime('%H:%M:%S IST'),
                'spot_price': spot_price,
                'strike': strike_price,
                'strike_type': strike_type,
                'call_oi': call_oi,
                'put_oi': put_oi,
                'call_volume': call_volume,
                'put_volume': put_volume,
                'total_volume': call_volume + put_volume,
                'call_iv': call_iv,
                'put_iv': put_iv,
                'call_gex': call_gex,
                'put_gex': put_gex,
                'net_gex': call_gex + put_gex,
                'call_dex': call_dex,
                'put_dex': put_dex,
                'net_dex': call_dex + put_dex,
                'call_vanna': call_vanna_exp,
                'put_vanna': put_vanna_exp,
                'net_vanna': call_vanna_exp + put_vanna_exp,
                'call_charm': call_charm_exp,
                'put_charm': put_charm_exp,
                'net_charm': call_charm_exp + put_charm_exp,
            })
            
            st.success(f"✅ {strike_type}: ₹{strike_price:,.0f} | OI C:{call_oi:,} P:{put_oi:,}")
            time.sleep(0.5)
        
        progress_bar.empty()
        status_text.empty()
        
        if not all_data:
            return None, None
        
        df = pd.DataFrame(all_data)
        
        # Calculate hedging pressure
        max_gex = df['net_gex'].abs().max()
        df['hedging_pressure'] = (df['net_gex'] / max_gex * 100) if max_gex > 0 else 0
        
        final_spot = np.median(spot_prices) if spot_prices else df['spot_price'].median()
        
        meta = {
            'symbol': symbol,
            'spot_price': final_spot,
            'time': df['time'].iloc[-1],
            'total_records': len(df),
            'strikes_count': df['strike'].nunique(),
            'expiry_code': expiry_code,
            'expiry_flag': expiry_flag
        }
        
        st.success(f"✅ Successfully fetched {len(df)} records | Spot: ₹{final_spot:,.2f}")
        
        return df, meta

# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def create_gex_chart(df: pd.DataFrame, spot_price: float, for_telegram: bool = False) -> go.Figure:
    df_sorted = df.sort_values('strike').reset_index(drop=True)
    colors = ['#10b981' if x > 0 else '#ef4444' for x in df_sorted['net_gex']]
    flip_zones = identify_gamma_flip_zones(df_sorted, spot_price)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_sorted['strike'], x=df_sorted['net_gex'], orientation='h',
        marker_color=colors, name='Net GEX',
        hovertemplate='Strike: %{y:,.0f}<br>Net GEX: %{x:.4f}B<extra></extra>',
        showlegend=False
    ))
    
    fig.add_hline(y=spot_price, line_dash="dash", line_color="#06b6d4", line_width=3,
                  annotation_text=f"Spot: {spot_price:,.2f}", annotation_position="top right")
    
    for zone in flip_zones:
        fig.add_hline(y=zone['strike'], line_dash="dot", line_color=zone['color'], line_width=2,
                      annotation_text=f"🔄 {zone['arrow']} {zone['strike']:,.0f}", annotation_position="left")
        fig.add_hrect(y0=zone['lower_strike'], y1=zone['upper_strike'], 
                      fillcolor=zone['color'], opacity=0.1, line_width=0)
    
    height = 800 if for_telegram else 700
    
    fig.update_layout(
        title="<b>🎯 Gamma Exposure (GEX) with Flip Zones</b>",
        xaxis_title="GEX (₹B)", yaxis_title="Strike Price",
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)', height=height,
        font=dict(size=14 if for_telegram else 12)
    )
    return fig

def create_dex_chart(df: pd.DataFrame, spot_price: float) -> go.Figure:
    df_sorted = df.sort_values('strike').reset_index(drop=True)
    colors = ['#10b981' if x > 0 else '#ef4444' for x in df_sorted['net_dex']]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_sorted['strike'], x=df_sorted['net_dex'], orientation='h',
        marker_color=colors, name='Net DEX', showlegend=False
    ))
    fig.add_hline(y=spot_price, line_dash="dash", line_color="#06b6d4", line_width=3)
    
    fig.update_layout(
        title="<b>📊 Delta Exposure (DEX)</b>",
        xaxis_title="DEX (₹B)", yaxis_title="Strike Price",
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)', height=700
    )
    return fig

def create_combined_chart(df: pd.DataFrame, spot_price: float) -> go.Figure:
    df_sorted = df.sort_values('strike').reset_index(drop=True)
    df_sorted['combined'] = df_sorted['net_gex'] + df_sorted['net_dex']
    colors = ['#10b981' if x > 0 else '#ef4444' for x in df_sorted['combined']]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_sorted['strike'], x=df_sorted['combined'], orientation='h',
        marker_color=colors, name='GEX+DEX', showlegend=False
    ))
    fig.add_hline(y=spot_price, line_dash="dash", line_color="#06b6d4", line_width=3)
    
    fig.update_layout(
        title="<b>⚡ Combined GEX + DEX</b>",
        xaxis_title="Combined (₹B)", yaxis_title="Strike Price",
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)', height=700
    )
    return fig

def create_hedging_pressure_chart(df: pd.DataFrame, spot_price: float) -> go.Figure:
    """Hedging pressure chart with Flip Zones"""
    df_sorted = df.sort_values('strike').reset_index(drop=True)
    flip_zones = identify_gamma_flip_zones(df_sorted, spot_price)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=df_sorted['strike'],
        x=df_sorted['hedging_pressure'],
        orientation='h',
        marker=dict(
            color=df_sorted['hedging_pressure'],
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(
                title=dict(text='Pressure %', font=dict(color='white', size=12)),
                tickfont=dict(color='white'),
                x=1.02,
                len=0.7,
                thickness=20
            ),
            cmin=-100,
            cmax=100
        ),
        hovertemplate='Strike: %{y:,.0f}<br>Pressure: %{x:.1f}%<extra></extra>',
        showlegend=False
    ))
    
    fig.add_hline(y=spot_price, line_dash="dash", line_color="#06b6d4", line_width=3,
                  annotation_text=f"Spot: {spot_price:,.2f}", annotation_position="top right")
    
    fig.add_vline(x=0, line_dash="dot", line_color="gray", line_width=1)
    
    for zone in flip_zones:
        fig.add_hline(y=zone['strike'], line_dash="dot", line_color=zone['color'], line_width=2,
                      annotation_text=f"🔄 {zone['arrow']} {zone['strike']:,.0f}", annotation_position="left")
        fig.add_hrect(y0=zone['lower_strike'], y1=zone['upper_strike'], 
                      fillcolor=zone['color'], opacity=0.1, line_width=0)
    
    fig.update_layout(
        title=dict(text="<b>🎪 Hedging Pressure with Flip Zones</b>", font=dict(size=18, color='white')),
        xaxis_title="Hedging Pressure (%)",
        yaxis_title="Strike Price",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)',
        height=700,
        showlegend=False,
        hovermode='closest',
        xaxis=dict(
            gridcolor='rgba(128,128,128,0.2)', 
            showgrid=True,
            zeroline=True,
            zerolinecolor='rgba(128,128,128,0.5)',
            zerolinewidth=2,
            range=[-110, 110]
        ),
        yaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True, autorange=True),
        margin=dict(l=80, r=120, t=80, b=80)
    )
    return fig

def create_gex_overlay_chart(df: pd.DataFrame, spot_price: float) -> go.Figure:
    """GEX Overlay - for live data this shows current GEX only (no OI changes without history)"""
    df_sorted = df.sort_values('strike').reset_index(drop=True)
    
    colors = ['#10b981' if x > 0 else '#ef4444' for x in df_sorted['net_gex']]
    flip_zones = identify_gamma_flip_zones(df_sorted, spot_price)
    
    fig = go.Figure()
    
    # Current GEX
    fig.add_trace(go.Bar(
        y=df_sorted['strike'],
        x=df_sorted['net_gex'],
        orientation='h',
        marker=dict(color=colors, opacity=0.7),
        name='Current GEX',
        hovertemplate='Strike: %{y:,.0f}<br>GEX: %{x:.4f}B<extra></extra>'
    ))
    
    fig.add_hline(y=spot_price, line_dash="dash", line_color="white", line_width=3,
                  annotation_text=f"Spot: {spot_price:,.2f}", annotation_position="top right")
    
    fig.add_vline(x=0, line_dash="dot", line_color="gray", line_width=2)
    
    for zone in flip_zones:
        fig.add_hline(y=zone['strike'], line_dash="dot", line_color=zone['color'], 
                      line_width=1, opacity=0.5)
    
    fig.update_layout(
        title=dict(
            text="<b>🔄 Current GEX Snapshot</b><br><sub>OI-based overlay requires historical data (use Historical dashboard)</sub>",
            font=dict(size=18, color='white')
        ),
        xaxis_title="GEX (₹ Billions)",
        yaxis_title="Strike Price",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)',
        height=700,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            font=dict(color='white', size=11),
            bgcolor='rgba(0,0,0,0.8)',
            bordercolor='white',
            borderwidth=1
        ),
        hovermode='closest',
        xaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True, zeroline=True, 
                   zerolinecolor='rgba(255,255,255,0.3)', zerolinewidth=2),
        yaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True, autorange=True),
        margin=dict(l=80, r=80, t=100, b=80)
    )
    
    # Add info note
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        text="ℹ️ Live Mode: Single Snapshot<br>For OI-based GEX comparison, use Historical Dashboard",
        showarrow=False,
        bgcolor="rgba(59,130,246,0.2)",
        bordercolor="#3b82f6",
        borderwidth=2,
        font=dict(color="white", size=12),
        align="center"
    )
    
    return fig

def create_vanna_exposure_chart(df: pd.DataFrame, spot_price: float) -> go.Figure:
    """VANNA Exposure chart"""
    df_sorted = df.sort_values('strike').reset_index(drop=True)
    
    colors_call = ['#10b981' if x > 0 else '#ef4444' for x in df_sorted['call_vanna']]
    colors_put = ['#10b981' if x > 0 else '#ef4444' for x in df_sorted['put_vanna']]
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("📈 Call VANNA", "📉 Put VANNA"),
        horizontal_spacing=0.12
    )
    
    fig.add_trace(go.Bar(
        y=df_sorted['strike'],
        x=df_sorted['call_vanna'],
        orientation='h',
        marker=dict(color=colors_call),
        name='Call VANNA',
        hovertemplate='Strike: %{y:,.0f}<br>Call VANNA: %{x:.4f}B<extra></extra>'
    ), row=1, col=1)
    
    fig.add_trace(go.Bar(
        y=df_sorted['strike'],
        x=df_sorted['put_vanna'],
        orientation='h',
        marker=dict(color=colors_put),
        name='Put VANNA',
        hovertemplate='Strike: %{y:,.0f}<br>Put VANNA: %{x:.4f}B<extra></extra>'
    ), row=1, col=2)
    
    for col in [1, 2]:
        fig.add_hline(y=spot_price, line_dash="dash", line_color="#06b6d4", line_width=2,
                      annotation_text=f"Spot: {spot_price:,.2f}", annotation_position="top right",
                      row=1, col=col)
    
    fig.update_layout(
        title=dict(text="<b>🌊 VANNA Exposure (dDelta/dVol)</b>", font=dict(size=18, color='white')),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)',
        height=600,
        showlegend=False,
        hovermode='closest',
        margin=dict(l=80, r=80, t=100, b=80)
    )
    
    fig.update_xaxes(title_text="VANNA (₹ Billions)", gridcolor='rgba(128,128,128,0.2)', showgrid=True)
    fig.update_yaxes(title_text="Strike Price", gridcolor='rgba(128,128,128,0.2)', showgrid=True)
    
    return fig

def create_charm_exposure_chart(df: pd.DataFrame, spot_price: float) -> go.Figure:
    """CHARM Exposure chart"""
    df_sorted = df.sort_values('strike').reset_index(drop=True)
    
    colors_call = ['#10b981' if x > 0 else '#ef4444' for x in df_sorted['call_charm']]
    colors_put = ['#10b981' if x > 0 else '#ef4444' for x in df_sorted['put_charm']]
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("📈 Call CHARM", "📉 Put CHARM"),
        horizontal_spacing=0.12
    )
    
    fig.add_trace(go.Bar(
        y=df_sorted['strike'],
        x=df_sorted['call_charm'],
        orientation='h',
        marker=dict(color=colors_call),
        name='Call CHARM',
        hovertemplate='Strike: %{y:,.0f}<br>Call CHARM: %{x:.4f}B<extra></extra>'
    ), row=1, col=1)
    
    fig.add_trace(go.Bar(
        y=df_sorted['strike'],
        x=df_sorted['put_charm'],
        orientation='h',
        marker=dict(color=colors_put),
        name='Put CHARM',
        hovertemplate='Strike: %{y:,.0f}<br>Put CHARM: %{x:.4f}B<extra></extra>'
    ), row=1, col=2)
    
    for col in [1, 2]:
        fig.add_hline(y=spot_price, line_dash="dash", line_color="#06b6d4", line_width=2,
                      annotation_text=f"Spot: {spot_price:,.2f}", annotation_position="top right",
                      row=1, col=col)
    
    fig.update_layout(
        title=dict(text="<b>⏰ CHARM Exposure (Delta Decay)</b>", font=dict(size=18, color='white')),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)',
        height=600,
        showlegend=False,
        hovermode='closest',
        margin=dict(l=80, r=80, t=100, b=80)
    )
    
    fig.update_xaxes(title_text="CHARM (₹ Billions)", gridcolor='rgba(128,128,128,0.2)', showgrid=True)
    fig.update_yaxes(title_text="Strike Price", gridcolor='rgba(128,128,128,0.2)', showgrid=True)
    
    return fig

def create_oi_chart(df: pd.DataFrame, spot_price: float) -> go.Figure:
    df_sorted = df.sort_values('strike').reset_index(drop=True)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_sorted['strike'], x=df_sorted['call_oi'], orientation='h',
        name='Call OI', marker_color='#10b981', opacity=0.7
    ))
    fig.add_trace(go.Bar(
        y=df_sorted['strike'], x=-df_sorted['put_oi'], orientation='h',
        name='Put OI', marker_color='#ef4444', opacity=0.7,
        customdata=df_sorted['put_oi']
    ))
    fig.add_hline(y=spot_price, line_dash="dash", line_color="#06b6d4", line_width=2)
    fig.add_vline(x=0, line_dash="dot", line_color="white", line_width=1)
    
    fig.update_layout(
        title="<b>📋 Open Interest</b>",
        xaxis_title="OI (Calls +ve | Puts -ve)", yaxis_title="Strike Price",
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)', height=500, barmode='overlay'
    )
    return fig

def fig_to_image_bytes(fig: go.Figure) -> bytes:
    """Convert Plotly figure to PNG bytes"""
    img_bytes = fig.to_image(format="png", width=1200, height=800, scale=2)
    return img_bytes

# ============================================================================
# TELEGRAM AUTO-UPDATE
# ============================================================================

def send_telegram_update(df: pd.DataFrame, meta: Dict) -> bool:
    """Send GEX chart to Telegram"""
    try:
        telegram = TelegramSender(TELEGRAM_CONFIG.bot_token, TELEGRAM_CONFIG.chat_id)
        spot_price = meta['spot_price']
        
        strike_interval = SYMBOL_CONFIG[meta['symbol']]["strike_interval"]
        strike_range = 3 * strike_interval
        df_calc = df[(df['strike'] >= spot_price - strike_range) & 
                     (df['strike'] <= spot_price + strike_range)]
        
        total_gex = df_calc['net_gex'].sum()
        total_dex = df_calc['net_dex'].sum()
        total_net = total_gex + total_dex
        total_call_oi = df_calc['call_oi'].sum()
        total_put_oi = df_calc['put_oi'].sum()
        pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 1
        
        flip_zones = identify_gamma_flip_zones(df, spot_price)
        
        caption = f"""
<b>🔴 NYZTrade LIVE Update</b>

📊 <b>{meta['symbol']}</b> | {meta['time']}
💰 Spot: ₹{spot_price:,.2f}

📈 <b>Metrics:</b>
- GEX: {total_gex:+.4f}B {'🟢' if total_gex > 0 else '🔴'}
- DEX: {total_dex:+.4f}B {'🟢' if total_dex > 0 else '🔴'}
- Combined: {total_net:+.4f}B
- PCR: {pcr:.2f}

🔄 <b>Flip Zones: {len(flip_zones)}</b>
"""
        
        if len(flip_zones) > 0:
            for zone in flip_zones[:3]:
                caption += f"• ₹{zone['strike']:,.0f} {zone['arrow']}\n"
        
        caption += f"\n⏰ Next update in 5 minutes"
        
        fig = create_gex_chart(df, spot_price, for_telegram=True)
        img_bytes = fig_to_image_bytes(fig)
        
        return telegram.send_photo(img_bytes, caption)
        
    except Exception as e:
        st.error(f"Telegram error: {str(e)}")
        return False

# ============================================================================
# COUNTDOWN TIMER COMPONENT
# ============================================================================

def display_countdown_timer(target_time: datetime, refresh_interval: int):
    """Display countdown timer until next refresh"""
    now = datetime.now()
    seconds_remaining = int((target_time - now).total_seconds())
    
    if seconds_remaining < 0:
        seconds_remaining = 0
    
    minutes = seconds_remaining // 60
    seconds = seconds_remaining % 60
    
    # Calculate progress
    progress = 1 - (seconds_remaining / refresh_interval)
    progress = max(0, min(1, progress))
    
    st.markdown(f"""
    <div class="countdown-box">
        <div style="font-size: 0.9rem; color: #94a3b8; margin-bottom: 8px;">⏱️ AUTO-REFRESH COUNTDOWN</div>
        <div class="countdown-timer">{minutes:02d}:{seconds:02d}</div>
        <div style="font-size: 0.85rem; color: #64748b; margin-top: 8px;">Next refresh in {seconds_remaining} seconds</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.progress(progress)
    
    return seconds_remaining

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Initialize session state
    if 'telegram_enabled' not in st.session_state:
        st.session_state.telegram_enabled = TELEGRAM_CONFIG.enabled
    if 'last_telegram_update' not in st.session_state:
        st.session_state.last_telegram_update = None
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1 style="font-family: 'Space Grotesk', sans-serif; font-size: 2rem; margin: 0; background: linear-gradient(135deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                📊 NYZTrade LIVE Enhanced</h1>
                <p style="font-family: 'JetBrains Mono', monospace; color: #94a3b8; font-size: 0.9rem; margin-top: 8px;">
                Real-Time Options Greeks | Hedge Pressure | VANNA & CHARM | Telegram Auto-Updates</p>
            </div>
            <div style="display: flex; gap: 10px; align-items: center;">
                <div class="live-indicator">
                    <div class="live-dot"></div>
                    <span style="color: #ef4444; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;">🔴 LIVE</span>
                </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.telegram_enabled:
        st.markdown("""
                <div class="telegram-indicator">
                    <span style="color: #228be6; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;">📱 TELEGRAM ON</span>
                </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        
        symbol = st.selectbox("📈 Index", list(DHAN_SECURITY_IDS.keys()), index=0)
        
        st.markdown("---")
        expiry_type = st.selectbox("Expiry Type", ["Weekly", "Monthly"], index=0)
        expiry_flag = "WEEK" if expiry_type == "Weekly" else "MONTH"
        
        expiry_option = st.selectbox(
            "Select Expiry",
            ["Current (Nearest)", "Next", "Far"],
            index=0
        )
        expiry_code = {"Current (Nearest)": 1, "Next": 2, "Far": 3}[expiry_option]
        
        st.markdown("---")
        strikes = st.multiselect(
            "🎯 Strikes",
            ["ATM", "ATM+1", "ATM-1", "ATM+2", "ATM-2", "ATM+3", "ATM-3", 
             "ATM+4", "ATM-4", "ATM+5", "ATM-5"],
            default=["ATM", "ATM+1", "ATM-1", "ATM+2", "ATM-2"]
        )
        
        st.markdown("---")
        st.markdown("### 📱 Telegram Updates")
        
        telegram_enabled = st.checkbox(
            "Enable Auto-Updates", 
            value=st.session_state.telegram_enabled,
            help="Send GEX chart every 5 minutes"
        )
        
        if telegram_enabled:
            st.success("✅ Telegram Configured")
            
            token_masked = f"{TELEGRAM_CONFIG.bot_token[:15]}...{TELEGRAM_CONFIG.bot_token[-8:]}"
            st.caption(f"🤖 Bot: {token_masked}")
            st.caption(f"💬 Chat: {TELEGRAM_CONFIG.chat_id}")
            
            if st.session_state.last_telegram_update:
                last_update = st.session_state.last_telegram_update
                st.caption(f"📤 Last: {last_update.strftime('%H:%M:%S')}")
            
            if st.button("🧪 Test Connection", use_container_width=True):
                telegram = TelegramSender(TELEGRAM_CONFIG.bot_token, TELEGRAM_CONFIG.chat_id)
                if telegram.test_connection():
                    if telegram.send_message("✅ <b>Test Successful!</b>\n\nNYZTrade bot working!"):
                        st.success("✅ Message sent!")
                    else:
                        st.error("❌ Failed to send. Check chat ID.")
                else:
                    st.error("❌ Invalid bot token")
        else:
            st.info("📱 Telegram disabled")
        
        st.session_state.telegram_enabled = telegram_enabled
        
        st.markdown("---")
        auto_refresh = st.checkbox("🔄 Auto-Refresh", value=False)
        if auto_refresh:
            refresh_interval = st.slider("Interval (sec)", 30, 300, 60)
        
        st.markdown("---")
        ist_now = datetime.now(IST)
        st.info(f"🕐 IST: {ist_now.strftime('%H:%M:%S')}")
        
        st.markdown("---")
        fetch_button = st.button("🚀 Fetch LIVE Data", use_container_width=True, type="primary")
    
    # Store config
    if fetch_button:
        st.session_state.config = {
            'symbol': symbol, 'strikes': strikes,
            'expiry_code': expiry_code, 'expiry_flag': expiry_flag
        }
        st.session_state.fetched = False
        st.session_state.last_refresh = datetime.now()
    
    # Auto-refresh with countdown
    if auto_refresh and st.session_state.get('fetched', False):
        next_refresh_time = st.session_state.last_refresh + timedelta(seconds=refresh_interval)
        seconds_remaining = display_countdown_timer(next_refresh_time, refresh_interval)
        
        if seconds_remaining <= 0:
            st.session_state.fetched = False
            st.rerun()
        
        # Auto-rerun every second to update countdown
        time.sleep(1)
        st.rerun()
    
    # Telegram auto-update
    if st.session_state.telegram_enabled and TELEGRAM_CONFIG.enabled:
        if st.session_state.get('fetched', False) and 'df' in st.session_state:
            last_update = st.session_state.last_telegram_update
            
            if last_update is None or (datetime.now() - last_update).total_seconds() >= 300:
                df = st.session_state.df
                meta = st.session_state.meta
                
                if send_telegram_update(df, meta):
                    st.session_state.last_telegram_update = datetime.now()
                    st.success(f"📱 Telegram update sent at {datetime.now(IST).strftime('%H:%M:%S')}")
    
    # Main content
    if fetch_button or (hasattr(st.session_state, 'config') and st.session_state.get('fetched', False)):
        if hasattr(st.session_state, 'config'):
            config = st.session_state.config
            symbol = config['symbol']
            strikes = config['strikes']
            expiry_code = config['expiry_code']
            expiry_flag = config['expiry_flag']
        
        if not strikes:
            st.error("❌ Please select strikes")
            return
        
        if not st.session_state.get('fetched', False):
            with st.spinner("🔴 Fetching LIVE data..."):
                try:
                    fetcher = DhanLiveFetcher(DhanConfig())
                    df, meta = fetcher.process_live_data(symbol, strikes, expiry_code, expiry_flag)
                    
                    if df is None or len(df) == 0:
                        st.error("❌ No data. Check market hours or API.")
                        return
                    
                    st.session_state.df = df
                    st.session_state.meta = meta
                    st.session_state.fetched = True
                    st.session_state.last_refresh = datetime.now()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    return
        
        # Display data
        df = st.session_state.df
        meta = st.session_state.meta
        spot_price = meta['spot_price']
        
        st.success(f"✅ {meta['time']} | Spot: ₹{spot_price:,.2f} | {meta['strikes_count']} strikes")
        
        # Metrics
        strike_interval = SYMBOL_CONFIG[symbol]["strike_interval"]
        strike_range = 3 * strike_interval
        df_calc = df[(df['strike'] >= spot_price - strike_range) & 
                     (df['strike'] <= spot_price + strike_range)]
        
        total_gex = df_calc['net_gex'].sum()
        total_dex = df_calc['net_dex'].sum()
        total_net = total_gex + total_dex
        total_call_oi = df_calc['call_oi'].sum()
        total_put_oi = df_calc['put_oi'].sum()
        pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 1
        
        flip_zones = identify_gamma_flip_zones(df, spot_price)
        
        st.markdown("### 📊 Live Metrics")
        
        cols = st.columns(5)
        with cols[0]:
            st.markdown(f"""<div class="metric-card neutral">
                <div style="font-size: 0.75rem; color: #64748b;">SPOT PRICE</div>
                <div style="font-size: 1.5rem; font-weight: 700;">₹{spot_price:,.2f}</div>
            </div>""", unsafe_allow_html=True)
        
        with cols[1]:
            gex_class = "positive" if total_gex > 0 else "negative"
            st.markdown(f"""<div class="metric-card {gex_class}">
                <div style="font-size: 0.75rem; color: #64748b;">NET GEX</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: {'#10b981' if total_gex > 0 else '#ef4444'};">{total_gex:.4f}B</div>
            </div>""", unsafe_allow_html=True)
        
        with cols[2]:
            dex_class = "positive" if total_dex > 0 else "negative"
            st.markdown(f"""<div class="metric-card {dex_class}">
                <div style="font-size: 0.75rem; color: #64748b;">NET DEX</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: {'#10b981' if total_dex > 0 else '#ef4444'};">{total_dex:.4f}B</div>
            </div>""", unsafe_allow_html=True)
        
        with cols[3]:
            net_class = "positive" if total_net > 0 else "negative"
            st.markdown(f"""<div class="metric-card {net_class}">
                <div style="font-size: 0.75rem; color: #64748b;">COMBINED</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: {'#10b981' if total_net > 0 else '#ef4444'};">{total_net:.4f}B</div>
            </div>""", unsafe_allow_html=True)
        
        with cols[4]:
            pcr_class = "positive" if pcr > 1 else "negative"
            st.markdown(f"""<div class="metric-card {pcr_class}">
                <div style="font-size: 0.75rem; color: #64748b;">PCR</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: {'#10b981' if pcr > 1 else '#ef4444'};">{pcr:.2f}</div>
            </div>""", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Signal badges
        cols = st.columns(4)
        with cols[0]:
            badge = "bullish" if total_gex > 0 else "bearish"
            st.markdown(f'<div class="signal-badge {badge}">{"🟢 SUPPRESSION" if total_gex > 0 else "🔴 AMPLIFICATION"}</div>', unsafe_allow_html=True)
        with cols[1]:
            badge = "bullish" if total_dex > 0 else "bearish"
            st.markdown(f'<div class="signal-badge {badge}">{"🟢 BULLISH" if total_dex > 0 else "🔴 BEARISH"}</div>', unsafe_allow_html=True)
        with cols[2]:
            badge = "bullish" if total_net > 0 else "bearish"
            st.markdown(f'<div class="signal-badge {badge}">{"🟢 POSITIVE" if total_net > 0 else "🔴 NEGATIVE"}</div>', unsafe_allow_html=True)
        with cols[3]:
            if len(flip_zones) > 0:
                st.markdown(f'<div class="signal-badge" style="background: rgba(245,158,11,0.15); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3);">🔄 {len(flip_zones)} FLIPS</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Telegram status
        if st.session_state.telegram_enabled and TELEGRAM_CONFIG.enabled:
            if st.session_state.last_telegram_update:
                next_update_time = st.session_state.last_telegram_update + timedelta(seconds=300)
                seconds_until_next = (next_update_time - datetime.now()).total_seconds()
                
                if seconds_until_next > 0:
                    minutes = int(seconds_until_next // 60)
                    seconds = int(seconds_until_next % 60)
                    st.info(f"📱 Next Telegram update in {minutes}m {seconds}s")
                else:
                    st.warning("📱 Telegram update pending...")
            else:
                st.info("📱 First Telegram update on next refresh")
        
        # Charts
        tabs = st.tabs(["🎯 GEX", "📊 DEX", "⚡ Combined", "🎪 Hedge Pressure", 
                        "🔄 GEX Overlay", "🌊 VANNA", "⏰ CHARM", "📋 OI", "📥 Data"])
        
        with tabs[0]:
            st.plotly_chart(create_gex_chart(df, spot_price), use_container_width=True)
            if len(flip_zones) > 0:
                st.markdown("#### 🔄 Flip Zones")
                for zone in flip_zones:
                    st.markdown(f"- **₹{zone['strike']:,.0f}** {zone['arrow']} {zone['flip_type']}")
        
        with tabs[1]:
            st.plotly_chart(create_dex_chart(df, spot_price), use_container_width=True)
        
        with tabs[2]:
            st.plotly_chart(create_combined_chart(df, spot_price), use_container_width=True)
        
        with tabs[3]:
            st.markdown("### 🎪 Hedging Pressure Analysis")
            st.markdown("""
            **Understanding Hedging Pressure:**
            - Shows normalized GEX at each strike (-100% to +100%)
            - **Positive (Green)**: Dealers need to sell on rallies (suppression)
            - **Negative (Red)**: Dealers need to buy on rallies (amplification)
            - **Flip zones** show critical dealer hedging transitions
            """)
            st.plotly_chart(create_hedging_pressure_chart(df, spot_price), use_container_width=True)
        
        with tabs[4]:
            st.markdown("### 🔄 GEX Snapshot")
            st.info("ℹ️ **Live Mode Limitation**: OI-based overlay requires historical time series data. Use the Historical Dashboard for full OI flow analysis.")
            st.plotly_chart(create_gex_overlay_chart(df, spot_price), use_container_width=True)
        
        with tabs[5]:
            st.markdown("### 🌊 VANNA Exposure (dDelta/dVol)")
            st.markdown("""
            **VANNA Interpretation:**
            - Measures how delta changes with volatility
            - **Positive VANNA**: Delta increases as IV increases
            - **Important for**: Hedging in volatile markets
            - **High VANNA strikes**: Sensitive to IV changes
            """)
            st.plotly_chart(create_vanna_exposure_chart(df, spot_price), use_container_width=True)
            
            total_call_vanna = df['call_vanna'].sum()
            total_put_vanna = df['put_vanna'].sum()
            net_vanna = df['net_vanna'].sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Call VANNA", f"{total_call_vanna:.4f}B")
            with col2:
                st.metric("Total Put VANNA", f"{total_put_vanna:.4f}B")
            with col3:
                st.metric("Net VANNA", f"{net_vanna:.4f}B")
        
        with tabs[6]:
            st.markdown("### ⏰ CHARM Exposure (Delta Decay)")
            st.markdown("""
            **CHARM Interpretation:**
            - Measures delta decay over time
            - **Shows**: How delta changes as expiration approaches
            - **Critical for**: Understanding time decay effects
            - **High CHARM strikes**: Delta will change significantly with time
            """)
            st.plotly_chart(create_charm_exposure_chart(df, spot_price), use_container_width=True)
            
            total_call_charm = df['call_charm'].sum()
            total_put_charm = df['put_charm'].sum()
            net_charm = df['net_charm'].sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Call CHARM", f"{total_call_charm:.4f}B")
            with col2:
                st.metric("Total Put CHARM", f"{total_put_charm:.4f}B")
            with col3:
                st.metric("Net CHARM", f"{net_charm:.4f}B")
        
        with tabs[7]:
            st.plotly_chart(create_oi_chart(df, spot_price), use_container_width=True)
        
        with tabs[8]:
            display_df = df[['strike', 'call_oi', 'put_oi', 'call_volume', 'put_volume', 
                           'net_gex', 'net_dex', 'net_vanna', 'net_charm']].copy()
            display_df['net_gex'] = display_df['net_gex'].apply(lambda x: f"{x:.4f}B")
            display_df['net_dex'] = display_df['net_dex'].apply(lambda x: f"{x:.4f}B")
            display_df['net_vanna'] = display_df['net_vanna'].apply(lambda x: f"{x:.4f}B")
            display_df['net_charm'] = display_df['net_charm'].apply(lambda x: f"{x:.4f}B")
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False)
            st.download_button(
                "📄 Download CSV",
                data=csv,
                file_name=f"NYZTrade_{symbol}_{datetime.now(IST).strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    else:
        st.info("""
        👋 **Welcome to NYZTrade LIVE Enhanced!**
        
        **🆕 New Features:**
        - ⏱️ **Auto-Refresh Countdown Timer** - Visual countdown to next refresh
        - 🎪 **Hedging Pressure Analysis** - Normalized GEX with flip zones
        - 🔄 **GEX Overlay** - Current snapshot (full overlay in Historical)
        - 🌊 **VANNA Exposure** - Delta sensitivity to volatility
        - ⏰ **CHARM Exposure** - Delta decay over time
        
        **Original Features:**
        - 🔴 Real-time market data
        - 📱 Auto-send GEX chart every 5 minutes to Telegram
        - 📊 GEX, DEX, Combined analysis
        - 🔄 Gamma flip zones
        - ⚡ Auto-refresh capability
        
        **How to use:**
        1. Configure settings in sidebar
        2. Enable Telegram & Auto-Refresh (optional)
        3. Click "Fetch LIVE Data"
        4. Watch countdown timer and charts update
        5. Explore 9 comprehensive analysis tabs
        
        **Pro Tips:**
        - Enable Auto-Refresh to see countdown timer
        - VANNA/CHARM show advanced Greeks sensitivity
        - Hedging Pressure reveals dealer positioning strength
        - For OI flow analysis, use Historical Dashboard
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 20px; color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem;">
    NYZTrade LIVE Enhanced | Countdown Timer | Hedge Pressure | VANNA & CHARM | ⚠️ Educational only
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
