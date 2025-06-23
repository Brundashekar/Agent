"""
Ticket Router - Main orchestrator for the multi-agent system
==========================================================

This class orchestrates the collaboration between different agents
to analyze and route customer support tickets.
"""

import sys
import os
from typing import Dict, Any, List
from datetime import datetime
import json

# Remove the relative imports and use absolute imports
# from .routing_agent import RoutingAgent
# from .priority_agent import PriorityAgent
# from .classification_agent import ClassificationAgent


class TicketRouter:
    """
    Main orchestrator that coordinates multiple agents to analyze and route tickets.
    Enhanced with summary statistics integration.
    """

    def __init__(self):
        # Initialize agents (assuming they are available in the environment)
        self.priority_agent = PriorityAgent()
        self.classification_agent = ClassificationAgent()
        self.routing_agent = RoutingAgent()
        self.processed_tickets = []
        self.ticket_counter = 1

    def _get_ticket_id(self, ticket: Dict[str, Any]) -> str:
        """
        Extract or generate a ticket ID for processing.

        Args:
            ticket: Dictionary containing ticket information

        Returns:
            String ticket ID
        """
        # Try multiple possible ID field names
        ticket_id = (ticket.get('id') or
                    ticket.get('ticket_id') or
                    ticket.get('ticketId') or
                    ticket.get('ticket_number') or
                    ticket.get('ref') or
                    ticket.get('reference'))

        # If no ID found, generate one
        if not ticket_id:
            # Generate a unique ID using timestamp and counter
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            ticket_id = f"TKT-{timestamp}-{self.ticket_counter:04d}"
            self.ticket_counter += 1

            # Store the generated ID back in the ticket for consistency
            ticket['id'] = ticket_id

        return str(ticket_id)

    def _normalize_priority_analysis(self, priority_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize priority analysis to ensure consistent key names"""
        normalized = priority_analysis.copy()

        # Ensure 'priority_level' exists
        if 'priority_level' not in normalized and 'priority' in normalized:
            normalized['priority_level'] = normalized['priority']
        elif 'priority_level' not in normalized:
            normalized['priority_level'] = 'Medium'

        # Ensure 'priority' exists (for backwards compatibility)
        if 'priority' not in normalized and 'priority_level' in normalized:
            normalized['priority'] = normalized['priority_level']

        return normalized

    def _normalize_routing_decision(self, routing_decision: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize routing decision to ensure consistent key names"""
        normalized = routing_decision.copy()

        # Ensure required keys exist
        if 'recommended_queue' not in normalized:
            normalized['recommended_queue'] = normalized.get('queue', 'General Support')

        if 'assigned_team' not in normalized:
            normalized['assigned_team'] = normalized.get('team', 'Support Team')

        if 'expected_response_time_hours' not in normalized and 'estimated_sla_hours' not in normalized:
            normalized['expected_response_time_hours'] = 24  # Default 24 hours

        if 'routing_confidence' not in normalized:
            normalized['routing_confidence'] = 0.85  # Default confidence

        return normalized

    def route_ticket(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route a ticket through the complete multi-agent analysis pipeline.

        Args:
            ticket: Dictionary containing ticket information with keys like:
                   - id: ticket identifier
                   - title/subject: ticket subject line
                   - description: detailed description
                   - customer_type: type of customer (regular, premium, enterprise)
                   - created_at: timestamp when ticket was created

        Returns:
            Complete analysis and routing result
        """
        try:
            # Get or generate ticket ID
            ticket_id = self._get_ticket_id(ticket)

            # Handle both 'title' and 'subject' keys for compatibility
            subject = ticket.get('title') or ticket.get('subject', 'No subject')

            # Handle both 'customer_type' and 'customer_tier' for compatibility
            customer_type = ticket.get('customer_type') or ticket.get('customer_tier', 'Regular')

            print(f"\n🎫 Processing Ticket #{ticket_id}")
            print(f"Subject: {subject}")
            print(f"Customer: {customer_type}")

            # Step 1: Priority Analysis
            print("\n🔍 Step 1: Priority Analysis")
            try:
                priority_analysis = self.priority_agent.analyze_priority(ticket)
                priority_analysis = self._normalize_priority_analysis(priority_analysis)

                priority_level = priority_analysis.get('priority_level', 'Medium')
                print(f"   Priority: {priority_level.upper()}")
                print(f"   Score: {priority_analysis.get('priority_score', 'N/A')}")

            except Exception as e:
                print(f"   ⚠️ Priority analysis failed: {e}")
                priority_analysis = {
                    'priority_level': 'Medium',
                    'priority': 'Medium',
                    'priority_score': 0.5,
                    'error': str(e)
                }

            # Step 2: Classification Analysis
            print("\n📊 Step 2: Classification Analysis")
            try:
                classification_analysis = self.classification_agent.classify_ticket(ticket)

                # Ensure required keys exist
                if 'category' not in classification_analysis:
                    classification_analysis['category'] = 'General'
                if 'complexity' not in classification_analysis:
                    classification_analysis['complexity'] = 'Medium'

                print(f"   Category: {classification_analysis['category']}")
                print(f"   Complexity: {classification_analysis['complexity']}")
                print(f"   Estimated Effort: {classification_analysis.get('estimated_effort_hours', 'N/A')} hours")

            except Exception as e:
                print(f"   ⚠️ Classification analysis failed: {e}")
                classification_analysis = {
                    'category': 'General',
                    'complexity': 'Medium',
                    'estimated_effort_hours': 2,
                    'error': str(e)
                }

            # Step 3: Routing Decision
            print("\n🎯 Step 3: Routing Decision")
            try:
                routing_decision = self.routing_agent.route_ticket(
                    ticket,
                    priority_analysis,
                    classification_analysis
                )
                routing_decision = self._normalize_routing_decision(routing_decision)

                print(f"   ➤ ROUTED TO: {routing_decision['recommended_queue']}")
                print(f"   Assigned Team: {routing_decision['assigned_team']}")

                expected_response = routing_decision.get('expected_response_time_hours',
                                                       routing_decision.get('estimated_sla_hours', 'N/A'))
                print(f"   Expected Response: {expected_response} hours")

                confidence = routing_decision.get('routing_confidence', 0.85)
                print(f"   Confidence: {confidence * 100:.1f}%")

            except Exception as e:
                print(f"   ⚠️ Routing decision failed: {e}")
                routing_decision = {
                    'recommended_queue': 'General Support',
                    'assigned_team': 'Support Team',
                    'expected_response_time_hours': 24,
                    'routing_confidence': 0.5,
                    'error': str(e)
                }

            # Compile final result
            result = {
                'ticket_id': ticket_id,
                'processed_at': datetime.now().isoformat(),
                'original_ticket': ticket,
                'priority_analysis': priority_analysis,
                'classification_analysis': classification_analysis,
                'routing_decision': routing_decision,
                'summary': self._generate_summary(priority_analysis, classification_analysis, routing_decision)
            }

            # Store for metrics
            self.processed_tickets.append(result)

            # Print summary
            print(f"\n✅ Summary: {result['summary']}")
            print("-" * 60)

            return result

        except Exception as e:
            print(f"❌ Critical error in ticket routing: {e}")
            # Generate fallback ticket ID if not available
            fallback_ticket_id = self._get_ticket_id(ticket)

            # Return a fallback result
            fallback_result = {
                'ticket_id': fallback_ticket_id,
                'processed_at': datetime.now().isoformat(),
                'original_ticket': ticket,
                'priority_analysis': {'priority_level': 'Medium', 'priority': 'Medium'},
                'classification_analysis': {'category': 'General', 'complexity': 'Medium'},
                'routing_decision': {
                    'recommended_queue': 'General Support',
                    'assigned_team': 'Support Team',
                    'expected_response_time_hours': 24,
                    'routing_confidence': 0.5
                },
                'error': str(e),
                'summary': 'ERROR: Ticket routing failed - assigned to General Support with default settings'
            }

            self.processed_tickets.append(fallback_result)
            print("-" * 60)
            return fallback_result

    def route_multiple_tickets(self, tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Route multiple tickets through the analysis pipeline and display summary statistics.

        Args:
            tickets: List of ticket dictionaries

        Returns:
            List of routing results
        """
        results = []

        print(f"\n🚀 Starting batch processing of {len(tickets)} tickets...")
        print("=" * 60)

        for i, ticket in enumerate(tickets, 1):
            print(f"\n[Batch {i}/{len(tickets)}]")
            result = self.route_ticket(ticket)
            results.append(result)

        print(f"\n🎉 Batch processing complete! Processed {len(results)} tickets.")

        # Display comprehensive summary statistics
        self.print_comprehensive_summary(tickets, results)

        return results

    def print_comprehensive_summary(self, original_tickets: List[Dict[str, Any]], results: List[Dict[str, Any]]):
        """Print comprehensive summary including routing table and statistics"""

        # Print routing summary table
        print("\n📊 ROUTING SUMMARY")
        print("=" * 100)
        print(f"{'Ticket ID':<15} {'Customer':<12} {'Category':<12} {'Priority':<10} {'Team':<18} {'SLA (h)':<8}")
        print("-" * 100)

        for result in results:
            ticket_id = result['ticket_id']
            original_ticket = result['original_ticket']
            customer_tier = original_ticket.get('customer_tier', original_ticket.get('customer_type', 'Regular'))
            category = result['classification_analysis'].get('category', 'General')
            priority = result['priority_analysis'].get('priority_level', 'Medium')
            team = result['routing_decision'].get('assigned_team', 'Support Team')
            sla_hours = result['routing_decision'].get('estimated_sla_hours',
                                                     result['routing_decision'].get('expected_response_time_hours', 'N/A'))

            print(f"{ticket_id:<15} {customer_tier:<12} {category:<12} {priority:<10} {team:<18} {sla_hours:<8}")

        print("\n🎯 KEY INSIGHTS:")
        insights = self._generate_routing_insights(results)
        for insight in insights:
            print(f"• {insight}")

        # Display detailed statistics from RoutingAgent
        print("\n" + "="*100)
        print("📈 DETAILED ROUTING STATISTICS")
        print("="*100)
        self.routing_agent.print_summary_statistics()

    def _generate_routing_insights(self, results: List[Dict[str, Any]]) -> List[str]:
        """Generate key insights from routing results"""
        insights = []

        # Analyze patterns
        enterprise_tickets = [r for r in results if r['original_ticket'].get('customer_tier') == 'Enterprise']
        security_tickets = [r for r in results if 'Security' in r['routing_decision'].get('assigned_team', '')]
        high_priority_tickets = [r for r in results if r['priority_analysis'].get('priority_level') == 'Critical']

        if enterprise_tickets:
            insights.append(f"Enterprise customers: {len(enterprise_tickets)} tickets prioritized for specialized teams")

        if security_tickets:
            insights.append(f"Security incidents: {len(security_tickets)} tickets routed to Security Team for immediate attention")

        if high_priority_tickets:
            insights.append(f"Critical priority: {len(high_priority_tickets)} tickets with expedited SLA")

        # Team utilization insights
        team_counts = {}
        for result in results:
            team = result['routing_decision'].get('assigned_team', 'Unknown')
            team_counts[team] = team_counts.get(team, 0) + 1

        if team_counts:
            most_used_team = max(team_counts, key=team_counts.get)
            insights.append(f"Primary load: {most_used_team} handling {team_counts[most_used_team]} tickets")

        return insights

    def _generate_summary(self, priority_analysis: Dict[str, Any],
                          classification_analysis: Dict[str, Any],
                          routing_decision: Dict[str, Any]) -> str:
        """Generate a human-readable summary of the routing decision"""
        priority = priority_analysis.get('priority_level', priority_analysis.get('priority', 'Medium'))
        category = classification_analysis.get('category', 'General')
        team = routing_decision.get('assigned_team', 'Support Team')
        response_time = routing_decision.get('expected_response_time_hours',
                                           routing_decision.get('estimated_sla_hours', 'N/A'))

        return (f"{priority.upper()} priority {category} ticket assigned to "
                f"{team} team (expected response: {response_time}h)")

    def get_routing_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive routing statistics combining TicketRouter and RoutingAgent data.

        Returns:
            Combined statistics from both components
        """
        if not self.processed_tickets:
            return {"message": "No tickets processed yet"}

        # Get basic TicketRouter statistics
        basic_stats = self._get_basic_statistics()

        # Get detailed RoutingAgent statistics
        detailed_stats = self.routing_agent.get_summary_statistics()

        # Combine both statistics
        combined_stats = {
            'processing_overview': basic_stats,
            'routing_analysis': detailed_stats,
            'integration_metrics': self._get_integration_metrics()
        }

        return combined_stats

    def _get_basic_statistics(self) -> Dict[str, Any]:
        """Get basic processing statistics from TicketRouter"""
        # Priority distribution
        priorities = [t['priority_analysis'].get('priority_level',
                     t['priority_analysis'].get('priority', 'Medium'))
                     for t in self.processed_tickets]
        priority_counts = {p: priorities.count(p) for p in set(priorities)}

        # Category distribution
        categories = [t['classification_analysis'].get('category', 'General') for t in self.processed_tickets]
        category_counts = {c: categories.count(c) for c in set(categories)}

        # Team distribution
        teams = [t['routing_decision'].get('assigned_team', 'Support Team') for t in self.processed_tickets]
        team_counts = {t: teams.count(t) for t in set(teams)}

        # Average response times
        response_times = []
        for t in self.processed_tickets:
            rt = t['routing_decision'].get('expected_response_time_hours',
                                         t['routing_decision'].get('estimated_sla_hours'))
            if rt and isinstance(rt, (int, float)):
                response_times.append(rt)

        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        # Error tracking
        error_count = sum(1 for t in self.processed_tickets if 'error' in t)

        return {
            'total_tickets_processed': len(self.processed_tickets),
            'successful_processing': len(self.processed_tickets) - error_count,
            'errors_encountered': error_count,
            'priority_distribution': priority_counts,
            'category_distribution': category_counts,
            'team_distribution': team_counts,
            'average_response_time_hours': round(avg_response_time, 2),
            'processing_success_rate': round(((len(self.processed_tickets) - error_count) / len(self.processed_tickets)) * 100, 2)
        }

    def _get_integration_metrics(self) -> Dict[str, Any]:
        """Get metrics specific to the integration between components"""
        if not self.processed_tickets:
            return {}

        # Agent utilization
        agents_used = {
            'priority_agent_calls': len(self.processed_tickets),
            'classification_agent_calls': len(self.processed_tickets),
            'routing_agent_calls': len(self.processed_tickets)
        }

        # Data consistency checks
        consistency_issues = 0
        for ticket in self.processed_tickets:
            # Check if priority levels are consistent
            p1 = ticket['priority_analysis'].get('priority_level')
            p2 = ticket['priority_analysis'].get('priority')
            if p1 and p2 and p1 != p2:
                consistency_issues += 1

        return {
            'agent_utilization': agents_used,
            'data_consistency_issues': consistency_issues,
            'pipeline_completion_rate': round((len(self.processed_tickets) / len(self.processed_tickets)) * 100, 2) if self.processed_tickets else 0
        }

    def print_summary_statistics(self):
        """Print comprehensive summary statistics"""
        stats = self.get_routing_statistics()

        if "message" in stats:
            print(stats["message"])
            return

        print("\n" + "="*80)
        print("📊 COMPREHENSIVE ROUTING STATISTICS")
        print("="*80)

        # Processing Overview
        print("\n🔧 PROCESSING OVERVIEW:")
        overview = stats['processing_overview']
        print(f"   Total Tickets: {overview['total_tickets_processed']}")
        print(f"   Successfully Processed: {overview['successful_processing']}")
        print(f"   Errors: {overview['errors_encountered']}")
        print(f"   Success Rate: {overview['processing_success_rate']}%")
        print(f"   Average Response Time: {overview['average_response_time_hours']} hours")

        # Integration Metrics
        print("\n🔗 INTEGRATION METRICS:")
        integration = stats['integration_metrics']
        print(f"   Agent Calls: {integration['agent_utilization']}")
        print(f"   Data Consistency Issues: {integration['data_consistency_issues']}")
        print(f"   Pipeline Completion Rate: {integration['pipeline_completion_rate']}%")

        # Detailed routing analysis is printed by the RoutingAgent
        print("\n" + "="*80)
        print("📈 DETAILED ROUTING ANALYSIS")
        print("="*80)
        self.routing_agent.print_summary_statistics()

    def get_ticket_by_id(self, ticket_id: str) -> Dict[str, Any]:
        """
        Retrieve a processed ticket by its ID.

        Args:
            ticket_id: The ticket ID to search for

        Returns:
            Ticket result dictionary or None if not found
        """
        for ticket in self.processed_tickets:
            if ticket['ticket_id'] == str(ticket_id):
                return ticket
        return None

    def print_processing_summary(self):
        """Print a summary of all processed tickets"""
        if not self.processed_tickets:
            print("\n📋 No tickets have been processed yet.")
            return

        print(f"\n📋 PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Total Tickets Processed: {len(self.processed_tickets)}")
        print("\nTickets by ID:")

        for ticket in self.processed_tickets:
            ticket_id = ticket['ticket_id']
            priority = ticket['priority_analysis'].get('priority_level',
                      ticket['priority_analysis'].get('priority', 'Medium'))
            category = ticket['classification_analysis'].get('category', 'General')
            team = ticket['routing_decision'].get('assigned_team', 'Support Team')

            # Show error status if present
            error_indicator = " ❌" if 'error' in ticket else ""

            print(f"  🎫 {ticket_id}: {priority.upper()} | {category} | → {team}{error_indicator}")

        print("=" * 60)

    def export_results(self, filename: str = None) -> str:
        """Export processed tickets and statistics to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ticket_routing_results_{timestamp}.json"

        # Get comprehensive statistics
        statistics = self.get_routing_statistics()

        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_tickets': len(self.processed_tickets),
            'comprehensive_statistics': statistics,
            'detailed_results': self.processed_tickets
        }

        try:
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            print(f"📄 Results and statistics exported to: {filename}")
            return filename
        except Exception as e:
            print(f"❌ Failed to export results: {e}")
            return None

    def reset_all_statistics(self):
        """Reset all statistics in both TicketRouter and RoutingAgent"""
        self.processed_tickets = []
        self.ticket_counter = 1
        self.routing_agent.reset_statistics()
        print("✅ All statistics have been reset.")

    def export_routing_statistics_only(self, filename: str = None):
        """Export only the routing statistics to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"routing_statistics_{timestamp}.json"

        self.routing_agent.export_statistics_to_json(filename)


# Example usage and demo functions
def create_sample_tickets():
    """Create sample tickets for testing"""
    return [
        {
            'id': 'TKT-001',
            'title': 'Cannot login to my account',
            'description': 'I have been trying to login for the past hour but keep getting error messages',
            'customer_tier': 'Free',
            'created_at': '2025-01-15T10:30:00Z'
        },
        {
            'id': 'TKT-002',
            'title': 'UI is very slow and unresponsive',
            'description': 'The dashboard takes forever to load and buttons are not working properly',
            'customer_tier': 'Enterprise',
            'created_at': '2025-01-15T11:00:00Z'
        },
        {
            'id': 'TKT-003',
            'title': 'Feature request: bulk export functionality',
            'description': 'We need ability to export all our data in bulk format for compliance',
            'customer_tier': 'Premium',
            'created_at': '2025-01-15T11:30:00Z'
        },
        {
            'id': 'TKT-004',
            'title': 'Possible security breach detected',
            'description': 'Suspicious login attempts from unknown IP addresses, need immediate help',
            'customer_tier': 'Enterprise',
            'created_at': '2025-01-15T12:00:00Z'
        }
    ]

def demo_summary_statistics():
    """Demonstrate the summary statistics functionality"""
    print("🚀 DEMO: Multi-Agent Ticket Routing with Summary Statistics")
    print("="*80)

    # Create router and sample tickets
    router = TicketRouter()
    tickets = create_sample_tickets()

    # Process tickets
    results = router.route_multiple_tickets(tickets)

    # Print comprehensive statistics
    print("\n📊 FINAL COMPREHENSIVE STATISTICS:")
    router.print_summary_statistics()

    # Export results
    filename = router.export_results()
    print(f"\n💾 All data exported to: {filename}")

if __name__ == "__main__":
    demo_summary_statistics()