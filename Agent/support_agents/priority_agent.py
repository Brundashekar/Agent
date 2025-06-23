"""
Priority Agent - Analyzes ticket urgency and business impact
===========================================================

This agent evaluates support tickets to determine their priority level
based on urgency, business impact, and customer type.
"""

from enum import Enum
from typing import Dict, Any, List

class Priority(Enum):
    """Priority levels for support tickets"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class RealisticAgentSimulator:
    """
    Simulates realistic agent responses based on actual ticket analysis.
    In production, this would be replaced with actual Pydantic AI agents.
    """

    @staticmethod
    def analyze_priority(ticket: Dict[str, Any]) -> Dict[str, Any]:
        customer_tier = ticket.get('customer_tier', 'regular')
        revenue = ticket.get('monthly_revenue', 0)
        previous_tickets = ticket.get('previous_tickets', 0)
        account_age = ticket.get('account_age_days', 365)
        subject = ticket.get('subject', '').lower()
        message = ticket.get('message', '').lower()

        # Base scores
        urgency = 5
        business_impact = 3

        # Customer tier impact
        if customer_tier == 'enterprise':
            business_impact += 4
            urgency += 1
        elif customer_tier == 'premium':
            business_impact += 2
            urgency += 1

        # Revenue impact
        if revenue >= 25000:
            business_impact += 2
        elif revenue >= 5000:
            business_impact += 1

        # Urgency keywords
        urgent_keywords = ['urgent', 'broken', 'security', 'vulnerability', 'down', 'error']
        for keyword in urgent_keywords:
            if keyword in subject or keyword in message:
                urgency += 2
                break

        # Emotional language
        emotional_keywords = ['worst', 'terrible', 'switching', '!!!']
        for keyword in emotional_keywords:
            if keyword in subject or keyword in message:
                urgency += 1
                break

        # Account health (frequent issues)
        if previous_tickets > 15:
            urgency += 1
            business_impact += 1

        # New customer issues
        if account_age < 30 and previous_tickets == 0:
            urgency += 1

        # Cap scores
        urgency = min(10, max(1, urgency))
        business_impact = min(10, max(1, business_impact))

        escalation_needed = urgency >= 8 or business_impact >= 8 or (urgency >= 6 and business_impact >= 6)

        return {
            'urgency_score': urgency,
            'business_impact': business_impact,
            'escalation_needed': escalation_needed,
            'reasoning': f"Customer tier: {customer_tier}, Revenue impact: ${revenue}, Issue indicators suggest urgency level {urgency}"
        }
    @staticmethod
    def make_routing_decision(ticket: Dict[str, Any], priority: Dict[str, Any], classification: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate routing agent decision."""
        print(priority)
        category = classification['category']
        urgency = priority['urgency_score']
        business_impact = priority['business_impact']
        complexity = classification['complexity_score']
        escalation_needed = priority['escalation_needed']

        # Determine queue
        if category == 'Security' or escalation_needed:
            if category == 'Security':
                queue = 'SECURITY_TEAM'
            else:
                queue = 'ESCALATION'
        elif category == 'API' and complexity >= 6:
            queue = 'L2_API_TEAM'
        elif complexity >= 6 or category == 'Feature':
            queue = 'L3_ENGINEERING'
        elif complexity >= 4:
            queue = 'L2_TECHNICAL'
        else:
            queue = 'L1_GENERAL'

        # Determine priority level
        if urgency >= 8 or business_impact >= 8:
            priority_level = 'CRITICAL'
            sla_hours = 2
        elif urgency >= 6 or business_impact >= 6:
            priority_level = 'HIGH'
            sla_hours = 4
        elif urgency >= 4 or business_impact >= 4:
            priority_level = 'MEDIUM'
            sla_hours = 12
        else:
            priority_level = 'LOW'
            sla_hours = 24

        # Calculate confidence based on agent agreement
        urgency_norm = urgency / 10
        complexity_norm = complexity / 10
        priority_map = {'LOW': 0.2, 'MEDIUM': 0.5, 'HIGH': 0.8, 'CRITICAL': 1.0}
        priority_norm = priority_map[priority_level]

        # Calculate overall confidence score
        confidence = (urgency_norm + complexity_norm + priority_norm) / 3

        return {
            'queue': queue,
            'priority_level': priority_level,
            'sla_hours': sla_hours,
            'confidence': round(confidence, 2),
            'routing_factors': {
                'category': category,
                'urgency': urgency,
                'business_impact': business_impact,
                'complexity': complexity,
                'escalation_needed': escalation_needed
            }
        }

class PriorityAgent:
    """
    Agent responsible for analyzing ticket priority based on various factors.
    """

    def __init__(self):
        self.name = "PriorityAgent"
        self.description = "Analyzes ticket urgency and business impact"

        # Priority keywords for different levels with weights
        self.critical_keywords = {
            'outage': 4, 'down': 4, 'critical': 4, 'emergency': 4, 'urgent': 3,
            'production': 3, 'system failure': 4, 'security breach': 4,
            'data loss': 4, 'crash': 3, 'broken': 3, 'not working': 3
        }

        self.high_keywords = {
            'bug': 2, 'error': 2, 'issue': 2, 'problem': 2, 'malfunction': 3,
            'timeout': 2, 'slow performance': 2, 'performance': 2
        }

        self.medium_keywords = {
            'feature request': 1, 'enhancement': 1, 'improvement': 1,
            'question': 1, 'clarification': 1, 'documentation': 1,
            'help': 1, 'how to': 1
        }

        # Customer type multipliers
        self.customer_multipliers = {
            'enterprise': 1.5,
            'premium': 1.3,
            'business': 1.1,
            'regular': 1.0,
            'free': 0.8
        }

    def analyze_priority(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the priority of a support ticket.

        Args:
            ticket: Dictionary containing ticket information

        Returns:
            Dictionary with priority analysis results
        """
        # Handle both 'description' and 'content' keys
        content = ticket.get('description', ticket.get('content', '')).lower()

        # Handle both 'subject' and 'title' keys
        subject = ticket.get('subject', ticket.get('title', '')).lower()

        # Handle various customer type field names
        customer_type = (
            ticket.get('customer_type') or
            ticket.get('customer_tier') or
            ticket.get('account_type') or
            'regular'
        ).lower()

        # Combine subject and content for analysis
        full_text = f"{subject} {content}"

        # Calculate base priority score from keywords
        base_score = self._calculate_priority_score(full_text)

        # Apply customer type multiplier
        customer_multiplier = self.customer_multipliers.get(customer_type, 1.0)
        adjusted_score = base_score * customer_multiplier

        # Determine final priority level
        priority = self._determine_priority_level(adjusted_score)

        # Generate detailed reasoning
        reasoning = self._get_priority_reasoning(
            priority, customer_type, full_text, base_score, adjusted_score
        )

        return {
            'priority': priority.value,
            'priority_level': priority.value,  # Include both keys for compatibility
            'priority_score': round(adjusted_score, 2),
            'base_score': base_score,
            'customer_multiplier': customer_multiplier,
            'reasoning': reasoning,
            'keywords_found': self._find_matching_keywords(full_text),
            'agent': self.name
        }

    def _calculate_priority_score(self, text: str) -> float:
        """Calculate priority score based on weighted keyword analysis"""
        score = 0.0

        # Check critical keywords (highest weight)
        critical_score = 0.0
        for keyword, weight in self.critical_keywords.items():
            if keyword in text:
                critical_score = max(critical_score, weight)

        # Check high priority keywords
        high_score = 0.0
        for keyword, weight in self.high_keywords.items():
            if keyword in text:
                high_score = max(high_score, weight)

        # Check medium priority keywords
        medium_score = 0.0
        for keyword, weight in self.medium_keywords.items():
            if keyword in text:
                medium_score = max(medium_score, weight)

        # Take the highest score from any category
        score = max(critical_score, high_score, medium_score)

        # If no keywords found, assign baseline score
        if score == 0:
            score = 1.0  # Default baseline score

        return score

    def _determine_priority_level(self, score: float) -> Priority:
        """Determine priority level based on adjusted score"""
        if score >= 4.0:
            return Priority.CRITICAL
        elif score >= 3.0:
            return Priority.HIGH
        elif score >= 2.0:
            return Priority.MEDIUM
        else:
            return Priority.LOW

    def _find_matching_keywords(self, text: str) -> Dict[str, List[str]]:
        """Find all matching keywords in the text"""
        found_keywords = {
            'critical': [],
            'high': [],
            'medium': []
        }

        for keyword in self.critical_keywords:
            if keyword in text:
                found_keywords['critical'].append(keyword)

        for keyword in self.high_keywords:
            if keyword in text:
                found_keywords['high'].append(keyword)

        for keyword in self.medium_keywords:
            if keyword in text:
                found_keywords['medium'].append(keyword)

        return found_keywords

    def _get_priority_reasoning(self, priority: Priority, customer_type: str,
                              text: str, base_score: float, adjusted_score: float) -> str:
        """Generate detailed reasoning for the priority assignment"""
        reasons = []

        # Priority level reasoning
        if priority == Priority.CRITICAL:
            reasons.append("Contains critical system impact indicators")
        elif priority == Priority.HIGH:
            reasons.append("Contains high-impact issue indicators")
        elif priority == Priority.MEDIUM:
            reasons.append("Standard support request")
        else:
            reasons.append("Low impact or informational request")

        # Customer type impact
        if customer_type in ['enterprise', 'premium', 'business']:
            reasons.append(f"Premium customer tier ({customer_type})")
        elif customer_type == 'free':
            reasons.append("Free tier customer")

        # Score information
        if base_score != adjusted_score:
            reasons.append(f"Score adjusted from {base_score} to {adjusted_score:.2f}")

        # Keyword matches
        keywords_found = self._find_matching_keywords(text)
        total_keywords = sum(len(kw_list) for kw_list in keywords_found.values())
        if total_keywords > 0:
            reasons.append(f"Found {total_keywords} priority indicator(s)")

        return "; ".join(reasons)

    def get_priority_statistics(self) -> Dict[str, Any]:
        """Get information about the priority analysis capabilities"""
        return {
            'agent_name': self.name,
            'priority_levels': [p.value for p in Priority],
            'critical_keywords_count': len(self.critical_keywords),
            'high_keywords_count': len(self.high_keywords),
            'medium_keywords_count': len(self.medium_keywords),
            'supported_customer_types': list(self.customer_multipliers.keys()),
            'description': self.description
        }