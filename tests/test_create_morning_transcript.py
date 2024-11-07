"""Unit tests for create_morning_transcript.py."""

import unittest
from morning import create_morning_transcript


class TestCreateMorningTranscriptMethods(unittest.TestCase):
    """Unit tests class"""

    def test_get_metadata(self):
        """Test get_metadata function"""
        m = create_morning_transcript.get_metadata("morning/audio", "20231013")
        self.assertEqual(m["episode"], "friday the 13th")
        self.assertEqual(m["isSpecial"], True)
        self.assertEqual(m["date"], "2023-10-13")
        self.assertEqual(m["id"], "QW_VwFyUBeU")


if __name__ == "__main__":
    unittest.main()
