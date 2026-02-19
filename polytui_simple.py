#!/usr/bin/env python3
"""
PolyTUI - Simple Terminal User Interface for Polymarket
A simpler version that works in any terminal without complex TUI frameworks.
"""

import json
import os
import sys
from datetime import datetime

# Try to load dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ============================================================================
# CONFIGURATION
# ============================================================================

CLOB_API_BASE = "https://clob.polymarket.com"
GAMMA_API_BASE = "https://gamma-api.polymarket.com"
DATA_API_BASE = "https://data-api.polymarket.com"

# ============================================================================
# API CLIENT
# ============================================================================

class PolymarketClient:
    """Client for interacting with Polymarket APIs."""

    def __init__(self):
        import requests
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        self.api_key = os.getenv("POLY_API_KEY")
        self.api_secret = os.getenv("POLY_API_SECRET")
        self.private_key = os.getenv("ETHEREUM_PRIVATE_KEY")
        self.is_authenticated = bool(self.api_key and self.private_key)

    def get_markets(self, limit: int = 50, active_only: bool = True):
        """Fetch active markets from Gamma API."""
        import requests
        params = {"limit": limit}
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
            markets = data if isinstance(data, list) else data.get("markets", [])
            return {"markets": markets, "cursor": None}
        except Exception as e:
            print(f"Error fetching markets: {e}")
            return {"markets": [], "cursor": None}

    def get_market(self, condition_id: str):
        """Fetch detailed market information."""
        import requests
        try:
            response = self.session.get(
                f"{GAMMA_API_BASE}/markets",
                params={"conditionId": condition_id},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            markets = data if isinstance(data, list) else data.get("markets", [])
            return markets[0] if markets else {}
        except Exception as e:
            print(f"Error fetching market: {e}")
            return {}

    def get_orderbook(self, token_id: str):
        """Fetch order book for a token."""
        import requests
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

    def get_price(self, token_id: str):
        """Fetch current price for a token."""
        import requests
        try:
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


# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Print the header with ASCII art."""
    print("""
+========================================+
|           PolyTUI v1.0                |
|   Polymarket Terminal Interface       |
+========================================+
""")


def print_market(market, index):
    """Print a single market."""
    question = market.get("question", "N/A")[:55]
    volume = f"${float(market.get('volume', 0)):,.0f}"
    liquidity = f"${float(market.get('liquidity', 0)):,.0f}"

    # Get yes price from outcomePrices
    try:
        outcome_prices = json.loads(market.get("outcomePrices", '["0.5", "0.5"]'))
        yes_price = float(outcome_prices[0]) * 100 if len(outcome_prices) > 0 else 50
    except:
        yes_price = 50

    print(f"  [{index}] {question}")
    print(f"      Vol: {volume:>12} | Liq: {liquidity:>12} | Yes: {yes_price:>5.1f}%")


def print_market_detail(market):
    """Print detailed market information."""
    question = market.get("question", "N/A")
    description = market.get("description", "No description available")
    volume = f"${float(market.get('volume', 0)):,.2f}"
    liquidity = f"${float(market.get('liquidity', 0)):,.2f}"
    end_date = market.get("endDate", "N/A")

    # Get prices
    try:
        outcome_prices = json.loads(market.get("outcomePrices", '["0.5", "0.5"]'))
        yes_price = float(outcome_prices[0]) * 100 if len(outcome_prices) > 0 else 50
        no_price = float(outcome_prices[1]) * 100 if len(outcome_prices) > 1 else 50
    except:
        yes_price = 50
        no_price = 50

    # Get token IDs
    token_ids_str = market.get("clobTokenIds", "[]")
    try:
        token_ids = json.loads(token_ids_str)
    except:
        token_ids = []

    print("\n" + "=" * 60)
    print("MARKET DETAILS")
    print("=" * 60)
    print(f"\nQuestion: {question}")
    print(f"\nDescription: {description[:300]}...")
    print(f"\nVolume: {volume}")
    print(f"Liquidity: {liquidity}")
    print(f"End Date: {end_date}")
    print(f"\nYes Price: {yes_price:.1f}%")
    print(f"No Price: {no_price:.1f}%")

    if token_ids:
        print(f"\nToken IDs:")
        print(f"  Yes: {token_ids[0] if len(token_ids) > 0 else 'N/A'}")
        print(f"  No:  {token_ids[1] if len(token_ids) > 1 else 'N/A'}")

    print("\n" + "=" * 60)


def print_orderbook(orderbook, token_id):
    """Print order book."""
    bids = orderbook.get("bids", [])
    asks = orderbook.get("asks", [])

    print("\n" + "=" * 40)
    print("ORDER BOOK")
    print("=" * 40)

    # Show asks (lowest prices first)
    print("\nASKS (Sell Orders):")
    if asks:
        for ask in asks[:5]:
            size = float(ask.get('size', 0))
            price = float(ask.get('price', 0))
            print(f"  Price: {price:.4f} | Size: {size:.2f}")
    else:
        print("  No asks available")

    # Show spread
    if bids and asks:
        best_bid = float(bids[0].get('price', 0)) if bids else 0
        best_ask = float(asks[0].get('price', 0)) if asks else 1
        spread = best_ask - best_bid
        print(f"\nSpread: {spread:.4f}")

    # Show bids (highest prices first)
    print("\nBIDS (Buy Orders):")
    if bids:
        for bid in bids[:5]:
            size = float(bid.get('size', 0))
            price = float(bid.get('price', 0))
            print(f"  Price: {price:.4f} | Size: {size:.2f}")
    else:
        print("  No bids available")

    print("=" * 40)


# ============================================================================
# INTERACTIVE MODE
# ============================================================================

def run_interactive():
    """Run the interactive TUI."""
    client = PolymarketClient()

    # Fetch markets
    print_header()
    print("Loading markets...")

    result = client.get_markets(limit=30)
    markets = result.get("markets", [])

    if not markets:
        print("No markets found!")
        return

    selected_index = 0

    while True:
        clear_screen()
        print_header()

        # Print markets list
        print("\nACTIVE MARKETS")
        print("-" * 60)
        for i, market in enumerate(markets[:15]):
            marker = ">" if i == selected_index else " "
            print(f"{marker} [{i+1:2}] {market.get('question', 'N/A')[:50]}")

        print("-" * 60)
        print("[n] Next page | [p] Previous | [q] Quit")
        print("[Enter] View details | [o] View orderbook")

        # Get selected market
        if 0 <= selected_index < len(markets):
            market = markets[selected_index]
            print_market_detail(market)

        # Get user input
        try:
            choice = input("\n> ").strip().lower()
        except EOFError:
            break

        if choice == 'q':
            break
        elif choice == 'n':
            selected_index = min(selected_index + 15, len(markets) - 1)
        elif choice == 'p':
            selected_index = max(selected_index - 15, 0)
        elif choice == 'o' and 0 <= selected_index < len(market):
            # Show orderbook
            token_ids_str = markets[selected_index].get("clobTokenIds", "[]")
            try:
                token_ids = json.loads(token_ids_str)
                if token_ids:
                    token_id = token_ids[0]
                    orderbook = client.get_orderbook(token_id)
                    print_orderbook(orderbook, token_id)
                    input("\nPress Enter to continue...")
            except:
                print("No token IDs available for this market")
                input("\nPress Enter to continue...")
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(markets):
                selected_index = idx


# ============================================================================
# MAIN
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="PolyTUI - Polymarket Terminal Interface")
    parser.add_argument("--agent", action="store_true", help="Run in agent/headless mode")
    parser.add_argument("--list", dest="list_markets", action="store_true", help="List markets")
    parser.add_argument("--limit", type=int, default=10, help="Number of markets")
    parser.add_argument("--market-id", type=str, help="Get specific market")
    parser.add_argument("--orderbook", type=str, help="Get orderbook for token")
    parser.add_argument("--price", type=str, help="Get price for token")

    args = parser.parse_args()

    client = PolymarketClient()

    if args.agent or args.list_markets:
        # Agent mode - output JSON
        result = client.get_markets(limit=args.limit)
        print(json.dumps(result, indent=2))
    elif args.market_id:
        market = client.get_market(args.market_id)
        print(json.dumps(market, indent=2))
    elif args.orderbook:
        orderbook = client.get_orderbook(args.orderbook)
        print(json.dumps(orderbook, indent=2))
    elif args.price:
        price = client.get_price(args.price)
        print(json.dumps(price, indent=2))
    else:
        # Interactive mode
        run_interactive()


if __name__ == "__main__":
    main()
