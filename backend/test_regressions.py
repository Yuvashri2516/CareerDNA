import unittest
import json
import app
import career_service

class RegressionTests(unittest.TestCase):
    def test_bug_2_back_arrow_navigation(self):
        # Verify that history.replaceState is called before form submission in assessment.html
        with open("c:/CAREER DNA/backend/templates/assessment.html", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn('history.replaceState(null, "", "/welcome");', content, 
                      "Bug 2 not fixed: history.replaceState not found in assessment.html")

    def test_bug_1_soft_skills_capabilities(self):
        # We test the endpoint by injecting a mock profile and asserting the capability score
        app.app.config['TESTING'] = True
        self.client = app.app.test_client()
        
        # Mocking auth and profile
        def mock_get_auth_user():
            return "test_user"
        
        app.get_auth_user = mock_get_auth_user
        
        original_get_profile = career_service.get_user_profile
        def mock_get_user_profile(username):
            return {
                "tech_skills": [
                    {"name": "Communication", "level": "Advanced"},
                    {"name": "Python", "level": "Beginner"}
                ]
            }
        career_service.get_user_profile = mock_get_user_profile
        
        original_get_dims = career_service.get_assessment_dimensions
        def mock_get_assessment_dimensions(username):
            return {"communication": 20} # should add 20 * 0.5 = 10 to communication
        career_service.get_assessment_dimensions = mock_get_assessment_dimensions

        response = self.client.get('/api/career-analytics')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        capabilities = data.get("skills_capability", {})
        
        # Communication is advanced -> val=90. dims adds 20*0.5=10. Total=100 (min 100).
        self.assertEqual(capabilities.get("Communication"), 100, "Soft skill was not processed correctly!")
        
        # Python is beginner -> val=40. dims adds 0. Total=40
        self.assertEqual(capabilities.get("Coding"), 40, "Coding skill was not processed correctly!")

        # Restore
        career_service.get_user_profile = original_get_profile
        career_service.get_assessment_dimensions = original_get_dims

if __name__ == '__main__':
    unittest.main()
