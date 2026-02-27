import unittest
from unittest.mock import patch

from scripts import m3u_core


class Response:
    def __init__(self, code):
        self.status_code = code

    def close(self):
        return None


class TestM3UCore(unittest.TestCase):
    def test_parse_m3u_entries_preserves_commas_and_defaults(self):
        content = """#EXTM3U
#EXTINF:-1 tvg-logo="logo1",Alpha, Beta
http://a.example/stream.m3u8
#EXTINF:-1 group-title="News" tvg-logo="logo2",Gamma
http://b.example/stream.m3u8
"""

        entries = m3u_core.parse_m3u_entries(content, default_group_title="Others")

        self.assertEqual(
            entries,
            [
                {
                    "group_title": "Others",
                    "tvg_logo": "logo1",
                    "name": "Alpha, Beta",
                    "url": "http://a.example/stream.m3u8",
                },
                {
                    "group_title": "News",
                    "tvg_logo": "logo2",
                    "name": "Gamma",
                    "url": "http://b.example/stream.m3u8",
                },
            ],
        )

    def test_normalize_m3u_content_dedupes_and_sorts_without_reachability_checks(self):
        content = """#EXTM3U
#EXTINF:-1 group-title="B" tvg-logo="",Zed
http://z.example/live.m3u8
#EXTINF:-1 group-title="A" tvg-logo="",Alpha
http://a.example/live.m3u8
#EXTINF:-1 group-title="A" tvg-logo="",Alpha dup
http://a.example/live.m3u8
#EXTINF:-1 group-title="A" tvg-logo="",Skip me
https://live-iptv.github.io/youtube_live/assets/info.m3u8
"""

        output = m3u_core.normalize_m3u_content(
            content,
            default_group_title="Others",
            sort_keys=("group_title", "name"),
            check_reachability=False,
        )

        self.assertEqual(
            output,
            "\n".join(
                [
                    "#EXTM3U",
                    '#EXTINF:-1 group-title="A" tvg-logo="",Alpha',
                    "http://a.example/live.m3u8",
                    '#EXTINF:-1 group-title="B" tvg-logo="",Zed',
                    "http://z.example/live.m3u8",
                ]
            ),
        )

    @patch("scripts.m3u_core.request_with_retries")
    def test_is_url_reachable_falls_back_to_get_on_405(self, mock_request_with_retries):
        calls = []

        def side_effect(method, _url, **_kwargs):
            calls.append(method)
            return Response(405) if method == "HEAD" else Response(200)

        mock_request_with_retries.side_effect = side_effect

        self.assertTrue(m3u_core.is_url_reachable("https://example.com/stream"))
        self.assertEqual(calls, ["HEAD", "GET"])

    @patch("scripts.m3u_core.request_with_retries")
    def test_is_url_reachable_does_not_fallback_for_non_fallback_status(self, mock_request_with_retries):
        calls = []

        def side_effect(method, _url, **_kwargs):
            calls.append(method)
            return Response(404) if method == "HEAD" else Response(200)

        mock_request_with_retries.side_effect = side_effect

        self.assertFalse(m3u_core.is_url_reachable("https://example.com/stream"))
        self.assertEqual(calls, ["HEAD"])

    def test_extract_json_entries_with_filters_and_stop_after_first_match(self):
        json_data = [
            {
                "label": "Malayalam",
                "channels": [
                    {"name": "One", "logo": "l1", "url": "http://one", "category": "Malayalam"},
                    {"name": "Skip", "logo": "l2", "url": "", "category": "Malayalam"},
                ],
            },
            {
                "label": "Malayalam",
                "channels": [
                    {"name": "Two", "logo": "l3", "url": "http://two", "category": "Malayalam"}
                ],
            },
        ]

        entries = m3u_core.extract_json_entries(
            json_data,
            category_filter=lambda category: category.get("label") == "Malayalam",
            channel_filter=lambda _category, channel: bool(channel.get("url")),
            group_title_resolver=lambda _category: "Entertainment",
            stop_after_first_category_match=True,
        )

        self.assertEqual(
            entries,
            [
                {
                    "group_title": "Entertainment",
                    "tvg_logo": "l1",
                    "name": "One",
                    "url": "http://one",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
