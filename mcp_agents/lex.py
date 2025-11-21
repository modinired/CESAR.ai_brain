"""
LexMCP - Legal Compliance & Contract Analysis System
======================================================

Complete production implementation for legal document analysis, contract review,
compliance checking, and regulatory tracking.

This system:
- Parses and analyzes legal documents
- Reviews contracts for risks and obligations
- Checks compliance against regulations
- Tracks regulatory changes
- Provides legal risk assessments
"""

import json
import os
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
import logging
from collections import defaultdict

from .base_agent import BaseMCPAgent

# Optional: OpenAI for advanced NLP
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# =============================================================================
# LAW PARSER AGENT
# =============================================================================

class LawParserAgent(BaseMCPAgent):
    """
    Parse and extract key information from legal documents
    """

    def __init__(self, db_dsn: str = None, openai_api_key: str = None):
        super().__init__(
            agent_id='mcp_lex_parser',
            mcp_system='lex',
            db_dsn=db_dsn
        )
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        if OPENAI_AVAILABLE and self.openai_api_key:
            openai.api_key = self.openai_api_key

    def process(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process legal document parsing

        Args:
            task_input: {
                'document_text': str,
                'document_type': str (optional: 'contract', 'statute', 'regulation'),
                'extract_entities': bool (optional)
            }

        Returns:
            Dict with parsed legal document
        """
        document_text = task_input.get('document_text', '')
        document_type = task_input.get('document_type', 'contract')
        extract_entities = task_input.get('extract_entities', True)

        parsed = self.parse_legal_document(
            document_text,
            document_type,
            extract_entities
        )

        return {
            'document_type': document_type,
            'parsed_data': parsed
        }

    def parse_legal_document(
        self,
        document_text: str,
        document_type: str,
        extract_entities: bool
    ) -> Dict[str, Any]:
        """
        Parse legal document and extract key information

        Args:
            document_text: Full text of document
            document_type: Type of legal document
            extract_entities: Whether to extract named entities

        Returns:
            Dict with parsed information
        """
        parsed = {
            'sections': [],
            'entities': {},
            'key_terms': [],
            'dates': [],
            'amounts': [],
            'parties': []
        }

        # Extract sections
        parsed['sections'] = self._extract_sections(document_text)

        # Extract dates
        parsed['dates'] = self._extract_dates(document_text)

        # Extract monetary amounts
        parsed['amounts'] = self._extract_amounts(document_text)

        # Extract parties (for contracts)
        if document_type == 'contract':
            parsed['parties'] = self._extract_parties(document_text)

        # Extract key legal terms
        parsed['key_terms'] = self._extract_key_terms(document_text)

        # Entity extraction (if OpenAI available)
        if extract_entities and OPENAI_AVAILABLE and self.openai_api_key:
            parsed['entities'] = self._extract_entities_ai(document_text)
        else:
            parsed['entities'] = self._extract_entities_basic(document_text)

        return parsed

    def _extract_sections(self, text: str) -> List[Dict[str, str]]:
        """Extract document sections"""
        sections = []

        # Pattern: Section numbers followed by title
        pattern = r'(?:Section|Article|Clause)\s+(\d+[\.\d]*)\s*[:\-]?\s*([^\n]+)'

        for match in re.finditer(pattern, text, re.IGNORECASE):
            sections.append({
                'number': match.group(1),
                'title': match.group(2).strip()
            })

        return sections

    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates from text"""
        dates = []

        # Common date patterns
        patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
            r'\b\d{4}-\d{2}-\d{2}\b',       # YYYY-MM-DD
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)

        return list(set(dates))  # Remove duplicates

    def _extract_amounts(self, text: str) -> List[Dict[str, Any]]:
        """Extract monetary amounts"""
        amounts = []

        # Pattern: $X,XXX.XX or USD X,XXX
        pattern = r'(?:\$|USD\s*)(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'

        for match in re.finditer(pattern, text):
            amount_str = match.group(1).replace(',', '')
            amounts.append({
                'text': match.group(0),
                'value': float(amount_str)
            })

        return amounts

    def _extract_parties(self, text: str) -> List[str]:
        """Extract contract parties"""
        parties = []

        # Look for common party indicators
        patterns = [
            r'between\s+([A-Z][A-Za-z\s&,\.]+?)(?:\s+and|\s+\()',
            r'Party:\s*([A-Z][A-Za-z\s&,\.]+?)(?:\n|$)',
            r'(?:hereinafter|referred to as)\s+"([^"]+)"'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            parties.extend(matches)

        # Clean and deduplicate
        parties = [p.strip() for p in parties if len(p.strip()) > 3]
        return list(set(parties))

    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key legal terms"""
        # Common legal keywords
        legal_terms = [
            'indemnification', 'liability', 'warranty', 'termination',
            'confidential', 'intellectual property', 'force majeure',
            'arbitration', 'jurisdiction', 'governing law', 'breach',
            'damages', 'remedy', 'obligation', 'covenant', 'representation'
        ]

        found_terms = []
        text_lower = text.lower()

        for term in legal_terms:
            if term in text_lower:
                found_terms.append(term)

        return found_terms

    def _extract_entities_basic(self, text: str) -> Dict[str, List[str]]:
        """Basic entity extraction without AI"""
        entities = {
            'organizations': [],
            'locations': [],
            'laws': []
        }

        # Simple capitalized word sequences (organizations)
        org_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}(?:\s+(?:Inc|LLC|Ltd|Corp|Corporation))?)\b'
        entities['organizations'] = list(set(re.findall(org_pattern, text)))[:10]

        # Law references (e.g., "17 U.S.C. § 101")
        law_pattern = r'\b\d+\s+U\.S\.C\.\s+§\s+\d+'
        entities['laws'] = list(set(re.findall(law_pattern, text)))

        return entities

    def _extract_entities_ai(self, text: str) -> Dict[str, List[str]]:
        """AI-powered entity extraction using OpenAI"""
        try:
            # Use GPT for entity extraction
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Extract legal entities, organizations, laws, and key obligations from the text. Return as JSON with keys: organizations, laws, obligations."
                    },
                    {
                        "role": "user",
                        "content": text[:4000]  # Limit to avoid token limits
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )

            result = response.choices[0].message.content
            entities = json.loads(result)

            return entities

        except Exception as e:
            self.logger.error(f"AI entity extraction failed: {e}")
            return self._extract_entities_basic(text)


# =============================================================================
# CONTRACT ANALYZER AGENT
# =============================================================================

class ContractAnalyzerAgent(BaseMCPAgent):
    """
    Analyze contracts for risks, obligations, and key terms
    """

    def __init__(self, db_dsn: str = None, openai_api_key: str = None):
        super().__init__(
            agent_id='mcp_lex_contract_analyzer',
            mcp_system='lex',
            db_dsn=db_dsn
        )
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

    def process(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process contract analysis

        Args:
            task_input: {
                'contract_text': str,
                'analysis_type': str (optional: 'full', 'risk', 'obligations')
            }

        Returns:
            Dict with contract analysis
        """
        contract_text = task_input.get('contract_text', '')
        analysis_type = task_input.get('analysis_type', 'full')

        analysis = self.analyze_contract(contract_text, analysis_type)

        return {
            'analysis_type': analysis_type,
            'analysis': analysis
        }

    def analyze_contract(
        self,
        contract_text: str,
        analysis_type: str
    ) -> Dict[str, Any]:
        """
        Analyze contract for risks and obligations

        Args:
            contract_text: Full contract text
            analysis_type: Type of analysis to perform

        Returns:
            Dict with analysis results
        """
        analysis = {}

        if analysis_type in ['full', 'risk']:
            analysis['risk_assessment'] = self._assess_risks(contract_text)

        if analysis_type in ['full', 'obligations']:
            analysis['obligations'] = self._extract_obligations(contract_text)

        if analysis_type == 'full':
            analysis['key_clauses'] = self._identify_key_clauses(contract_text)
            analysis['missing_clauses'] = self._check_missing_clauses(contract_text)
            analysis['red_flags'] = self._identify_red_flags(contract_text)

        return analysis

    def _assess_risks(self, contract_text: str) -> Dict[str, Any]:
        """Assess contract risks"""
        risks = {
            'high': [],
            'medium': [],
            'low': [],
            'overall_score': 0  # 0-100, higher = riskier
        }

        text_lower = contract_text.lower()

        # High-risk indicators
        high_risk_terms = [
            ('unlimited liability', 'Unlimited liability exposure'),
            ('no limitation of liability', 'No liability cap'),
            ('perpetual license', 'Perpetual commitment'),
            ('automatic renewal', 'Auto-renewal without notice'),
            ('waive all claims', 'Broad claims waiver')
        ]

        for term, description in high_risk_terms:
            if term in text_lower:
                risks['high'].append(description)

        # Medium-risk indicators
        medium_risk_terms = [
            ('indemnify', 'Indemnification obligations'),
            ('exclusivity', 'Exclusivity requirements'),
            ('non-compete', 'Non-compete restrictions'),
            ('minimum purchase', 'Minimum purchase obligations')
        ]

        for term, description in medium_risk_terms:
            if term in text_lower:
                risks['medium'].append(description)

        # Calculate risk score
        risk_score = (len(risks['high']) * 30) + (len(risks['medium']) * 10)
        risks['overall_score'] = min(100, risk_score)

        return risks

    def _extract_obligations(self, contract_text: str) -> List[Dict[str, Any]]:
        """Extract contractual obligations"""
        obligations = []

        # Pattern: "shall" obligations
        shall_pattern = r'([A-Z][^.!?]*?\bshall\b[^.!?]*?[.!?])'

        for match in re.finditer(shall_pattern, contract_text):
            obligation_text = match.group(1).strip()

            obligations.append({
                'text': obligation_text,
                'type': 'mandatory',
                'severity': 'high'
            })

        # Pattern: "must" obligations
        must_pattern = r'([A-Z][^.!?]*?\bmust\b[^.!?]*?[.!?])'

        for match in re.finditer(must_pattern, contract_text):
            obligation_text = match.group(1).strip()

            obligations.append({
                'text': obligation_text,
                'type': 'mandatory',
                'severity': 'high'
            })

        return obligations[:20]  # Limit to top 20

    def _identify_key_clauses(self, contract_text: str) -> List[str]:
        """Identify key contract clauses"""
        key_clauses = []

        important_clauses = [
            'termination', 'liability', 'indemnification',
            'warranty', 'confidentiality', 'intellectual property',
            'payment terms', 'dispute resolution', 'force majeure',
            'assignment', 'governing law', 'severability'
        ]

        text_lower = contract_text.lower()

        for clause in important_clauses:
            if clause in text_lower:
                key_clauses.append(clause.title())

        return key_clauses

    def _check_missing_clauses(self, contract_text: str) -> List[str]:
        """Check for commonly missing but important clauses"""
        recommended_clauses = [
            'limitation of liability',
            'indemnification',
            'confidentiality',
            'termination',
            'dispute resolution',
            'force majeure',
            'intellectual property'
        ]

        text_lower = contract_text.lower()
        missing = []

        for clause in recommended_clauses:
            if clause not in text_lower:
                missing.append(clause.title())

        return missing

    def _identify_red_flags(self, contract_text: str) -> List[Dict[str, str]]:
        """Identify contract red flags"""
        red_flags = []

        text_lower = contract_text.lower()

        # Check for problematic terms
        problematic_terms = {
            'unilateral': 'Unilateral modification rights',
            'sole discretion': 'Sole discretion clauses',
            'without notice': 'Changes without notice',
            'as-is': 'As-is warranty disclaimer',
            'no refund': 'No refund policy'
        }

        for term, flag in problematic_terms.items():
            if term in text_lower:
                red_flags.append({
                    'flag': flag,
                    'severity': 'high' if term in ['unilateral', 'sole discretion'] else 'medium'
                })

        return red_flags


# =============================================================================
# RISK ASSESSMENT AGENT
# =============================================================================

class RiskAssessmentAgent(BaseMCPAgent):
    """
    Assess legal and compliance risks
    """

    def __init__(self, db_dsn: str = None):
        super().__init__(
            agent_id='mcp_lex_risk',
            mcp_system='lex',
            db_dsn=db_dsn
        )

    def process(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process risk assessment

        Args:
            task_input: {
                'context': str,
                'risk_areas': list (optional),
                'jurisdiction': str (optional)
            }

        Returns:
            Dict with risk assessment
        """
        context = task_input.get('context', '')
        risk_areas = task_input.get('risk_areas', ['all'])
        jurisdiction = task_input.get('jurisdiction', 'US')

        assessment = self.assess_risks(context, risk_areas, jurisdiction)

        return {
            'jurisdiction': jurisdiction,
            'assessment': assessment
        }

    def assess_risks(
        self,
        context: str,
        risk_areas: List[str],
        jurisdiction: str
    ) -> Dict[str, Any]:
        """
        Comprehensive risk assessment

        Args:
            context: Context or document to assess
            risk_areas: Specific risk areas to focus on
            jurisdiction: Legal jurisdiction

        Returns:
            Dict with risk assessment
        """
        assessment = {
            'overall_risk_level': 'medium',
            'risk_score': 0,  # 0-100
            'risk_categories': {},
            'recommendations': []
        }

        # Assess different risk categories
        if 'all' in risk_areas or 'privacy' in risk_areas:
            assessment['risk_categories']['privacy'] = self._assess_privacy_risk(
                context, jurisdiction
            )

        if 'all' in risk_areas or 'compliance' in risk_areas:
            assessment['risk_categories']['compliance'] = self._assess_compliance_risk(
                context, jurisdiction
            )

        if 'all' in risk_areas or 'ip' in risk_areas:
            assessment['risk_categories']['intellectual_property'] = self._assess_ip_risk(
                context
            )

        if 'all' in risk_areas or 'liability' in risk_areas:
            assessment['risk_categories']['liability'] = self._assess_liability_risk(
                context
            )

        # Calculate overall risk score
        category_scores = [
            cat.get('score', 0)
            for cat in assessment['risk_categories'].values()
        ]

        if category_scores:
            avg_score = sum(category_scores) / len(category_scores)
            assessment['risk_score'] = round(avg_score, 2)

            # Determine overall risk level
            if avg_score >= 70:
                assessment['overall_risk_level'] = 'high'
            elif avg_score >= 40:
                assessment['overall_risk_level'] = 'medium'
            else:
                assessment['overall_risk_level'] = 'low'

        # Generate recommendations
        assessment['recommendations'] = self._generate_recommendations(
            assessment['risk_categories']
        )

        return assessment

    def _assess_privacy_risk(self, context: str, jurisdiction: str) -> Dict[str, Any]:
        """Assess privacy and data protection risks"""
        risk = {
            'score': 0,
            'issues': [],
            'regulations': []
        }

        text_lower = context.lower()

        # Check for personal data handling
        data_terms = ['personal data', 'pii', 'personal information', 'user data']

        if any(term in text_lower for term in data_terms):
            risk['score'] += 30
            risk['issues'].append('Handles personal data')

            # Check jurisdiction-specific regulations
            if jurisdiction in ['US', 'California']:
                risk['regulations'].append('CCPA')
                risk['score'] += 10

            if jurisdiction == 'EU':
                risk['regulations'].append('GDPR')
                risk['score'] += 15

        # Check for security measures
        if 'encryption' not in text_lower and 'secure' not in text_lower:
            risk['score'] += 20
            risk['issues'].append('No explicit security measures mentioned')

        return risk

    def _assess_compliance_risk(self, context: str, jurisdiction: str) -> Dict[str, Any]:
        """Assess regulatory compliance risks"""
        risk = {
            'score': 0,
            'issues': [],
            'applicable_regulations': []
        }

        text_lower = context.lower()

        # Industry-specific regulations
        if 'health' in text_lower or 'medical' in text_lower:
            risk['applicable_regulations'].append('HIPAA')
            risk['score'] += 15

        if 'financial' in text_lower or 'payment' in text_lower:
            risk['applicable_regulations'].append('PCI-DSS')
            risk['score'] += 15

        if 'sox' in text_lower or 'sarbanes' in text_lower:
            risk['applicable_regulations'].append('SOX')
            risk['score'] += 10

        # Compliance indicators
        if 'audit' not in text_lower:
            risk['score'] += 10
            risk['issues'].append('No audit provisions mentioned')

        return risk

    def _assess_ip_risk(self, context: str) -> Dict[str, Any]:
        """Assess intellectual property risks"""
        risk = {
            'score': 0,
            'issues': []
        }

        text_lower = context.lower()

        # IP protection checks
        if 'intellectual property' not in text_lower and 'ip' not in text_lower:
            risk['score'] += 25
            risk['issues'].append('No IP protection clauses')

        if 'copyright' not in text_lower:
            risk['score'] += 15
            risk['issues'].append('No copyright provisions')

        if 'trade secret' not in text_lower:
            risk['score'] += 10
            risk['issues'].append('No trade secret protection')

        return risk

    def _assess_liability_risk(self, context: str) -> Dict[str, Any]:
        """Assess liability risks"""
        risk = {
            'score': 0,
            'issues': []
        }

        text_lower = context.lower()

        # Liability checks
        if 'unlimited liability' in text_lower:
            risk['score'] += 40
            risk['issues'].append('Unlimited liability exposure')

        if 'limitation of liability' not in text_lower:
            risk['score'] += 25
            risk['issues'].append('No liability limitations')

        if 'indemnification' in text_lower:
            risk['score'] += 15
            risk['issues'].append('Indemnification obligations present')

        return risk

    def _generate_recommendations(
        self,
        risk_categories: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []

        for category, data in risk_categories.items():
            if data.get('score', 0) >= 50:
                recommendations.append(
                    f"High risk in {category.replace('_', ' ').title()}: "
                    f"Immediate review required"
                )

            for issue in data.get('issues', []):
                recommendations.append(f"Address: {issue}")

        return recommendations


# =============================================================================
# REGULATORY TRACKER AGENT
# =============================================================================

class RegulatoryTrackerAgent(BaseMCPAgent):
    """
    Track regulatory changes and compliance requirements
    """

    def __init__(self, db_dsn: str = None):
        super().__init__(
            agent_id='mcp_lex_regulatory',
            mcp_system='lex',
            db_dsn=db_dsn
        )

    def process(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process regulatory tracking

        Args:
            task_input: {
                'regulations': list,
                'jurisdiction': str (optional),
                'industry': str (optional)
            }

        Returns:
            Dict with regulatory tracking info
        """
        regulations = task_input.get('regulations', [])
        jurisdiction = task_input.get('jurisdiction', 'US')
        industry = task_input.get('industry')

        tracking = self.track_regulations(regulations, jurisdiction, industry)

        return {
            'jurisdiction': jurisdiction,
            'industry': industry,
            'tracking': tracking
        }

    def track_regulations(
        self,
        regulations: List[str],
        jurisdiction: str,
        industry: Optional[str]
    ) -> Dict[str, Any]:
        """
        Track compliance with regulations

        Args:
            regulations: List of regulations to track
            jurisdiction: Legal jurisdiction
            industry: Industry sector

        Returns:
            Dict with regulatory tracking data
        """
        tracking = {
            'active_regulations': [],
            'upcoming_changes': [],
            'compliance_checklist': []
        }

        # Load regulation database (would be from DB in production)
        reg_db = self._get_regulation_database(jurisdiction, industry)

        for reg_name in regulations:
            reg_info = reg_db.get(reg_name, {})

            if reg_info:
                tracking['active_regulations'].append({
                    'name': reg_name,
                    'status': 'active',
                    'last_updated': reg_info.get('last_updated'),
                    'key_requirements': reg_info.get('requirements', [])
                })

                tracking['compliance_checklist'].extend(
                    reg_info.get('checklist', [])
                )

        # Check for upcoming changes (simulated)
        tracking['upcoming_changes'] = self._check_upcoming_changes(
            regulations, jurisdiction
        )

        return tracking

    def _get_regulation_database(
        self,
        jurisdiction: str,
        industry: Optional[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Get regulation database (simulated)"""
        # This would query a real regulatory database in production
        reg_db = {
            'GDPR': {
                'last_updated': '2023-01-01',
                'requirements': [
                    'Data subject rights',
                    'Privacy by design',
                    'Data breach notification',
                    'Consent management'
                ],
                'checklist': [
                    'Implement consent mechanism',
                    'Create privacy policy',
                    'Establish data breach procedures',
                    'Appoint DPO if required'
                ]
            },
            'CCPA': {
                'last_updated': '2023-07-01',
                'requirements': [
                    'Consumer rights notice',
                    'Do not sell opt-out',
                    'Data inventory',
                    'Privacy policy'
                ],
                'checklist': [
                    'Update privacy policy',
                    'Implement opt-out mechanism',
                    'Conduct data mapping',
                    'Train staff on CCPA'
                ]
            },
            'HIPAA': {
                'last_updated': '2023-03-15',
                'requirements': [
                    'Administrative safeguards',
                    'Physical safeguards',
                    'Technical safeguards',
                    'Privacy rule compliance'
                ],
                'checklist': [
                    'Conduct risk assessment',
                    'Implement access controls',
                    'Encrypt PHI',
                    'Create BAA templates'
                ]
            },
            'PCI-DSS': {
                'last_updated': '2023-04-01',
                'requirements': [
                    'Secure network',
                    'Encrypt cardholder data',
                    'Access control',
                    'Monitoring and testing'
                ],
                'checklist': [
                    'Install firewall',
                    'Encrypt data transmission',
                    'Implement MFA',
                    'Conduct quarterly scans'
                ]
            }
        }

        return reg_db

    def _check_upcoming_changes(
        self,
        regulations: List[str],
        jurisdiction: str
    ) -> List[Dict[str, Any]]:
        """Check for upcoming regulatory changes"""
        # This would check a real regulatory update feed in production
        upcoming = []

        # Simulated upcoming changes
        if 'GDPR' in regulations:
            upcoming.append({
                'regulation': 'GDPR',
                'change': 'Updated guidelines on consent',
                'effective_date': '2024-01-01',
                'impact': 'medium'
            })

        if 'CCPA' in regulations:
            upcoming.append({
                'regulation': 'CCPA',
                'change': 'CPRA amendments taking effect',
                'effective_date': '2024-03-01',
                'impact': 'high'
            })

        return upcoming


# =============================================================================
# LEX ORCHESTRATOR
# =============================================================================

class LexOrchestrator:
    """
    Orchestrator for LexMCP legal compliance system

    Coordinates all legal agents:
    1. LawParserAgent - Parse legal documents
    2. ContractAnalyzerAgent - Analyze contracts
    3. RiskAssessmentAgent - Assess legal risks
    4. RegulatoryTrackerAgent - Track regulations
    """

    def __init__(self, db_dsn: str = None, openai_api_key: str = None):
        """
        Initialize Lex orchestrator

        Args:
            db_dsn: Database connection string
            openai_api_key: OpenAI API key
        """
        self.db_dsn = db_dsn or os.getenv(
            "DATABASE_URL",
            "postgresql://mcp_user:change-this-in-production-use-strong-password@postgres:5432/mcp"
        )
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        self.logger = logging.getLogger("LexOrchestrator")
        self.logger.info("Initializing LexMCP Orchestrator")

        # Initialize agents
        self.agents = {}
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize all Lex agents"""
        try:
            self.agents['parser'] = LawParserAgent(
                db_dsn=self.db_dsn,
                openai_api_key=self.openai_api_key
            )
            self.agents['contract'] = ContractAnalyzerAgent(
                db_dsn=self.db_dsn,
                openai_api_key=self.openai_api_key
            )
            self.agents['risk'] = RiskAssessmentAgent(db_dsn=self.db_dsn)
            self.agents['regulatory'] = RegulatoryTrackerAgent(db_dsn=self.db_dsn)

            self.logger.info(f"Initialized {len(self.agents)} Lex agents")

        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {e}")

    def execute_task(
        self,
        task_type: str,
        task_input: Dict[str, Any],
        material_id: Optional[uuid.UUID] = None,
        priority: int = 5
    ) -> Dict[str, Any]:
        """
        Execute a Lex task

        Args:
            task_type: Type of task
            task_input: Task input data
            material_id: Optional related material
            priority: Task priority

        Returns:
            Dict with task results
        """
        self.logger.info(f"Executing Lex task: {task_type}")

        try:
            if task_type == 'legal_analysis':
                return self.analyze_legal_document(task_input)

            elif task_type == 'contract_review':
                return self.review_contract(task_input)

            elif task_type == 'compliance_check':
                return self.check_compliance(task_input)

            elif task_type == 'regulatory_tracking':
                return self.agents['regulatory'].execute_task(
                    task_type, task_input, material_id, priority
                )

            else:
                return {
                    'status': 'error',
                    'error': f'Unknown task type: {task_type}'
                }

        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def analyze_legal_document(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete legal document analysis pipeline

        Args:
            task_input: {
                'document_text': str,
                'document_type': str (optional)
            }

        Returns:
            Dict with analysis results
        """
        # Step 1: Parse document
        parse_result = self.agents['parser'].execute_task(
            task_type='document_parsing',
            task_input=task_input
        )

        if parse_result['status'] != 'completed':
            return parse_result

        # Step 2: Assess risks
        risk_result = self.agents['risk'].execute_task(
            task_type='risk_assessment',
            task_input={'context': task_input.get('document_text', '')}
        )

        return {
            'status': 'completed',
            'parsed_document': parse_result['output']['parsed_data'],
            'risk_assessment': risk_result['output']['assessment']
        }

    def review_contract(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete contract review pipeline

        Args:
            task_input: {
                'contract_text': str
            }

        Returns:
            Dict with review results
        """
        contract_text = task_input.get('contract_text', '')

        # Step 1: Parse contract
        parse_result = self.agents['parser'].execute_task(
            task_type='document_parsing',
            task_input={
                'document_text': contract_text,
                'document_type': 'contract'
            }
        )

        # Step 2: Analyze contract
        analysis_result = self.agents['contract'].execute_task(
            task_type='contract_analysis',
            task_input={
                'contract_text': contract_text,
                'analysis_type': 'full'
            }
        )

        # Step 3: Risk assessment
        risk_result = self.agents['risk'].execute_task(
            task_type='risk_assessment',
            task_input={'context': contract_text}
        )

        return {
            'status': 'completed',
            'parsed_contract': parse_result['output']['parsed_data'],
            'contract_analysis': analysis_result['output']['analysis'],
            'risk_assessment': risk_result['output']['assessment']
        }

    def check_compliance(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check compliance with regulations

        Args:
            task_input: {
                'context': str,
                'regulations': list,
                'jurisdiction': str (optional)
            }

        Returns:
            Dict with compliance results
        """
        # Step 1: Risk assessment
        risk_result = self.agents['risk'].execute_task(
            task_type='risk_assessment',
            task_input={
                'context': task_input.get('context', ''),
                'jurisdiction': task_input.get('jurisdiction', 'US')
            }
        )

        # Step 2: Regulatory tracking
        regulatory_result = self.agents['regulatory'].execute_task(
            task_type='regulatory_tracking',
            task_input={
                'regulations': task_input.get('regulations', []),
                'jurisdiction': task_input.get('jurisdiction', 'US')
            }
        )

        return {
            'status': 'completed',
            'risk_assessment': risk_result['output']['assessment'],
            'regulatory_compliance': regulatory_result['output']['tracking']
        }

    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return {
            'system': 'lex',
            'status': 'active',
            'agents': list(self.agents.keys()),
            'agent_count': len(self.agents)
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_lex_orchestrator(
    db_dsn: str = None,
    openai_api_key: str = None
) -> LexOrchestrator:
    """
    Factory function to create Lex orchestrator

    Args:
        db_dsn: Database connection string
        openai_api_key: OpenAI API key

    Returns:
        LexOrchestrator instance
    """
    return LexOrchestrator(
        db_dsn=db_dsn,
        openai_api_key=openai_api_key
    )


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

if __name__ == "__main__":
    # Initialize orchestrator
    orchestrator = create_lex_orchestrator()

    # Example: Review a contract
    contract_text = """
    This Agreement is entered into on January 1, 2024, between
    Acme Corporation ("Company") and John Doe ("Contractor").

    1. Services
    Contractor shall provide software development services.

    2. Payment
    Company shall pay Contractor $10,000 per month.

    3. Termination
    Either party may terminate with 30 days notice.

    4. Liability
    Company's liability shall not exceed the fees paid.
    """

    result = orchestrator.review_contract({
        'contract_text': contract_text
    })

    print("Contract Review Result:", json.dumps(result, indent=2))
