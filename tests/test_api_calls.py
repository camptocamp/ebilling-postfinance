# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import os
from ebilling_postfinance import ebilling_postfinance


class TestApiCalls:
    @classmethod
    def setup_class(cls):
        cls.biller_id = os.getenv("BILLER_ID", "1234")
        cls.service = ebilling_postfinance.WebService(
            True,
            os.getenv("POSTFINANCE_USER", "user"),
            os.getenv("POSTFINANCE_PWD", "pwd"),
            cls.biller_id
        )

    def test_ping(self):
        res = self.service.ping()
        assert res == self.biller_id
