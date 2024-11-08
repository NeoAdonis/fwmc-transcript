"""Unit tests for create_morning_transcript.py."""

import unittest
from morning import create_transcript


class TestMorningCreateMorningTranscriptMethods(unittest.TestCase):
    """Unit tests class"""

    def test_get_metadata(self):
        """Test get_metadata function"""
        metadata = create_transcript.get_metadata("morning/audio/20230731", "20230731")
        self.assertEqual(metadata["episode"], "0")
        self.assertEqual(metadata["isSpecial"], False)
        self.assertEqual(metadata["date"], "2023-07-31")
        self.assertEqual(metadata["id"], "Qd7ohtlOOkQ")
        metadata = create_transcript.get_metadata("morning/audio/20240214", "20240214")
        self.assertEqual(metadata["episode"], "BAU-lentine's day")
        self.assertEqual(metadata["isSpecial"], True)
        self.assertEqual(metadata["date"], "2024-02-14")
        self.assertEqual(metadata["id"], "nMl8WQ1Iuls")


if __name__ == "__main__":
    unittest.main()
