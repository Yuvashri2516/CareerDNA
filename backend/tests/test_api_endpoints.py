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
        res = self.client.post('/api/chat', json={'message': 'Which career is right for me?'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('reply', data)

if __name__ == '__main__':
    unittest.main()
