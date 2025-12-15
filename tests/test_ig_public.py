from __future__ import annotations

import json
import unittest
from pathlib import Path

from ig_public.normalize import normalize_posts, normalize_profile
from ig_public.utils import parse_username


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "web_profile_info_sample.json"


class TestParseUsername(unittest.TestCase):
    def test_accepts_at_handle(self) -> None:
        self.assertEqual(parse_username("@NotJustAnalytics"), "notjustanalytics")

    def test_accepts_plain_handle(self) -> None:
        self.assertEqual(parse_username("  NotJustAnalytics  "), "notjustanalytics")

    def test_accepts_instagram_url(self) -> None:
        self.assertEqual(
            parse_username("https://www.instagram.com/NotJustAnalytics/?hl=es"),
            "notjustanalytics",
        )

    def test_rejects_post_urls(self) -> None:
        self.assertEqual(parse_username("https://www.instagram.com/p/ABC123/"), "")


class TestNormalization(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_normalize_profile(self) -> None:
        profile = normalize_profile(self.raw, fetched_at_utc="2020-01-01T00:00:00Z")
        self.assertEqual(profile["username"], "notjustanalytics")
        self.assertEqual(profile["full_name"], "Not Just Analytics")
        self.assertEqual(profile["followers"], 12345)
        self.assertEqual(profile["following"], 678)
        self.assertEqual(profile["media_count"], 100)
        self.assertIn("fetched_at_utc", profile)

    def test_normalize_posts(self) -> None:
        posts = normalize_posts(self.raw, max_posts=24)
        self.assertEqual(len(posts), 2)

        by_shortcode = {post["shortcode"]: post for post in posts}
        self.assertIn("ABC123", by_shortcode)
        self.assertIn("DEF456", by_shortcode)

        first = by_shortcode["ABC123"]
        self.assertEqual(first["permalink"], "https://www.instagram.com/p/ABC123/")
        self.assertEqual(first["likes_count"], 200)
        self.assertEqual(first["comments_count"], 10)
        self.assertEqual(first["caption"], "Hola mundo")
        self.assertTrue(first["taken_at_utc"].endswith("Z"))

        second = by_shortcode["DEF456"]
        self.assertEqual(second["likes_count"], 150)
        self.assertEqual(second["comments_count"], 5)
        self.assertEqual(second["caption"], "Caption fallback")

    def test_tolerates_missing_structure(self) -> None:
        self.assertEqual(normalize_posts({}, max_posts=10), [])
        profile = normalize_profile({})
        self.assertEqual(profile["followers"], 0)
        self.assertEqual(profile["media_count"], 0)


if __name__ == "__main__":
    unittest.main()

