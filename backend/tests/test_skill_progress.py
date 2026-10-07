import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app

class TestSkillProgress(unittest.TestCase):

    def setUp(self):
        app.app.config['TESTING'] = True
        self.client = app.app.test_client()

    def test_skill_progress_new_user(self):
        import uuid
        # 1. new/incomplete user -> ideal_match is None
        user_name = f"TestUser_{uuid.uuid4().hex}"
        
        # Verify initial state
        res_get = self.client.get(f'/api/career/software-engineer/skills', headers={'X-User-Name': user_name})
        self.assertEqual(res_get.status_code, 200)
        data_get = res_get.get_json()
        self.assertTrue(data_get['success'])
        
        # Verify it has no strong skills initially
        analysis = data_get['skill_analysis']
        self.assertEqual(len(analysis['already_strong']), 0)
        
        # 2. POST skill-progress
        payload = {
            "skill_name": "Python",
            "level": "Advanced"
        }
        res_post = self.client.post('/api/skill-progress', json=payload, headers={'X-User-Name': user_name})
        
        # 3. no exception
        self.assertEqual(res_post.status_code, 200)
        data_post = res_post.get_json()
        self.assertTrue(data_post['success'])
        
        # 4. GET returns saved skill (skill is persisted)
        res_verify = self.client.get(f'/api/career/software-engineer/skills', headers={'X-User-Name': user_name})
        data_verify = res_verify.get_json()
        analysis_verify = data_verify['skill_analysis']
        
        strong_skills = [s['skill'].lower() for s in analysis_verify['already_strong']]
        self.assertIn("python", strong_skills)

if __name__ == '__main__':
    unittest.main()
