"""Unified Broker Adapter Layer for UI Trading System.

Provides a unified interface allowing UI Trading System to trade seamlessly
via either Zerodha Kite Connect or DhanHQ v2, controlled by the `[broker]`
section in configfile.ini.
"""

from __future__ import annotations

import configparser
import logging
import os
import sqlite3
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "instruments.db")
CONFIG_PATH = os.path.join(BASE_DIR, "configfile.ini")

logger = logging.getLogger(__name__)


class BaseBrokerAdapter(ABC):
    """Abstract base class establishing the standard broker contract."""

    @property
    @abstractmethod
    def broker_name(self) -> str:
        """Returns the broker name ('kite' or 'dhan')."""
        pass

    @abstractmethod
    def profile(self) -> Dict[str, Any]:
        """Fetch user profile."""
        pass

    @abstractmethod
    def margins(self) -> Dict[str, Any]:
        """Fetch account fund limits / margins normalized to Kite format."""
        pass

    @abstractmethod
    def positions(self) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch open positions normalized to {'net': [...], 'day': [...]}."""
        pass

    @abstractmethod
    def orders(self) -> List[Dict[str, Any]]:
        """Fetch order book."""
        pass

    @abstractmethod
    def order_history(self, order_id: str) -> List[Dict[str, Any]]:
        """Fetch status history for a specific order."""
        pass

    @abstractmethod
    def place_order(
        self,
        variety: str = "regular",
        exchange: str = "NFO",
        tradingsymbol: str = "",
        transaction_type: str = "BUY",
        quantity: int = 0,
        product: str = "NRML",
        order_type: str = "LIMIT",
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        tag: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Place an order. Returns order ID."""
        pass

    @abstractmethod
    def modify_order(
        self,
        variety: str = "regular",
        order_id: str = "",
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        order_type: Optional[str] = None,
        trigger_price: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        """Modify an existing open order."""
        pass

    @abstractmethod
    def cancel_order(self, variety: str = "regular", order_id: str = "") -> str:
        """Cancel an open order."""
        pass

    @abstractmethod
    def quote(self, *symbols: str) -> Dict[str, Dict[str, Any]]:
        """Fetch quote data for given symbols."""
        pass

    @abstractmethod
    def instruments(self, segment: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch instruments list."""
        pass

    @abstractmethod
    def ltp(self, *symbols: str) -> Dict[str, Dict[str, float]]:
        """Fetch Last Traded Price (LTP) for given symbols."""
        pass

    @abstractmethod
    def get_gtts(self) -> List[Dict[str, Any]]:
        """Fetch all active GTT / Forever orders."""
        pass

    @abstractmethod
    def place_gtt(
        self,
        trigger_type: str,
        tradingsymbol: str,
        exchange: str,
        trigger_values: List[float],
        last_price: float,
        orders: List[Dict[str, Any]],
    ) -> int:
        """Place a GTT / Forever order."""
        pass

    @abstractmethod
    def modify_gtt(
        self,
        trigger_id: int,
        trigger_type: str,
        tradingsymbol: str,
        exchange: str,
        trigger_values: List[float],
        last_price: float,
        orders: List[Dict[str, Any]],
    ) -> int:
        """Modify a GTT / Forever order."""
        pass

    @abstractmethod
    def delete_gtt(self, trigger_id: int) -> int:
        """Cancel/delete a GTT / Forever order."""
        pass


class KiteAdapter(BaseBrokerAdapter):
    """Adapter wrapping Zerodha Kite Connect."""

    def __init__(self, kite_client: Any) -> None:
        self._kite = kite_client

    @property
    def broker_name(self) -> str:
        return "kite"

    @property
    def raw_client(self) -> Any:
        return self._kite

    def __getattr__(self, name: str) -> Any:
        """Delegate any unhandled methods directly to the underlying KiteConnect client."""
        return getattr(self._kite, name)

    def profile(self) -> Dict[str, Any]:
        return self._kite.profile()

    def margins(self) -> Dict[str, Any]:
        return self._kite.margins()

    def positions(self) -> Dict[str, List[Dict[str, Any]]]:
        return self._kite.positions()

    def orders(self) -> List[Dict[str, Any]]:
        return self._kite.orders()

    def order_history(self, order_id: str) -> List[Dict[str, Any]]:
        return self._kite.order_history(order_id)

    def place_order(
        self,
        variety: str = "regular",
        exchange: str = "NFO",
        tradingsymbol: str = "",
        transaction_type: str = "BUY",
        quantity: int = 0,
        product: str = "NRML",
        order_type: str = "LIMIT",
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        tag: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        return self._kite.place_order(
            variety=variety,
            exchange=exchange,
            tradingsymbol=tradingsymbol,
            transaction_type=transaction_type,
            quantity=quantity,
            product=product,
            order_type=order_type,
            price=price,
            trigger_price=trigger_price,
            tag=tag,
            **kwargs,
        )

    def modify_order(
        self,
        variety: str = "regular",
        order_id: str = "",
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        order_type: Optional[str] = None,
        trigger_price: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        return self._kite.modify_order(
            variety=variety,
            order_id=order_id,
            quantity=quantity,
            price=price,
            order_type=order_type,
            trigger_price=trigger_price,
            **kwargs,
        )

    def cancel_order(self, variety: str = "regular", order_id: str = "") -> str:
        return self._kite.cancel_order(variety=variety, order_id=order_id)

    def quote(self, *symbols: str) -> Dict[str, Dict[str, Any]]:
        return self._kite.quote(*symbols)

    def ltp(self, *symbols: str) -> Dict[str, Dict[str, float]]:
        return self._kite.ltp(*symbols)

    def instruments(self, segment: Optional[str] = None) -> List[Dict[str, Any]]:
        return self._kite.instruments(segment) if segment else self._kite.instruments()

    def get_gtts(self) -> List[Dict[str, Any]]:
        return self._kite.get_gtts()

    def place_gtt(
        self,
        trigger_type: str,
        tradingsymbol: str,
        exchange: str,
        trigger_values: List[float],
        last_price: float,
        orders: List[Dict[str, Any]],
    ) -> int:
        return self._kite.place_gtt(
            trigger_type=trigger_type,
            tradingsymbol=tradingsymbol,
            exchange=exchange,
            trigger_values=trigger_values,
            last_price=last_price,
            orders=orders,
        )

    def modify_gtt(
        self,
        trigger_id: int,
        trigger_type: str,
        tradingsymbol: str,
        exchange: str,
        trigger_values: List[float],
        last_price: float,
        orders: List[Dict[str, Any]],
    ) -> int:
        return self._kite.modify_gtt(
            trigger_id=trigger_id,
            trigger_type=trigger_type,
            tradingsymbol=tradingsymbol,
            exchange=exchange,
            trigger_values=trigger_values,
            last_price=last_price,
            orders=orders,
        )

    def delete_gtt(self, trigger_id: int) -> int:
        return self._kite.delete_gtt(trigger_id=trigger_id)


class DhanAdapter(BaseBrokerAdapter):
    """Adapter wrapping DhanHQ v2 API (`dhanhq.dhanhq`)."""

    INDEX_SECURITY_MAP = {
        "NSE:NIFTY 50": ("13", "IDX_I"),
        "NIFTY 50": ("13", "IDX_I"),
        "NSE:NIFTY BANK": ("25", "IDX_I"),
        "NIFTY BANK": ("25", "IDX_I"),
        "NSE:INDIA VIX": ("21", "IDX_I"),
        "INDIA VIX": ("21", "IDX_I"),
        "BSE:SENSEX": ("51", "IDX_I"),
        "SENSEX": ("51", "IDX_I"),
    }

    def __init__(
        self,
        client_id: str,
        access_token: str,
        live_trading: bool = False,
    ) -> None:
        self.client_id = client_id
        self.access_token = access_token
        self.live_trading = live_trading
        self._dhan: Any = None
        self._init_client()

    def _init_client(self) -> None:
        try:
            from dhanhq import dhanhq, DhanContext
            self._dhan = dhanhq(DhanContext(self.client_id, self.access_token))
        except (ImportError, TypeError, AttributeError):
            try:
                from dhanhq import dhanhq
                self._dhan = dhanhq(self.client_id, self.access_token)
            except ImportError:
                logger.error("dhanhq package not installed. Run: pip install dhanhq")
                self._dhan = None
            except Exception as exc:
                logger.error("Failed to initialize DhanHQ client: %s", exc)
                self._dhan = None
        except Exception as exc:
            logger.error("Failed to initialize DhanHQ client: %s", exc)
            self._dhan = None

    @property
    def broker_name(self) -> str:
        return "dhan"

    @property
    def raw_client(self) -> Any:
        return self._dhan

    def set_access_token(self, token: str) -> None:
        """Update access token and reinitialize client."""
        self.access_token = token
        self._init_client()

    def _lookup_instrument(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Lookup instrument info from local instruments.db."""
        if not os.path.exists(DB_PATH):
            return None
        clean_symbol = symbol.split(":")[-1]
        try:
            conn = sqlite3.connect(DB_PATH, timeout=2.0)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT instrument_token, tradingsymbol, exchange, segment, tick_size, lot_size "
                "FROM instruments WHERE tradingsymbol = ? LIMIT 1",
                (clean_symbol,),
            )
            row = cursor.fetchone()
            conn.close()
            if row:
                return {
                    "security_id": str(row[0]),
                    "tradingsymbol": row[1],
                    "exchange": row[2],
                    "segment": row[3],
                    "tick_size": row[4],
                    "lot_size": row[5],
                }
        except Exception as exc:
            logger.debug("Instrument lookup failed for %s: %s", symbol, exc)
        return None

    def profile(self) -> Dict[str, Any]:
        """Fetch profile from Dhan fund limits or client ID."""
        user_id = self.client_id or "dhan_user"
        user_name = "DhanHQ User"
        if self._dhan:
            try:
                funds = self._dhan.get_fund_limits()
                if isinstance(funds, dict) and funds.get("status") == "success":
                    data = funds.get("data", {})
                    user_name = data.get("dhanClientId", user_id)
            except Exception:
                pass
        return {
            "user_id": user_id,
            "user_name": user_name,
            "broker": "DhanHQ",
            "email": f"{user_id}@dhan.co",
        }

    def margins(self) -> Dict[str, Any]:
        """Normalize Dhan fund limits to KiteConnect margins schema."""
        avail_cash = 0.0
        opening_balance = 0.0
        utilised = 0.0
        if self._dhan:
            try:
                res = self._dhan.get_fund_limits()
                if isinstance(res, dict) and res.get("status") == "success":
                    data = res.get("data", {})
                    avail_cash = float(data.get("availabelBalance", data.get("availableBalance", 0.0)))
                    opening_balance = float(data.get("sodLimit", 0.0))
                    utilised = float(data.get("utilizedAmount", 0.0))
            except Exception as exc:
                logger.warning("Error fetching Dhan fund limits: %s", exc)

        return {
            "equity": {
                "enabled": True,
                "net": avail_cash,
                "available": {
                    "cash": avail_cash,
                    "opening_balance": opening_balance,
                    "collateral": 0.0,
                    "intraday_payin": 0.0,
                },
                "utilised": {
                    "debits": utilised,
                    "exposure": 0.0,
                    "m2m_realised": 0.0,
                    "m2m_unrealised": 0.0,
                    "option_premium": 0.0,
                    "span": 0.0,
                    "holding_sales": 0.0,
                    "turnover": 0.0,
                },
            },
            "commodity": {
                "enabled": False,
                "net": 0.0,
                "available": {"cash": 0.0},
                "utilised": {"debits": 0.0},
            },
        }

    def positions(self) -> Dict[str, List[Dict[str, Any]]]:
        """Normalize Dhan positions to Kite format."""
        net_list: List[Dict[str, Any]] = []
        day_list: List[Dict[str, Any]] = []

        if not self._dhan:
            return {"net": net_list, "day": day_list}

        try:
            res = self._dhan.get_positions()
            raw_positions = []
            if isinstance(res, dict) and res.get("status") == "success":
                raw_positions = res.get("data", [])
            elif isinstance(res, list):
                raw_positions = res

            for pos in raw_positions:
                security_id = str(pos.get("securityId", ""))
                symbol = pos.get("tradingSymbol", pos.get("customSymbol", f"SEC_{security_id}"))
                product_type = pos.get("positionType", "NRML")
                net_qty = int(pos.get("netQty", 0))
                buy_qty = int(pos.get("buyQty", 0))
                sell_qty = int(pos.get("sellQty", 0))
                buy_avg = float(pos.get("buyAvg", 0.0))
                sell_avg = float(pos.get("sellAvg", 0.0))
                cost_price = float(pos.get("costPrice", 0.0))
                ltp = float(pos.get("lastTradedPrice", pos.get("ltp", 0.0)))
                realized_pnl = float(pos.get("realizedProfit", 0.0))
                unrealized_pnl = float(pos.get("unrealizedProfit", 0.0))
                total_pnl = realized_pnl + unrealized_pnl

                norm_pos = {
                    "tradingsymbol": symbol,
                    "exchange": pos.get("exchangeSegment", "NSE_FNO").split("_")[0],
                    "instrument_token": int(security_id) if security_id.isdigit() else 0,
                    "product": product_type,
                    "quantity": net_qty,
                    "overnight_quantity": 0,
                    "multiplier": 1,
                    "average_price": cost_price or buy_avg or sell_avg,
                    "close_price": 0.0,
                    "last_price": ltp,
                    "value": net_qty * ltp,
                    "pnl": total_pnl,
                    "m2m": unrealized_pnl,
                    "unrealised": unrealized_pnl,
                    "realised": realized_pnl,
                    "buy_quantity": buy_qty,
                    "buy_price": buy_avg,
                    "buy_value": buy_qty * buy_avg,
                    "buy_m2m": 0.0,
                    "sell_quantity": sell_qty,
                    "sell_price": sell_avg,
                    "sell_value": sell_qty * sell_avg,
                    "sell_m2m": 0.0,
                    "day_buy_quantity": buy_qty,
                    "day_buy_price": buy_avg,
                    "day_buy_value": buy_qty * buy_avg,
                    "day_sell_quantity": sell_qty,
                    "day_sell_price": sell_avg,
                    "day_sell_value": sell_qty * sell_avg,
                }
                net_list.append(norm_pos)
                day_list.append(norm_pos)

        except Exception as exc:
            logger.error("Failed to fetch/normalize Dhan positions: %s", exc)

        return {"net": net_list, "day": day_list}

    def orders(self) -> List[Dict[str, Any]]:
        """Fetch and normalize order book from Dhan."""
        normalized: List[Dict[str, Any]] = []
        if not self._dhan:
            return normalized

        try:
            res = self._dhan.get_order_list()
            order_list = []
            if isinstance(res, dict) and res.get("status") == "success":
                order_list = res.get("data", [])
            elif isinstance(res, list):
                order_list = res

            for ord_item in order_list:
                status_raw = str(ord_item.get("orderStatus", "")).upper()
                status_mapped = {
                    "CONFIRMED": "OPEN",
                    "TRANSIT": "TRIGGER PENDING",
                    "TRADED": "COMPLETE",
                    "CANCELLED": "CANCELLED",
                    "REJECTED": "REJECTED",
                    "EXPIRED": "CANCELLED",
                }.get(status_raw, status_raw)

                normalized.append({
                    "order_id": str(ord_item.get("orderId", "")),
                    "parent_order_id": None,
                    "exchange_order_id": str(ord_item.get("exchangeOrderId", "")),
                    "placed_by": self.client_id,
                    "variety": "regular",
                    "status": status_mapped,
                    "status_message": ord_item.get("remarks", ""),
                    "tradingsymbol": ord_item.get("tradingSymbol", ord_item.get("customSymbol", "")),
                    "exchange": ord_item.get("exchangeSegment", "NSE_FNO").split("_")[0],
                    "transaction_type": ord_item.get("transactionType", "BUY").upper(),
                    "order_type": ord_item.get("orderType", "LIMIT").upper(),
                    "product": ord_item.get("productType", "NRML").upper(),
                    "quantity": int(ord_item.get("quantity", 0)),
                    "price": float(ord_item.get("price", 0.0)),
                    "trigger_price": float(ord_item.get("triggerPrice", 0.0)),
                    "average_price": float(ord_item.get("tradedPrice", 0.0)),
                    "filled_quantity": int(ord_item.get("filledQty", 0)),
                    "pending_quantity": int(ord_item.get("quantity", 0)) - int(ord_item.get("filledQty", 0)),
                    "cancelled_quantity": 0,
                    "order_timestamp": ord_item.get("createTime", ""),
                    "exchange_timestamp": ord_item.get("exchangeTime", ""),
                    "tag": ord_item.get("correlationId", None),
                })
        except Exception as exc:
            logger.error("Failed to fetch Dhan orders: %s", exc)

        return normalized

    def order_history(self, order_id: str) -> List[Dict[str, Any]]:
        """Fetch single order history."""
        if not self._dhan:
            return []
        try:
            res = self._dhan.get_order_by_id(order_id)
            if isinstance(res, dict) and res.get("status") == "success":
                data = res.get("data", {})
                return [{
                    "order_id": order_id,
                    "status": data.get("orderStatus", "COMPLETE"),
                    "status_message": data.get("remarks", ""),
                    "order_timestamp": data.get("createTime", ""),
                }]
        except Exception as exc:
            logger.debug("Failed to fetch order history for %s: %s", order_id, exc)
        return []

    def place_order(
        self,
        variety: str = "regular",
        exchange: str = "NFO",
        tradingsymbol: str = "",
        transaction_type: str = "BUY",
        quantity: int = 0,
        product: str = "NRML",
        order_type: str = "LIMIT",
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        tag: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Route order to Dhan or simulate if dry-run."""
        order_details = (
            f"[DHAN-ORDER] {transaction_type} {quantity}x {tradingsymbol} "
            f"@{price or 'MKT'} ({order_type}, {product})"
        )

        if not self.live_trading:
            sim_id = f"SIM_DHAN_{int(time.time() * 1000)}"
            logger.info("DRY-RUN SIMULATED ORDER: %s | Generated ID: %s", order_details, sim_id)
            return sim_id

        if not self._dhan:
            raise RuntimeError("DhanHQ client not initialized for live trading.")

        inst = self._lookup_instrument(tradingsymbol)
        if not inst:
            raise ValueError(f"Instrument not found in database for symbol: {tradingsymbol}")

        security_id = inst["security_id"]
        # Map segment
        exchange_segment = "NSE_FNO"
        if "BSE" in exchange or "BFO" in exchange:
            exchange_segment = "BSE_FNO"
        elif exchange == "NSE" and inst.get("segment") == "NSE":
            exchange_segment = "NSE_EQ"

        res = self._dhan.place_order(
            security_id=security_id,
            exchange_segment=exchange_segment,
            transaction_type=transaction_type.upper(),
            quantity=quantity,
            order_type=order_type.upper(),
            product_type=product.upper(),
            price=float(price or 0.0),
            trigger_price=float(trigger_price or 0.0),
            tag=tag or "UITRADE",
        )

        if isinstance(res, dict) and res.get("status") == "success":
            order_id = str(res.get("data", {}).get("orderId", ""))
            logger.info("LIVE DHAN ORDER PLACED: %s | ID: %s", order_details, order_id)
            return order_id
        else:
            err = res.get("remarks", res) if isinstance(res, dict) else str(res)
            logger.error("DhanHQ order placement failed: %s", err)
            raise RuntimeError(f"DhanHQ Order Failed: {err}")

    def modify_order(
        self,
        variety: str = "regular",
        order_id: str = "",
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        order_type: Optional[str] = None,
        trigger_price: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        if not self.live_trading or order_id.startswith("SIM_"):
            logger.info("DRY-RUN SIMULATED MODIFY: %s qty=%s price=%s", order_id, quantity, price)
            return order_id

        if not self._dhan:
            raise RuntimeError("DhanHQ client not initialized.")

        res = self._dhan.modify_order(
            order_id=order_id,
            order_type=order_type or "LIMIT",
            leg_name="ENTRY_LEG",
            quantity=quantity or 0,
            price=float(price or 0.0),
            trigger_price=float(trigger_price or 0.0),
            disclosed_quantity=0,
            validity="DAY",
        )
        if isinstance(res, dict) and res.get("status") == "success":
            return order_id
        err = res.get("remarks", res) if isinstance(res, dict) else str(res)
        raise RuntimeError(f"DhanHQ Modify Order Failed: {err}")

    def cancel_order(self, variety: str = "regular", order_id: str = "") -> str:
        if not self.live_trading or order_id.startswith("SIM_"):
            logger.info("DRY-RUN SIMULATED CANCEL: %s", order_id)
            return order_id

        if not self._dhan:
            raise RuntimeError("DhanHQ client not initialized.")

        res = self._dhan.cancel_order(order_id=order_id)
        if isinstance(res, dict) and res.get("status") == "success":
            return order_id
        err = res.get("remarks", res) if isinstance(res, dict) else str(res)
        raise RuntimeError(f"DhanHQ Cancel Order Failed: {err}")

    def quote(self, *symbols: Any) -> Dict[str, Dict[str, Any]]:
        """Fetch quote data and map to Kite schema."""
        out: Dict[str, Dict[str, Any]] = {}
        if not symbols or not self._dhan:
            return out

        flattened_symbols: List[str] = []
        for item in symbols:
            if isinstance(item, (list, tuple, set)):
                flattened_symbols.extend(str(s) for s in item)
            elif item is not None:
                flattened_symbols.append(str(item))

        sec_map: Dict[str, List[int]] = {}
        sym_lookup: Dict[Tuple[str, str], str] = {}

        for sym in flattened_symbols:
            if sym in self.INDEX_SECURITY_MAP:
                sid, seg = self.INDEX_SECURITY_MAP[sym]
                sec_map.setdefault(seg, []).append(int(sid))
                sym_lookup[(seg, sid)] = sym
            else:
                inst = self._lookup_instrument(sym)
                if inst:
                    sid = inst["security_id"]
                    seg = "NSE_FNO" if "NFO" in inst.get("segment", "") else "NSE_EQ"
                    sec_map.setdefault(seg, []).append(int(sid))
                    sym_lookup[(seg, sid)] = sym

        if not sec_map:
            return out

        try:
            res = self._dhan.quote_data(securities=sec_map)
            if isinstance(res, dict) and res.get("status") == "success":
                data_map = res.get("data", {}).get("data", {})
                for seg, sids in data_map.items():
                    for sid_str, quote_info in sids.items():
                        orig_sym = sym_lookup.get((seg, sid_str))
                        if orig_sym:
                            ltp = float(quote_info.get("last_price", 0.0))
                            ohlc = quote_info.get("ohlc", {})
                            out[orig_sym] = {
                                "instrument_token": int(sid_str) if sid_str.isdigit() else 0,
                                "last_price": ltp,
                                "net_change": float(quote_info.get("net_change", 0.0)),
                                "ohlc": {
                                    "open": float(ohlc.get("open", 0.0)),
                                    "high": float(ohlc.get("high", 0.0)),
                                    "low": float(ohlc.get("low", 0.0)),
                                    "close": float(ohlc.get("close", 0.0)),
                                },
                            }
        except Exception as exc:
            logger.debug("Dhan quote_data error: %s", exc)

        return out

    def ltp(self, *symbols: str) -> Dict[str, Dict[str, float]]:
        quotes = self.quote(*symbols)
        return {sym: {"last_price": q.get("last_price", 0.0)} for sym, q in quotes.items()}

    def instruments(self, segment: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch Dhan scrip master CSV and convert to standard instruments list."""
        import csv
        import urllib.request

        url = "https://images.dhan.co/api-data/api-scrip-master.csv"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        instruments_list = []
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                lines = (line.decode("utf-8", errors="ignore") for line in resp)
                reader = csv.DictReader(lines)
                for row in reader:
                    exch = row.get("SEM_EXM_EXCH_ID", "NSE")
                    inst_type_raw = row.get("SEM_INSTRUMENT_NAME", "")
                    sec_id_str = row.get("SEM_SMST_SECURITY_ID", "")
                    if not sec_id_str:
                        continue
                    token = int(sec_id_str)

                    if exch == "NSE":
                        if inst_type_raw in ("OPTIDX", "OPTSTK"):
                            seg = "NFO-OPT"
                        elif inst_type_raw in ("FUTIDX", "FUTSTK"):
                            seg = "NFO-FUT"
                        else:
                            seg = "NSE"
                    elif exch == "BSE":
                        if inst_type_raw in ("OPTIDX", "OPTSTK"):
                            seg = "BFO-OPT"
                        elif inst_type_raw in ("FUTIDX", "FUTSTK"):
                            seg = "BFO-FUT"
                        else:
                            seg = "BSE"
                    else:
                        seg = exch

                    if segment and seg != segment:
                        continue

                    strike_val = None
                    strike_raw = row.get("SEM_STRIKE_PRICE")
                    if strike_raw and float(strike_raw) > 0:
                        strike_val = float(strike_raw)

                    exp_val = None
                    exp_raw = row.get("SEM_EXPIRY_DATE")
                    if exp_raw and exp_raw.strip():
                        exp_val = exp_raw.strip().split()[0]

                    opt_type = row.get("SEM_OPTION_TYPE")
                    if not opt_type or opt_type == "XX":
                        if "FUT" in inst_type_raw:
                            opt_type = "FUT"
                        else:
                            opt_type = "EQ"

                    symbol = row.get("SEM_CUSTOM_SYMBOL") or row.get("SEM_TRADING_SYMBOL") or f"SEC_{token}"

                    instruments_list.append({
                        "instrument_token": token,
                        "tradingsymbol": symbol,
                        "name": row.get("SM_SYMBOL_NAME", symbol),
                        "expiry": exp_val,
                        "strike": strike_val,
                        "instrument_type": opt_type,
                        "lot_size": int(float(row.get("SEM_LOT_UNITS", 1))),
                        "segment": seg,
                        "exchange": exch,
                        "tick_size": float(row.get("SEM_TICK_SIZE", 0.05)),
                    })
        except Exception as exc:
            logger.error("Failed to download or parse Dhan scrip master: %s", exc)
        return instruments_list

    def get_gtts(self) -> List[Dict[str, Any]]:
        """Fetch and map Dhan Forever orders to Kite GTT schema."""
        gtts: List[Dict[str, Any]] = []
        if not self._dhan:
            return gtts

        try:
            res = self._dhan.get_forever()
            raw_list = []
            if isinstance(res, dict) and res.get("status") == "success":
                raw_list = res.get("data", [])
            elif isinstance(res, list):
                raw_list = res

            for item in raw_list:
                gtts.append({
                    "id": item.get("orderId"),
                    "type": "single",
                    "status": item.get("orderStatus", "active"),
                    "condition": {
                        "exchange": item.get("exchangeSegment", "NSE_FNO").split("_")[0],
                        "tradingsymbol": item.get("tradingSymbol", item.get("customSymbol", "")),
                        "trigger_values": [float(item.get("triggerPrice", 0.0))],
                        "last_price": float(item.get("price", 0.0)),
                    },
                    "orders": [{
                        "transaction_type": item.get("transactionType", "BUY"),
                        "quantity": int(item.get("quantity", 0)),
                        "order_type": item.get("orderType", "LIMIT"),
                        "product": item.get("productType", "NRML"),
                        "price": float(item.get("price", 0.0)),
                    }],
                    "created_at": item.get("createTime", ""),
                })
        except Exception as exc:
            logger.debug("Failed to fetch Dhan forever orders: %s", exc)

        return gtts

    def place_gtt(
        self,
        trigger_type: str,
        tradingsymbol: str,
        exchange: str,
        trigger_values: List[float],
        last_price: float,
        orders: List[Dict[str, Any]],
    ) -> int:
        if not self.live_trading:
            sim_id = int(time.time() * 1000) % 100000000
            logger.info("DRY-RUN SIMULATED GTT PLACEMENT: %s triggers=%s", tradingsymbol, trigger_values)
            return sim_id

        if not self._dhan or not orders:
            raise RuntimeError("Dhan client or order definition missing.")

        inst = self._lookup_instrument(tradingsymbol)
        if not inst:
            raise ValueError(f"Instrument not found for {tradingsymbol}")

        first_order = orders[0]
        res = self._dhan.place_forever(
            security_id=inst["security_id"],
            exchange_segment="NSE_FNO" if "NFO" in exchange else "NSE_EQ",
            transaction_type=first_order.get("transaction_type", "SELL").upper(),
            product_type=first_order.get("product", "NRML").upper(),
            order_type=first_order.get("order_type", "LIMIT").upper(),
            quantity=int(first_order.get("quantity", 0)),
            price=float(first_order.get("price", 0.0)),
            trigger_Price=float(trigger_values[0] if trigger_values else 0.0),
        )
        if isinstance(res, dict) and res.get("status") == "success":
            return int(res.get("data", {}).get("orderId", 0))
        err = res.get("remarks", res) if isinstance(res, dict) else str(res)
        raise RuntimeError(f"Dhan Forever order failed: {err}")

    def modify_gtt(
        self,
        trigger_id: int,
        trigger_type: str,
        tradingsymbol: str,
        exchange: str,
        trigger_values: List[float],
        last_price: float,
        orders: List[Dict[str, Any]],
    ) -> int:
        if not self.live_trading:
            logger.info("DRY-RUN SIMULATED GTT MODIFY: %s", trigger_id)
            return trigger_id
        return trigger_id

    def delete_gtt(self, trigger_id: int) -> int:
        if not self.live_trading:
            logger.info("DRY-RUN SIMULATED GTT DELETE: %s", trigger_id)
            return trigger_id
        if self._dhan:
            self._dhan.cancel_forever(order_id=str(trigger_id))
        return trigger_id


def get_configured_broker_name(config: Optional[configparser.ConfigParser] = None) -> str:
    """Return the active broker name ('kite' or 'dhan') from config."""
    if config is None:
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_PATH):
            config.read(CONFIG_PATH)

    if config.has_section("broker"):
        name = config.get("broker", "name", fallback="").strip().lower()
        if name in ("kite", "dhan"):
            return name

    # Auto-detect if dhan_login_details exists and has non-placeholder values
    if config.has_section("dhan_login_details"):
        cid = config.get("dhan_login_details", "client_id", fallback="").strip()
        if cid and cid not in ("YOUR_CLIENT_ID", "YOUR_DHAN_CLIENT_ID", ""):
            return "dhan"

    return "kite"


def create_broker_adapter(
    config: Optional[configparser.ConfigParser] = None,
    session_data: Optional[Dict[str, Any]] = None,
) -> BaseBrokerAdapter:
    """Factory creating the configured broker adapter."""
    if config is None:
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_PATH):
            config.read(CONFIG_PATH)

    broker_name = get_configured_broker_name(config)
    live_trading = False
    if config.has_section("safety"):
        live_trading = config.getboolean("safety", "live_trading", fallback=False)

    if broker_name == "dhan":
        client_id = ""
        access_token = ""
        if config.has_section("dhan_login_details"):
            client_id = config.get("dhan_login_details", "client_id", fallback="").strip()
            access_token = config.get("dhan_login_details", "access_token", fallback="").strip()

        if session_data and session_data.get("dhan_access_token"):
            access_token = session_data["dhan_access_token"]

        return DhanAdapter(client_id=client_id, access_token=access_token, live_trading=live_trading)

    # Default to Kite
    api_key = ""
    if config.has_section("kite_login_details"):
        api_key = config.get("kite_login_details", "api_key", fallback="").strip()

    from kiteconnect import KiteConnect
    from kite_api_monitor import MonitoredKite

    kite = MonitoredKite(KiteConnect(api_key=api_key), account_id="main")
    if session_data and "access_token" in session_data:
        kite.set_access_token(session_data["access_token"])

    return KiteAdapter(kite)
