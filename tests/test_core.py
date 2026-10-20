"""Unit tests for netcalc.core - run with: python -m unittest discover -s tests"""

import unittest

from netcalc.core import (
    NetcalcError,
    contains,
    host_range,
    parse_address,
    parse_network,
    split,
    summarize,
    usable_hosts,
)


class TestParsing(unittest.TestCase):
    def test_host_bits_are_masked_off(self):
        net = parse_network("192.168.10.77/24")
        self.assertEqual(str(net), "192.168.10.0/24")

    def test_strict_mode_rejects_host_bits(self):
        with self.assertRaises(NetcalcError):
            parse_network("192.168.10.77/24", strict=True)

    def test_invalid_network_raises(self):
        with self.assertRaises(NetcalcError):
            parse_network("999.1.1.0/24")

    def test_invalid_address_raises(self):
        with self.assertRaises(NetcalcError):
            parse_address("not-an-ip")


class TestUsableHosts(unittest.TestCase):
    def test_ipv4_slash_24(self):
        self.assertEqual(usable_hosts(parse_network("192.168.10.0/24")), 254)

    def test_ipv4_slash_30(self):
        self.assertEqual(usable_hosts(parse_network("10.0.0.0/30")), 2)

    def test_ipv4_slash_31_is_point_to_point(self):
        self.assertEqual(usable_hosts(parse_network("10.0.0.0/31")), 2)

    def test_ipv4_slash_32_is_a_single_host(self):
        self.assertEqual(usable_hosts(parse_network("10.0.0.5/32")), 1)

    def test_ipv6_has_no_broadcast(self):
        self.assertEqual(usable_hosts(parse_network("2001:db8::/126")), 4)


class TestHostRange(unittest.TestCase):
    def test_ipv4_range_excludes_network_and_broadcast(self):
        first, last = host_range(parse_network("192.168.10.0/24"))
        self.assertEqual(str(first), "192.168.10.1")
        self.assertEqual(str(last), "192.168.10.254")

    def test_slash_31_uses_both_addresses(self):
        first, last = host_range(parse_network("10.0.0.0/31"))
        self.assertEqual(str(first), "10.0.0.0")
        self.assertEqual(str(last), "10.0.0.1")


class TestSummarize(unittest.TestCase):
    def test_ipv4_summary_fields(self):
        data = summarize(parse_network("192.168.10.0/24"))
        self.assertEqual(data["netmask"], "255.255.255.0")
        self.assertEqual(data["wildcard"], "0.0.0.255")
        self.assertEqual(data["broadcast"], "192.168.10.255")
        self.assertEqual(data["usable_hosts"], 254)
        self.assertTrue(data["is_private"])

    def test_ipv6_summary_has_no_broadcast_key(self):
        data = summarize(parse_network("2001:db8::/64"))
        self.assertNotIn("broadcast", data)
        self.assertNotIn("wildcard", data)
        self.assertEqual(data["version"], 6)


class TestSplit(unittest.TestCase):
    def test_split_into_four(self):
        result = [str(n) for n in split(parse_network("192.168.10.0/24"), 26)]
        self.assertEqual(
            result,
            [
                "192.168.10.0/26",
                "192.168.10.64/26",
                "192.168.10.128/26",
                "192.168.10.192/26",
            ],
        )

    def test_split_is_lazy(self):
        # A /8 into /30 is over 4 million networks; taking two must be instant
        # and must not allocate the whole list.
        gen = split(parse_network("10.0.0.0/8"), 30)
        self.assertEqual(str(next(gen)), "10.0.0.0/30")
        self.assertEqual(str(next(gen)), "10.0.0.4/30")

    def test_prefix_smaller_than_network_raises(self):
        with self.assertRaises(NetcalcError):
            split(parse_network("192.168.10.0/24"), 16)

    def test_prefix_beyond_maximum_raises(self):
        with self.assertRaises(NetcalcError):
            split(parse_network("192.168.10.0/24"), 33)


class TestContains(unittest.TestCase):
    def test_address_inside(self):
        self.assertTrue(
            contains(parse_network("192.168.10.0/24"), parse_address("192.168.10.50"))
        )

    def test_address_outside(self):
        self.assertFalse(
            contains(parse_network("192.168.10.0/24"), parse_address("192.168.11.50"))
        )

    def test_mixed_versions_raise(self):
        with self.assertRaises(NetcalcError):
            contains(parse_network("192.168.10.0/24"), parse_address("2001:db8::1"))


if __name__ == "__main__":
    unittest.main()
