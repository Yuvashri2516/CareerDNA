import sys
import os
import unittest
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app

class TestProfileEndpoint(unittest.TestCase):

    def setUp(self):
        app.app.config['TESTING'] = True
        self.client = app.app.test_client()

    def test_profile_completeness(self):
        user_name = f"TestUser_{uuid.uuid4().hex}"
        
        # New user
        res = self.client.get('/api/profile', headers={'X-User-Name': user_name})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue('completion' in data)
        self.assertIsInstance(data['completion'], dict)
        self.assertEqual(data['completion']['completion_percentage'], 0)
        
        # Partially completed profile
        payload = {
            "education_level": "Bachelor's Degree",
            "bio": "Hello World"
        }
        res_put = self.client.put('/api/profile', json=payload, headers={'X-User-Name': user_name})
        self.assertEqual(res_put.status_code, 200)
        data_put = res_put.get_json()
        self.assertTrue('completion' in data_put)
        self.assertIsInstance(data_put['completion'], dict)
        self.assertGreater(data_put['completion']['completion_percentage'], 0)

if __name__ == '__main__':
    unittest.main()
