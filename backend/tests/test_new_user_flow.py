import sys
import os
import unittest
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app
import career_service

class TestNewUserFlow(unittest.TestCase):

    def setUp(self):
        app.app.config['TESTING'] = True
        self.client = app.app.test_client()
        self.test_username = "test_new_user_xyz"

    def test_new_user_zero_initial_state_and_progression(self):
        # 1. Register new user
        reg_res = self.client.post('/api/register', json={
            "username": self.test_username,
            "password": "Password123!"
        })
        self.assertIn(reg_res.status_code, [201, 409])

        # Login session
        with self.client.session_transaction() as sess:
            sess['user'] = self.test_username

        # 2. Verify NEW USER initial zero state
        profile_res = self.client.get('/api/profile')
        profile_data = profile_res.get_json()
        self.assertTrue(profile_data['success'])
        self.assertEqual(profile_data['completion']['completion_percentage'], 0)

        dash_res = self.client.get('/api/dashboard-summary')
        dash_data = dash_res.get_json()
        self.assertEqual(dash_data['profile_completion'], 0)
        self.assertFalse(dash_data['has_assessment'])
        self.assertFalse(dash_data['has_career_match'])
        self.assertEqual(dash_data['ideal_career'], 'Not calculated')
        self.assertEqual(dash_data['career_readiness_score'], 0)
        self.assertEqual(len(dash_data['top_user_skills']), 0)
        self.assertEqual(dash_data['current_roadmap_stage'], 0)
        self.assertEqual(dash_data['recommended_next_action'], 'Complete your Career Profile')

        achieve_res = self.client.get('/api/achievements')
        achieve_data = achieve_res.get_json()
        self.assertEqual(achieve_data['unlocked_count'], 0)

        # 3. Complete Profile Section
        put_res = self.client.put('/api/profile', json={
            "education_level": "Bachelor's Degree",
            "tech_skills": [{"name": "Python", "level": "Intermediate"}],
            "interests": ["Data Science"],
            "goals": {"desired_career": "Data Scientist"}
        })
        self.assertTrue(put_res.get_json()['success'])

        dash_res2 = self.client.get('/api/dashboard-summary')
        dash_data2 = dash_res2.get_json()
        self.assertGreater(dash_data2['profile_completion'], 0)
        self.assertEqual(dash_data2['recommended_next_action'], 'Take the Career Assessment')

        # 4. Complete Assessment
        assess_res = self.client.post('/api/assessment/dimensions', json={
            "dimensions": {
                "analytical_thinking": 85,
                "creativity": 60,
                "communication": 75,
                "leadership": 70,
                "problem_solving": 90,
                "technical_interest": 95,
                "social_interest": 50,
                "business_interest": 65,
                "research_interest": 80,
                "design_interest": 55,
                "risk_tolerance": 60,
                "work_style_score": 75,
                "learning_preference": 85
            }
        })
        self.assertTrue(assess_res.get_json()['success'])

        dash_res3 = self.client.get('/api/dashboard-summary')
        dash_data3 = dash_res3.get_json()
        self.assertTrue(dash_data3['has_assessment'])
        self.assertTrue(dash_data3['has_career_match'])
        self.assertNotEqual(dash_data3['ideal_career'], 'Not calculated')
        self.assertGreater(dash_data3['ideal_match_score'], 0)
        self.assertGreater(dash_data3['career_readiness_score'], 0)

        # 5. Check Achievements unlocked after actions
        achieve_res2 = self.client.get('/api/achievements')
        achieve_data2 = achieve_res2.get_json()
        self.assertGreater(achieve_data2['unlocked_count'], 0)

if __name__ == '__main__':
    unittest.main()
