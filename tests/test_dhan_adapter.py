"""Tests for DhanAdapter and broker abstraction layer."""

import configparser
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from broker_adapter import (
    BaseBrokerAdapter,
    DhanAdapter,
    KiteAdapter,
    create_broker_adapter,
    get_configured_broker_name,
)


class TestDhanAdapter(unittest.TestCase):
    """Unit tests for DhanAdapter functionality and normalization."""

    def setUp(self):
        self.adapter = DhanAdapter(
            client_id="1000000001",
            access_token="test_jwt_access_token_12345",
            live_trading=False,
        )

    def test_broker_name(self):
        self.assertEqual(self.adapter.broker_name, "dhan")

    def test_profile(self):
        profile = self.adapter.profile()
        self.assertEqual(profile["user_id"], "1000000001")
        self.assertEqual(profile["broker"], "DhanHQ")

    def test_margins_normalization(self):
        mock_dhan = MagicMock()
        mock_dhan.get_fund_limits.return_value = {
            "status": "success",
            "data": {
                "availableBalance": 250000.50,
                "sodLimit": 200000.0,
                "utilizedAmount": 50000.0,
            },
        }
        self.adapter._dhan = mock_dhan
        margins = self.adapter.margins()

        self.assertIn("equity", margins)
        equity = margins["equity"]
        self.assertEqual(equity["net"], 250000.50)
        self.assertEqual(equity["available"]["cash"], 250000.50)
        self.assertEqual(equity["available"]["opening_balance"], 200000.0)
        self.assertEqual(equity["utilised"]["debits"], 50000.0)

    def test_positions_normalization(self):
        mock_dhan = MagicMock()
        mock_dhan.get_positions.return_value = {
            "status": "success",
            "data": [
                {
                    "securityId": "12345",
                    "tradingSymbol": "NIFTY24SEP25000CE",
                    "positionType": "NRML",
                    "exchangeSegment": "NSE_FNO",
                    "netQty": -75,
                    "buyQty": 0,
                    "sellQty": 75,
                    "buyAvg": 0.0,
                    "sellAvg": 120.50,
                    "costPrice": 120.50,
                    "lastTradedPrice": 95.0,
                    "realizedProfit": 0.0,
                    "unrealizedProfit": 1912.50,
                }
            ],
        }
        self.adapter._dhan = mock_dhan
        pos_data = self.adapter.positions()

        self.assertIn("net", pos_data)
        net_pos = pos_data["net"]
        self.assertEqual(len(net_pos), 1)
        item = net_pos[0]
        self.assertEqual(item["tradingsymbol"], "NIFTY24SEP25000CE")
        self.assertEqual(item["quantity"], -75)
        self.assertEqual(item["product"], "NRML")
        self.assertEqual(item["instrument_token"], 12345)
        self.assertEqual(item["last_price"], 95.0)
        self.assertEqual(item["pnl"], 1912.50)

    def test_orders_normalization(self):
        mock_dhan = MagicMock()
        mock_dhan.get_order_list.return_value = {
            "status": "success",
            "data": [
                {
                    "orderId": "DHAN101010",
                    "exchangeOrderId": "EX123456",
                    "tradingSymbol": "NIFTY24SEP25000CE",
                    "orderStatus": "TRADED",
                    "transactionType": "SELL",
                    "orderType": "LIMIT",
                    "productType": "NRML",
                    "quantity": 75,
                    "price": 120.50,
                    "triggerPrice": 0.0,
                    "tradedPrice": 120.50,
                    "filledQty": 75,
                    "createTime": "2026-09-27 10:15:00",
                }
            ],
        }
        self.adapter._dhan = mock_dhan
        orders = self.adapter.orders()

        self.assertEqual(len(orders), 1)
        order = orders[0]
        self.assertEqual(order["order_id"], "DHAN101010")
        self.assertEqual(order["status"], "COMPLETE")
        self.assertEqual(order["tradingsymbol"], "NIFTY24SEP25000CE")
        self.assertEqual(order["quantity"], 75)

    def test_dry_run_safety_guard(self):
        # When live_trading is False, place_order must simulate and never call self._dhan.place_order
        mock_dhan = MagicMock()
        self.adapter._dhan = mock_dhan
        self.adapter.live_trading = False

        order_id = self.adapter.place_order(
            tradingsymbol="NIFTY24SEP25000CE",
            transaction_type="BUY",
            quantity=75,
            price=100.0,
        )

        self.assertTrue(order_id.startswith("SIM_DHAN_"))
        mock_dhan.place_order.assert_not_called()

    def test_create_broker_adapter_factory(self):
        cfg = configparser.ConfigParser()
        cfg.add_section("broker")
        cfg.set("broker", "name", "dhan")
        cfg.add_section("dhan_login_details")
        cfg.set("dhan_login_details", "client_id", "1000000001")
        cfg.set("dhan_login_details", "access_token", "test_token_abc")
        cfg.add_section("safety")
        cfg.set("safety", "live_trading", "false")

        adapter = create_broker_adapter(config=cfg)
        self.assertIsInstance(adapter, DhanAdapter)
        self.assertEqual(adapter.broker_name, "dhan")
        self.assertEqual(adapter.client_id, "1000000001")

    def test_setup_wizard_form_validation(self):
        try:
            import flask
        except ImportError:
            sys.modules["flask"] = MagicMock()
        try:
            import werkzeug.security
        except ImportError:
            sys.modules["werkzeug"] = MagicMock()
            sys.modules["werkzeug.security"] = MagicMock()
        import setup_wizard

        # Missing dhan client id
        err = setup_wizard._validate_form({
            "broker": "dhan",
            "client_id": "",
            "access_token": "valid_token_12345",
            "username": "admin",
            "password": "password123",
            "password_confirm": "password123",
        })
        self.assertIsNotNone(err)
        self.assertIn("Dhan Client ID", err)

        # Valid dhan form
        err_ok = setup_wizard._validate_form({
            "broker": "dhan",
            "client_id": "1000000001",
            "access_token": "valid_token_12345",
            "username": "admin",
            "password": "password123",
            "password_confirm": "password123",
        })
        self.assertIsNone(err_ok)


if __name__ == "__main__":
    unittest.main()
