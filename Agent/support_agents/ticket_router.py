"""
Ticket Router - Main orchestrator for the multi-agent system
==========================================================

This class orchestrates the collaboration between different agents
to analyze and route customer support tickets.
"""

import sys
import os
from typing import Dict, Any
from datetime import datetime
import json

from .routing_agent import RoutingAgent
from .priority_agent import PriorityAgent
from .classification_agent import ClassificationAgent


class TicketRouter:
    """
    Main orchestrator that coordinates multiple agents to analyze and route tickets.
    """

    def __init__(self):
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
            print(ticket_id, "ticket ID")

            # Handle both 'title' and 'subject' keys for compatibility
            subject = ticket.get('title') or ticket.get('subject', 'No subject')

            # Handle both 'customer_type' and 'customer_tier' for compatibility
            customer_type = ticket.get('customer_type') or ticket.get('customer_tier', 'Regular')
            print(ticket.get('ticket_id'), "ticket ID from dict")
            print(f"\n🎫 Processing Ticket #{ticket_id}")
            print(f"Subject: {subject}")
            print(f"Customer: {customer_type}")

            # Step 1: Priority Analysis
            print("\n🔍 Step 1: Priority Agent Analysis")
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
            print("\n📊 Step 2: Classification Agent Analysis")
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

    def route_multiple_tickets(self, tickets: list) -> list:
        """
        Route multiple tickets through the analysis pipeline.

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
        print("=" * 60)

        return results

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
        """Get statistics about processed tickets"""
        if not self.processed_tickets:
            return {"message": "No tickets processed yet"}

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

        # Get ticket IDs for reference
        ticket_ids_processed = [t['ticket_id'] for t in self.processed_tickets]

        return {
            'total_tickets_processed': len(self.processed_tickets),
            'ticket_ids_processed': ticket_ids_processed,
            'successful_processing': len(self.processed_tickets) - error_count,
            'errors_encountered': error_count,
            'priority_distribution': priority_counts,
            'category_distribution': category_counts,
            'team_distribution': team_counts,
            'average_response_time_hours': round(avg_response_time, 2),
            'agents_used': {
                'priority_agent': getattr(self.priority_agent, 'name', 'PriorityAgent'),
                'classification_agent': getattr(self.classification_agent, 'name', 'ClassificationAgent'),
                'routing_agent': getattr(self.routing_agent, 'name', 'RoutingAgent')
            }
        }

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
        """Export processed tickets to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ticket_routing_results_{timestamp}.json"

        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_tickets': len(self.processed_tickets),
            'statistics': self.get_routing_statistics(),
            'detailed_results': self.processed_tickets
        }

        try:
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            print(f"📄 Results exported to: {filename}")
            return filename
        except Exception as e:
            print(f"❌ Failed to export results: {e}")
            return None