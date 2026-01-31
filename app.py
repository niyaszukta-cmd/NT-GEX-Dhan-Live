# ============================================================================
# NYZTrade LIVE GEX/DEX Dashboard - ENHANCED VERSION
# Features: Live Data | Weekly Options | VANNA & CHARM | Gamma Flip Zones | Auto-Refresh
# ===========================================================================

# Standard imports
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
# PAGE CONFIG & STYLING
# ============================================================================

st.set_page_config(
    page_title="NYZTrade Live GEX/DEX Enhanced",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Dark Theme CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    
    /* Hide GitHub link */
    header[data-testid="stHeader"] a[href*="github"] {
        display: none !important;
    }
    
    button[kind="header"][data-testid="baseButton-header"] svg {
        display: none !important;
    }
    
    a[aria-label*="GitHub"],
    a[aria-label*="github"],
    a[href*="github.com"] {
        display: none !important;
    }
    
    :root {
        --bg-primary: #0a0e17;
        --bg-secondary: #111827;
        --bg-card: #1a2332;
        --bg-card-hover: #232f42;
        --accent-green: #10b981;
        --accent-red: #ef4444;
        --accent-blue: #3b82f6;
        --accent-purple: #8b5cf6;
        --accent-yellow: #f59e0b;
        --accent-cyan: #06b6d4;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --border-color: #2d3748;
    }
    
    .stApp {
        background: linear-gradient(135deg, var(--bg-primary) 0%, #0f172a 50%, var(--bg-primary) 100%);
    }
    
    .main-header {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        backdrop-filter: blur(10px);
    }
    
    .main-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #3b82f6, #8b5cf6, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    .sub-title {
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-secondary);
        font-size: 0.9rem;
        margin-top: 8px;
    }
    
    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 20px;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        background: var(--bg-card-hover);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }
    
    .metric-card.positive { border-left: 4px solid var(--accent-green); }
    .metric-card.negative { border-left: 4px solid var(--accent-red); }
    .metric-card.neutral { border-left: 4px solid var(--accent-yellow); }
    
    .metric-label {
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-muted);
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 8px;
    }
    
    .metric-value {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1.2;
    }
    
    .metric-value.positive { color: var(--accent-green); }
    .metric-value.negative { color: var(--accent-red); }
    .metric-value.neutral { color: var(--accent-yellow); }
    
    .metric-delta {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        margin-top: 8px;
        color: var(--text-secondary);
    }
    
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
    
    .signal-badge.volatile {
        background: rgba(245, 158, 11, 0.15);
        color: var(--accent-yellow);
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    
    .live-indicator {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 20px;
        animation: pulse 2s infinite;
    }
    
    .live-dot {
        width: 8px;
        height: 8px;
        background: var(--accent-red);
        border-radius: 50%;
        animation: blink 1s infinite;
    }
    
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0.3; }
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    .countdown-timer {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 20px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9rem;
        color: var(--accent-blue);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class DhanConfig:
    client_id: str = "1100480354"
    access_token: str = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY5OTc1MjA2LCJhcHBfaWQiOiJjOTNkM2UwOSIsImlhdCI6MTc2OTg4ODgwNiwidG9rZW5Db25zdW1lclR5cGUiOiJBUFAiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMDQ4MDM1NCJ9.LF4-rlL4nxwwdyv4R1vWLTzW2AeJEssxoYA2r1dWtrApkDFnYH4vGmdHFPyFctwV7iVi56pn52CUA3hK2ew63w"
DHAN_SECURITY_IDS = {
    "NIFTY": 13, "BANKNIFTY": 25, "FINNIFTY": 27, "MIDCPNIFTY": 442
}

SYMBOL_CONFIG = {
    "NIFTY": {"contract_size": 25, "strike_interval": 50},
    "BANKNIFTY": {"contract_size": 15, "strike_interval": 100},
    "FINNIFTY": {"contract_size": 40, "strike_interval": 50},
    "MIDCPNIFTY": {"contract_size": 75, "strike_interval": 25},
}

# Indian timezone
IST = pytz.timezone('Asia/Kolkata')

# ============================================================================
# BLACK-SCHOLES CALCULATOR (ENHANCED WITH VANNA & CHARM)
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
        """Calculate Vanna (dDelta/dVol)"""
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return 0
        try:
            d1 = BlackScholesCalculator.calculate_d1(S, K, T, r, sigma)
            d2 = BlackScholesCalculator.calculate_d2(S, K, T, r, sigma)
            vanna = -norm.pdf(d1) * d2 / sigma
            return vanna
        except:
            return 0
    
    @staticmethod
    def calculate_charm(S, K, T, r, sigma, option_type='call'):
        """Calculate Charm (Delta Decay)"""
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return 0
        try:
            d1 = BlackScholesCalculator.calculate_d1(S, K, T, r, sigma)
            d2 = BlackScholesCalculator.calculate_d2(S, K, T, r, sigma)
            charm = -norm.pdf(d1) * (2*r*T - d2*sigma*np.sqrt(T)) / (2*T*sigma*np.sqrt(T))
            return charm
        except:
            return 0

# ============================================================================
# GAMMA FLIP ZONE CALCULATOR
# ============================================================================

def identify_gamma_flip_zones(df: pd.DataFrame, spot_price: float) -> List[Dict]:
    """
    Identifies gamma flip zones where GEX crosses zero.
    Returns list of flip zones with strike levels and direction indicators.
    """
    df_sorted = df.sort_values('strike').reset_index(drop=True)
    
    flip_zones = []
    
    for i in range(len(df_sorted) - 1):
        current_gex = df_sorted.iloc[i]['net_gex']
        next_gex = df_sorted.iloc[i + 1]['net_gex']
        current_strike = df_sorted.iloc[i]['strike']
        next_strike = df_sorted.iloc[i + 1]['strike']
        
        # Check if GEX crosses zero between these strikes
        if (current_gex > 0 and next_gex < 0) or (current_gex < 0 and next_gex > 0):
            # Interpolate the exact flip strike
            flip_strike = current_strike + (next_strike - current_strike) * (abs(current_gex) / (abs(current_gex) + abs(next_gex)))
            
            # Determine flip direction based on spot position
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
                'lower_gex': current_gex,
                'upper_gex': next_gex,
                'direction': direction,
                'arrow': arrow,
                'color': color,
                'flip_type': 'Positive→Negative' if current_gex > 0 else 'Negative→Positive'
            })
    
    return flip_zones

# ============================================================================
# DHAN LIVE API FETCHER (ENHANCED)
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
    
    def fetch_rolling_data(self, symbol: str, from_date: str, to_date: str, 
                          strike_type: str = "ATM", option_type: str = "CALL", 
                          interval: str = "60", expiry_code: int = 1, expiry_flag: str = "WEEK"):
        """Fetch rolling options data"""
        try:
            security_id = DHAN_SECURITY_IDS.get(symbol, 13)
            
            payload = {
                "exchangeSegment": "NSE_FNO",
                "interval": interval,
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
    
    def process_live_data(self, symbol: str, target_date: str, strikes: List[str], 
                         interval: str = "60", expiry_code: int = 1, expiry_flag: str = "WEEK"):
        """Process live data with VANNA and CHARM"""
        
        # Convert to datetime
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        from_date = (target_dt - timedelta(days=2)).strftime('%Y-%m-%d')
        to_date = (target_dt + timedelta(days=2)).strftime('%Y-%m-%d')
        
        config = SYMBOL_CONFIG.get(symbol, SYMBOL_CONFIG["NIFTY"])
        contract_size = config["contract_size"]
        
        all_data = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_steps = len(strikes) * 2
        current_step = 0
        
        for strike_type in strikes:
            status_text.text(f"Fetching {strike_type} ({expiry_flag} Expiry {expiry_code})...")
            
            # Fetch CALL data
            call_data = self.fetch_rolling_data(symbol, from_date, to_date, strike_type, "CALL", 
                                                interval, expiry_code, expiry_flag)
            current_step += 1
            progress_bar.progress(current_step / total_steps)
            time.sleep(1)
            
            # Fetch PUT data
            put_data = self.fetch_rolling_data(symbol, from_date, to_date, strike_type, "PUT", 
                                               interval, expiry_code, expiry_flag)
            current_step += 1
            progress_bar.progress(current_step / total_steps)
            time.sleep(1)
            
            if not call_data or not put_data:
                continue
            
            ce_data = call_data.get('ce', {})
            pe_data = put_data.get('pe', {})
            
            if not ce_data:
                continue
            
            timestamps = ce_data.get('timestamp', [])
            
            for i, ts in enumerate(timestamps):
                try:
                    # Convert timestamp to IST
                    dt_utc = datetime.fromtimestamp(ts, tz=pytz.UTC)
                    dt_ist = dt_utc.astimezone(IST)
                    
                    # Filter for target date
                    if dt_ist.date() != target_dt.date():
                        continue
                    
                    spot_price = ce_data.get('spot', [0])[i] if i < len(ce_data.get('spot', [])) else 0
                    strike_price = ce_data.get('strike', [0])[i] if i < len(ce_data.get('strike', [])) else 0
                    
                    if spot_price == 0 or strike_price == 0:
                        continue
                    
                    # Get OI and other data
                    call_oi = ce_data.get('oi', [0])[i] if i < len(ce_data.get('oi', [])) else 0
                    put_oi = pe_data.get('oi', [0])[i] if i < len(pe_data.get('oi', [])) else 0
                    call_volume = ce_data.get('volume', [0])[i] if i < len(ce_data.get('volume', [])) else 0
                    put_volume = pe_data.get('volume', [0])[i] if i < len(pe_data.get('volume', [])) else 0
                    call_iv = ce_data.get('iv', [15])[i] if i < len(ce_data.get('iv', [])) else 15
                    put_iv = pe_data.get('iv', [15])[i] if i < len(pe_data.get('iv', [])) else 15
                    
                    # Calculate Greeks
                    time_to_expiry = 7 / 365  # Approximate
                    call_iv_dec = call_iv / 100 if call_iv > 1 else call_iv
                    put_iv_dec = put_iv / 100 if put_iv > 1 else put_iv
                    
                    # Standard Greeks
                    call_gamma = self.bs_calc.calculate_gamma(spot_price, strike_price, time_to_expiry, self.risk_free_rate, call_iv_dec)
                    put_gamma = self.bs_calc.calculate_gamma(spot_price, strike_price, time_to_expiry, self.risk_free_rate, put_iv_dec)
                    call_delta = self.bs_calc.calculate_call_delta(spot_price, strike_price, time_to_expiry, self.risk_free_rate, call_iv_dec)
                    put_delta = self.bs_calc.calculate_put_delta(spot_price, strike_price, time_to_expiry, self.risk_free_rate, put_iv_dec)
                    
                    # VANNA and CHARM
                    call_vanna = self.bs_calc.calculate_vanna(spot_price, strike_price, time_to_expiry, self.risk_free_rate, call_iv_dec)
                    put_vanna = self.bs_calc.calculate_vanna(spot_price, strike_price, time_to_expiry, self.risk_free_rate, put_iv_dec)
                    call_charm = self.bs_calc.calculate_charm(spot_price, strike_price, time_to_expiry, self.risk_free_rate, call_iv_dec, 'call')
                    put_charm = self.bs_calc.calculate_charm(spot_price, strike_price, time_to_expiry, self.risk_free_rate, put_iv_dec, 'put')
                    
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
                        'time': dt_ist.strftime('%H:%M IST'),
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
                    
                except Exception as e:
                    continue
        
        progress_bar.empty()
        status_text.empty()
        
        if not all_data:
            return None, None
        
        df = pd.DataFrame(all_data)
        
        # Sort by timestamp for flow calculations
        df = df.sort_values(['strike', 'timestamp']).reset_index(drop=True)
        
        # Calculate flows
        df['call_gex_flow'] = 0.0
        df['put_gex_flow'] = 0.0
        df['net_gex_flow'] = 0.0
        df['call_dex_flow'] = 0.0
        df['put_dex_flow'] = 0.0
        df['net_dex_flow'] = 0.0
        df['call_oi_change'] = 0.0
        df['put_oi_change'] = 0.0
        df['call_oi_gex'] = 0.0
        df['put_oi_gex'] = 0.0
        df['net_oi_gex'] = 0.0
        
        try:
            for strike in df['strike'].unique():
                strike_mask = df['strike'] == strike
                strike_data = df[strike_mask].copy()
                
                if len(strike_data) > 1:
                    df.loc[strike_mask, 'call_gex_flow'] = strike_data['call_gex'].diff().fillna(0)
                    df.loc[strike_mask, 'put_gex_flow'] = strike_data['put_gex'].diff().fillna(0)
                    df.loc[strike_mask, 'net_gex_flow'] = strike_data['net_gex'].diff().fillna(0)
                    df.loc[strike_mask, 'call_dex_flow'] = strike_data['call_dex'].diff().fillna(0)
                    df.loc[strike_mask, 'put_dex_flow'] = strike_data['put_dex'].diff().fillna(0)
                    df.loc[strike_mask, 'net_dex_flow'] = strike_data['net_dex'].diff().fillna(0)
                    
                    df.loc[strike_mask, 'call_oi_change'] = strike_data['call_oi'].diff().fillna(0)
                    df.loc[strike_mask, 'put_oi_change'] = strike_data['put_oi'].diff().fillna(0)
            
            # Calculate OI-based GEX
            for strike in df['strike'].unique():
                strike_mask = df['strike'] == strike
                strike_data = df[strike_mask].copy()
                
                for idx in strike_data.index:
                    try:
                        row = df.loc[idx]
                        spot = row['spot_price']
                        strike_price = row['strike']
                        time_to_expiry = 7 / 365
                        call_iv_dec = row['call_iv'] / 100 if row['call_iv'] > 1 else row['call_iv']
                        put_iv_dec = row['put_iv'] / 100 if row['put_iv'] > 1 else row['put_iv']
                        
                        call_gamma = self.bs_calc.calculate_gamma(spot, strike_price, time_to_expiry, self.risk_free_rate, call_iv_dec)
                        put_gamma = self.bs_calc.calculate_gamma(spot, strike_price, time_to_expiry, self.risk_free_rate, put_iv_dec)
                        
                        call_oi_change = row['call_oi_change']
                        put_oi_change = row['put_oi_change']
                        
                        call_oi_gex_val = (call_oi_change * call_gamma * spot**2 * contract_size) / 1e9
                        put_oi_gex_val = -(put_oi_change * put_gamma * spot**2 * contract_size) / 1e9
                        
                        df.loc[idx, 'call_oi_gex'] = call_oi_gex_val
                        df.loc[idx, 'put_oi_gex'] = put_oi_gex_val
                        df.loc[idx, 'net_oi_gex'] = call_oi_gex_val + put_oi_gex_val
                    except Exception as e:
                        continue
        except Exception as e:
            pass
        
        # Calculate hedging pressure
        max_gex = df['net_gex'].abs().max()
        df['hedging_pressure'] = (df['net_gex'] / max_gex * 100) if max_gex > 0 else 0
        
        # Initialize predictive columns
        df['volume_weighted_gex'] = 0.0
        df['support_resistance_strength'] = 0.0
        df['vanna_adj_gex_vol_up'] = 0.0
        df['vanna_adj_gex_vol_down'] = 0.0
        df['charm_adj_gex_2hr'] = 0.0
        df['charm_adj_gex_4hr'] = 0.0
        
        try:
            for idx, row in df.iterrows():
                try:
                    spot = row['spot_price']
                    strike = row['strike']
                    net_gex = row['net_gex']
                    total_vol = row['total_volume']
                    timestamp = row['timestamp']
                    timestamp_mask = df['timestamp'] == timestamp
                    net_vanna = row['net_vanna']
                    net_charm = row['net_charm']
                    
                    # Volume-weighted GEX
                    total_vol_at_time = df[timestamp_mask]['total_volume'].sum()
                    if total_vol_at_time > 0:
                        volume_weight = total_vol / total_vol_at_time
                        vwgex = net_gex * volume_weight * 100
                        df.loc[idx, 'volume_weighted_gex'] = vwgex
                    
                    # Support/Resistance strength
                    distance_from_spot = abs(strike - spot)
                    distance_pct = (distance_from_spot / spot) * 100
                    proximity_factor = 1 / (1 + distance_pct) if distance_pct > 0 else 1.0
                    avg_volume = df[timestamp_mask]['total_volume'].mean()
                    volume_factor = (total_vol / avg_volume) if avg_volume > 0 else 1
                    strength = abs(net_gex) * proximity_factor * volume_factor
                    df.loc[idx, 'support_resistance_strength'] = strength
                    
                    # VANNA-adjusted GEX
                    vol_change_up = 0.05
                    vanna_impact_up = net_vanna * vol_change_up
                    df.loc[idx, 'vanna_adj_gex_vol_up'] = net_gex + vanna_impact_up
                    
                    vol_change_down = -0.05
                    vanna_impact_down = net_vanna * vol_change_down
                    df.loc[idx, 'vanna_adj_gex_vol_down'] = net_gex + vanna_impact_down
                    
                    # CHARM-adjusted GEX
                    time_decay_2hr = 2 / 24
                    charm_impact_2hr = net_charm * time_decay_2hr * 10
                    df.loc[idx, 'charm_adj_gex_2hr'] = net_gex + charm_impact_2hr
                    
                    time_decay_4hr = 4 / 24
                    charm_impact_4hr = net_charm * time_decay_4hr * 10
                    df.loc[idx, 'charm_adj_gex_4hr'] = net_gex + charm_impact_4hr
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            pass
        
        # Get latest data point for metadata
        latest = df.sort_values('timestamp').iloc[-1]
        spot_prices = df['spot_price'].unique()
        spot_variation = (spot_prices.max() - spot_prices.min()) / spot_prices.mean() * 100
        
        meta = {
            'symbol': symbol,
            'date': target_date,
            'spot_price': latest['spot_price'],
            'spot_price_min': spot_prices.min(),
            'spot_price_max': spot_prices.max(),
            'spot_variation_pct': spot_variation,
            'total_records': len(df),
            'time_range': f"{df['time'].min()} - {df['time'].max()}",
            'strikes_count': df['strike'].nunique(),
            'interval': f"{interval} minutes" if interval != "1" else "1 minute",
            'expiry_code': expiry_code,
            'expiry_flag': expiry_flag
        }
        
        return df, meta

# ============================================================================
# VISUALIZATION FUNCTIONS (SAME AS HISTORICAL VERSION)
# ============================================================================

def create_intraday_timeline(df: pd.DataFrame, selected_timestamp) -> go.Figure:
    """Create intraday timeline of total GEX and DEX"""
    timeline_df = df.groupby('timestamp').agg({
        'net_gex': 'sum',
        'net_dex': 'sum',
        'spot_price': 'first'
    }).reset_index()
    
    timeline_df = timeline_df.sort_values('timestamp')
    
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=('Total Net GEX Over Time', 'Total Net DEX Over Time', 'Spot Price Movement'),
        vertical_spacing=0.1,
        row_heights=[0.35, 0.35, 0.3]
    )
    
    # GEX timeline
    gex_colors = ['#10b981' if x > 0 else '#ef4444' for x in timeline_df['net_gex']]
    fig.add_trace(
        go.Bar(
            x=timeline_df['timestamp'],
            y=timeline_df['net_gex'],
            marker_color=gex_colors,
            name='Net GEX',
            hovertemplate='%{x|%H:%M}<br>GEX: %{y:.4f}B<extra></extra>'
        ),
        row=1, col=1
    )
    
    # DEX timeline
    dex_colors = ['#10b981' if x > 0 else '#ef4444' for x in timeline_df['net_dex']]
    fig.add_trace(
        go.Bar(
            x=timeline_df['timestamp'],
            y=timeline_df['net_dex'],
            marker_color=dex_colors,
            name='Net DEX',
            hovertemplate='%{x|%H:%M}<br>DEX: %{y:.4f}B<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Spot price
    fig.add_trace(
        go.Scatter(
            x=timeline_df['timestamp'],
            y=timeline_df['spot_price'],
            mode='lines+markers',
            line=dict(color='#3b82f6', width=2),
            marker=dict(size=4),
            name='Spot Price',
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.1)',
            hovertemplate='%{x|%H:%M}<br>Spot: ₹%{y:,.2f}<extra></extra>'
        ),
        row=3, col=1
    )
    
    # Add vertical line at selected timestamp
    fig.add_vline(x=selected_timestamp, line_dash="dash", line_color="#f59e0b", line_width=3, row=1, col=1)
    fig.add_vline(x=selected_timestamp, line_dash="dash", line_color="#f59e0b", line_width=3, row=2, col=1)
    fig.add_vline(x=selected_timestamp, line_dash="dash", line_color="#f59e0b", line_width=3, row=3, col=1)
    
    fig.update_layout(
        title=dict(text="<b>📈 Intraday Evolution</b>", font=dict(size=18, color='white')),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)',
        height=900,
        showlegend=False,
        hovermode='x unified'
    )
    
    fig.update_xaxes(title_text="Time (IST)", row=3, col=1)
    fig.update_yaxes(title_text="GEX (₹B)", row=1, col=1)
    fig.update_yaxes(title_text="DEX (₹B)", row=2, col=1)
    fig.update_yaxes(title_text="Spot Price (₹)", row=3, col=1)
    
    return fig

def create_gex_flow_chart(df: pd.DataFrame, spot_price: float) -> go.Figure:
    """Create GEX Flow chart with Gamma Flip Zones"""
    df_sorted = df.sort_values('strike').reset_index(drop=True)
    colors = ['#10b981' if x > 0 else '#ef4444' for x in df_sorted['net_gex_flow']]
    
    flip_zones = identify_gamma_flip_zones(df_sorted, spot_price)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=df_sorted['strike'],
        x=df_sorted['net_gex_flow'],
        orientation='h',
        marker_color=colors,
        name='Net GEX Flow',
        hovertemplate='Strike: %{y:,.0f}<br>Net GEX Flow: %{x:.4f}B<extra></extra>',
        showlegend=False
    ))
    
    fig.add_hline(y=spot_price, line_dash="dash", line_color="#06b6d4", line_width=3,
                  annotation_text=f"Spot: {spot_price:,.2f}", annotation_position="top right",
                  annotation=dict(font=dict(size=12, color="white")))
    
    fig.add_vline(x=0, line_dash="dot", line_color="gray", line_width=1)
    
    for zone in flip_zones:
        fig.add_hline(
            y=zone['strike'],
            line_dash="dot",
            line_color=zone['color'],
            line_width=2,
            annotation_text=f"🔄 Flip {zone['arrow']} {zone['strike']:,.0f}",
            annotation_position="left",
            annotation=dict(
                font=dict(size=10, color=zone['color']),
                bgcolor='rgba(0,0,0,0.7)',
                bordercolor=zone['color'],
                borderwidth=1
            )
        )
        
        fig.add_hrect(
            y0=zone['lower_strike'],
            y1=zone['upper_strike'],
            fillcolor=zone['color'],
            opacity=0.1,
            line_width=0,
            annotation_text=zone['arrow'],
            annotation_position="right",
            annotation=dict(font=dict(size=16, color=zone['color']))
        )
    
    fig.update_layout(
        title=dict(text="<b>🌊 GEX Flow with Flip Zones</b>", font=dict(size=18, color='white')),
        xaxis_title="Net GEX Flow (₹ Billions)",
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
            zerolinewidth=2
        ),
        yaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True, autorange=True),
        margin=dict(l=80, r=80, t=80, b=80)
    )
    
    return fig

def create_oi_based_gex_chart(df: pd.DataFrame, spot_price: float) -> go.Figure:
    """Create OI-Based GEX chart"""
    df_sorted = df.sort_values('strike').reset_index(drop=True)
    
    if 'net_oi_gex' not in df_sorted.columns:
        df_sorted['net_oi_gex'] = 0.0
    
    df_sorted['net_oi_gex'] = df_sorted['net_oi_gex'].fillna(0)
    colors = ['#10b981' if x > 0 else '#ef4444' for x in df_sorted['net_oi_gex']]
    flip_zones = identify_gamma_flip_zones(df_sorted, spot_price)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=df_sorted['strike'],
        x=df_sorted['net_oi_gex'],
        orientation='h',
        marker_color=colors,
        name='OI-Based GEX',
        hovertemplate='Strike: %{y:,.0f}<br>OI-Based GEX: %{x:.4f}B<extra></extra>',
        showlegend=False
    ))
    
    fig.add_hline(y=spot_price, line_dash="dash", line_color="#06b6d4", line_width=3,
                  annotation_text=f"Spot: {spot_price:,.2f}", annotation_position="top right",
                  annotation=dict(font=dict(size=12, color="white")))
    
    fig.add_vline(x=0, line_dash="dot", line_color="gray", line_width=1)
    
    for zone in flip_zones:
        fig.add_hline(
            y=zone['strike'],
            line_dash="dot",
            line_color=zone['color'],
            line_width=2,
            annotation_text=f"🔄 Flip {zone['arrow']} {zone['strike']:,.0f}",
            annotation_position="left",
            annotation=dict(
                font=dict(size=10, color=zone['color']),
                bgcolor='rgba(0,0,0,0.7)',
                bordercolor=zone['color'],
                borderwidth=1
            )
        )
        
        fig.add_hrect(
            y0=zone['lower_strike'],
            y1=zone['upper_strike'],
            fillcolor=zone['color'],
            opacity=0.1,
            line_width=0,
            annotation_text=zone['arrow'],
            annotation_position="right",
            annotation=dict(font=dict(size=16, color=zone['color']))
        )
    
    fig.update_layout(
        title=dict(text="<b>📊 OI-Based GEX (Pure Position Changes)</b>", font=dict(size=18, color='white')),
        xaxis_title="OI Contribution to GEX (₹ Billions)",
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
            zerolinewidth=2
        ),
        yaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True, autorange=True),
        margin=dict(l=80, r=80, t=80, b=80)
    )
    
    return fig

def create_dex_flow_chart(df: pd.DataFrame, spot_price: float) -> go.Figure:
    """Create DEX Flow chart"""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=df['strike'],
        x=df['call_dex_flow'],
        orientation='h',
        name='Call DEX Flow',
        marker_color='rgba(16, 185, 129, 0.6)',
        hovertemplate='Strike: %{y}<br>Call Flow: %{x:.4f}B<extra></extra>'
    ))
    
    fig.add_trace(go.Bar(
        y=df['strike'],
        x=df['put_dex_flow'],
        orientation='h',
        name='Put DEX Flow',
        marker_color='rgba(239, 68, 68, 0.6)',
        hovertemplate='Strike: %{y}<br>Put Flow: %{x:.4f}B<extra></extra>'
    ))
    
    fig.add_hline(y=spot_price, line_dash="dash", line_color="#3b82f6", line_width=2,
                  annotation_text=f"Spot: ₹{spot_price:,.0f}", annotation_position="right")
    
    fig.update_layout(
        title=dict(text="<b>🌊 DEX Flow Distribution</b>", font=dict(size=18, color='white')),
        xaxis_title="DEX Flow (₹B)",
        yaxis_title="Strike Price",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)',
        height=600,
        barmode='relative',
        hovermode='y unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def create_separate_gex_chart(df: pd.DataFrame, spot_price: float) -> go.Figure:
    """GEX chart with Gamma Flip Zones"""
    df_sorted = df.sort_values('strike').reset_index(drop=True)
    colors = ['#10b981' if x > 0 else '#ef4444' for x in df_sorted['net_gex']]
    flip_zones = identify_gamma_flip_zones(df_sorted, spot_price)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=df_sorted['strike'],
        x=df_sorted['net_gex'],
        orientation='h',
        marker_color=colors,
        name='Net GEX',
        hovertemplate='Strike: %{y:,.0f}<br>Net GEX: %{x:.4f}B<extra></extra>',
        showlegend=False
    ))
    
    fig.add_hline(y=spot_price, line_dash="dash", line_color="#06b6d4", line_width=3,
                  annotation_text=f"Spot: {spot_price:,.2f}", annotation_position="top right",
                  annotation=dict(font=dict(size=12, color="white")))
    
    for zone in flip_zones:
        fig.add_hline(
            y=zone['strike'],
            line_dash="dot",
            line_color=zone['color'],
            line_width=2,
            annotation_text=f"🔄 Flip {zone['arrow']} {zone['strike']:,.0f}",
            annotation_position="left",
            annotation=dict(
                font=dict(size=10, color=zone['color']),
                bgcolor='rgba(0,0,0,0.7)',
                bordercolor=zone['color'],
                borderwidth=1
            )
        )
        
        fig.add_hrect(
            y0=zone['lower_strike'],
            y1=zone['upper_strike'],
            fillcolor=zone['color'],
            opacity=0.1,
            line_width=0,
            annotation_text=zone['arrow'],
            annotation_position="right",
            annotation=dict(font=dict(size=16, color=zone['color']))
        )
    
    fig.update_layout(
        title=dict(text="<b>🎯 Gamma Exposure (GEX) with Flip Zones</b>", font=dict(size=18, color='white')),
        xaxis_title="GEX (₹ Billions)",
        yaxis_title="Strike Price",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)',
        height=700,
        showlegend=False,
        hovermode='closest',
        xaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True),
        yaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True, autorange=True),
        margin=dict(l=80, r=80, t=80, b=80)
    )
    
    return fig

def create_mixed_gex_overlay_chart(df_weekly: pd.DataFrame, df_monthly: pd.DataFrame, spot_price: float, selected_timestamp: str) -> go.Figure:
    """Mixed GEX: Weekly and Monthly overlaid"""
    df_w = df_weekly[df_weekly['timestamp'] == selected_timestamp].copy().sort_values('strike').reset_index(drop=True)
    df_m = df_monthly[df_monthly['timestamp'] == selected_timestamp].copy().sort_values('strike').reset_index(drop=True)
    
    flip_zones = identify_gamma_flip_zones(df_w, spot_price)
    
    fig = go.Figure()
    
    if len(df_w) > 0:
        weekly_colors = ['#3b82f6' if x > 0 else '#8b5cf6' for x in df_w['net_gex']]
        fig.add_trace(go.Bar(
            y=df_w['strike'],
            x=df_w['net_gex'],
            orientation='h',
            marker=dict(color=weekly_colors, opacity=0.7, line=dict(width=0)),
            name=f'Weekly GEX (Max: {df_w["net_gex"].abs().max():.4f}B)',
            hovertemplate='Strike: %{y:,.0f}<br>Weekly GEX: %{x:.4f}B<extra></extra>'
        ))
    
    if len(df_m) > 0:
        monthly_colors = ['#10b981' if x > 0 else '#ef4444' for x in df_m['net_gex']]
        fig.add_trace(go.Bar(
            y=df_m['strike'],
            x=df_m['net_gex'],
            orientation='h',
            marker=dict(color=monthly_colors, opacity=0.7, line=dict(color='white', width=1)),
            name=f'Monthly GEX (Max: {df_m["net_gex"].abs().max():.4f}B)',
            hovertemplate='Strike: %{y:,.0f}<br>Monthly GEX: %{x:.4f}B<extra></extra>'
        ))
    
    fig.add_hline(y=spot_price, line_dash="dash", line_color="white", line_width=3,
                  annotation_text=f"Spot: {spot_price:,.2f}", annotation_position="top right",
                  annotation=dict(font=dict(size=12, color="white", family="Arial Black")))
    
    fig.add_vline(x=0, line_dash="dot", line_color="gray", line_width=2)
    
    for zone in flip_zones:
        fig.add_hline(y=zone['strike'], line_dash="dot", line_color=zone['color'], line_width=1, opacity=0.5)
    
    fig.update_layout(
        title=dict(
            text="<b>🔀 Mixed GEX: Weekly vs Monthly Overlay</b><br><sub>Blue/Purple = Weekly | Green/Red = Monthly</sub>",
            font=dict(size=18, color='white')
        ),
        xaxis_title="GEX (₹ Billions)",
        yaxis_title="Strike Price",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)',
        height=700,
        barmode='overlay',
        bargap=0.15,
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
        xaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True, zeroline=True, zerolinecolor='rgba(255,255,255,0.3)', zerolinewidth=2),
        yaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True, autorange=True),
        margin=dict(l=80, r=80, t=100, b=80)
    )
    
    return fig

def create_mixed_vanna_overlay_chart(df_weekly: pd.DataFrame, df_monthly: pd.DataFrame, spot_price: float, selected_timestamp: str) -> go.Figure:
    """Mixed VANNA overlay"""
    df_w = df_weekly[df_weekly['timestamp'] == selected_timestamp].copy().sort_values('strike').reset_index(drop=True)
    df_m = df_monthly[df_monthly['timestamp'] == selected_timestamp].copy().sort_values('strike').reset_index(drop=True)
    
    fig = go.Figure()
    
    if len(df_w) > 0:
        weekly_colors = ['#3b82f6' if x > 0 else '#8b5cf6' for x in df_w['net_vanna']]
        fig.add_trace(go.Bar(
            y=df_w['strike'],
            x=df_w['net_vanna'],
            orientation='h',
            marker=dict(color=weekly_colors, opacity=0.7),
            name=f'Weekly VANNA (Max: {df_w["net_vanna"].abs().max():.4f}B)',
            hovertemplate='Strike: %{y:,.0f}<br>Weekly VANNA: %{x:.4f}B<extra></extra>'
        ))
    
    if len(df_m) > 0:
        monthly_colors = ['#06b6d4' if x > 0 else '#f97316' for x in df_m['net_vanna']]
        fig.add_trace(go.Bar(
            y=df_m['strike'],
            x=df_m['net_vanna'],
            orientation='h',
            marker=dict(color=monthly_colors, opacity=0.7, line=dict(color='white', width=1)),
            name=f'Monthly VANNA (Max: {df_m["net_vanna"].abs().max():.4f}B)',
            hovertemplate='Strike: %{y:,.0f}<br>Monthly VANNA: %{x:.4f}B<extra></extra>'
        ))
    
    fig.add_hline(y=spot_price, line_dash="dash", line_color="white", line_width=3,
                  annotation_text=f"Spot: {spot_price:,.2f}", annotation_position="top right")
    
    fig.add_vline(x=0, line_dash="dot", line_color="gray", line_width=2)
    
    fig.update_layout(
        title=dict(
            text="<b>🔀 Mixed VANNA: Weekly vs Monthly Overlay</b><br><sub>Blue/Purple = Weekly | Cyan/Orange = Monthly</sub>",
            font=dict(size=18, color='white')
        ),
        xaxis_title="VANNA (dDelta/dVol)",
        yaxis_title="Strike Price",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)',
        height=700,
        barmode='overlay',
        bargap=0.15,
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
        xaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True, zeroline=True, zerolinecolor='rgba(255,255,255,0.3)', zerolinewidth=2),
        yaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True, autorange=True),
        margin=dict(l=80, r=80, t=100, b=80)
    )
    
    return fig

def create_mixed_charm_overlay_chart(df_weekly: pd.DataFrame, df_monthly: pd.DataFrame, spot_price: float, selected_timestamp: str) -> go.Figure:
    """Mixed CHARM overlay"""
    df_w = df_weekly[df_weekly['timestamp'] == selected_timestamp].copy().sort_values('strike').reset_index(drop=True)
    df_m = df_monthly[df_monthly['timestamp'] == selected_timestamp].copy().sort_values('strike').reset_index(drop=True)
    
    fig = go.Figure()
    
    if len(df_w) > 0:
        weekly_colors = ['#3b82f6' if x > 0 else '#8b5cf6' for x in df_w['net_charm']]
        fig.add_trace(go.Bar(
            y=df_w['strike'],
            x=df_w['net_charm'],
            orientation='h',
            marker=dict(color=weekly_colors, opacity=0.7),
            name=f'Weekly CHARM (Max: {df_w["net_charm"].abs().max():.4f}B)',
            hovertemplate='Strike: %{y:,.0f}<br>Weekly CHARM: %{x:.4f}B<extra></extra>'
        ))
    
    if len(df_m) > 0:
        monthly_colors = ['#eab308' if x > 0 else '#ec4899' for x in df_m['net_charm']]
        fig.add_trace(go.Bar(
            y=df_m['strike'],
            x=df_m['net_charm'],
            orientation='h',
            marker=dict(color=monthly_colors, opacity=0.7, line=dict(color='white', width=1)),
            name=f'Monthly CHARM (Max: {df_m["net_charm"].abs().max():.4f}B)',
            hovertemplate='Strike: %{y:,.0f}<br>Monthly CHARM: %{x:.4f}B<extra></extra>'
        ))
    
    fig.add_hline(y=spot_price, line_dash="dash", line_color="white", line_width=3,
                  annotation_text=f"Spot: {spot_price:,.2f}", annotation_position="top right")
    
    fig.add_vline(x=0, line_dash="dot", line_color="gray", line_width=2)
    
    fig.update_layout(
        title=dict(
            text="<b>🔀 Mixed CHARM: Weekly vs Monthly Overlay</b><br><sub>Blue/Purple = Weekly | Yellow/Pink = Monthly</sub>",
            font=dict(size=18, color='white')
        ),
        xaxis_title="CHARM (Delta Decay)",
        yaxis_title="Strike Price",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)',
        height=700,
        barmode='overlay',
        bargap=0.15,
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
        xaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True, zeroline=True, zerolinecolor='rgba(255,255,255,0.3)', zerolinewidth=2),
        yaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True, autorange=True),
        margin=dict(l=80, r=80, t=100, b=80)
    )
    
    return fig

def create_separate_dex_chart(df: pd.DataFrame, spot_price: float) -> go.Figure:
    """DEX chart"""
    df_sorted = df.sort_values('strike').reset_index(drop=True)
    colors = ['#10b981' if x > 0 else '#ef4444' for x in df_sorted['net_dex']]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=df_sorted['strike'],
        x=df_sorted['net_dex'],
        orientation='h',
        marker_color=colors,
        name='Net DEX',
        hovertemplate='Strike: %{y:,.0f}<br>Net DEX: %{x:.4f}B<extra></extra>',
        showlegend=False
    ))
    
    fig.add_hline(y=spot_price, line_dash="dash", line_color="#06b6d4", line_width=3,
                  annotation_text=f"Spot: {spot_price:,.2f}", annotation_position="top right",
                  annotation=dict(font=dict(size=12, color="white")))
    
    fig.update_layout(
        title=dict(text="<b>📊 Delta Exposure (DEX)</b>", font=dict(size=18, color='white')),
        xaxis_title="DEX (₹ Billions)",
        yaxis_title="Strike Price",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)',
        height=700,
        showlegend=False,
        hovermode='closest',
        xaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True),
        yaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True, autorange=True),
        margin=dict(l=80, r=80, t=80, b=80)
    )
    
    return fig

def create_net_gex_dex_chart(df: pd.DataFrame, spot_price: float) -> go.Figure:
    """NET GEX+DEX chart with Flip Zones"""
    df_sorted = df.sort_values('strike').reset_index(drop=True)
    df_sorted['net_gex_dex'] = df_sorted['net_gex'] + df_sorted['net_dex']
    colors = ['#10b981' if x > 0 else '#ef4444' for x in df_sorted['net_gex_dex']]
    flip_zones = identify_gamma_flip_zones(df_sorted, spot_price)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=df_sorted['strike'],
        x=df_sorted['net_gex_dex'],
        orientation='h',
        marker_color=colors,
        name='Net GEX+DEX',
        hovertemplate='Strike: %{y:,.0f}<br>Net GEX+DEX: %{x:.4f}B<extra></extra>',
        showlegend=False
    ))
    
    fig.add_hline(y=spot_price, line_dash="dash", line_color="#06b6d4", line_width=3,
                  annotation_text=f"Spot: {spot_price:,.2f}", annotation_position="top right",
                  annotation=dict(font=dict(size=12, color="white")))
    
    for zone in flip_zones:
        fig.add_hline(
            y=zone['strike'],
            line_dash="dot",
            line_color=zone['color'],
            line_width=2,
            annotation_text=f"🔄 Flip {zone['arrow']} {zone['strike']:,.0f}",
            annotation_position="left",
            annotation=dict(
                font=dict(size=10, color=zone['color']),
                bgcolor='rgba(0,0,0,0.7)',
                bordercolor=zone['color'],
                borderwidth=1
            )
        )
        
        fig.add_hrect(
            y0=zone['lower_strike'],
            y1=zone['upper_strike'],
            fillcolor=zone['color'],
            opacity=0.1,
            line_width=0,
            annotation_text=zone['arrow'],
            annotation_position="right",
            annotation=dict(font=dict(size=16, color=zone['color']))
        )
    
    fig.update_layout(
        title=dict(text="<b>⚡ Combined NET GEX + DEX with Flip Zones</b>", font=dict(size=18, color='white')),
        xaxis_title="Combined Exposure (₹ Billions)",
        yaxis_title="Strike Price",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)',
        height=700,
        showlegend=False,
        hovermode='closest',
        xaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True),
        yaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True, autorange=True),
        margin=dict(l=80, r=80, t=80, b=80)
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
                  annotation_text=f"Spot: {spot_price:,.2f}", annotation_position="top right",
                  annotation=dict(font=dict(size=12, color="white")))
    
    fig.add_vline(x=0, line_dash="dot", line_color="gray", line_width=1)
    
    for zone in flip_zones:
        fig.add_hline(
            y=zone['strike'],
            line_dash="dot",
            line_color=zone['color'],
            line_width=2,
            annotation_text=f"🔄 Flip {zone['arrow']} {zone['strike']:,.0f}",
            annotation_position="left",
            annotation=dict(
                font=dict(size=10, color=zone['color']),
                bgcolor='rgba(0,0,0,0.7)',
                bordercolor=zone['color'],
                borderwidth=1
            )
        )
        
        fig.add_hrect(
            y0=zone['lower_strike'],
            y1=zone['upper_strike'],
            fillcolor=zone['color'],
            opacity=0.1,
            line_width=0,
            annotation_text=zone['arrow'],
            annotation_position="right",
            annotation=dict(font=dict(size=16, color=zone['color']))
        )
    
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

def create_oi_distribution(df: pd.DataFrame, spot_price: float) -> go.Figure:
    """OI Distribution chart"""
    df_sorted = df.sort_values('strike').reset_index(drop=True)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=df_sorted['strike'],
        x=df_sorted['call_oi'],
        orientation='h',
        name='Call OI',
        marker_color='#10b981',
        opacity=0.7,
        hovertemplate='Strike: %{y:,.0f}<br>Call OI: %{x:,.0f}<extra></extra>'
    ))
    
    fig.add_trace(go.Bar(
        y=df_sorted['strike'],
        x=-df_sorted['put_oi'],
        orientation='h',
        name='Put OI',
        marker_color='#ef4444',
        opacity=0.7,
        hovertemplate='Strike: %{y:,.0f}<br>Put OI: %{customdata:,.0f}<extra></extra>',
        customdata=df_sorted['put_oi']
    ))
    
    fig.add_hline(y=spot_price, line_dash="dash", line_color="#06b6d4", line_width=2,
                  annotation_text=f"Spot: {spot_price:,.2f}", annotation_position="top right",
                  annotation=dict(font=dict(size=12, color="white")))
    
    fig.add_vline(x=0, line_dash="dot", line_color="white", line_width=1)
    
    fig.update_layout(
        title=dict(text="<b>📋 Open Interest Distribution</b>", font=dict(size=16, color='white')),
        xaxis_title="Open Interest (Calls +ve | Puts -ve)",
        yaxis_title="Strike Price",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)',
        height=500,
        barmode='overlay',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, font=dict(color='white')),
        hovermode='closest',
        xaxis=dict(
            gridcolor='rgba(128,128,128,0.2)', 
            showgrid=True,
            zeroline=True,
            zerolinecolor='rgba(255,255,255,0.3)',
            zerolinewidth=2
        ),
        yaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True, autorange=True),
        margin=dict(l=80, r=80, t=80, b=80)
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
                      annotation=dict(font=dict(size=10, color="white")), row=1, col=col)
    
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
                      annotation=dict(font=dict(size=10, color="white")), row=1, col=col)
    
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

def create_gex_overlay_chart(df: pd.DataFrame, spot_price: float) -> go.Figure:
    """Overlay chart comparing Original GEX vs OI-Based GEX"""
    df_sorted = df.sort_values('strike').reset_index(drop=True)
    
    if 'net_gex' not in df_sorted.columns:
        df_sorted['net_gex'] = 0.0
    if 'net_oi_gex' not in df_sorted.columns:
        df_sorted['net_oi_gex'] = 0.0
    
    df_sorted['net_gex'] = df_sorted['net_gex'].fillna(0)
    df_sorted['net_oi_gex'] = df_sorted['net_oi_gex'].fillna(0)
    
    gex_sum = abs(df_sorted['net_gex'].sum())
    oi_gex_sum = abs(df_sorted['net_oi_gex'].sum())
    has_gex_data = gex_sum > 0.000001
    has_oi_data = oi_gex_sum > 0.000001
    
    max_gex = df_sorted['net_gex'].abs().max()
    max_oi_gex = df_sorted['net_oi_gex'].abs().max()
    
    flip_zones = identify_gamma_flip_zones(df_sorted, spot_price)
    
    fig = go.Figure()
    
    if not has_gex_data:
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            text="❌ No GEX Data Found<br>Check data source",
            showarrow=False,
            bgcolor="rgba(255,0,0,0.3)",
            bordercolor="red",
            borderwidth=2,
            font=dict(color="white", size=16),
            align="center"
        )
    else:
        original_colors = ['#10b981' if x > 0 else '#ef4444' for x in df_sorted['net_gex']]
        fig.add_trace(go.Bar(
            y=df_sorted['strike'],
            x=df_sorted['net_gex'],
            orientation='h',
            marker=dict(color=original_colors, opacity=0.6, line=dict(width=0)),
            name=f'Original GEX - Max: {max_gex:.4f}B',
            hovertemplate='Strike: %{y:,.0f}<br>Original GEX: %{x:.4f}B<extra></extra>'
        ))
        
        if has_oi_data:
            oi_colors = ['#06b6d4' if x > 0 else '#f97316' for x in df_sorted['net_oi_gex']]
            fig.add_trace(go.Bar(
                y=df_sorted['strike'],
                x=df_sorted['net_oi_gex'],
                orientation='h',
                marker=dict(color=oi_colors, opacity=0.85, line=dict(color='white', width=1)),
                name=f'OI-Based GEX - Max: {max_oi_gex:.4f}B',
                hovertemplate='Strike: %{y:,.0f}<br>OI-Based GEX: %{x:.4f}B<extra></extra>'
            ))
        else:
            fig.add_annotation(
                xref="paper", yref="paper",
                x=0.02, y=0.98,
                text="ℹ️ No OI-Based GEX<br>(Needs 2+ time points)",
                showarrow=False,
                bgcolor="rgba(255,165,0,0.2)",
                bordercolor="orange",
                borderwidth=1,
                font=dict(color="white", size=10),
                align="left",
                xanchor="left",
                yanchor="top"
            )
    
    fig.add_hline(y=spot_price, line_dash="dash", line_color="white", line_width=3,
                  annotation_text=f"Spot: {spot_price:,.2f}", annotation_position="top right",
                  annotation=dict(font=dict(size=12, color="white", family="Arial Black")))
    
    fig.add_vline(x=0, line_dash="dot", line_color="gray", line_width=2)
    
    for zone in flip_zones:
        fig.add_hline(
            y=zone['strike'],
            line_dash="dot",
            line_color=zone['color'],
            line_width=2,
            annotation_text=f"🔄 {zone['strike']:,.0f}",
            annotation_position="left",
            annotation=dict(
                font=dict(size=10, color=zone['color']),
                bgcolor='rgba(0,0,0,0.7)',
                bordercolor=zone['color'],
                borderwidth=1
            )
        )
        
        fig.add_hrect(
            y0=zone['lower_strike'],
            y1=zone['upper_strike'],
            fillcolor=zone['color'],
            opacity=0.05,
            line_width=0
        )
    
    fig.update_layout(
        title=dict(
            text="<b>🔄 GEX Overlay: Original vs OI-Based</b><br><sub>Green/Red = All effects | Cyan/Orange = Pure position changes</sub>", 
            font=dict(size=18, color='white')
        ),
        xaxis_title="GEX (₹ Billions)",
        yaxis_title="Strike Price",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)',
        height=700,
        barmode='overlay',
        bargap=0.15,
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
        xaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True, zeroline=True, zerolinecolor='rgba(255,255,255,0.3)', zerolinewidth=2),
        yaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True, autorange=True),
        margin=dict(l=80, r=80, t=100, b=80)
    )
    
    return fig

def create_volume_weighted_gex_chart(df: pd.DataFrame, spot_price: float) -> go.Figure:
    """Volume-Weighted GEX"""
    df_sorted = df.sort_values('strike').reset_index(drop=True)
    
    if 'volume_weighted_gex' not in df_sorted.columns:
        df_sorted['volume_weighted_gex'] = 0.0
    
    colors = ['#10b981' if x > 0 else '#ef4444' for x in df_sorted['volume_weighted_gex']]
    flip_zones = identify_gamma_flip_zones(df_sorted, spot_price)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=df_sorted['strike'],
        x=df_sorted['volume_weighted_gex'],
        orientation='h',
        marker_color=colors,
        name='VWGEX',
        hovertemplate='Strike: %{y:,.0f}<br>VW-GEX: %{x:.2f}<extra></extra>',
        showlegend=False
    ))
    
    fig.add_hline(y=spot_price, line_dash="dash", line_color="#06b6d4", line_width=3,
                  annotation_text=f"Spot: {spot_price:,.2f}", annotation_position="top right",
                  annotation=dict(font=dict(size=12, color="white")))
    
    fig.add_vline(x=0, line_dash="dot", line_color="gray", line_width=1)
    
    for zone in flip_zones:
        fig.add_hline(
            y=zone['strike'],
            line_dash="dot",
            line_color=zone['color'],
            line_width=2,
            annotation_text=f"🔄 {zone['strike']:,.0f}",
            annotation_position="left",
            annotation=dict(font=dict(size=10, color=zone['color']))
        )
    
    fig.update_layout(
        title=dict(text="<b>💰 Volume-Weighted GEX (Smart Money Positioning)</b>", font=dict(size=18, color='white')),
        xaxis_title="Volume-Weighted GEX Score",
        yaxis_title="Strike Price",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)',
        height=700,
        showlegend=False,
        hovermode='closest',
        xaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True, zeroline=True, zerolinecolor='rgba(128,128,128,0.5)'),
        yaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True),
        margin=dict(l=80, r=80, t=80, b=80)
    )
    
    return fig

def create_support_resistance_strength_chart(df: pd.DataFrame, spot_price: float) -> go.Figure:
    """Support/Resistance Strength"""
    df_sorted = df.sort_values('strike').reset_index(drop=True)
    
    if 'support_resistance_strength' not in df_sorted.columns:
        df_sorted['support_resistance_strength'] = 0.0
    
    flip_zones = identify_gamma_flip_zones(df_sorted, spot_price)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=df_sorted['strike'],
        x=df_sorted['support_resistance_strength'],
        orientation='h',
        marker=dict(
            color=df_sorted['support_resistance_strength'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(
                title=dict(text='Strength', font=dict(color='white', size=12)),
                tickfont=dict(color='white'),
                x=1.02
            )
        ),
        name='SR Strength',
        hovertemplate='Strike: %{y:,.0f}<br>Strength: %{x:.4f}<extra></extra>',
        showlegend=False
    ))
    
    fig.add_hline(y=spot_price, line_dash="dash", line_color="#06b6d4", line_width=3,
                  annotation_text=f"Spot: {spot_price:,.2f}", annotation_position="top right",
                  annotation=dict(font=dict(size=12, color="white")))
    
    for zone in flip_zones:
        fig.add_hline(
            y=zone['strike'],
            line_dash="dot",
            line_color=zone['color'],
            line_width=2,
            annotation_text=f"🔄 {zone['strike']:,.0f}",
            annotation_position="left",
            annotation=dict(font=dict(size=10, color=zone['color']))
        )
    
    fig.update_layout(
        title=dict(text="<b>🎯 Support/Resistance Strength Score</b>", font=dict(size=18, color='white')),
        xaxis_title="Strength Score (Higher = Stronger)",
        yaxis_title="Strike Price",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)',
        height=700,
        showlegend=False,
        hovermode='closest',
        xaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True),
        yaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True),
        margin=dict(l=80, r=120, t=80, b=80)
    )
    
    return fig

def create_vanna_adjusted_gex_chart(df: pd.DataFrame, spot_price: float) -> go.Figure:
    """VANNA-Adjusted GEX"""
    df_sorted = df.sort_values('strike').reset_index(drop=True)
    
    for col in ['net_gex', 'vanna_adj_gex_vol_up', 'vanna_adj_gex_vol_down']:
        if col not in df_sorted.columns:
            df_sorted[col] = 0.0
    
    df_sorted['vanna_impact_up'] = df_sorted['vanna_adj_gex_vol_up'] - df_sorted['net_gex']
    df_sorted['vanna_impact_down'] = df_sorted['vanna_adj_gex_vol_down'] - df_sorted['net_gex']
    max_impact = max(abs(df_sorted['vanna_impact_up'].max()), abs(df_sorted['vanna_impact_down'].min()))
    
    flip_zones = identify_gamma_flip_zones(df_sorted, spot_price)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        y=df_sorted['strike'],
        x=df_sorted['vanna_adj_gex_vol_down'],
        mode='lines+markers',
        name='Vol -5% (VANNA Adj)',
        line=dict(color='#ef4444', width=3, dash='dash'),
        marker=dict(size=5, symbol='triangle-left'),
        hovertemplate='Strike: %{y:,.0f}<br>Vol -5%: %{x:.4f}B<br>Impact: %{customdata:.4f}B<extra></extra>',
        customdata=df_sorted['vanna_impact_down']
    ))
    
    fig.add_trace(go.Scatter(
        y=df_sorted['strike'],
        x=df_sorted['net_gex'],
        mode='lines+markers',
        name='Current GEX',
        line=dict(color='#06b6d4', width=4),
        marker=dict(size=8, symbol='circle'),
        hovertemplate='Strike: %{y:,.0f}<br>Current: %{x:.4f}B<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        y=df_sorted['strike'],
        x=df_sorted['vanna_adj_gex_vol_up'],
        mode='lines+markers',
        name='Vol +5% (VANNA Adj)',
        line=dict(color='#10b981', width=3, dash='dash'),
        marker=dict(size=5, symbol='triangle-right'),
        hovertemplate='Strike: %{y:,.0f}<br>Vol +5%: %{x:.4f}B<br>Impact: %{customdata:.4f}B<extra></extra>',
        customdata=df_sorted['vanna_impact_up']
    ))
    
    fig.add_hline(y=spot_price, line_dash="dash", line_color="white", line_width=2,
                  annotation_text=f"Spot: {spot_price:,.2f}", annotation_position="top right",
                  annotation=dict(font=dict(size=12, color="white", family="Arial Black")))
    
    fig.add_vline(x=0, line_dash="dot", line_color="gray", line_width=1)
    
    near_spot = df_sorted[abs(df_sorted['strike'] - spot_price) <= spot_price * 0.02].copy()
    if len(near_spot) > 0:
        max_impact_row = near_spot.loc[near_spot['vanna_impact_up'].abs().idxmax()]
        if abs(max_impact_row['vanna_impact_up']) > 0.01:
            fig.add_annotation(
                x=max_impact_row['net_gex'],
                y=max_impact_row['strike'],
                text=f"VANNA Impact:<br>+5% vol = +{max_impact_row['vanna_impact_up']:.3f}B<br>-5% vol = {max_impact_row['vanna_impact_down']:.3f}B",
                showarrow=True,
                arrowhead=2,
                arrowcolor="yellow",
                bgcolor="rgba(0,0,0,0.8)",
                bordercolor="yellow",
                borderwidth=2,
                font=dict(color="white", size=10)
            )
    
    for zone in flip_zones:
        fig.add_hline(y=zone['strike'], line_dash="dot", line_color=zone['color'], line_width=1, opacity=0.3)
    
    fig.update_layout(
        title=dict(
            text="<b>🌊 VANNA-Adjusted GEX (Volatility Scenarios)</b><br><sub>Shows how GEX shifts with ±5% IV change</sub>",
            font=dict(size=18, color='white')
        ),
        xaxis_title="GEX (₹ Billions)",
        yaxis_title="Strike Price",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)',
        height=700,
        legend=dict(
            orientation='v',
            yanchor='top',
            y=0.99,
            xanchor='left',
            x=0.01,
            font=dict(color='white', size=12),
            bgcolor='rgba(0,0,0,0.7)',
            bordercolor='white',
            borderwidth=1
        ),
        hovermode='closest',
        xaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True, zeroline=True, zerolinecolor='rgba(128,128,128,0.5)'),
        yaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True),
        margin=dict(l=80, r=80, t=100, b=80)
    )
    
    if max_impact > 0.001:
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.98, y=0.02,
            text=f"Max VANNA Impact: ±{max_impact:.3f}B<br>5% vol change effect",
            showarrow=False,
            bgcolor="rgba(255,255,255,0.1)",
            bordercolor="white",
            borderwidth=1,
            font=dict(color="white", size=10),
            align="right"
        )
    
    return fig

def create_charm_adjusted_gex_chart(df: pd.DataFrame, spot_price: float) -> go.Figure:
    """CHARM-Adjusted GEX"""
    df_sorted = df.sort_values('strike').reset_index(drop=True)
    
    for col in ['net_gex', 'charm_adj_gex_2hr', 'charm_adj_gex_4hr']:
        if col not in df_sorted.columns:
            df_sorted[col] = 0.0
    
    df_sorted['charm_impact_2hr'] = df_sorted['charm_adj_gex_2hr'] - df_sorted['net_gex']
    df_sorted['charm_impact_4hr'] = df_sorted['charm_adj_gex_4hr'] - df_sorted['net_gex']
    max_impact = max(abs(df_sorted['charm_impact_4hr'].max()), abs(df_sorted['charm_impact_4hr'].min()))
    
    flip_zones = identify_gamma_flip_zones(df_sorted, spot_price)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        y=df_sorted['strike'],
        x=df_sorted['charm_adj_gex_4hr'],
        mode='lines+markers',
        name='+4 Hours (CHARM Adj)',
        line=dict(color='#8b5cf6', width=3, dash='dash'),
        marker=dict(size=5, symbol='diamond'),
        hovertemplate='Strike: %{y:,.0f}<br>+4hrs: %{x:.4f}B<br>Impact: %{customdata:.4f}B<extra></extra>',
        customdata=df_sorted['charm_impact_4hr']
    ))
    
    fig.add_trace(go.Scatter(
        y=df_sorted['strike'],
        x=df_sorted['charm_adj_gex_2hr'],
        mode='lines+markers',
        name='+2 Hours (CHARM Adj)',
        line=dict(color='#f59e0b', width=3, dash='dash'),
        marker=dict(size=5, symbol='square'),
        hovertemplate='Strike: %{y:,.0f}<br>+2hrs: %{x:.4f}B<br>Impact: %{customdata:.4f}B<extra></extra>',
        customdata=df_sorted['charm_impact_2hr']
    ))
    
    fig.add_trace(go.Scatter(
        y=df_sorted['strike'],
        x=df_sorted['net_gex'],
        mode='lines+markers',
        name='Current GEX',
        line=dict(color='#06b6d4', width=4),
        marker=dict(size=8, symbol='circle'),
        hovertemplate='Strike: %{y:,.0f}<br>Current: %{x:.4f}B<extra></extra>'
    ))
    
    fig.add_hline(y=spot_price, line_dash="dash", line_color="white", line_width=2,
                  annotation_text=f"Spot: {spot_price:,.2f}", annotation_position="top right",
                  annotation=dict(font=dict(size=12, color="white", family="Arial Black")))
    
    fig.add_vline(x=0, line_dash="dot", line_color="gray", line_width=1)
    
    near_spot = df_sorted[abs(df_sorted['strike'] - spot_price) <= spot_price * 0.02].copy()
    if len(near_spot) > 0:
        max_impact_row = near_spot.loc[near_spot['charm_impact_4hr'].abs().idxmax()]
        if abs(max_impact_row['charm_impact_4hr']) > 0.01:
            fig.add_annotation(
                x=max_impact_row['net_gex'],
                y=max_impact_row['strike'],
                text=f"CHARM Impact:<br>+2hr = {max_impact_row['charm_impact_2hr']:.3f}B<br>+4hr = {max_impact_row['charm_impact_4hr']:.3f}B",
                showarrow=True,
                arrowhead=2,
                arrowcolor="orange",
                bgcolor="rgba(0,0,0,0.8)",
                bordercolor="orange",
                borderwidth=2,
                font=dict(color="white", size=10)
            )
    
    for zone in flip_zones:
        fig.add_hline(y=zone['strike'], line_dash="dot", line_color=zone['color'], line_width=1, opacity=0.3)
    
    fig.update_layout(
        title=dict(
            text="<b>⏰ CHARM-Adjusted GEX (Time Decay Scenarios)</b><br><sub>Shows how GEX evolves with time decay</sub>",
            font=dict(size=18, color='white')
        ),
        xaxis_title="GEX (₹ Billions)",
        yaxis_title="Strike Price",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)',
        height=700,
        legend=dict(
            orientation='v',
            yanchor='top',
            y=0.99,
            xanchor='left',
            x=0.01,
            font=dict(color='white', size=12),
            bgcolor='rgba(0,0,0,0.7)',
            bordercolor='white',
            borderwidth=1
        ),
        hovermode='closest',
        xaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True, zeroline=True, zerolinecolor='rgba(128,128,128,0.5)'),
        yaxis=dict(gridcolor='rgba(128,128,128,0.2)', showgrid=True),
        margin=dict(l=80, r=80, t=100, b=80)
    )
    
    if max_impact > 0.001:
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.98, y=0.02,
            text=f"Max CHARM Impact: ±{max_impact:.3f}B<br>4-hour time decay effect",
            showarrow=False,
            bgcolor="rgba(255,255,255,0.1)",
            bordercolor="white",
            borderwidth=1,
            font=dict(color="white", size=10),
            align="right"
        )
    
    return fig

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Initialize session state for auto-refresh
    if 'last_refresh_time' not in st.session_state:
        st.session_state.last_refresh_time = time.time()
    if 'auto_refresh_enabled' not in st.session_state:
        st.session_state.auto_refresh_enabled = False
    if 'refresh_interval' not in st.session_state:
        st.session_state.refresh_interval = 300  # 5 minutes default
    
    # Header
    ist_now = datetime.now(IST)
    st.markdown(f"""
    <div class="main-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1 class="main-title">📊 NYZTrade Live GEX/DEX Dashboard Enhanced</h1>
                <p class="sub-title">Live Options Greeks | Weekly/Monthly Options | VANNA & CHARM | Gamma Flip Zones | Auto-Refresh | IST</p>
            </div>
            <div style="display: flex; gap: 12px; align-items: center;">
                <div class="live-indicator">
                    <div class="live-dot"></div>
                    <span style="color: #ef4444; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem;">LIVE</span>
                </div>
                <div style="text-align: right; font-family: 'JetBrains Mono', monospace; color: #94a3b8; font-size: 0.85rem;">
                    <div>{ist_now.strftime('%Y-%m-%d')}</div>
                    <div>{ist_now.strftime('%H:%M:%S IST')}</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        
        symbol = st.selectbox(
            "📈 Select Index",
            options=list(DHAN_SECURITY_IDS.keys()),
            index=0
        )
        
        st.markdown("---")
        st.markdown("### 🔄 Auto-Refresh Control")
        
        auto_refresh = st.toggle("Enable Auto-Refresh", value=st.session_state.auto_refresh_enabled)
        st.session_state.auto_refresh_enabled = auto_refresh
        
        if auto_refresh:
            refresh_interval = st.selectbox(
                "Refresh Interval",
                options=[60, 120, 300, 600],
                format_func=lambda x: f"{x//60} minute{'s' if x//60 > 1 else ''}",
                index=2
            )
            st.session_state.refresh_interval = refresh_interval
            
            # Calculate countdown
            elapsed = time.time() - st.session_state.last_refresh_time
            remaining = max(0, refresh_interval - elapsed)
            
            countdown_placeholder = st.empty()
            countdown_placeholder.markdown(f"""
            <div class="countdown-timer">
                ⏱️ Next refresh in: {int(remaining)}s
            </div>
            """, unsafe_allow_html=True)
            
            # Auto-refresh logic
            if remaining <= 0:
                st.session_state.last_refresh_time = time.time()
                st.rerun()
        
        manual_refresh = st.button("🔄 Manual Refresh Now", use_container_width=True, type="primary")
        if manual_refresh:
            st.session_state.last_refresh_time = time.time()
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📅 Date Selection (Past 5 Days)")
        
        # Generate past 5 trading days
        end_date = datetime.now()
        date_list = []
        current_date = end_date
        
        while len(date_list) < 5:
            if current_date.weekday() < 5:  # Monday to Friday
                date_list.append(current_date.date())
            current_date = current_date - timedelta(days=1)
        
        selected_date = st.selectbox(
            "Select Trading Day",
            options=date_list,
            index=0,
            format_func=lambda x: x.strftime('%Y-%m-%d (%A)')
        )
        
        target_date = selected_date.strftime('%Y-%m-%d')
        
        st.markdown("---")
        st.markdown("### 📆 Expiry Type & Selection")
        
        expiry_type = st.selectbox("Expiry Type", ["Weekly", "Monthly", "Mixed (Weekly + Monthly)"], index=0)
        
        if expiry_type == "Mixed (Weekly + Monthly)":
            st.info("🔀 **Mixed Mode**: Displays Weekly + Monthly side-by-side")
            expiry_flag = "MIXED"
            expiry_code = 1
        else:
            expiry_flag = "WEEK" if expiry_type == "Weekly" else "MONTH"
            
            expiry_option = st.selectbox(
                "Select Expiry",
                ["Current Week/Month (Nearest)", "Next Week/Month", "Far Week/Month"],
                index=0
            )
            
            expiry_code_map = {
                "Current Week/Month (Nearest)": 1,
                "Next Week/Month": 2,
                "Far Week/Month": 3
            }
            expiry_code = expiry_code_map[expiry_option]
            
            st.info(f"📌 Selected: **{expiry_type}** | **{expiry_option}**")
        
        st.markdown("---")
        st.markdown("### 🎯 Strike Selection")
        
        strikes = st.multiselect(
            "Select Strikes",
            ["ATM", "ATM+1", "ATM-1", "ATM+2", "ATM-2", "ATM+3", "ATM-3", 
             "ATM+4", "ATM-4", "ATM+5", "ATM-5", "ATM+6", "ATM-6", "ATM+7", "ATM-7", 
             "ATM+8", "ATM-8", "ATM+9", "ATM-9", "ATM+10", "ATM-10"],
            default=["ATM", "ATM+1", "ATM-1", "ATM+2", "ATM-2", "ATM+3", "ATM-3", 
                    "ATM+4", "ATM-4", "ATM+5", "ATM-5"]
        )
        
        st.markdown("---")
        st.markdown("### ⏱️ Time Interval")
        
        interval = st.selectbox(
            "Select Interval",
            options=["1", "5", "15", "60"],
            format_func=lambda x: "1 minute" if x == "1" else "5 minutes" if x == "5" else "15 minutes" if x == "15" else "1 hour",
            index=1
        )
        
        st.info(f"📊 Selected: {len(strikes)} strikes | {interval} min interval")
        
        st.markdown("---")
        st.markdown("### 🕐 Current IST Time")
        st.info(f"{ist_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        st.markdown("---")
        
        fetch_button = st.button("🚀 Fetch Live Data", use_container_width=True, type="primary")
    
    # Store configuration in session state
    if fetch_button:
        st.session_state.fetch_config = {
            'symbol': symbol,
            'target_date': target_date,
            'strikes': strikes,
            'interval': interval,
            'expiry_code': expiry_code,
            'expiry_flag': expiry_flag
        }
        st.session_state.data_fetched = False
        st.session_state.last_refresh_time = time.time()
    
    # Main content
    if fetch_button or (hasattr(st.session_state, 'fetch_config') and st.session_state.get('data_fetched', False)):
        if hasattr(st.session_state, 'fetch_config'):
            config = st.session_state.fetch_config
            symbol = config['symbol']
            target_date = config['target_date']
            strikes = config['strikes']
            interval = config['interval']
            expiry_code = config.get('expiry_code', 1)
            expiry_flag = config.get('expiry_flag', 'WEEK')
        
        if not strikes:
            st.error("❌ Please select at least one strike")
            return
        
        if not st.session_state.get('data_fetched', False) or 'df_data' not in st.session_state:
            st.markdown(f"""
            <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, rgba(239,68,68,0.2), rgba(220,38,38,0.2)); 
                        border-radius: 12px; margin: 20px 0; border: 2px solid rgba(239,68,68,0.4);'>
                <div style='font-size: 1.5rem; color: #ef4444; font-weight: bold; margin-bottom: 10px;'>
                    📡 FETCHING LIVE DATA
                </div>
                <div style='font-size: 0.9rem; color: #fca5a5;'>
                    {symbol} | {target_date} | {interval} min | This may take 1-3 minutes
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="metric-card neutral" style="margin: 20px 0;">
                <div class="metric-label">Fetching Live Data</div>
                <div class="metric-value" style="color: #ef4444; font-size: 1.2rem;">
                    {symbol} | {target_date} | {interval} min | {expiry_flag} Expiry {expiry_code}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            try:
                start_time = time.time()
                fetcher = DhanLiveFetcher(DhanConfig())
                
                # Handle Mixed expiry
                if expiry_flag == "MIXED":
                    st.info("🔀 Fetching Weekly data...")
                    df_weekly, meta_weekly = fetcher.process_live_data(symbol, target_date, strikes, interval, 1, "WEEK")
                    
                    st.info("🔀 Fetching Monthly data...")
                    df_monthly, meta_monthly = fetcher.process_live_data(symbol, target_date, strikes, interval, 1, "MONTH")
                    
                    load_time = time.time() - start_time
                    st.info(f"📡 Fetched in {load_time:.1f} seconds")
                    
                    if df_weekly is not None and len(df_weekly) > 0 and df_monthly is not None and len(df_monthly) > 0:
                        st.success(f"✅ Loaded {len(df_weekly)} weekly + {len(df_monthly)} monthly data points")
                        
                        df = df_weekly
                        meta = meta_weekly
                        meta['expiry_type'] = 'Mixed (Weekly + Monthly Overlay)'
                        
                        st.session_state.df_monthly = df_monthly
                        st.session_state.has_mixed_data = True
                        
                    elif df_weekly is not None and len(df_weekly) > 0:
                        st.warning("⚠️ Monthly data not available, using Weekly only")
                        df, meta = df_weekly, meta_weekly
                        st.session_state.has_mixed_data = False
                    elif df_monthly is not None and len(df_monthly) > 0:
                        st.warning("⚠️ Weekly data not available, using Monthly only")
                        df, meta = df_monthly, meta_monthly
                        st.session_state.has_mixed_data = False
                    else:
                        st.error("❌ No data available")
                        return
                else:
                    df, meta = fetcher.process_live_data(symbol, target_date, strikes, interval, expiry_code, expiry_flag)
                    
                    load_time = time.time() - start_time
                    st.info(f"📡 Fetched in {load_time:.1f} seconds")
                    
                    st.session_state.has_mixed_data = False
                
                if df is None or len(df) == 0:
                    st.error("❌ No data available. Please try a different date.")
                    return
                
                st.session_state.df_data = df
                st.session_state.meta_data = meta
                st.session_state.data_fetched = True
                st.rerun()
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("Please check your API credentials and try again.")
                import traceback
                st.code(traceback.format_exc())
                return
        
        # Retrieve from session state
        df = st.session_state.df_data
        meta = st.session_state.meta_data
        
        all_timestamps = sorted(df['timestamp'].unique())
        timestamp_options = [ts.strftime('%H:%M IST') for ts in all_timestamps]
        
        st.success(f"✅ Data loaded | Records: {len(df):,} | Interval: {meta['interval']} | {meta['expiry_flag']} Expiry Code: {meta['expiry_code']}")
        
        st.markdown("---")
        st.markdown("### ⏱️ Time Navigation")
            
        control_cols = st.columns([1, 1, 1, 1, 1, 1, 1, 1])
        
        with control_cols[0]:
            if st.button("⏮️ First", use_container_width=True):
                st.session_state.timestamp_idx = 0
        
        with control_cols[1]:
            if st.button("◀️ Prev", use_container_width=True):
                current = st.session_state.get('timestamp_idx', len(all_timestamps) - 1)
                st.session_state.timestamp_idx = max(0, current - 1)
        
        with control_cols[2]:
            if st.button("🔄 Reset", use_container_width=True):
                st.session_state.timestamp_idx = len(all_timestamps) - 1
        
        with control_cols[3]:
            if st.button("▶️ Next", use_container_width=True):
                current = st.session_state.get('timestamp_idx', len(all_timestamps) - 1)
                st.session_state.timestamp_idx = min(len(all_timestamps) - 1, current + 1)
        
        with control_cols[4]:
            if st.button("⏭️ Last", use_container_width=True):
                st.session_state.timestamp_idx = len(all_timestamps) - 1
        
        with control_cols[5]:
            if st.button("⏰ 9:30", use_container_width=True):
                morning_times = [i for i, ts in enumerate(all_timestamps) if ts.hour == 9 and ts.minute >= 30]
                if morning_times:
                    st.session_state.timestamp_idx = morning_times[0]
        
        with control_cols[6]:
            if st.button("⏰ 12:00", use_container_width=True):
                noon_times = [i for i, ts in enumerate(all_timestamps) if ts.hour == 12]
                if noon_times:
                    st.session_state.timestamp_idx = noon_times[0]
        
        with control_cols[7]:
            if st.button("⏰ 3:15", use_container_width=True):
                close_times = [i for i, ts in enumerate(all_timestamps) if ts.hour == 15 and ts.minute >= 15]
                if close_times:
                    st.session_state.timestamp_idx = close_times[0]
        
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            st.markdown(f"""<div class="metric-card neutral" style="padding: 15px;">
                <div class="metric-label">Start Time</div>
                <div class="metric-value" style="font-size: 1.2rem;">{timestamp_options[0]}</div>
            </div>""", unsafe_allow_html=True)
        
        with col2:
            if 'timestamp_idx' not in st.session_state:
                st.session_state.timestamp_idx = len(all_timestamps) - 1
            
            selected_timestamp_idx = st.slider(
                "🎯 Drag to navigate through intraday data points",
                min_value=0,
                max_value=len(all_timestamps) - 1,
                value=st.session_state.timestamp_idx,
                format="",
                key="time_slider"
            )
            
            st.session_state.timestamp_idx = selected_timestamp_idx
            selected_timestamp = all_timestamps[selected_timestamp_idx]
            
            progress = (selected_timestamp_idx + 1) / len(all_timestamps)
            st.progress(progress)
            
            st.info(f"📍 **{selected_timestamp.strftime('%H:%M:%S IST')}** | Point {selected_timestamp_idx + 1} of {len(all_timestamps)}")
        
        with col3:
            st.markdown(f"""<div class="metric-card neutral" style="padding: 15px;">
                <div class="metric-label">End Time</div>
                <div class="metric-value" style="font-size: 1.2rem;">{timestamp_options[-1]}</div>
            </div>""", unsafe_allow_html=True)
        
        # Filter data for selected timestamp
        df_selected = df[df['timestamp'] == selected_timestamp].copy()
        
        if len(df_selected) == 0:
            closest_idx = min(range(len(all_timestamps)), 
                             key=lambda i: abs((all_timestamps[i] - selected_timestamp).total_seconds()))
            df_selected = df[df['timestamp'] == all_timestamps[closest_idx]].copy()
        
        df_latest = df_selected
        spot_price = df_latest['spot_price'].iloc[0] if len(df_latest) > 0 else 0
        
        # Calculate strike range for nearest 6 strikes
        config = SYMBOL_CONFIG.get(symbol, SYMBOL_CONFIG["NIFTY"])
        strike_interval = config["strike_interval"]
        
        strike_range = 3 * strike_interval
        df_calc = df_latest[
            (df_latest['strike'] >= spot_price - strike_range) & 
            (df_latest['strike'] <= spot_price + strike_range)
        ].copy()
        
        # Calculate metrics
        total_gex = df_calc['net_gex'].sum()
        total_dex = df_calc['net_dex'].sum()
        total_net = total_gex + total_dex
        total_call_oi = df_calc['call_oi'].sum()
        total_put_oi = df_calc['put_oi'].sum()
        pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 1
        
        # Identify gamma flip zones
        flip_zones = identify_gamma_flip_zones(df_latest, spot_price)
        
        # Display overview metrics
        st.markdown("### 📊 Live Data Overview")
        
        if len(flip_zones) > 0:
            flip_info = " | ".join([f"🔄 Flip @ ₹{z['strike']:,.0f} {z['arrow']}" for z in flip_zones[:3]])
            st.info(f"""
            📊 **Calculation**: Metrics use nearest 6 strikes (±3 from ATM at ₹{spot_price:,.0f})
            
            🎯 **Gamma Flip Zones**: {flip_info}
            """)
        else:
            st.info(f"📊 **Calculation**: Metrics use nearest 6 strikes (±3 from ATM at ₹{spot_price:,.0f})")
        
        cols = st.columns(6)
        
        with cols[0]:
            st.markdown(f"""<div class="metric-card neutral">
                <div class="metric-label">Date & Time</div>
                <div class="metric-value" style="font-size: 1.2rem;">{target_date}</div>
                <div class="metric-delta">{selected_timestamp.strftime('%H:%M:%S IST')}</div>
            </div>""", unsafe_allow_html=True)
        
        with cols[1]:
            st.markdown(f"""<div class="metric-card neutral">
                <div class="metric-label">Spot Price</div>
                <div class="metric-value">₹{spot_price:,.2f}</div>
                <div class="metric-delta">@ Selected Time</div>
            </div>""", unsafe_allow_html=True)
        
        with cols[2]:
            gex_class = "positive" if total_gex > 0 else "negative"
            st.markdown(f"""<div class="metric-card {gex_class}">
                <div class="metric-label">Total NET GEX</div>
                <div class="metric-value {gex_class}">{total_gex:.4f}B</div>
                <div class="metric-delta">{'Suppression' if total_gex > 0 else 'Amplification'}</div>
            </div>""", unsafe_allow_html=True)
        
        with cols[3]:
            dex_class = "positive" if total_dex > 0 else "negative"
            st.markdown(f"""<div class="metric-card {dex_class}">
                <div class="metric-label">Total NET DEX</div>
                <div class="metric-value {dex_class}">{total_dex:.4f}B</div>
                <div class="metric-delta">{'Bullish' if total_dex > 0 else 'Bearish'}</div>
            </div>""", unsafe_allow_html=True)
        
        with cols[4]:
            net_class = "positive" if total_net > 0 else "negative"
            st.markdown(f"""<div class="metric-card {net_class}">
                <div class="metric-label">GEX + DEX</div>
                <div class="metric-value {net_class}">{total_net:.4f}B</div>
                <div class="metric-delta">Combined Signal</div>
            </div>""", unsafe_allow_html=True)
        
        with cols[5]:
            pcr_class = "positive" if pcr > 1 else "negative"
            st.markdown(f"""<div class="metric-card {pcr_class}">
                <div class="metric-label">Put/Call Ratio</div>
                <div class="metric-value {pcr_class}">{pcr:.2f}</div>
                <div class="metric-delta">{'Bearish' if pcr > 1.2 else 'Bullish' if pcr < 0.8 else 'Neutral'}</div>
            </div>""", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Signal badges
        cols = st.columns(5)
        with cols[0]:
            gex_signal = "🟢 GEX SUPPRESSION" if total_gex > 0 else "🔴 GEX AMPLIFICATION"
            gex_badge = "bullish" if total_gex > 0 else "bearish"
            st.markdown(f'<div class="signal-badge {gex_badge}">{gex_signal}</div>', unsafe_allow_html=True)
        
        with cols[1]:
            dex_signal = "🟢 DEX BULLISH" if total_dex > 0 else "🔴 DEX BEARISH"
            dex_badge = "bullish" if total_dex > 0 else "bearish"
            st.markdown(f'<div class="signal-badge {dex_badge}">{dex_signal}</div>', unsafe_allow_html=True)
        
        with cols[2]:
            net_signal = "🟢 NET POSITIVE" if total_net > 0 else "🔴 NET NEGATIVE"
            net_badge = "bullish" if total_net > 0 else "bearish"
            st.markdown(f'<div class="signal-badge {net_badge}">{net_signal}</div>', unsafe_allow_html=True)
        
        with cols[3]:
            st.markdown(f'<div class="signal-badge volatile">📊 {len(df_latest)} Strikes</div>', unsafe_allow_html=True)
        
        with cols[4]:
            if len(flip_zones) > 0:
                st.markdown(f'<div class="signal-badge volatile">🔄 {len(flip_zones)} Flip Zones</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ALL CHART TABS (keeping everything from historical version)
        tabs = st.tabs(["🎯 GEX", "📊 DEX", "⚡ NET GEX+DEX", "🎪 Hedge Pressure", 
                        "🌊 GEX Flow", "🔄 GEX Overlay", "📊 OI Change GEX", "🌊 DEX Flow", 
                        "🔮 Predictive Models", "🌊 VANNA", "⏰ CHARM",
                        "📈 Intraday Timeline", "📋 OI & Data"])
        
        with tabs[0]:
            st.markdown("### 🎯 Gamma Exposure (GEX) Analysis with Flip Zones")
            
            if st.session_state.get('has_mixed_data', False) and 'df_monthly' in st.session_state:
                st.info("🔀 **Mixed Mode Active**: Blue/Purple = Weekly | Green/Red = Monthly")
                st.plotly_chart(create_mixed_gex_overlay_chart(df, st.session_state.df_monthly, spot_price, selected_timestamp), use_container_width=True)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    weekly_pos = df_latest[df_latest['net_gex'] > 0]['net_gex'].sum()
                    st.metric("Weekly Positive", f"{weekly_pos:.4f}B")
                with col2:
                    weekly_neg = df_latest[df_latest['net_gex'] < 0]['net_gex'].sum()
                    st.metric("Weekly Negative", f"{weekly_neg:.4f}B")
                
                df_monthly_latest = st.session_state.df_monthly[st.session_state.df_monthly['timestamp'] == selected_timestamp]
                with col3:
                    monthly_pos = df_monthly_latest[df_monthly_latest['net_gex'] > 0]['net_gex'].sum()
                    st.metric("Monthly Positive", f"{monthly_pos:.4f}B")
                with col4:
                    monthly_neg = df_monthly_latest[df_monthly_latest['net_gex'] < 0]['net_gex'].sum()
                    st.metric("Monthly Negative", f"{monthly_neg:.4f}B")
            else:
                st.plotly_chart(create_separate_gex_chart(df_latest, spot_price), use_container_width=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    positive_gex = df_latest[df_latest['net_gex'] > 0]['net_gex'].sum()
                    st.metric("Positive GEX", f"{positive_gex:.4f}B")
                with col2:
                    negative_gex = df_latest[df_latest['net_gex'] < 0]['net_gex'].sum()
                    st.metric("Negative GEX", f"{negative_gex:.4f}B")
            
            if len(flip_zones) > 0:
                st.markdown("#### 🔄 Gamma Flip Zones")
                for zone in flip_zones:
                    st.markdown(f"- **Flip @ ₹{zone['strike']:,.0f}** {zone['arrow']} | {zone['flip_type']}")
            
        with tabs[1]:
            st.markdown("### 📊 Delta Exposure (DEX) Analysis")
            st.plotly_chart(create_separate_dex_chart(df_latest, spot_price), use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                positive_dex = df_latest[df_latest['net_dex'] > 0]['net_dex'].sum()
                st.metric("Positive DEX", f"{positive_dex:.4f}B")
            with col2:
                negative_dex = df_latest[df_latest['net_dex'] < 0]['net_dex'].sum()
                st.metric("Negative DEX", f"{negative_dex:.4f}B")
            
        with tabs[2]:
            st.markdown("### ⚡ Combined NET GEX + DEX with Flip Zones")
            st.plotly_chart(create_net_gex_dex_chart(df_latest, spot_price), use_container_width=True)
            
        with tabs[3]:
            st.markdown("### 🎪 Hedging Pressure with Flip Zones")
            st.plotly_chart(create_hedging_pressure_chart(df_latest, spot_price), use_container_width=True)
            
        with tabs[4]:
            st.markdown("### 🌊 GEX Flow Analysis with Flip Zones")
            st.plotly_chart(create_gex_flow_chart(df_latest, spot_price), use_container_width=True)
            
            total_gex_inflow = df_latest[df_latest['net_gex_flow'] > 0]['net_gex_flow'].sum()
            total_gex_outflow = df_latest[df_latest['net_gex_flow'] < 0]['net_gex_flow'].sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("GEX Inflow", f"{total_gex_inflow:.4f}B")
            with col2:
                st.metric("GEX Outflow", f"{total_gex_outflow:.4f}B")
            with col3:
                net_flow = total_gex_inflow + total_gex_outflow
                st.metric("Net GEX Flow", f"{net_flow:.4f}B")
        
        with tabs[5]:
            st.markdown("### 🔄 GEX Overlay: Original vs OI-Based")
            st.plotly_chart(create_gex_overlay_chart(df_latest, spot_price), use_container_width=True)
        
        with tabs[6]:
            st.markdown("### 📊 OI Change GEX - Pure Position Activity")
            st.plotly_chart(create_oi_based_gex_chart(df_latest, spot_price), use_container_width=True)
            
        with tabs[7]:
            st.markdown("### 🌊 DEX Flow Analysis")
            st.plotly_chart(create_dex_flow_chart(df_latest, spot_price), use_container_width=True)
            
        with tabs[8]:
            st.markdown("### 🔮 Predictive GEX Models")
            st.plotly_chart(create_volume_weighted_gex_chart(df_latest, spot_price), use_container_width=True)
            st.plotly_chart(create_support_resistance_strength_chart(df_latest, spot_price), use_container_width=True)
            
        with tabs[9]:
            st.markdown("### 🌊 VANNA Exposure")
            if st.session_state.get('has_mixed_data', False) and 'df_monthly' in st.session_state:
                st.plotly_chart(create_mixed_vanna_overlay_chart(df, st.session_state.df_monthly, spot_price, selected_timestamp), use_container_width=True)
            else:
                st.plotly_chart(create_vanna_exposure_chart(df_latest, spot_price), use_container_width=True)
                st.plotly_chart(create_vanna_adjusted_gex_chart(df_latest, spot_price), use_container_width=True)
            
        with tabs[10]:
            st.markdown("### ⏰ CHARM Exposure")
            if st.session_state.get('has_mixed_data', False) and 'df_monthly' in st.session_state:
                st.plotly_chart(create_mixed_charm_overlay_chart(df, st.session_state.df_monthly, spot_price, selected_timestamp), use_container_width=True)
            else:
                st.plotly_chart(create_charm_exposure_chart(df_latest, spot_price), use_container_width=True)
                st.plotly_chart(create_charm_adjusted_gex_chart(df_latest, spot_price), use_container_width=True)
            
        with tabs[11]:
            st.markdown("### 📈 Intraday Evolution")
            st.plotly_chart(create_intraday_timeline(df, selected_timestamp), use_container_width=True)
            
        with tabs[12]:
            st.markdown("### 📋 Open Interest Distribution")
            st.plotly_chart(create_oi_distribution(df_latest, spot_price), use_container_width=True)
            
            st.markdown("### 📊 Complete Data Table")
            display_df = df_latest[['strike', 'call_oi', 'put_oi', 'call_volume', 'put_volume', 
                                   'net_gex', 'net_dex', 'hedging_pressure']].copy()
            display_df['net_gex'] = display_df['net_gex'].apply(lambda x: f"{x:.4f}B")
            display_df['net_dex'] = display_df['net_dex'].apply(lambda x: f"{x:.4f}B")
            display_df['hedging_pressure'] = display_df['hedging_pressure'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)
            
            # Download button
            st.markdown("### 📥 Download Data")
            csv = df.to_csv(index=False)
            st.download_button(
                "📄 Download CSV",
                data=csv,
                file_name=f"NYZTrade_Live_{symbol}_{target_date}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    else:
        # Initial instructions
        st.info("""
        👋 **Welcome to NYZTrade Live GEX/DEX Dashboard!**
        
        **🔴 LIVE DATA with AUTO-REFRESH**
        - ⚡ Real-time options data fetching
        - 🔄 Auto-refresh with countdown timer
        - 📊 Manual refresh anytime
        - 🕐 IST timezone display
        
        **📅 Past 5 Trading Days Available**
        - Select any of the last 5 trading days
        - Full intraday data with all intervals
        - Complete historical analysis
        
        **🆕 Enhanced Features:**
        - 📆 Weekly, Monthly & Mixed Options
        - 🌊 VANNA & CHARM Exposure
        - 🔄 Gamma Flip Zones
        - ⏱️ 1-Minute to 1-Hour Intervals
        - 🌊 GEX & DEX Flow Analysis
        - 📊 OI Change GEX
        - 🔄 GEX Overlay Charts
        - 🔮 Predictive Models
        
        **How to use:**
        1. Select index (NIFTY/BANKNIFTY/FINNIFTY/MIDCPNIFTY)
        2. Enable/disable auto-refresh
        3. Choose date from past 5 trading days
        4. Select expiry type (Weekly/Monthly/Mixed)
        5. Select strikes (ATM ±10)
        6. Choose interval (1/5/15/60 minutes)
        7. Click "Fetch Live Data"
        8. Navigate through time with slider
        9. Explore 13 analysis tabs
        """)
    
    # Footer
    st.markdown("---")
    st.markdown(f"""<div style="text-align: center; padding: 20px; color: #64748b;">
        <p style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;">
        NYZTrade Live GEX/DEX Dashboard | Live Data with Auto-Refresh | Data: Dhan API | IST<br>
        Weekly/Monthly/Mixed Options | VANNA & CHARM | Gamma Flip Zones | All Chart Types<br>
        13 Analysis Tabs | Past 5 Trading Days | 1-min to 60-min Intervals</p>
        <p style="font-size: 0.75rem;">⚠️ Educational purposes only. Options trading involves substantial risk.</p>
    </div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
