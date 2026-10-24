"""AI Powered Employee Onboarding System.

A rule-based onboarding automation tool built with Streamlit. Given an
employee's name, role and department it generates a welcome email, a 7-day
plan, document and IT access checklists, FAQs and role-based training.
No external APIs are used.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import streamlit as st

# --------------------------------------------------------------------------- #
# Configuration & reference data
# --------------------------------------------------------------------------- #

COMPANY_DEFAULT = "Acme Corp"

DEPARTMENTS = [
    "Engineering",
    "Data & Analytics",
    "Product",
    "Design",
    "Sales",
    "Marketing",
    "Customer Success",
    "Human Resources",
    "Finance",
    "Operations",
    "Legal & Compliance",
    "IT & Security",
]

# Role keyword -> role family. First match wins, so order matters.
ROLE_FAMILIES: list[tuple[str, tuple[str, ...]]] = [
    ("data", ("data", "analyst", "scientist", "machine learning", "ml ", "ai ", "bi ")),
    ("engineering", ("engineer", "developer", "devops", "sre", "architect", "qa", "programmer")),
    ("design", ("design", "ux", "ui ", "creative")),
    ("sales", ("sales", "account executive", "business development", "sdr", "bdr")),
    ("marketing", ("marketing", "content", "seo", "growth", "brand")),
    ("support", ("support", "customer success", "service", "helpdesk")),
    ("hr", ("hr", "recruit", "talent", "people")),
    ("finance", ("finance", "account", "auditor", "controller", "payroll")),
    ("product", ("product", "project", "program", "scrum")),
]

LEADERSHIP_KEYWORDS = ("manager", "lead", "head", "director", "vp", "chief", "principal")

COMMON_DOCUMENTS = [
    "Signed offer letter and employment contract",
    "Government-issued photo ID (passport / national ID / driver's licence)",
    "Proof of address (utility bill or bank statement, last 3 months)",
    "Tax identification form (e.g. W-4 / PAN / TIN)",
    "Bank account details for payroll (voided cheque or statement)",
    "Emergency contact information",
    "Signed Non-Disclosure Agreement (NDA)",
    "Signed Acceptable Use & Code of Conduct acknowledgement",
    "Highest education certificates (copies)",
    "Relieving / experience letters from previous employers",
    "Passport-size photograph for ID badge",
]

DEPARTMENT_DOCUMENTS = {
    "Engineering": ["Signed IP assignment & open-source contribution agreement"],
    "Data & Analytics": ["Data handling & privacy (GDPR / DPDP) acknowledgement"],
    "Finance": [
        "Financial controls & anti-fraud policy acknowledgement",
        "Professional certification copies (CA / CPA / ACCA, if applicable)",
    ],
    "Human Resources": ["Confidentiality addendum for employee records"],
    "Legal & Compliance": ["Conflict-of-interest disclosure form", "Bar / professional registration proof"],
    "Sales": ["Commission plan agreement", "Non-solicitation agreement"],
    "IT & Security": ["Privileged access agreement", "Background verification consent (enhanced)"],
}

BASE_IT_ACCESS = [
    "Corporate email & calendar account",
    "Single Sign-On (SSO) with multi-factor authentication",
    "Company chat & video conferencing",
    "Laptop, charger and peripherals (asset tag recorded)",
    "VPN client and endpoint security agent",
    "Password manager licence",
    "HR portal (payroll, leave, benefits)",
    "Intranet & company knowledge base",
]

DEPARTMENT_IT_ACCESS = {
    "Engineering": [
        "Source control organisation (GitHub / GitLab) and team repositories",
        "CI/CD pipelines and artifact registry",
        "Cloud console - development & staging (read-only production)",
        "Issue tracker and engineering wiki",
        "IDE licences and container tooling",
        "Observability stack (logging, metrics, alerting)",
    ],
    "Data & Analytics": [
        "Data warehouse (read access; write on sandbox schema)",
        "BI platform (Tableau / Power BI / Looker) licence",
        "Notebook environment and compute quota",
        "Data catalogue & lineage tool",
        "Source control for analytics code",
    ],
    "Product": [
        "Issue tracker & roadmap tool",
        "Product analytics platform",
        "User research repository",
        "Design review tool (read access)",
    ],
    "Design": [
        "Design suite licence (Figma / Adobe CC)",
        "Shared design system library",
        "Asset management / brand portal",
        "User research repository",
    ],
    "Sales": [
        "CRM (Salesforce / HubSpot) with territory assignment",
        "Sales engagement & dialer tool",
        "Proposal / e-signature platform",
        "Pipeline dashboards",
    ],
    "Marketing": [
        "Marketing automation platform",
        "CMS and web analytics",
        "Social media management tool",
        "Brand asset library and design tool access",
    ],
    "Customer Success": [
        "Helpdesk / ticketing system",
        "CRM (read access) and customer health dashboards",
        "Knowledge base editor access",
        "Call recording & telephony tool",
    ],
    "Human Resources": [
        "HRIS admin access (role-restricted)",
        "Applicant tracking system",
        "Background verification portal",
        "Learning management system (admin)",
    ],
    "Finance": [
        "ERP / accounting system with role-based approvals",
        "Expense & procurement platform",
        "Banking portal (view-only until approved)",
        "Financial reporting & consolidation tool",
    ],
    "Operations": [
        "Project & workflow management tool",
        "Vendor management system",
        "Operational dashboards",
        "Procurement platform",
    ],
    "Legal & Compliance": [
        "Contract lifecycle management system",
        "Compliance and audit tracking tool",
        "Secure legal document repository",
    ],
    "IT & Security": [
        "Identity provider admin console",
        "Endpoint management (MDM) console",
        "SIEM and vulnerability scanner",
        "Privileged access management vault",
        "Ticketing system - agent role",
    ],
}

LEADERSHIP_IT_EXTRAS = [
    "Team directory & org-chart management",
    "Approval workflows (leave, expenses, hiring)",
    "Budget and headcount dashboards",
]

# Training resources: general -> role-family specific.
GENERAL_TRAINING = [
    ("Company Culture & Values", "Self-paced module", "1 hr"),
    ("Information Security Awareness", "Mandatory e-learning", "1.5 hrs"),
    ("Code of Conduct & Anti-Harassment", "Mandatory e-learning", "1 hr"),
    ("Data Privacy Fundamentals", "Mandatory e-learning", "45 min"),
    ("Workplace Tools Bootcamp", "Live workshop", "2 hrs"),
]

FAMILY_TRAINING = {
    "engineering": [
        ("Engineering Handbook & Coding Standards", "Internal wiki", "2 hrs"),
        ("Git Workflow, Code Review & Release Process", "Workshop", "2 hrs"),
        ("Secure Coding (OWASP Top 10)", "Course", "3 hrs"),
        ("System Architecture Walkthrough", "Session with tech lead", "2 hrs"),
        ("On-call & Incident Response Basics", "Playbook + shadowing", "3 hrs"),
    ],
    "data": [
        ("Data Platform & Warehouse Orientation", "Workshop", "2 hrs"),
        ("SQL Best Practices & Query Optimisation", "Course", "3 hrs"),
        ("Data Governance & PII Handling", "Mandatory e-learning", "1.5 hrs"),
        ("Experiment Design & Statistical Rigor", "Course", "4 hrs"),
        ("Model Deployment & Monitoring Standards", "Internal wiki", "2 hrs"),
    ],
    "design": [
        ("Design System & Brand Guidelines", "Workshop", "2 hrs"),
        ("Accessibility (WCAG) Essentials", "Course", "2 hrs"),
        ("User Research Methods", "Course", "3 hrs"),
        ("Design-to-Engineering Handoff Process", "Internal wiki", "1 hr"),
    ],
    "sales": [
        ("Product Demo Certification", "Live practice", "4 hrs"),
        ("Sales Methodology (MEDDIC / SPIN)", "Course", "4 hrs"),
        ("CRM Hygiene & Forecasting", "Workshop", "2 hrs"),
        ("Competitive Positioning & Objection Handling", "Battlecards", "2 hrs"),
        ("Pricing, Discounting & Contract Policy", "Internal wiki", "1 hr"),
    ],
    "marketing": [
        ("Brand Voice & Messaging Framework", "Workshop", "2 hrs"),
        ("Marketing Automation & Analytics Tools", "Course", "3 hrs"),
        ("SEO & Content Strategy Fundamentals", "Course", "3 hrs"),
        ("Campaign Planning & Attribution", "Internal wiki", "2 hrs"),
    ],
    "support": [
        ("Product Deep Dive for Support", "Workshop", "4 hrs"),
        ("Ticket Triage, SLAs & Escalation Paths", "Playbook", "2 hrs"),
        ("De-escalation & Customer Communication", "Role-play workshop", "3 hrs"),
        ("Knowledge Base Authoring Standards", "Internal wiki", "1 hr"),
    ],
    "hr": [
        ("Employment Law & Compliance Overview", "Course", "4 hrs"),
        ("HRIS Administration", "Workshop", "3 hrs"),
        ("Inclusive Hiring & Interviewing", "Course", "2 hrs"),
        ("Employee Relations Case Handling", "Playbook", "2 hrs"),
    ],
    "finance": [
        ("Financial Close Process", "Walkthrough", "3 hrs"),
        ("ERP System Training", "Workshop", "4 hrs"),
        ("Internal Controls & SOX Awareness", "Mandatory e-learning", "2 hrs"),
        ("Procurement & Expense Policy", "Internal wiki", "1 hr"),
    ],
    "product": [
        ("Product Strategy & Roadmap Process", "Workshop", "2 hrs"),
        ("Customer Discovery & Prioritisation", "Course", "3 hrs"),
        ("Agile Delivery Framework", "Course", "2 hrs"),
        ("Metrics & Product Analytics", "Workshop", "2 hrs"),
    ],
    "general": [
        ("Department Functions & Processes", "Session with manager", "2 hrs"),
        ("Cross-functional Collaboration Guide", "Internal wiki", "1 hr"),
    ],
}

LEADERSHIP_TRAINING = [
    ("Leading Teams: Management Fundamentals", "Course", "4 hrs"),
    ("Performance Reviews & Feedback", "Workshop", "2 hrs"),
    ("Hiring, Interviewing & Onboarding Your Team", "Course", "3 hrs"),
    ("Budgeting & Resource Planning", "Internal wiki", "1.5 hrs"),
]

DEPARTMENT_FOCUS = {
    "Engineering": "shipping reliable, secure software",
    "Data & Analytics": "turning data into decisions",
    "Product": "building products customers love",
    "Design": "crafting intuitive experiences",
    "Sales": "growing our customer base",
    "Marketing": "telling our story and generating demand",
    "Customer Success": "making our customers successful",
    "Human Resources": "building a great place to work",
    "Finance": "keeping the business financially healthy",
    "Operations": "making the business run smoothly",
    "Legal & Compliance": "protecting and guiding the business",
    "IT & Security": "keeping our people and systems secure",
}


# --------------------------------------------------------------------------- #
# Domain model & classification
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Employee:
    name: str
    role: str
    department: str
    company: str = COMPANY_DEFAULT

    @property
    def first_name(self) -> str:
        return self.name.split()[0]

    @property
    def is_leader(self) -> bool:
        role = f" {self.role.lower()} "
        return any(f" {kw}" in role or role.strip().startswith(kw) for kw in LEADERSHIP_KEYWORDS)

    @property
    def family(self) -> str:
        """Role family derived from role keywords, falling back to the department."""
        role = f"{self.role.lower()} "
        for family, keywords in ROLE_FAMILIES:
            if any(kw in role for kw in keywords):
                return family
        return {
            "Engineering": "engineering",
            "Data & Analytics": "data",
            "Design": "design",
            "Sales": "sales",
            "Marketing": "marketing",
            "Customer Success": "support",
            "Human Resources": "hr",
            "Finance": "finance",
            "Product": "product",
        }.get(self.department, "general")


# --------------------------------------------------------------------------- #
# Content generators
# --------------------------------------------------------------------------- #

def generate_welcome_email(emp: Employee) -> str:
    focus = DEPARTMENT_FOCUS.get(emp.department, "doing great work")
    leader_line = (
        "As a leader, you will also meet your direct reports and key stakeholders "
        "during your first week so you can hit the ground running.\n\n"
        if emp.is_leader
        else ""
    )
    return (
        f"Subject: Welcome to {emp.company}, {emp.first_name}!\n\n"
        f"Dear {emp.first_name},\n\n"
        f"On behalf of everyone at {emp.company}, welcome aboard! We are thrilled to have you "
        f"join us as {_article(emp.role)} {emp.role} in the {emp.department} team, where the focus "
        f"is on {focus}.\n\n"
        f"Your first week is designed to help you settle in, meet the people you will work with, "
        f"and get set up with everything you need. Here is what to expect:\n\n"
        f"  - Day 1: Welcome session, laptop setup and introductions to your team\n"
        f"  - Week 1: Guided onboarding plan, training modules and a 1:1 with your manager\n"
        f"  - Support: Your onboarding buddy and the HR team are here to help at any time\n\n"
        f"{leader_line}"
        f"Please bring the required identification and documents listed in your onboarding "
        f"checklist, and check your inbox for your account credentials from IT.\n\n"
        f"If you have any questions before your start date, reply to this email or contact "
        f"people@{_domain(emp.company)}.\n\n"
        f"We look forward to seeing you!\n\n"
        f"Warm regards,\n"
        f"People & Culture Team\n"
        f"{emp.company}"
    )


def generate_onboarding_plan(emp: Employee) -> list[dict[str, object]]:
    family_focus = {
        "engineering": "set up your dev environment and ship a first small pull request",
        "data": "get warehouse access and run your first analysis on a sample dataset",
        "design": "explore the design system and review a recent design project",
        "sales": "shadow discovery calls and learn the product demo flow",
        "marketing": "review active campaigns and brand guidelines",
        "support": "shadow live tickets and learn the escalation process",
        "hr": "review people processes and HRIS workflows",
        "finance": "walk through the close calendar and ERP workflows",
        "product": "review the roadmap and sit in on customer calls",
        "general": "learn the core processes of your team",
    }[emp.family]

    day7_goal = (
        "Present a 30-60-90 day plan to your team and agree on leadership priorities."
        if emp.is_leader
        else "Share your key learnings and agree on 30-60-90 day goals with your manager."
    )

    day3_extra = (
        "Meet your direct reports individually (30 min each)"
        if emp.is_leader
        else "Pair with your onboarding buddy on a real task"
    )

    return [
        {
            "day": "Day 1 - Welcome & Setup",
            "tasks": [
                "Arrive, collect ID badge and tour the office (or join the virtual welcome call)",
                "Meet HR for paperwork, payroll and benefits enrolment",
                "Receive laptop and complete first-login and MFA setup",
                f"Introductions with the {emp.department} team and your onboarding buddy",
                "Lunch with your team",
            ],
        },
        {
            "day": "Day 2 - Company & Culture",
            "tasks": [
                "Company overview: mission, vision, strategy and org structure",
                "Complete Information Security and Code of Conduct training",
                "1:1 with your manager: role expectations and success metrics",
                f"Review the {emp.department} charter and team goals",
            ],
        },
        {
            "day": "Day 3 - Tools & Processes",
            "tasks": [
                "Confirm access to all department systems (see IT checklist)",
                "Workplace tools bootcamp (chat, wiki, ticketing, calendars)",
                day3_extra,
                f"Hands-on: {family_focus}",
            ],
        },
        {
            "day": "Day 4 - Role Deep Dive",
            "tasks": [
                f"Begin role-specific training for {emp.role}",
                "Shadow a senior colleague on day-to-day work",
                "Review current projects, backlog and priorities",
                "Meet key cross-functional partners",
            ],
        },
        {
            "day": "Day 5 - First Contributions",
            "tasks": [
                "Take on your first small, well-scoped task",
                "Continue role-specific training modules",
                "Weekly team meeting - introduce yourself and share early impressions",
                "Submit any outstanding documents to HR",
            ],
        },
        {
            "day": "Day 6 - Practice & Feedback",
            "tasks": [
                "Work independently on your first assignment with a check-in mid-day",
                "Request feedback from your buddy on your progress",
                "Complete remaining mandatory compliance training",
                "Log questions and blockers for tomorrow's review",
            ],
        },
        {
            "day": "Day 7 - Review & Goal Setting",
            "tasks": [
                "Week-one retrospective with your manager",
                day7_goal,
                "Complete the onboarding experience survey",
                "Plan your 30-60-90 day learning and delivery goals",
            ],
        },
    ]


def generate_document_checklist(emp: Employee) -> list[str]:
    docs = list(COMMON_DOCUMENTS)
    docs.extend(DEPARTMENT_DOCUMENTS.get(emp.department, []))
    if emp.is_leader:
        docs.append("Signed management responsibilities & delegation-of-authority acknowledgement")
    return docs


def generate_it_checklist(emp: Employee) -> dict[str, list[str]]:
    sections = {
        "Core access (all employees)": list(BASE_IT_ACCESS),
        f"{emp.department} systems": list(DEPARTMENT_IT_ACCESS.get(emp.department, [])),
    }
    if emp.is_leader:
        sections["Leadership access"] = list(LEADERSHIP_IT_EXTRAS)
    return {title: items for title, items in sections.items() if items}


def generate_faqs(emp: Employee) -> list[tuple[str, str]]:
    manager_noun = "team" if emp.is_leader else "manager"
    faqs = [
        (
            "What are the standard working hours?",
            "Core hours are 10:00-16:00 local time, with flexibility around them. "
            "Your manager will confirm team-specific expectations.",
        ),
        (
            "Who do I contact if I have IT issues?",
            "Raise a ticket via the IT Helpdesk portal or message #it-help. "
            "For urgent access problems, call the IT service desk.",
        ),
        (
            "When will I receive my first salary?",
            "Payroll runs monthly. Your first payment is processed in the next cycle "
            "after your bank details and tax forms are verified by HR.",
        ),
        (
            "How do I request leave?",
            "Submit requests in the HR portal under 'Time Off'. Your approver is notified "
            "automatically. Plan ahead for extended leave.",
        ),
        (
            "What is the remote / hybrid work policy?",
            "Most teams follow a hybrid model. Confirm your in-office days with your "
            f"{manager_noun} and review the Flexible Work Policy on the intranet.",
        ),
        (
            "Who is my onboarding buddy and what do they do?",
            "Your buddy is a peer who helps with day-to-day questions, introduces you to the "
            "team and shows you how things really work. You will be introduced on Day 1.",
        ),
        (
            "What benefits am I eligible for?",
            "Health insurance, retirement contributions, learning budget and wellness "
            "programmes. Enrol within 30 days of joining via the HR portal.",
        ),
        (
            "How are expenses and reimbursements handled?",
            "Submit receipts in the expense platform within 30 days. Approved claims are "
            "paid with the next payroll.",
        ),
        (
            "What is the probation period and how will I be evaluated?",
            "Probation is typically 3-6 months, with check-ins at 30, 60 and 90 days "
            "to review goals, feedback and support needs.",
        ),
    ]

    family_faqs = {
        "engineering": (
            "How do I get my code reviewed and deployed?",
            "Open a pull request, request two reviewers, and merge after CI passes. "
            "Deployments follow the release calendar in the engineering handbook.",
        ),
        "data": (
            "How do I request access to sensitive datasets?",
            "Submit a data access request through the data catalogue. Approvals need the "
            "data owner and your manager, and all access is audited.",
        ),
        "design": (
            "Where do I find brand assets and design components?",
            "The shared design system library and brand portal contain approved components, "
            "logos and guidelines.",
        ),
        "sales": (
            "How are quotas and commissions calculated?",
            "See your commission plan agreement and the Sales Ops wiki. Sales Ops will walk "
            "you through quota ramp during Week 1.",
        ),
        "marketing": (
            "What is the approval process for external content?",
            "All external content goes through brand review, and legal review when it "
            "includes claims or customer references.",
        ),
        "support": (
            "What are our response-time SLAs?",
            "SLAs vary by customer tier and are documented in the support playbook. "
            "The ticketing system highlights upcoming breaches.",
        ),
        "hr": (
            "How do I handle confidential employee information?",
            "Access employee records only on a need-to-know basis, through the HRIS. "
            "Never share records over chat or personal email.",
        ),
        "finance": (
            "What are the month-end close deadlines?",
            "The finance close calendar lists deadlines for each step. Your manager will "
            "assign your tasks during Week 1.",
        ),
        "product": (
            "How are roadmap priorities decided?",
            "Quarterly planning combines customer insight, business goals and engineering "
            "capacity. You will join the next planning session.",
        ),
    }
    if emp.family in family_faqs:
        faqs.append(family_faqs[emp.family])

    if emp.is_leader:
        faqs.append(
            (
                "What approvals do I now own as a people leader?",
                "Leave, expenses, hiring requisitions and performance reviews for your team. "
                "HR will cover delegation of authority and leadership training in Week 1.",
            )
        )
    return faqs


def generate_training(emp: Employee) -> dict[str, list[tuple[str, str, str]]]:
    sections = {
        "Foundations (all employees)": list(GENERAL_TRAINING),
        f"Role track: {emp.role}": list(FAMILY_TRAINING.get(emp.family, FAMILY_TRAINING["general"])),
    }
    if emp.is_leader:
        sections["Leadership development"] = list(LEADERSHIP_TRAINING)
    return sections


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _domain(company: str) -> str:
    slug = "".join(ch for ch in company.lower() if ch.isalnum())
    return f"{slug or 'company'}.com"


def build_markdown_package(emp: Employee, data: dict[str, object]) -> str:
    """Combine all generated content into a single downloadable Markdown file."""
    lines = [
        f"# Onboarding Package - {emp.name}",
        f"*{emp.role} | {emp.department} | {emp.company} | Generated {date.today():%d %b %Y}*",
        "",
        "## 1. Welcome Email",
        "```",
        str(data["email"]),
        "```",
        "",
        "## 2. 7-Day Onboarding Plan",
    ]
    for day in data["plan"]:  # type: ignore[union-attr]
        lines.append(f"### {day['day']}")
        lines.extend(f"- [ ] {task}" for task in day["tasks"])
        lines.append("")

    lines.append("## 3. Required Documents")
    lines.extend(f"- [ ] {doc}" for doc in data["documents"])  # type: ignore[union-attr]
    lines.append("")

    lines.append("## 4. IT Access Checklist")
    for title, items in data["it"].items():  # type: ignore[union-attr]
        lines.append(f"### {title}")
        lines.extend(f"- [ ] {item}" for item in items)
        lines.append("")

    lines.append("## 5. FAQs")
    for question, answer in data["faqs"]:  # type: ignore[union-attr]
        lines.append(f"**Q: {question}**  \nA: {answer}\n")

    lines.append("## 6. Training Resources")
    for title, courses in data["training"].items():  # type: ignore[union-attr]
        lines.append(f"### {title}")
        lines.append("| Course | Format | Duration |\n|---|---|---|")
        lines.extend(f"| {c} | {f} | {d} |" for c, f, d in courses)
        lines.append("")
    return "\n".join(lines)


def validate(name: str, role: str) -> list[str]:
    errors = []
    if len(name.strip()) < 2:
        errors.append("Please enter the employee's full name.")
    if len(role.strip()) < 2:
        errors.append("Please enter a job role.")
    return errors


# --------------------------------------------------------------------------- #
# UI
# --------------------------------------------------------------------------- #

CSS = """
<style>
    .block-container {padding-top: 2rem; max-width: 1100px;}
    .hero {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        padding: 1.8rem 2rem; border-radius: 16px; color: #fff; margin-bottom: 1.5rem;
    }
    .hero h1 {color: #fff; margin: 0; font-size: 2rem;}
    .hero p {color: #e0e7ff; margin: .4rem 0 0 0;}
    .chip {
        display: inline-block; padding: .2rem .7rem; margin: 0 .4rem .4rem 0;
        border-radius: 999px; background: rgba(79,70,229,.12); color: #4f46e5;
        font-size: .85rem; font-weight: 600;
    }
    .email-box {
        white-space: pre-wrap; font-family: inherit; padding: 1.2rem 1.5rem;
        border: 1px solid rgba(128,128,128,.3); border-radius: 12px; line-height: 1.6;
    }
    div[data-testid="stForm"] {border-radius: 14px;}
</style>
"""


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero">
            <h1>AI Powered Employee Onboarding System</h1>
            <p>Generate a complete, role-aware onboarding package in seconds.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_checklist(items: list[str], key_prefix: str) -> None:
    done = 0
    for i, item in enumerate(items):
        if st.checkbox(item, key=f"{key_prefix}_{i}"):
            done += 1
    st.progress(done / len(items) if items else 0.0, text=f"{done}/{len(items)} completed")


def render_results(emp: Employee, data: dict[str, object]) -> None:
    st.markdown(
        f'<span class="chip">{emp.name}</span><span class="chip">{emp.role}</span>'
        f'<span class="chip">{emp.department}</span>'
        f'<span class="chip">{"Leadership track" if emp.is_leader else "Individual contributor"}</span>',
        unsafe_allow_html=True,
    )

    st.download_button(
        "Download full onboarding package (.md)",
        data=build_markdown_package(emp, data),
        file_name=f"onboarding_{emp.name.lower().replace(' ', '_')}.md",
        mime="text/markdown",
        type="primary",
    )

    tabs = st.tabs(
        [
            "Welcome Email",
            "7-Day Plan",
            "Documents",
            "IT Access",
            "FAQs",
            "Training",
        ]
    )

    with tabs[0]:
        st.header("Welcome Email")
        email = str(data["email"])
        st.markdown(f'<div class="email-box">{_escape(email)}</div>', unsafe_allow_html=True)
        with st.expander("Copy-friendly plain text"):
            st.code(email, language=None)

    with tabs[1]:
        st.header("7-Day Onboarding Plan")
        for day in data["plan"]:  # type: ignore[union-attr]
            with st.expander(day["day"], expanded=day["day"].startswith("Day 1")):
                for task in day["tasks"]:
                    st.markdown(f"- {task}")

    with tabs[2]:
        st.header("Required Documents Checklist")
        render_checklist(data["documents"], "doc")  # type: ignore[arg-type]

    with tabs[3]:
        st.header("IT Access Checklist")
        for n, (title, items) in enumerate(data["it"].items()):  # type: ignore[union-attr]
            st.subheader(title)
            render_checklist(items, f"it{n}")

    with tabs[4]:
        st.header("Frequently Asked Questions")
        for question, answer in data["faqs"]:  # type: ignore[union-attr]
            with st.expander(question):
                st.write(answer)

    with tabs[5]:
        st.header("Training Resources")
        for title, courses in data["training"].items():  # type: ignore[union-attr]
            st.subheader(title)
            st.table(
                {
                    "Course": [c for c, _, _ in courses],
                    "Format": [f for _, f, _ in courses],
                    "Duration": [d for _, _, d in courses],
                }
            )


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> None:
    st.set_page_config(
        page_title="Employee Onboarding System",
        page_icon="🧭",
        layout="wide",
    )
    st.markdown(CSS, unsafe_allow_html=True)
    render_hero()

    with st.sidebar:
        st.header("Settings")
        company = st.text_input("Company name", value=COMPANY_DEFAULT)
        st.caption(
            "All content is generated locally with rule-based logic. "
            "No data leaves this application."
        )

    st.header("Employee Details")
    with st.form("onboarding_form"):
        col1, col2, col3 = st.columns(3)
        name = col1.text_input("Employee Name", placeholder="e.g. Priya Sharma")
        role = col2.text_input("Role", placeholder="e.g. Senior Backend Engineer")
        department = col3.selectbox("Department", DEPARTMENTS)
        submitted = st.form_submit_button("Generate Onboarding Package", type="primary")

    if submitted:
        errors = validate(name, role)
        if errors:
            for err in errors:
                st.error(err)
            st.session_state.pop("onboarding", None)
        else:
            emp = Employee(
                name=" ".join(name.split()),
                role=" ".join(role.split()),
                department=department,
                company=company.strip() or COMPANY_DEFAULT,
            )
            st.session_state["onboarding"] = (
                emp,
                {
                    "email": generate_welcome_email(emp),
                    "plan": generate_onboarding_plan(emp),
                    "documents": generate_document_checklist(emp),
                    "it": generate_it_checklist(emp),
                    "faqs": generate_faqs(emp),
                    "training": generate_training(emp),
                },
            )
            # Reset checklist state for the new employee.
            for key in [k for k in st.session_state if k.startswith(("doc_", "it"))]:
                del st.session_state[key]

    if "onboarding" in st.session_state:
        emp, data = st.session_state["onboarding"]
        st.success(f"Onboarding package ready for {emp.name}.")
        render_results(emp, data)
    else:
        st.info("Enter the employee's details above and click **Generate Onboarding Package**.")


if __name__ == "__main__":
    main()
