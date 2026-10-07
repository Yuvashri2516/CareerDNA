import sys
import os
import unittest
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app

class TestAPIEndpoints(unittest.TestCase):

    def setUp(self):
        app.app.config['TESTING'] = True
        self.client = app.app.test_client()

    def test_career_recommendations_endpoint(self):
        res = self.client.get('/api/career-recommendations')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('ideal_match', data)
        self.assertIn('top_careers', data)
        self.assertEqual(len(data['top_careers']), 5)

    def test_career_detail_endpoint(self):
        res = self.client.get('/api/career/data-scientist')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('match_analysis', data)

    def test_career_skills_endpoint(self):
        res = self.client.get('/api/career/software-engineer/skills')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('skill_analysis', data)
        self.assertIn('top_3_to_learn_next', data['skill_analysis'])

    def test_career_roadmap_endpoint(self):
        res = self.client.get('/api/career/ai-engineer/roadmap')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('stages', data['roadmap'])

    def test_career_market_endpoint(self):
        res = self.client.get('/api/career/data-scientist/market')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('market_data', data)
        self.assertIn('source', data['market_data'])

    def test_internships_endpoint(self):
        res = self.client.get('/api/internships')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('opportunities', data)

    def test_readiness_endpoint(self):
        res = self.client.get('/api/readiness')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('readiness', data)

    def test_career_compare_endpoint(self):
        res = self.client.get('/api/career/compare?ids=data-scientist,ai-engineer')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['comparison']), 2)

    def test_dashboard_summary_endpoint(self):
        res = self.client.get('/api/dashboard-summary')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('ideal_career', data)
        self.assertIn('profile_completion', data)

    def test_chat_personalized_endpoint(self):
        import career_service
        career_service.add_user_skill('test_user', 'Python', 'Advanced')
        career_service.add_user_skill('test_user', 'SQL', 'Intermediate')
        career_service.save_assessment_dimensions('test_user', {'tech_focus': 80})

        questions = [
            ("explain about skill tracker", "helps you monitor your current skills"),
            ("what is skill tracker", "identify the skills you need to improve"),
            ("what skills am I missing?", "Missing Gaps (Priority)"),
            ("how can I improve Python?", "project-based approach"),
            ("what is my top career?", "is currently your strongest match at"),
            ("why is software engineer my top match?", "because your profile aligns strongly"),
            ("explain learning roadmap", "step-by-step personalized guide"),
            ("what is resume builder?", "clean, ATS-friendly resume layout")
        ]
        
        responses = []
        for q, expected_snippet in questions:
            res = self.client.post('/api/chat?user_name=test_user', json={'message': q})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            reply = data.get('reply', '')
            self.assertTrue(len(reply) > 0)
            self.assertIn(expected_snippet.lower(), reply.lower(), f"Failed on '{q}', got: {reply}")
            responses.append(reply)

    def test_chat_new_user_no_assessment(self):
        new_user = 'brand_new_user_12345'
        res1 = self.client.post(f'/api/chat?user_name={new_user}', json={'message': 'What career is best for me?'})
        self.assertEqual(res1.status_code, 200)
        data1 = res1.get_json()
        self.assertIn("don't have enough information", data1.get('reply', ''))

        res2 = self.client.post(f'/api/chat?user_name={new_user}', json={'message': 'What skills am I missing?'})
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()
        self.assertIn("isn't available yet", data2.get('reply', ''))

if __name__ == '__main__':
    unittest.main()
