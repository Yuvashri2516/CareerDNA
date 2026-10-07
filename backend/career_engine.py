import json
import os
import re

def slugify(text):
    """Convert text like 'Data Scientist' into a URL slug 'data-scientist'."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[\s_-]+', '-', text)

def get_careers_data():
    """Load and normalize career records from data/careers.json."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(os.path.dirname(base_dir), 'data', 'careers.json')
    
    if not os.path.exists(data_path):
        data_path = os.path.join(base_dir, 'data', 'careers.json')
        
    if not os.path.exists(data_path):
        return []

    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            careers = json.load(f)
            
        for item in careers:
            if 'id' not in item:
                item['id'] = slugify(item.get('name', ''))
            if 'skills' not in item:
                item['skills'] = []
            if 'preferred_skills' not in item:
                item['preferred_skills'] = item.get('tech_stack', [])[:3]
            if 'traits' not in item:
                item['traits'] = item.get('strengths', ['Analytical', 'Problem Solving'])
            if 'interests' not in item:
                item['interests'] = [item.get('name', '')]
            if 'industries' not in item:
                item['industries'] = ['Technology', 'Professional Services']
            if 'work_environment' not in item:
                item['work_environment'] = 'Flexible / Hybrid'
        return careers
    except Exception as e:
        print(f"[CareerEngine] Error loading careers.json: {e}")
        return []

def calculate_profile_completion(profile):
    """
    Calculate user profile completion percentage based on filled sections.
    Returns: { "completion_percentage": int, "missing_sections": [str] }
    """
    if not profile:
        profile = {}

    total_weight = 0
    earned_weight = 0
    missing = []

    # Section 1: Basic Info (15%)
    total_weight += 15
    if profile.get('full_name') and profile.get('education_level'):
        earned_weight += 15
    else:
        missing.append("Education & Basic Details")

    # Section 2: Technical Skills (25%)
    total_weight += 25
    tech_skills = profile.get('tech_skills', [])
    if isinstance(tech_skills, str):
        try:
            tech_skills = json.loads(tech_skills)
        except:
            tech_skills = []
    if len(tech_skills) > 0:
        earned_weight += 25
    else:
        missing.append("Technical Skills")

    # Section 3: Soft Skills & Interests (20%)
    total_weight += 20
    interests = profile.get('interests', [])
    if isinstance(interests, str):
        try:
            interests = json.loads(interests)
        except:
            interests = []
    if len(interests) > 0:
        earned_weight += 20
    else:
        missing.append("Interests & Soft Skills")

    # Section 4: Work Style & Preferences (15%)
    total_weight += 15
    work_style = profile.get('work_style', {})
    if isinstance(work_style, str):
        try:
            work_style = json.loads(work_style)
        except:
            work_style = {}
    if work_style and any(work_style.values()):
        earned_weight += 15
    else:
        missing.append("Work Style Preferences")

    # Section 5: Career Goals (15%)
    total_weight += 15
    goals = profile.get('goals', {})
    if isinstance(goals, str):
        try:
            goals = json.loads(goals)
        except:
            goals = {}
    if goals and (goals.get('desired_career') or goals.get('desired_industry')):
        earned_weight += 15
    else:
        missing.append("Career Goals")

    # Section 6: Experience & Projects (10%)
    total_weight += 10
    experience = profile.get('experience', [])
    if isinstance(experience, str):
        try:
            experience = json.loads(experience)
        except:
            experience = []
    if len(experience) > 0:
        earned_weight += 10
    else:
        missing.append("Projects or Experience")

    percentage = min(100, max(0, round((earned_weight / total_weight) * 100))) if total_weight > 0 else 0
    return {
        "completion_percentage": percentage,
        "missing_sections": missing
    }

def match_user_to_career(user_profile, assessment_dims, career):
    """
    Calculate deterministic, multi-factor match score (0-100%) between a user and a career.
    """
    if not user_profile:
        user_profile = {}
    if not assessment_dims:
        assessment_dims = {}

    # Parse JSON fields safely if stored as strings
    tech_skills = user_profile.get('tech_skills', [])
    if isinstance(tech_skills, str):
        try: tech_skills = json.loads(tech_skills)
        except: tech_skills = []
    
    # Standardize skills list to dict of name -> level_score
    user_skill_dict = {}
    for s in tech_skills:
        if isinstance(s, dict):
            lvl = str(s.get('level', 'Intermediate')).lower()
            val = 100 if lvl == 'advanced' else (70 if lvl == 'intermediate' else 40)
            user_skill_dict[s.get('name', '').lower().strip()] = val
        elif isinstance(s, str):
            user_skill_dict[s.lower().strip()] = 70

    user_interests = user_profile.get('interests', [])
    if isinstance(user_interests, str):
        try: user_interests = json.loads(user_interests)
        except: user_interests = []
    user_interests = [str(i).lower().strip() for i in user_interests]

    work_style = user_profile.get('work_style', {})
    if isinstance(work_style, str):
        try: work_style = json.loads(work_style)
        except: work_style = {}

    goals = user_profile.get('goals', {})
    if isinstance(goals, str):
        try: goals = json.loads(goals)
        except: goals = {}

    explanations = []
    skill_gaps = []

    # 1. Personality & Trait Fit (weight: 20%)
    analytical = assessment_dims.get('analytical_thinking', 60)
    creativity = assessment_dims.get('creativity', 60)
    tech_int = assessment_dims.get('technical_interest', 60)
    research = assessment_dims.get('research_interest', 60)
    business = assessment_dims.get('business_interest', 60)
    design_score = assessment_dims.get('design_interest', 60)

    career_name_lower = career.get('name', '').lower()
    
    # Calculate dimensional fit score
    if any(k in career_name_lower for k in ['data', 'ai', 'machine learning', 'analytics', 'engineer', 'developer', 'software']):
        trait_score = (analytical * 0.4) + (tech_int * 0.4) + (research * 0.2)
        if analytical >= 75:
            explanations.append("✓ Strong analytical thinking alignment")
        if research >= 70:
            explanations.append("✓ High research orientation matches technical depth")
    elif any(k in career_name_lower for k in ['ui', 'ux', 'design', 'frontend', 'game']):
        trait_score = (creativity * 0.4) + (design_score * 0.4) + (tech_int * 0.2)
        if creativity >= 70:
            explanations.append("✓ Creative mindset fits design-focused workflows")
    elif any(k in career_name_lower for k in ['business', 'marketing', 'manager', 'product', 'consultant', 'accountant']):
        trait_score = (business * 0.4) + (assessment_dims.get('communication', 60) * 0.4) + (assessment_dims.get('leadership', 60) * 0.2)
        if business >= 70:
            explanations.append("✓ Business interest aligns with strategic focus")
    else:
        trait_score = (analytical * 0.3) + (creativity * 0.3) + (tech_int * 0.4)

    personality_fit = round(min(100, max(40, trait_score)))

    # 2. Interest Fit (weight: 20%)
    career_interests = [str(i).lower().strip() for i in career.get('interests', [])] + [career_name_lower]
    matched_interests = [i for i in user_interests if any(i in ci or ci in i for ci in career_interests)]
    
    if len(user_interests) > 0 and matched_interests:
        interest_fit = round(min(100, 70 + (len(matched_interests) * 15)))
    elif len(user_interests) > 0:
        interest_fit = 60
    else:
        interest_fit = round(min(100, max(50, (tech_int + research) / 2)))

    if matched_interests:
        explanations.append(f"✓ Shares interest in {', '.join(matched_interests[:2])}")
    elif tech_int >= 75:
        explanations.append("✓ Strong general technology & engineering interest")

    # 3. Skill Fit (weight: 25%)
    all_career_skills = list(set([s.lower().strip() for s in career.get('skills', []) + career.get('tech_stack', [])]))
    
    matched_skills = []
    missing = []

    for req in all_career_skills:
        found = False
        for u_skill, u_val in user_skill_dict.items():
            if req in u_skill or u_skill in req:
                matched_skills.append(req.title())
                found = True
                break
        if not found:
            missing.append(req.title())

    if all_career_skills:
        if matched_skills:
            skill_fit = round(min(100, 50 + (len(matched_skills) * 20)))
        else:
            skill_fit = 45
    else:
        skill_fit = 65

    if matched_skills:
        explanations.append(f"✓ Key foundation in {', '.join(matched_skills[:3])}")
    
    for m in missing[:3]:
        skill_gaps.append(f"⚠ {m}")

    # 4. Education Fit (weight: 10%)
    edu_user = str(user_profile.get('education_level', '')).lower()
    edu_req = str(career.get('education', '')).lower()
    
    if ('master' in edu_req or 'phd' in edu_req) and ('master' in edu_user or 'phd' in edu_user):
        education_fit = 95
        explanations.append("✓ Graduate degree meets advanced criteria")
    elif 'bachelor' in edu_req and ('bachelor' in edu_user or 'master' in edu_user or 'degree' in edu_user):
        education_fit = 90
        explanations.append("✓ Degree background satisfies education requirements")
    elif edu_user:
        education_fit = 80
    else:
        education_fit = 65

    # 5. Work Style Fit (weight: 10%)
    work_style_fit = 80
    user_env = str(work_style.get('environment', '')).lower()
    if user_env and ('remote' in user_env or 'hybrid' in user_env):
        work_style_fit = 90
        explanations.append("✓ Work environment matches preferred remote/hybrid model")

    # 6. Goal Fit (weight: 10%)
    desired_career = str(goals.get('desired_career', '')).lower()
    if desired_career and (desired_career in career_name_lower or career_name_lower in desired_career):
        goal_fit = 98
        explanations.append("✓ Explicitly listed as your target career goal")
    elif goals.get('desired_industry'):
        goal_fit = 85
    else:
        goal_fit = 70

    # 7. Experience Fit (weight: 5%)
    exp_list = user_profile.get('experience', [])
    if isinstance(exp_list, str):
        try: exp_list = json.loads(exp_list)
        except: exp_list = []
    
    if len(exp_list) > 0:
        experience_fit = round(min(100, 70 + (len(exp_list) * 15)))
    else:
        experience_fit = 60

    # Calculate Weighted Overall Match
    overall = (
        (personality_fit * 0.20) +
        (interest_fit     * 0.20) +
        (skill_fit        * 0.25) +
        (education_fit    * 0.10) +
        (work_style_fit   * 0.10) +
        (goal_fit         * 0.10) +
        (experience_fit   * 0.05)
    )

    overall_match = round(min(99, max(45, overall)))

    # Fallback explanation if empty
    if not explanations:
        explanations = [
            "✓ Balanced skill and preference alignment",
            "✓ Fits career path growth projections"
        ]

    return {
        "career_id": career.get('id', slugify(career.get('name', ''))),
        "career_name": career.get('name', ''),
        "overall_match": overall_match,
        "factor_breakdown": {
            "personality_fit": personality_fit,
            "interest_fit": interest_fit,
            "skill_fit": skill_fit,
            "education_fit": education_fit,
            "work_style_fit": work_style_fit,
            "goal_fit": goal_fit,
            "experience_fit": experience_fit
        },
        "explanations": explanations[:4],
        "skill_gaps": skill_gaps[:3],
        "salary": career.get('salary', 'N/A'),
        "demand": career.get('demand', 'High growth')
    }

def calculate_career_readiness(user_profile, assessment_dims):
    """
    Calculate real Career Readiness Score (0-100%) and factor breakdown.
    """
    if not user_profile: user_profile = {}
    if not assessment_dims: assessment_dims = {}

    # 1. Skills Readiness
    tech_skills = user_profile.get('tech_skills', [])
    if isinstance(tech_skills, str):
        try: tech_skills = json.loads(tech_skills)
        except: tech_skills = []
    skills_score = min(100, len(tech_skills) * 20) if tech_skills else 30

    # 2. Education Readiness
    edu = str(user_profile.get('education_level', '')).lower()
    if 'master' in edu or 'phd' in edu: edu_score = 95
    elif 'bachelor' in edu: edu_score = 85
    elif edu: edu_score = 70
    else: edu_score = 40

    # 3. Projects & Experience
    exp = user_profile.get('experience', [])
    if isinstance(exp, str):
        try: exp = json.loads(exp)
        except: exp = []
    projects_score = min(100, 30 + (len(exp) * 25))

    # 4. Assessment Readiness
    dims_count = sum(1 for v in assessment_dims.values() if v and v != 50)
    assessment_score = min(100, 40 + (dims_count * 10))

    # Overall Weighted Readiness
    overall_readiness = round(
        (skills_score * 0.35) +
        (edu_score * 0.20) +
        (projects_score * 0.25) +
        (assessment_score * 0.20)
    )

    return {
        "overall_readiness": min(98, max(20, overall_readiness)),
        "breakdown": {
            "skills": skills_score,
            "education": edu_score,
            "projects": projects_score,
            "assessment": assessment_score,
            "certifications": min(100, skills_score + 10),
            "resume": min(100, round((skills_score + edu_score) / 2))
        }
    }
