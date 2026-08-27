import io
import os
import json
import sqlite3
from flask import Flask, render_template, request, redirect, session, send_file, jsonify
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)
app.secret_key = "secret123"

# Setup paths relative to backend directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(backend_dir, 'database', 'career_dna.db')

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

    conn.commit()
    conn.close()

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
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
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

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
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

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, user_name, best_career, best_score, second_career, second_score, created_at
        FROM results
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    return render_template('history.html', rows=rows)


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM results")
    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT best_career, COUNT(*)
        FROM results
        GROUP BY best_career
        ORDER BY COUNT(*) DESC
        LIMIT 1
    """)
    top = cursor.fetchone()

    if top:
        top_career, top_count = top
    else:
        top_career, top_count = "N/A", 0

    cursor.execute("""
        SELECT user_name, best_career, best_score
        FROM results
        ORDER BY id DESC
        LIMIT 5
    """)
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
    message = data.get("message", "").lower()
    
    # Intelligent response based on keywords
    if any(k in message for k in ["roadmap", "path", "learn", "timeline"]):
        reply = "Here is a recommended learning roadmap:<br>1. **Beginner**: Master basic languages (Python, JavaScript, SQL) and command line.<br>2. **Intermediate**: Work on data structures, build 2-3 personal portfolio projects, use GitHub.<br>3. **Advanced**: Specialize in frameworks (Django, React, PyTorch), deploy apps to cloud platforms, and obtain professional certifications. Which career path are you interested in specifically?"
    elif any(k in message for k in ["resume", "cv", "portfolio"]):
        reply = "Here is key advice to build a winning resume:<br>- Keep it to one page, clean formatting, and use a PDF format.<br>- Focus on accomplishments rather than tasks; use the Action + Task + Result structure (e.g. 'Optimized database queries, reducing loading times by 40%').<br>- List direct GitHub links to 2-3 projects.<br>- Group technical skills clearly by category (Languages, Databases, Tools)."
    elif any(k in message for k in ["interview", "mock", "prepare"]):
        reply = "For interview success, apply these tactics:<br>- Use the **STAR Method** (Situation, Task, Action, Result) for behavioral questions.<br>- Practice live coding out loud so interviewers can follow your logical steps.<br>- Research the company's tech stack and latest business releases.<br>- Ask insightful questions at the end about their development sprint cycles and engineering challenges."
    elif any(k in message for k in ["software engineer", "software developer", "programmer", "coding"]):
        reply = "Software Engineers design and build application systems. Key skills: Python, Java, JavaScript, System Design, DSA, and Git. Average Salary: $105,000/yr. Future Demand: 25% growth. Recommended Certifications: AWS Certified Developer, Meta Front-End/Back-End Developer."
    elif any(k in message for k in ["ai", "machine learning", "ml", "data scientist"]):
        reply = "AI & ML Engineers develop algorithms that learn from patterns in data. Key skills: Python, Linear Algebra, PyTorch/TensorFlow, Statistics, and SQL. Average Salary: $135,000/yr. Future Demand: Extremely high (35%+ growth). Recommended Certifications: Google Cloud Professional ML Engineer, TensorFlow Developer Certificate."
    elif any(k in message for k in ["cyber", "security", "cybersecurity", "hack"]):
        reply = "Cybersecurity Analysts protect networks and infrastructure from attacks. Key skills: Networking, Linux, Wireshark, Metasploit, Risk Assessment. Average Salary: $98,000/yr. Future Demand: 33% growth. Recommended Certifications: CompTIA Security+, Certified Ethical Hacker (CEH), CISSP."
    elif any(k in message for k in ["cloud", "aws", "azure"]):
        reply = "Cloud Engineers design and support cloud infrastructure. Key skills: AWS, Azure, Linux, Terraform, Docker, Kubernetes. Average Salary: $118,000/yr. Future Demand: 27% growth. Recommended Certifications: AWS Solutions Architect, Google Professional Cloud Architect."
    elif any(k in message for k in ["ui", "ux", "design", "figma"]):
        reply = "UI/UX Designers craft user journeys and interface designs. Key skills: Figma, Prototyping, Wireframing, UX Research, Color Theory. Average Salary: $88,000/yr. Future Demand: High. Recommended Certifications: Google UX Design Certificate, Interaction Design Foundation certifications."
    else:
        reply = "Hello! I am your AI Career Assistant. I can help you with:<br>1. Custom roadmaps for any career.<br>2. Professional resume building advice.<br>3. Interview preparation strategy & mock questions.<br>4. Informing you about average salaries, top companies, and demand statistics. What would you like to explore first?"
        
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
def skills():
    if 'user' not in session:
        return redirect('/login')
    return render_template('skills.html')

@app.route('/roadmap')
def roadmap():
    if 'user' not in session:
        return redirect('/login')
    return render_template('roadmap.html')

@app.route('/resume-builder')
def resume_builder():
    if 'user' not in session:
        return redirect('/login')
    return render_template('resume_builder.html')

@app.route('/interview')
def interview():
    if 'user' not in session:
        return redirect('/login')
    return render_template('interview.html')

@app.route('/certifications')
def certifications():
    if 'user' not in session:
        return redirect('/login')
    return render_template('certifications.html')

@app.route('/internships')
def internships():
    if 'user' not in session:
        return redirect('/login')
    return render_template('internships.html')

@app.route('/analytics')
def analytics():
    if 'user' not in session:
        return redirect('/login')
    return render_template('analytics.html')

@app.route('/ai-assistant')
def ai_assistant():
    if 'user' not in session:
        return redirect('/login')
    return render_template('ai_assistant.html')

@app.route('/achievements')
def achievements():
    if 'user' not in session:
        return redirect('/login')
    return render_template('achievements.html')

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
