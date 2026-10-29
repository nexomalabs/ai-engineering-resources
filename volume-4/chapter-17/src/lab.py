"""Lab 17 — Enterprise AI Adoption Roadmap (starter).

This file RUNS as supplied. Timelines show the raw quarter numbers 1-12, and the cost
estimates are not converted, so the total comes out as zero, and the foundations
check passes every roadmap. Complete the three TODOs.

    python src/lab.py
"""

from dataclasses import dataclass, field

from tabulate import tabulate

# Maya's list in Volume IV, Chapter 17: what carried Wren through its first peak. No better
# model makes any of them obsolete, so every AI release should start with all of them in place.
FOUNDATIONS = [
    "evaluation sets",
    "cost attribution",
    "canary releases",
    "governance review",
    "model-version logging",
]


@dataclass
class RoadmapInitiative:
    name: str
    category: str  # Technology, Process, Governance, People
    phase: int  # 1, 2, or 3 (year)
    quarter_start: int  # 1-12 (Q1Y1 through Q4Y3)
    quarter_end: int
    description: str
    success_metric: str
    dependencies: list[str] = field(default_factory=list)
    owner: str = "AI Team"
    estimated_cost: str = "TBD"
    risk: str = "Medium"
    establishes: list[str] = field(default_factory=list)  # foundations it puts in place
    ships_ai: bool = False  # puts an AI system in front of users


def build_medicore_roadmap() -> list[RoadmapInitiative]:
    return [
        # ── YEAR 1: FOUNDATION ───────────────────────────────────────────
        RoadmapInitiative(
            name="AI Governance Framework",
            category="Governance",
            phase=1,
            quarter_start=1,
            quarter_end=2,
            description="Establish AI policy, risk register, designated AI officer, incident "
            "response procedures, and a governance review before every AI launch. Adopt "
            "NIST AI RMF profile.",
            success_metric="AI governance policy approved; AI officer designated; "
            "risk register operational",
            establishes=["governance review"],
            owner="Legal + Engineering",
            estimated_cost="$80K",
            risk="Low",
        ),
        RoadmapInitiative(
            name="AI Literacy Program",
            category="People",
            phase=1,
            quarter_start=1,
            quarter_end=4,
            description="Training for all 500 employees on AI fundamentals, appropriate "
            "use, and risk awareness. Advanced training for 50 power users.",
            success_metric="90% completion rate; power users certified",
            owner="HR + AI Team",
            estimated_cost="$120K",
            risk="Low",
        ),
        RoadmapInitiative(
            name="Data Foundation Upgrade",
            category="Technology",
            phase=1,
            quarter_start=1,
            quarter_end=4,
            description="Implement data catalog, data lineage tracking, and HIPAA-compliant "
            "data access controls. Prerequisite for AI use with PHI.",
            success_metric="Data catalog covers 100% of clinical datasets; HIPAA audit passed",
            dependencies=["AI Governance Framework"],
            owner="Data Engineering",
            estimated_cost="$350K",
            risk="Medium",
        ),
        RoadmapInitiative(
            name="Production Foundations",
            category="Process",
            phase=1,
            quarter_start=1,
            quarter_end=2,
            description="Before the first pilot: an evaluation set for each use case, cost "
            "attribution by feature and user, canary releases for every model or prompt "
            "change, and the model version logged with every response.",
            success_metric="Pilot evaluation set reviewed by clinicians; every model call "
            "attributed and version-logged; canary process rehearsed",
            establishes=[
                "evaluation sets",
                "cost attribution",
                "canary releases",
                "model-version logging",
            ],
            owner="AI Team",
            estimated_cost="$150K",
            risk="Low",
        ),
        RoadmapInitiative(
            name="Pilot: AI Clinical Documentation Assistant",
            category="Process",
            phase=1,
            quarter_start=3,
            quarter_end=4,
            description="Pilot AI-assisted clinical note summarization for 5 hospital clients. "
            "Measure time savings and clinician satisfaction.",
            success_metric="20% reduction in documentation time; NPS > 40",
            dependencies=[
                "Data Foundation Upgrade",
                "AI Governance Framework",
                "Production Foundations",
            ],
            ships_ai=True,
            owner="Product",
            estimated_cost="$200K",
            risk="High",
        ),
        # ── YEAR 2: INTEGRATION ──────────────────────────────────────────
        RoadmapInitiative(
            name="AI Platform Build",
            category="Technology",
            phase=2,
            quarter_start=5,
            quarter_end=7,
            description="Build internal AI platform: LLM gateway, evaluation pipeline, "
            "cost tracking, monitoring dashboard, prompt registry.",
            success_metric="Platform serving 3+ products; evaluation running "
            "continuously; cost visibility for all teams",
            dependencies=["Pilot: AI Clinical Documentation Assistant"],
            establishes=["cost attribution"],
            owner="AI Platform Team",
            estimated_cost="$600K",
            risk="Medium",
        ),
        RoadmapInitiative(
            name="Patient Risk Stratification Model",
            category="Technology",
            phase=2,
            quarter_start=6,
            quarter_end=8,
            description="Deploy AI-powered patient risk stratification into clinical "
            "analytics dashboards, after independent model validation.",
            success_metric="AUC > 0.82; validated for 3 clinical outcomes; "
            "deployed to 20 hospital clients",
            dependencies=["AI Platform Build", "Data Foundation Upgrade"],
            ships_ai=True,
            owner="Data Science",
            estimated_cost="$450K",
            risk="High",
        ),
        RoadmapInitiative(
            name="Evaluation and Quality Program",
            category="Governance",
            phase=2,
            quarter_start=5,
            quarter_end=6,
            description="Implement LLM-as-Judge evaluation, A/B testing infrastructure, "
            "and quality gates in CI/CD for all AI products.",
            success_metric="100% of AI deployments pass quality gate; "
            "weekly quality reports published",
            dependencies=["AI Platform Build"],
            establishes=["evaluation sets"],
            owner="AI Team",
            estimated_cost="$150K",
            risk="Low",
        ),
        # ── YEAR 3: DIFFERENTIATION ──────────────────────────────────────
        RoadmapInitiative(
            name="Clinical Trial AI Automation",
            category="Process",
            phase=3,
            quarter_start=9,
            quarter_end=11,
            description="AI-powered clinical trial data extraction, validation, and "
            "regulatory submission package preparation.",
            success_metric="50% reduction in trial data processing time; "
            "FDA submission package generation validated",
            dependencies=["AI Platform Build", "Evaluation and Quality Program"],
            ships_ai=True,
            owner="Clinical Affairs + AI Team",
            estimated_cost="$800K",
            risk="Very High",
        ),
        RoadmapInitiative(
            name="Proprietary Clinical AI Model",
            category="Technology",
            phase=3,
            quarter_start=10,
            quarter_end=12,
            description="Fine-tune an open-source base model on MediCore's proprietary "
            "clinical data. Deploy on sovereign infrastructure.",
            success_metric="Model outperforms GPT-6.1 Sol on MediCore clinical benchmarks; "
            "fully on-premises deployment",
            dependencies=["Patient Risk Stratification Model", "Evaluation and Quality Program"],
            ships_ai=True,
            owner="Data Science + Infrastructure",
            estimated_cost="$1.2M",
            risk="High",
        ),
    ]


def parse_cost(cost: str) -> float:
    """Convert an estimate such as "$80K" or "$1.2M" to dollars; "TBD" counts as 0."""
    # TODO 1: Strip "~" and "$", read a trailing K (thousand) or M (million) as a
    #   multiplier, and return the amount in dollars. Return 0.0 for "TBD".
    return 0.0


def print_roadmap(initiatives: list[RoadmapInitiative]):
    print("\n" + "=" * 70)
    print("  MEDICORE ANALYTICS — 3-YEAR AI ADOPTION ROADMAP")
    print("=" * 70)

    for phase in [1, 2, 3]:
        phase_names = {
            1: "YEAR 1: FOUNDATION",
            2: "YEAR 2: INTEGRATION",
            3: "YEAR 3: DIFFERENTIATION",
        }
        print(f"\n{'─' * 70}")
        print(f"  {phase_names[phase]}")
        print(f"{'─' * 70}")

        phase_items = [i for i in initiatives if i.phase == phase]
        table = [
            [
                i.name,
                i.category,
                # TODO 2: Quarters run 1-12 across three years; show each as Q1-Q4 within
                #   its year, so quarter 5 prints as Q1.
                f"Q{i.quarter_start}–Q{i.quarter_end}",
                i.owner,
                i.estimated_cost,
                i.risk,
            ]
            for i in phase_items
        ]
        print(
            tabulate(
                table,
                headers=["Initiative", "Category", "Timeline", "Owner", "Cost", "Risk"],
                tablefmt="simple",
            )
        )
        print()
        for item in phase_items:
            print(f"  [{item.name}]")
            print(f"  Goal: {item.description}")
            print(f"  Success: {item.success_metric}")
            if item.dependencies:
                print(f"  Depends on: {', '.join(item.dependencies)}")
            print()

    total = sum(parse_cost(i.estimated_cost) for i in initiatives)
    total_cost_str = f"~${total / 1_000_000:.2f}M over 3 years"
    print(f"{'─' * 70}")
    print(f"  Total estimated investment: {total_cost_str}")
    print(f"{'─' * 70}\n")


def missing_foundations(initiatives: list[RoadmapInitiative]) -> dict[str, list[str]]:
    """For each initiative that ships AI, the foundations not yet in place when it starts.

    A foundation is in place once an initiative that establishes it has ended.
    """
    missing = {}
    # TODO 3: for each initiative that ships AI, collect the foundations established by
    #   initiatives that end before it starts, and record the FOUNDATIONS it lacks, in
    #   FOUNDATIONS order, under its name. As supplied nothing is ever missing, so the
    #   first draft passes the check.
    return missing


def print_foundations_check(title: str, initiatives: list[RoadmapInitiative]) -> None:
    print(f"Foundations check: {title}")
    missing = missing_foundations(initiatives)
    for release in initiatives:
        if release.name in missing:
            year, quarter = divmod(release.quarter_start - 1, 4)
            print(f"  {release.name} starts in Y{year + 1} Q{quarter + 1} without:")
            print(f"    {', '.join(missing[release.name])}")
    if not missing:
        print(f"  Every AI release starts with all {len(FOUNDATIONS)} foundations in place.")
    print()


if __name__ == "__main__":
    roadmap = build_medicore_roadmap()
    print_roadmap(roadmap)
    draft = [i for i in roadmap if i.name != "Production Foundations"]
    print_foundations_check("the first draft, without Production Foundations", draft)
    print_foundations_check("this roadmap", roadmap)
