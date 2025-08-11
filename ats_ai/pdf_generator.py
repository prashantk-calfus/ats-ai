import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_pdf_report(evaluation_results, parsed_resume, candidate_name, jd_source="Unknown JD", weightage_config=None):
    """Generate a clean, readable PDF report matching the Streamlit app format exactly"""

    # Create reports directory if it doesn't exist
    os.makedirs("reports", exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reports/{candidate_name.replace(' ', '_')}_{timestamp}.pdf"

    # Create PDF document with better margins
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    story = []
    styles = getSampleStyleSheet()

    # Simple, clean styles
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=20, spaceAfter=20, alignment=1, fontName="Helvetica-Bold")
    heading_style = ParagraphStyle("Heading", parent=styles["Heading2"], fontSize=14, spaceAfter=12, fontName="Helvetica-Bold")
    subheading_style = ParagraphStyle("SubHeading", parent=styles["Heading3"], fontSize=12, spaceAfter=8, fontName="Helvetica-Bold")

    # Title
    story.append(Paragraph(f"Evaluation Report for: {candidate_name}", title_style))
    story.append(Paragraph(f"Job Description: {jd_source}", styles["Normal"]))

    # ADD WEIGHTAGE INFORMATION HERE
    if weightage_config:
        weightage_display = f"Experience: {weightage_config['experience_weight']}%, " f"Skills: {weightage_config['skills_weight']}%, " f"Projects: {weightage_config['projects_weight']}%, " f"Education: {weightage_config['education_weight']}%"
        story.append(Paragraph(f"Weightage Used: {weightage_display}", styles["Normal"]))
    else:
        story.append(Paragraph("Weightage Used: Default (Experience: 30%, Skills: 40%, Projects: 20%, Education: 10%)", styles["Normal"]))

    story.append(Spacer(1, 30))

    # === OVERALL PERFORMANCE ===
    story.append(Paragraph("Overall Performance", heading_style))

    overall_score = evaluation_results.get("Overall_Weighted_Score", "N/A")
    match_percentage = evaluation_results.get("Match_Percentage", "N/A")
    qualification_status = evaluation_results.get("Qualification Status", "N/A")

    # Simple metrics table with adjusted column widths
    metrics_data = [["Overall Score (0-10)", "Match with JD", "Status"], [str(overall_score), f"{match_percentage}%", str(qualification_status)]]

    # Adjusted column widths - make Status column wider
    metrics_table = Table(metrics_data, colWidths=[1.8 * inch, 1.7 * inch, 2.5 * inch])
    metrics_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    story.append(metrics_table)
    story.append(Spacer(1, 20))

    # === DETAILED SCORES WITH DYNAMIC WEIGHTAGE ===
    story.append(Paragraph("Detailed Scores", heading_style))

    projects_score = evaluation_results.get("Projects_Score", 0)
    projects_excluded = projects_score == 0.0

    # Use weightage config if provided, otherwise use defaults
    if weightage_config:
        exp_pct = weightage_config["experience_weight"]
        skills_pct = weightage_config["skills_weight"]
        edu_pct = weightage_config["education_weight"]
        projects_pct = weightage_config["projects_weight"]
    else:
        exp_pct = 30
        skills_pct = 40
        edu_pct = 10
        projects_pct = 20

    if projects_excluded:
        # Calculate redistributed weights
        total_other = exp_pct + skills_pct + edu_pct
        exp_adj = exp_pct + (projects_pct * (exp_pct / total_other))
        skills_adj = skills_pct + (projects_pct * (skills_pct / total_other))
        edu_adj = edu_pct + (projects_pct * (edu_pct / total_other))

        story.append(Paragraph(f"Note: Projects excluded from scoring. Weights redistributed: Experience: {exp_adj:.1f}%, Skills: {skills_adj:.1f}%, Education: {edu_adj:.1f}%", styles["Normal"]))
        story.append(Spacer(1, 8))

        detailed_data = [
            [f"Experience ({exp_adj:.1f}%)", f"Skills ({skills_adj:.1f}%)", f"Education ({edu_adj:.1f}%)"],
            [str(evaluation_results.get("Experience_Score", "N/A")), str(evaluation_results.get("Skills_Score", "N/A")), str(evaluation_results.get("Education_Score", "N/A"))],
        ]
        detailed_table = Table(detailed_data, colWidths=[2 * inch, 2 * inch, 2 * inch])
    else:
        detailed_data = [
            [f"Experience ({exp_pct}%)", f"Skills ({skills_pct}%)", f"Education ({edu_pct}%)", f"Projects ({projects_pct}%)"],
            [str(evaluation_results.get("Experience_Score", "N/A")), str(evaluation_results.get("Skills_Score", "N/A")), str(evaluation_results.get("Education_Score", "N/A")), str(evaluation_results.get("Projects_Score", "N/A"))],
        ]
        detailed_table = Table(detailed_data, colWidths=[1.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])

    detailed_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    story.append(detailed_table)
    story.append(Spacer(1, 20))

    # === STRENGTHS AND WEAKNESSES - SIMPLE LIST FORMAT ===
    story.append(Paragraph("Strengths and Areas for Improvement", heading_style))

    # Strengths
    story.append(Paragraph("Strengths:", subheading_style))
    pros = evaluation_results.get("Pros", [])
    if pros:
        for strength in pros:
            story.append(Paragraph(f"• {strength}", styles["Normal"]))
    else:
        story.append(Paragraph("• No specific strengths identified.", styles["Normal"]))

    story.append(Spacer(1, 15))

    # Weaknesses
    story.append(Paragraph("Weaknesses:", subheading_style))
    cons = evaluation_results.get("Cons", [])
    if cons:
        for weakness in cons:
            story.append(Paragraph(f"• {weakness}", styles["Normal"]))
    else:
        story.append(Paragraph("• No specific weaknesses identified.", styles["Normal"]))

    story.append(Spacer(1, 20))

    # === SKILLS ANALYSIS ===
    skills_match = evaluation_results.get("Skills Match", [])
    if skills_match and len(skills_match) > 0:
        story.append(Paragraph("Skills Matched with JD", subheading_style))
        for skill_item in skills_match:
            story.append(Paragraph(f"✓ {skill_item}", styles["Normal"]))
        story.append(Spacer(1, 15))

    missing_skills = evaluation_results.get("Required_Skills_Missing_from_Resume", [])
    if missing_skills and len(missing_skills) > 0:
        story.append(Paragraph("Required Skills Missing from Resume", subheading_style))
        story.append(Paragraph(", ".join(missing_skills), styles["Normal"]))
        story.append(Spacer(1, 15))

    extra_skills = evaluation_results.get("Extra skills", [])
    if extra_skills and len(extra_skills) > 0:
        story.append(Paragraph("Extra Skills (Beyond JD Requirements)", subheading_style))
        story.append(Paragraph(", ".join(extra_skills), styles["Normal"]))
        story.append(Spacer(1, 15))

    # Summary
    summary = evaluation_results.get("Summary")
    if summary:
        story.append(Paragraph("Summary", subheading_style))
        story.append(Paragraph(f"• {summary}", styles["Normal"]))
        story.append(Spacer(1, 20))

    # === PARSED RESUME INFORMATION ===
    story.append(Paragraph("Parsed Resume Information", heading_style))

    if parsed_resume:
        # Basic Information
        story.append(Paragraph("Basic Information", subheading_style))
        story.append(Paragraph(f"Name: {candidate_name}", styles["Normal"]))

        contact_details = parsed_resume.get("Contact_Details", {})
        story.append(Paragraph(f"Mobile No: {contact_details.get('Mobile_No', 'N/A')}", styles["Normal"]))
        story.append(Paragraph(f"Email: {contact_details.get('Email', 'N/A')}", styles["Normal"]))

        github_repo = parsed_resume.get("Github_Repo", "N/A")
        if github_repo and github_repo.strip().lower() != "na":
            story.append(Paragraph(f"GitHub: {github_repo}", styles["Normal"]))
        else:
            story.append(Paragraph("GitHub: Not provided", styles["Normal"]))

        linkedin = parsed_resume.get("LinkedIn", "N/A")
        if linkedin and linkedin.strip().lower() != "na":
            story.append(Paragraph(f"LinkedIn: {linkedin}", styles["Normal"]))
        else:
            story.append(Paragraph("LinkedIn: Not provided", styles["Normal"]))

        story.append(Spacer(1, 15))

        # Education
        story.append(Paragraph("Education", subheading_style))
        education_entries = parsed_resume.get("Education", [])
        if education_entries:
            for edu in education_entries:
                degree = edu.get("Degree", "N/A")
                institution = edu.get("Institution", "N/A")
                story.append(Paragraph(f"• {degree} at {institution}", styles["Normal"]))

                score = edu.get("Score", "N/A")
                duration = edu.get("Duration", "N/A")
                story.append(Paragraph(f"  Score: {score}, Duration: {duration}", styles["Normal"]))
                story.append(Spacer(1, 5))
        else:
            story.append(Paragraph("No education details provided.", styles["Normal"]))

        story.append(Spacer(1, 15))

        # Professional Experience
        story.append(Paragraph("Professional Experience", subheading_style))
        experience_entries = parsed_resume.get("Professional_Experience", [])
        if experience_entries:
            for exp in experience_entries:
                role = exp.get("Role", "N/A")
                company = exp.get("Company", "N/A")
                duration = exp.get("Duration", "N/A")

                story.append(Paragraph(f"• {role} at {company}", styles["Normal"]))
                story.append(Paragraph(f"  Duration: {duration}", styles["Normal"]))

                description = exp.get("Description", "N/A")
                if description and description.strip().lower() not in ["na", "n/a"]:
                    # Split long descriptions into readable chunks
                    if len(description) > 500:
                        description = description[:500] + "..."
                    story.append(Paragraph(f"  Description: {description}", styles["Normal"]))
                story.append(Spacer(1, 8))
        else:
            story.append(Paragraph("No professional experience details provided.", styles["Normal"]))

        story.append(Spacer(1, 15))

        # Projects
        story.append(Paragraph("Projects", subheading_style))
        project_entries = parsed_resume.get("Projects", [])

        has_valid_projects = False
        if project_entries:
            for proj in project_entries:
                project_name = proj.get("Project_Name", proj.get("Title", "")).strip()
                if project_name and project_name.upper() not in ["NA", "N/A", ""]:
                    has_valid_projects = True
                    break

        if has_valid_projects:
            for proj in project_entries:
                project_name = proj.get("Project_Name", proj.get("Title", "N/A"))
                if project_name.upper() not in ["NA", "N/A"]:
                    story.append(Paragraph(f"• Project: {project_name}", styles["Normal"]))
                    description = proj.get("Project_Description", proj.get("Description", "N/A"))
                    if description and description.strip().lower() not in ["na", "n/a"]:
                        # Limit description length for readability
                        if len(description) > 300:
                            description = description[:300] + "..."
                        story.append(Paragraph(f"  Description: {description}", styles["Normal"]))
                    story.append(Spacer(1, 5))
        else:
            story.append(Paragraph("No project details provided.", styles["Normal"]))

        story.append(Spacer(1, 15))

        # Certifications
        story.append(Paragraph("Certifications", subheading_style))
        certification_entries = parsed_resume.get("Certifications", [])
        if certification_entries and len(certification_entries) > 0:
            for cert in certification_entries:
                story.append(Paragraph(f"• {cert}", styles["Normal"]))
        else:
            story.append(Paragraph("No certifications provided.", styles["Normal"]))

        story.append(Spacer(1, 15))

        # Technical Skills
        story.append(Paragraph("Technical Skills", subheading_style))
        programming_languages = parsed_resume.get("Programming_Language", [])
        frameworks = parsed_resume.get("Frameworks", [])
        technologies = parsed_resume.get("Technologies", [])

        if programming_languages:
            story.append(Paragraph("Programming Languages:", styles["Normal"]))
            lang_text = ", ".join(programming_languages)
            story.append(Paragraph(lang_text, styles["Normal"]))
            story.append(Spacer(1, 8))

        if frameworks:
            story.append(Paragraph("Frameworks:", styles["Normal"]))
            framework_text = ", ".join(frameworks)
            story.append(Paragraph(framework_text, styles["Normal"]))
            story.append(Spacer(1, 8))

        if technologies:
            story.append(Paragraph("Technologies:", styles["Normal"]))
            tech_text = ", ".join(technologies)
            story.append(Paragraph(tech_text, styles["Normal"]))
            story.append(Spacer(1, 8))

        if not (programming_languages or frameworks or technologies):
            story.append(Paragraph("No technical skills provided.", styles["Normal"]))

    else:
        story.append(Paragraph("No parsed resume data available.", styles["Normal"]))

    # Footer
    story.append(Spacer(1, 20))
    footer_style = ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey, alignment=1)
    story.append(Paragraph(f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))

    # Build PDF
    doc.build(story)
    return filename
