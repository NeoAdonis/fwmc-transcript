"""Unit tests for update_summary_index.py."""

import os
import unittest
from morning import update_summary_index


class TestUpdateSummaryIndexMethods(unittest.TestCase):
    """Unit tests class"""

    def test_load_metadata(self):
        """Test get_metadata function"""
        m = update_summary_index.load_metadata("morning/transcripts/20231013")
        self.assertEqual(m["episode"], "friday the 13th")
        self.assertEqual(m["isSpecial"], True)
        self.assertEqual(m["date"], "2023-10-13")
        self.assertEqual(m["id"], "QW_VwFyUBeU")
        self.assertEqual(m["link"], "https://youtu.be/QW_VwFyUBeU")

    def test_format_episode_filename(self):
        """Test format_episode_filename function"""
        os.chdir("morning/transcripts")
        filename_reg = update_summary_index.format_episode_filename(
            "20201234", {"episode": "123"}
        )
        filename_spaces = update_summary_index.format_episode_filename(
            "20202345", {"episode": "special episode in space"}
        )
        filename_kana = update_summary_index.format_episode_filename(
            "20231229", {"episode": "あさモコLIVE"}
        )
        self.assertEqual(filename_reg, "20201234_123")
        self.assertEqual(filename_spaces, "20202345_special_episode_in_space")
        self.assertEqual(filename_kana, "20231229_ASAMOCOLIVE")

    def test_format_header_line_base(self):
        """Test format_header_line function"""
        line = update_summary_index.format_header_line(
            [
                {"Pattern": r"\btest", "Emoji": "🧪"},
                {"Pattern": r"unit", "Emoji": "❌"},
            ],
            "##",
            "Unit Testing (12:34)",
            "Test Episode",
            "https://youtu.be/jNQXAC9IVRw",
        )
        self.assertEqual(
            line,
            "## 🧪 Unit Testing ([12:34](https://youtu.be/jNQXAC9IVRw?t=12m34s))\n",
        )

    def test_format_header_line_intro(self):
        """Test format_header_line function on an introduction section"""
        line = update_summary_index.format_header_line(
            [{"Pattern": r"test", "Emoji": "🧪"}, {"Pattern": r"intro", "Emoji": "❌"}],
            "##",
            "Introduction (12:34)",
            "Test Episode",
            "https://youtu.be/jNQXAC9IVRw",
        )
        self.assertEqual(
            line,
            "# Test Episode (start: [12:34](https://youtu.be/jNQXAC9IVRw?t=12m34s))\n",
        )

    def test_format_header_line_no_emoji(self):
        """Test format_header_line function on an episode that should not use emoji"""
        line = update_summary_index.format_header_line(
            [
                {"Pattern": r"\btest", "Emoji": "🧪"},
                {"Pattern": r"unit", "Emoji": "❌"},
            ],
            "##",
            "Unit Testing (12:34)",
            "friday the 13th",  # Known no emoji episode
            "https://youtu.be/jNQXAC9IVRw",
        )
        self.assertEqual(
            line,
            "## Unit Testing ([12:34](https://youtu.be/jNQXAC9IVRw?t=12m34s))\n",
        )


if __name__ == "__main__":
    unittest.main()
