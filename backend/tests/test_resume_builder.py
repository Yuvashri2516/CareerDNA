import unittest
import json
from app import app, db_path, init_db
import sqlite3
import os

class ResumeBuilderTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        init_db()

    def test_resume_template_download(self):
        # 1. Resume template download route/file exists.
        # 2. Download returns HTTP 200.
        res = self.client.get('/Career_DNA_Professional_Resume_Template.docx')
        self.assertEqual(res.status_code, 200)

        # 3. Download response is an attachment.
        cd = res.headers.get('Content-Disposition')
        self.assertTrue(cd and 'attachment' in cd)
        self.assertTrue('Career_DNA_Professional_Resume_Template.docx' in cd)
        
        # Verify file type
        self.assertEqual(res.headers.get('Content-Type'), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    def test_resume_score_progress(self):
        import uuid
        user1 = f"resume_user_{uuid.uuid4().hex[:6]}"
        user2 = f"resume_user_{uuid.uuid4().hex[:6]}"

        # Create users
        with app.app_context():
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute(f"INSERT OR IGNORE INTO users (username, password) VALUES ('{user1}', '123')")
            cur.execute(f"INSERT OR IGNORE INTO users (username, password) VALUES ('{user2}', '123')")
            conn.commit()
            conn.close()

        # 4. New user's resume score is 0%.
        res1 = self.client.get('/api/resume-progress', headers={'X-User-Name': user1})
        data1 = json.loads(res1.data)
        self.assertEqual(data1['score'], 0)

        res2 = self.client.get('/api/resume-progress', headers={'X-User-Name': user2})
        data2 = json.loads(res2.data)
        self.assertEqual(data2['score'], 0)

        # 5. Checkbox interaction increases the score.
        payload = {
            'score': 33,
            'completed_sections': 2,
            'total_sections': 6,
            'sections': {'personal': True, 'education': True}
        }
        self.client.put('/api/resume-progress', json=payload, headers={'X-User-Name': user1})

        res1_after = self.client.get('/api/resume-progress', headers={'X-User-Name': user1})
        data1_after = json.loads(res1_after.data)
        self.assertEqual(data1_after['score'], 33)

        # 6. Unchecking decreases the score
        payload_uncheck = {
            'score': 17,
            'completed_sections': 1,
            'total_sections': 6,
            'sections': {'personal': True, 'education': False}
        }
        self.client.put('/api/resume-progress', json=payload_uncheck, headers={'X-User-Name': user1})
        res1_final = self.client.get('/api/resume-progress', headers={'X-User-Name': user1})
        data1_final = json.loads(res1_final.data)
        self.assertEqual(data1_final['score'], 17)
        self.assertFalse(data1_final['sections'].get('education', False))

        # 7. Score is isolated per user.
        res2_after = self.client.get('/api/resume-progress', headers={'X-User-Name': user2})
        data2_after = json.loads(res2_after.data)
        self.assertEqual(data2_after['score'], 0)

if __name__ == '__main__':
    unittest.main()
