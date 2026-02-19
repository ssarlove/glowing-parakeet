# PolyTUI - Polymarket Terminal User Interface

A professional Terminal User Interface (TUI) for browsing and exploring prediction markets on Polymarket.

**Two versions available:**
- `polytui_simple.py` - Simple version that works in ANY terminal (recommended)
- `polytui.py` - Advanced Textual-based version for rich interactive terminals

## Features

- **Interactive Market Browser**: Browse and search through active prediction markets
- **Real-time Order Book**: View live bid/ask order books for each market
- **Market Details**: View comprehensive market information including volume, liquidity, and probabilities
- **Dual Mode**: Works both as interactive TUI and headless agent for automation

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/polytui.git
cd polytui
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Copy `.env.example` to `.env` and add your API credentials for authenticated features:
```bash
cp .env.example .env
# Edit .env with your Polymarket API credentials
```

## Usage

### Simple Version (Recommended - works in any terminal)

```bash
# Interactive mode
python polytui_simple.py

# Agent mode (headless)
python polytui_simple.py --list --limit 10
python polytui_simple.py --market-id <condition_id>
python polytui_simple.py --orderbook <token_id>
python polytui_simple.py --price <token_id>
```

### Advanced Version (Textual-based)

For rich interactive terminals:

```bash
# Interactive mode
python polytui.py

# Agent mode (headless)
python polytui.py --agent --list --limit 10
python polytui.py --agent --market-id <condition_id>
python polytui.py --agent --orderbook <token_id>
python polytui.py --agent --price <token_id>
```

#### Keyboard Shortcuts (Advanced version)

| Key | Action |
|-----|--------|
| `q` | Quit |
| `r` | Refresh markets |
| `j` / `k` | Navigate up/down |
| `Enter` | Select market |

### Agent Mode Examples

```bash
# Get top 5 markets
python polytui.py --agent --list --limit 5

# Get market by ID
python polytui.py --agent --market-id 0x1234567890abcdef...

# Get orderbook
python polytui.py --agent --orderbook 0xabcdef123456...
```

## API Integration

### Public APIs (No Authentication Required)

- **Gamma API** (`https://gamma-api.polymarket.com`): Market discovery and metadata
- **CLOB API** (`https://clob.polymarket.com`): Order books and prices
- **Data API** (`https://data-api.polymarket.com`): User positions and history

### Authenticated APIs (Optional)

For trading functionality, you need:
1. A Polymarket account
2. API credentials from https://polymarket.com/account
3. Ethereum private key for signing transactions

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    PolyTUI App                       │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┬─────────────┬────────────────────┐  │
│  │   Market    │   Market    │    Order Book      │  │
│  │   List      │   Details   │    & Trade Panel   │  │
│  └─────────────┴─────────────┴────────────────────┘  │
├─────────────────────────────────────────────────────┤
│                    Status Bar                         │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                PolymarketClient                      │
├─────────────────────────────────────────────────────┤
│  • Gamma API (Markets, Events)                      │
│  • CLOB API (Order Book, Prices)                    │
│  • Data API (Positions, History)                    │
└─────────────────────────────────────────────────────┘
```

## Technologies

- **Textual**: Modern TUI framework for Python
- **Rich**: Rich library for enhanced terminal formatting
- **Requests**: HTTP client for API calls

## Disclaimer

This software is for educational and informational purposes only. 
- Not affiliated with Polymarket
- Always do your own research before making any trading decisions
- Never share your private keys or API secrets

## License

MIT License

## Author

PolyTUI - Built with Python and Textual
