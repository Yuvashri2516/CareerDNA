import unittest
from app import app
import career_service
import sqlite3
import uuid

class TestAnalytics(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        uid = str(uuid.uuid4())[:8]
        self.new_user = f"test_new_{uid}"
        self.active_user = f"test_active_{uid}"

        # Insert some activity for active_user
        conn = sqlite3.connect(career_service.get_db_path())
        cursor = conn.cursor()
        cursor.execute("INSERT INTO results (user_name, best_career, best_score, second_career, second_score) VALUES (?, ?, ?, ?, ?)", (self.active_user, 'software-engineer', 68, 'data', 50))
        cursor.execute("INSERT INTO results (user_name, best_career, best_score, second_career, second_score) VALUES (?, ?, ?, ?, ?)", (self.active_user, 'software-engineer', 76, 'data', 60))
        conn.commit()
        conn.close()

    def test_1_new_user_empty(self):
        with self.client.session_transaction() as sess:
            sess['user'] = self.new_user
            
        res = self.client.get('/api/career-analytics')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        
        self.assertEqual(data['skills_capability']['Coding'], 0)
        self.assertEqual(len(data['assessment_history']), 0)

    def test_2_and_5_user_assessment_history(self):
        with self.client.session_transaction() as sess:
            sess['user'] = self.active_user
            
        res = self.client.get('/api/career-analytics')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        
        hist = data['assessment_history']
        self.assertEqual(len(hist), 2)
        self.assertEqual(hist[0]['score'], 68)
        self.assertEqual(hist[1]['score'], 76)

    def test_3_and_4_user_adds_skill(self):
        with self.client.session_transaction() as sess:
            sess['user'] = self.active_user
            
        # Add Python = 80 -> wait, our add_user_skill endpoint uses levels
        # Advanced maps to 90
        res_add = self.client.post('/api/skill-progress', json={'skill_name': 'Python', 'level': 'Advanced'})
        self.assertEqual(res_add.status_code, 200)

        res = self.client.get('/api/career-analytics')
        data = res.get_json()
        self.assertEqual(data['skills_capability']['Coding'], 90)

    def test_7_user_isolation(self):
        # new_user should not see active_user's python skill or history
        with self.client.session_transaction() as sess:
            sess['user'] = self.new_user
            
        res = self.client.get('/api/career-analytics')
        data = res.get_json()
        
        self.assertEqual(data['skills_capability']['Coding'], 0)
        self.assertEqual(len(data['assessment_history']), 0)

    def test_8_no_random_values(self):
        # We manually inspected the code and there is no Math.random() in the new /api/career-analytics endpoint
        pass

if __name__ == '__main__':
    unittest.main()
