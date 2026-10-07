import unittest
from app import app
import career_service
import sqlite3
import uuid

class TestHistoryIsolation(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        uid = str(uuid.uuid4())[:8]
        self.user_a = f"test_user_a_{uid}"
        self.user_b = f"test_user_b_{uid}"
        self.new_user = f"test_new_user_{uid}"

        # Setup mock database entries
        conn = sqlite3.connect(career_service.get_db_path())
        cursor = conn.cursor()
        
        # User A has 2 assessments
        cursor.execute("INSERT INTO results (user_name, best_career, best_score, second_career, second_score) VALUES (?, ?, ?, ?, ?)", (self.user_a, 'Software Developer', 80, 'Data Scientist', 75))
        cursor.execute("INSERT INTO results (user_name, best_career, best_score, second_career, second_score) VALUES (?, ?, ?, ?, ?)", (self.user_a, 'Data Scientist', 85, 'Data Analyst', 70))
        
        # User B has 1 assessment
        cursor.execute("INSERT INTO results (user_name, best_career, best_score, second_career, second_score) VALUES (?, ?, ?, ?, ?)", (self.user_b, 'UI/UX Designer', 72, 'Digital Marketer', 65))
        
        conn.commit()
        conn.close()

    def test_user_a_isolation(self):
        with self.client.session_transaction() as sess:
            sess['user'] = self.user_a

        res = self.client.get('/history')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        # Ensure User A's results are shown
        self.assertIn("Software Developer", html)
        self.assertIn("<td>80</td>", html)
        self.assertIn("Data Scientist", html)
        self.assertIn("<td>85</td>", html)

        # Ensure User B's result is NOT shown
        self.assertNotIn("UI/UX Designer", html)
        self.assertNotIn("<td>72</td>", html)

    def test_user_b_isolation(self):
        with self.client.session_transaction() as sess:
            sess['user'] = self.user_b

        res = self.client.get('/history')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        # Ensure User B's result is shown
        self.assertIn("UI/UX Designer", html)
        self.assertIn("<td>72</td>", html)

        # Ensure User A's result is NOT shown
        self.assertNotIn("Software Developer", html)
        self.assertNotIn("<td>80</td>", html)
        
    def test_new_user_empty(self):
        with self.client.session_transaction() as sess:
            sess['user'] = self.new_user

        res = self.client.get('/history')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        # Ensure no other user's results are shown for the new user
        self.assertNotIn("Software Developer", html)
        self.assertNotIn("UI/UX Designer", html)
