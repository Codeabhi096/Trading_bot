# 🤖 Binance Futures Testnet Trading Bot

A clean, production-quality Python CLI application for placing orders on the **Binance Futures Testnet (USDT-M)**. Supports **MARKET**, **LIMIT**, and **STOP-LIMIT** orders with structured logging, full input validation, and robust error handling.

---

## 📁 Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package init
│   ├── client.py            # Binance REST API client (signing, HTTP, retries)
│   ├── orders.py            # Order placement logic + OrderResult dataclass
│   ├── validators.py        # CLI input validation functions
│   └── logging_config.py    # Rotating file + console logging setup
├── logs/
│   └── trading_bot.log      # Auto-created on first run
├── cli.py                   # CLI entry point (argparse)
├── .env.example             # Example environment file
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup Instructions

### 1. Clone / Download the Project

```bash
git clone <your-repo-url>
cd trading_bot
```

### 2. Create a Virtual Environment (Recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Getting Binance Futures Testnet API Keys

1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in with your GitHub account (no KYC required)
3. Navigate to **API Key** in the top-right menu
4. Click **Generate Key**
5. Copy your **API Key** and **Secret Key** — the secret is shown only once

---

## 🛠️ Configure Environment Variables

Copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```env
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_api_secret_here
```

> ⚠️ **Never commit your `.env` file to version control.**

---

## 🚀 How to Run

### Basic Syntax

```bash
python cli.py --symbol SYMBOL --side BUY|SELL --type MARKET|LIMIT|STOP_LIMIT --quantity QTY [--price PRICE] [--stop-price STOP_PRICE] [--tif GTC|IOC|FOK]
```

### Arguments

| Argument | Required | Description |
|---|---|---|
| `--symbol` | ✅ | Trading pair, e.g. `BTCUSDT`, `ETHUSDT` |
| `--side` | ✅ | `BUY` or `SELL` |
| `--type` | ✅ | `MARKET`, `LIMIT`, or `STOP_LIMIT` |
| `--quantity` | ✅ | Order quantity, e.g. `0.01` |
| `--price` | For LIMIT/STOP_LIMIT | Limit price |
| `--stop-price` | For STOP_LIMIT only | Stop trigger price |
| `--tif` | No | Time-in-force: `GTC` (default), `IOC`, `FOK` |
| `--log-level` | No | `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: `INFO`) |

---

## 📋 Example Commands

### MARKET Order — Buy

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### MARKET Order — Sell

```bash
python cli.py --symbol ETHUSDT --side SELL --type MARKET --quantity 0.1
```

### LIMIT Order — Sell

```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 68000
```

### LIMIT Order — Buy with IOC

```bash
python cli.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.01 --price 65000 --tif IOC
```

### STOP-LIMIT Order (Bonus Feature)

```bash
python cli.py --symbol BTCUSDT --side BUY --type STOP_LIMIT --quantity 0.01 --price 66500 --stop-price 66800
```

---

## 📤 Expected Output

### MARKET Order (BUY)

```
══════════════════════════════════════════════════
  ORDER REQUEST SUMMARY
══════════════════════════════════════════════════
  Symbol         : BTCUSDT
  Side           : BUY
  Order Type     : MARKET
  Quantity       : 0.01
══════════════════════════════════════════════════

──────────────────────────────────────────────────
  ORDER RESPONSE
──────────────────────────────────────────────────
  Order ID       : 4751283920
  Client Order ID: web_aKjd72hJSla92bPq
  Symbol         : BTCUSDT
  Side           : BUY
  Type           : MARKET
  Status         : FILLED
  Price          : 0
  Avg Price      : 67423.50000
  Orig Qty       : 0.01
  Executed Qty   : 0.01
  Time In Force  : GTC
──────────────────────────────────────────────────

  ✅  Order placed successfully! Order ID: 4751283920
```

### LIMIT Order (SELL)

```
══════════════════════════════════════════════════
  ORDER REQUEST SUMMARY
══════════════════════════════════════════════════
  Symbol         : BTCUSDT
  Side           : SELL
  Order Type     : LIMIT
  Quantity       : 0.01
  Price          : 68000.0
  Time-in-Force  : GTC
══════════════════════════════════════════════════

──────────────────────────────────────────────────
  ORDER RESPONSE
──────────────────────────────────────────────────
  Order ID       : 4751291047
  Client Order ID: web_3mXpQ8nTy2oPl6rW
  Symbol         : BTCUSDT
  Side           : SELL
  Type           : LIMIT
  Status         : NEW
  Price          : 68000
  Avg Price      : 0.00000
  Orig Qty       : 0.01
  Executed Qty   : 0
  Time In Force  : GTC
──────────────────────────────────────────────────

  ✅  Order placed successfully! Order ID: 4751291047
```

---

## 📝 Logging

All API requests, responses, and errors are logged to:

```
logs/trading_bot.log
```

The log file rotates at **5 MB** and keeps up to **3 backups**. Log format:

```
2025-07-10 14:22:01 | INFO     | trading_bot.client | POST https://testnet.binancefuture.com/fapi/v1/order | body: {...}
2025-07-10 14:22:02 | INFO     | trading_bot.client | Response HTTP 200 | body: {...}
2025-07-10 14:22:02 | INFO     | trading_bot.cli | Order success | orderId=4751283920 status=FILLED executedQty=0.01 avgPrice=67423.50000
```

---

## ❌ Error Handling

| Scenario | Behaviour |
|---|---|
| Missing API credentials | Exits with clear message, logs error |
| Invalid symbol / side / type | Exits with validation error before any API call |
| Missing price for LIMIT order | Validation error with explanation |
| Binance API error (e.g. insufficient margin) | Prints API error code + message |
| Network / timeout failure | Retries up to 3 times, then prints network error |
| Unexpected exception | Logs full traceback, prints friendly message |

---

## 🧰 Dependencies

| Package | Purpose |
|---|---|
| `requests` | HTTP client for Binance REST API |
| `urllib3` | Retry logic via `HTTPAdapter` |
| `python-dotenv` | Load `.env` credentials |

---

## 📌 Assumptions

- All orders are placed on the **USDT-M Futures Testnet** (`https://testnet.binancefuture.com`)
- Position side defaults to `BOTH` (one-way mode); hedge mode is not supported
- Quantity precision must match the symbol's lot size filter on the testnet (check exchange info if you get filter errors)
- The `STOP_LIMIT` order maps to Binance Futures `type=STOP`, which is a stop-limit order (not stop-market)
- Testnet accounts are periodically reset by Binance; regenerate API keys if authentication fails
