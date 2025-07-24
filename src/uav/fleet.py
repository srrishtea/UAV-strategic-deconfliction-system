"""
Fleet Manager for UAV Deconfliction System.
Manages multiple UAVs and handles conflict detection and resolution.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Set
import time
from .uav import UAV, UAVStatus, UAVType


class ConflictInfo:
    """Information about a detected conflict between UAVs."""
    
    def __init__(self, uav1: UAV, uav2: UAV, time_to_conflict: float, min_distance: float):
        self.uav1 = uav1
        self.uav2 = uav2
        self.time_to_conflict = time_to_conflict
        self.min_distance = min_distance
        self.severity = self._calculate_severity()
        
    def _calculate_severity(self) -> str:
        """Calculate conflict severity based on time and distance."""
        if self.time_to_conflict < 5.0 or self.min_distance < 20.0:
            return "CRITICAL"
        elif self.time_to_conflict < 15.0 or self.min_distance < 40.0:
            return "HIGH"
        elif self.time_to_conflict < 30.0 or self.min_distance < 60.0:
            return "MEDIUM"
        else:
            return "LOW"


class FleetManager:
    """
    Manages a fleet of UAVs and handles deconfliction.
    
    This class is responsible for:
    - Managing multiple UAVs
    - Detecting conflicts between UAVs
    - Coordinating conflict resolution
    - Monitoring fleet status
    """
    
    def __init__(self, simulation_area: Tuple[float, float, float, float] = (-1000, 1000, -1000, 1000)):
        """
        Initialize the Fleet Manager.
        
        Args:
            simulation_area: (min_x, max_x, min_y, max_y) boundaries of the operation area
        """
        self.uavs: Dict[str, UAV] = {}
        self.conflicts: List[ConflictInfo] = []
        self.simulation_area = simulation_area
        self.current_time = 0.0
        self.total_conflicts_detected = 0
        self.total_conflicts_resolved = 0
        
        # Deconfliction parameters
        self.conflict_detection_horizon = 60.0  # seconds
        self.update_frequency = 1.0  # Hz
        self.emergency_separation = 30.0  # meters
        
    def add_uav(self, uav: UAV) -> bool:
        """
        Add a UAV to the fleet.
        
        Args:
            uav: UAV instance to add
            
        Returns:
            True if successfully added, False if ID already exists
        """
        if uav.id in self.uavs:
            print(f"Warning: UAV {uav.id} already exists in fleet")
            return False
            
        self.uavs[uav.id] = uav
        print(f"Added UAV {uav.id} to fleet")
        return True
        
    def remove_uav(self, uav_id: str) -> bool:
        """
        Remove a UAV from the fleet.
        
        Args:
            uav_id: ID of UAV to remove
            
        Returns:
            True if successfully removed, False if not found
        """
        if uav_id in self.uavs:
            del self.uavs[uav_id]
            print(f"Removed UAV {uav_id} from fleet")
            return True
        return False
        
    def get_uav(self, uav_id: str) -> Optional[UAV]:
        """Get a UAV by its ID."""
        return self.uavs.get(uav_id)
        
    def get_active_uavs(self) -> List[UAV]:
        """Get list of UAVs that are currently active (not idle or in maintenance)."""
        return [uav for uav in self.uavs.values() 
                if uav.status in [UAVStatus.ACTIVE, UAVStatus.MISSION]]
        
    def detect_conflicts(self) -> List[ConflictInfo]:
        """
        Detect potential conflicts between all UAVs in the fleet.
        
        Returns:
            List of detected conflicts
        """
        conflicts = []
        active_uavs = self.get_active_uavs()
        
        # Check each pair of active UAVs
        for i in range(len(active_uavs)):
            for j in range(i + 1, len(active_uavs)):
                uav1, uav2 = active_uavs[i], active_uavs[j]
                
                conflict_info = self._check_uav_pair_conflict(uav1, uav2)
                if conflict_info:
                    conflicts.append(conflict_info)
                    
        return conflicts
        
    def _check_uav_pair_conflict(self, uav1: UAV, uav2: UAV) -> Optional[ConflictInfo]:
        """
        Check if two UAVs will conflict.
        
        Args:
            uav1, uav2: UAVs to check
            
        Returns:
            ConflictInfo if conflict detected, None otherwise
        """
        min_distance = float('inf')
        time_to_conflict = float('inf')
        conflict_detected = False
        
        required_separation = max(uav1.min_separation, uav2.min_separation)
        
        # Check current and future positions
        for t in np.arange(0, self.conflict_detection_horizon, 1.0):
            pos1 = uav1.get_predicted_position(t)
            pos2 = uav2.get_predicted_position(t)
            distance = np.linalg.norm(pos1 - pos2)
            
            if distance < min_distance:
                min_distance = distance
                
            if distance < required_separation and not conflict_detected:
                time_to_conflict = t
                conflict_detected = True
                
        if conflict_detected:
            return ConflictInfo(uav1, uav2, time_to_conflict, min_distance)
        return None
        
    def resolve_conflicts(self, conflicts: List[ConflictInfo]):
        """
        Resolve detected conflicts using strategic deconfliction.
        
        Args:
            conflicts: List of conflicts to resolve
        """
        # Sort conflicts by severity (most critical first)
        conflicts.sort(key=lambda c: (c.severity == "CRITICAL", c.time_to_conflict))
        
        for conflict in conflicts:
            self._resolve_single_conflict(conflict)
            
    def _resolve_single_conflict(self, conflict: ConflictInfo):
        """
        Resolve a single conflict between two UAVs.
        
        Args:
            conflict: Conflict information
        """
        uav1, uav2 = conflict.uav1, conflict.uav2
        
        print(f"Resolving {conflict.severity} conflict between {uav1.id} and {uav2.id}")
        
        # Strategy 1: Priority-based resolution
        if uav1.priority < uav2.priority:  # Lower number = higher priority
            self._apply_avoidance_maneuver(uav2, uav1)
        elif uav2.priority < uav1.priority:
            self._apply_avoidance_maneuver(uav1, uav2)
        else:
            # Same priority - use altitude separation
            self._apply_altitude_separation(uav1, uav2)
            
        self.total_conflicts_resolved += 1
        
    def _apply_avoidance_maneuver(self, avoiding_uav: UAV, priority_uav: UAV):
        """
        Apply avoidance maneuver to the lower priority UAV.
        
        Args:
            avoiding_uav: UAV that needs to avoid
            priority_uav: UAV with higher priority
        """
        # Calculate avoidance vector (perpendicular to approach)
        relative_position = priority_uav.position - avoiding_uav.position
        
        if np.linalg.norm(relative_position) > 0:
            # Create perpendicular vector for lateral avoidance
            perpendicular = np.array([-relative_position[1], relative_position[0], 0])
            perpendicular = perpendicular / np.linalg.norm(perpendicular) if np.linalg.norm(perpendicular) > 0 else np.array([1, 0, 0])
            
            # Calculate avoidance position
            avoidance_distance = max(avoiding_uav.min_separation, priority_uav.min_separation) * 1.5
            avoidance_offset = perpendicular * avoidance_distance
            
            # Temporarily modify velocity for avoidance
            avoiding_uav.velocity = avoidance_offset / 10.0  # Gentle avoidance maneuver
            
    def _apply_altitude_separation(self, uav1: UAV, uav2: UAV):
        """
        Separate UAVs vertically when they have the same priority.
        
        Args:
            uav1, uav2: UAVs to separate
        """
        altitude_separation = 50.0  # meters
        
        # Move one UAV up, one down
        uav1.position[2] += altitude_separation / 2
        uav2.position[2] -= altitude_separation / 2
        
        print(f"Applied altitude separation: {uav1.id} to {uav1.position[2]:.1f}m, {uav2.id} to {uav2.position[2]:.1f}m")
        
    def update_fleet(self, dt: float):
        """
        Update all UAVs in the fleet and handle conflicts.
        
        Args:
            dt: Time step in seconds
        """
        self.current_time += dt
        
        # Update all UAV positions
        for uav in self.uavs.values():
            uav.update_position(dt)
            
        # Detect and resolve conflicts
        conflicts = self.detect_conflicts()
        if conflicts:
            self.total_conflicts_detected += len(conflicts)
            self.resolve_conflicts(conflicts)
            
        self.conflicts = conflicts
        
    def get_fleet_status(self) -> Dict:
        """
        Get comprehensive fleet status information.
        
        Returns:
            Dictionary with fleet statistics and status
        """
        active_uavs = self.get_active_uavs()
        
        status = {
            'total_uavs': len(self.uavs),
            'active_uavs': len(active_uavs),
            'current_conflicts': len(self.conflicts),
            'total_conflicts_detected': self.total_conflicts_detected,
            'total_conflicts_resolved': self.total_conflicts_resolved,
            'simulation_time': self.current_time,
            'uav_details': []
        }
        
        for uav in self.uavs.values():
            status['uav_details'].append(uav.get_info())
            
        return status
        
    def emergency_land_all(self):
        """Emergency land all UAVs in the fleet."""
        print("EMERGENCY: Landing all UAVs")
        for uav in self.uavs.values():
            uav.emergency_stop()
            
    def set_fleet_mission(self, mission_data: Dict[str, List[Tuple[float, float, float]]]):
        """
        Set missions for multiple UAVs.
        
        Args:
            mission_data: Dictionary mapping UAV IDs to their waypoint lists
        """
        for uav_id, waypoints in mission_data.items():
            if uav_id in self.uavs:
                self.uavs[uav_id].set_mission(waypoints)
                print(f"Mission set for UAV {uav_id}: {len(waypoints)} waypoints")
            else:
                print(f"Warning: UAV {uav_id} not found in fleet")
                
    def get_conflict_summary(self) -> str:
        """Get a human-readable summary of current conflicts."""
        if not self.conflicts:
            return "No conflicts detected"
            
        summary = f"Detected {len(self.conflicts)} conflicts:\n"
        for i, conflict in enumerate(self.conflicts, 1):
            summary += (f"{i}. {conflict.uav1.id} vs {conflict.uav2.id}: "
                       f"{conflict.severity} (in {conflict.time_to_conflict:.1f}s, "
                       f"min distance: {conflict.min_distance:.1f}m)\n")
        return summary
        
    def __str__(self) -> str:
        """String representation of the fleet."""
        return (f"Fleet Manager: {len(self.uavs)} UAVs, "
                f"{len(self.get_active_uavs())} active, "
                f"{len(self.conflicts)} conflicts")
