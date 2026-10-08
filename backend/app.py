import io
import os
import json
import sqlite3
from flask import Flask, render_template, request, redirect, session, send_file, jsonify
from flask_cors import CORS
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from werkzeug.security import generate_password_hash, check_password_hash
import career_engine
import career_service


app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)
# Secret key — MUST be set as SECRET_KEY env var on Render for production.
# A weak fallback is provided for local dev ONLY; never deploy without the env var.
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

# ── CORS — allow the Vercel frontend to call /api/* routes ─────────────────
# Credentials (session cookies) are included by the frontend fetch() calls,
# so we must specify the exact origin rather than "*".
CORS(
    app,
    resources={r"/api/*": {"origins": [
        "https://career-dna-vdzg.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000",
    ]}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "OPTIONS"],
)

# ── Database path — always absolute, derived from this file's location ────
# Using __file__ guarantees the correct path regardless of the working
# directory that Gunicorn or the OS sets when starting the process.
backend_dir = os.path.dirname(os.path.abspath(__file__))
db_dir  = os.path.join(backend_dir, 'database')
db_path = os.path.join(db_dir, 'career_dna.db')

# Ensure the database directory exists before any sqlite3.connect() call.
# This is critical on Render where the directory may not pre-exist.
os.makedirs(db_dir, exist_ok=True)

# Helper to fetch detailed career info from data/careers.json with fallbacks
def get_career_details(name):
    # Default fallback values matching the required keys
    fallback = {
        "name": name,
        "description": "A rewarding career path fitting your personality and interests.",
        "skills": ["Communication", "Problem Solving", "Adaptability"],
        "next_step": "Research online resources and build introductory projects.",
        "salary": "$85,000",
        "demand": "High (15% growth)",
        "education": "Bachelor's degree or equivalent certifications",
        "companies": ["Google", "Microsoft", "Meta", "Amazon"],
        "growth": "Junior -> Mid-Level -> Senior -> Lead/Manager",
        "roadmap": ["Learn the basics", "Build personal projects", "Get certified", "Apply for internships"],
        "certifications": ["Google Career Certificates", "Coursera Specializations"],
        "advantages": ["High growth potential", "Interesting challenges", "Continuous learning"],
        "challenges": ["Requires continuous learning", "Fast-paced environment", "High technical bar"],
        "tech_stack": ["Git", "Command Line"],
        "reasoning": "Your scores show strong capability in logical reasoning, interest in technical solutions, and a preference for structured systems.",
        "strengths": ["Analytical reasoning", "Logical thinking", "Problem solving"],
        "weaknesses": ["Requires coding familiarity", "Steep initial learning curve"],
        "learning_plan": "Spend 2 hours daily on syntax and problem solving. Build 3 projects in 6 months.",
        "future_scope": "Excellent long-term growth due to digital transformation and automation."
    }
    
    project_root = os.path.dirname(backend_dir)
    json_path = os.path.join(project_root, 'data', 'careers.json')
    try:
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                careers = json.load(f)
                for c in careers:
                    if c.get("name").lower() == name.lower() or c.get("name").lower() in name.lower() or name.lower() in c.get("name").lower():
                        # Merge with fallback to ensure all keys exist
                        merged = fallback.copy()
                        merged.update(c)
                        return merged
    except Exception as e:
        print("Error reading careers.json in get_career_details:", e)
        
    return fallback


# -----------------------------
# Career Info
# -----------------------------
career_info = {
    "Software Developer": {
        "description": "You enjoy building apps and solving logical problems.",
        "skills": ["Python", "Java", "DSA", "SQL"],
        "next_step": "Build projects and practice coding regularly."
    },
    "Data Analyst": {
        "description": "You like working with data, numbers, and insights.",
        "skills": ["Excel", "SQL", "Python", "Power BI"],
        "next_step": "Start with Excel and SQL, then move to Python."
    },
    "UI/UX Designer": {
        "description": "You are creative and love designing user experiences.",
        "skills": ["Figma", "Wireframing", "Prototyping"],
        "next_step": "Learn Figma and redesign apps."
    },
    "Digital Marketer": {
        "description": "You enjoy trends, marketing strategies, and communication.",
        "skills": ["SEO", "Content", "Analytics"],
        "next_step": "Create campaigns and learn tools."
    }
}

# -----------------------------
# DB INIT
# -----------------------------
def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # Check and add profile fields if they don't exist
    try:
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "email" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT DEFAULT ''")
        if "photo_url" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN photo_url TEXT DEFAULT '/static/images/avatar1.png'")
        if "bio" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN bio TEXT DEFAULT ''")
        if "theme" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN theme TEXT DEFAULT 'purple'")
        if "profile_visibility" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN profile_visibility TEXT DEFAULT 'public'")
    except Exception as e:
        print("Error checking or adding columns:", e)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            best_career TEXT,
            best_score INTEGER,
            second_career TEXT,
            second_score INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_name TEXT PRIMARY KEY,
            full_name TEXT DEFAULT '',
            education_level TEXT DEFAULT '',
            degree TEXT DEFAULT '',
            grad_year INTEGER DEFAULT 0,
            tech_skills TEXT DEFAULT '[]',
            soft_skills TEXT DEFAULT '[]',
            interests TEXT DEFAULT '[]',
            work_style TEXT DEFAULT '{}',
            goals TEXT DEFAULT '{}',
            experience TEXT DEFAULT '[]',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessment_dimensions (
            user_name TEXT PRIMARY KEY,
            analytical_thinking INTEGER DEFAULT 0,
            creativity INTEGER DEFAULT 0,
            communication INTEGER DEFAULT 0,
            leadership INTEGER DEFAULT 0,
            problem_solving INTEGER DEFAULT 0,
            technical_interest INTEGER DEFAULT 0,
            social_interest INTEGER DEFAULT 0,
            business_interest INTEGER DEFAULT 0,
            research_interest INTEGER DEFAULT 0,
            design_interest INTEGER DEFAULT 0,
            risk_tolerance INTEGER DEFAULT 0,
            work_style_score INTEGER DEFAULT 0,
            learning_preference INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roadmap_progress (
            user_name TEXT PRIMARY KEY,
            career_id TEXT,
            completed_stages TEXT DEFAULT '[]',
            current_stage INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resume_progress (
            user_name TEXT PRIMARY KEY,
            score INTEGER DEFAULT 0,
            sections TEXT DEFAULT '{}',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def get_auth_user():
    """Extract authenticated user name from session or request headers."""
    user = session.get('user')
    if user:
        return user
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]
    req_user = request.headers.get('X-User-Name') or request.args.get('user_name')
    if req_user:
        return req_user
    return None


# -----------------------------
# SAVE RESULT
# -----------------------------
def save_result(user_name, best, best_score, second, second_score):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO results (user_name, best_career, best_score, second_career, second_score)
        VALUES (?, ?, ?, ?, ?)
    """, (user_name, best, best_score, second, second_score))

    conn.commit()
    conn.close()

# -----------------------------
# RESUME PROGRESS ENDPOINTS
# -----------------------------
@app.route('/api/resume-progress', methods=['GET', 'PUT'])
def handle_resume_progress():
    user = get_auth_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    if request.method == 'GET':
        cur.execute("SELECT score, sections FROM resume_progress WHERE user_name = ?", (user,))
        row = cur.fetchone()
        conn.close()
        
        if row:
            score = row[0]
            try:
                sections = json.loads(row[1])
            except:
                sections = {}
        else:
            score = 0
            sections = {}
            
        return jsonify({
            "success": True,
            "score": score,
            "sections": sections
        })
        
    elif request.method == 'PUT':
        data = request.json or {}
        score = data.get('score', 0)
        sections = data.get('sections', {})
        completed_sections = data.get('completed_sections', 0)
        total_sections = data.get('total_sections', 0)
        
        cur.execute("""
            INSERT INTO resume_progress (user_name, score, sections) 
            VALUES (?, ?, ?) 
            ON CONFLICT(user_name) DO UPDATE SET 
            score=excluded.score, 
            sections=excluded.sections,
            updated_at=CURRENT_TIMESTAMP
        """, (user, score, json.dumps(sections)))
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "score": score,
            "completed_sections": completed_sections,
            "total_sections": total_sections,
            "sections": sections
        })

# -----------------------------
# AUTH ROUTES
# -----------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            hashed = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "User already exists"

        conn.close()
        return redirect('/login')

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Support ?next= redirect (e.g. from "Take the Test" button)
    next_url = request.args.get('next', '/welcome')

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Preserve next_url from hidden field on POST
        next_url = request.form.get('next_url', '/welcome')

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Fetch by username only, then verify password (hash-aware)
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_row = cursor.fetchone()

        authenticated = False
        if user_row:
            stored_pw = user_row[2]  # password column
            if stored_pw.startswith('pbkdf2:') or stored_pw.startswith('scrypt:'):
                # Hashed password
                authenticated = check_password_hash(stored_pw, password)
            else:
                # Legacy plaintext — verify then upgrade
                if stored_pw == password:
                    authenticated = True
                    hashed = generate_password_hash(password)
                    cursor.execute(
                        "UPDATE users SET password=? WHERE username=?",
                        (hashed, username)
                    )
                    conn.commit()

        conn.close()

        if authenticated:
            session['user'] = username
            # Validate next_url to prevent open redirect
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('/welcome')
        return "Invalid credentials"

    return render_template('login.html', next_url=next_url)


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

# -----------------------------
# MAIN ROUTES
# -----------------------------
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/assessment')
def assessment():
    if 'user' not in session:
        return redirect('/login')
    return render_template('assessment.html', name=session['user'])


@app.route('/result', methods=['POST'])
def result():
    if 'user' not in session:
        return redirect('/login')

    user_name = session['user']

    scores = {
        "Software Developer": 0,
        "Data Analyst": 0,
        "UI/UX Designer": 0,
        "Digital Marketer": 0
    }

    answers = {f"q{i}": request.form.get(f"q{i}") for i in range(1, 11)}

    if answers["q1"] == "coding":
        scores["Software Developer"] += 3
    elif answers["q1"] == "design":
        scores["UI/UX Designer"] += 3
    elif answers["q1"] == "business":
        scores["Digital Marketer"] += 3

    if answers["q2"] == "numbers":
        scores["Data Analyst"] += 3
    elif answers["q2"] == "creativity":
        scores["UI/UX Designer"] += 2

    if answers["q3"] == "logic":
        scores["Software Developer"] += 2
        scores["Data Analyst"] += 2
    elif answers["q3"] == "people":
        scores["Digital Marketer"] += 2

    if answers["q4"] == "independent":
        scores["Software Developer"] += 1
        scores["Data Analyst"] += 1
    elif answers["q4"] == "team":
        scores["UI/UX Designer"] += 1
        scores["Digital Marketer"] += 1

    if answers["q5"] == "apps":
        scores["Software Developer"] += 3
    elif answers["q5"] == "analysis":
        scores["Data Analyst"] += 3
    elif answers["q5"] == "visuals":
        scores["UI/UX Designer"] += 3
    elif answers["q5"] == "marketing":
        scores["Digital Marketer"] += 3

    for _, value in answers.items():
        if value == "technical":
            scores["Software Developer"] += 1
        if value == "creative":
            scores["UI/UX Designer"] += 1
        if value == "analytical":
            scores["Data Analyst"] += 1
        if value == "trends":
            scores["Digital Marketer"] += 1

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    best = sorted_scores[0][0]
    best_score = sorted_scores[0][1]
    second = sorted_scores[1][0]
    second_score = sorted_scores[1][1]
    top_two = sorted_scores[:2]

    save_result(user_name, best, best_score, second, second_score)

    info = get_career_details(best)
    
    # Generate top 5 career recommendations based on top match
    related_mapping = {
        "Software Developer": ["Software Engineer", "AI Engineer", "Machine Learning Engineer", "Cloud Engineer", "DevOps Engineer"],
        "Data Analyst": ["Data Analyst", "Data Scientist", "Business Analyst", "Financial Analyst", "Digital Marketing"],
        "UI/UX Designer": ["UI Designer", "UX Designer", "Frontend Developer", "Graphic Designer", "Product Manager"],
        "Digital Marketer": ["Digital Marketing", "Entrepreneur", "Content Writer", "HR Specialist", "Business Analyst"]
    }
    
    related_names = related_mapping.get(best, ["Software Engineer", "Data Analyst", "UI/UX Designer", "Digital Marketing", "Business Analyst"])
    top_five_careers = [get_career_details(name) for name in related_names]

    return render_template(
        'result.html',
        user_name=user_name,
        career=best,
        score=best_score,
        scores=sorted_scores,
        top_two=top_two,
        top_five=top_five_careers,
        info=info
    )


@app.route('/history')
def history():
    if 'user' not in session:
        return redirect('/login')

    user_name = session['user']
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, user_name, best_career, best_score, second_career, second_score, created_at
        FROM results
        WHERE user_name = ?
        ORDER BY id DESC
    """, (user_name,))
    rows = cursor.fetchall()
    conn.close()

    return render_template('history.html', rows=rows)


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    user_name = session['user']
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM results WHERE user_name = ?", (user_name,))
    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT best_career, COUNT(*)
        FROM results
        WHERE user_name = ?
        GROUP BY best_career
        ORDER BY COUNT(*) DESC
        LIMIT 1
    """, (user_name,))
    top = cursor.fetchone()

    if top:
        top_career, top_count = top
    else:
        top_career, top_count = "N/A", 0

    cursor.execute("""
        SELECT user_name, best_career, best_score
        FROM results
        WHERE user_name = ?
        ORDER BY id DESC
        LIMIT 5
    """, (user_name,))
    recent = cursor.fetchall()

    conn.close()

    return render_template(
        'dashboard.html',
        total=total,
        top_career=top_career,
        top_count=top_count,
        recent=recent
    )


@app.route('/download')
def download_pdf():
    if 'user' not in session:
        return redirect('/login')

    name = request.args.get('name', 'Guest')
    career = request.args.get('career', 'N/A')
    score = request.args.get('score', '0')

    info = get_career_details(career)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    content = []

    content.append(Paragraph("Career DNA Report", styles['Title']))
    content.append(Spacer(1, 20))

    content.append(Paragraph(f"<b>Name:</b> {name}", styles['Normal']))
    content.append(Spacer(1, 10))

    content.append(Paragraph(f"<b>Best Career Match:</b> {career}", styles['Normal']))
    content.append(Spacer(1, 10))

    content.append(Paragraph(f"<b>Match Score:</b> {score}", styles['Normal']))
    content.append(Spacer(1, 20))

    content.append(Paragraph("<b>Description</b>", styles['Heading2']))
    content.append(Paragraph(info["description"], styles['Normal']))
    content.append(Spacer(1, 20))

    content.append(Paragraph("<b>Recommended Skills</b>", styles['Heading2']))
    for skill in info["skills"]:
        content.append(Paragraph(f"• {skill}", styles['Normal']))
    content.append(Spacer(1, 20))

    content.append(Paragraph("<b>Suggested Next Step</b>", styles['Heading2']))
    content.append(Paragraph(info["next_step"], styles['Normal']))

    doc.build(content)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="career_dna_report.pdf",
        mimetype="application/pdf"
    )

@app.route('/Career_DNA_Professional_Resume_Template.docx')
def download_resume_template():
    return send_file(
        os.path.join(app.static_folder, 'Career_DNA_Professional_Resume_Template.docx'),
        as_attachment=True,
        download_name="Career_DNA_Professional_Resume_Template.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

# -----------------------------
# EXTRA PAGES
# -----------------------------
@app.route('/career-paths')
def career_paths():
    if 'user' not in session:
        return redirect('/login?next=/career-paths')
    import json
    import os
    project_root = os.path.dirname(backend_dir)
    json_path = os.path.join(project_root, 'data', 'careers.json')
    try:
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                careers_list = json.load(f)
        else:
            careers_list = []
    except Exception as e:
        print("Error reading careers.json:", e)
        careers_list = []
    return render_template('career_paths.html', careers=careers_list)


@app.route('/resources')
def resources():
    if 'user' not in session:
        return redirect('/login?next=/resources')
    return render_template('resources.html')


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect('/login')
        
    username = session['user']
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    if request.method == 'POST':
        email = request.form.get('email', '')
        photo_url = request.form.get('photo_url', '/static/images/avatar1.png')
        bio = request.form.get('bio', '')
        theme = request.form.get('theme', 'purple')
        profile_visibility = request.form.get('profile_visibility', 'public')
        
        cursor.execute("""
            UPDATE users 
            SET email = ?, photo_url = ?, bio = ?, theme = ?, profile_visibility = ?
            WHERE username = ?
        """, (email, photo_url, bio, theme, profile_visibility, username))
        conn.commit()
        
    # Fetch current user data
    cursor.execute("""
        SELECT username, email, photo_url, bio, theme, profile_visibility 
        FROM users 
        WHERE username = ?
    """, (username,))
    user_data = cursor.fetchone()
    
    # Fetch results history count and details
    cursor.execute("""
        SELECT best_career, best_score, second_career, second_score, created_at
        FROM results
        WHERE user_name = ?
        ORDER BY id DESC
    """, (username,))
    results = cursor.fetchall()
    conn.close()
    
    # Calculate badges
    assessments_count = len(results)
    badges = []
    if assessments_count > 0:
        badges.append("Completed Assessment")
    if assessments_count >= 3:
        badges.append("Top Learner")
    
    # Check if they have a logic-heavy career
    has_logic = False
    for r in results:
        if r[0] in ["Software Developer", "Software Engineer", "Data Analyst", "AI Engineer", "Machine Learning Engineer"]:
            has_logic = True
            break
    if has_logic:
        badges.append("Problem Solver")
        
    if assessments_count > 0:
        badges.append("Quick Learner")
        badges.append("AI Explorer")
        
    # Set default profile if none exists
    user_dict = {
        "username": username,
        "email": user_data[1] if user_data and user_data[1] else "",
        "photo_url": user_data[2] if user_data and user_data[2] else "/static/images/avatar1.png",
        "bio": user_data[3] if user_data and user_data[3] else "",
        "theme": user_data[4] if user_data and user_data[4] else "purple",
        "profile_visibility": user_data[5] if user_data and user_data[5] else "public"
    }
    
    latest_career = results[0][0] if assessments_count > 0 else "No assessment taken yet"
    
    return render_template(
        'profile.html',
        user=user_dict,
        results_count=assessments_count,
        results=results,
        latest_career=latest_career,
        badges=badges
    )


@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    
    user_name = get_auth_user()
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    history = session['chat_history']
    
    if user_name:
        reply = career_service.get_personalized_chat_response(user_name, message, history)
    else:
        # Default behavior if not logged in
        reply = "Hello! I am your AI Career Assistant. Please log in to get personalized career advice."

    # update history
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})
    if len(history) > 20: # keep last 10 pairs
        history = history[-20:]
    session['chat_history'] = history
    
    return jsonify({"reply": reply})


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if 'user' not in session:
        return redirect('/login?next=/contact')
    success = False

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        success = True

    return render_template('contact.html', success=success)


# -----------------------------
# RUN
# -----------------------------
@app.route('/welcome')
def welcome():
    if 'user' not in session:
        return redirect('/login')

    user_name = session['user']

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT best_career, best_score, second_career, second_score, created_at
        FROM results
        WHERE user_name = ?
        ORDER BY id DESC
        LIMIT 1
    """, (user_name,))
    latest_result = cursor.fetchone()

    conn.close()

    if latest_result:
        best_career = latest_result[0]
        best_score = latest_result[1]
        second_career = latest_result[2]
        second_score = latest_result[3]
        created_at = latest_result[4]
    else:
        best_career = "No assessment taken yet"
        best_score = 0
        second_career = "Not available"
        second_score = 0
        created_at = "No data"

    return render_template(
        'welcome.html',
        user_name=user_name,
        best_career=best_career,
        best_score=best_score,
        second_career=second_career,
        second_score=second_score,
        created_at=created_at
    )

@app.route('/career-match')
def career_match():
    if 'user' not in session:
        return redirect('/login')
    return render_template('career_match.html')

@app.route('/skills')
@app.route('/skills/')
@app.route('/skill-tracker')
@app.route('/skill-tracker/')
def skills():
    if 'user' not in session:
        return redirect('/login')
    return render_template('skills.html')

@app.route('/roadmap')
@app.route('/roadmap/')
def roadmap():
    if 'user' not in session:
        return redirect('/login')
    return render_template('roadmap.html')

@app.route('/resume-builder')
@app.route('/resume-builder/')
def resume_builder():
    if 'user' not in session:
        return redirect('/login')
    return render_template('resume_builder.html')

@app.route('/interview')
@app.route('/interview/')
def interview():
    if 'user' not in session:
        return redirect('/login')
    return render_template('interview.html')

@app.route('/certifications')
@app.route('/certifications/')
def certifications():
    if 'user' not in session:
        return redirect('/login')
    return render_template('certifications.html')

@app.route('/internships')
@app.route('/internships/')
def internships():
    if 'user' not in session:
        return redirect('/login')
    return render_template('internships.html')

@app.route('/analytics')
@app.route('/analytics/')
def analytics():
    if 'user' not in session:
        return redirect('/login')
    return render_template('analytics.html')

@app.route('/ai-assistant')
@app.route('/ai-assistant/')
def ai_assistant():
    if 'user' not in session:
        return redirect('/login')
    return render_template('ai_assistant.html')

@app.route('/achievements')
@app.route('/achievements/')
def achievements():
    if 'user' not in session:
        return redirect('/login')
    return render_template('achievements.html')

@app.route('/hr-question-bank')
@app.route('/hr-question-bank/')
def hr_question_bank():
    return render_template('hr_question_bank.html')

@app.route('/system-design-guide')
@app.route('/system-design-guide/')
def system_design_guide():
    return render_template('system_design_guide.html')

# ── Initialise the database at module load time ───────────────────────────
# When Gunicorn starts the app it imports this module directly; the
# `if __name__ == "__main__"` block is NEVER executed.  We therefore call
# init_db() here so the tables always exist when any worker starts.
try:
    init_db()
except Exception as _init_err:
    print(f"[Career DNA] WARNING: init_db() failed at startup: {_init_err}")


# ─────────────────────────────────────────────────────────────────────────
# JSON API ROUTES  (consumed by the Vercel frontend via fetch())
# The browser stays on the Vercel domain; only these fetch() calls reach
# Render.  All routes accept application/json and return application/json.
# The existing HTML form routes (/login, /signup, /contact …) are preserved
# unchanged so the backend website continues to work.
# ─────────────────────────────────────────────────────────────────────────

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def api_login():
    """JSON login endpoint for the Vercel frontend."""
    if request.method == 'OPTIONS':
        # Preflight is handled automatically by Flask-CORS; returning 200 here
        # as an explicit fallback.
        return jsonify({}), 200

    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required.'}), 400

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Fetch by username only, then verify password securely
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_row = cursor.fetchone()

        authenticated = False
        if user_row:
            stored_pw = user_row[2]  # password column
            if stored_pw.startswith('pbkdf2:') or stored_pw.startswith('scrypt:'):
                # Hashed password — standard secure check
                authenticated = check_password_hash(stored_pw, password)
            else:
                # Legacy plaintext — verify and silently upgrade to hash
                if stored_pw == password:
                    authenticated = True
                    hashed = generate_password_hash(password)
                    cursor.execute(
                        "UPDATE users SET password=? WHERE username=?",
                        (hashed, username)
                    )
                    conn.commit()

        conn.close()
    except Exception as e:
        print(f"[Career DNA] /api/login DB error: {e}")
        return jsonify({'success': False, 'message': 'Database error. Please try again.'}), 500

    if authenticated:
        session['user'] = username
        return jsonify({'success': True, 'redirect': '/welcome'}), 200
    return jsonify({'success': False, 'message': 'Invalid username or password.'}), 401


@app.route('/api/register', methods=['POST', 'OPTIONS'])
def api_register():
    """JSON registration endpoint for the Vercel frontend."""
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required.'}), 400
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters.'}), 400

    hashed = generate_password_hash(password)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed)
        )
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': 'Username already exists. Please choose another.'}), 409
    except Exception as e:
        print(f"[Career DNA] /api/register DB error: {e}")
        return jsonify({'success': False, 'message': 'Database error. Please try again.'}), 500

    return jsonify({'success': True, 'redirect': '/login'}), 201


@app.route('/api/contact', methods=['POST', 'OPTIONS'])
def api_contact():
    """JSON contact form endpoint for the Vercel frontend."""
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    data = request.get_json(silent=True) or {}
    name    = (data.get('name') or '').strip()
    email   = (data.get('email') or '').strip()
    message = (data.get('message') or '').strip()

    if not name or not email:
        return jsonify({'success': False, 'message': 'Name and email are required.'}), 400

    # Contact messages are currently logged server-side.
    # Extend this to send email / save to DB as needed.
    print(f"[Career DNA] Contact form: name={name!r} email={email!r} msg={message[:80]!r}")
    return jsonify({'success': True, 'message': 'Message received. We will get back to you soon.'}), 200


# ── API ENDPOINTS FOR REAL-TIME CAREER INTELLIGENCE SYSTEM ──────────────────

@app.route('/api/profile', methods=['GET', 'PUT', 'POST', 'OPTIONS'])
def api_profile():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    user_name = get_auth_user()
    if not user_name:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401

    if request.method in ['PUT', 'POST']:
        data = request.get_json(silent=True) or {}
        ok, msg = career_service.save_user_profile(user_name, data)
        if not ok:
            return jsonify({'success': False, 'message': msg}), 400

    profile = career_service.get_user_profile(user_name)
    completion = career_engine.calculate_profile_completion(profile)

    return jsonify({
        'success': True,
        'profile': profile,
        'completion': completion
    }), 200

@app.route('/api/assessment/dimensions', methods=['GET', 'POST', 'OPTIONS'])
@app.route('/api/assessment/results', methods=['GET', 'POST', 'OPTIONS'])
def api_assessment_results():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    user_name = get_auth_user()
    if not user_name:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401

    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        dims = data.get('dimensions', data)
        career_service.save_assessment_dimensions(user_name, dims)

    dims = career_service.get_assessment_dimensions(user_name)
    return jsonify({
        'success': True,
        'user_name': user_name,
        'dimensions': dims
    }), 200

@app.route('/api/career-recommendations', methods=['GET', 'OPTIONS'])
def api_career_recommendations():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    user_name = get_auth_user() or 'Guest'
    recs = career_service.get_user_recommendations(user_name)
    return jsonify({
        'success': True,
        'user_name': user_name,
        'ideal_match': recs.get('ideal_match'),
        'top_careers': recs.get('top_careers', []),
        'total_evaluated': recs.get('total_careers_evaluated', 0)
    }), 200

@app.route('/api/career/<career_id>', methods=['GET', 'OPTIONS'])
def api_career_detail(career_id):
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    user_name = get_auth_user() or 'Guest'
    careers = career_engine.get_careers_data()
    target = None
    for c in careers:
        if c.get('id') == career_id or career_engine.slugify(c.get('name', '')) == career_id:
            target = c
            break

    if not target:
        return jsonify({'success': False, 'message': 'Career not found.'}), 404

    profile = career_service.get_user_profile(user_name)
    dims = career_service.get_assessment_dimensions(user_name)
    match_data = career_engine.match_user_to_career(profile, dims, target)

    return jsonify({
        'success': True,
        'career': target,
        'match_analysis': match_data
    }), 200

@app.route('/api/career/<career_id>/skills', methods=['GET', 'OPTIONS'])
def api_career_skills(career_id):
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    user_name = get_auth_user() or 'Guest'
    analysis = career_service.get_skill_gap_analysis(user_name, career_id)
    return jsonify({
        'success': True,
        'skill_analysis': analysis
    }), 200

@app.route('/api/career/<career_id>/roadmap', methods=['GET', 'OPTIONS'])
def api_career_roadmap(career_id):
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    user_name = get_auth_user() or 'Guest'
    roadmap_data = career_service.get_user_roadmap(user_name, career_id)
    return jsonify({
        'success': True,
        'roadmap': roadmap_data
    }), 200

@app.route('/api/roadmap-progress', methods=['POST', 'OPTIONS'])
def api_roadmap_progress():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    user_name = get_auth_user()
    if not user_name:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401

    data = request.get_json(silent=True) or {}
    career_id = data.get('career_id', '')
    completed_stages = data.get('completed_stages', [])
    current_stage = data.get('current_stage', 1)

    db_path_val = career_service.get_db_path()
    try:
        conn = sqlite3.connect(db_path_val)
        cursor = conn.cursor()
        cursor.execute("SELECT user_name FROM roadmap_progress WHERE user_name = ?", (user_name,))
        if cursor.fetchone():
            cursor.execute("""
                UPDATE roadmap_progress SET career_id=?, completed_stages=?, current_stage=?, updated_at=CURRENT_TIMESTAMP
                WHERE user_name=?
            """, (career_id, json.dumps(completed_stages), current_stage, user_name))
        else:
            cursor.execute("""
                INSERT INTO roadmap_progress (user_name, career_id, completed_stages, current_stage)
                VALUES (?, ?, ?, ?)
            """, (user_name, career_id, json.dumps(completed_stages), current_stage))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[API] roadmap-progress error: {e}")

    roadmap_data = career_service.get_user_roadmap(user_name, career_id)
    return jsonify({
        'success': True,
        'roadmap': roadmap_data
    }), 200

@app.route('/api/skill-progress', methods=['POST', 'OPTIONS'])
def api_skill_progress():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    user_name = get_auth_user()
    if not user_name:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401

    data = request.get_json(silent=True) or {}
    skill_name = (data.get('skill_name') or data.get('skill') or '').strip()
    level = data.get('level', 'Advanced')

    if not skill_name:
        return jsonify({'success': False, 'message': 'Skill name is required.'}), 400

    res = career_service.add_user_skill(user_name, skill_name, level)
    return jsonify(res), 200

@app.route('/api/career/<career_id>/market', methods=['GET', 'OPTIONS'])
def api_career_market(career_id):
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    careers = career_engine.get_careers_data()
    target = None
    for c in careers:
        if c.get('id') == career_id or career_engine.slugify(c.get('name', '')) == career_id:
            target = c
            break

    if not target and careers:
        target = careers[0]

    # Check if external market provider key exists
    market_key = os.environ.get('MARKET_DATA_API_KEY')
    is_live = bool(market_key)

    market_info = {
        'career_id': target.get('id', career_id) if target else career_id,
        'career_name': target.get('name', '') if target else career_id,
        'is_live': is_live,
        'source': 'LIVE_MARKET_PROVIDER' if is_live else 'INTERNAL_KNOWLEDGE_BASE',
        'status_label': 'Live Market Feed' if is_live else 'Market data (Curated Baseline)',
        'salary_range': target.get('salary', '$95,000 - $140,000') if target else '$95,000',
        'projected_growth': target.get('demand', 'High demand (20%+ growth)') if target else 'High growth',
        'top_hiring_companies': target.get('companies', ['Google', 'Microsoft', 'Amazon', 'Meta']) if target else [],
        'required_tech_stack': target.get('tech_stack', []) if target else []
    }

    return jsonify({
        'success': True,
        'market_data': market_info
    }), 200

@app.route('/api/internships', methods=['GET', 'OPTIONS'])
def api_internships():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    user_name = get_auth_user() or 'Guest'
    recs = career_service.get_user_recommendations(user_name)
    ideal = recs.get('ideal_match') or {}
    career_name = ideal.get('career_name', 'Software Development')

    opportunities = [
        {
            "id": "opp-1",
            "title": f"Junior {career_name} Intern",
            "company": "TechNova Solutions",
            "location": "Remote / Hybrid",
            "work_type": "Internship",
            "stipend": "$3,500 / month",
            "skills": ideal.get('explanations', ['Python', 'SQL'])[:2],
            "posted_date": "Recently posted",
            "apply_url": "https://careers.google.com"
        },
        {
            "id": "opp-2",
            "title": f"Associate {career_name} Trainee",
            "company": "Global Data Systems",
            "location": "On-site / San Francisco, CA",
            "work_type": "Full-time Entry Level",
            "stipend": "$85,000 / year",
            "skills": ["Problem Solving", "Git"],
            "posted_date": "2 days ago",
            "apply_url": "https://careers.microsoft.com"
        },
        {
            "id": "opp-3",
            "title": "AI & Analytics Research Apprentice",
            "company": "Apex AI Labs",
            "location": "Remote",
            "work_type": "Apprenticeship",
            "stipend": "$4,000 / month",
            "skills": ["Machine Learning", "Python"],
            "posted_date": "1 day ago",
            "apply_url": "https://openai.com/careers"
        }
    ]

    return jsonify({
        'success': True,
        'is_live': False,
        'source': 'INTERNAL_KNOWLEDGE_BASE',
        'status_label': 'Curated Baseline Opportunities',
        'target_career': career_name,
        'opportunities': opportunities
    }), 200

@app.route('/api/readiness', methods=['GET', 'OPTIONS'])
def api_readiness():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    user_name = get_auth_user() or 'Guest'
    profile = career_service.get_user_profile(user_name)
    dims = career_service.get_assessment_dimensions(user_name)
    readiness = career_engine.calculate_career_readiness(profile, dims)

    return jsonify({
        'success': True,
        'user_name': user_name,
        'readiness': readiness
    }), 200

@app.route('/api/career/compare', methods=['GET', 'OPTIONS'])
def api_career_compare():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    user_name = get_auth_user() or 'Guest'
    ids_param = request.args.get('ids', 'software-engineer,data-scientist,ai-engineer')
    requested_ids = [i.strip() for i in ids_param.split(',') if i.strip()]

    profile = career_service.get_user_profile(user_name)
    dims = career_service.get_assessment_dimensions(user_name)
    careers = career_engine.get_careers_data()

    comparison_list = []
    for cid in requested_ids:
        target = None
        for c in careers:
            if c.get('id') == cid or career_engine.slugify(c.get('name', '')) == cid:
                target = c
                break
        if target:
            match_res = career_engine.match_user_to_career(profile, dims, target)
            skill_gap = career_service.get_skill_gap_analysis(user_name, target.get('id'))
            comparison_list.append({
                'career': target,
                'match': match_res,
                'skill_gap': skill_gap
            })

    return jsonify({
        'success': True,
        'comparison': comparison_list
    }), 200

@app.route('/api/achievements', methods=['GET', 'OPTIONS'])
def api_achievements():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    user_name = get_auth_user() or 'Guest'
    profile = career_service.get_user_profile(user_name)
    dims = career_service.get_assessment_dimensions(user_name)
    
    completion = career_engine.calculate_profile_completion(profile)
    comp_pct = completion.get('completion_percentage', 0)

    has_assessment = bool(dims)
    has_skills = len(profile.get('tech_skills', [])) > 0
    has_projects = len(profile.get('experience', [])) > 0
    
    roadmap_started = False
    db_path = career_service.get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT completed_stages, current_stage FROM roadmap_progress WHERE user_name = ?", (user_name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            stages = json.loads(row[0]) if row[0] else []
            if len(stages) > 0 or (row[1] and row[1] > 0):
                roadmap_started = True
    except:
        pass

    badges = [
        {
            "id": "first_step",
            "title": "First Step Done",
            "desc": "Complete your baseline Career DNA assessment.",
            "unlocked": has_assessment,
            "icon": "🎯",
            "progress": 100 if has_assessment else 0
        },
        {
            "id": "skill_pioneer",
            "title": "Skill Pioneer",
            "desc": "Track and maintain technical & soft skills.",
            "unlocked": has_skills,
            "icon": "⚡",
            "progress": 100 if has_skills else 0
        },
        {
            "id": "roadmap_runner",
            "title": "Roadmap Runner",
            "desc": "Start your personalized learning roadmap.",
            "unlocked": roadmap_started,
            "icon": "🚩",
            "progress": 100 if roadmap_started else 0
        },
        {
            "id": "profile_complete",
            "title": "Profile Master",
            "desc": "Reach 100% profile completeness.",
            "unlocked": comp_pct >= 100,
            "icon": "👑",
            "progress": comp_pct
        },
        {
            "id": "first_project",
            "title": "Builder & Maker",
            "desc": "Add portfolio projects to your profile.",
            "unlocked": has_projects,
            "icon": "🔬",
            "progress": 100 if has_projects else 0
        }
    ]

    unlocked_count = sum(1 for b in badges if b['unlocked'])

    return jsonify({
        'success': True,
        'user_name': user_name,
        'unlocked_count': unlocked_count,
        'total_badges': len(badges),
        'badges': badges
    }), 200

@app.route('/api/career-analytics', methods=['GET', 'OPTIONS'])
def api_career_analytics():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    user_name = get_auth_user()
    if not user_name:
        return jsonify({'success': False, 'message': 'Auth required'}), 401

    profile = career_service.get_user_profile(user_name)
    dims = career_service.get_assessment_dimensions(user_name)
    
    coding_score = 0
    sql_score = 0
    design_score = 0
    comm_score = 0
    lead_score = 0
    prob_score = 0
    
    tech_skills = profile.get('tech_skills', [])
    if isinstance(tech_skills, str):
        try: tech_skills = json.loads(tech_skills)
        except: tech_skills = []
        
    for s in tech_skills:
        skill_name = (s.get('name', '') if isinstance(s, dict) else str(s)).lower()
        lvl = (s.get('level', 'Intermediate') if isinstance(s, dict) else 'Intermediate').lower()
        val = 90 if lvl == 'advanced' else (70 if lvl == 'intermediate' else 40)
        
        if 'python' in skill_name or 'java' in skill_name or 'c++' in skill_name or 'coding' in skill_name or 'javascript' in skill_name:
            coding_score = max(coding_score, val)
        if 'sql' in skill_name or 'database' in skill_name:
            sql_score = max(sql_score, val)
        if 'design' in skill_name or 'ui' in skill_name or 'ux' in skill_name or 'figma' in skill_name:
            design_score = max(design_score, val)
        if 'communication' in skill_name:
            comm_score = max(comm_score, val)
        if 'leadership' in skill_name:
            lead_score = max(lead_score, val)
        if 'problem solving' in skill_name:
            prob_score = max(prob_score, val)

    if dims:
        comm_score = min(100, comm_score + (dims.get('communication', 0) * 0.5))
        lead_score = min(100, lead_score + (dims.get('leadership', 0) * 0.5))
        prob_score = min(100, prob_score + (dims.get('problem_solving', 0) * 0.5) + (dims.get('analytical_thinking', 0) / 4))
        coding_score = min(100, coding_score + (dims.get('technical_interest', 0) * 0.5))
        design_score = min(100, design_score + (dims.get('design_interest', 0) * 0.5))

    soft_skills = profile.get('soft_skills', [])
    if isinstance(soft_skills, str):
        try: soft_skills = json.loads(soft_skills)
        except: soft_skills = []
    
    for s in soft_skills:
        s_lower = str(s).lower()
        if 'communication' in s_lower: comm_score = max(comm_score, 70)
        if 'leadership' in s_lower: lead_score = max(lead_score, 70)
        if 'problem solving' in s_lower: prob_score = max(prob_score, 70)

    capabilities = {
        "Coding": int(coding_score),
        "Design": int(design_score),
        "SQL": int(sql_score),
        "Communication": int(comm_score),
        "Leadership": int(lead_score),
        "Problem Solving": int(prob_score)
    }

    conn = sqlite3.connect(career_service.get_db_path())
    cursor = conn.cursor()
    cursor.execute("""
        SELECT best_score FROM results
        WHERE user_name = ?
        ORDER BY created_at ASC
    """, (user_name,))
    rows = cursor.fetchall()
    conn.close()

    history = []
    for idx, row in enumerate(rows):
        history.append({
            "stage": f"Stage {idx + 1}",
            "score": row[0]
        })

    return jsonify({
        "success": True,
        "skills_capability": capabilities,
        "assessment_history": history
    }), 200

@app.route('/api/dashboard-summary', methods=['GET', 'OPTIONS'])
def api_dashboard_summary():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    user_name = get_auth_user() or 'Guest'
    profile = career_service.get_user_profile(user_name)
    dims = career_service.get_assessment_dimensions(user_name)
    
    completion = career_engine.calculate_profile_completion(profile)
    comp_pct = completion.get('completion_percentage', 0)

    recs = career_service.get_user_recommendations(user_name)
    has_match = recs.get('has_data', False)
    ideal = recs.get('ideal_match', {}) if has_match and recs.get('ideal_match') else {}

    readiness = career_engine.calculate_career_readiness(profile, dims)
    
    career_id = ideal.get('career_id', 'software-engineer') if ideal else 'software-engineer'
    roadmap = career_service.get_user_roadmap(user_name, career_id)

    top_skills = [s['name'] if isinstance(s, dict) else s for s in profile.get('tech_skills', [])[:3]]

    if comp_pct < 50:
        recommended_action = "Complete your Career Profile"
    elif not dims:
        recommended_action = "Take the Career Assessment"
    elif has_match and (not roadmap.get('has_progress') or roadmap.get('current_stage', 0) == 0):
        recommended_action = "Start your personalized learning roadmap"
    elif ideal and ideal.get('skill_gaps'):
        gap_clean = ideal.get('skill_gaps')[0].replace('⚠ ', '')
        recommended_action = f"Learn {gap_clean} fundamentals"
    else:
        recommended_action = "Review your career progress & analytics"

    return jsonify({
        'success': True,
        'user_name': user_name,
        'profile_completion': comp_pct,
        'has_assessment': bool(dims),
        'has_career_match': has_match,
        'ideal_career': ideal.get('career_name', 'Not calculated') if has_match else 'Not calculated',
        'ideal_career_id': ideal.get('career_id', 'software-engineer') if has_match else 'software-engineer',
        'ideal_match_score': ideal.get('overall_match', 0) if has_match else 0,
        'career_readiness_score': readiness.get('overall_readiness', 0),
        'top_user_skills': top_skills,
        'skills_to_develop': [g.replace('⚠ ', '') for g in ideal.get('skill_gaps', [])[:3]] if has_match else [],
        'current_roadmap_stage': roadmap.get('current_stage', 0) if has_match else 0,
        'total_roadmap_stages': roadmap.get('total_stages', 0) if has_match else 0,
        'recommended_next_action': recommended_action
    }), 200


if __name__ == "__main__":
    app.run(debug=True)

