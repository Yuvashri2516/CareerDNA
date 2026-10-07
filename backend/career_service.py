import json
import sqlite3
import os
from career_engine import (
    get_careers_data,
    calculate_profile_completion,
    match_user_to_career,
    calculate_career_readiness,
    slugify
)

def get_db_path():
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(backend_dir, 'database', 'career_dna.db')

def get_user_profile(user_name):
    """Fetch user profile dict from DB or return default structure."""
    if not user_name:
        return {}

    db_path = get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT full_name, education_level, degree, grad_year,
                   tech_skills, soft_skills, interests, work_style, goals, experience
            FROM user_profiles WHERE user_name = ?
        """, (user_name,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return {
                "user_name": user_name,
                "full_name": user_name,
                "education_level": "",
                "degree": "",
                "grad_year": 0,
                "tech_skills": [],
                "soft_skills": [],
                "interests": [],
                "work_style": {},
                "goals": {},
                "experience": []
            }

        def parse_json(val, default):
            if not val: return default
            try: return json.loads(val)
            except: return default

        return {
            "user_name": user_name,
            "full_name": row[0] or user_name,
            "education_level": row[1] or "",
            "degree": row[2] or "",
            "grad_year": row[3] or 0,
            "tech_skills": parse_json(row[4], []),
            "soft_skills": parse_json(row[5], []),
            "interests": parse_json(row[6], []),
            "work_style": parse_json(row[7], {}),
            "goals": parse_json(row[8], {}),
            "experience": parse_json(row[9], [])
        }
    except Exception as e:
        print(f"[CareerService] get_user_profile DB error: {e}")
        return {"user_name": user_name, "tech_skills": [], "interests": []}

def save_user_profile(user_name, data):
    """Save or update user profile in DB."""
    if not user_name:
        return False, "User not authenticated"

    db_path = get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Existing profile check
        cursor.execute("SELECT user_name FROM user_profiles WHERE user_name = ?", (user_name,))
        exists = cursor.fetchone()

        full_name = data.get('full_name', '')
        education_level = data.get('education_level', '')
        degree = data.get('degree', '')
        grad_year = int(data.get('grad_year', 0) or 0)
        
        tech_skills = json.dumps(data.get('tech_skills', []))
        soft_skills = json.dumps(data.get('soft_skills', []))
        interests = json.dumps(data.get('interests', []))
        work_style = json.dumps(data.get('work_style', {}))
        goals = json.dumps(data.get('goals', {}))
        experience = json.dumps(data.get('experience', []))

        if exists:
            cursor.execute("""
                UPDATE user_profiles
                SET full_name=?, education_level=?, degree=?, grad_year=?,
                    tech_skills=?, soft_skills=?, interests=?, work_style=?, goals=?, experience=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE user_name=?
            """, (full_name, education_level, degree, grad_year, tech_skills, soft_skills, interests, work_style, goals, experience, user_name))
        else:
            cursor.execute("""
                INSERT INTO user_profiles
                (user_name, full_name, education_level, degree, grad_year, tech_skills, soft_skills, interests, work_style, goals, experience)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_name, full_name, education_level, degree, grad_year, tech_skills, soft_skills, interests, work_style, goals, experience))

        conn.commit()
        conn.close()
        return True, "Profile updated successfully"
    except Exception as e:
        print(f"[CareerService] save_user_profile error: {e}")
        return False, str(e)

def get_assessment_dimensions(user_name):
    """Fetch stored 13 assessment dimensional scores for user."""
    if not user_name:
        return {}

    db_path = get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT analytical_thinking, creativity, communication, leadership, problem_solving,
                   technical_interest, social_interest, business_interest, research_interest,
                   design_interest, risk_tolerance, work_style_score, learning_preference
            FROM assessment_dimensions WHERE user_name = ?
        """, (user_name,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "analytical_thinking": row[0],
                "creativity": row[1],
                "communication": row[2],
                "leadership": row[3],
                "problem_solving": row[4],
                "technical_interest": row[5],
                "social_interest": row[6],
                "business_interest": row[7],
                "research_interest": row[8],
                "design_interest": row[9],
                "risk_tolerance": row[10],
                "work_style_score": row[11],
                "learning_preference": row[12]
            }
        else:
            return {}
    except Exception as e:
        print(f"[CareerService] get_assessment_dimensions error: {e}")
        return {}

def save_assessment_dimensions(user_name, dims):
    """Save user assessment dimensions to DB."""
    if not user_name or not dims:
        return

    db_path = get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT user_name FROM assessment_dimensions WHERE user_name = ?", (user_name,))
        exists = cursor.fetchone()

        vals = (
            dims.get('analytical_thinking', 50), dims.get('creativity', 50), dims.get('communication', 50),
            dims.get('leadership', 50), dims.get('problem_solving', 50), dims.get('technical_interest', 50),
            dims.get('social_interest', 50), dims.get('business_interest', 50), dims.get('research_interest', 50),
            dims.get('design_interest', 50), dims.get('risk_tolerance', 50), dims.get('work_style_score', 50),
            dims.get('learning_preference', 50)
        )

        if exists:
            cursor.execute("""
                UPDATE assessment_dimensions
                SET analytical_thinking=?, creativity=?, communication=?, leadership=?, problem_solving=?,
                    technical_interest=?, social_interest=?, business_interest=?, research_interest=?,
                    design_interest=?, risk_tolerance=?, work_style_score=?, learning_preference=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE user_name=?
            """, vals + (user_name,))
        else:
            cursor.execute("""
                INSERT INTO assessment_dimensions
                (analytical_thinking, creativity, communication, leadership, problem_solving,
                 technical_interest, social_interest, business_interest, research_interest,
                 design_interest, risk_tolerance, work_style_score, learning_preference, user_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, vals + (user_name,))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[CareerService] save_assessment_dimensions error: {e}")

def get_user_recommendations(user_name):
    """Calculate and return ranked career recommendations for user based strictly on stored data."""
    profile = get_user_profile(user_name)
    dims = get_assessment_dimensions(user_name)
    careers = get_careers_data()

    has_skills = bool(profile.get('tech_skills'))
    has_edu = bool(profile.get('education_level'))
    has_dims = bool(dims)
    has_data = has_dims or has_skills or has_edu

    results = []
    for c in careers:
        res = match_user_to_career(profile, dims, c)
        results.append(res)

    results.sort(key=lambda x: x['overall_match'], reverse=True)

    top_5 = results[:5]
    ideal_match = results[0] if (results and has_data) else None

    return {
        "has_data": has_data,
        "ideal_match": ideal_match,
        "top_careers": top_5,
        "total_careers_evaluated": len(careers),
        "message": "Complete your profile and assessment to unlock your personalized ideal match." if not has_data else ""
    }

def get_skill_gap_analysis(user_name, career_id):
    """Categorize career skills into Already Strong, Developing, Missing."""
    careers = get_careers_data()
    target = None
    for c in careers:
        if c.get('id') == career_id or slugify(c.get('name', '')) == career_id:
            target = c
            break

    if not target and careers:
        target = careers[0]

    profile = get_user_profile(user_name)
    tech_skills = profile.get('tech_skills', [])
    if isinstance(tech_skills, str):
        try: tech_skills = json.loads(tech_skills)
        except: tech_skills = []

    user_skill_map = {}
    for s in tech_skills:
        if isinstance(s, dict):
            lvl = str(s.get('level', 'Intermediate')).lower()
            val = 90 if lvl == 'advanced' else (70 if lvl == 'intermediate' else 40)
            user_skill_map[s.get('name', '').lower().strip()] = val
        elif isinstance(s, str):
            user_skill_map[s.lower().strip()] = 70

    all_req = target.get('skills', []) + target.get('tech_stack', [])
    seen = set()
    req_skills = []
    for s in all_req:
        s_clean = s.strip()
        if s_clean.lower() not in seen:
            seen.add(s_clean.lower())
            req_skills.append(s_clean)

    already_strong = []
    developing = []
    missing = []

    for req in req_skills:
        req_lower = req.lower()
        score = 0
        for u_s, val in user_skill_map.items():
            if req_lower in u_s or u_s in req_lower:
                score = val
                break
        
        if score >= 75:
            already_strong.append({"skill": req, "proficiency": score, "status": "Strong"})
        elif score >= 40:
            developing.append({"skill": req, "proficiency": score, "status": "Developing"})
        else:
            missing.append({"skill": req, "proficiency": 0, "status": "Missing"})

    top_3_learn = (missing + developing)[:3]

    return {
        "career_id": target.get('id', slugify(target.get('name', ''))),
        "career_name": target.get('name', ''),
        "already_strong": already_strong,
        "developing": developing,
        "missing": missing,
        "top_3_to_learn_next": [s['skill'] for s in top_3_learn]
    }

def get_user_roadmap(user_name, career_id):
    """Generate dynamic multi-stage roadmap tailored to career & user progress."""
    careers = get_careers_data()
    target = None
    for c in careers:
        if c.get('id') == career_id or slugify(c.get('name', '')) == career_id:
            target = c
            break

    if not target and careers:
        target = careers[0]

    db_path = get_db_path()
    completed_stages = []
    current_stage = 0
    has_progress = False
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT completed_stages, current_stage FROM roadmap_progress WHERE user_name = ?", (user_name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            has_progress = True
            completed_stages = json.loads(row[0]) if row[0] else []
            current_stage = row[1] if row[1] is not None else 0
    except Exception as e:
        print(f"[CareerService] get_user_roadmap error: {e}")

    raw_roadmap = target.get('roadmap', [
        "Master foundational programming and tools",
        "Learn core data structures and algorithms",
        "Build 2-3 portfolio projects",
        "Obtain professional certifications",
        "Prepare resume and interview practice"
    ])

    stages = []
    for idx, step_title in enumerate(raw_roadmap, start=1):
        is_completed = idx in completed_stages
        is_current = (idx == current_stage) and current_stage > 0 and not is_completed
        
        status_label = "Completed" if is_completed else ("Current" if is_current else "Not Started")
        stages.append({
            "stage_number": idx,
            "title": f"Stage {idx}: {step_title}",
            "description": f"Focus on mastering {step_title} to build essential career competence.",
            "status": status_label,
            "completed": is_completed
        })

    completion_pct = round((len(completed_stages) / float(len(stages))) * 100) if stages else 0

    return {
        "career_id": target.get('id', slugify(target.get('name', ''))),
        "career_name": target.get('name', ''),
        "current_stage": current_stage,
        "total_stages": len(stages),
        "completion_percentage": completion_pct,
        "has_progress": has_progress,
        "stages": stages
    }

def add_user_skill(user_name, skill_name, level="Advanced"):
    """Add or update a skill in user profile and recalculate match."""
    profile = get_user_profile(user_name)
    tech_skills = profile.get('tech_skills', [])
    if isinstance(tech_skills, str):
        try: tech_skills = json.loads(tech_skills)
        except: tech_skills = []

    # Get initial top match
    recs_before = get_user_recommendations(user_name)
    ideal_before = recs_before.get('ideal_match') or {}
    prev_match = ideal_before.get('overall_match', 70)
    prev_career = ideal_before.get('career_name', '')

    # Update or append skill
    updated = False
    for s in tech_skills:
        if isinstance(s, dict) and s.get('name', '').lower().strip() == skill_name.lower().strip():
            s['level'] = level
            updated = True
            break
    if not updated:
        tech_skills.append({"name": skill_name.strip(), "level": level})

    profile['tech_skills'] = tech_skills
    save_user_profile(user_name, profile)

    # Get updated top match
    recs_after = get_user_recommendations(user_name)
    new_match_obj = recs_after.get('ideal_match') or {}
    new_match = new_match_obj.get('overall_match', 70)
    new_career = new_match_obj.get('career_name', '')

    delta = new_match - prev_match

    return {
        "success": True,
        "skill_added": skill_name,
        "level": level,
        "prev_match_score": prev_match,
        "new_match_score": new_match,
        "match_delta": delta,
        "ideal_career": new_career,
        "explanation": f"Your match for {new_career} changed from {prev_match}% to {new_match}% because {skill_name} is a key skill."
    }

def get_personalized_chat_response(user_name, message, history=None):
    """Inject user's actual profile, assessment, and top career match into AI chat response."""
    msg_lower = message.lower().strip()
    if history is None:
        history = []
        
    context_text = " ".join([h['content'] for h in history[-4:]] if isinstance(history, list) else []).lower()
    full_text = context_text + " " + msg_lower

    intent = "unknown"
    feature_topic = None
    
    # 1. Check feature explanation first
    if any(f in msg_lower for f in ["skill tracker", "career assessment", "the assessment", "career match", "career matching", "learning roadmap", "my roadmap", "resume builder", "interview preparation", "certifications", "certification recommendations", "internship opportunities", "internships", "career analytics", "achievements", "profile completion"]):
        if any(w in msg_lower for w in ["what is", "explain", "how does", "how do", "tell me about", "what does", "what are", "how can i use"]):
            intent = "feature_explanation"
            if "skill tracker" in msg_lower: feature_topic = "skill_tracker"
            elif "assessment" in msg_lower: feature_topic = "assessment"
            elif "career match" in msg_lower or "career matching" in msg_lower: feature_topic = "career_match"
            elif "roadmap" in msg_lower: feature_topic = "roadmap"
            elif "resume builder" in msg_lower: feature_topic = "resume"
            elif "interview preparation" in msg_lower: feature_topic = "interview"
            elif "certifications" in msg_lower or "certification recommendations" in msg_lower: feature_topic = "certifications"
            elif "internship" in msg_lower: feature_topic = "internships"
            elif "career analytics" in msg_lower: feature_topic = "analytics"
            elif "achievements" in msg_lower: feature_topic = "achievements"
            elif "profile" in msg_lower: feature_topic = "profile"
            
    if intent == "unknown":
        if any(k in msg_lower for k in ["what career", "which career", "job suits me", "ideal career", "career is best", "my match", "recommend", "best fit", "choose", "top career"]):
            intent = "career_recommendation"
        elif any(k in msg_lower for k in ["why am i matched", "why is", "top match", "tell me about", "what does a", "explain"]):
            intent = "career_explanation"
        elif any(k in msg_lower for k in ["what skills", "which skills", "missing", "skills do i need", "skills should i learn", "skills should i improve", "skill", "gap", "skill progress"]):
            intent = "skills"
        elif any(k in msg_lower for k in ["how can i improve", "how do i learn", "what should i practice", "improve my", "learn"]):
            intent = "skill_improvement"
        elif any(k in msg_lower for k in ["roadmap", "learn first", "what should i do next", "learn next"]):
            intent = "learning_roadmap"
        elif any(k in msg_lower for k in ["resume", "cv"]):
            intent = "resume"
        elif any(k in msg_lower for k in ["interview", "hr question", "mock", "prepare"]):
            intent = "interview_preparation"
        elif any(k in msg_lower for k in ["salary", "companies hire", "in demand", "job demand", "market"]):
            intent = "salary_market"
        elif any(k in msg_lower for k in ["certification", "certificate", "cert"]):
            intent = "certifications"
        elif any(k in msg_lower for k in ["internship", "apply for", "jobs", "find jobs"]):
            intent = "internship_jobs"
        elif any(k in msg_lower for k in ["profile", "information is missing", "what should i update", "complete"]):
            intent = "profile"
        
    if intent == "unknown":
        if any(k in full_text for k in ["roadmap", "learn first", "what should i do next", "learn next"]):
            intent = "learning_roadmap"
        elif any(k in full_text for k in ["interview", "hr question", "mock", "prepare"]):
            intent = "interview_preparation"

    profile = get_user_profile(user_name)
    recs = get_user_recommendations(user_name)
    ideal = recs.get('ideal_match') or {}
    
    default_career = ideal.get('career_name')
    career_id = ideal.get('career_id')
    
    # Try to extract mentioned career
    mentioned_career = default_career
    for c in ["data scientist", "ai engineer", "software engineer", "cybersecurity", "cloud engineer", "ui/ux designer", "product manager", "data analyst"]:
        if c in full_text:
            mentioned_career = c.title()
            break
            
    career_name = mentioned_career if mentioned_career else default_career
    match_pct = ideal.get('overall_match', 0)
    
    completion = calculate_profile_completion(profile)
    comp_pct = completion.get('completion_percentage', 0)
    
    if not default_career:
        if intent == "career_recommendation":
            return "I don't have enough information to determine your ideal career yet.\n\nComplete your profile and Career Assessment first. Once those are available, I can compare your interests, strengths, skills, work style, and goals and recommend your strongest career matches."
        if intent == "skills":
            return "Your personalized skill-gap analysis isn't available yet. Complete your profile and assessment first, then I'll identify the skills you should develop for your strongest career matches."

    if intent == "career_recommendation":
        explanations = ideal.get('explanations', [])
        gaps = ideal.get('skill_gaps', [])
        reasons_text = "<br>".join([f"• {e}" for e in explanations[:3]])
        gaps_text = ", ".join([g.replace('⚠ ', '') for g in gaps[:2]]) if gaps else "Advanced specialization"
        reply = (f"Based on your Career DNA profile and assessment data, <b>{default_career}</b> is currently your strongest match at <b>{match_pct}%</b>!<br><br>"
                 f"<b>Key matching factors:</b><br>{reasons_text}<br><br>"
                 f"<b>Primary areas to focus on next:</b> {gaps_text}.<br><br>")
        if comp_pct < 70:
            reply += f"<i>Tip: Your Career Profile completion is currently {comp_pct}%. Complete missing sections on your dashboard for an even more accurate recommendation!</i>"
        return reply

    if intent == "feature_explanation":
        if feature_topic == "skill_tracker":
            return "The Skill Tracker helps you monitor your current skills and identify the skills you need to improve for your target career. You can update your proficiency level for each skill, and Career DNA uses that information to show which skills are already strong, which are developing, and which skills are missing. Your skill progress also contributes to your personalized career readiness."
        elif feature_topic == "assessment":
            return "The Career Assessment evaluates your interests, strengths, and work style through a series of questions. We use this data to match you with careers that align with your natural aptitudes and preferences."
        elif feature_topic == "career_match":
            return "Career Matching compares your profile, skills, and assessment results against our database of career requirements. It calculates a compatibility percentage to recommend roles where you are most likely to succeed."
        elif feature_topic == "roadmap":
            return "The Learning Roadmap provides a step-by-step personalized guide to reach your target career. It breaks down the required skills, projects, and milestones you need to accomplish over time."
        elif feature_topic == "resume":
            return "The Resume Builder helps you craft a professional CV tailored to your target career. It uses your profile data, skills, and achievements to generate a clean, ATS-friendly resume layout."
        elif feature_topic == "interview":
            return "Interview Preparation offers role-specific mock questions, HR behavioral guides, and technical challenges (like System Design) to help you practice and succeed in your upcoming job interviews."
        elif feature_topic == "certifications":
            return "Certifications are industry-recognized credentials that validate your skills. We recommend specific certifications based on your career path to strengthen your profile and improve your employability."
        elif feature_topic == "internships":
            return "Internships provide hands-on experience in your chosen field. We help you identify internship opportunities that align with your current skill level and target career goals."
        elif feature_topic == "analytics":
            return "Career Analytics gives you a high-level overview of your progress, showing your profile completeness, skill growth, and how close you are to being fully ready for your target career."
        elif feature_topic == "achievements":
            return "Achievements are badges you earn by completing milestones in Career DNA, such as finishing your assessment, adding skills, or completing your profile. They track your active engagement and progress."
        elif feature_topic == "profile":
            return "Your Profile is the central hub of your professional data. By completing it with your education, experience, and skills, you enable Career DNA to give you more accurate career matches and personalized advice."
        else:
            return "Career DNA offers many personalized tools including the Skill Tracker, Learning Roadmap, Resume Builder, and Interview Prep to guide you to your ideal career."

    if intent == "career_explanation":
        explanations = ideal.get('explanations', [])
        reasons_text = "<br>".join([f"• {e}" for e in explanations]) if explanations else "Your profile aligns well with this role."
        return (f"<b>{default_career}</b> is your top match ({match_pct}%) because your profile aligns strongly with its requirements:<br><br>"
                f"{reasons_text}<br><br>"
                f"They generally build scalable systems, design architectures, or work with data depending on the specific role.")

    if intent == "skills":
        gap_analysis = get_skill_gap_analysis(user_name, career_id) if career_id else {}
        strong = [s['skill'] for s in gap_analysis.get('strong', [])]
        developing = [s['skill'] for s in gap_analysis.get('developing', [])]
        missing = [s['skill'] for s in gap_analysis.get('missing', [])]
        
        reply = f"For <b>{career_name}</b>, here is your personalized skill profile:<br><br>"
        if strong: reply += f"<b>Already Strong:</b> {', '.join(strong)}<br>"
        if developing: reply += f"<b>Developing:</b> {', '.join(developing)}<br>"
        reply += f"<b>Missing Gaps (Priority):</b> {', '.join(missing) if missing else 'None! You are well prepared.'}<br><br>"
        reply += "Focus on your missing gaps to increase your match score!"
        return reply

    if intent == "skill_improvement":
        return (f"To improve your skills for <b>{career_name}</b>, I recommend following a project-based approach:<br>"
                "1. Choose a small project related to the skill.<br>"
                "2. Read the official documentation and follow tutorials.<br>"
                "3. Apply it to your target career domain.<br>"
                "4. Add the completed project to your Career DNA portfolio.")

    if intent == "learning_roadmap":
        roadmap = get_user_roadmap(user_name, career_id) if career_id else []
        if not roadmap:
            return f"I suggest starting with the basics for {career_name}."
        reply = f"Here is your personalized roadmap for <b>{career_name}</b>:<br><br>"
        for step in roadmap[:3]:
            reply += f"• <b>{step.get('title')}</b>: {step.get('desc')}<br>"
        return reply

    if intent == "resume":
        return ("Based on your profile, ensure your resume highlights your strongest skills and completed projects.<br>"
                "- Use the STAR method (Situation, Task, Action, Result) for bullet points.<br>"
                "- Tailor your summary to match your target career.<br>"
                "- Ensure your contact information and GitHub/LinkedIn are up to date.")

    if intent == "interview_preparation":
        return (f"To prepare for <b>{career_name}</b> interviews, practice both technical and behavioral questions.<br><br>"
                "<b>Example Question:</b> 'Can you describe a time you had to optimize a slow-performing system or algorithm?'<br><br>"
                "Check out the Interview Preparation tab for mock questions and the HR Question Bank.")

    if intent == "salary_market":
        return (f"Based on available market data, a typical <b>{career_name}</b> sees strong demand globally.<br>"
                "Salaries vary by location, but generally start around $80k-$100k for entry-level and can exceed $150k for senior roles.<br>"
                "Top tech companies and financial institutions are actively hiring for these skills.")

    if intent == "certifications":
        return (f"For <b>{career_name}</b>, industry-recognized certifications can boost your profile.<br>"
                "Consider looking into AWS, Azure, Google Cloud, or specialized certificates like CompTIA or Meta Developer certificates based on your specific focus.")

    if intent == "internship_jobs":
        return (f"To find internships for <b>{career_name}</b>, check your university career portal, LinkedIn, and platforms like internships.com.<br>"
                "Tailor your profile to match the internship description, highlighting your personal projects and related coursework.")

    if intent == "profile":
        return (f"Your profile is currently <b>{comp_pct}%</b> complete.<br>"
                "To reach 100%, make sure you have added your Skills, Work Experience, Projects, and completed the Career Assessment.")

    return "I want to make sure I answer the right question. You can ask me about your Skill Tracker, career assessment, career match, learning roadmap, resume, interviews, certifications, internships, or career profile."
