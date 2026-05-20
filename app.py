from __future__ import annotations

import json
import math
import re
import time
from html import escape
from typing import Any, Iterable

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
from bs4 import BeautifulSoup
from plotly.subplots import make_subplots


st.set_page_config(
    page_title="미국 주식 리서치 대시보드",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


PERIOD_OPTIONS = {
    "1개월": "1mo",
    "3개월": "3mo",
    "6개월": "6mo",
    "1년": "1y",
    "3년": "3y",
    "5년": "5y",
    "최대": "max",
}

INTERVAL_OPTIONS = {
    "일봉": "1d",
    "주봉": "1wk",
    "월봉": "1mo",
}

AUTO_REFRESH_OPTIONS = {
    "끄기": 0,
    "15초": 15,
    "30초": 30,
    "1분": 60,
    "3분": 180,
    "5분": 300,
    "10분": 600,
}

FINANCIAL_NAME_KO = {
    "Total Revenue": "매출",
    "Gross Profit": "매출총이익",
    "Operating Income": "영업이익",
    "Net Income": "순이익",
    "Total Assets": "총자산",
    "Total Liabilities Net Minority Interest": "총부채",
    "Total Liab": "총부채",
    "Stockholders Equity": "자기자본",
    "Total Stockholder Equity": "자기자본",
    "Operating Cash Flow": "영업활동현금흐름",
    "Capital Expenditure": "설비투자",
    "Free Cash Flow": "잉여현금흐름",
    "Cost Of Revenue": "매출원가",
    "Research And Development": "연구개발비",
    "Selling General And Administration": "판매관리비",
    "Basic EPS": "기본 EPS",
    "Diluted EPS": "희석 EPS",
    "EBITDA": "EBITDA",
    "Current Assets": "유동자산",
    "Current Liabilities": "유동부채",
    "Total Debt": "총차입금",
    "Cash And Cash Equivalents": "현금및현금성자산",
    "Repurchase Of Capital Stock": "자사주매입",
    "Dividends Paid": "배당금지급",
}

VALUATION_INTERPRETATIONS = {
    "PER": "주가가 순이익 대비 어느 정도 수준인지 보는 지표다. 높으면 성장 기대가 반영됐을 수 있지만 고평가 가능성도 함께 점검해야 한다.",
    "Forward PER": "향후 예상 이익 기준의 PER이다. 미래 실적 전망이 바뀌면 값도 크게 달라질 수 있다.",
    "PBR": "자산 대비 주가 수준을 보는 지표다. 업종별 자산 구조가 달라 단순 비교에는 주의가 필요하다.",
    "PSR": "매출 대비 시가총액 수준을 보는 지표다. 이익 변동성이 큰 성장 기업 분석에 보조적으로 쓰인다.",
    "EV/EBITDA": "기업가치를 EBITDA와 비교한 지표다. 부채와 현금 구조를 함께 반영한다.",
    "PEG Ratio": "PER을 이익 성장률과 함께 보는 지표다. 성장률 추정치의 신뢰도가 중요하다.",
    "ROE": "자기자본 대비 수익성을 보여준다. 부채 비중이 높은 기업은 함께 확인해야 한다.",
    "ROA": "총자산 대비 수익성을 보여준다. 자산을 얼마나 효율적으로 쓰는지 참고할 수 있다.",
    "Gross Margin": "매출총이익률이다. 제품이나 서비스의 기본 수익성을 보여준다.",
    "Operating Margin": "영업이익률이다. 본업의 비용 구조와 수익성을 함께 반영한다.",
    "Net Margin": "순이익률이다. 영업 외 손익과 세금까지 반영한 최종 수익성 지표다.",
    "Debt to Equity": "자기자본 대비 차입 부담을 보는 지표다. 업종별 적정 수준이 다르다.",
    "Current Ratio": "유동부채 대비 유동자산 비율이다. 단기 지급 능력을 참고하는 지표다.",
    "Free Cash Flow Yield": "시가총액 대비 잉여현금흐름 비율이다. 현금 창출력을 가격과 함께 보는 보조 지표다.",
    "배당수익률": "주가 대비 연간 배당 수준을 보여준다. 배당 지속 가능성은 현금흐름과 함께 확인해야 한다.",
}

MAJOR_US_LISTED_TICKERS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "GOOG",
    "META",
    "BRK-B",
    "LLY",
    "AVGO",
    "TSM",
    "TSLA",
    "JPM",
    "V",
    "UNH",
    "XOM",
    "MA",
    "COST",
    "NFLX",
    "WMT",
    "PG",
    "JNJ",
    "HD",
    "ORCL",
    "ABBV",
    "BAC",
    "KO",
    "CRM",
    "AMD",
    "PLTR",
    "CSCO",
    "CVX",
    "MRK",
    "PEP",
    "TMO",
    "LIN",
    "ADBE",
    "MCD",
    "IBM",
    "QCOM",
    "WFC",
    "ABT",
    "DIS",
    "INTU",
    "PM",
    "TXN",
    "AMGN",
    "CAT",
    "ISRG",
    "NOW",
    "GS",
    "UBER",
    "RTX",
    "MS",
    "NEE",
    "HON",
    "BKNG",
    "SPGI",
    "LOW",
    "PFE",
    "UNP",
    "BLK",
]

MAJOR_TICKER_SECTORS = {
    "AAPL": "Technology",
    "MSFT": "Technology",
    "NVDA": "Technology",
    "AMZN": "Consumer Discretionary",
    "GOOGL": "Communication Services",
    "GOOG": "Communication Services",
    "META": "Communication Services",
    "BRK-B": "Financials",
    "LLY": "Health Care",
    "AVGO": "Technology",
    "TSM": "Technology",
    "TSLA": "Consumer Discretionary",
    "JPM": "Financials",
    "V": "Financials",
    "UNH": "Health Care",
    "XOM": "Energy",
    "MA": "Financials",
    "COST": "Consumer Staples",
    "NFLX": "Communication Services",
    "WMT": "Consumer Staples",
    "PG": "Consumer Staples",
    "JNJ": "Health Care",
    "HD": "Consumer Discretionary",
    "ORCL": "Technology",
    "ABBV": "Health Care",
    "BAC": "Financials",
    "KO": "Consumer Staples",
    "CRM": "Technology",
    "AMD": "Technology",
    "PLTR": "Technology",
    "CSCO": "Technology",
    "CVX": "Energy",
    "MRK": "Health Care",
    "PEP": "Consumer Staples",
    "TMO": "Health Care",
    "LIN": "Materials",
    "ADBE": "Technology",
    "MCD": "Consumer Discretionary",
    "IBM": "Technology",
    "QCOM": "Technology",
    "WFC": "Financials",
    "ABT": "Health Care",
    "DIS": "Communication Services",
    "INTU": "Technology",
    "PM": "Consumer Staples",
    "TXN": "Technology",
    "AMGN": "Health Care",
    "CAT": "Industrials",
    "ISRG": "Health Care",
    "NOW": "Technology",
    "GS": "Financials",
    "UBER": "Industrials",
    "RTX": "Industrials",
    "MS": "Financials",
    "NEE": "Utilities",
    "HON": "Industrials",
    "BKNG": "Consumer Discretionary",
    "SPGI": "Financials",
    "LOW": "Consumer Discretionary",
    "PFE": "Health Care",
    "UNP": "Industrials",
    "BLK": "Financials",
}

YAHOO_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

SEC_HEADERS = {
    "User-Agent": "personal-stock-research-dashboard/1.0 contact@example.com",
    "Accept-Encoding": "gzip, deflate",
}

YAHOO_INFO_MODULES = ",".join(
    [
        "price",
        "summaryDetail",
        "defaultKeyStatistics",
        "financialData",
        "assetProfile",
    ]
)

SEC_FACT_TAGS = {
    "Total Revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    ],
    "Gross Profit": ["GrossProfit"],
    "Operating Income": ["OperatingIncomeLoss"],
    "Net Income": ["NetIncomeLoss", "ProfitLoss"],
    "Total Assets": ["Assets"],
    "Total Liabilities Net Minority Interest": ["Liabilities"],
    "Stockholders Equity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    "Operating Cash Flow": ["NetCashProvidedByUsedInOperatingActivities"],
    "Capital Expenditure": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
    ],
}


def apply_custom_style() -> None:
    st.markdown(
        """
        <style>
        :root {
            --dash-border: rgba(49, 65, 88, 0.16);
            --dash-muted: #64748b;
            --dash-soft: #f6f8fb;
            --dash-ink: #0f172a;
            --dash-blue: #1d4ed8;
        }
        .block-container {
            padding-top: 2.1rem;
            padding-bottom: 2.5rem;
        }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid var(--dash-border);
            border-radius: 8px;
            padding: 0.85rem 0.95rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }
        div[data-testid="stMetricLabel"] p {
            color: var(--dash-muted);
            font-size: 0.86rem;
        }
        div[data-testid="stMetricValue"] {
            color: var(--dash-ink);
            font-size: 1.2rem;
        }
        .app-subtitle {
            color: var(--dash-muted);
            margin-top: -0.5rem;
            margin-bottom: 1.2rem;
            font-size: 1rem;
        }
        .info-card {
            background: #ffffff;
            border: 1px solid var(--dash-border);
            border-radius: 8px;
            padding: 0.9rem 1rem;
            min-height: 92px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }
        .info-card .label {
            color: var(--dash-muted);
            display: block;
            font-size: 0.84rem;
            margin-bottom: 0.45rem;
        }
        .info-card .value {
            color: var(--dash-ink);
            font-size: 1.02rem;
            font-weight: 650;
            overflow-wrap: anywhere;
        }
        .section-note {
            color: var(--dash-muted);
            font-size: 0.9rem;
        }
        .quote-card-grid {
            display: grid;
            gap: 0.75rem;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            margin: 0.25rem 0 1.05rem;
        }
        .quote-card {
            background: #ffffff;
            border: 1px solid var(--dash-border);
            border-radius: 8px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
            min-height: 76px;
            padding: 0.85rem 0.95rem;
        }
        .quote-card .label {
            color: var(--dash-muted);
            display: block;
            font-size: 0.82rem;
            margin-bottom: 0.32rem;
        }
        .quote-card .value {
            color: var(--dash-ink);
            display: block;
            font-size: 1.04rem;
            font-weight: 700;
            overflow-wrap: anywhere;
        }
        @media (max-width: 768px) {
            .block-container {
                padding-left: 0.75rem;
                padding-right: 0.75rem;
                padding-top: 0.9rem;
            }
            h1 {
                font-size: 1.75rem !important;
                line-height: 1.18 !important;
            }
            h2, h3 {
                line-height: 1.25 !important;
            }
            .app-subtitle {
                font-size: 0.88rem;
                line-height: 1.45;
                margin-bottom: 0.8rem;
            }
            .quote-card-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 0.55rem;
            }
            .quote-card {
                min-height: 66px;
                padding: 0.72rem 0.78rem;
            }
            .quote-card .label {
                font-size: 0.76rem;
            }
            .quote-card .value {
                font-size: 0.96rem;
            }
            div[data-testid="stHorizontalBlock"] {
                gap: 0.55rem;
            }
            div[data-testid="stTabs"] div[role="tablist"] {
                overflow-x: auto;
                white-space: nowrap;
                flex-wrap: nowrap;
                scrollbar-width: none;
            }
            div[data-testid="stTabs"] div[role="tablist"]::-webkit-scrollbar {
                display: none;
            }
            div[data-testid="stTabs"] button[role="tab"] {
                flex: 0 0 auto;
                padding-left: 0.45rem;
                padding-right: 0.45rem;
            }
            div[data-testid="stSidebar"] {
                min-width: min(92vw, 21rem) !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (dict, list, tuple, pd.Series, pd.DataFrame)):
        return False
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def clean_float(value: Any) -> float | None:
    if is_missing(value):
        return None
    if isinstance(value, str):
        cleaned = (
            value.replace(",", "")
            .replace("%", "")
            .replace("$", "")
            .replace("USD", "")
            .strip()
        )
        if cleaned in {"", "-", "N/A", "None", "nan"}:
            return None
        value = cleaned
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(numeric) or math.isinf(numeric):
        return None
    return numeric


def first_valid(*values: Any) -> Any:
    for value in values:
        if not is_missing(value):
            return value
    return None


def safe_divide(numerator: Any, denominator: Any) -> float | None:
    top = clean_float(numerator)
    bottom = clean_float(denominator)
    if top is None or bottom in (None, 0):
        return None
    return top / bottom


def parse_compact_number(value: Any) -> float | None:
    if is_missing(value):
        return None
    if not isinstance(value, str):
        return clean_float(value)
    text = value.strip().upper().replace(",", "").replace("$", "")
    match = re.match(r"^([-+]?\d+(?:\.\d+)?)\s*([TMBK])?$", text)
    if not match:
        return clean_float(text)
    number = float(match.group(1))
    multiplier = {"T": 1e12, "B": 1e9, "M": 1e6, "K": 1e3}.get(match.group(2), 1)
    return number * multiplier


def yahoo_value(value: Any) -> Any:
    if isinstance(value, dict):
        if "raw" in value:
            return value.get("raw")
        if "fmt" in value:
            compact = parse_compact_number(value.get("fmt"))
            return compact if compact is not None else value.get("fmt")
    return value


def merge_missing(base: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base or {})
    for key, value in fallback.items():
        if not is_missing(value) and is_missing(merged.get(key)):
            merged[key] = value
    return merged


def normalize_ticker(ticker: str) -> str:
    return ticker.strip().upper().replace(".", "-")


def display_ticker(ticker: str) -> str:
    return ticker.strip().upper().replace("-", ".")


def format_number(
    value: Any,
    *,
    compact: bool = False,
    suffix: str = "",
    precision: int = 2,
    na_text: str = "데이터 없음",
) -> str:
    number = clean_float(value)
    if number is None:
        return na_text

    if compact:
        abs_number = abs(number)
        for threshold, unit in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
            if abs_number >= threshold:
                return f"{number / threshold:,.{precision}f}{unit}{suffix}"
        if abs_number >= 100:
            return f"{number:,.0f}{suffix}"
        return f"{number:,.{precision}f}{suffix}"

    if abs(number) >= 1000:
        if float(number).is_integer():
            return f"{number:,.0f}{suffix}"
        return f"{number:,.2f}{suffix}"
    if float(number).is_integer():
        return f"{number:,.0f}{suffix}"
    return f"{number:,.{precision}f}{suffix}"


def format_market_cap(value: Any) -> str:
    return format_number(value, compact=True, suffix=" USD", precision=2, na_text="데이터 없음")


def format_price(value: Any, currency: str | None = "USD") -> str:
    number = clean_float(value)
    if number is None:
        return "데이터 없음"
    suffix = f" {currency}" if currency else ""
    return f"{number:,.2f}{suffix}"


def format_percent(
    value: Any,
    *,
    already_percent: bool = False,
    precision: int = 2,
    na_text: str = "데이터 없음",
) -> str:
    number = clean_float(value)
    if number is None:
        return na_text
    if not already_percent:
        number *= 100
    return f"{number:,.{precision}f}%"


def format_multiple(value: Any) -> str:
    number = clean_float(value)
    if number is None:
        return "계산 불가"
    return f"{number:,.2f}x"


def format_plain_ratio(value: Any) -> str:
    number = clean_float(value)
    if number is None:
        return "계산 불가"
    return f"{number:,.2f}"


def card_html(label: str, value: Any) -> str:
    safe_label = escape(str(label))
    safe_value = escape(str(value))
    return f"""
    <div class="info-card">
        <span class="label">{safe_label}</span>
        <span class="value">{safe_value}</span>
    </div>
    """


def quote_cards_html(items: Iterable[tuple[str, Any]]) -> str:
    cards = []
    for label, value in items:
        safe_label = escape(str(label))
        safe_value = escape(str(value))
        cards.append(
            f'<div class="quote-card"><span class="label">{safe_label}</span>'
            f'<span class="value">{safe_value}</span></div>'
        )
    return f"<div class=\"quote-card-grid\">{''.join(cards)}</div>"


def format_date_column(column: Any) -> str:
    try:
        return pd.to_datetime(column).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return str(column)


def sort_statement_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    try:
        sorted_columns = sorted(df.columns, key=lambda value: pd.to_datetime(value), reverse=True)
        return df.loc[:, sorted_columns]
    except (TypeError, ValueError):
        return df


@st.cache_resource(show_spinner=False)
def get_yahoo_session() -> tuple[requests.Session, str | None]:
    session = requests.Session()
    session.headers.update(YAHOO_HEADERS)
    crumb: str | None = None
    try:
        session.get("https://fc.yahoo.com", timeout=10)
        crumb_response = session.get("https://query1.finance.yahoo.com/v1/test/getcrumb", timeout=10)
        if crumb_response.ok:
            crumb = crumb_response.text.strip() or None
    except Exception:
        crumb = None
    return session, crumb


def yahoo_get_json(url: str, params: dict[str, Any] | None = None, *, use_crumb: bool = False) -> dict[str, Any]:
    session, crumb = get_yahoo_session()
    request_params = dict(params or {})
    if use_crumb and crumb:
        request_params["crumb"] = crumb
    response = session.get(url, params=request_params, timeout=20)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=30 * 60, show_spinner=False)
def get_yahoo_chart_payload(ticker: str, period: str, interval: str) -> dict[str, Any]:
    symbol = normalize_ticker(ticker)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"interval": interval, "events": "history", "includePrePost": "false"}
    if period == "max":
        # Yahoo's range=max endpoint can downsample every interval into sparse monthly/quarterly data.
        # period1/period2 preserves the selected candle interval for detailed chart navigation.
        params["period1"] = 0
        params["period2"] = int(time.time())
    else:
        params["range"] = period
    try:
        data = yahoo_get_json(url, params=params)
        result = data.get("chart", {}).get("result") or []
        return result[0] if result else {}
    except Exception:
        return {}


def yahoo_chart_to_dataframe(payload: dict[str, Any]) -> pd.DataFrame:
    timestamps = payload.get("timestamp") or []
    indicators = payload.get("indicators", {})
    quote_list = indicators.get("quote") or []
    if not timestamps or not quote_list:
        return pd.DataFrame()

    quote = quote_list[0]
    data = pd.DataFrame(
        {
            "Open": quote.get("open"),
            "High": quote.get("high"),
            "Low": quote.get("low"),
            "Close": quote.get("close"),
            "Volume": quote.get("volume"),
        }
    )
    adjclose = (indicators.get("adjclose") or [{}])[0].get("adjclose")
    if adjclose:
        data["Adj Close"] = adjclose

    index = pd.to_datetime(timestamps, unit="s", utc=True)
    timezone_name = payload.get("meta", {}).get("exchangeTimezoneName")
    if timezone_name:
        try:
            index = index.tz_convert(timezone_name)
        except Exception:
            pass
    data.index = index
    data = data.dropna(how="all")
    if "Close" in data.columns:
        data = data.dropna(subset=["Close"])
    return data


@st.cache_data(ttl=15 * 60, show_spinner=False)
def get_yahoo_price_data(ticker: str, period: str, interval: str) -> pd.DataFrame:
    return yahoo_chart_to_dataframe(get_yahoo_chart_payload(ticker, period, interval))


@st.cache_data(ttl=15 * 60, show_spinner=False)
def get_yahoo_quote_batch(symbols: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    cleaned_symbols = tuple(dict.fromkeys(normalize_ticker(symbol) for symbol in symbols if symbol))
    if not cleaned_symbols:
        return {}

    results: dict[str, dict[str, Any]] = {}
    chunk_size = 80
    url = "https://query1.finance.yahoo.com/v7/finance/quote"
    for start in range(0, len(cleaned_symbols), chunk_size):
        chunk = cleaned_symbols[start : start + chunk_size]
        try:
            data = yahoo_get_json(url, {"symbols": ",".join(chunk)}, use_crumb=True)
            for item in data.get("quoteResponse", {}).get("result", []):
                symbol = normalize_ticker(str(item.get("symbol", "")))
                if symbol:
                    results[symbol] = item
        except Exception:
            continue
    return results


def get_yahoo_quote_snapshot(symbol: str) -> dict[str, Any]:
    return get_yahoo_quote_batch((normalize_ticker(symbol),)).get(normalize_ticker(symbol), {})


@st.cache_data(ttl=5, show_spinner=False)
def get_live_quote_info(ticker: str, refresh_bucket: int = 0) -> dict[str, Any]:
    symbol = normalize_ticker(ticker)
    url = "https://query1.finance.yahoo.com/v7/finance/quote"
    try:
        data = yahoo_get_json(url, {"symbols": symbol}, use_crumb=True)
        result = data.get("quoteResponse", {}).get("result") or []
        quote = result[0] if result else {}
    except Exception:
        quote = {}

    if not quote:
        return {}
    return {
        "currentPrice": quote.get("regularMarketPrice"),
        "regularMarketPrice": quote.get("regularMarketPrice"),
        "previousClose": quote.get("regularMarketPreviousClose"),
        "regularMarketPreviousClose": quote.get("regularMarketPreviousClose"),
        "marketCap": quote.get("marketCap"),
        "fiftyTwoWeekHigh": quote.get("fiftyTwoWeekHigh"),
        "fiftyTwoWeekLow": quote.get("fiftyTwoWeekLow"),
        "volume": quote.get("regularMarketVolume"),
        "regularMarketVolume": quote.get("regularMarketVolume"),
        "currency": quote.get("currency"),
        "financialCurrency": quote.get("financialCurrency"),
    }


@st.cache_data(ttl=60 * 60, show_spinner=False)
def get_yahoo_quote_summary(ticker: str, modules: str = YAHOO_INFO_MODULES) -> dict[str, Any]:
    symbol = normalize_ticker(ticker)
    url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
    try:
        data = yahoo_get_json(url, {"modules": modules}, use_crumb=True)
        result = data.get("quoteSummary", {}).get("result") or []
        return result[0] if result else {}
    except Exception:
        return {}


def flatten_yahoo_summary_info(ticker: str) -> dict[str, Any]:
    symbol = normalize_ticker(ticker)
    quote = get_yahoo_quote_snapshot(symbol)
    summary = get_yahoo_quote_summary(symbol)
    price = summary.get("price", {})
    details = summary.get("summaryDetail", {})
    stats = summary.get("defaultKeyStatistics", {})
    financial = summary.get("financialData", {})
    profile = summary.get("assetProfile", {})

    info: dict[str, Any] = {
        "symbol": first_valid(quote.get("symbol"), yahoo_value(price.get("symbol")), display_ticker(symbol)),
        "longName": first_valid(quote.get("longName"), yahoo_value(price.get("longName"))),
        "shortName": first_valid(quote.get("shortName"), quote.get("displayName"), yahoo_value(price.get("shortName"))),
        "exchange": first_valid(quote.get("exchange"), yahoo_value(price.get("exchangeName"))),
        "fullExchangeName": first_valid(quote.get("fullExchangeName"), yahoo_value(price.get("exchangeName"))),
        "currency": first_valid(quote.get("currency"), yahoo_value(price.get("currency"))),
        "financialCurrency": first_valid(quote.get("financialCurrency"), yahoo_value(price.get("currency"))),
        "currentPrice": first_valid(quote.get("regularMarketPrice"), yahoo_value(price.get("regularMarketPrice"))),
        "regularMarketPrice": first_valid(quote.get("regularMarketPrice"), yahoo_value(price.get("regularMarketPrice"))),
        "previousClose": first_valid(quote.get("regularMarketPreviousClose"), yahoo_value(details.get("previousClose"))),
        "regularMarketPreviousClose": quote.get("regularMarketPreviousClose"),
        "marketCap": first_valid(quote.get("marketCap"), yahoo_value(price.get("marketCap"))),
        "fiftyTwoWeekHigh": first_valid(quote.get("fiftyTwoWeekHigh"), yahoo_value(details.get("fiftyTwoWeekHigh"))),
        "fiftyTwoWeekLow": first_valid(quote.get("fiftyTwoWeekLow"), yahoo_value(details.get("fiftyTwoWeekLow"))),
        "volume": first_valid(quote.get("regularMarketVolume"), yahoo_value(details.get("volume"))),
        "regularMarketVolume": quote.get("regularMarketVolume"),
        "beta": first_valid(quote.get("beta"), yahoo_value(details.get("beta"))),
        "dividendYield": first_valid(quote.get("dividendYield"), yahoo_value(details.get("dividendYield"))),
        "dividendRate": first_valid(quote.get("dividendRate"), yahoo_value(details.get("dividendRate"))),
        "trailingPE": first_valid(quote.get("trailingPE"), yahoo_value(details.get("trailingPE"))),
        "forwardPE": first_valid(quote.get("forwardPE"), yahoo_value(stats.get("forwardPE"))),
        "priceToBook": first_valid(quote.get("priceToBook"), yahoo_value(stats.get("priceToBook"))),
        "enterpriseValue": yahoo_value(stats.get("enterpriseValue")),
        "enterpriseToEbitda": yahoo_value(stats.get("enterpriseToEbitda")),
        "pegRatio": first_valid(yahoo_value(stats.get("pegRatio")), yahoo_value(stats.get("trailingPegRatio"))),
        "trailingPegRatio": yahoo_value(stats.get("trailingPegRatio")),
        "trailingEps": first_valid(quote.get("epsTrailingTwelveMonths"), yahoo_value(stats.get("trailingEps"))),
        "forwardEps": first_valid(quote.get("epsForward"), yahoo_value(stats.get("forwardEps"))),
        "sharesOutstanding": first_valid(quote.get("sharesOutstanding"), yahoo_value(stats.get("sharesOutstanding"))),
        "returnOnEquity": yahoo_value(financial.get("returnOnEquity")),
        "returnOnAssets": yahoo_value(financial.get("returnOnAssets")),
        "grossMargins": yahoo_value(financial.get("grossMargins")),
        "operatingMargins": yahoo_value(financial.get("operatingMargins")),
        "profitMargins": yahoo_value(financial.get("profitMargins")),
        "totalDebt": yahoo_value(financial.get("totalDebt")),
        "currentRatio": yahoo_value(financial.get("currentRatio")),
        "freeCashflow": yahoo_value(financial.get("freeCashflow")),
        "ebitda": yahoo_value(financial.get("ebitda")),
        "debtToEquity": yahoo_value(financial.get("debtToEquity")),
        "sector": profile.get("sector"),
        "industry": profile.get("industry"),
        "country": profile.get("country"),
        "website": profile.get("website"),
        "fullTimeEmployees": profile.get("fullTimeEmployees"),
        "longBusinessSummary": profile.get("longBusinessSummary"),
        "companyOfficers": profile.get("companyOfficers"),
    }

    chart_meta = (get_yahoo_chart_payload(symbol, "5d", "1d") or {}).get("meta", {})
    info = merge_missing(
        info,
        {
            "currency": chart_meta.get("currency"),
            "exchange": chart_meta.get("exchangeName"),
            "currentPrice": chart_meta.get("regularMarketPrice"),
            "previousClose": chart_meta.get("chartPreviousClose"),
        },
    )
    return {key: value for key, value in info.items() if not is_missing(value)}


def get_fast_value(fast_info: Any, keys: Iterable[str]) -> Any:
    if fast_info is None:
        return None
    for key in keys:
        try:
            if hasattr(fast_info, "get"):
                value = fast_info.get(key)
            else:
                value = getattr(fast_info, key)
            if not is_missing(value):
                return value
        except Exception:
            continue
    return None


def get_info_value(info: dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        value = info.get(key)
        if not is_missing(value):
            return value
    return None


@st.cache_data(ttl=60 * 60, show_spinner=False)
def get_stock_info(ticker: str) -> dict[str, Any]:
    symbol = normalize_ticker(ticker)
    stock = yf.Ticker(symbol)
    info: dict[str, Any] = {}

    try:
        info = stock.get_info()
    except Exception:
        try:
            info = stock.info or {}
        except Exception as exc:
            info = {"__error__": str(exc)}

    try:
        fast_info = stock.fast_info
    except Exception:
        fast_info = None

    fast_key_map = {
        "fast_last_price": ("last_price", "lastPrice"),
        "fast_previous_close": ("previous_close", "previousClose", "regularMarketPreviousClose"),
        "fast_market_cap": ("market_cap", "marketCap"),
        "fast_year_high": ("year_high", "yearHigh"),
        "fast_year_low": ("year_low", "yearLow"),
        "fast_volume": ("last_volume", "lastVolume"),
        "fast_currency": ("currency",),
    }
    for output_key, lookup_keys in fast_key_map.items():
        info[output_key] = get_fast_value(fast_info, lookup_keys)

    info = merge_missing(info, flatten_yahoo_summary_info(symbol))
    info["input_ticker"] = ticker.strip().upper()
    info["yf_symbol"] = symbol
    return info


@st.cache_data(ttl=15 * 60, show_spinner=False)
def get_price_data(ticker: str, period: str, interval: str) -> pd.DataFrame:
    symbol = normalize_ticker(ticker)
    data = get_yahoo_price_data(symbol, period, interval)
    if not data.empty:
        return data

    stock = yf.Ticker(symbol)
    try:
        data = stock.history(period=period, interval=interval, auto_adjust=False, actions=False)
    except Exception:
        data = pd.DataFrame()

    if data.empty:
        try:
            data = yf.download(
                symbol,
                period=period,
                interval=interval,
                auto_adjust=False,
                progress=False,
                threads=False,
            )
        except Exception:
            data = pd.DataFrame()

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    if data.empty:
        return pd.DataFrame()

    data = data.copy()
    data.index = pd.to_datetime(data.index)
    data = data.dropna(how="all")
    if "Close" in data.columns:
        data = data.dropna(subset=["Close"])
    return data


def calculate_rsi(price_data: pd.DataFrame | pd.Series, period: int = 14) -> pd.Series:
    close = price_data["Close"] if isinstance(price_data, pd.DataFrame) else price_data
    close = pd.to_numeric(close, errors="coerce")
    if close.empty or period <= 0:
        return pd.Series(dtype=float)

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    average_gain = gain.rolling(window=period, min_periods=period).mean()
    average_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = average_gain / average_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.where(~((average_loss == 0) & (average_gain > 0)), 100)
    rsi = rsi.where(~((average_gain == 0) & (average_loss > 0)), 0)
    return rsi


def calculate_moving_average(price_data: pd.DataFrame, window: int) -> pd.Series:
    if price_data.empty or "Close" not in price_data.columns or window <= 0:
        return pd.Series(dtype=float)
    return pd.to_numeric(price_data["Close"], errors="coerce").rolling(window=window).mean()


def build_price_summary(info: dict[str, Any], price_data: pd.DataFrame) -> dict[str, Any]:
    currency = first_valid(
        info.get("currency"),
        info.get("financialCurrency"),
        info.get("fast_currency"),
        "USD",
    )

    close = price_data["Close"].dropna() if "Close" in price_data.columns else pd.Series(dtype=float)
    volume = price_data["Volume"].dropna() if "Volume" in price_data.columns else pd.Series(dtype=float)

    latest_close = close.iloc[-1] if len(close) else None
    previous_close_from_chart = close.iloc[-2] if len(close) >= 2 else None
    latest_volume = volume.iloc[-1] if len(volume) else None

    current_price = first_valid(
        info.get("currentPrice"),
        info.get("regularMarketPrice"),
        info.get("fast_last_price"),
        latest_close,
    )
    previous_close = first_valid(
        info.get("previousClose"),
        info.get("regularMarketPreviousClose"),
        info.get("fast_previous_close"),
        previous_close_from_chart,
    )
    change_pct = safe_divide(
        clean_float(current_price) - clean_float(previous_close)
        if clean_float(current_price) is not None and clean_float(previous_close) is not None
        else None,
        previous_close,
    )
    if change_pct is not None:
        change_pct *= 100

    return {
        "currency": currency,
        "current_price": current_price,
        "change_pct": change_pct,
        "year_high": first_valid(info.get("fiftyTwoWeekHigh"), info.get("fast_year_high")),
        "year_low": first_valid(info.get("fiftyTwoWeekLow"), info.get("fast_year_low")),
        "volume": first_valid(info.get("volume"), info.get("regularMarketVolume"), info.get("fast_volume"), latest_volume),
        "market_cap": first_valid(info.get("marketCap"), info.get("fast_market_cap")),
    }


def render_price_summary_cards(ticker: str, info: dict[str, Any], price_data: pd.DataFrame, settings: dict[str, Any]) -> None:
    def draw_cards(latest_info: dict[str, Any]) -> None:
        summary = build_price_summary(latest_info, price_data)
        st.markdown(
            quote_cards_html(
                [
                    ("현재가", format_price(summary["current_price"], summary["currency"])),
                    ("전일 대비 등락률", format_percent(summary["change_pct"], already_percent=True)),
                    ("52주 최고가", format_price(summary["year_high"], summary["currency"])),
                    ("52주 최저가", format_price(summary["year_low"], summary["currency"])),
                    ("거래량", format_number(summary["volume"], compact=True)),
                ]
            ),
            unsafe_allow_html=True,
        )

    refresh_seconds = int(settings.get("auto_refresh_seconds", 0) or 0)
    if refresh_seconds <= 0:
        draw_cards(info)
        return

    @st.fragment(run_every=f"{refresh_seconds}s")
    def quote_cards_fragment() -> None:
        live_bucket = int(time.time() // refresh_seconds)
        live_info = merge_missing(get_live_quote_info(ticker, live_bucket), info)
        draw_cards(live_info)

    quote_cards_fragment()


def read_statement_from_attrs(stock: yf.Ticker, attrs: Iterable[str]) -> pd.DataFrame:
    for attr in attrs:
        try:
            data = getattr(stock, attr)
            if isinstance(data, pd.DataFrame) and not data.empty:
                return data
        except Exception:
            continue
    return pd.DataFrame()


@st.cache_data(ttl=24 * 60 * 60, show_spinner=False)
def get_sec_company_tickers() -> pd.DataFrame:
    try:
        response = requests.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers=SEC_HEADERS,
            timeout=20,
        )
        response.raise_for_status()
        records = list(response.json().values())
        df = pd.DataFrame(records)
        if df.empty:
            return pd.DataFrame()
        df["ticker"] = df["ticker"].astype(str).str.upper()
        df["cik_str"] = df["cik_str"].astype(int).astype(str).str.zfill(10)
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=24 * 60 * 60, show_spinner=False)
def get_sec_company_facts(ticker: str) -> dict[str, Any]:
    tickers = get_sec_company_tickers()
    symbol = display_ticker(ticker).upper()
    if tickers.empty or symbol not in set(tickers["ticker"]):
        return {}

    cik = tickers.loc[tickers["ticker"] == symbol, "cik_str"].iloc[0]
    try:
        response = requests.get(
            f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
            headers=SEC_HEADERS,
            timeout=25,
        )
        response.raise_for_status()
        return response.json()
    except Exception:
        return {}


def get_sec_fact_entries(facts: dict[str, Any], tags: list[str], period_type: str) -> list[dict[str, Any]]:
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    annual_forms = {"10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A"}
    quarterly_forms = {"10-Q", "10-Q/A"}

    for tag in tags:
        units = us_gaap.get(tag, {}).get("units", {})
        entries = units.get("USD") or units.get("usd") or []
        if not entries:
            continue

        filtered: list[dict[str, Any]] = []
        for entry in entries:
            form = str(entry.get("form", "")).upper()
            fp = str(entry.get("fp", "")).upper()
            value = clean_float(entry.get("val"))
            if value is None or not entry.get("end"):
                continue
            if period_type == "annual":
                if form in annual_forms and fp == "FY":
                    filtered.append(entry)
            elif form in quarterly_forms and fp.startswith("Q"):
                filtered.append(entry)

        if period_type == "quarterly":
            framed = [
                entry
                for entry in filtered
                if re.search(r"CY\d{4}Q[1-4]I?$", str(entry.get("frame", "")))
            ]
            if framed:
                filtered = framed

        if filtered:
            return filtered
    return []


def sec_entries_to_series(entries: list[dict[str, Any]], *, cash_outflow: bool = False, limit: int = 8) -> pd.Series:
    if not entries:
        return pd.Series(dtype=float)

    sorted_entries = sorted(
        entries,
        key=lambda item: (str(item.get("end", "")), str(item.get("filed", ""))),
        reverse=True,
    )
    values: dict[pd.Timestamp, float] = {}
    for entry in sorted_entries:
        try:
            end_date = pd.to_datetime(entry.get("end"))
        except Exception:
            continue
        if end_date in values:
            continue
        value = clean_float(entry.get("val"))
        if value is None:
            continue
        values[end_date] = -abs(value) if cash_outflow else value
        if len(values) >= limit:
            break

    if not values:
        return pd.Series(dtype=float)
    return pd.Series(values).sort_index(ascending=False)


def build_sec_statement(facts: dict[str, Any], rows: list[str], period_type: str) -> pd.DataFrame:
    if not facts:
        return pd.DataFrame()

    limit = 8 if period_type == "quarterly" else 5
    series_by_row: dict[str, pd.Series] = {}
    for row in rows:
        entries = get_sec_fact_entries(facts, SEC_FACT_TAGS.get(row, []), period_type)
        series_by_row[row] = sec_entries_to_series(
            entries,
            cash_outflow=row == "Capital Expenditure",
            limit=limit,
        )

    df = pd.DataFrame(series_by_row).T
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    if df.empty:
        return pd.DataFrame()

    if "Operating Cash Flow" in df.index and "Capital Expenditure" in df.index:
        df.loc["Free Cash Flow"] = df.loc["Operating Cash Flow"].add(
            df.loc["Capital Expenditure"],
            fill_value=np.nan,
        )
    return sort_statement_columns(df)


@st.cache_data(ttl=6 * 60 * 60, show_spinner=False)
def get_sec_financial_statements(ticker: str, period_type: str = "annual") -> dict[str, pd.DataFrame]:
    facts = get_sec_company_facts(ticker)
    if not facts:
        return {"income": pd.DataFrame(), "balance": pd.DataFrame(), "cashflow": pd.DataFrame()}

    return {
        "income": build_sec_statement(
            facts,
            ["Total Revenue", "Gross Profit", "Operating Income", "Net Income"],
            period_type,
        ),
        "balance": build_sec_statement(
            facts,
            ["Total Assets", "Total Liabilities Net Minority Interest", "Stockholders Equity"],
            period_type,
        ),
        "cashflow": build_sec_statement(
            facts,
            ["Operating Cash Flow", "Capital Expenditure"],
            period_type,
        ),
    }


@st.cache_data(ttl=60 * 60, show_spinner=False)
def get_financial_statements(ticker: str, period_type: str = "annual") -> dict[str, pd.DataFrame]:
    symbol = normalize_ticker(ticker)
    stock = yf.Ticker(symbol)

    if period_type == "quarterly":
        income_attrs = ("quarterly_income_stmt", "quarterly_financials")
        balance_attrs = ("quarterly_balance_sheet",)
        cashflow_attrs = ("quarterly_cashflow", "quarterly_cash_flow")
    else:
        income_attrs = ("income_stmt", "financials")
        balance_attrs = ("balance_sheet",)
        cashflow_attrs = ("cashflow", "cash_flow")

    statements = {
        "income": read_statement_from_attrs(stock, income_attrs),
        "balance": read_statement_from_attrs(stock, balance_attrs),
        "cashflow": read_statement_from_attrs(stock, cashflow_attrs),
    }

    cleaned: dict[str, pd.DataFrame] = {}
    for name, df in statements.items():
        if df.empty:
            cleaned[name] = pd.DataFrame()
            continue
        fixed = df.copy()
        fixed.index = fixed.index.map(str)
        fixed = fixed[~fixed.index.duplicated(keep="first")]
        fixed = fixed.dropna(axis=1, how="all")
        cleaned[name] = sort_statement_columns(fixed)

    sec_fallback = get_sec_financial_statements(symbol, period_type)
    for name, fallback_df in sec_fallback.items():
        if cleaned.get(name, pd.DataFrame()).empty and not fallback_df.empty:
            cleaned[name] = fallback_df
    return cleaned


def prepare_financial_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    display_df = df.copy()
    display_df.index = [FINANCIAL_NAME_KO.get(str(idx), str(idx)) for idx in display_df.index]
    display_df.columns = [format_date_column(col) for col in display_df.columns]
    for column in display_df.columns:
        display_df[column] = display_df[column].map(
            lambda value: format_number(value, compact=True, precision=2, na_text="데이터 없음")
        )
    display_df.insert(0, "항목", display_df.index)
    return display_df.reset_index(drop=True)


def get_statement_value(df: pd.DataFrame, possible_names: Iterable[str], column_position: int = 0) -> Any:
    if df.empty or len(df.columns) <= column_position:
        return None
    for name in possible_names:
        if name not in df.index:
            continue
        value = df.loc[name]
        if isinstance(value, pd.DataFrame):
            value = value.iloc[0]
        try:
            candidate = value.iloc[column_position]
        except Exception:
            candidate = None
        if not is_missing(candidate):
            return candidate
    return None


def calculate_statement_growth(
    df: pd.DataFrame,
    possible_names: Iterable[str],
    period_type: str,
) -> tuple[float | None, str]:
    if period_type == "quarterly" and len(df.columns) >= 5:
        compare_position = 4
        label = "전년 동기 대비"
    else:
        compare_position = 1
        label = "전년 대비" if period_type == "annual" else "이전 기간 대비"

    latest = get_statement_value(df, possible_names, 0)
    previous = get_statement_value(df, possible_names, compare_position)
    growth = safe_divide(
        clean_float(latest) - clean_float(previous)
        if clean_float(latest) is not None and clean_float(previous) is not None
        else None,
        abs(clean_float(previous)) if clean_float(previous) is not None else None,
    )
    return growth, label


def get_valuation_metrics(ticker: str) -> list[dict[str, str]]:
    info = get_stock_info(ticker)
    statements = get_financial_statements(ticker, "annual")
    income = statements.get("income", pd.DataFrame())
    balance = statements.get("balance", pd.DataFrame())
    cashflow = statements.get("cashflow", pd.DataFrame())

    market_cap = first_valid(info.get("marketCap"), info.get("fast_market_cap"))
    current_price = first_valid(info.get("currentPrice"), info.get("regularMarketPrice"), info.get("fast_last_price"))
    revenue = get_statement_value(income, ("Total Revenue",))
    gross_profit = get_statement_value(income, ("Gross Profit",))
    operating_income = get_statement_value(income, ("Operating Income",))
    net_income = get_statement_value(income, ("Net Income",))
    total_assets = get_statement_value(balance, ("Total Assets",))
    equity = get_statement_value(balance, ("Stockholders Equity", "Total Stockholder Equity"))
    total_debt = first_valid(info.get("totalDebt"), get_statement_value(balance, ("Total Debt",)))
    current_assets = get_statement_value(balance, ("Current Assets", "Total Current Assets"))
    current_liabilities = get_statement_value(balance, ("Current Liabilities", "Total Current Liabilities"))
    operating_cash_flow = get_statement_value(cashflow, ("Operating Cash Flow",))
    capex = get_statement_value(cashflow, ("Capital Expenditure",))
    fcf_from_statement = first_valid(
        get_statement_value(cashflow, ("Free Cash Flow",)),
        clean_float(operating_cash_flow) + clean_float(capex)
        if clean_float(operating_cash_flow) is not None and clean_float(capex) is not None
        else None,
    )
    free_cash_flow = first_valid(info.get("freeCashflow"), fcf_from_statement)
    ebitda = first_valid(info.get("ebitda"), get_statement_value(income, ("EBITDA",)))
    enterprise_value = info.get("enterpriseValue")

    trailing_pe = first_valid(
        info.get("trailingPE"),
        safe_divide(current_price, info.get("trailingEps")),
    )
    forward_pe = first_valid(
        info.get("forwardPE"),
        safe_divide(current_price, info.get("forwardEps")),
    )
    pbr = first_valid(info.get("priceToBook"), safe_divide(market_cap, equity))
    psr = first_valid(info.get("priceToSalesTrailing12Months"), safe_divide(market_cap, revenue))
    ev_to_ebitda = first_valid(info.get("enterpriseToEbitda"), safe_divide(enterprise_value, ebitda))
    peg = first_valid(info.get("pegRatio"), info.get("trailingPegRatio"))
    roe = first_valid(info.get("returnOnEquity"), safe_divide(net_income, equity))
    roa = first_valid(info.get("returnOnAssets"), safe_divide(net_income, total_assets))
    gross_margin = first_valid(info.get("grossMargins"), safe_divide(gross_profit, revenue))
    operating_margin = first_valid(info.get("operatingMargins"), safe_divide(operating_income, revenue))
    net_margin = first_valid(info.get("profitMargins"), safe_divide(net_income, revenue))
    debt_to_equity = safe_divide(total_debt, equity)
    if debt_to_equity is None:
        raw_debt_to_equity = clean_float(info.get("debtToEquity"))
        debt_to_equity = raw_debt_to_equity / 100 if raw_debt_to_equity is not None else None
    current_ratio = first_valid(info.get("currentRatio"), safe_divide(current_assets, current_liabilities))
    fcf_yield = safe_divide(free_cash_flow, market_cap)
    dividend_yield = info.get("dividendYield")

    metric_specs = [
        ("PER", trailing_pe, "multiple"),
        ("Forward PER", forward_pe, "multiple"),
        ("PBR", pbr, "multiple"),
        ("PSR", psr, "multiple"),
        ("EV/EBITDA", ev_to_ebitda, "multiple"),
        ("PEG Ratio", peg, "plain"),
        ("ROE", roe, "percent"),
        ("ROA", roa, "percent"),
        ("Gross Margin", gross_margin, "percent"),
        ("Operating Margin", operating_margin, "percent"),
        ("Net Margin", net_margin, "percent"),
        ("Debt to Equity", debt_to_equity, "multiple"),
        ("Current Ratio", current_ratio, "multiple"),
        ("Free Cash Flow Yield", fcf_yield, "percent"),
        ("배당수익률", dividend_yield, "percent"),
    ]

    rows: list[dict[str, str]] = []
    for metric, raw_value, format_type in metric_specs:
        if format_type == "percent":
            formatted = format_percent(raw_value, na_text="계산 불가")
        elif format_type == "multiple":
            formatted = format_multiple(raw_value)
        else:
            formatted = format_plain_ratio(raw_value)
        rows.append(
            {
                "지표": metric,
                "값": formatted,
                "해석": VALUATION_INTERPRETATIONS[metric],
            }
        )
    return rows


def get_major_ticker_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Symbol": MAJOR_US_LISTED_TICKERS,
            "YFinanceSymbol": MAJOR_US_LISTED_TICKERS,
            "Security": "",
            "GICS Sector": [MAJOR_TICKER_SECTORS.get(symbol, "") for symbol in MAJOR_US_LISTED_TICKERS],
            "Source": "Major US-listed list",
        }
    )


@st.cache_data(ttl=24 * 60 * 60, show_spinner=False)
def get_sp500_tickers() -> pd.DataFrame:
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; streamlit-stock-research/1.0)"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", {"id": "constituents"})
        if table is None:
            raise ValueError("S&P 500 constituents table not found")

        rows = []
        for tr in table.find_all("tr")[1:]:
            cells = [cell.get_text(strip=True) for cell in tr.find_all(["td", "th"])]
            if len(cells) < 4:
                continue
            symbol = cells[0].replace(".", "-")
            rows.append(
                {
                    "Symbol": cells[0],
                    "YFinanceSymbol": symbol,
                    "Security": cells[1],
                    "GICS Sector": cells[2],
                    "Source": "Wikipedia S&P 500",
                }
            )
        if rows:
            return pd.DataFrame(rows)
    except Exception:
        pass
    return get_major_ticker_frame().assign(Source="Fallback major list")


@st.cache_data(ttl=6 * 60 * 60, show_spinner=False)
def fetch_market_snapshot(symbol: str, need_profile: bool = False) -> dict[str, Any]:
    quote = get_yahoo_quote_snapshot(symbol)
    snapshot: dict[str, Any] = {
        "market_cap": quote.get("marketCap"),
        "current_price": quote.get("regularMarketPrice"),
        "previous_close": quote.get("regularMarketPreviousClose"),
        "name": first_valid(quote.get("longName"), quote.get("shortName"), quote.get("displayName"), ""),
        "sector": "",
    }

    if not need_profile and all(
        not is_missing(snapshot.get(key)) for key in ("market_cap", "current_price", "previous_close")
    ):
        return snapshot

    stock = yf.Ticker(symbol)

    try:
        fast_info = stock.fast_info
    except Exception:
        fast_info = None

    snapshot["market_cap"] = first_valid(
        snapshot.get("market_cap"),
        get_fast_value(fast_info, ("market_cap", "marketCap")),
    )
    snapshot["current_price"] = first_valid(
        snapshot.get("current_price"),
        get_fast_value(fast_info, ("last_price", "lastPrice")),
    )
    snapshot["previous_close"] = first_valid(
        snapshot.get("previous_close"),
        get_fast_value(fast_info, ("previous_close", "previousClose", "regularMarketPreviousClose")),
    )

    needs_info = need_profile or any(
        is_missing(snapshot.get(key)) for key in ("market_cap", "current_price", "previous_close")
    )
    if needs_info:
        try:
            info = stock.get_info()
        except Exception:
            try:
                info = stock.info or {}
            except Exception:
                info = {}
        snapshot["market_cap"] = first_valid(snapshot.get("market_cap"), info.get("marketCap"))
        snapshot["current_price"] = first_valid(
            snapshot.get("current_price"),
            info.get("currentPrice"),
            info.get("regularMarketPrice"),
        )
        snapshot["previous_close"] = first_valid(
            snapshot.get("previous_close"),
            info.get("previousClose"),
            info.get("regularMarketPreviousClose"),
        )
        snapshot["name"] = first_valid(info.get("longName"), info.get("shortName"), "")
        snapshot["sector"] = first_valid(info.get("sector"), "")
    return snapshot


@st.cache_data(ttl=6 * 60 * 60, show_spinner=False)
def get_market_cap_ranking(source: str = "major") -> pd.DataFrame:
    constituents = get_sp500_tickers() if source == "sp500" else get_major_ticker_frame()
    sector_lookup = {
        normalize_ticker(str(row["Symbol"])): row.get("GICS Sector")
        for _, row in constituents.iterrows()
        if not is_missing(row.get("GICS Sector"))
    }
    sector_lookup.update(MAJOR_TICKER_SECTORS)
    yf_symbols = tuple(str(value).replace(".", "-") for value in constituents.get("YFinanceSymbol", constituents["Symbol"]))
    quote_batch = get_yahoo_quote_batch(tuple(normalize_ticker(symbol) for symbol in yf_symbols))
    rows: list[dict[str, Any]] = []

    for _, item in constituents.iterrows():
        symbol = str(item["Symbol"])
        yf_symbol = str(item.get("YFinanceSymbol", symbol)).replace(".", "-")
        quote = quote_batch.get(normalize_ticker(yf_symbol), {})
        snapshot = {
            "market_cap": quote.get("marketCap"),
            "current_price": quote.get("regularMarketPrice"),
            "previous_close": quote.get("regularMarketPreviousClose"),
            "name": first_valid(quote.get("longName"), quote.get("shortName"), quote.get("displayName")),
            "sector": "",
        }
        if any(is_missing(snapshot.get(key)) for key in ("market_cap", "current_price", "previous_close")):
            snapshot = merge_missing(snapshot, fetch_market_snapshot(yf_symbol, need_profile=False))
        market_cap = clean_float(snapshot.get("market_cap"))
        if market_cap is None:
            continue
        current_price = clean_float(snapshot.get("current_price"))
        previous_close = clean_float(snapshot.get("previous_close"))
        change_pct = None
        if current_price is not None and previous_close not in (None, 0):
            change_pct = ((current_price - previous_close) / previous_close) * 100

        rows.append(
            {
                "ticker": display_ticker(symbol),
                "yf_symbol": yf_symbol,
                "name": first_valid(item.get("Security"), snapshot.get("name"), "확인 불가"),
                "sector": first_valid(
                    item.get("GICS Sector"),
                    sector_lookup.get(normalize_ticker(symbol)),
                    sector_lookup.get(normalize_ticker(yf_symbol)),
                    snapshot.get("sector"),
                    "확인 불가",
                ),
                "market_cap": market_cap,
                "current_price": current_price,
                "change_pct": change_pct,
                "source": item.get("Source", ""),
            }
        )

    if not rows:
        return pd.DataFrame()

    ranking = pd.DataFrame(rows).sort_values("market_cap", ascending=False).reset_index(drop=True)
    ranking.insert(0, "rank", np.arange(1, len(ranking) + 1))
    return ranking


def init_moving_average_state() -> None:
    if "ma_items" not in st.session_state:
        st.session_state.ma_items = [
            {"id": 1, "enabled": True, "window": 20},
            {"id": 2, "enabled": True, "window": 60},
            {"id": 3, "enabled": True, "window": 120},
        ]
    if "ma_next_id" not in st.session_state:
        st.session_state.ma_next_id = 4


def render_moving_average_controls() -> list[dict[str, Any]]:
    init_moving_average_state()

    add_col, reset_col = st.columns(2)
    if add_col.button("이동평균선 추가", use_container_width=True):
        current_windows = [int(item.get("window", 20)) for item in st.session_state.ma_items]
        next_window = min(max((current_windows[-1] + 20) if current_windows else 20, 2), 300)
        st.session_state.ma_items.append(
            {
                "id": st.session_state.ma_next_id,
                "enabled": True,
                "window": next_window,
            }
        )
        st.session_state.ma_next_id += 1
        st.rerun()

    if reset_col.button("기본값 복원", use_container_width=True):
        st.session_state.ma_items = [
            {"id": 1, "enabled": True, "window": 20},
            {"id": 2, "enabled": True, "window": 60},
            {"id": 3, "enabled": True, "window": 120},
        ]
        st.session_state.ma_next_id = 4
        st.rerun()

    ma_settings: list[dict[str, Any]] = []
    if not st.session_state.ma_items:
        st.caption("표시할 이동평균선이 없습니다. 추가 버튼으로 새 선을 만들 수 있습니다.")
        return ma_settings

    for idx, item in enumerate(list(st.session_state.ma_items), start=1):
        item_id = int(item["id"])
        enabled_key = f"ma_enabled_dynamic_{item_id}"
        window_key = f"ma_window_dynamic_{item_id}"
        cols = st.columns([0.95, 1.25, 0.72])
        enabled = cols[0].checkbox(f"MA {idx}", value=bool(item.get("enabled", True)), key=enabled_key)
        window = cols[1].number_input(
            "기간",
            min_value=2,
            max_value=300,
            value=int(item.get("window", 20)),
            step=1,
            key=window_key,
            label_visibility="collapsed",
        )
        if cols[2].button("삭제", key=f"ma_remove_{item_id}", use_container_width=True):
            st.session_state.ma_items = [
                ma_item for ma_item in st.session_state.ma_items if int(ma_item["id"]) != item_id
            ]
            st.rerun()

        item["enabled"] = enabled
        item["window"] = int(window)
        ma_settings.append({"enabled": enabled, "window": int(window)})

    return ma_settings


def render_sidebar() -> dict[str, Any]:
    with st.sidebar:
        st.header("분석 설정")
        ticker = st.text_input("티커 입력", value="AAPL", placeholder="예: AAPL, MSFT, NVDA, TSM")
        if st.button("데이터 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.rerun()

        auto_refresh_label = st.selectbox(
            "자동 새로고침",
            list(AUTO_REFRESH_OPTIONS.keys()),
            index=1,
            help="선택한 간격마다 주요 데이터 영역을 조용히 갱신합니다.",
        )
        st.divider()

        chart_mode = st.radio("차트 모드", ["간단한 차트", "자세한 차트"], horizontal=True)
        chart_type = st.radio("차트 종류", ["캔들차트", "라인차트"], horizontal=True)

        if chart_mode == "간단한 차트":
            period_label = st.selectbox("기간 선택", list(PERIOD_OPTIONS.keys()), index=3)
            interval_label = "일봉"
            ma_settings = []
            show_volume = False
            show_rsi = False
            rsi_period = 14
        else:
            period_label = "최대"
            interval_label = st.selectbox("봉 종류", list(INTERVAL_OPTIONS.keys()), index=0)
            show_volume = st.checkbox("거래량 표시", value=True)

            st.divider()
            st.subheader("이동평균선 설정")
            ma_settings = render_moving_average_controls()

            st.divider()
            st.subheader("RSI 설정")
            show_rsi = st.checkbox("RSI 표시", value=True)
            rsi_period = st.number_input("RSI 기간", min_value=2, max_value=100, value=14, step=1)

    return {
        "ticker": normalize_ticker(ticker or "AAPL"),
        "auto_refresh_seconds": AUTO_REFRESH_OPTIONS[auto_refresh_label],
        "chart_mode": chart_mode,
        "period_label": period_label,
        "period": PERIOD_OPTIONS[period_label],
        "interval_label": interval_label,
        "interval": INTERVAL_OPTIONS[interval_label],
        "chart_type": chart_type,
        "ma_settings": ma_settings,
        "show_volume": show_volume,
        "show_rsi": show_rsi,
        "rsi_period": int(rsi_period),
    }


def render_header() -> None:
    st.title("미국 주식 리서치 대시보드")
    st.markdown(
        '<p class="app-subtitle">차트, 재무제표, 기업 개요, 밸류에이션, 시가총액 순위를 한 번에 확인하는 리서치 도구</p>',
        unsafe_allow_html=True,
    )


def get_initial_detailed_chart_range(price_data: pd.DataFrame, interval: str) -> list[Any] | None:
    if price_data.empty:
        return None

    valid_index = price_data.index[price_data["Close"].notna()] if "Close" in price_data.columns else price_data.index
    if len(valid_index) < 2:
        return None

    visible_candles = {
        "1d": 252,
        "1wk": 156,
        "1mo": 120,
    }.get(interval, 252)
    start_position = max(0, len(valid_index) - visible_candles)
    return [valid_index[start_position], valid_index[-1]]


def get_chart_render_limit(interval: str, *, detailed: bool) -> int | None:
    if detailed:
        return {
            "1d": 1260,
            "1wk": 780,
            "1mo": 480,
        }.get(interval, 1260)
    return {
        "1d": 2500,
        "1wk": 1600,
        "1mo": 900,
    }.get(interval)


def limit_chart_data_for_rendering(price_data: pd.DataFrame, interval: str, *, detailed: bool) -> pd.DataFrame:
    if price_data.empty:
        return price_data

    row_limit = get_chart_render_limit(interval, detailed=detailed)
    if row_limit is None or len(price_data) <= row_limit:
        return price_data
    return price_data.tail(row_limit).copy()


def get_visible_price_data(price_data: pd.DataFrame, x_range: list[Any] | None) -> pd.DataFrame:
    if price_data.empty or x_range is None:
        return price_data
    start, end = x_range
    return price_data.loc[(price_data.index >= start) & (price_data.index <= end)]


def calculate_price_axis_range(
    price_data: pd.DataFrame,
    x_range: list[Any] | None,
    chart_type: str,
    ma_settings: list[dict[str, Any]],
) -> list[float] | None:
    visible_data = get_visible_price_data(price_data, x_range)
    if visible_data.empty:
        return None

    series_list: list[pd.Series] = []
    if chart_type == "캔들차트" and {"High", "Low"}.issubset(visible_data.columns):
        series_list.extend(
            [
                pd.to_numeric(visible_data["High"], errors="coerce"),
                pd.to_numeric(visible_data["Low"], errors="coerce"),
            ]
        )
    elif "Close" in visible_data.columns:
        series_list.append(pd.to_numeric(visible_data["Close"], errors="coerce"))

    for ma in ma_settings:
        if not ma.get("enabled"):
            continue
        ma_series = calculate_moving_average(price_data, int(ma.get("window", 20)))
        if not ma_series.empty:
            series_list.append(ma_series.loc[visible_data.index.intersection(ma_series.index)])

    if not series_list:
        return None

    values = pd.concat(series_list).dropna()
    if values.empty:
        return None

    min_price = float(values.min())
    max_price = float(values.max())
    if min_price == max_price:
        padding = max(abs(max_price) * 0.02, 0.01)
    else:
        padding = max((max_price - min_price) * 0.08, abs((max_price + min_price) / 2) * 0.002, 0.01)
    lower_bound = min_price - padding
    if min_price > 0 and lower_bound <= 0:
        lower_bound = min_price * 0.9
    return [lower_bound, max_price + padding]


def calculate_volume_axis_range(price_data: pd.DataFrame, x_range: list[Any] | None) -> list[float] | None:
    visible_data = get_visible_price_data(price_data, x_range)
    if visible_data.empty or "Volume" not in visible_data.columns:
        return None

    volume = pd.to_numeric(visible_data["Volume"], errors="coerce").dropna()
    if volume.empty:
        return None

    max_volume = float(volume.max())
    if max_volume <= 0:
        return None
    return [0, max_volume * 1.15]


def render_dynamic_plotly_chart(fig: go.Figure, *, ticker: str, height: int) -> None:
    safe_ticker = re.sub(r"[^A-Za-z0-9_-]+", "-", display_ticker(ticker)).strip("-") or "stock"
    div_id = f"detailed-stock-chart-{safe_ticker.lower()}"
    mobile_height = 640 if height >= 760 else max(520, height - 80)
    config = {
        "scrollZoom": True,
        "displayModeBar": False,
        "displaylogo": False,
        "responsive": True,
        "doubleClick": "reset",
    }
    plot_html = fig.to_html(
        include_plotlyjs="cdn",
        full_html=False,
        config=config,
        div_id=div_id,
    )
    dynamic_axis_script = """
    <script>
    (function () {
        const plotId = __PLOT_ID__;
        const desktopHeight = __DESKTOP_HEIGHT__;
        const mobileHeight = __MOBILE_HEIGHT__;
        let pending = false;
        let adjusting = false;
        let activeXRange = null;
        const traceTimeCache = new WeakMap();

        function targetHeight() {
            return window.innerWidth <= 768 ? mobileHeight : desktopHeight;
        }

        function toTime(value) {
            if (value === null || value === undefined) {
                return NaN;
            }
            if (typeof value === "number") {
                return value;
            }
            const parsed = new Date(value).getTime();
            return Number.isFinite(parsed) ? parsed : NaN;
        }

        function isNumber(value) {
            const numeric = Number(value);
            return Number.isFinite(numeric);
        }

        function addNumber(values, value) {
            const numeric = Number(value);
            if (Number.isFinite(numeric)) {
                values.push(numeric);
            }
        }

        function traceTimes(trace) {
            if (traceTimeCache.has(trace)) {
                return traceTimeCache.get(trace);
            }
            const times = (trace.x || []).map(toTime);
            traceTimeCache.set(trace, times);
            return times;
        }

        function allXTimes(gd) {
            const values = [];
            (gd.data || []).forEach((trace) => {
                traceTimes(trace).forEach((timestamp) => {
                    if (Number.isFinite(timestamp)) {
                        values.push(timestamp);
                    }
                });
            });
            return values;
        }

        function normalizeRange(startValue, endValue) {
            const start = toTime(startValue);
            const end = toTime(endValue);
            if (!Number.isFinite(start) || !Number.isFinite(end)) {
                return null;
            }
            return [Math.min(start, end), Math.max(start, end)];
        }

        function parseRelayoutXRange(eventData) {
            if (!eventData) {
                return null;
            }

            const axisNames = Array.from(
                new Set(
                    Object.keys(eventData)
                        .map((key) => key.match(/^(xaxis\\d*)/))
                        .filter(Boolean)
                        .map((match) => match[1])
                )
            ).sort((left, right) => {
                const leftNumber = Number(left.replace("xaxis", "") || "1");
                const rightNumber = Number(right.replace("xaxis", "") || "1");
                return rightNumber - leftNumber;
            });

            for (const axisName of axisNames) {
                const directRange = eventData[axisName + ".range"];
                if (Array.isArray(directRange) && directRange.length >= 2) {
                    const parsed = normalizeRange(directRange[0], directRange[1]);
                    if (parsed) {
                        return parsed;
                    }
                }

                const start = eventData[axisName + ".range[0]"];
                const end = eventData[axisName + ".range[1]"];
                const parsed = normalizeRange(start, end);
                if (parsed) {
                    return parsed;
                }
            }

            if (Object.keys(eventData).some((key) => key.startsWith("xaxis") && key.endsWith(".autorange"))) {
                activeXRange = null;
            }
            return null;
        }

        function currentXRange(gd) {
            if (activeXRange) {
                return activeXRange;
            }

            const layout = gd._fullLayout || gd.layout || {};
            const axisKeys = Object.keys(layout)
                .filter((key) => /^xaxis\\d*$/.test(key))
                .sort((left, right) => {
                    const leftNumber = Number(left.replace("xaxis", "") || "1");
                    const rightNumber = Number(right.replace("xaxis", "") || "1");
                    return rightNumber - leftNumber;
                });

            for (const key of axisKeys) {
                const axis = layout[key];
                if (axis && axis.range && axis.range.length >= 2) {
                    const parsed = normalizeRange(axis.range[0], axis.range[1]);
                    if (parsed) {
                        return parsed;
                    }
                }
            }

            const allTimes = allXTimes(gd);
            if (!allTimes.length) {
                return null;
            }
            return [Math.min(...allTimes), Math.max(...allTimes)];
        }

        function traceVisible(trace) {
            return trace.visible !== false && trace.visible !== "legendonly";
        }

        function inRange(xValue, start, end) {
            const timestamp = toTime(xValue);
            return Number.isFinite(timestamp) && timestamp >= start && timestamp <= end;
        }

        function timestampInRange(timestamp, start, end) {
            return Number.isFinite(timestamp) && timestamp >= start && timestamp <= end;
        }

        function paddedRange(values, axisType) {
            const cleanValues = values.filter(isNumber).map(Number);
            if (!cleanValues.length) {
                return null;
            }

            let minValue = Math.min(...cleanValues);
            let maxValue = Math.max(...cleanValues);
            let padding;
            if (minValue === maxValue) {
                padding = Math.max(Math.abs(maxValue) * 0.02, 0.01);
            } else {
                padding = Math.max((maxValue - minValue) * 0.08, Math.abs((maxValue + minValue) / 2) * 0.002, 0.01);
            }

            let lower = minValue - padding;
            if (axisType === "price" && minValue > 0 && lower <= 0) {
                lower = minValue * 0.9;
            }
            return [lower, maxValue + padding];
        }

        function axisLayoutKey(axisName) {
            if (!axisName || axisName === "y") {
                return "yaxis";
            }
            return "yaxis" + axisName.replace("y", "");
        }

        function collectMainAxisValues(gd, start, end) {
            const values = [];
            (gd.data || []).forEach((trace) => {
                if (!traceVisible(trace) || (trace.yaxis || "y") !== "y") {
                    return;
                }

                const xValues = trace.x || [];
                const xTimes = traceTimes(trace);
                if (trace.type === "candlestick") {
                    for (let index = 0; index < xValues.length; index += 1) {
                        if (timestampInRange(xTimes[index], start, end)) {
                            addNumber(values, trace.high && trace.high[index]);
                            addNumber(values, trace.low && trace.low[index]);
                        }
                    }
                    return;
                }

                const yValues = trace.y || [];
                for (let index = 0; index < xValues.length; index += 1) {
                    if (timestampInRange(xTimes[index], start, end)) {
                        addNumber(values, yValues[index]);
                    }
                }
            });
            return values;
        }

        function collectNamedAxisValues(gd, start, end, matcher) {
            const values = [];
            let axisName = null;
            (gd.data || []).forEach((trace) => {
                if (!traceVisible(trace) || !matcher(trace)) {
                    return;
                }

                axisName = trace.yaxis || axisName || "y2";
                const xValues = trace.x || [];
                const xTimes = traceTimes(trace);
                const yValues = trace.y || [];
                for (let index = 0; index < xValues.length; index += 1) {
                    if (timestampInRange(xTimes[index], start, end)) {
                        addNumber(values, yValues[index]);
                    }
                }
            });
            return { axisName, values };
        }

        function adjustAxes() {
            if (adjusting) {
                return;
            }

            const gd = document.getElementById(plotId);
            if (!gd || !window.Plotly || !gd.data || !gd._fullLayout) {
                return;
            }

            const xRange = currentXRange(gd);
            if (!xRange) {
                return;
            }

            const [start, end] = xRange;
            const updates = { height: targetHeight() };
            const priceRange = paddedRange(collectMainAxisValues(gd, start, end), "price");
            if (priceRange) {
                updates["yaxis.range"] = priceRange;
            }

            const volume = collectNamedAxisValues(
                gd,
                start,
                end,
                (trace) => trace.type === "bar" || String(trace.name || "").includes("거래량")
            );
            if (volume.axisName && volume.values.length) {
                const maxVolume = Math.max(...volume.values.filter(isNumber).map(Number));
                if (Number.isFinite(maxVolume) && maxVolume > 0) {
                    updates[axisLayoutKey(volume.axisName) + ".range"] = [0, maxVolume * 1.15];
                }
            }

            const rsi = collectNamedAxisValues(
                gd,
                start,
                end,
                (trace) => String(trace.name || "").startsWith("RSI")
            );
            if (rsi.axisName) {
                updates[axisLayoutKey(rsi.axisName) + ".range"] = [0, 100];
            }

            adjusting = true;
            Plotly.relayout(gd, updates)
                .catch(() => {})
                .finally(() => {
                    adjusting = false;
                });
        }

        function scheduleAdjust() {
            if (pending) {
                return;
            }
            pending = true;
            window.requestAnimationFrame(() => {
                pending = false;
                adjustAxes();
            });
        }

        function shouldAdjustFromRelayout(eventData) {
            if (!eventData) {
                return false;
            }
            return Object.keys(eventData).some((key) => key.startsWith("xaxis"));
        }

        function install() {
            const gd = document.getElementById(plotId);
            if (!gd || !window.Plotly || !gd._fullLayout) {
                window.setTimeout(install, 80);
                return;
            }

            scheduleAdjust();
            gd.on("plotly_relayout", (eventData) => {
                if (shouldAdjustFromRelayout(eventData)) {
                    const parsedRange = parseRelayoutXRange(eventData);
                    if (parsedRange) {
                        activeXRange = parsedRange;
                    }
                    scheduleAdjust();
                }
            });
            gd.on("plotly_legendclick", () => window.setTimeout(scheduleAdjust, 0));
            gd.on("plotly_legenddoubleclick", () => window.setTimeout(scheduleAdjust, 0));
            window.addEventListener("resize", scheduleAdjust);
        }

        install();
    })();
    </script>
    """
    dynamic_axis_script = (
        dynamic_axis_script.replace("__PLOT_ID__", json.dumps(div_id))
        .replace("__DESKTOP_HEIGHT__", str(height))
        .replace("__MOBILE_HEIGHT__", str(mobile_height))
    )
    chart_html = f"""
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        html, body {{
            background: transparent;
            margin: 0;
            overflow: hidden;
            padding: 0;
        }}
        #{div_id} {{
            height: {height}px !important;
            touch-action: none;
            width: 100% !important;
        }}
        .modebar {{
            display: none !important;
        }}
        @media (max-width: 768px) {{
            #{div_id} {{
                height: {mobile_height}px !important;
            }}
            .legend text {{
                font-size: 10px !important;
            }}
        }}
    </style>
    {plot_html}
    {dynamic_axis_script}
    """
    components.html(chart_html, height=height, scrolling=False)
    st.caption("차트 안에서 드래그하면 좌우 이동, 마우스 휠이나 핀치로 확대·축소할 수 있습니다. 가격축과 거래량축은 현재 보이는 구간에 맞춰 자동 조정됩니다.")


def render_chart_tab(ticker: str, settings: dict[str, Any]) -> None:
    st.subheader(f"{display_ticker(ticker)} {settings['chart_mode']}")
    with st.spinner("주가 데이터를 불러오는 중입니다..."):
        info = get_stock_info(ticker)
        price_data = get_price_data(ticker, settings["period"], settings["interval"])

    if price_data.empty:
        st.warning("선택한 조건에 해당하는 주가 데이터가 없습니다.")
        return

    render_price_summary_cards(ticker, info, price_data, settings)

    is_detailed_chart = settings["chart_mode"] == "자세한 차트"
    show_volume = bool(settings.get("show_volume")) and is_detailed_chart
    show_rsi = bool(settings.get("show_rsi")) and is_detailed_chart
    chart_data = limit_chart_data_for_rendering(price_data, settings["interval"], detailed=is_detailed_chart)
    initial_x_range = get_initial_detailed_chart_range(chart_data, settings["interval"]) if is_detailed_chart else None

    subplot_titles = ["가격"]
    row_heights = [1.0]
    volume_row = None
    rsi_row = None

    if show_volume:
        volume_row = len(subplot_titles) + 1
        subplot_titles.append("거래량")
    if show_rsi:
        rsi_row = len(subplot_titles) + 1
        subplot_titles.append("RSI")

    if show_volume and show_rsi:
        row_heights = [0.62, 0.2, 0.18]
    elif show_volume or show_rsi:
        row_heights = [0.74, 0.26]

    fig = make_subplots(
        rows=len(subplot_titles),
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=row_heights,
        subplot_titles=tuple(subplot_titles),
    )

    if settings["chart_type"] == "캔들차트" and {"Open", "High", "Low", "Close"}.issubset(chart_data.columns):
        fig.add_trace(
            go.Candlestick(
                x=chart_data.index,
                open=chart_data["Open"],
                high=chart_data["High"],
                low=chart_data["Low"],
                close=chart_data["Close"],
                name="가격",
                increasing_line_color="#dc2626",
                decreasing_line_color="#2563eb",
            ),
            row=1,
            col=1,
        )
    else:
        fig.add_trace(
            go.Scattergl(
                x=chart_data.index,
                y=chart_data["Close"],
                mode="lines",
                line=dict(color="#1d4ed8", width=2),
                name="종가",
            ),
            row=1,
            col=1,
        )

    ma_colors = [
        "#f59e0b",
        "#10b981",
        "#7c3aed",
        "#ef4444",
        "#0891b2",
        "#a16207",
        "#db2777",
        "#16a34a",
    ]
    if is_detailed_chart:
        for idx, ma in enumerate(settings["ma_settings"]):
            if not ma["enabled"]:
                continue
            ma_series = calculate_moving_average(price_data, ma["window"]).reindex(chart_data.index)
            if ma_series.dropna().empty:
                continue
            fig.add_trace(
                go.Scattergl(
                    x=chart_data.index,
                    y=ma_series,
                    mode="lines",
                    line=dict(width=1.6, color=ma_colors[idx % len(ma_colors)]),
                    name=f"MA {ma['window']}",
                ),
                row=1,
                col=1,
            )

    if show_volume and volume_row is not None:
        volume_colors = np.where(chart_data["Close"].diff().fillna(0) >= 0, "#ef4444", "#3b82f6")
        fig.add_trace(
            go.Bar(
                x=chart_data.index,
                y=chart_data.get("Volume", pd.Series(index=chart_data.index, dtype=float)),
                marker_color=volume_colors,
                name="거래량",
                opacity=0.55,
            ),
            row=volume_row,
            col=1,
        )

    latest_rsi = None
    if show_rsi and rsi_row is not None:
        rsi = calculate_rsi(price_data, settings["rsi_period"]).reindex(chart_data.index)
        latest_rsi = rsi.dropna().iloc[-1] if not rsi.dropna().empty else None
        fig.add_trace(
            go.Scattergl(
                x=chart_data.index,
                y=rsi,
                mode="lines",
                line=dict(color="#475569", width=1.6),
                name=f"RSI {settings['rsi_period']}",
            ),
            row=rsi_row,
            col=1,
        )
        fig.add_hline(y=70, line_dash="dash", line_color="#dc2626", row=rsi_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#2563eb", row=rsi_row, col=1)

    axis_source_data = price_data if is_detailed_chart else chart_data
    price_axis_range = calculate_price_axis_range(
        axis_source_data,
        initial_x_range,
        settings["chart_type"],
        settings["ma_settings"] if is_detailed_chart else [],
    )
    volume_axis_range = calculate_volume_axis_range(axis_source_data, initial_x_range) if show_volume else None
    chart_height = 780 if is_detailed_chart else 560
    fig.update_layout(
        height=chart_height,
        margin=dict(l=20, r=20, t=45, b=20),
        hovermode="x" if is_detailed_chart else "x unified",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
        xaxis_rangeslider_visible=False,
        dragmode="pan" if is_detailed_chart else False,
        template="plotly_white",
        uirevision=f"{ticker}-{settings['interval']}-{settings['chart_type']}",
    )
    fig.update_xaxes(rangeslider_visible=False)
    if is_detailed_chart and initial_x_range:
        fig.update_xaxes(range=initial_x_range)
        fig.update_yaxes(fixedrange=True)
    fig.update_yaxes(tickformat=",.2f", range=price_axis_range, row=1, col=1)
    if show_volume and volume_row is not None:
        fig.update_yaxes(tickformat=",.0f", range=volume_axis_range, row=volume_row, col=1)
    if show_rsi and rsi_row is not None:
        fig.update_yaxes(range=[0, 100], row=rsi_row, col=1)

    if is_detailed_chart:
        render_dynamic_plotly_chart(fig, ticker=ticker, height=chart_height)
    else:
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "scrollZoom": False,
                "displayModeBar": False,
                "displaylogo": False,
                "doubleClick": False,
                "responsive": True,
            },
        )

    if show_rsi:
        if latest_rsi is None:
            st.info("RSI 계산에 필요한 데이터가 부족합니다.")
        elif latest_rsi >= 70:
            st.warning(f"최근 RSI는 {latest_rsi:.1f}입니다. 70 이상은 일반적으로 과매수 구간으로 참고됩니다.")
        elif latest_rsi <= 30:
            st.info(f"최근 RSI는 {latest_rsi:.1f}입니다. 30 이하는 일반적으로 과매도 구간으로 참고됩니다.")
        else:
            st.caption(f"최근 RSI는 {latest_rsi:.1f}입니다. 30~70 구간은 중립 구간으로 해석하는 경우가 많습니다.")


def render_financials_tab(ticker: str) -> None:
    st.subheader(f"{display_ticker(ticker)} 재무제표")
    period_label = st.radio("재무제표 기간", ["연간", "분기"], horizontal=True)
    period_type = "annual" if period_label == "연간" else "quarterly"

    with st.spinner("재무제표 데이터를 불러오는 중입니다..."):
        statements = get_financial_statements(ticker, period_type)

    income = statements.get("income", pd.DataFrame())
    balance = statements.get("balance", pd.DataFrame())
    cashflow = statements.get("cashflow", pd.DataFrame())

    st.markdown("#### 주요 재무지표 요약")
    summary_items = [
        ("최근 매출", income, ("Total Revenue",)),
        ("최근 순이익", income, ("Net Income",)),
        ("최근 영업현금흐름", cashflow, ("Operating Cash Flow",)),
        ("최근 잉여현금흐름", cashflow, ("Free Cash Flow",)),
    ]
    cols = st.columns(4)
    for col, (label, df, keys) in zip(cols, summary_items):
        value = get_statement_value(df, keys)
        growth, growth_label = calculate_statement_growth(df, keys, period_type)
        delta = format_percent(growth, na_text="") if growth is not None else None
        col.metric(
            label,
            format_number(value, compact=True, precision=2, na_text="데이터 없음"),
            delta=f"{growth_label} {delta}" if delta else None,
        )

    statement_tabs = st.tabs(["손익계산서", "재무상태표", "현금흐름표"])
    for tab, label, df in zip(
        statement_tabs,
        ["손익계산서", "재무상태표", "현금흐름표"],
        [income, balance, cashflow],
    ):
        with tab:
            display_df = prepare_financial_table(df)
            if display_df.empty:
                st.warning(f"{label} 데이터 없음")
            else:
                st.dataframe(display_df, use_container_width=True, hide_index=True)


def extract_ceo_and_officers(info: dict[str, Any]) -> tuple[str, pd.DataFrame]:
    officers = info.get("companyOfficers") or []
    if not isinstance(officers, list):
        return "확인 불가", pd.DataFrame()

    rows = []
    ceo = "확인 불가"
    for officer in officers:
        if not isinstance(officer, dict):
            continue
        name = first_valid(officer.get("name"), "확인 불가")
        title = first_valid(officer.get("title"), "확인 불가")
        if ceo == "확인 불가" and any(keyword in str(title).lower() for keyword in ("chief executive", "ceo")):
            ceo = f"{name} ({title})"
        rows.append({"이름": name, "직책": title})
    return ceo, pd.DataFrame(rows[:8])


def render_company_tab(ticker: str) -> None:
    st.subheader(f"{display_ticker(ticker)} 기업 개요")
    with st.spinner("기업 기본 정보를 불러오는 중입니다..."):
        info = get_stock_info(ticker)
        price_data = get_price_data(ticker, "1y", "1d")

    summary = build_price_summary(info, price_data if not price_data.empty else pd.DataFrame())
    currency = summary.get("currency", "USD")
    ceo, officers_df = extract_ceo_and_officers(info)
    dividend_yield = info.get("dividendYield")
    dividend_rate = info.get("dividendRate")
    has_dividend = "예" if clean_float(dividend_rate) not in (None, 0) or clean_float(dividend_yield) not in (None, 0) else "아니오 또는 확인 불가"

    card_values = [
        ("기업명", first_valid(info.get("longName"), info.get("shortName"), "확인 불가")),
        ("티커", display_ticker(ticker)),
        ("거래소", first_valid(info.get("exchange"), info.get("fullExchangeName"), "확인 불가")),
        ("섹터", first_valid(info.get("sector"), "확인 불가")),
        ("산업", first_valid(info.get("industry"), "확인 불가")),
        ("국가", first_valid(info.get("country"), "확인 불가")),
        ("임직원 수", format_number(info.get("fullTimeEmployees"), na_text="확인 불가")),
        ("CEO 또는 주요 임원", ceo),
        ("시가총액", format_market_cap(summary.get("market_cap"))),
        ("현재 주가", format_price(summary.get("current_price"), currency)),
        ("52주 최고가", format_price(summary.get("year_high"), currency)),
        ("52주 최저가", format_price(summary.get("year_low"), currency)),
        ("베타", format_number(info.get("beta"), precision=2, na_text="확인 불가")),
        ("배당수익률", format_percent(dividend_yield, na_text="확인 불가")),
        ("배당 여부", has_dividend),
    ]

    for row_start in range(0, len(card_values), 3):
        cols = st.columns(3)
        for col, (label, value) in zip(cols, card_values[row_start : row_start + 3]):
            col.markdown(card_html(label, value), unsafe_allow_html=True)

    website = info.get("website")
    st.markdown("#### 웹사이트")
    if website:
        st.link_button("기업 웹사이트 열기", website)
        st.caption(website)
    else:
        st.write("확인 불가")

    st.markdown("#### 기업 설명")
    summary_text = info.get("longBusinessSummary")
    if summary_text:
        with st.expander("기업 설명 접기/펼치기", expanded=False):
            st.write(summary_text)
    else:
        st.write("확인 불가")

    st.markdown("#### 주요 임원")
    if officers_df.empty:
        st.write("확인 불가")
    else:
        st.dataframe(officers_df, use_container_width=True, hide_index=True)


def render_valuation_tab(ticker: str) -> None:
    st.subheader(f"{display_ticker(ticker)} 밸류에이션")
    st.info("아래 지표는 참고용 지표이며, 투자 추천이나 매수·매도 판단을 의미하지 않습니다.")
    with st.spinner("밸류에이션 지표를 계산하는 중입니다..."):
        metrics = get_valuation_metrics(ticker)

    valuation_df = pd.DataFrame(metrics)
    if valuation_df.empty:
        st.warning("밸류에이션 데이터 없음")
        return
    st.dataframe(valuation_df, use_container_width=True, hide_index=True)


def render_market_cap_tab() -> None:
    st.subheader("미국 주요 기업 시가총액 순위")
    st.caption("기본 목록은 주요 미국 상장 대형주입니다. S&P 500 전체는 Wikipedia 구성종목을 가져온 뒤 yfinance로 시가총액을 조회합니다.")

    source_label = st.radio(
        "조회 대상",
        ["주요 미국 상장 대형주", "S&P 500 전체"],
        horizontal=True,
    )
    source = "sp500" if source_label == "S&P 500 전체" else "major"

    with st.spinner("시가총액 순위 데이터를 불러오는 중입니다. 최초 실행 시 시간이 걸릴 수 있습니다..."):
        ranking = get_market_cap_ranking(source)

    if ranking.empty:
        st.warning("시가총액 순위 데이터 없음")
        return

    if source == "sp500" and ranking["source"].astype(str).str.contains("Fallback").all():
        st.warning("Wikipedia S&P 500 구성종목을 가져오지 못해 주요 대형주 목록으로 대체했습니다.")

    search = st.text_input("검색", placeholder="티커 또는 기업명 검색")
    sectors = sorted([sector for sector in ranking["sector"].dropna().unique() if sector])
    selected_sectors = st.multiselect("섹터 필터", sectors, default=[])

    filtered = ranking.copy()
    if search.strip():
        keyword = search.strip().lower()
        filtered = filtered[
            filtered["ticker"].astype(str).str.lower().str.contains(keyword)
            | filtered["name"].astype(str).str.lower().str.contains(keyword)
        ]
    if selected_sectors:
        filtered = filtered[filtered["sector"].isin(selected_sectors)]

    top20 = filtered.head(20)
    if not top20.empty:
        fig = go.Figure(
            go.Bar(
                x=top20["ticker"],
                y=top20["market_cap"],
                text=[format_market_cap(value) for value in top20["market_cap"]],
                textposition="outside",
                marker_color="#1d4ed8",
                hovertemplate="<b>%{x}</b><br>시가총액: %{text}<extra></extra>",
            )
        )
        fig.update_layout(
            height=420,
            margin=dict(l=20, r=20, t=30, b=30),
            template="plotly_white",
            yaxis_title="시가총액",
            xaxis_title="티커",
        )
        st.plotly_chart(fig, use_container_width=True)

    display_df = filtered.copy()
    display_df["시가총액"] = display_df["market_cap"].map(format_market_cap)
    display_df["현재가"] = display_df["current_price"].map(lambda value: format_price(value, "USD"))
    display_df["전일 대비 등락률"] = display_df["change_pct"].map(
        lambda value: format_percent(value, already_percent=True)
    )
    display_df = display_df.rename(
        columns={
            "rank": "순위",
            "ticker": "티커",
            "name": "기업명",
            "sector": "섹터",
        }
    )
    st.dataframe(
        display_df[["순위", "티커", "기업명", "섹터", "시가총액", "현재가", "전일 대비 등락률"]],
        use_container_width=True,
        hide_index=True,
    )


def safe_render(render_func: Any, *args: Any) -> None:
    try:
        render_func(*args)
    except Exception as exc:
        st.error("데이터를 불러오거나 화면을 구성하는 중 오류가 발생했습니다.")
        st.caption(f"오류 내용: {exc}")


def render_dashboard_tabs(settings: dict[str, Any]) -> None:
    tabs = st.tabs(["종목 차트", "재무제표", "기업 개요", "밸류에이션", "시가총액 순위"])
    with tabs[0]:
        safe_render(render_chart_tab, settings["ticker"], settings)
    with tabs[1]:
        safe_render(render_financials_tab, settings["ticker"])
    with tabs[2]:
        safe_render(render_company_tab, settings["ticker"])
    with tabs[3]:
        safe_render(render_valuation_tab, settings["ticker"])
    with tabs[4]:
        safe_render(render_market_cap_tab)


def main() -> None:
    apply_custom_style()
    settings = render_sidebar()
    render_header()
    render_dashboard_tabs(settings)

    st.divider()
    st.caption("본 앱은 투자 참고용이며, 매수·매도 추천이 아닙니다. 데이터는 yfinance와 공개 웹 데이터에 의존하므로 지연, 누락, 오류가 있을 수 있습니다.")


if __name__ == "__main__":
    main()
