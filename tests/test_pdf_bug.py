import unittest
import os

class TestPDFBug(unittest.TestCase):
    def test_pdf_generation_is_not_automatic(self):
        """Verify 'Generating PDF Report' text is completely removed from the frontend loaders."""
        assessment_paths = [
            "c:/CAREER DNA/backend/templates/assessment.html",
            "c:/CAREER DNA/frontend/templates/assessment.html"
        ]
        
        for path in assessment_paths:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.assertNotIn("Generating PDF Report", content, f"Bug present in {path}")
                    self.assertNotIn("Finalizing career profile DNA details.", content, f"Bug present in {path}")

    def test_back_arrow_navigation_exists(self):
        """Verify the explicit back arrow element and its dashboard routing logic exist."""
        result_paths = [
            "c:/CAREER DNA/backend/templates/result.html",
            "c:/CAREER DNA/frontend/templates/result.html"
        ]
        
        for path in result_paths:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.assertIn('id="backToDashboard"', content, f"Back arrow missing in {path}")
                    self.assertIn('window.location.href = "/welcome";', content, f"Back arrow logic missing in {path}")
                    self.assertIn('event.preventDefault();', content, f"Prevention logic missing in {path}")

if __name__ == '__main__':
    unittest.main()
