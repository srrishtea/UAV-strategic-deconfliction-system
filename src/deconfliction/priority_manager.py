"""
Priority Manager for UAV fleet operations.
Handles dynamic priority assignment and mission-critical operations.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
import time

# Import from the same package level
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uav.uav import UAV, UAVStatus, UAVType


class MissionType(Enum):
    """Types of missions with different priority levels."""
    EMERGENCY_RESPONSE = "emergency_response"
    MEDICAL_DELIVERY = "medical_delivery"
    SEARCH_RESCUE = "search_rescue"
    SURVEILLANCE = "surveillance"
    CARGO_DELIVERY = "cargo_delivery"
    PATROL = "patrol"
    TRAINING = "training"
    TESTING = "testing"


class PriorityLevel(Enum):
    """Priority levels for UAV operations."""
    CRITICAL = 1    # Emergency, life-threatening situations
    HIGH = 2        # Urgent operations
    MEDIUM = 3      # Standard operations
    LOW = 4         # Routine operations
    MINIMAL = 5     # Training, testing


class PriorityManager:
    """
    Manages dynamic priority assignment for UAV fleet operations.
    
    Handles:
    - Mission-based priority assignment
    - Dynamic priority adjustment
    - Conflict resolution priority
    - Emergency escalation
    """
    
    def __init__(self):
        self.mission_priorities = {
            MissionType.EMERGENCY_RESPONSE: PriorityLevel.CRITICAL,
            MissionType.MEDICAL_DELIVERY: PriorityLevel.CRITICAL,
            MissionType.SEARCH_RESCUE: PriorityLevel.HIGH,
            MissionType.SURVEILLANCE: PriorityLevel.HIGH,
            MissionType.CARGO_DELIVERY: PriorityLevel.MEDIUM,
            MissionType.PATROL: PriorityLevel.MEDIUM,
            MissionType.TRAINING: PriorityLevel.LOW,
            MissionType.TESTING: PriorityLevel.MINIMAL
        }
        
        self.dynamic_factors = {
            'fuel_critical': 1,      # Boost priority if fuel is critically low
            'battery_critical': 1,   # Boost priority if battery is critically low
            'weather_emergency': 1,  # Boost priority due to weather
            'airspace_violation': 2, # High boost for airspace issues
            'equipment_failure': 1   # Boost priority for equipment problems
        }
        
        self.priority_history = []  # Track priority changes
        
    def assign_mission_priority(self, uav: UAV, mission_type: MissionType, 
                              urgency_factor: float = 1.0) -> int:
        """
        Assign priority to a UAV based on its mission type.
        
        Args:
            uav: UAV to assign priority to
            mission_type: Type of mission
            urgency_factor: Multiplier for urgency (1.0 = normal, >1.0 = more urgent)
            
        Returns:
            Assigned priority level (1-5, lower is higher priority)
        """
        base_priority = self.mission_priorities[mission_type].value
        
        # Apply urgency factor
        if urgency_factor > 1.5:
            base_priority = max(1, base_priority - 1)  # Increase priority
        elif urgency_factor < 0.5:
            base_priority = min(5, base_priority + 1)  # Decrease priority
            
        # Apply UAV-specific factors
        adjusted_priority = self._apply_uav_factors(uav, base_priority)
        
        # Update UAV priority
        old_priority = uav.priority
        uav.priority = adjusted_priority
        
        # Log priority change
        self.priority_history.append({
            'uav_id': uav.id,
            'old_priority': old_priority,
            'new_priority': adjusted_priority,
            'mission_type': mission_type.value,
            'urgency_factor': urgency_factor,
            'timestamp': time.time()
        })
        
        return adjusted_priority
        
    def _apply_uav_factors(self, uav: UAV, base_priority: int) -> int:
        """
        Apply UAV-specific factors to adjust priority.
        
        Args:
            uav: UAV to evaluate
            base_priority: Base priority level
            
        Returns:
            Adjusted priority level
        """
        priority = base_priority
        
        # Fuel/battery critical situations
        if uav.fuel_level < 20.0 or uav.battery_level < 20.0:
            priority = max(1, priority - self.dynamic_factors['fuel_critical'])
            
        # Emergency landing situations
        if uav.emergency_landing:
            priority = 1  # Highest priority
            
        # Equipment status
        if uav.status == UAVStatus.EMERGENCY:
            priority = max(1, priority - self.dynamic_factors['equipment_failure'])
            
        return min(5, max(1, priority))  # Ensure priority stays in valid range
        
    def escalate_priority(self, uav: UAV, reason: str) -> int:
        """
        Escalate UAV priority due to emergency or critical situation.
        
        Args:
            uav: UAV to escalate
            reason: Reason for escalation
            
        Returns:
            New priority level
        """
        old_priority = uav.priority
        
        if reason in self.dynamic_factors:
            boost = self.dynamic_factors[reason]
            uav.priority = max(1, uav.priority - boost)
        else:
            uav.priority = max(1, uav.priority - 1)  # Default escalation
            
        self.priority_history.append({
            'uav_id': uav.id,
            'old_priority': old_priority,
            'new_priority': uav.priority,
            'action': 'escalation',
            'reason': reason,
            'timestamp': time.time()
        })
        
        return uav.priority
        
    def normalize_priorities(self, uav_list: List[UAV]) -> Dict[str, int]:
        """
        Normalize priorities across a fleet to avoid conflicts.
        Ensures no two UAVs have identical priorities if possible.
        
        Args:
            uav_list: List of UAVs to normalize
            
        Returns:
            Dictionary mapping UAV IDs to new priorities
        """
        # Sort UAVs by current priority and other factors
        sorted_uavs = sorted(uav_list, key=lambda u: (
            u.priority,
            u.fuel_level < 20.0,  # Fuel critical
            u.battery_level < 20.0,  # Battery critical
            u.status == UAVStatus.EMERGENCY,  # Emergency status
            u.id  # Tie-breaker with ID
        ))
        
        new_priorities = {}
        current_priority = 1
        
        for uav in sorted_uavs:
            # Check if we need to skip a priority level
            if uav.emergency_landing or uav.status == UAVStatus.EMERGENCY:
                new_priorities[uav.id] = 1
            else:
                new_priorities[uav.id] = current_priority
                current_priority += 1
                
        # Apply new priorities
        for uav in uav_list:
            if uav.id in new_priorities:
                old_priority = uav.priority
                uav.priority = new_priorities[uav.id]
                
                if old_priority != uav.priority:
                    self.priority_history.append({
                        'uav_id': uav.id,
                        'old_priority': old_priority,
                        'new_priority': uav.priority,
                        'action': 'normalization',
                        'timestamp': time.time()
                    })
                    
        return new_priorities
        
    def get_priority_conflicts(self, uav_list: List[UAV]) -> List[Tuple[UAV, UAV]]:
        """
        Identify UAVs with identical priorities that might need resolution.
        
        Args:
            uav_list: List of UAVs to check
            
        Returns:
            List of UAV pairs with same priority
        """
        priority_groups = {}
        
        for uav in uav_list:
            if uav.priority not in priority_groups:
                priority_groups[uav.priority] = []
            priority_groups[uav.priority].append(uav)
            
        conflicts = []
        for priority, uavs in priority_groups.items():
            if len(uavs) > 1:
                # Create pairs of UAVs with same priority
                for i in range(len(uavs)):
                    for j in range(i + 1, len(uavs)):
                        conflicts.append((uavs[i], uavs[j]))
                        
        return conflicts
        
    def calculate_dynamic_priority(self, uav: UAV, current_situation: Dict) -> int:
        """
        Calculate dynamic priority based on current situation.
        
        Args:
            uav: UAV to calculate priority for
            current_situation: Dictionary with situation parameters
            
        Returns:
            Calculated priority level
        """
        base_priority = uav.priority
        adjustments = 0
        
        # Weather conditions
        if current_situation.get('severe_weather', False):
            adjustments -= 1
            
        # Air traffic density
        traffic_density = current_situation.get('traffic_density', 0)
        if traffic_density > 0.8:  # High traffic
            adjustments -= 1
            
        # Mission progress
        mission_progress = current_situation.get('mission_progress', 1.0)
        if mission_progress > 0.8:  # Near completion
            adjustments -= 1
            
        # Equipment status
        if uav.fuel_level < 30.0 or uav.battery_level < 30.0:
            adjustments -= 1
            
        # Emergency zones
        if current_situation.get('in_emergency_zone', False):
            adjustments -= 2
            
        new_priority = max(1, min(5, base_priority + adjustments))
        return new_priority
        
    def get_priority_matrix(self, uav_list: List[UAV]) -> Dict:
        """
        Generate a priority matrix for the fleet.
        
        Args:
            uav_list: List of UAVs
            
        Returns:
            Dictionary with priority analysis
        """
        matrix = {
            'priorities': {},
            'distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            'conflicts': [],
            'recommendations': []
        }
        
        for uav in uav_list:
            matrix['priorities'][uav.id] = {
                'current': uav.priority,
                'status': uav.status.value,
                'fuel': uav.fuel_level,
                'battery': uav.battery_level,
                'mission_progress': len(uav.waypoints) - uav.current_waypoint_index if uav.waypoints else 0
            }
            matrix['distribution'][uav.priority] += 1
            
        # Identify conflicts and recommendations
        conflicts = self.get_priority_conflicts(uav_list)
        matrix['conflicts'] = [(c[0].id, c[1].id) for c in conflicts]
        
        # Generate recommendations
        if len(conflicts) > 0:
            matrix['recommendations'].append("Consider priority normalization")
            
        if matrix['distribution'][1] > 3:
            matrix['recommendations'].append("Too many critical priority UAVs")
            
        if matrix['distribution'][5] > len(uav_list) * 0.5:
            matrix['recommendations'].append("Consider increasing some priorities")
            
        return matrix
        
    def get_priority_history(self, uav_id: Optional[str] = None, 
                           limit: int = 50) -> List[Dict]:
        """
        Get priority change history.
        
        Args:
            uav_id: Filter by specific UAV ID (None for all)
            limit: Maximum number of records to return
            
        Returns:
            List of priority change records
        """
        history = self.priority_history
        
        if uav_id:
            history = [h for h in history if h['uav_id'] == uav_id]
            
        # Sort by timestamp (newest first) and limit
        sorted_history = sorted(history, key=lambda h: h['timestamp'], reverse=True)
        return sorted_history[:limit]
        
    def clear_history(self):
        """Clear priority change history."""
        self.priority_history.clear()
        
    def __str__(self) -> str:
        """String representation of the priority manager."""
        return f"PriorityManager: {len(self.priority_history)} priority changes tracked"
