from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

def add_heading(doc, text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.size = Pt(12)
    run.font.bold = True
    run.font.color.rgb = RGBColor(101, 49, 179) # Career DNA purple
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(2)
    # Add a border-like effect by adding a line or just keep it clean
    
def generate_resume():
    doc = Document()
    
    # Set margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
        
    # Name
    name_p = doc.add_paragraph()
    name_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    name_run = name_p.add_run("[YOUR NAME]")
    name_run.font.size = Pt(24)
    name_run.font.bold = True
    
    # Job Title
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run("[Target Role]")
    title_run.font.size = Pt(14)
    
    # Contact Info
    contact_p = doc.add_paragraph()
    contact_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    contact_run = contact_p.add_run("[email@example.com] | [Phone Number] | [LinkedIn URL] | [GitHub URL] | [Location]")
    contact_run.font.size = Pt(10)
    
    # Professional Summary
    add_heading(doc, "PROFESSIONAL SUMMARY")
    summary = doc.add_paragraph("[Write 2–3 lines highlighting your core strengths, years of experience, key achievements, and the value you bring to a potential employer. Keep it concise, actionable, and tailored to the job description.]")
    
    # Education
    add_heading(doc, "EDUCATION")
    edu_p = doc.add_paragraph()
    edu_p.add_run("[Degree] — [University]").bold = True
    edu_p.add_run("\t\t\t[Year]") # Tab formatting can be tricky, let's just use simple text
    edu_p.paragraph_format.tab_stops.add_tab_stop(Inches(7)) # Right align tab
    
    # Technical Skills
    add_heading(doc, "TECHNICAL SKILLS")
    skills_p = doc.add_paragraph()
    skills_p.add_run("Programming:\t").bold = True
    skills_p.add_run("[Python, Java, JavaScript, C++, etc.]\n")
    skills_p.add_run("Tools:\t\t").bold = True
    skills_p.add_run("[Git, Docker, AWS, Linux, etc.]\n")
    skills_p.add_run("Frameworks:\t").bold = True
    skills_p.add_run("[React, Node.js, Flask, Spring Boot, etc.]\n")
    skills_p.add_run("Databases:\t").bold = True
    skills_p.add_run("[MySQL, PostgreSQL, MongoDB, etc.]")
    
    # Projects
    add_heading(doc, "PROJECTS")
    proj_p = doc.add_paragraph()
    proj_p.add_run("[Project Name]").bold = True
    proj_p.add_run(" | [Technologies used]")
    
    ul1 = doc.add_paragraph("Accomplishment/result", style="List Bullet")
    ul2 = doc.add_paragraph("Quantifiable impact", style="List Bullet")
    
    # Experience
    add_heading(doc, "EXPERIENCE")
    exp_p = doc.add_paragraph()
    exp_p.add_run("[Company Name]").bold = True
    exp_p.add_run(" — [Location]")
    
    role_p = doc.add_paragraph()
    role_p.add_run("[Role]\t\t\t[Dates]").italic = True
    
    ul3 = doc.add_paragraph("Managed X resulting in Y", style="List Bullet")
    ul4 = doc.add_paragraph("Developed feature Z using technology W", style="List Bullet")
    
    # Certifications
    add_heading(doc, "CERTIFICATIONS")
    doc.add_paragraph("[Certification Name] — [Issuing Organization] ([Year])")
    
    # Achievements
    add_heading(doc, "ACHIEVEMENTS")
    doc.add_paragraph("[Achievement / Award] — [Context/Organization] ([Year])")
    
    # Save it
    doc.save("Career_DNA_Professional_Resume_Template.docx")
    
if __name__ == "__main__":
    generate_resume()
