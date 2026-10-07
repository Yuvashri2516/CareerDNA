import sys
import os
import unittest

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import career_engine
import career_service

class TestCareerEngine(unittest.TestCase):

    def setUp(self):
        self.careers = career_engine.get_careers_data()
        self.assertTrue(len(self.careers) > 0, "Careers knowledge base must not be empty.")

    def test_analytical_user_top_match(self):
        profile = {
            "full_name": "Alice Analyst",
            "education_level": "Bachelor's Degree",
            "tech_skills": [{"name": "Python", "level": "Advanced"}, {"name": "SQL", "level": "Advanced"}],
            "interests": ["Data Science", "Machine Learning"],
            "goals": {"desired_career": "Data Scientist"}
        }
        dims = {
            "analytical_thinking": 95,
            "technical_interest": 90,
            "research_interest": 88,
            "creativity": 50,
            "business_interest": 60
        }
        
        scores = []
        for c in self.careers:
            res = career_engine.match_user_to_career(profile, dims, c)
            scores.append(res)

        scores.sort(key=lambda x: x['overall_match'], reverse=True)
        top_name = scores[0]['career_name']
        self.assertIn(top_name, ["Data Scientist", "Machine Learning Engineer", "AI Engineer", "Software Engineer"])
        self.assertGreaterEqual(scores[0]['overall_match'], 80)

    def test_creative_user_top_match(self):
        profile = {
            "full_name": "Bob Designer",
            "education_level": "Bachelor's Degree",
            "tech_skills": [{"name": "Figma", "level": "Advanced"}, {"name": "Wireframing", "level": "Advanced"}],
            "interests": ["UI/UX Design", "Product Design"],
            "goals": {"desired_career": "UI/UX Designer"}
        }
        dims = {
            "analytical_thinking": 45,
            "creativity": 95,
            "design_interest": 92,
            "technical_interest": 60
        }

        scores = []
        for c in self.careers:
            res = career_engine.match_user_to_career(profile, dims, c)
            scores.append(res)

        scores.sort(key=lambda x: x['overall_match'], reverse=True)
        top_name = scores[0]['career_name']
        self.assertIn(top_name, ["UI Designer", "UX Designer", "UI/UX Designer", "Frontend Developer"])

    def test_empty_profile_handling(self):
        profile = {}
        dims = {}
        res = career_engine.match_user_to_career(profile, dims, self.careers[0])
        self.assertIsInstance(res['overall_match'], int)
        self.assertGreaterEqual(res['overall_match'], 0)
        self.assertLessEqual(res['overall_match'], 100)

    def test_score_determinism(self):
        profile = {"tech_skills": [{"name": "Python", "level": "Intermediate"}]}
        dims = {"analytical_thinking": 80}
        res1 = career_engine.match_user_to_career(profile, dims, self.careers[0])
        res2 = career_engine.match_user_to_career(profile, dims, self.careers[0])
        self.assertEqual(res1['overall_match'], res2['overall_match'])

    def test_profile_completion_calculator(self):
        p_empty = {}
        res_empty = career_engine.calculate_profile_completion(p_empty)
        self.assertEqual(res_empty['completion_percentage'], 0)

        p_full = {
            "full_name": "Test User",
            "education_level": "Bachelor's",
            "tech_skills": [{"name": "Python"}],
            "interests": ["AI"],
            "work_style": {"environment": "Remote"},
            "goals": {"desired_career": "AI Engineer"},
            "experience": [{"title": "Intern"}]
        }
        res_full = career_engine.calculate_profile_completion(p_full)
        self.assertGreaterEqual(res_full['completion_percentage'], 90)

    def test_career_readiness_calculator(self):
        profile = {
            "education_level": "Bachelor's Degree",
            "tech_skills": [{"name": "Python", "level": "Advanced"}, {"name": "SQL", "level": "Intermediate"}],
            "experience": [{"title": "Developer Intern"}]
        }
        dims = {"analytical_thinking": 80, "technical_interest": 85}
        readiness = career_engine.calculate_career_readiness(profile, dims)
        self.assertIn('overall_readiness', readiness)
        self.assertGreaterEqual(readiness['overall_readiness'], 50)

if __name__ == '__main__':
    unittest.main()
