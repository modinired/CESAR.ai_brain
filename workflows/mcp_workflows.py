"""
MCP Workflows - Prefect Workflows for MCP Systems
==================================================

Example Prefect workflows demonstrating all 6 MCP systems in action:
- Financial analysis with report generation
- Workflow automation pipeline
- Legal compliance checking
- Innovation research pipeline
- Creative campaign creation
- Personalized learning path generation
"""

from prefect import flow, task
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from mcp_agents.central_orchestrator import create_central_orchestrator


# =============================================================================
# TASK DEFINITIONS
# =============================================================================

@task(name="Initialize MCP Orchestrator", retries=3)
def initialize_orchestrator():
    """Initialize the Central MCP Orchestrator"""
    return create_central_orchestrator()


@task(name="Execute MCP Task", retries=2)
def execute_mcp_task(orchestrator, task_type: str, task_data: dict):
    """Execute a task on appropriate MCP system"""
    return orchestrator.route_task(
        task_type=task_type,
        task_data=task_data
    )


# =============================================================================
# WORKFLOW 1: FINANCIAL ANALYSIS WITH REPORTING
# =============================================================================

@flow(name="Financial Analysis with Report Generation")
def financial_analysis_workflow(ticker: str = "AAPL"):
    """
    Complete financial analysis workflow:
    1. Analyze stock with FinPsyMCP
    2. Generate professional report with CreativeMCP
    """
    orchestrator = initialize_orchestrator()

    # Step 1: Stock analysis
    analysis_result = execute_mcp_task(
        orchestrator,
        task_type='stock_analysis',
        task_data={
            'ticker': ticker,
            'start_date': '2023-01-01'
        }
    )

    # Step 2: Generate report
    report_result = execute_mcp_task(
        orchestrator,
        task_type='content_generation',
        task_data={
            'content_type': 'article',
            'topic': f'{ticker} Stock Analysis Report',
            'tone': 'professional',
            'length': 'long'
        }
    )

    return {
        'ticker': ticker,
        'analysis': analysis_result,
        'report': report_result,
        'timestamp': datetime.now().isoformat()
    }


# =============================================================================
# WORKFLOW 2: WORKFLOW AUTOMATION PIPELINE
# =============================================================================

@flow(name="Workflow Automation Pipeline")
def workflow_automation_pipeline(workflow_json: dict, platform: str = "n8n"):
    """
    Complete workflow automation:
    1. Convert workflow with PydiniRedMCP
    2. Test generated script
    3. Package for deployment
    """
    orchestrator = initialize_orchestrator()

    # Complete automation pipeline
    result = execute_mcp_task(
        orchestrator,
        task_type='workflow_automation',
        task_data={
            'workflow_json': workflow_json,
            'platform': platform,
            'package_format': 'docker'
        }
    )

    return result


# =============================================================================
# WORKFLOW 3: LEGAL COMPLIANCE PIPELINE
# =============================================================================

@flow(name="Legal Compliance Pipeline")
def legal_compliance_workflow(contract_text: str, regulations: list):
    """
    Complete legal compliance check:
    1. Review contract with LexMCP
    2. Check compliance with regulations
    3. Generate compliance report
    """
    orchestrator = initialize_orchestrator()

    # Step 1: Contract review
    review_result = execute_mcp_task(
        orchestrator,
        task_type='contract_review',
        task_data={'contract_text': contract_text}
    )

    # Step 2: Compliance check
    compliance_result = execute_mcp_task(
        orchestrator,
        task_type='compliance_check',
        task_data={
            'context': contract_text,
            'regulations': regulations,
            'jurisdiction': 'US'
        }
    )

    return {
        'contract_review': review_result,
        'compliance_check': compliance_result,
        'timestamp': datetime.now().isoformat()
    }


# =============================================================================
# WORKFLOW 4: INNOVATION RESEARCH PIPELINE
# =============================================================================

@flow(name="Innovation Research Pipeline")
def innovation_research_workflow(problem: str, market: str, competitors: list):
    """
    Complete innovation pipeline:
    1. Patent search with InnoMCP
    2. Market trend analysis
    3. Competitor analysis
    4. Idea generation
    5. Feasibility assessment
    """
    orchestrator = initialize_orchestrator()

    # Use complete innovation pipeline
    result = execute_mcp_task(
        orchestrator,
        task_type='innovation_pipeline',
        task_data={
            'problem_statement': problem,
            'market': market,
            'competitors': competitors
        }
    )

    return result


# =============================================================================
# WORKFLOW 5: CREATIVE CAMPAIGN CREATION
# =============================================================================

@flow(name="Creative Campaign Creation")
def creative_campaign_workflow(topic: str, platform: str = "social"):
    """
    Complete creative campaign:
    1. Generate script with CreativeMCP
    2. Design visual style
    3. Compose music (if video/podcast)
    4. Optimize for engagement
    """
    orchestrator = initialize_orchestrator()

    # Use complete campaign pipeline
    result = execute_mcp_task(
        orchestrator,
        task_type='complete_campaign',
        task_data={
            'topic': topic,
            'platform': platform,
            'include_visuals': True,
            'include_music': platform in ['video', 'podcast']
        }
    )

    return result


# =============================================================================
# WORKFLOW 6: PERSONALIZED LEARNING PATH
# =============================================================================

@flow(name="Personalized Learning Path Creation")
def learning_path_workflow(learner_id: str, subject: str, assessment: dict):
    """
    Complete personalized learning:
    1. Create learner profile with EduMCP
    2. Design curriculum
    3. Recommend content
    4. Setup feedback loop
    """
    orchestrator = initialize_orchestrator()

    # Use complete learning path pipeline
    result = execute_mcp_task(
        orchestrator,
        task_type='learning_path',
        task_data={
            'learner_id': learner_id,
            'subject': subject,
            'assessment_data': assessment
        }
    )

    return result


# =============================================================================
# WORKFLOW 7: MULTI-SYSTEM ORCHESTRATION
# =============================================================================

@flow(name="Multi-System Orchestration Demo")
def multi_system_demo_workflow():
    """
    Demonstrate coordination across all 6 MCP systems:
    1. FinPsy: Analyze market opportunity
    2. Inno: Research innovation landscape
    3. Creative: Create marketing campaign
    4. Lex: Review legal compliance
    5. PydiniRed: Automate workflow
    6. Edu: Train team on new product
    """
    orchestrator = initialize_orchestrator()

    workflow_steps = [
        {
            'name': 'market_analysis',
            'task_type': 'market_trends',
            'task_data': {'market': 'AI Healthcare'}
        },
        {
            'name': 'patent_research',
            'task_type': 'patent_search',
            'task_data': {
                'query': 'AI healthcare diagnosis',
                'max_results': 10
            }
        },
        {
            'name': 'campaign_creation',
            'task_type': 'content_generation',
            'task_data': {
                'content_type': 'article',
                'topic': 'AI Healthcare Innovation',
                'tone': 'professional'
            },
            'depends_on': 0  # Uses market analysis
        },
        {
            'name': 'compliance_check',
            'task_type': 'compliance_check',
            'task_data': {
                'context': 'AI healthcare product',
                'regulations': ['HIPAA', 'GDPR'],
                'jurisdiction': 'US'
            }
        },
        {
            'name': 'training_curriculum',
            'task_type': 'curriculum_design',
            'task_data': {
                'learner_profile': {'learning_style': 'visual'},
                'subject': 'AI Healthcare Product Training',
                'duration_weeks': 4
            }
        }
    ]

    result = orchestrator.execute_multi_system_workflow(
        workflow_steps=workflow_steps,
        workflow_name="ai_healthcare_launch"
    )

    return result


# =============================================================================
# DAILY RECURSIVE LEARNING WORKFLOW (Enhanced with MCP)
# =============================================================================

@flow(name="Enhanced Daily Recursive Learning")
def enhanced_recursive_learning_workflow():
    """
    Enhanced daily learning with MCP integration:
    1. Regular learning material processing
    2. MCP-powered deep analysis
    3. Cross-system knowledge synthesis
    """
    orchestrator = initialize_orchestrator()

    results = {
        'start_time': datetime.now().isoformat(),
        'mcp_analyses': []
    }

    # Example: Use EduMCP to recommend learning content
    learning_recommendation = execute_mcp_task(
        orchestrator,
        task_type='content_recommendation',
        task_data={
            'learner_profile': {'learning_style': 'visual'},
            'num_recommendations': 5
        }
    )

    results['learning_recommendations'] = learning_recommendation

    # Example: Use InnoMCP to identify innovation opportunities
    innovation_analysis = execute_mcp_task(
        orchestrator,
        task_type='idea_generation',
        task_data={
            'problem_statement': 'Improve learning efficiency',
            'num_ideas': 3
        }
    )

    results['innovation_ideas'] = innovation_analysis

    results['end_time'] = datetime.now().isoformat()

    return results


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("MCP WORKFLOW EXAMPLES")
    print("=" * 70)

    # Example 1: Financial Analysis
    print("\n1. Running Financial Analysis Workflow...")
    financial_result = financial_analysis_workflow(ticker="AAPL")
    print(f"   Status: {financial_result['analysis'].get('status')}")

    # Example 2: Creative Campaign
    print("\n2. Running Creative Campaign Workflow...")
    campaign_result = creative_campaign_workflow(
        topic="AI in Healthcare",
        platform="video"
    )
    print(f"   Status: {campaign_result.get('status')}")

    # Example 3: Multi-System Demo
    print("\n3. Running Multi-System Orchestration...")
    demo_result = multi_system_demo_workflow()
    print(f"   Workflow: {demo_result['workflow_name']}")
    print(f"   Steps: {demo_result['total_steps']}")
    print(f"   Successful: {demo_result['successful_steps']}")
    print(f"   Status: {demo_result['status']}")

    print("\n" + "=" * 70)
    print("All workflows completed successfully!")
    print("=" * 70)
