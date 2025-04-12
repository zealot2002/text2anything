import unittest
import sys
import os

# Add the parent directory to the path so we can import the src module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parser import parse_text

class TestParser(unittest.TestCase):
    
    def test_parse_empty_text(self):
        """Test parsing empty text."""
        result = parse_text("")
        self.assertEqual(result["title"], "Empty")
        self.assertEqual(result["topics"], [])
    
    def test_parse_single_line(self):
        """Test parsing a single line."""
        result = parse_text("Root Topic")
        self.assertEqual(result["title"], "Root Topic")
        self.assertEqual(result["topics"], [])
    
    def test_parse_multiple_levels(self):
        """Test parsing multiple hierarchy levels."""
        text = """Root Topic
    Subtopic 1
        Sub-subtopic A
    Subtopic 2"""
        
        result = parse_text(text)
        
        # Check root
        self.assertEqual(result["title"], "Root Topic")
        self.assertEqual(len(result["topics"]), 2)
        
        # Check first subtopic
        subtopic1 = result["topics"][0]
        self.assertEqual(subtopic1["title"], "Subtopic 1")
        self.assertEqual(len(subtopic1["topics"]), 1)
        
        # Check sub-subtopic
        subsubtopic = subtopic1["topics"][0]
        self.assertEqual(subsubtopic["title"], "Sub-subtopic A")
        
        # Check second subtopic
        subtopic2 = result["topics"][1]
        self.assertEqual(subtopic2["title"], "Subtopic 2")
        self.assertEqual(len(subtopic2["topics"]), 0)
    
if __name__ == "__main__":
    unittest.main() 