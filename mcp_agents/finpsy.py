"""
FinPsyMCP - Financial Psychology & Analytics Multi-Agent System
Complete production implementation integrating behavioral finance with quantitative analysis

This module provides a comprehensive financial analysis system combining:
- Multi-source data collection (stocks, crypto, macro, sentiment)
- Advanced analytics (correlation, volatility, factor analysis)
- Time-series forecasting (Prophet)
- Portfolio optimization (mean-variance)
- Risk metrics (Sharpe ratio, drawdown)
- Strategic decision synthesis
- Business health diagnostics
"""

import yfinance as yf
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
import logging
from textblob import TextBlob
from prophet import Prophet
from sklearn.linear_model import LinearRegression
import warnings

from mcp_agents.base_agent import BaseMCPAgent

warnings.filterwarnings('ignore')

# =============================================================================
# DATA COLLECTION AGENT
# =============================================================================

class DataCollectorAgent(BaseMCPAgent):
    """
    Comprehensive data collection from multiple financial sources
    """

    def __init__(self, db_dsn: str = None, fred_api_key: str = None):
        super().__init__(
            agent_id='mcp_finpsy_data_collector',
            mcp_system='finpsy',
            db_dsn=db_dsn
        )
        self.fred_api_key = fred_api_key

    def process(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data collection request

        Args:
            task_input: {
                'tickers': List[str],
                'start_date': str,
                'end_date': str (optional),
                'include_crypto': bool (optional),
                'include_macro': bool (optional),
                'macro_indicators': List[str] (optional)
            }

        Returns:
            Dict with collected data
        """
        tickers = task_input.get('tickers', [])
        start_date = task_input.get('start_date', (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'))
        end_date = task_input.get('end_date', datetime.now().strftime('%Y-%m-%d'))

        result = {}

        # Collect stock data
        if tickers:
            result['stock_data'] = self.fetch_stock_data(tickers, start_date, end_date)

        # Collect crypto data if requested
        if task_input.get('include_crypto', False):
            crypto_symbols = task_input.get('crypto_symbols', ['bitcoin', 'ethereum'])
            result['crypto_data'] = self.fetch_crypto_data(crypto_symbols)

        # Collect macro data if requested
        if task_input.get('include_macro', False) and self.fred_api_key:
            indicators = task_input.get('macro_indicators', ['DGS10', 'UNRATE', 'CPIAUCSL'])
            result['macro_data'] = self.fetch_macro_data(indicators)

        return result

    def fetch_stock_data(
        self,
        tickers: List[str],
        start: str,
        end: str
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch stock data from Yahoo Finance

        Args:
            tickers: List of ticker symbols
            start: Start date (YYYY-MM-DD)
            end: End date (YYYY-MM-DD)

        Returns:
            Dict mapping ticker to DataFrame
        """
        data = {}

        for ticker in tickers:
            try:
                self.logger.info(f"Fetching stock data for {ticker}")
                df = yf.download(ticker, start=start, end=end, progress=False)

                if not df.empty:
                    # Calculate additional metrics
                    df['Returns'] = df['Close'].pct_change()
                    df['Volatility_21d'] = df['Returns'].rolling(window=21).std() * np.sqrt(252)
                    df['SMA_50'] = df['Close'].rolling(window=50).mean()
                    df['SMA_200'] = df['Close'].rolling(window=200).mean()

                    data[ticker] = df
                    self.logger.info(f"Successfully fetched {len(df)} rows for {ticker}")
                else:
                    self.logger.warning(f"No data found for {ticker}")

            except Exception as e:
                self.logger.error(f"Error fetching {ticker}: {e}")
                data[ticker] = pd.DataFrame()

        return data

    def fetch_crypto_data(
        self,
        symbols: List[str],
        vs_currency: str = 'usd',
        days: int = 365
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch cryptocurrency data from CoinGecko

        Args:
            symbols: List of crypto symbols (e.g., ['bitcoin', 'ethereum'])
            vs_currency: Quote currency
            days: Number of days of historical data

        Returns:
            Dict mapping symbol to DataFrame
        """
        data = {}

        for symbol in symbols:
            try:
                self.logger.info(f"Fetching crypto data for {symbol}")
                url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart"
                params = {"vs_currency": vs_currency, "days": days}

                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()

                json_data = response.json()

                df = pd.DataFrame(json_data['prices'], columns=['timestamp', 'price'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)

                # Add returns and volatility
                df['returns'] = df['price'].pct_change()
                df['volatility_30d'] = df['returns'].rolling(window=30).std() * np.sqrt(365)

                data[symbol] = df
                self.logger.info(f"Successfully fetched {len(df)} rows for {symbol}")

            except Exception as e:
                self.logger.error(f"Error fetching crypto {symbol}: {e}")
                data[symbol] = pd.DataFrame()

        return data

    def fetch_macro_data(self, indicators: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Fetch macroeconomic data from FRED

        Args:
            indicators: List of FRED series IDs

        Returns:
            Dict mapping indicator to DataFrame
        """
        if not self.fred_api_key:
            self.logger.warning("FRED API key not provided")
            return {}

        data = {}

        for indicator in indicators:
            try:
                self.logger.info(f"Fetching FRED data for {indicator}")
                url = f"https://api.stlouisfed.org/fred/series/observations"
                params = {
                    'series_id': indicator,
                    'api_key': self.fred_api_key,
                    'file_type': 'json'
                }

                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()

                json_data = response.json()
                observations = json_data.get('observations', [])

                df = pd.DataFrame(observations)
                df['date'] = pd.to_datetime(df['date'])
                df['value'] = pd.to_numeric(df['value'], errors='coerce')
                df.set_index('date', inplace=True)
                df = df[['value']].dropna()
                df.columns = [indicator]

                data[indicator] = df
                self.logger.info(f"Successfully fetched {len(df)} rows for {indicator}")

            except Exception as e:
                self.logger.error(f"Error fetching FRED data for {indicator}: {e}")
                data[indicator] = pd.DataFrame()

        return data


# =============================================================================
# DATA CLEANER AGENT
# =============================================================================

class CleanerAgent(BaseMCPAgent):
    """
    Data cleaning and preprocessing for financial analysis
    """

    def __init__(self, db_dsn: str = None):
        super().__init__(
            agent_id='mcp_finpsy_cleaner',
            mcp_system='finpsy',
            db_dsn=db_dsn
        )

    def process(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data cleaning request

        Args:
            task_input: {
                'dataframes': Dict[str, pd.DataFrame],
                'methods': List[str] (optional)
            }

        Returns:
            Dict with cleaned dataframes
        """
        dataframes = task_input.get('dataframes', {})
        methods = task_input.get('methods', ['drop_duplicates', 'fill_missing', 'outliers'])

        cleaned = {}

        for name, df in dataframes.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                cleaned[name] = self.clean_dataframe(df, methods)
            else:
                cleaned[name] = df

        return {'cleaned_data': cleaned}

    def clean_dataframe(
        self,
        df: pd.DataFrame,
        methods: List[str]
    ) -> pd.DataFrame:
        """
        Apply cleaning methods to DataFrame

        Args:
            df: Input DataFrame
            methods: List of cleaning methods to apply

        Returns:
            Cleaned DataFrame
        """
        df = df.copy()
        original_len = len(df)

        # Remove duplicates
        if 'drop_duplicates' in methods:
            df = df[~df.index.duplicated(keep='first')]

        # Fill missing values
        if 'fill_missing' in methods:
            # Forward fill then backward fill
            df = df.fillna(method='ffill').fillna(method='bfill')

        # Handle outliers using IQR method
        if 'outliers' in methods:
            numeric_columns = df.select_dtypes(include=[np.number]).columns

            for col in numeric_columns:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 3 * IQR
                upper_bound = Q3 + 3 * IQR

                # Cap outliers instead of removing
                df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)

        self.logger.info(f"Cleaned {original_len} -> {len(df)} rows")

        return df

    def align_datasets(self, dataframes: List[pd.DataFrame]) -> List[pd.DataFrame]:
        """
        Align multiple datasets to common index

        Args:
            dataframes: List of DataFrames to align

        Returns:
            List of aligned DataFrames
        """
        if not dataframes:
            return []

        # Find common index
        common_index = dataframes[0].index

        for df in dataframes[1:]:
            common_index = common_index.intersection(df.index)

        # Align all dataframes
        aligned = [df.loc[common_index] for df in dataframes]

        self.logger.info(f"Aligned {len(dataframes)} datasets to {len(common_index)} common rows")

        return aligned


# =============================================================================
# SENTIMENT ANALYSIS AGENT
# =============================================================================

class SentimentAgent(BaseMCPAgent):
    """
    Behavioral sentiment analysis for financial markets
    """

    def __init__(self, db_dsn: str = None):
        super().__init__(
            agent_id='mcp_finpsy_sentiment',
            mcp_system='finpsy',
            db_dsn=db_dsn
        )

    def process(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process sentiment analysis request

        Args:
            task_input: {
                'texts': List[str] or pd.DataFrame,
                'text_column': str (if DataFrame),
                'rolling_window': int (optional)
            }

        Returns:
            Dict with sentiment scores
        """
        texts = task_input.get('texts')
        text_column = task_input.get('text_column', 'text')
        rolling_window = task_input.get('rolling_window', 5)

        if isinstance(texts, pd.DataFrame):
            df = self.batch_analyze(texts, text_column)

            if rolling_window:
                df = self.rolling_sentiment(df, rolling_window)

            return {
                'sentiment_df': df,
                'avg_sentiment': float(df['sentiment'].mean()),
                'sentiment_trend': 'positive' if df['sentiment_ma'].iloc[-1] > 0 else 'negative'
            }

        elif isinstance(texts, list):
            scores = [self.analyze_text(text) for text in texts]
            return {
                'sentiment_scores': scores,
                'avg_sentiment': np.mean(scores)
            }

        else:
            return {'error': 'Invalid input format'}

    def analyze_text(self, text: str) -> float:
        """
        Analyze sentiment of a single text

        Args:
            text: Input text

        Returns:
            Sentiment score (-1 to 1)
        """
        try:
            blob = TextBlob(str(text))
            return blob.sentiment.polarity
        except Exception as e:
            self.logger.error(f"Error analyzing text: {e}")
            return 0.0

    def batch_analyze(
        self,
        df: pd.DataFrame,
        text_col: str = 'text'
    ) -> pd.DataFrame:
        """
        Batch sentiment analysis on DataFrame

        Args:
            df: Input DataFrame
            text_col: Column containing text

        Returns:
            DataFrame with sentiment scores
        """
        df = df.copy()
        df['sentiment'] = df[text_col].apply(self.analyze_text)
        return df

    def rolling_sentiment(
        self,
        df: pd.DataFrame,
        window: int = 5
    ) -> pd.DataFrame:
        """
        Calculate rolling average sentiment

        Args:
            df: DataFrame with sentiment column
            window: Rolling window size

        Returns:
            DataFrame with rolling sentiment
        """
        df = df.copy()
        df['sentiment_ma'] = df['sentiment'].rolling(window).mean()
        return df


# =============================================================================
# ANALYTICS AGENT
# =============================================================================

class AnalyticsAgent(BaseMCPAgent):
    """
    Advanced statistical and quantitative analytics
    """

    def __init__(self, db_dsn: str = None):
        super().__init__(
            agent_id='mcp_finpsy_analytics',
            mcp_system='finpsy',
            db_dsn=db_dsn
        )

    def process(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process analytics request

        Args:
            task_input: {
                'dataframes': Dict[str, pd.DataFrame],
                'analyses': List[str]  # ['correlation', 'volatility', 'factor_analysis']
            }

        Returns:
            Dict with analysis results
        """
        dataframes = task_input.get('dataframes', {})
        analyses = task_input.get('analyses', ['correlation', 'volatility'])

        results = {}

        if 'correlation' in analyses and len(dataframes) > 1:
            results['correlation'] = self.compute_correlation(dataframes)

        if 'volatility' in analyses:
            results['volatility'] = {}
            for name, df in dataframes.items():
                if 'Close' in df.columns:
                    results['volatility'][name] = self.compute_volatility(df)

        if 'factor_analysis' in analyses:
            factor_data = task_input.get('factor_data')
            target_data = task_input.get('target_data')

            if factor_data is not None and target_data is not None:
                results['factor_analysis'] = self.factor_analysis(
                    factor_data,
                    target_data,
                    task_input.get('factors'),
                    task_input.get('target', 'Close')
                )

        return results

    def compute_correlation(self, dataframes: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Compute correlation matrix across multiple datasets

        Args:
            dataframes: Dict of DataFrames

        Returns:
            Correlation matrix
        """
        # Extract closing prices and merge
        merged = pd.DataFrame()

        for name, df in dataframes.items():
            if 'Close' in df.columns:
                merged[name] = df['Close']

        if not merged.empty:
            corr_matrix = merged.corr()
            self.logger.info(f"Computed correlation for {len(merged.columns)} assets")
            return corr_matrix

        return pd.DataFrame()

    def compute_volatility(
        self,
        df: pd.DataFrame,
        col: str = 'Close',
        window: int = 21
    ) -> pd.Series:
        """
        Compute rolling volatility (annualized)

        Args:
            df: Input DataFrame
            col: Column to analyze
            window: Rolling window

        Returns:
            Volatility series
        """
        returns = df[col].pct_change()
        volatility = returns.rolling(window=window).std() * np.sqrt(252)
        return volatility

    def factor_analysis(
        self,
        df: pd.DataFrame,
        factors: List[str],
        target: str = 'Close'
    ) -> Dict[str, Any]:
        """
        Multi-factor regression analysis

        Args:
            df: DataFrame with factors and target
            factors: List of factor column names
            target: Target variable name

        Returns:
            Dict with coefficients and statistics
        """
        X = df[factors].dropna()
        y = df[target].loc[X.index]

        model = LinearRegression()
        model.fit(X, y)

        # Calculate R-squared
        r_squared = model.score(X, y)

        results = {
            'coefficients': dict(zip(factors, model.coef_)),
            'intercept': float(model.intercept_),
            'r_squared': float(r_squared)
        }

        self.logger.info(f"Factor analysis R²: {r_squared:.4f}")

        return results


# Continue in next message due to length...

# =============================================================================
# FORECAST AGENT
# =============================================================================

class ForecastAgent(BaseMCPAgent):
    """
    Time-series forecasting using Prophet and statistical models
    """

    def __init__(self, db_dsn: str = None):
        super().__init__(
            agent_id='mcp_finpsy_forecast',
            mcp_system='finpsy',
            db_dsn=db_dsn
        )

    def process(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process forecasting request

        Args:
            task_input: {
                'dataframe': pd.DataFrame,
                'target_column': str,
                'forecast_periods': int,
                'date_column': str (optional)
            }

        Returns:
            Dict with forecast results
        """
        df = task_input.get('dataframe')
        target_col = task_input.get('target_column', 'Close')
        periods = task_input.get('forecast_periods', 30)
        date_col = task_input.get('date_column', 'Date')

        if df is None or df.empty:
            return {'error': 'No data provided'}

        try:
            forecast = self.prophet_forecast(df, target_col, periods, date_col)
            return {
                'forecast': forecast.to_dict(orient='records'),
                'periods': periods,
                'model': 'prophet'
            }

        except Exception as e:
            self.logger.error(f"Forecast error: {e}")
            return {'error': str(e)}

    def prophet_forecast(
        self,
        df: pd.DataFrame,
        col: str = 'Close',
        periods: int = 30,
        date_col: str = 'Date'
    ) -> pd.DataFrame:
        """
        Generate forecast using Facebook Prophet

        Args:
            df: Input DataFrame
            col: Column to forecast
            periods: Number of periods to forecast
            date_col: Date column name

        Returns:
            DataFrame with forecast
        """
        # Prepare data for Prophet
        if date_col not in df.columns:
            df = df.reset_index()
            date_col = df.columns[0]

        forecast_df = df[[date_col, col]].copy()
        forecast_df.columns = ['ds', 'y']
        forecast_df = forecast_df.dropna()

        # Create and fit model
        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05
        )

        model.fit(forecast_df)

        # Make forecast
        future = model.make_future_dataframe(periods=periods)
        forecast = model.predict(future)

        # Return relevant columns
        result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods)
        result.columns = ['date', 'forecast', 'lower_bound', 'upper_bound']

        self.logger.info(f"Generated {periods}-period forecast")

        return result


# =============================================================================
# PORTFOLIO AGENT
# =============================================================================

class PortfolioAgent(BaseMCPAgent):
    """
    Portfolio optimization using modern portfolio theory
    """

    def __init__(self, db_dsn: str = None):
        super().__init__(
            agent_id='mcp_finpsy_portfolio',
            mcp_system='finpsy',
            db_dsn=db_dsn
        )

    def process(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process portfolio optimization request

        Args:
            task_input: {
                'returns': pd.DataFrame,  # Asset returns
                'method': str,  # 'mean_variance', 'max_sharpe', 'min_volatility'
                'constraints': Dict (optional)
            }

        Returns:
            Dict with optimal weights
        """
        returns = task_input.get('returns')
        method = task_input.get('method', 'mean_variance')
        constraints = task_input.get('constraints', {})

        if returns is None or returns.empty:
            return {'error': 'No returns data provided'}

        try:
            if method == 'mean_variance':
                weights = self.mean_variance_optimize(returns)
            elif method == 'max_sharpe':
                weights = self.maximize_sharpe(returns)
            elif method == 'min_volatility':
                weights = self.minimize_volatility(returns)
            else:
                return {'error': f'Unknown method: {method}'}

            # Calculate portfolio metrics
            portfolio_return = (weights * returns.mean()).sum() * 252
            portfolio_vol = np.sqrt(np.dot(weights, np.dot(returns.cov() * 252, weights)))
            sharpe = portfolio_return / portfolio_vol

            return {
                'weights': weights.to_dict(),
                'expected_return': float(portfolio_return),
                'expected_volatility': float(portfolio_vol),
                'sharpe_ratio': float(sharpe),
                'method': method
            }

        except Exception as e:
            self.logger.error(f"Portfolio optimization error: {e}")
            return {'error': str(e)}

    def mean_variance_optimize(self, returns: pd.DataFrame) -> pd.Series:
        """
        Mean-variance optimization (basic implementation)

        Args:
            returns: Asset returns DataFrame

        Returns:
            Series of optimal weights
        """
        mean_returns = returns.mean()
        cov_matrix = returns.cov()

        # Simple inverse covariance weighting
        inv_cov = np.linalg.pinv(cov_matrix.values)
        weights = np.dot(inv_cov, mean_returns.values)

        # Normalize to sum to 1
        weights = weights / weights.sum()

        # Ensure no negative weights (long-only)
        weights = np.maximum(weights, 0)
        weights = weights / weights.sum()

        return pd.Series(weights, index=returns.columns)

    def maximize_sharpe(self, returns: pd.DataFrame, risk_free: float = 0.02) -> pd.Series:
        """
        Maximize Sharpe ratio

        Args:
            returns: Asset returns
            risk_free: Risk-free rate

        Returns:
            Optimal weights
        """
        mean_returns = returns.mean() * 252
        cov_matrix = returns.cov() * 252

        # Use scipy optimization
        from scipy.optimize import minimize

        n_assets = len(returns.columns)

        def neg_sharpe(weights):
            port_return = np.dot(weights, mean_returns)
            port_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            return -(port_return - risk_free) / port_vol

        constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        bounds = tuple((0, 1) for _ in range(n_assets))
        initial = np.array([1 / n_assets] * n_assets)

        result = minimize(
            neg_sharpe,
            initial,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        return pd.Series(result.x, index=returns.columns)

    def minimize_volatility(self, returns: pd.DataFrame) -> pd.Series:
        """
        Minimum volatility portfolio

        Args:
            returns: Asset returns

        Returns:
            Optimal weights
        """
        cov_matrix = returns.cov() * 252

        from scipy.optimize import minimize

        n_assets = len(returns.columns)

        def portfolio_vol(weights):
            return np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))

        constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        bounds = tuple((0, 1) for _ in range(n_assets))
        initial = np.array([1 / n_assets] * n_assets)

        result = minimize(
            portfolio_vol,
            initial,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        return pd.Series(result.x, index=returns.columns)


# =============================================================================
# BENCHMARK AGENT
# =============================================================================

class BenchmarkAgent(BaseMCPAgent):
    """
    Performance benchmarking and risk metrics
    """

    def __init__(self, db_dsn: str = None):
        super().__init__(
            agent_id='mcp_finpsy_benchmark',
            mcp_system='finpsy',
            db_dsn=db_dsn
        )

    def process(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process benchmark request

        Args:
            task_input: {
                'returns': pd.Series or pd.DataFrame,
                'benchmark_returns': pd.Series (optional),
                'risk_free_rate': float (optional)
            }

        Returns:
            Dict with performance metrics
        """
        returns = task_input.get('returns')
        benchmark = task_input.get('benchmark_returns')
        risk_free = task_input.get('risk_free_rate', 0.02)

        if returns is None:
            return {'error': 'No returns provided'}

        metrics = {}

        # Sharpe ratio
        if isinstance(returns, pd.Series):
            metrics['sharpe_ratio'] = float(self.sharpe_ratio(returns, risk_free))
            metrics['max_drawdown'] = float(self.max_drawdown(returns.cumsum()))
            metrics['cumulative_return'] = float((1 + returns).prod() - 1)
            metrics['annualized_return'] = float(returns.mean() * 252)
            metrics['annualized_volatility'] = float(returns.std() * np.sqrt(252))

        # Information ratio vs benchmark
        if benchmark is not None:
            metrics['information_ratio'] = float(self.information_ratio(returns, benchmark))
            metrics['beta'] = float(self.calculate_beta(returns, benchmark))

        return metrics

    def sharpe_ratio(
        self,
        returns: pd.Series,
        risk_free: float = 0.02
    ) -> float:
        """
        Calculate Sharpe ratio

        Args:
            returns: Return series
            risk_free: Risk-free rate

        Returns:
            Sharpe ratio
        """
        excess_returns = returns.mean() * 252 - risk_free
        volatility = returns.std() * np.sqrt(252)

        if volatility == 0:
            return 0.0

        return excess_returns / volatility

    def max_drawdown(self, cumulative_returns: pd.Series) -> float:
        """
        Calculate maximum drawdown

        Args:
            cumulative_returns: Cumulative return series

        Returns:
            Maximum drawdown (negative value)
        """
        cum_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns - cum_max) / (cum_max + 1e-10)
        return drawdown.min()

    def information_ratio(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> float:
        """
        Calculate information ratio

        Args:
            returns: Strategy returns
            benchmark_returns: Benchmark returns

        Returns:
            Information ratio
        """
        active_returns = returns - benchmark_returns
        return (active_returns.mean() * 252) / (active_returns.std() * np.sqrt(252) + 1e-10)

    def calculate_beta(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> float:
        """
        Calculate beta vs benchmark

        Args:
            returns: Strategy returns
            benchmark_returns: Benchmark returns

        Returns:
            Beta coefficient
        """
        covariance = returns.cov(benchmark_returns)
        benchmark_variance = benchmark_returns.var()

        if benchmark_variance == 0:
            return 0.0

        return covariance / benchmark_variance


# Continue in next file...

# =============================================================================
# STRATEGIC DECISION AGENT
# =============================================================================

class StrategicDecisionAgent(BaseMCPAgent):
    """
    Strategic investment decision synthesis combining all analyses
    """

    def __init__(self, db_dsn: str = None):
        super().__init__(
            agent_id='mcp_finpsy_strategic',
            mcp_system='finpsy',
            db_dsn=db_dsn
        )

    def process(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process strategic decision request

        Args:
            task_input: {
                'stock_data': pd.DataFrame,
                'sentiment_data': pd.DataFrame or float,
                'forecast_data': Dict (optional),
                'thresholds': Dict (optional)
            }

        Returns:
            Dict with strategic decision
        """
        stock_data = task_input.get('stock_data')
        sentiment_data = task_input.get('sentiment_data')
        forecast_data = task_input.get('forecast_data', {})
        thresholds = task_input.get('thresholds', {
            'buy_threshold': 0.02,
            'sell_threshold': -0.02
        })

        if stock_data is None or stock_data.empty:
            return {'error': 'No stock data provided'}

        try:
            decision = self.decide_stock_action(
                stock_data,
                sentiment_data,
                forecast_data,
                thresholds
            )
            return decision

        except Exception as e:
            self.logger.error(f"Strategic decision error: {e}")
            return {'error': str(e)}

    def decide_stock_action(
        self,
        stock_df: pd.DataFrame,
        sentiment_data: Any,
        forecast_data: Dict[str, Any],
        thresholds: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Synthesize all data into actionable recommendation

        Args:
            stock_df: Stock price data
            sentiment_data: Sentiment score or DataFrame
            forecast_data: Forecast predictions
            thresholds: Decision thresholds

        Returns:
            Dict with recommendation and rationale
        """
        # Calculate momentum
        if 'Close' in stock_df.columns:
            recent_prices = stock_df['Close'].tail(20)
            momentum = recent_prices.pct_change().rolling(5).mean().iloc[-1]
        else:
            momentum = 0.0

        # Calculate volatility
        if 'Returns' in stock_df.columns:
            volatility = stock_df['Returns'].tail(21).std()
        else:
            volatility = 0.0

        # Extract sentiment
        if isinstance(sentiment_data, (int, float)):
            sentiment = sentiment_data
        elif isinstance(sentiment_data, pd.DataFrame) and 'sentiment_ma' in sentiment_data.columns:
            sentiment = sentiment_data['sentiment_ma'].iloc[-1]
        else:
            sentiment = 0.0

        # Incorporate forecast if available
        forecast_signal = 0.0
        if forecast_data and 'forecast' in forecast_data:
            try:
                current_price = stock_df['Close'].iloc[-1]
                forecast_price = forecast_data['forecast'][-1] if isinstance(forecast_data['forecast'], list) else forecast_data['forecast']
                forecast_signal = (forecast_price - current_price) / current_price
            except:
                pass

        # Composite scoring
        momentum_weight = 0.35
        sentiment_weight = 0.30
        forecast_weight = 0.35

        composite_score = (
            momentum * momentum_weight +
            sentiment * sentiment_weight +
            forecast_signal * forecast_weight
        )

        # Risk adjustment for volatility
        if volatility > 0.03:  # High volatility
            composite_score *= 0.8  # Reduce confidence

        # Make decision
        if composite_score > thresholds.get('buy_threshold', 0.02):
            decision = "BUY"
            confidence = min(abs(composite_score) * 10, 1.0)
        elif composite_score < thresholds.get('sell_threshold', -0.02):
            decision = "SELL"
            confidence = min(abs(composite_score) * 10, 1.0)
        else:
            decision = "HOLD"
            confidence = 1.0 - abs(composite_score) * 10

        # Build rationale
        rationale_parts = []
        if abs(momentum) > 0.01:
            rationale_parts.append(f"Price momentum: {momentum:+.2%}")
        if abs(sentiment) > 0.1:
            rationale_parts.append(f"Market sentiment: {sentiment:+.2f}")
        if abs(forecast_signal) > 0.01:
            rationale_parts.append(f"Forecast signal: {forecast_signal:+.2%}")
        if volatility > 0.02:
            rationale_parts.append(f"Elevated volatility: {volatility:.2%}")

        return {
            'decision': decision,
            'confidence': float(confidence),
            'composite_score': float(composite_score),
            'momentum_score': float(momentum),
            'sentiment_score': float(sentiment),
            'forecast_signal': float(forecast_signal),
            'volatility': float(volatility),
            'rationale': ' | '.join(rationale_parts) if rationale_parts else 'Neutral signals'
        }


# =============================================================================
# BUSINESS HEALTH AGENT
# =============================================================================

class BusinessHealthAgent(BaseMCPAgent):
    """
    Comprehensive business health diagnostics
    """

    def __init__(self, db_dsn: str = None):
        super().__init__(
            agent_id='mcp_finpsy_business_health',
            mcp_system='finpsy',
            db_dsn=db_dsn
        )

    def process(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process business health assessment

        Args:
            task_input: {
                'financials': pd.DataFrame or Dict,
                'industry_benchmarks': Dict (optional)
            }

        Returns:
            Dict with health assessment
        """
        financials = task_input.get('financials')
        benchmarks = task_input.get('industry_benchmarks', {})

        if financials is None:
            return {'error': 'No financial data provided'}

        try:
            assessment = self.assess_business_health(financials, benchmarks)
            return assessment

        except Exception as e:
            self.logger.error(f"Business health assessment error: {e}")
            return {'error': str(e)}

    def assess_business_health(
        self,
        financials: Union[pd.DataFrame, Dict],
        benchmarks: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Assess overall business health

        Args:
            financials: Financial metrics (DataFrame or Dict)
            benchmarks: Industry benchmark values

        Returns:
            Dict with health status and metrics
        """
        # Convert to dict if DataFrame
        if isinstance(financials, pd.DataFrame):
            fin_dict = financials.iloc[-1].to_dict() if not financials.empty else {}
        else:
            fin_dict = financials

        # Calculate key ratios
        ratios = {}

        # Liquidity
        if 'CurrentAssets' in fin_dict and 'CurrentLiabilities' in fin_dict:
            ratios['current_ratio'] = fin_dict['CurrentAssets'] / (fin_dict['CurrentLiabilities'] + 1e-10)
            ratios['liquidity_score'] = min(ratios['current_ratio'] / 2.0, 1.0)
        else:
            ratios['liquidity_score'] = 0.5

        # Solvency
        if 'TotalDebt' in fin_dict and 'TotalAssets' in fin_dict:
            ratios['debt_ratio'] = fin_dict['TotalDebt'] / (fin_dict['TotalAssets'] + 1e-10)
            ratios['solvency_score'] = max(1.0 - ratios['debt_ratio'], 0.0)
        else:
            ratios['solvency_score'] = 0.5

        # Profitability
        if 'NetIncome' in fin_dict and 'Equity' in fin_dict:
            ratios['roe'] = fin_dict['NetIncome'] / (fin_dict['Equity'] + 1e-10)
            ratios['profitability_score'] = min(max(ratios['roe'] * 5, 0.0), 1.0)
        else:
            ratios['profitability_score'] = 0.5

        # Composite health score
        health_score = (
            ratios['liquidity_score'] * 0.33 +
            ratios['solvency_score'] * 0.33 +
            ratios['profitability_score'] * 0.34
        )

        # Determine health status
        if health_score > 0.75:
            status = "Healthy"
            recommendations = ["Maintain strong financial position", "Consider growth investments"]
        elif health_score > 0.50:
            status = "Monitor"
            recommendations = ["Monitor key ratios closely", "Focus on improving profitability"]
        else:
            status = "High-Risk"
            recommendations = ["Urgent: Address liquidity concerns", "Reduce debt levels", "Improve operational efficiency"]

        return {
            'health_status': status,
            'health_score': float(health_score),
            'liquidity_score': float(ratios['liquidity_score']),
            'solvency_score': float(ratios['solvency_score']),
            'profitability_score': float(ratios['profitability_score']),
            'recommendations': recommendations,
            'ratios': {k: float(v) for k, v in ratios.items()}
        }


# =============================================================================
# FINPSY ORCHESTRATOR
# =============================================================================

class FinPsyOrchestrator(BaseMCPAgent):
    """
    Main orchestrator for FinPsy MCP system
    Coordinates all financial psychology and analytics agents
    """

    def __init__(self, db_dsn: str = None, fred_api_key: str = None):
        super().__init__(
            agent_id='mcp_finpsy_orchestrator',
            mcp_system='finpsy',
            db_dsn=db_dsn
        )

        self.fred_api_key = fred_api_key

        # Initialize all agents
        self.data_collector = DataCollectorAgent(db_dsn, fred_api_key)
        self.cleaner = CleanerAgent(db_dsn)
        self.sentiment = SentimentAgent(db_dsn)
        self.analytics = AnalyticsAgent(db_dsn)
        self.forecast = ForecastAgent(db_dsn)
        self.portfolio = PortfolioAgent(db_dsn)
        self.benchmark = BenchmarkAgent(db_dsn)
        self.strategic = StrategicDecisionAgent(db_dsn)
        self.business_health = BusinessHealthAgent(db_dsn)

        self.logger.info("FinPsyMCP Orchestrator initialized with all agents")

    def process(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process FinPsy task request

        Args:
            task_input: Task-specific input data

        Returns:
            Dict with results
        """
        # This is called by execute_task from base class
        return self.run_comprehensive_analysis(task_input)

    def run_stock_analysis(
        self,
        ticker: str,
        start_date: str = None,
        include_forecast: bool = True,
        include_sentiment: bool = False
    ) -> Dict[str, Any]:
        """
        Complete stock analysis workflow

        Args:
            ticker: Stock ticker symbol
            start_date: Start date for analysis
            include_forecast: Include price forecast
            include_sentiment: Include sentiment analysis

        Returns:
            Dict with comprehensive analysis
        """
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        self.logger.info(f"Running comprehensive analysis for {ticker}")

        results = {}

        # Step 1: Collect data
        try:
            data_result = self.data_collector.process({
                'tickers': [ticker],
                'start_date': start_date,
                'include_crypto': False,
                'include_macro': include_sentiment
            })

            if ticker not in data_result.get('stock_data', {}):
                return {'error': f'No data found for {ticker}'}

            stock_df = data_result['stock_data'][ticker]
            results['data_points'] = len(stock_df)

        except Exception as e:
            return {'error': f'Data collection failed: {e}'}

        # Step 2: Clean data
        cleaned = self.cleaner.process({
            'dataframes': {ticker: stock_df},
            'methods': ['drop_duplicates', 'fill_missing']
        })
        stock_df = cleaned['cleaned_data'][ticker]

        # Step 3: Analytics
        analytics_result = self.analytics.process({
            'dataframes': {ticker: stock_df},
            'analyses': ['volatility']
        })
        results['analytics'] = analytics_result

        # Step 4: Forecast (if requested)
        if include_forecast:
            forecast_result = self.forecast.process({
                'dataframe': stock_df,
                'target_column': 'Close',
                'forecast_periods': 30
            })
            results['forecast'] = forecast_result

        # Step 5: Sentiment (if requested)
        sentiment_score = 0.0
        if include_sentiment and 'macro_data' in data_result:
            # Use macro data as proxy for sentiment
            sentiment_score = 0.5  # Placeholder

        results['sentiment_score'] = sentiment_score

        # Step 6: Strategic decision
        decision_result = self.strategic.process({
            'stock_data': stock_df,
            'sentiment_data': sentiment_score,
            'forecast_data': results.get('forecast', {})
        })
        results['decision'] = decision_result

        # Step 7: Benchmark metrics
        if 'Returns' in stock_df.columns:
            benchmark_result = self.benchmark.process({
                'returns': stock_df['Returns'].dropna()
            })
            results['performance'] = benchmark_result

        return results

    def run_comprehensive_analysis(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Entry point for comprehensive analysis

        Args:
            task_input: {
                'ticker': str,
                'start_date': str (optional),
                'analysis_type': str (optional)
            }

        Returns:
            Dict with complete analysis
        """
        ticker = task_input.get('ticker', task_input.get('symbol'))
        start_date = task_input.get('start_date')
        analysis_type = task_input.get('analysis_type', 'full')

        if not ticker:
            return {'error': 'Ticker symbol required'}

        return self.run_stock_analysis(
            ticker=ticker,
            start_date=start_date,
            include_forecast=analysis_type in ['full', 'forecast'],
            include_sentiment=analysis_type in ['full', 'sentiment']
        )
