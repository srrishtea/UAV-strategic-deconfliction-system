"""
Advanced deconfliction algorithms for UAV strategic conflict resolution.
Implements multiple sophisticated strategies for resolving UAV conflicts.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from enum import Enum
import math

# Import from the same package level
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uav.uav import UAV, UAVStatus, UAVType
from uav.fleet import ConflictInfo


class DeconflictionStrategy(Enum):
    """Available deconfliction strategies."""
    PRIORITY_BASED = "priority_based"
    ALTITUDE_LAYERING = "altitude_layering"
    GEOMETRIC_SEPARATION = "geometric_separation"
    VELOCITY_ADJUSTMENT = "velocity_adjustment"
    COOPERATIVE_PATHFINDING = "cooperative_pathfinding"
    EMERGENCY_AVOIDANCE = "emergency_avoidance"


class ManeuverType(Enum):
    """Types of avoidance maneuvers."""
    LATERAL_LEFT = "lateral_left"
    LATERAL_RIGHT = "lateral_right"
    ALTITUDE_UP = "altitude_up"
    ALTITUDE_DOWN = "altitude_down"
    SPEED_REDUCTION = "speed_reduction"
    LOITER = "loiter"
    EMERGENCY_STOP = "emergency_stop"


class DeconflictionAlgorithm:
    """
    Advanced algorithms for UAV deconfliction.
    
    This class implements multiple strategies for resolving conflicts:
    - Geometric separation using mathematical models
    - Velocity vector adjustments
    - Cooperative path planning
    - Emergency procedures
    """
    
    def __init__(self):
        self.safety_margin = 1.5  # Safety multiplier for separation distances
        self.max_altitude_change = 100.0  # meters
        self.max_speed_reduction = 0.5  # 50% of max speed
        self.loiter_radius = 30.0  # meters
        self.resolution_history = []  # Track past resolutions
        
    def resolve_conflict(self, conflict: ConflictInfo, strategy: DeconflictionStrategy) -> Dict:
        """
        Resolve a conflict using the specified strategy.
        
        Args:
            conflict: Conflict information
            strategy: Strategy to use for resolution
            
        Returns:
            Dictionary with resolution details and actions
        """
        resolution = {
            'conflict_id': f"{conflict.uav1.id}-{conflict.uav2.id}",
            'strategy': strategy.value,
            'severity': conflict.severity,
            'actions': [],
            'success': False
        }
        
        try:
            if strategy == DeconflictionStrategy.PRIORITY_BASED:
                resolution = self._priority_based_resolution(conflict, resolution)
            elif strategy == DeconflictionStrategy.ALTITUDE_LAYERING:
                resolution = self._altitude_layering_resolution(conflict, resolution)
            elif strategy == DeconflictionStrategy.GEOMETRIC_SEPARATION:
                resolution = self._geometric_separation_resolution(conflict, resolution)
            elif strategy == DeconflictionStrategy.VELOCITY_ADJUSTMENT:
                resolution = self._velocity_adjustment_resolution(conflict, resolution)
            elif strategy == DeconflictionStrategy.COOPERATIVE_PATHFINDING:
                resolution = self._cooperative_pathfinding_resolution(conflict, resolution)
            elif strategy == DeconflictionStrategy.EMERGENCY_AVOIDANCE:
                resolution = self._emergency_avoidance_resolution(conflict, resolution)
                
            self.resolution_history.append(resolution)
            
        except Exception as e:
            resolution['error'] = str(e)
            print(f"Error resolving conflict: {e}")
            
        return resolution
        
    def _priority_based_resolution(self, conflict: ConflictInfo, resolution: Dict) -> Dict:
        """
        Resolve conflict based on UAV priorities.
        Higher priority UAV continues, lower priority performs avoidance.
        """
        uav1, uav2 = conflict.uav1, conflict.uav2
        
        if uav1.priority < uav2.priority:  # Lower number = higher priority
            avoiding_uav, priority_uav = uav2, uav1
        elif uav2.priority < uav1.priority:
            avoiding_uav, priority_uav = uav1, uav2
        else:
            # Equal priority - use geometric separation
            return self._geometric_separation_resolution(conflict, resolution)
            
        # Calculate optimal avoidance maneuver
        maneuver = self._calculate_optimal_maneuver(avoiding_uav, priority_uav, conflict)
        self._execute_maneuver(avoiding_uav, maneuver)
        
        resolution['actions'].append({
            'uav_id': avoiding_uav.id,
            'action': 'priority_avoidance',
            'maneuver': maneuver['type'].value,
            'details': maneuver
        })
        
        resolution['success'] = True
        return resolution
        
    def _altitude_layering_resolution(self, conflict: ConflictInfo, resolution: Dict) -> Dict:
        """
        Resolve conflict by separating UAVs into different altitude layers.
        Creates vertical separation while maintaining horizontal paths.
        """
        uav1, uav2 = conflict.uav1, conflict.uav2
        
        # Calculate required altitude separation
        min_separation = max(uav1.min_separation, uav2.min_separation) * self.safety_margin
        
        # Determine altitude changes based on current altitudes and mission requirements
        if uav1.position[2] > uav2.position[2]:
            # UAV1 is higher, move it up more and UAV2 down
            altitude_change_1 = min_separation / 2
            altitude_change_2 = -min_separation / 2
        else:
            # UAV2 is higher, move it up more and UAV1 down
            altitude_change_1 = -min_separation / 2
            altitude_change_2 = min_separation / 2
            
        # Apply altitude changes
        new_altitude_1 = uav1.position[2] + altitude_change_1
        new_altitude_2 = uav2.position[2] + altitude_change_2
        
        # Ensure altitudes are within safe limits
        new_altitude_1 = max(50, min(500, new_altitude_1))  # 50m to 500m range
        new_altitude_2 = max(50, min(500, new_altitude_2))
        
        uav1.position[2] = new_altitude_1
        uav2.position[2] = new_altitude_2
        
        resolution['actions'].extend([
            {
                'uav_id': uav1.id,
                'action': 'altitude_change',
                'new_altitude': new_altitude_1,
                'change': altitude_change_1
            },
            {
                'uav_id': uav2.id,
                'action': 'altitude_change',
                'new_altitude': new_altitude_2,
                'change': altitude_change_2
            }
        ])
        
        resolution['success'] = True
        return resolution
        
    def _geometric_separation_resolution(self, conflict: ConflictInfo, resolution: Dict) -> Dict:
        """
        Resolve conflict using geometric analysis to find optimal separation paths.
        Uses vector mathematics to calculate minimal deviation paths.
        """
        uav1, uav2 = conflict.uav1, conflict.uav2
        
        # Calculate relative position and velocity vectors
        rel_pos = uav2.position - uav1.position
        rel_vel = uav2.velocity - uav1.velocity
        
        # Find closest point of approach
        if np.linalg.norm(rel_vel) > 0.1:
            time_to_cpa = -np.dot(rel_pos, rel_vel) / np.dot(rel_vel, rel_vel)
            time_to_cpa = max(0, time_to_cpa)  # Can't resolve past conflicts
        else:
            time_to_cpa = 0
            
        # Calculate separation vectors
        required_separation = max(uav1.min_separation, uav2.min_separation) * self.safety_margin
        
        # Create perpendicular separation vectors
        if np.linalg.norm(rel_pos[:2]) > 0:
            # Horizontal separation
            perp_vector = np.array([-rel_pos[1], rel_pos[0], 0])
            perp_vector = perp_vector / np.linalg.norm(perp_vector) * required_separation
        else:
            # Default separation if UAVs are vertically aligned
            perp_vector = np.array([required_separation, 0, 0])
            
        # Apply separation maneuvers
        maneuver_1 = perp_vector / 2
        maneuver_2 = -perp_vector / 2
        
        # Modify velocities temporarily for separation
        separation_time = 10.0  # seconds
        uav1.velocity += maneuver_1 / separation_time
        uav2.velocity += maneuver_2 / separation_time
        
        resolution['actions'].extend([
            {
                'uav_id': uav1.id,
                'action': 'geometric_separation',
                'maneuver_vector': maneuver_1.tolist(),
                'duration': separation_time
            },
            {
                'uav_id': uav2.id,
                'action': 'geometric_separation',
                'maneuver_vector': maneuver_2.tolist(),
                'duration': separation_time
            }
        ])
        
        resolution['success'] = True
        return resolution
        
    def _velocity_adjustment_resolution(self, conflict: ConflictInfo, resolution: Dict) -> Dict:
        """
        Resolve conflict by adjusting UAV velocities (speed and direction).
        Uses temporal separation by having one UAV slow down or speed up.
        """
        uav1, uav2 = conflict.uav1, conflict.uav2
        
        # Determine which UAV should adjust velocity
        if uav1.priority <= uav2.priority:
            adjusting_uav, other_uav = uav2, uav1
        else:
            adjusting_uav, other_uav = uav1, uav2
            
        # Calculate velocity adjustment
        current_speed = np.linalg.norm(adjusting_uav.velocity)
        
        if current_speed > adjusting_uav.max_speed * 0.3:
            # Reduce speed for temporal separation
            speed_reduction = min(current_speed * self.max_speed_reduction, 
                                current_speed - adjusting_uav.max_speed * 0.2)
            new_speed = current_speed - speed_reduction
            
            # Maintain direction, reduce magnitude
            if current_speed > 0:
                velocity_factor = new_speed / current_speed
                adjusting_uav.velocity *= velocity_factor
                
            action_type = 'speed_reduction'
            adjustment_value = speed_reduction
        else:
            # UAV is already slow, use lateral maneuver instead
            return self._geometric_separation_resolution(conflict, resolution)
            
        resolution['actions'].append({
            'uav_id': adjusting_uav.id,
            'action': action_type,
            'adjustment': adjustment_value,
            'new_speed': new_speed,
            'duration': conflict.time_to_conflict + 10.0
        })
        
        resolution['success'] = True
        return resolution
        
    def _cooperative_pathfinding_resolution(self, conflict: ConflictInfo, resolution: Dict) -> Dict:
        """
        Resolve conflict using cooperative pathfinding where both UAVs adjust their paths.
        Implements a simplified version of distributed path planning.
        """
        uav1, uav2 = conflict.uav1, conflict.uav2
        
        # Get current targets for both UAVs
        target1 = uav1.get_current_target()
        target2 = uav2.get_current_target()
        
        if target1 is None or target2 is None:
            # Fall back to geometric separation if no targets
            return self._geometric_separation_resolution(conflict, resolution)
            
        # Calculate intermediate waypoints for both UAVs
        required_separation = max(uav1.min_separation, uav2.min_separation) * self.safety_margin
        
        # Create offset waypoints
        midpoint = (uav1.position + uav2.position) / 2
        separation_vector = uav2.position - uav1.position
        
        if np.linalg.norm(separation_vector) > 0:
            sep_unit = separation_vector / np.linalg.norm(separation_vector)
            offset = sep_unit * required_separation
            
            # Create intermediate waypoints for cooperative navigation
            waypoint1 = midpoint - offset
            waypoint2 = midpoint + offset
            
            # Insert waypoints into UAV missions
            uav1.waypoints.insert(uav1.current_waypoint_index, waypoint1)
            uav2.waypoints.insert(uav2.current_waypoint_index, waypoint2)
            
            resolution['actions'].extend([
                {
                    'uav_id': uav1.id,
                    'action': 'cooperative_waypoint',
                    'waypoint': waypoint1.tolist(),
                    'position_in_mission': uav1.current_waypoint_index
                },
                {
                    'uav_id': uav2.id,
                    'action': 'cooperative_waypoint',
                    'waypoint': waypoint2.tolist(),
                    'position_in_mission': uav2.current_waypoint_index
                }
            ])
            
            resolution['success'] = True
        else:
            # UAVs are at same position - use altitude separation
            resolution = self._altitude_layering_resolution(conflict, resolution)
            
        return resolution
        
    def _emergency_avoidance_resolution(self, conflict: ConflictInfo, resolution: Dict) -> Dict:
        """
        Emergency conflict resolution for critical situations.
        Implements immediate and aggressive avoidance maneuvers.
        """
        uav1, uav2 = conflict.uav1, conflict.uav2
        
        if conflict.severity == "CRITICAL":
            # Immediate emergency stop for both UAVs
            uav1.emergency_stop()
            uav2.emergency_stop()
            
            resolution['actions'].extend([
                {
                    'uav_id': uav1.id,
                    'action': 'emergency_stop',
                    'reason': 'critical_conflict'
                },
                {
                    'uav_id': uav2.id,
                    'action': 'emergency_stop',
                    'reason': 'critical_conflict'
                }
            ])
        else:
            # Aggressive separation maneuver
            required_separation = max(uav1.min_separation, uav2.min_separation) * 2.0
            
            # Move both UAVs away from each other
            separation_vector = uav2.position - uav1.position
            if np.linalg.norm(separation_vector) > 0:
                sep_unit = separation_vector / np.linalg.norm(separation_vector)
                
                # Apply strong separation forces
                uav1.velocity = -sep_unit * uav1.max_speed * 0.8
                uav2.velocity = sep_unit * uav2.max_speed * 0.8
                
                resolution['actions'].extend([
                    {
                        'uav_id': uav1.id,
                        'action': 'emergency_separation',
                        'direction': (-sep_unit).tolist(),
                        'intensity': 0.8
                    },
                    {
                        'uav_id': uav2.id,
                        'action': 'emergency_separation',
                        'direction': sep_unit.tolist(),
                        'intensity': 0.8
                    }
                ])
                
        resolution['success'] = True
        return resolution
        
    def _calculate_optimal_maneuver(self, avoiding_uav: UAV, priority_uav: UAV, conflict: ConflictInfo) -> Dict:
        """
        Calculate the optimal avoidance maneuver for a UAV.
        
        Args:
            avoiding_uav: UAV that needs to perform avoidance
            priority_uav: UAV with higher priority
            conflict: Conflict information
            
        Returns:
            Dictionary with maneuver details
        """
        # Analyze the conflict geometry
        rel_pos = priority_uav.position - avoiding_uav.position
        rel_vel = priority_uav.velocity - avoiding_uav.velocity
        
        maneuver = {
            'type': ManeuverType.LATERAL_LEFT,
            'magnitude': 0.0,
            'duration': 0.0,
            'cost': 0.0
        }
        
        # Choose maneuver type based on geometry and constraints
        if abs(rel_pos[2]) < 20.0:  # Similar altitudes
            # Prefer lateral maneuver
            if rel_pos[0] > 0:  # Priority UAV is to the right
                maneuver['type'] = ManeuverType.LATERAL_LEFT
            else:
                maneuver['type'] = ManeuverType.LATERAL_RIGHT
            maneuver['magnitude'] = avoiding_uav.min_separation * 1.5
        else:
            # Use altitude separation
            if avoiding_uav.position[2] < priority_uav.position[2]:
                maneuver['type'] = ManeuverType.ALTITUDE_DOWN
            else:
                maneuver['type'] = ManeuverType.ALTITUDE_UP
            maneuver['magnitude'] = 50.0  # meters
            
        maneuver['duration'] = max(10.0, conflict.time_to_conflict)
        maneuver['cost'] = self._calculate_maneuver_cost(avoiding_uav, maneuver)
        
        return maneuver
        
    def _execute_maneuver(self, uav: UAV, maneuver: Dict):
        """Execute a calculated maneuver on a UAV."""
        maneuver_type = maneuver['type']
        magnitude = maneuver['magnitude']
        
        if maneuver_type == ManeuverType.LATERAL_LEFT:
            uav.velocity[1] -= magnitude / maneuver['duration']
        elif maneuver_type == ManeuverType.LATERAL_RIGHT:
            uav.velocity[1] += magnitude / maneuver['duration']
        elif maneuver_type == ManeuverType.ALTITUDE_UP:
            uav.position[2] += magnitude
        elif maneuver_type == ManeuverType.ALTITUDE_DOWN:
            uav.position[2] -= magnitude
        elif maneuver_type == ManeuverType.SPEED_REDUCTION:
            current_speed = np.linalg.norm(uav.velocity)
            if current_speed > 0:
                reduction_factor = 1.0 - (magnitude / current_speed)
                uav.velocity *= max(0.2, reduction_factor)
        elif maneuver_type == ManeuverType.EMERGENCY_STOP:
            uav.emergency_stop()
            
    def _calculate_maneuver_cost(self, uav: UAV, maneuver: Dict) -> float:
        """
        Calculate the cost of a maneuver (fuel, time, mission impact).
        
        Args:
            uav: UAV performing the maneuver
            maneuver: Maneuver details
            
        Returns:
            Cost value (lower is better)
        """
        # Simple cost model based on deviation and time
        magnitude_cost = maneuver['magnitude'] / 100.0  # Distance cost
        time_cost = maneuver['duration'] / 60.0  # Time cost
        
        # Priority penalty (higher priority UAVs get lower cost for maneuvers)
        priority_factor = uav.priority / 5.0
        
        return (magnitude_cost + time_cost) * priority_factor
        
    def select_best_strategy(self, conflict: ConflictInfo) -> DeconflictionStrategy:
        """
        Select the best deconfliction strategy for a given conflict.
        
        Args:
            conflict: Conflict to resolve
            
        Returns:
            Recommended strategy
        """
        # Strategy selection logic based on conflict characteristics
        if conflict.severity == "CRITICAL":
            return DeconflictionStrategy.EMERGENCY_AVOIDANCE
        elif conflict.time_to_conflict < 10.0:
            return DeconflictionStrategy.GEOMETRIC_SEPARATION
        elif abs(conflict.uav1.priority - conflict.uav2.priority) > 1:
            return DeconflictionStrategy.PRIORITY_BASED
        elif abs(conflict.uav1.position[2] - conflict.uav2.position[2]) < 30.0:
            return DeconflictionStrategy.ALTITUDE_LAYERING
        elif conflict.uav1.get_current_target() is not None and conflict.uav2.get_current_target() is not None:
            return DeconflictionStrategy.COOPERATIVE_PATHFINDING
        else:
            return DeconflictionStrategy.VELOCITY_ADJUSTMENT
