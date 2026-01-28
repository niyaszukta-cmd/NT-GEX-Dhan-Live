# ============================================================================
# NYZTrade LIVE GEX/DEX Dashboard - WITH TELEGRAM AUTO-UPDATES
# Telegram credentials configured in code (not UI)
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
import io
warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="NYZTrade LIVE + Telegram",
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
    access_token: str = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY5MzI2MTMxLCJhcHBfaWQiOiJjOTNkM2UwOSIsImlhdCI6MTc2OTIzOTczMSwidG9rZW5Db25zdW1lclR5cGUiOiJBUFAiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMDQ4MDM1NCJ9.4trDIGZjd0TqGLrVL4dIk3vrrOexCnJ0AYbls7IlBf4dB74zZj00jgTGjmWyfO66T8nVnPVMKRb-OyGKkwva3Q"

# ============================================================================
# TELEGRAM CONFIGURATION - ⬇️ EDIT YOUR CREDENTIALS HERE ⬇️
# ============================================================================

@dataclass
class TelegramConfig:
    # 🤖 Bot Token - Get from @BotFather on Telegram
    # Example: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
    bot_token: str = "8429392375:AAESOsxilsEOaj..."  # ← PASTE YOUR FULL TOKEN HERE
    
    # 💬 Chat ID - Your channel/group ID
    # Example: "-1001234567890" (for channel, starts with -100)
    chat_id: str = "-1002570595829"  # ← PASTE YOUR CHAT ID HERE
    
    # ⚙️ Enable/Disable Telegram Updates (True/False)
    enabled: bool = True  # Set to False to completely disable Telegram

TELEGRAM_CONFIG = TelegramConfig()

# ============================================================================

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
# TELEGRAM BOT INTEGRATION
# ============================================================================

class TelegramSender:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, text: str) -> bool:
        """Send text message to Telegram"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            st.error(f"Telegram message error: {str(e)}")
            return False
    
    def send_photo(self, image_bytes: bytes, caption: str = "") -> bool:
        """Send photo to Telegram"""
        try:
            url = f"{self.base_url}/sendPhoto"
            files = {'photo': ('chart.png', image_bytes, 'image/png')}
            data = {
                'chat_id': self.chat_id,
                'caption': caption,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, files=files, data=data, timeout=30)
            return response.status_code == 200
        except Exception as e:
            st.error(f"Telegram photo error: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """Test bot connection"""
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                bot_info = response.json()
                return bot_info.get('ok', False)
            return False
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
                    direction = "upward"
                    arrow = "↑"
                    color = "#ef4444"
                else:
                    direction = "downward"
                    arrow = "↓"
                    color = "#10b981"
            else:
                if current_gex < 0:
                    direction = "downward"
                    arrow = "↓"
                    color = "#10b981"
                else:
                    direction = "upward"
                    arrow = "↑"
                    color = "#ef4444"
            
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
# DHAN LIVE API FETCHER
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
    
    def fetch_live_option_chain(self, symbol: str, strikes: List[str], 
                                expiry_code: int = 1, expiry_flag: str = "WEEK"):
        try:
            security_id = DHAN_SECURITY_IDS.get(symbol, 13)
            
            # Get spot price
            spot_payload = {"exchangeSegment": "NSE_FNO", "securityId": security_id}
            spot_response = requests.post(f"{self.base_url}/marketfeed/quote", 
                                         headers=self.headers, json=spot_payload, timeout=10)
            
            spot_price = 0
            if spot_response.status_code == 200:
                spot_price = spot_response.json().get('data', {}).get('LTP', 0)
            
            if spot_price == 0:
                return None, spot_price
            
            # Fetch option chain
            all_data = []
            
            for strike_type in strikes:
                # CALL
                call_payload = {
                    "exchangeSegment": "NSE_FNO", "securityId": security_id,
                    "instrument": "OPTIDX", "expiryFlag": expiry_flag,
                    "expiryCode": expiry_code, "strike": strike_type, "drvOptionType": "CALL"
                }
                call_response = requests.post(f"{self.base_url}/optionchain", 
                                             headers=self.headers, json=call_payload, timeout=10)
                
                # PUT
                put_payload = call_payload.copy()
                put_payload["drvOptionType"] = "PUT"
                put_response = requests.post(f"{self.base_url}/optionchain", 
                                            headers=self.headers, json=put_payload, timeout=10)
                
                if call_response.status_code != 200 or put_response.status_code != 200:
                    continue
                
                call_data = call_response.json().get('data', {})
                put_data = put_response.json().get('data', {})
                
                if not call_data or not put_data:
                    continue
                
                all_data.append({
                    'strike': call_data.get('strike', 0),
                    'strike_type': strike_type,
                    'call_oi': call_data.get('openInterest', 0),
                    'put_oi': put_data.get('openInterest', 0),
                    'call_volume': call_data.get('volume', 0),
                    'put_volume': put_data.get('volume', 0),
                    'call_iv': call_data.get('iv', 15),
                    'put_iv': put_data.get('iv', 15),
                    'spot_price': spot_price
                })
                
                time.sleep(0.5)
            
            return all_data, spot_price
            
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return None, 0
    
    def process_live_data(self, symbol: str, strikes: List[str], 
                         expiry_code: int = 1, expiry_flag: str = "WEEK"):
        config = SYMBOL_CONFIG.get(symbol, SYMBOL_CONFIG["NIFTY"])
        contract_size = config["contract_size"]
        
        raw_data, spot_price = self.fetch_live_option_chain(symbol, strikes, expiry_code, expiry_flag)
        
        if not raw_data or spot_price == 0:
            return None, None
        
        current_time = datetime.now(IST)
        processed_data = []
        
        for row in raw_data:
            strike_price = row['strike']
            call_oi = row['call_oi']
            put_oi = row['put_oi']
            call_volume = row['call_volume']
            put_volume = row['put_volume']
            call_iv = row['call_iv']
            put_iv = row['put_iv']
            
            time_to_expiry = 7 / 365
            call_iv_dec = call_iv / 100 if call_iv > 1 else call_iv
            put_iv_dec = put_iv / 100 if put_iv > 1 else put_iv
            
            # Calculate Greeks
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
            
            processed_data.append({
                'timestamp': current_time,
                'time': current_time.strftime('%H:%M:%S IST'),
                'spot_price': spot_price,
                'strike': strike_price,
                'strike_type': row['strike_type'],
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
        
        df = pd.DataFrame(processed_data)
        
        # Calculate hedging pressure
        max_gex = df['net_gex'].abs().max()
        df['hedging_pressure'] = (df['net_gex'] / max_gex * 100) if max_gex > 0 else 0
        
        meta = {
            'symbol': symbol,
            'spot_price': spot_price,
            'time': current_time.strftime('%H:%M:%S IST'),
            'total_records': len(df),
            'strikes_count': df['strike'].nunique(),
            'expiry_code': expiry_code,
            'expiry_flag': expiry_flag
        }
        
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
# TELEGRAM AUTO-UPDATE FUNCTION
# ============================================================================

def send_telegram_update(df: pd.DataFrame, meta: Dict) -> bool:
    """Send GEX chart and summary to Telegram"""
    try:
        telegram = TelegramSender(TELEGRAM_CONFIG.bot_token, TELEGRAM_CONFIG.chat_id)
        spot_price = meta['spot_price']
        
        # Calculate metrics
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
        
        # Create caption
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
        
        # Create chart
        fig = create_gex_chart(df, spot_price, for_telegram=True)
        
        # Convert to image
        img_bytes = fig_to_image_bytes(fig)
        
        # Send to Telegram
        success = telegram.send_photo(img_bytes, caption)
        
        return success
        
    except Exception as e:
        st.error(f"Telegram update error: {str(e)}")
        return False

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Initialize session state
    if 'telegram_enabled' not in st.session_state:
        st.session_state.telegram_enabled = TELEGRAM_CONFIG.enabled
    if 'last_telegram_update' not in st.session_state:
        st.session_state.last_telegram_update = None
    
    # Header
    st.markdown("""
    <div class="main-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1 style="font-family: 'Space Grotesk', sans-serif; font-size: 2rem; margin: 0; background: linear-gradient(135deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                📊 NYZTrade LIVE + Telegram</h1>
                <p style="font-family: 'JetBrains Mono', monospace; color: #94a3b8; font-size: 0.9rem; margin-top: 8px;">
                Real-Time GEX/DEX | Auto Telegram Updates Every 5 Min | Gamma Flip Zones</p>
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
            help="Send GEX chart every 5 minutes to Telegram"
        )
        
        if telegram_enabled:
            st.success("✅ Telegram Configured")
            
            # Show masked credentials
            token_masked = f"{TELEGRAM_CONFIG.bot_token[:15]}...{TELEGRAM_CONFIG.bot_token[-8:]}"
            st.caption(f"🤖 Bot: {token_masked}")
            st.caption(f"💬 Chat: {TELEGRAM_CONFIG.chat_id}")
            
            if st.session_state.last_telegram_update:
                last_update = st.session_state.last_telegram_update
                st.caption(f"📤 Last: {last_update.strftime('%H:%M:%S')}")
            
            # Test button
            if st.button("🧪 Test Connection", use_container_width=True):
                telegram = TelegramSender(TELEGRAM_CONFIG.bot_token, TELEGRAM_CONFIG.chat_id)
                if telegram.test_connection():
                    if telegram.send_message("✅ <b>Test Successful!</b>\n\nNYZTrade bot is working perfectly!"):
                        st.success("✅ Message sent!")
                    else:
                        st.error("❌ Failed to send. Check chat ID.")
                else:
                    st.error("❌ Invalid bot token")
        else:
            st.info("📱 Telegram updates disabled")
            st.caption("Enable checkbox above to activate")
        
        st.session_state.telegram_enabled = telegram_enabled
        
        st.markdown("---")
        auto_refresh = st.checkbox("🔄 Auto-Refresh", value=False)
        if auto_refresh:
            refresh_interval = st.slider("Interval (sec)", 10, 300, 60)
        
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
    
    # Auto-refresh
    if auto_refresh and 'last_refresh' in st.session_state:
        if (datetime.now() - st.session_state.last_refresh).total_seconds() >= refresh_interval:
            st.session_state.fetched = False
            st.rerun()
    
    # Telegram auto-update check (every 5 minutes = 300 seconds)
    if st.session_state.telegram_enabled and TELEGRAM_CONFIG.enabled:
        if st.session_state.get('fetched', False) and 'df' in st.session_state:
            last_update = st.session_state.last_telegram_update
            
            if last_update is None or (datetime.now() - last_update).total_seconds() >= 300:
                # Send update
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
                        st.error("❌ No data. Check market hours.")
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
        tabs = st.tabs(["🎯 GEX", "📊 DEX", "⚡ Combined", "📋 Open Interest", "📥 Data"])
        
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
            st.plotly_chart(create_oi_chart(df, spot_price), use_container_width=True)
        
        with tabs[4]:
            display_df = df[['strike', 'call_oi', 'put_oi', 'call_volume', 'put_volume', 
                           'net_gex', 'net_dex']].copy()
            display_df['net_gex'] = display_df['net_gex'].apply(lambda x: f"{x:.4f}B")
            display_df['net_dex'] = display_df['net_dex'].apply(lambda x: f"{x:.4f}B")
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
        👋 **Welcome to NYZTrade LIVE + Telegram!**
        
        **🆕 Telegram Features:**
        - 📱 Auto-send GEX chart every 5 minutes
        - 📊 Summary with GEX, DEX, PCR metrics
        - 🔄 Flip zone alerts
        - ⏰ Timestamp on every update
        
        **Setup:**
        1. Edit `app.py` lines 85-90 with your credentials
        2. Deploy to Railway
        3. Enable "Telegram Updates" checkbox
        4. Done! Updates auto-send every 5 min
        
        **Other Features:**
        - 🔴 Real-time market data
        - 📊 GEX, DEX, Combined analysis
        - 🔄 Gamma flip zones
        - ⚡ Auto-refresh capability
        
        **How to use:**
        1. Configure settings in sidebar
        2. Enable Telegram (optional)
        3. Click "Fetch LIVE Data"
        4. Charts update automatically
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 20px; color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem;">
    NYZTrade LIVE + Telegram | Auto-Updates Every 5 Min | ⚠️ Educational purposes only
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
