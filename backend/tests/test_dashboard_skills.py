import unittest
from app import app
import career_service
import uuid

class TestDashboardSkills(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        # Create isolated users dynamically
        uid = str(uuid.uuid4())[:8]
        self.new_user = f"test_new_{uid}"
        self.active_user = f"test_active_{uid}"

    def test_1_new_user_empty_skills(self):
        with self.client.session_transaction() as sess:
            sess['user'] = self.new_user
        
        # Dashboard Summary should return success and calculate
        res = self.client.get('/api/dashboard-summary')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        career_id = data.get('ideal_career_id', 'software-engineer')
        
        # Fetch skills for this career
        skill_res = self.client.get(f'/api/career/{career_id}/skills')
        self.assertEqual(skill_res.status_code, 200)
        skill_data = skill_res.get_json()
        
        strong = skill_data['skill_analysis'].get('already_strong', [])
        developing = skill_data['skill_analysis'].get('developing', [])
        
        self.assertEqual(len(strong), 0)
        self.assertEqual(len(developing), 0)

    def test_2_and_3_user_adds_and_updates_skill(self):
        with self.client.session_transaction() as sess:
            sess['user'] = self.active_user
            
        res_add = self.client.post('/api/skill-progress', json={'skill_name': 'Python', 'level': 'Advanced'})
        self.assertEqual(res_add.status_code, 200)

        res_dash = self.client.get('/api/dashboard-summary')
        career_id = res_dash.get_json().get('ideal_career_id', 'software-engineer')

        skill_res = self.client.get(f'/api/career/{career_id}/skills')
        skill_data = skill_res.get_json()
        
        all_skills = skill_data['skill_analysis'].get('already_strong', []) + skill_data['skill_analysis'].get('developing', [])
        python_skill = next((s for s in all_skills if 'python' in s['skill'].lower()), None)
        
        self.assertIsNotNone(python_skill)
        self.assertEqual(python_skill['proficiency'], 90)

        res_update = self.client.post('/api/skill-progress', json={'skill_name': 'Python', 'level': 'Intermediate'})
        self.assertEqual(res_update.status_code, 200)
        
        skill_res_2 = self.client.get(f'/api/career/{career_id}/skills')
        skill_data_2 = skill_res_2.get_json()
        
        all_skills_2 = skill_data_2['skill_analysis'].get('already_strong', []) + skill_data_2['skill_analysis'].get('developing', [])
        python_skill_2 = next((s for s in all_skills_2 if 'python' in s['skill'].lower()), None)
        
        self.assertIsNotNone(python_skill_2)
        self.assertEqual(python_skill_2['proficiency'], 70)
        
    def test_4_user_isolation(self):
        with self.client.session_transaction() as sess:
            sess['user'] = self.new_user
        
        res_dash = self.client.get('/api/dashboard-summary')
        career_id = res_dash.get_json().get('ideal_career_id', 'software-engineer')
        skill_res = self.client.get(f'/api/career/{career_id}/skills')
        skill_data = skill_res.get_json()
        
        strong = skill_data['skill_analysis'].get('already_strong', [])
        developing = skill_data['skill_analysis'].get('developing', [])
        
        self.assertEqual(len(strong), 0)
        self.assertEqual(len(developing), 0)

if __name__ == '__main__':
    unittest.main()
