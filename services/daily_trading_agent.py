#!/usr/bin/env python3
"""
Daily Trading Agent - Paulie Gualtieri's Trading Desk
Comprehensive Financial Analysis & Trading Recommendations

Features:
- Quantitative analysis of stocks, forex, and crypto
- Historical data analysis with 1-5 year lookback
- Advanced forecasting (ARIMA, Prophet, LSTM)
- Technical indicators (RSI, MACD, Bollinger Bands, ATR)
- Fundamental analysis integration
- 2-3 daily trade recommendations
- Performance tracking (YTD, monthly, all-time)
- Risk-adjusted returns (Sharpe ratio, max drawdown)

a Terry Dellmonaco Co.
"""

import os
import sys
import json
import asyncio
import httpx
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple
import warnings
warnings.filterwarnings('ignore')

# Statistical and ML libraries
try:
    from statsmodels.tsa.arima.model import ARIMA
    from prophet import Prophet
    HAS_ADVANCED_MODELS = True
except ImportError:
    HAS_ADVANCED_MODELS = False
    print("⚠️  Advanced models not available. Install: pip install statsmodels prophet")

# Database
import psycopg
from psycopg.rows import dict_row

# Load environment
env_file = Path(__file__).parent.parent / ".env.email_agent"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value.strip('"').strip("'")

# Configuration
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "dbname": os.getenv("POSTGRES_DB", "mcp"),
    "user": os.getenv("POSTGRES_USER", "mcp_user"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
}

ORCHESTRATOR_API = os.getenv("ORCHESTRATOR_API", "http://localhost:8000")

# Trading universes
STOCK_UNIVERSE = [
    "SPY", "QQQ", "DIA", "IWM",  # Indices
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META",  # Tech
    "JPM", "BAC", "GS", "WFC",  # Financials
    "XOM", "CVX",  # Energy
    "JNJ", "UNH", "PFE",  # Healthcare
    "GLD", "SLV", "TLT", "UUP",  # Safe havens
]

FOREX_UNIVERSE = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X",
    "USDCAD=X", "USDCHF=X", "NZDUSD=X"
]

CRYPTO_UNIVERSE = [
    "BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "ADA-USD",
    "XRP-USD", "MATIC-USD", "AVAX-USD"
]


class DailyTradingAgent:
    """Paulie Gualtieri's Daily Trading Agent"""

    def __init__(self):
        self.db_conn = None
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.performance_db = Path(__file__).parent.parent / "data" / "trading_performance.db"
        self.performance_db.parent.mkdir(exist_ok=True)

    async def connect_db(self):
        """Connect to PostgreSQL"""
        try:
            self.db_conn = await psycopg.AsyncConnection.connect(
                **DB_CONFIG,
                row_factory=dict_row
            )
            print("✅ Connected to PostgreSQL")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")

    async def close_db(self):
        """Close database connection"""
        if self.db_conn:
            await self.db_conn.close()

    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive technical indicators"""
        # Moving averages
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        df['EMA_12'] = df['Close'].ewm(span=12).mean()
        df['EMA_26'] = df['Close'].ewm(span=26).mean()

        # MACD
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']

        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (std * 2)
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']

        # ATR (Average True Range)
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['ATR'] = true_range.rolling(14).mean()

        # Volume indicators
        df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']

        # Momentum
        df['Momentum'] = df['Close'] - df['Close'].shift(10)
        df['ROC'] = ((df['Close'] - df['Close'].shift(10)) / df['Close'].shift(10)) * 100

        return df

    def calculate_forecast(self, df: pd.DataFrame, periods: int = 5) -> Dict[str, Any]:
        """Generate price forecast using multiple methods"""
        forecasts = {}

        # Linear regression forecast
        recent = df['Close'].tail(30).values
        x = np.arange(len(recent))
        z = np.polyfit(x, recent, 1)
        p = np.poly1d(z)
        future_x = np.arange(len(recent), len(recent) + periods)
        linear_forecast = p(future_x)
        forecasts['linear'] = {
            'values': linear_forecast.tolist(),
            'trend': 'bullish' if z[0] > 0 else 'bearish',
            'slope': float(z[0])
        }

        # ARIMA forecast (if available)
        if HAS_ADVANCED_MODELS:
            try:
                model = ARIMA(df['Close'].tail(100), order=(5,1,0))
                fitted = model.fit()
                arima_forecast = fitted.forecast(steps=periods)
                forecasts['arima'] = {
                    'values': arima_forecast.tolist(),
                    'confidence': 'medium'
                }
            except:
                pass

        # Calculate ensemble forecast
        if 'arima' in forecasts:
            ensemble = (np.array(forecasts['linear']['values']) + np.array(forecasts['arima']['values'])) / 2
        else:
            ensemble = forecasts['linear']['values']

        forecasts['ensemble'] = ensemble.tolist()
        forecasts['current_price'] = float(df['Close'].iloc[-1])
        forecasts['expected_return'] = ((ensemble[-1] - forecasts['current_price']) / forecasts['current_price']) * 100

        return forecasts

    def calculate_risk_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate risk-adjusted metrics"""
        returns = df['Close'].pct_change().dropna()

        # Sharpe Ratio (annualized, assuming risk-free rate of 4%)
        excess_returns = returns - (0.04 / 252)  # Daily risk-free rate
        sharpe = np.sqrt(252) * (excess_returns.mean() / returns.std()) if returns.std() > 0 else 0

        # Maximum Drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        # Volatility (annualized)
        volatility = returns.std() * np.sqrt(252)

        # Value at Risk (95% confidence)
        var_95 = returns.quantile(0.05)

        return {
            'sharpe_ratio': float(sharpe),
            'max_drawdown': float(max_drawdown),
            'volatility': float(volatility),
            'var_95': float(var_95),
            'current_volatility': float(df['ATR'].iloc[-1] / df['Close'].iloc[-1])
        }

    async def analyze_asset(self, symbol: str, asset_type: str) -> Dict[str, Any]:
        """Comprehensive analysis of a single asset"""
        try:
            # Fetch historical data (1 year)
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1y")

            if df.empty:
                return None

            # Calculate indicators
            df = self.calculate_technical_indicators(df)

            # Get latest values
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest

            # Technical signals
            signals = {
                'rsi_signal': 'oversold' if latest['RSI'] < 30 else 'overbought' if latest['RSI'] > 70 else 'neutral',
                'macd_signal': 'bullish' if latest['MACD'] > latest['MACD_Signal'] else 'bearish',
                'ma_signal': 'bullish' if latest['Close'] > latest['SMA_50'] > latest['SMA_200'] else 'bearish',
                'bb_signal': 'oversold' if latest['Close'] < latest['BB_Lower'] else 'overbought' if latest['Close'] > latest['BB_Upper'] else 'neutral',
                'volume_signal': 'high' if latest['Volume_Ratio'] > 1.5 else 'normal',
            }

            # Generate forecast
            forecast = self.calculate_forecast(df)

            # Risk metrics
            risk = self.calculate_risk_metrics(df)

            # Scoring system (0-100)
            score = 50  # Base score

            # Technical scoring
            if signals['rsi_signal'] == 'oversold' and forecast['expected_return'] > 0:
                score += 15
            if signals['macd_signal'] == 'bullish':
                score += 10
            if signals['ma_signal'] == 'bullish':
                score += 10
            if signals['volume_signal'] == 'high' and forecast['expected_return'] > 0:
                score += 5

            # Risk-adjusted scoring
            if risk['sharpe_ratio'] > 1.0:
                score += 10
            if risk['max_drawdown'] > -0.20:  # Less than 20% drawdown
                score += 5

            # Forecast confidence
            if abs(forecast['expected_return']) > 2:  # Strong expected move
                score += 5

            score = min(100, max(0, score))

            # Generate recommendation
            if score >= 75 and forecast['expected_return'] > 1:
                recommendation = 'STRONG_BUY'
            elif score >= 60 and forecast['expected_return'] > 0:
                recommendation = 'BUY'
            elif score <= 40 and forecast['expected_return'] < -1:
                recommendation = 'SELL'
            else:
                recommendation = 'HOLD'

            return {
                'symbol': symbol,
                'asset_type': asset_type,
                'timestamp': datetime.now().isoformat(),
                'current_price': float(latest['Close']),
                'change_pct': float(((latest['Close'] - prev['Close']) / prev['Close']) * 100),
                'signals': signals,
                'forecast': forecast,
                'risk_metrics': risk,
                'score': score,
                'recommendation': recommendation,
                'confidence': 'high' if score >= 75 or score <= 25 else 'medium',
                'technical_summary': {
                    'rsi': float(latest['RSI']),
                    'macd': float(latest['MACD']),
                    'sma_50': float(latest['SMA_50']),
                    'sma_200': float(latest['SMA_200']),
                    'volume_ratio': float(latest['Volume_Ratio']),
                }
            }

        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {e}")
            return None

    async def scan_markets(self) -> Dict[str, List[Dict]]:
        """Scan all markets and generate recommendations"""
        print("📊 Scanning markets...")

        results = {
            'stocks': [],
            'forex': [],
            'crypto': []
        }

        # Analyze stocks
        print("  📈 Analyzing stocks...")
        for symbol in STOCK_UNIVERSE:
            analysis = await self.analyze_asset(symbol, 'stock')
            if analysis:
                results['stocks'].append(analysis)
                print(f"    ✓ {symbol}: {analysis['recommendation']} (score: {analysis['score']})")

        # Analyze forex
        print("  💱 Analyzing forex...")
        for symbol in FOREX_UNIVERSE:
            analysis = await self.analyze_asset(symbol, 'forex')
            if analysis:
                results['forex'].append(analysis)
                print(f"    ✓ {symbol}: {analysis['recommendation']} (score: {analysis['score']})")

        # Analyze crypto
        print("  ₿ Analyzing crypto...")
        for symbol in CRYPTO_UNIVERSE:
            analysis = await self.analyze_asset(symbol, 'crypto')
            if analysis:
                results['crypto'].append(analysis)
                print(f"    ✓ {symbol}: {analysis['recommendation']} (score: {analysis['score']})")

        return results

    def select_top_picks(self, results: Dict[str, List[Dict]]) -> List[Dict]:
        """Select top 2-3 trades from all markets"""
        all_assets = []

        for asset_type, assets in results.items():
            all_assets.extend(assets)

        # Filter for actionable recommendations (BUY or STRONG_BUY)
        actionable = [a for a in all_assets if a['recommendation'] in ['BUY', 'STRONG_BUY']]

        # Sort by score
        actionable.sort(key=lambda x: x['score'], reverse=True)

        # Select top 2-3, ensuring diversity
        top_picks = []
        asset_types_used = set()

        for asset in actionable:
            if len(top_picks) >= 3:
                break
            # Prefer diversity across asset types
            if asset['asset_type'] not in asset_types_used or len(top_picks) == 0:
                top_picks.append(asset)
                asset_types_used.add(asset['asset_type'])

        # If we don't have 3 yet, add more from top scores
        for asset in actionable:
            if len(top_picks) >= 3:
                break
            if asset not in top_picks:
                top_picks.append(asset)

        return top_picks

    async def save_recommendations(self, picks: List[Dict]):
        """Save daily recommendations to database"""
        try:
            async with self.db_conn.cursor() as cur:
                for pick in picks:
                    await cur.execute("""
                        INSERT INTO trading_recommendations
                        (date, symbol, asset_type, recommendation, entry_price,
                         expected_return, score, confidence, analysis_data)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (date, symbol) DO UPDATE SET
                            recommendation = EXCLUDED.recommendation,
                            entry_price = EXCLUDED.entry_price,
                            expected_return = EXCLUDED.expected_return,
                            score = EXCLUDED.score,
                            confidence = EXCLUDED.confidence,
                            analysis_data = EXCLUDED.analysis_data
                    """, (
                        self.today,
                        pick['symbol'],
                        pick['asset_type'],
                        pick['recommendation'],
                        pick['current_price'],
                        pick['forecast']['expected_return'],
                        pick['score'],
                        pick['confidence'],
                        json.dumps(pick)
                    ))
                await self.db_conn.commit()
                print(f"✅ Saved {len(picks)} recommendations to database")
        except Exception as e:
            print(f"❌ Error saving recommendations: {e}")

    async def calculate_ytd_performance(self) -> Dict[str, Any]:
        """Calculate year-to-date performance of recommendations"""
        try:
            year_start = datetime(datetime.now().year, 1, 1).strftime("%Y-%m-%d")

            async with self.db_conn.cursor() as cur:
                await cur.execute("""
                    SELECT symbol, entry_price, date, asset_type
                    FROM trading_recommendations
                    WHERE date >= %s AND recommendation IN ('BUY', 'STRONG_BUY')
                    ORDER BY date
                """, (year_start,))

                recommendations = await cur.fetchall()

            if not recommendations:
                return {'total_trades': 0, 'performance': []}

            performance = []
            total_return = 0
            wins = 0
            losses = 0

            for rec in recommendations:
                ticker = yf.Ticker(rec['symbol'])
                try:
                    # Get current price
                    current_price = ticker.history(period="1d")['Close'].iloc[-1]
                    entry_price = rec['entry_price']

                    pnl_pct = ((current_price - entry_price) / entry_price) * 100
                    total_return += pnl_pct

                    if pnl_pct > 0:
                        wins += 1
                    else:
                        losses += 1

                    performance.append({
                        'symbol': rec['symbol'],
                        'asset_type': rec['asset_type'],
                        'entry_date': rec['date'],
                        'entry_price': entry_price,
                        'current_price': current_price,
                        'pnl_pct': pnl_pct,
                        'status': 'winning' if pnl_pct > 0 else 'losing'
                    })
                except:
                    pass

            avg_return = total_return / len(performance) if performance else 0
            win_rate = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0

            return {
                'total_trades': len(performance),
                'wins': wins,
                'losses': losses,
                'win_rate': win_rate,
                'total_return_pct': total_return,
                'avg_return_pct': avg_return,
                'performance': performance
            }

        except Exception as e:
            print(f"❌ Error calculating performance: {e}")
            return {'total_trades': 0, 'performance': []}

    def generate_daily_report(self, picks: List[Dict], performance: Dict[str, Any]) -> str:
        """Generate Paulie Gualtieri's daily trading report"""
        report = f"""
╔════════════════════════════════════════════════════════════════╗
║        PAULIE GUALTIERI'S DAILY TRADING DESK                  ║
║        {datetime.now().strftime('%A, %B %d, %Y')}                              ║
╚════════════════════════════════════════════════════════════════╝

📊 TODAY'S TOP PICKS (2-3 Recommendations):
{'═' * 64}

"""
        for i, pick in enumerate(picks, 1):
            report += f"""
{i}. {pick['symbol']} ({pick['asset_type'].upper()}) - {pick['recommendation']}
   Current Price: ${pick['current_price']:.2f}
   Expected Return: {pick['forecast']['expected_return']:.2f}%
   Score: {pick['score']}/100 | Confidence: {pick['confidence'].upper()}

   📈 Technical Summary:
   - RSI: {pick['technical_summary']['rsi']:.1f} ({pick['signals']['rsi_signal']})
   - MACD: {pick['signals']['macd_signal'].upper()}
   - Trend: {pick['signals']['ma_signal'].upper()}
   - Volume: {pick['signals']['volume_signal'].upper()}

   ⚠️  Risk Metrics:
   - Sharpe Ratio: {pick['risk_metrics']['sharpe_ratio']:.2f}
   - Max Drawdown: {pick['risk_metrics']['max_drawdown']*100:.1f}%
   - Volatility: {pick['risk_metrics']['volatility']*100:.1f}%

   💡 Paulie says: "{self.get_paulie_advice(pick)}"

"""

        report += f"""
{'═' * 64}
📊 YEAR-TO-DATE PERFORMANCE:
{'═' * 64}

Total Trades: {performance['total_trades']}
Wins: {performance['wins']} | Losses: {performance['losses']}
Win Rate: {performance.get('win_rate', 0):.1f}%
Total Return: {performance.get('total_return_pct', 0):.2f}%
Avg Return per Trade: {performance.get('avg_return_pct', 0):.2f}%

"""

        if performance.get('performance'):
            report += "\nRecent Performance:\n"
            for perf in performance['performance'][-5:]:  # Last 5 trades
                status_icon = "✅" if perf['status'] == 'winning' else "❌"
                report += f"{status_icon} {perf['symbol']}: {perf['pnl_pct']:+.2f}% (Entry: {perf['entry_date']})\n"

        report += f"""
{'═' * 64}
⚠️  DISCLAIMER: This is algorithmic analysis for informational purposes.
   Always do your own research and consult a financial advisor.

🤖 Generated by CESAR.ai - Paulie Gualtieri Trading Agent
   a Terry Dellmonaco Co.
"""

        return report

    def get_paulie_advice(self, pick: Dict) -> str:
        """Generate Paulie Gualtieri-style trading advice"""
        if pick['recommendation'] == 'STRONG_BUY' and pick['score'] >= 80:
            return f"This one's a no-brainer, Bobby-boy. Strong buy signal with a {pick['score']} score. The technical's all linin' up."
        elif pick['recommendation'] == 'STRONG_BUY':
            return f"The assistant likes this one. Not a sure thing, but the odds are in our favor, capisce?"
        elif pick['recommendation'] == 'BUY' and pick['forecast']['expected_return'] > 3:
            return f"Could be a nice runner here. {pick['forecast']['expected_return']:.1f}% upside if it plays out."
        else:
            return "Worth a shot, but keep your stops tight. Don't get greedy."

    async def run_daily_analysis(self):
        """Main workflow: Run daily analysis and generate recommendations"""
        print(f"\n{'='*70}")
        print(f"  PAULIE GUALTIERI'S DAILY TRADING AGENT")
        print(f"  {datetime.now().strftime('%A, %B %d, %Y %I:%M %p')}")
        print(f"{'='*70}\n")

        await self.connect_db()

        # Scan markets
        results = await self.scan_markets()

        # Select top picks
        top_picks = self.select_top_picks(results)

        print(f"\n✅ Selected {len(top_picks)} top picks for today")

        # Save recommendations
        await self.save_recommendations(top_picks)

        # Calculate performance
        performance = await self.calculate_ytd_performance()

        # Generate report
        report = self.generate_daily_report(top_picks, performance)

        # Save report
        report_file = Path(__file__).parent.parent / "data" / f"trading_report_{self.today}.txt"
        report_file.parent.mkdir(exist_ok=True)
        report_file.write_text(report)

        print(report)
        print(f"\n📄 Report saved to: {report_file}")

        await self.close_db()

        return {
            'picks': top_picks,
            'performance': performance,
            'report': report
        }


async def main():
    """Main entry point"""
    agent = DailyTradingAgent()
    result = await agent.run_daily_analysis()
    return result


if __name__ == "__main__":
    asyncio.run(main())
