#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  deploy.sh  — Außerhalb des Repos ausführen, z.B. im Home-Dir
#  Ablauf: Clone → Branch → Patch-Dateien schreiben → Commit → Push
# ─────────────────────────────────────────────────────────────
set -e

REPO_URL="https://github.com/macyb27/aether-trader-web.git"
BRANCH="deep-aether-v3-full-patch"
DIR="aether-trader-web"

# ── 1. Clone ─────────────────────────────────────────────────
if [ -d "$DIR" ]; then
  echo "==> Verzeichnis existiert bereits — nutze vorhandenes Repo"
  cd "$DIR"
  git fetch origin
else
  echo "==> Klone Repo..."
  git clone "$REPO_URL"
  cd "$DIR"
fi

# ── 2. Branch erstellen ──────────────────────────────────────
echo "==> Erstelle Branch: $BRANCH"
git checkout -b "$BRANCH" 2>/dev/null || git checkout "$BRANCH"

# ── 3. Patch-Skript herunterladen & ausführen (nur Dateien schreiben, KEIN git) ──
echo "==> Schreibe alle Projektdateien..."
python3 - << 'PATCHSCRIPT'
# ════════════════ INLINE PATCH — schreibt alle Dateien ════════
from pathlib import Path

ROOT = Path(".")

def w(path, content):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.lstrip("\n"))
    print(f"  ✓ {path}")

# ── requirements.txt ──────────────────────────────────────────
w("requirements.txt", """
fastapi==0.111.0
uvicorn[standard]==0.29.0
pandas==2.2.2
numpy==1.26.4
vectorbt==0.26.2
ccxt==4.3.20
yfinance==0.2.40
stable-baselines3==2.3.2
gymnasium==0.29.1
torch==2.3.0
sqlalchemy==2.0.30
asyncpg==0.29.0
redis==5.0.4
psycopg2-binary==2.9.9
alembic==1.13.1
scikit-learn==1.4.2
scipy==1.13.0
ta==0.11.0
python-dotenv==1.0.1
httpx==0.27.0
pydantic==2.7.1
pydantic-settings==2.2.1
prometheus-client==0.20.0
loguru==0.7.2
deap==1.4.1
pyportfolioopt==1.5.5
hmmlearn==0.3.2
vaderSentiment==3.3.2
newsapi-python==0.2.7
finnhub-python==2.4.20
schedule==1.2.1
pyarrow==16.0.0
""")

# ── .env.example ─────────────────────────────────────────────
w(".env.example", """
DATABASE_URL=postgresql+asyncpg://aether:aether@localhost:5432/aether_db
REDIS_URL=redis://localhost:6379/0
EXCHANGE_ID=binance
EXCHANGE_API_KEY=
EXCHANGE_SECRET=
PAPER_TRADING=true
NEWS_API_KEY=
FINNHUB_API_KEY=
LOG_LEVEL=INFO
HISTORICAL_YEARS=3
LIVE_GATE_MIN_DAYS=30
LIVE_GATE_MIN_SHARPE=1.5
LIVE_GATE_MAX_DRAWDOWN=0.10
LIVE_GATE_MIN_TRADES=50
LIVE_GATE_MIN_WIN_RATE=0.52
""")

# ── app/core/config.py ────────────────────────────────────────
w("app/core/config.py", """
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://aether:aether@localhost:5432/aether_db"
    redis_url: str = "redis://localhost:6379/0"
    exchange_id: str = "binance"
    exchange_api_key: str = ""
    exchange_secret: str = ""
    paper_trading: bool = True
    news_api_key: Optional[str] = None
    finnhub_api_key: Optional[str] = None
    live_gate_min_days: int = 30
    live_gate_min_sharpe: float = 1.5
    live_gate_max_drawdown: float = 0.10
    live_gate_min_trades: int = 50
    live_gate_min_win_rate: float = 0.52
    log_level: str = "INFO"
    prometheus_port: int = 8001
    historical_years: int = 3

    class Config:
        env_file = ".env"

settings = Settings()
""")

# ── server.py ─────────────────────────────────────────────────
w("server.py", """
from fastapi import FastAPI
from app.api.routes import data, strategies, backtest, portfolio, execution
from prometheus_client import make_asgi_app
import uvicorn

app = FastAPI(title="Aether Trader", version="3.0.0")

app.include_router(data.router,       prefix="/api/data",       tags=["Data"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["Strategies"])
app.include_router(backtest.router,   prefix="/api/backtest",   tags=["Backtest"])
app.include_router(portfolio.router,  prefix="/api/portfolio",  tags=["Portfolio"])
app.include_router(execution.router,  prefix="/api/execution",  tags=["Execution"])

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/health")
def health():
    return {"status": "running", "version": "3.0.0"}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
""")

# ── __init__ files ────────────────────────────────────────────
for d in [
    "app", "app/api", "app/api/routes", "app/core", "app/data",
    "app/research", "app/optimization", "app/backtesting",
    "app/risk", "app/portfolio", "app/execution",
    "app/storage", "app/monitoring", "app/ai",
]:
    w(f"{d}/__init__.py", "")

# ── app/data/historical.py ────────────────────────────────────
w("app/data/historical.py", """
from pathlib import Path
from datetime import datetime
import pandas as pd
import yfinance as yf
from loguru import logger
from app.core.config import settings

CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"]
YF_MAP  = {
    "BTC/USDT": "BTC-USD", "ETH/USDT": "ETH-USD",
    "SOL/USDT": "SOL-USD", "BNB/USDT": "BNB-USD", "XRP/USDT": "XRP-USD",
}
MACRO_TICKERS = {"SP500": "^GSPC", "VIX": "^VIX", "GOLD": "GC=F", "BONDS": "^TNX"}
PERIOD_MAP = {"1m": "7d", "5m": "60d", "15m": "60d", "1h": "730d", "4h": "1825d", "1d": "max"}


def _cache_path(symbol, tf):
    safe = symbol.replace("/","_").replace("^","X").replace("=","")
    return CACHE_DIR / f"{safe}_{tf}.parquet"


def _cache_fresh(path, hours=2):
    if not path.exists(): return False
    return (datetime.now().timestamp() - path.stat().st_mtime) / 3600 < hours


def load_historical_data(symbols=None, timeframe="1h", years=None, force_refresh=False):
    symbols = symbols or SYMBOLS
    years   = years or settings.historical_years
    period  = PERIOD_MAP.get(timeframe, f"{years*365}d")
    data    = {}
    for sym in symbols:
        cache = _cache_path(sym, timeframe)
        if not force_refresh and _cache_fresh(cache):
            data[sym] = pd.read_parquet(cache)
            logger.debug(f"Cache: {sym} {timeframe} ({len(data[sym])} rows)")
            continue
        try:
            ticker = YF_MAP.get(sym, sym.replace("/","-"))
            df = yf.download(ticker, period=period, interval=timeframe,
                             progress=False, auto_adjust=True)
            if df.empty: raise ValueError("Empty")
            df.columns = [c.lower() for c in df.columns]
            df.index.name = "timestamp"
            df = df[["open","high","low","close","volume"]].dropna()
            df.to_parquet(cache)
            data[sym] = df
            logger.info(f"Loaded {len(df)} rows | {sym} | {timeframe}")
        except Exception as e:
            logger.error(f"Failed {sym}: {e}")
    return data


def load_macro_context():
    frames = []
    for name, ticker in MACRO_TICKERS.items():
        try:
            df = yf.download(ticker, period="5y", interval="1d",
                             progress=False, auto_adjust=True)
            if not df.empty:
                s = df["Close"].rename(name.lower())
                s.index.name = "timestamp"
                frames.append(s)
        except Exception as e:
            logger.warning(f"Macro {name} skipped: {e}")
    if not frames: return pd.DataFrame()
    return pd.concat(frames, axis=1).ffill().dropna(how="all")
""")

# ── app/data/news_sentiment.py ────────────────────────────────
w("app/data/news_sentiment.py", """
import requests
from datetime import datetime, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from loguru import logger
from app.core.config import settings
from app.storage.database import cache_get, cache_set

_vader = SentimentIntensityAnalyzer()

CATEGORIES = {
    "FED_RATE":     ["federal reserve","fed rate","fomc","interest rate","powell"],
    "INFLATION":    ["inflation","cpi","pce","consumer price"],
    "REGULATION":   ["sec","regulation","ban","crackdown","lawsuit"],
    "ETF_NEWS":     ["etf","spot bitcoin","blackrock","fidelity","approval"],
    "HACK_EXPLOIT": ["hack","exploit","stolen","breach","attack"],
    "MACRO_RISK":   ["recession","gdp","unemployment","war","sanctions"],
    "ADOPTION":     ["partnership","adoption","institutional","buy"],
}
SYMBOL_KEYWORDS = {
    "BTC/USDT": ["bitcoin","btc"],
    "ETH/USDT": ["ethereum","eth","defi"],
    "SOL/USDT": ["solana","sol"],
    "BNB/USDT": ["binance","bnb"],
    "XRP/USDT": ["xrp","ripple"],
}


def _score(text): return _vader.polarity_scores(text)["compound"]
def _categorize(text):
    lo = text.lower()
    for cat, kws in CATEGORIES.items():
        if any(k in lo for k in kws): return cat
    return "GENERAL"
def _symbols(text):
    lo = text.lower()
    return [s for s,kws in SYMBOL_KEYWORDS.items() if any(k in lo for k in kws)] or list(SYMBOL_KEYWORDS)


def _fetch_cryptopanic():
    try:
        r = requests.get(
            "https://cryptopanic.com/api/v1/posts/?auth_token=free&public=true&kind=news",
            timeout=8)
        return r.json().get("results", [])
    except Exception as e:
        logger.warning(f"CryptoPanic: {e}"); return []


def _fetch_newsapi():
    if not settings.news_api_key: return []
    try:
        r = requests.get("https://newsapi.org/v2/everything", timeout=8, params={
            "q": "bitcoin ethereum crypto", "apiKey": settings.news_api_key,
            "pageSize": 20, "sortBy": "publishedAt", "language": "en",
            "from": (datetime.utcnow()-timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M:%S"),
        })
        return r.json().get("articles", [])
    except Exception as e:
        logger.warning(f"NewsAPI: {e}"); return []


class SentimentAggregator:
    KEY = "sentiment:aggregated"

    def get_sentiment(self, force_refresh=False):
        if not force_refresh:
            cached = cache_get(self.KEY)
            if cached: return cached
        articles = []
        for item in _fetch_cryptopanic():
            articles.append({"text": item.get("title","")})
        for item in _fetch_newsapi():
            articles.append({"text": f"{item.get('title','')} {item.get('description','')}"})
        logger.info(f"Sentiment: {len(articles)} articles")
        result = self._aggregate(articles)
        cache_set(self.KEY, result, ttl=3600)
        return result

    def _aggregate(self, articles):
        scores = {s: [] for s in SYMBOL_KEYWORDS}
        for art in articles:
            t = art.get("text","")
            sc = _score(t)
            for sym in _symbols(t):
                scores[sym].append(sc)
        out = {}
        for sym, sc_list in scores.items():
            if sc_list:
                avg  = sum(sc_list)/len(sc_list)
                conf = min(len(sc_list)/20.0, 1.0)
            else:
                avg, conf = 0.0, 0.0
            out[sym] = {"score": round(avg,4), "confidence": round(conf,4),
                        "article_count": len(sc_list)}
        return out


class NewsImpactTracker:
    HEURISTIC = {
        "ETF_NEWS":    0.08, "REGULATION": -0.05, "HACK_EXPLOIT": -0.06,
        "FED_RATE":   -0.03, "ADOPTION":    0.04, "INFLATION":    -0.02,
    }
    def predict_impact(self, category, sentiment):
        base = self.HEURISTIC.get(category, 0.01)
        return base * sentiment


sentiment_aggregator = SentimentAggregator()
news_impact_tracker  = NewsImpactTracker()
""")

# ── app/data/regime_detector.py ───────────────────────────────
w("app/data/regime_detector.py", """
import pickle
from pathlib import Path
import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from loguru import logger

MODEL_PATH = Path("models/regime_hmm.pkl")
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
REGIME_NAMES = {0: "BULL", 1: "BEAR", 2: "HIGH_VOL"}

def _features(df):
    lr   = np.log(df["close"]/df["close"].shift(1)).fillna(0)
    rvol = lr.rolling(20).std().fillna(method="bfill")
    return np.column_stack([lr.values, rvol.values]).astype(np.float64)

def train_regime_model(df):
    X = _features(df)
    m = GaussianHMM(n_components=3, covariance_type="full", n_iter=200, random_state=42)
    m.fit(X)
    with open(MODEL_PATH,"wb") as f: pickle.dump(m,f)
    logger.info(f"Regime HMM trained (score={m.score(X):.2f})")
    return m

def load_regime_model():
    if not MODEL_PATH.exists(): raise FileNotFoundError("Train regime model first")
    with open(MODEL_PATH,"rb") as f: return pickle.load(f)

def get_current_regime(df):
    try: model = load_regime_model()
    except FileNotFoundError: model = train_regime_model(df)
    X      = _features(df)
    states = model.predict(X)
    probs  = model.predict_proba(X)
    means  = model.means_[:,0]
    order  = np.argsort(means)[::-1]
    lmap   = {order[0]:0, order[1]:2, order[2]:1}
    raw    = int(states[-1])
    label  = lmap.get(raw, raw)
    return {"regime": REGIME_NAMES[label], "state_id": label,
            "confidence": round(float(probs[-1,raw]),4)}

REGIME_STRATEGY_FIT = {
    "BULL":     {"EMA_Crossover":1.0,"RSI_MeanReversion":0.6,"MACD_Momentum":1.0,"BB_Breakout":0.7},
    "BEAR":     {"EMA_Crossover":0.4,"RSI_MeanReversion":0.9,"MACD_Momentum":0.3,"BB_Breakout":0.8},
    "HIGH_VOL": {"EMA_Crossover":0.5,"RSI_MeanReversion":1.0,"MACD_Momentum":0.5,"BB_Breakout":1.0},
}

def get_regime_multiplier(strategy_name, regime):
    fit_map = REGIME_STRATEGY_FIT.get(regime, {})
    for key, val in fit_map.items():
        if strategy_name.startswith(key): return val
    return 0.7
""")

# ── app/data/features.py ──────────────────────────────────────
w("app/data/features.py", """
import pandas as pd
import numpy as np
import ta
from loguru import logger
from app.storage.database import cache_get

RL_FEATURE_COLS = [
    "open","high","low","close","volume",
    "rsi","ema_20","ema_50","macd","atr_pct",
    "bb_width","stoch_k","obv_ema","ret_1","ret_24",
    "rvol_24","sentiment_signal","cmf","adx","roc",
]

def build_features(market_data, macro_context=None):
    out = {}
    sentiment = _load_sentiment()
    for sym, df in market_data.items():
        try:
            out[sym] = _build(df, sym, sentiment, macro_context)
        except Exception as e:
            logger.warning(f"Features failed {sym}: {e}")
    return out

def _load_sentiment():
    try: return cache_get("sentiment:aggregated") or {}
    except: return {}

def _build(df, sym, sentiment, macro):
    f = df.copy()
    f["ema_8"]   = ta.trend.EMAIndicator(f["close"],8).ema_indicator()
    f["ema_20"]  = ta.trend.EMAIndicator(f["close"],20).ema_indicator()
    f["ema_50"]  = ta.trend.EMAIndicator(f["close"],50).ema_indicator()
    f["ema_200"] = ta.trend.EMAIndicator(f["close"],200).ema_indicator()
    macd = ta.trend.MACD(f["close"])
    f["macd"]    = macd.macd_diff()
    f["macd_sig"]= macd.macd_signal()
    f["adx"]     = ta.trend.ADXIndicator(f["high"],f["low"],f["close"]).adx()
    f["cci"]     = ta.trend.CCIIndicator(f["high"],f["low"],f["close"]).cci()
    f["rsi"]     = ta.momentum.RSIIndicator(f["close"],14).rsi()
    f["rsi_fast"]= ta.momentum.RSIIndicator(f["close"],7).rsi()
    stoch        = ta.momentum.StochasticOscillator(f["high"],f["low"],f["close"])
    f["stoch_k"] = stoch.stoch()
    f["stoch_d"] = stoch.stoch_signal()
    f["roc"]     = ta.momentum.ROCIndicator(f["close"],12).roc()
    bb           = ta.volatility.BollingerBands(f["close"])
    f["bb_high"] = bb.bollinger_hband()
    f["bb_low"]  = bb.bollinger_lband()
    f["bb_width"]= bb.bollinger_wband()
    f["atr"]     = ta.volatility.AverageTrueRange(f["high"],f["low"],f["close"]).average_true_range()
    f["atr_pct"] = f["atr"] / f["close"]
    f["obv"]     = ta.volume.OnBalanceVolumeIndicator(f["close"],f["volume"]).on_balance_volume()
    f["obv_ema"] = f["obv"].ewm(span=20).mean()
    f["cmf"]     = ta.volume.ChaikinMoneyFlowIndicator(f["high"],f["low"],f["close"],f["volume"]).chaikin_money_flow()
    f["vwap"]    = (f["volume"]*(f["high"]+f["low"]+f["close"])/3).cumsum()/f["volume"].cumsum()
    f["ret_1"]   = f["close"].pct_change(1)
    f["ret_4"]   = f["close"].pct_change(4)
    f["ret_24"]  = f["close"].pct_change(24)
    f["log_ret"] = np.log(f["close"]/f["close"].shift(1))
    f["rvol_24"] = f["log_ret"].rolling(24).std()*np.sqrt(24)
    if macro is not None and not macro.empty:
        mr = macro.reindex(f.index, method="ffill")
        for col in mr.columns:
            f[f"macro_{col}"] = mr[col].pct_change(1).fillna(0)
    sym_s = sentiment.get(sym, {})
    f["sentiment_score"]  = float(sym_s.get("score",0.0))
    f["sentiment_conf"]   = float(sym_s.get("confidence",0.0))
    f["sentiment_signal"] = f["sentiment_score"] * f["sentiment_conf"]
    f.dropna(inplace=True)
    return f
""")

# ── app/storage/database.py ───────────────────────────────────
w("app/storage/database.py", """
import json
import redis as redis_lib
from datetime import datetime
from sqlalchemy import (create_engine, Column, String, Float,
                        DateTime, JSON, Integer, Boolean, Text)
from sqlalchemy.orm import declarative_base, sessionmaker
from loguru import logger
from app.core.config import settings

Base = declarative_base()

class TradeRecord(Base):
    __tablename__ = "trades"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    strategy   = Column(String, index=True)
    symbol     = Column(String)
    signal     = Column(Integer)
    price      = Column(Float)
    size       = Column(Float)
    pnl        = Column(Float, default=0.0)
    action     = Column(String)
    trade_type = Column(String, default="paper")
    status     = Column(String, default="filled")
    extra_data = Column(JSON, default={})
    timestamp  = Column(DateTime, default=datetime.utcnow)

class NewsImpactRecord(Base):
    __tablename__ = "news_impact"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    category   = Column(String, index=True)
    sentiment  = Column(Float)
    symbol     = Column(String, index=True)
    impact_24h = Column(Float, nullable=True)
    timestamp  = Column(DateTime, default=datetime.utcnow)

class StrategyStatusRecord(Base):
    __tablename__ = "strategy_status"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    name       = Column(String, unique=True, index=True)
    state_data = Column(JSON)
    updated_at = Column(DateTime, default=datetime.utcnow)

class PaperPortfolioStateRecord(Base):
    __tablename__ = "paper_portfolio_state"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    state_json = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow)

class RegimeHistoryRecord(Base):
    __tablename__ = "regime_history"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    symbol     = Column(String, index=True)
    regime     = Column(String)
    confidence = Column(Float)
    timestamp  = Column(DateTime, default=datetime.utcnow)

_engine = None
_Session = None

def get_session():
    global _engine, _Session
    if _engine is None:
        url = settings.database_url.replace("+asyncpg","")
        _engine = create_engine(url, echo=False, pool_pre_ping=True)
        Base.metadata.create_all(_engine)
        _Session = sessionmaker(bind=_engine)
    return _Session()

def save_trade(trade):
    s = get_session()
    try:
        s.add(TradeRecord(
            strategy=trade.get("strategy"), symbol=trade.get("symbol",""),
            signal=trade.get("signal",0), price=trade.get("price",0.0),
            size=trade.get("size",0.0), pnl=trade.get("pnl",0.0),
            action=trade.get("action",""), trade_type=trade.get("type","paper"),
            status=trade.get("status","filled"),
        ))
        s.commit()
    except Exception as e:
        s.rollback(); logger.debug(f"save_trade: {e}")
    finally: s.close()

def save_news_impact(impact):
    s = get_session()
    try:
        s.add(NewsImpactRecord(
            category=impact.get("category"), sentiment=impact.get("sentiment"),
 
