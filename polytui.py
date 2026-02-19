#!/usr/bin/env python3
"""
PolyTUI - Polymarket Terminal User Interface
A professional TUI for browsing and trading on Polymarket prediction markets.
Supports both interactive human usage and headless agent mode.
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Optional

import requests
from rich.console import Console
from rich.text import Text as RichText
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Footer, Header, Static
from textual.widget import Widget

# Try to load dotenv, but make it optional
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

# ============================================================================
# CONFIGURATION
# ============================================================================

CLOB_API_BASE = "https://clob.polymarket.com"
GAMMA_API_BASE = "https://gamma-api.polymarket.com"
DATA_API_BASE = "https://data-api.polymarket.com"

# Console colors
COLOR_BG = "#0d1117"
COLOR_PANEL = "#161b22"
COLOR_BORDER = "#30363d"
COLOR_TEXT = "#c9d1d9"
COLOR_ACCENT = "#58a6ff"
COLOR_GREEN = "#3fb950"
COLOR_RED = "#f85149"
COLOR_YELLOW = "#d29922"
COLOR_PURPLE = "#a371f7"

# ============================================================================
# ASCII ART - Simple version that works on all terminals
# ============================================================================

POLYTUI_ASCII = """
+========================================+
|           PolyTUI v1.0                |
|   Polymarket Terminal Interface       |
+========================================+
"""

POLYTUI_ASCII_COMPACT = """
+========================================+
|        PolyTUI - Polymarket           |
+========================================+
"""

# ============================================================================
# API CLIENT
# ============================================================================

class PolymarketClient:
    """Client for interacting with Polymarket APIs."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        # Optional authenticated client
        self.api_key = os.getenv("POLY_API_KEY")
        self.api_secret = os.getenv("POLY_API_SECRET")
        self.private_key = os.getenv("ETHEREUM_PRIVATE_KEY")
        self.is_authenticated = bool(self.api_key and self.private_key)
    
    def get_markets(self, limit: int = 50, cursor: str = None, active_only: bool = True) -> dict:
        """Fetch active markets from Gamma API."""
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        
        # Filter for open markets if requested
        if active_only:
            params["closed"] = "false"
        
        try:
            response = self.session.get(
                f"{GAMMA_API_BASE}/markets",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Handle both list and dict responses
            markets = data if isinstance(data, list) else data.get("markets", [])
            
            return {"markets": markets, "cursor": None}
        except Exception as e:
            print(f"Error fetching markets: {e}")
            return {"markets": [], "cursor": None}
    
    def get_market(self, condition_id: str) -> dict:
        """Fetch detailed market information."""
        try:
            response = self.session.get(
                f"{GAMMA_API_BASE}/markets",
                params={"conditionId": condition_id},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            # Handle both list and dict responses
            markets = data if isinstance(data, list) else data.get("markets", [])
            return markets[0] if markets else {}
        except Exception as e:
            print(f"Error fetching market: {e}")
            return {}
    
    def get_orderbook(self, token_id: str) -> dict:
        """Fetch order book for a token."""
        try:
            response = self.session.get(
                f"{CLOB_API_BASE}/book",
                params={"token_id": token_id},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching orderbook: {e}")
            return {"bids": [], "asks": []}
    
    def get_price(self, token_id: str) -> dict:
        """Fetch current price for a token."""
        try:
            # Try the price endpoint
            response = self.session.get(
                f"{CLOB_API_BASE}/price",
                params={"token_id": token_id},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            # If price endpoint fails, try midpoint
            response = self.session.get(
                f"{CLOB_API_BASE}/midpoint",
                params={"token_id": token_id},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"Status code: {response.status_code}"}
        except Exception as e:
            print(f"Error fetching price: {e}")
            return {}
    
    def get_positions(self, address: str) -> dict:
        """Fetch user positions."""
        if not self.is_authenticated:
            return {"positions": []}
        
        try:
            response = self.session.get(
                f"{DATA_API_BASE}/positions",
                params={"address": address},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching positions: {e}")
            return {"positions": []}
    
    def place_order(self, token_id: str, side: str, amount: float, price: float) -> dict:
        """Place a limit order (requires authentication)."""
        if not self.is_authenticated:
            return {"error": "Authentication required"}
        
        # Order placement would require proper EIP-712 signing
        # This is a placeholder for the actual implementation
        order_data = {
            "token_id": token_id,
            "side": side,  # "BUY" or "SELL"
            "amount": str(amount),
            "price": str(price),
        }
        
        try:
            # In production, this would require proper L1/L2 authentication
            response = self.session.post(
                f"{CLOB_API_BASE}/order",
                json=order_data,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}


# ============================================================================
# CUSTOM WIDGETS
# ============================================================================

# Note: In Textual, Static widgets render strings. For Rich objects,
# we use the update() method to display formatted content.


# ============================================================================
# MAIN SCREEN
# ============================================================================

class PolyTUIScreen(Screen):
    """Main TUI screen."""
    
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("/", "search", "Search", show=True),
        Binding("j", "cursor_down", "Down", show=True),
        Binding("k", "cursor_up", "Up", show=True),
        Binding("enter", "select_market", "Select", show=True),
        Binding("escape", "clear_selection", "Back", show=True),
        Binding("1", "buy_yes", "Buy Yes", show=True),
        Binding("2", "buy_no", "Buy No", show=True),
        Binding("3", "sell_yes", "Sell Yes", show=True),
        Binding("4", "sell_no", "Sell No", show=True),
    ]
    
    def __init__(self, client: PolymarketClient, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = client
        self.markets = []
        self.selected_index = 0
        self.selected_market = None
        self.orderbook = {"bids": [], "asks": []}
        self.search_query = ""
    
    def compose(self) -> ComposeResult:
        """Compose the UI layout."""
        # Top header with ASCII art
        yield Static(POLYTUI_ASCII_COMPACT)

        # Main content area - use vertical layout for simplicity
        # Left panel - Market list
        yield Static("Loading markets...", id="market-list")

        # Center panel - Market details
        yield Static("Select a market to view details", id="market-detail")

        # Right panel - Order book
        yield Static("Order Book", id="orderbook")

        # Status bar
        yield Static("| Ready. Press 'q' to quit, 'r' to refresh.", id="status")
    
    def on_mount(self) -> None:
        """Initialize the screen."""
        self.load_markets()
    
    def load_markets(self):
        """Load markets from API."""
        self.update_status("Fetching markets...")
        
        try:
            response = self.client.get_markets(limit=50)
            self.markets = response.get("markets", [])
            
            if self.markets:
                self.update_status(f"Loaded {len(self.markets)} markets")
                self.update_market_list()
            else:
                self.update_status("No markets found")
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
    
    def update_market_list(self):
        """Update the market list display."""
        # Create simple text-based market list without Rich markup for compatibility
        content = "=== ACTIVE MARKETS ===\n\n"
        for i, market in enumerate(self.markets[:20], 1):
            question = market.get("question", "N/A")[:50]
            volume = f"${float(market.get('volume', 0)):,.0f}"
            yes_prob = float(market.get("yesPrice", 0.5)) * 100
            content += f"{i:2}. {question}\n"
            content += f"    Vol: {volume} | Yes: {yes_prob:.1f}%\n\n"

        try:
            market_list = self.query_one("#market-list")
            market_list.update(content)
            market_list.refresh()
        except Exception as e:
            print(f"Error updating market list: {e}")
    
    def update_market_detail(self):
        """Update the market detail panel."""
        if not self.selected_market:
            detail = self.query_one("#market-detail")
            detail.update("Select a market to view details")
            return

        market = self.selected_market
        question = market.get("question", "N/A")
        description = market.get("description", "No description available")
        volume = f"${market.get('volume', 0):,.2f}"
        liquidity = f"${market.get('liquidity', 0):,.2f}"
        yes_price = float(market.get("yesPrice", 0)) * 100
        no_price = (1 - float(market.get("yesPrice", 0))) * 100
        end_date = market.get("endDate", "N/A")

        # Get tokens
        tokens = market.get("tokens", [])

        detail_content = f"""=== MARKET DETAILS ===

QUESTION:
{question}

DESCRIPTION:
{description[:200]}...

VOLUME: {volume}
LIQUIDITY: {liquidity}
END DATE: {end_date}

YES PRICE: {yes_price:.1f}%
NO PRICE: {no_price:.1f}%

TOKENS:
"""
        for token in tokens:
            token_id = token.get("tokenId", "N/A")
            outcome = token.get("outcome", "N/A")
            price = float(token.get("price", 0)) * 100
            detail_content += f"  - {outcome}: {price:.1f}% (ID: {token_id[:20]}...)\n"

        detail_content += """

Press ENTER to view order book
Press 1/2/3/4 to trade
"""

        try:
            detail = self.query_one("#market-detail")
            detail.update(detail_content)
            detail.refresh()
        except Exception as e:
            print(f"Error updating market detail: {e}")
    
    def update_orderbook_display(self):
        """Update the order book display."""
        bids = self.orderbook.get("bids", [])
        asks = self.orderbook.get("asks", [])

        # Create simple text-based orderbook display
        content = "=== ORDER BOOK ===\n\n"

        # Show asks (sorted by price ascending)
        content += "ASKS:\n"
        for ask in asks[:10]:
            size = float(ask.get('size', 0))
            price = float(ask.get('price', 0))
            content += f"  Size: {size:.4f} @ Price: {price:.4f}\n"

        # Show spread
        if bids and asks:
            best_bid = float(bids[0].get('price', 0)) if bids else 0
            best_ask = float(asks[0].get('price', 0)) if asks else 1
            spread = best_ask - best_bid
            content += f"\nSPREAD: {spread:.4f}\n"

        # Show bids (sorted by price descending)
        content += "\nBIDS:\n"
        for bid in bids[:10]:
            size = float(bid.get('size', 0))
            price = float(bid.get('price', 0))
            content += f"  Size: {size:.4f} @ Price: {price:.4f}\n"

        try:
            orderbook_panel = self.query_one("#orderbook")
            orderbook_panel.update(content)
            orderbook_panel.refresh()
        except Exception as e:
            print(f"Error updating orderbook: {e}")

    def update_status(self, message: str):
        """Update the status bar."""
        try:
            status = self.query_one("#status")
            status.update(f"| {message}")
            status.refresh()
        except Exception as e:
            print(f"Error updating status: {e}")
    
    def action_cursor_down(self):
        """Move cursor down in market list."""
        if self.markets:
            self.selected_index = (self.selected_index + 1) % len(self.markets)
            self.update_market_list()
    
    def action_cursor_up(self):
        """Move cursor up in market list."""
        if self.markets:
            self.selected_index = (self.selected_index - 1) % len(self.markets)
            self.update_market_list()
    
    def action_select_market(self):
        """Select current market and load details."""
        if self.markets and 0 <= self.selected_index < len(self.markets):
            self.selected_market = self.markets[self.selected_index]
            self.update_market_detail()
            
            # Load order book if tokens available
            tokens = self.selected_market.get("tokens", [])
            if tokens:
                token_id = tokens[0].get("tokenId")
                if token_id:
                    self.orderbook = self.client.get_orderbook(token_id)
                    self.update_orderbook_display()
                    self.update_status(f"Loaded order book for {tokens[0].get('outcome', 'market')}")
    
    def action_clear_selection(self):
        """Clear market selection."""
        self.selected_market = None
        self.selected_index = 0
        self.update_market_detail()
        self.orderbook = {"bids": [], "asks": []}
        self.update_orderbook_display()
    
    def action_refresh(self):
        """Refresh market data."""
        self.load_markets()
    
    def action_search(self):
        """Activate search mode."""
        self.update_status("Search: Type to filter markets...")
    
    def action_quit(self):
        """Quit the application."""
        self.app.exit()
    
    def action_buy_yes(self):
        """Buy Yes action."""
        if self.selected_market:
            self.update_status("BUY YES - Use web interface or API for trading")
    
    def action_buy_no(self):
        """Buy No action."""
        if self.selected_market:
            self.update_status("BUY NO - Use web interface or API for trading")
    
    def action_sell_yes(self):
        """Sell Yes action."""
        if self.selected_market:
            self.update_status("SELL YES - Use web interface or API for trading")
    
    def action_sell_no(self):
        """Sell No action."""
        if self.selected_market:
            self.update_status("SELL NO - Use web interface or API for trading")


# ============================================================================
# MAIN APP
# ============================================================================

class PolyTUIApp(App):
    """PolyTUI - Polymarket Terminal User Interface."""
    
    TITLE = "PolyTUI - Polymarket Terminal Interface"
    SUB_TITLE = "Prediction Markets Terminal"
    
    CSS = """
    Screen {
        background: #1e1e1e;
    }

    Static {
        color: #ffffff;
        padding: 1 2;
    }

    #status {
        dock: bottom;
        height: 1;
        background: #252526;
        color: #cccccc;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("ctrl+c", "quit", "Quit", show=True),
    ]
    
    def __init__(self, agent_mode: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent_mode = agent_mode
        self.client = PolymarketClient()
    
    def compose(self) -> ComposeResult:
        """Compose the application."""
        yield Header(show_clock=True)
        yield PolyTUIScreen(self.client)
        yield Footer()
    
    def on_mount(self) -> None:
        """Handle app mount."""
        if self.agent_mode:
            self.update_status("Running in AGENT mode")
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


# ============================================================================
# AGENT MODE FUNCTIONS
# ============================================================================

def run_agent_mode(args):
    """Run in headless agent mode."""
    client = PolymarketClient()
    
    if args.list_markets:
        # List markets
        response = client.get_markets(limit=args.limit)
        print(json.dumps(response, indent=2))
        return
    
    if args.market_id:
        # Get specific market
        market = client.get_market(args.market_id)
        print(json.dumps(market, indent=2))
        return
    
    if args.orderbook:
        # Get orderbook
        orderbook = client.get_orderbook(args.orderbook)
        print(json.dumps(orderbook, indent=2))
        return
    
    if args.price:
        # Get price
        price = client.get_price(args.price)
        print(json.dumps(price, indent=2))
        return
    
    if args.trade:
        # Place a trade
        if not args.token_id or not args.side or not args.amount or not args.trade_price:
            print(json.dumps({"error": "Missing required arguments: --token-id, --side, --amount, --price"}, indent=2))
            return
        
        # Validate price
        if args.trade_price < 0 or args.trade_price > 1:
            print(json.dumps({"error": "Price must be between 0 and 1"}, indent=2))
            return
        
        # Place the order
        result = client.place_order(args.token_id, args.side.upper(), args.amount, args.trade_price)
        print(json.dumps(result, indent=2))
        return
    
    # Default: list markets
    response = client.get_markets(limit=args.limit)
    print(json.dumps(response, indent=2))


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="PolyTUI - Polymarket Terminal User Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  polytui                    # Run interactive TUI
  polytui --agent --list     # List markets in JSON (agent mode)
  polytui --agent --limit 10 # List top 10 markets
  polytui --agent --market-id <id>  # Get specific market details
  polytui --agent --orderbook <token_id>  # Get orderbook
        """
    )
    
    parser.add_argument(
        "--agent",
        action="store_true",
        help="Run in headless agent mode (returns JSON)"
    )
    parser.add_argument(
        "--list",
        dest="list_markets",
        action="store_true",
        help="List markets (agent mode)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Number of markets to fetch (default: 20)"
    )
    parser.add_argument(
        "--market-id",
        type=str,
        help="Get specific market by condition ID"
    )
    parser.add_argument(
        "--orderbook",
        type=str,
        help="Get orderbook for token ID"
    )
    parser.add_argument(
        "--price",
        type=str,
        help="Get price for token ID"
    )
    parser.add_argument(
        "--trade",
        action="store_true",
        help="Place a trade (requires --token-id, --side, --amount, --price)"
    )
    parser.add_argument(
        "--token-id",
        type=str,
        help="Token ID for trading"
    )
    parser.add_argument(
        "--side",
        type=str,
        choices=["buy", "sell"],
        help="Trade side: buy or sell"
    )
    parser.add_argument(
        "--amount",
        type=float,
        help="Trade amount"
    )
    parser.add_argument(
        "--trade-price",
        type=float,
        help="Limit price for trade (0.0-1.0)"
    )
    
    args = parser.parse_args()
    
    if args.agent:
        # Run in agent/headless mode
        run_agent_mode(args)
    else:
        # Run interactive TUI
        app = PolyTUIApp()
        app.run()


if __name__ == "__main__":
    main()
