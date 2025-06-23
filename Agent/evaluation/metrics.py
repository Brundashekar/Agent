"""
Routing Metrics and Evaluation
==============================

This module provides comprehensive evaluation metrics for the
multi-agent ticket routing system.
"""

from typing import List, Dict, Any
from collections import defaultdict, Counter
import statistics


# Option 1: If your ticket data has an 'id' field
def get_ticket_id(ticket_data):
    """Extract ticket ID from ticket data structure."""
    # Try common field names for ticket ID
    possible_id_fields = ['id', 'ticket_id', 'ticket_number', 'number', 'reference']

    for field in possible_id_fields:
        if isinstance(ticket_data, dict) and field in ticket_data:
            return ticket_data[field]

    # If no ID field found, return a default
    return "Unknown"


# Option 2: If you're processing a list of tickets with indices
def process_tickets_with_proper_ids(tickets, ticket_router):
    """Process tickets with proper ID display."""

    # If your tickets have predefined IDs
    ticket_ids = ["SUP-001", "SUP-002", "SUP-003", "SUP-004", "SUP-005", "SUP-006", "SUP-007", "SUP-008"]

    results = []

    for i, ticket in enumerate(tickets):
        # Use predefined ID or generate one
        ticket_id = ticket_ids[i] if i < len(ticket_ids) else f"SUP-{i + 1:03d}"

        print(f"🎫 Processing Ticket: {ticket_id}")
        print(f"Subject: {ticket.get('subject', 'No subject')}")
        print(f"Customer: {ticket.get('customer_tier', 'unknown')}")
        print()

        # Process the ticket
        result = ticket_router.process_ticket(ticket)

        # Add the ticket ID to the result
        result['ticket_id'] = ticket_id
        result['input_ticket'] = ticket

        results.append(result)

        print("------------------------------------------------------------")
        print()

    return results


# Option 3: If your ticket data structure needs the ID added
def add_ticket_ids_to_data(tickets):
    """Add ticket IDs to existing ticket data."""
    ticket_ids = ["SUP-001", "SUP-002", "SUP-003", "SUP-004", "SUP-005", "SUP-006", "SUP-007", "SUP-008"]

    for i, ticket in enumerate(tickets):
        if isinstance(ticket, dict):
            ticket['id'] = ticket_ids[i] if i < len(ticket_ids) else f"SUP-{i + 1:03d}"

    return tickets


class RoutingMetrics:
    """Class for evaluating routing performance and generating insights."""
    
    def __init__(self):
        """Initialize metrics calculator."""
        self.queue_priorities = {
            'L1_GENERAL': 1,
            'L2_TECHNICAL': 2, 
            'L2_API_TEAM': 2,
            'L3_ENGINEERING': 3,
            'SECURITY_TEAM': 4,
            'ESCALATION': 5
        }
    
    def evaluate_routing_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Comprehensive evaluation of routing results.
        
        Args:
            results: List of routing results from TicketRouter
            
        Returns:
            Dictionary containing evaluation metrics
        """
        print("📊 ROUTING EVALUATION METRICS")
        print("=" * 50)

        # Basic statistics
        self._print_basic_statistics(results)

        # Queue distribution
        self._print_queue_distribution(results)

        # Priority analysis
        self._print_priority_analysis(results)

        # Customer tier analysis
        self._print_customer_tier_analysis(results)

        # Confidence analysis
        self._print_confidence_analysis(results)

        # Performance insights
        self._print_performance_insights(results)

        return self._calculate_metrics(results)

    def _print_basic_statistics(self, results: List[Dict[str, Any]]):
        """Print basic routing statistics."""
        total_tickets = len(results)
        # print(f"Results data: {results}")

        # Fixed: Use 'priority_score' instead of 'urgency_score'
        avg_urgency = statistics.mean([r['priority_analysis']['priority_score'] for r in results])
        print(f"Avg urgency: {avg_urgency}")

        # Fixed: Use correct path for complexity score
        avg_complexity = statistics.mean([r['classification_analysis']['estimated_effort_hours'] for r in results])

        # Fixed: Use correct path for confidence score
        avg_confidence = statistics.mean([r['routing_decision']['routing_confidence'] for r in results])

        print(f"📋 Basic Statistics:")
        print(f"   Total Tickets Processed: {total_tickets}")
        print(f"   Average Priority Score: {avg_urgency:.1f}/10")
        print(f"   Average Estimated Effort Hours: {avg_complexity:.1f}")
        print(f"   Average Routing Confidence: {avg_confidence:.2f}")
        print()

    def _print_queue_distribution(self, results: List[Dict[str, Any]]):
        """Print queue distribution analysis."""
        # Fixed: Use correct path for queue information
        queue_counts = Counter([r['routing_decision']['recommended_queue'] for r in results])

        print(f"🎯 Queue Distribution:")
        for queue, count in queue_counts.most_common():
            percentage = (count / len(results)) * 100
            print(f"   {queue}: {count} tickets ({percentage:.1f}%)")
        print()

    def _print_priority_analysis(self, results: List[Dict[str, Any]]):
        """Print priority level analysis."""
        # Fixed: Use correct path for priority level
        priority_counts = Counter([r['routing_decision']['priority_info']['priority_level'] for r in results])

        print(f"🚨 Priority Distribution:")
        priority_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
        for priority in priority_order:
            # Make comparison case-insensitive
            count = sum(1 for p in priority_counts if p.upper() == priority)
            percentage = (count / len(results)) * 100 if len(results) > 0 else 0
            print(f"   {priority}: {count} tickets ({percentage:.1f}%)")
        print()

    def _print_customer_tier_analysis(self, results: List[Dict[str, Any]]):
        """Print customer tier routing analysis."""
        tier_queues = defaultdict(list)
        tier_priorities = defaultdict(list)

        for result in results:
            # Check if input_ticket exists in the structure
            if 'input_ticket' in result:
                tier = result['input_ticket']['customer_tier']
            else:
                # Fallback - extract from expected outcome or use default
                tier = 'unknown'

            queue = result['routing_decision']['recommended_queue']
            priority = result['routing_decision']['priority_info']['priority_level']

            tier_queues[tier].append(queue)
            tier_priorities[tier].append(priority)

        print(f"👥 Customer Tier Analysis:")
        for tier in ['enterprise', 'premium', 'free', 'unknown']:
            if tier in tier_queues:
                queues = tier_queues[tier]
                priorities = tier_priorities[tier]

                most_common_queue = Counter(queues).most_common(1)[0]
                most_common_priority = Counter(priorities).most_common(1)[0]

                print(f"   {tier.title()} customers:")
                print(f"     Most common queue: {most_common_queue[0]} ({most_common_queue[1]} tickets)")
                print(f"     Most common priority: {most_common_priority[0]} ({most_common_priority[1]} tickets)")
        print()

    def _print_confidence_analysis(self, results: List[Dict[str, Any]]):
        """Print confidence score analysis."""
        # Fixed: Use correct path for confidence score
        confidences = [r['routing_decision']['routing_confidence'] for r in results]

        low_confidence = [c for c in confidences if c < 0.7]
        medium_confidence = [c for c in confidences if 0.7 <= c < 0.85]
        high_confidence = [c for c in confidences if c >= 0.85]

        print(f"🎯 Confidence Analysis:")
        print(f"   High Confidence (≥0.85): {len(high_confidence)} tickets ({len(high_confidence)/len(results)*100:.1f}%)")
        print(f"   Medium Confidence (0.7-0.85): {len(medium_confidence)} tickets ({len(medium_confidence)/len(results)*100:.1f}%)")
        print(f"   Low Confidence (<0.7): {len(low_confidence)} tickets ({len(low_confidence)/len(results)*100:.1f}%)")

        if low_confidence:
            print(f"   → {len(low_confidence)} tickets may need human review")
        print()

    def _print_performance_insights(self, results: List[Dict[str, Any]]):
        """Print performance insights and recommendations."""
        print(f"💡 Performance Insights:")

        # Escalation rate - check if escalation_needed exists
        escalations = []
        for r in results:
            if 'escalation_needed' in r.get('priority_analysis', {}):
                if r['priority_analysis']['escalation_needed']:
                    escalations.append(r)
            elif r['routing_decision']['recommended_queue'] == 'ESCALATION':
                escalations.append(r)

        escalation_rate = len(escalations) / len(results) * 100
        print(f"   Escalation Rate: {escalation_rate:.1f}% ({len(escalations)} tickets)")

        # Security issues
        security_tickets = [r for r in results if r['classification_analysis']['category'].lower() == 'security']
        if security_tickets:
            print(f"   Security Issues: {len(security_tickets)} tickets require immediate attention")

        # High-value customer routing
        enterprise_tickets = []
        for r in results:
            if 'input_ticket' in r and r['input_ticket']['customer_tier'] == 'enterprise':
                enterprise_tickets.append(r)

        if enterprise_tickets:
            avg_enterprise_sla = statistics.mean([r['routing_decision']['estimated_sla_hours'] for r in enterprise_tickets])
            print(f"   Enterprise Customer SLA: {avg_enterprise_sla:.1f} hours average")

        # Category complexity
        categories = defaultdict(list)
        for result in results:
            cat = result['classification_analysis']['category']
            effort_hours = result['classification_analysis']['estimated_effort_hours']
            categories[cat].append(effort_hours)

        print(f"   Category Complexity (by effort hours):")
        for category, effort_hours in categories.items():
            avg_effort = statistics.mean(effort_hours)
            print(f"     {category}: {avg_effort:.1f} hours average effort")

        print()

    def _calculate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive metrics for programmatic use."""
        return {
            'total_tickets': len(results),
            'average_priority_score': statistics.mean([r['priority_analysis']['priority_score'] for r in results]),
            'average_effort_hours': statistics.mean([r['classification_analysis']['estimated_effort_hours'] for r in results]),
            'average_confidence': statistics.mean([r['routing_decision']['routing_confidence'] for r in results]),
            'escalation_rate': len([r for r in results if r['routing_decision']['recommended_queue'] == 'ESCALATION']) / len(results),
            'queue_distribution': dict(Counter([r['routing_decision']['recommended_queue'] for r in results])),
            'priority_distribution': dict(Counter([r['routing_decision']['priority_info']['priority_level'] for r in results])),
            'category_distribution': dict(Counter([r['classification_analysis']['category'] for r in results]))
        }

    def compare_routing_strategies(self, results_a: List[Dict[str, Any]], results_b: List[Dict[str, Any]],
                                 strategy_a_name: str = "Strategy A", strategy_b_name: str = "Strategy B"):
        """
        Compare two different routing strategies.

        Args:
            results_a: Results from first routing strategy
            results_b: Results from second routing strategy
            strategy_a_name: Name for first strategy
            strategy_b_name: Name for second strategy
        """
        print(f"⚖️  ROUTING STRATEGY COMPARISON")
        print(f"=" * 50)

        metrics_a = self._calculate_metrics(results_a)
        metrics_b = self._calculate_metrics(results_b)

        print(f"Strategy: {strategy_a_name} vs {strategy_b_name}")
        print(f"Average Confidence: {metrics_a['average_confidence']:.3f} vs {metrics_b['average_confidence']:.3f}")
        print(f"Escalation Rate: {metrics_a['escalation_rate']:.1%} vs {metrics_b['escalation_rate']:.1%}")

        # Determine better strategy
        if metrics_a['average_confidence'] > metrics_b['average_confidence']:
            print(f"🏆 {strategy_a_name} shows higher routing confidence")
        else:
            print(f"🏆 {strategy_b_name} shows higher routing confidence")