"""
UAV (Unmanned Aerial Vehicle) class definition.
This represents an individual drone with its properties and capabilities.
"""

import numpy as np
from typing import List, Tuple, Optional
from enum import Enum


class UAVStatus(Enum):
    """Status of the UAV"""
    IDLE = "idle"
    ACTIVE = "active"
    MISSION = "mission"
    EMERGENCY = "emergency"
    MAINTENANCE = "maintenance"


class UAVType(Enum):
    """Types of UAVs with different characteristics"""
    QUADCOPTER = "quadcopter"
    FIXED_WING = "fixed_wing"
    HELICOPTER = "helicopter"
    VTOL = "vtol"  # Vertical Take-Off and Landing


class UAV:
    """
    Represents a single UAV with its properties, current state, and mission.
    
    This class handles:
    - Position and movement
    - Mission waypoints
    - Safety parameters
    - Communication with the fleet
    """
    
    def __init__(self, 
                 uav_id: str,
                 uav_type: UAVType,
                 initial_position: Tuple[float, float, float],
                 max_speed: float = 15.0,
                 min_separation: float = 50.0,
                 priority: int = 1):
        """
        Initialize a UAV instance.
        
        Args:
            uav_id: Unique identifier for this UAV
            uav_type: Type of UAV (affects flight characteristics)
            initial_position: Starting position (x, y, altitude) in meters
            max_speed: Maximum speed in m/s
            min_separation: Minimum safe distance from other UAVs in meters
            priority: Priority level (1=highest, 5=lowest)
        """
        self.id = uav_id
        self.type = uav_type
        self.position = np.array(initial_position, dtype=float)
        self.velocity = np.array([0.0, 0.0, 0.0])  # Current velocity (vx, vy, vz)
        self.heading = 0.0  # Direction in degrees (0-360)
        
        # Flight characteristics
        self.max_speed = max_speed
        self.min_separation = min_separation
        self.priority = priority
        
        # Mission parameters
        self.waypoints = []  # List of waypoints to visit
        self.current_waypoint_index = 0
        self.mission_complete = False
        
        # Status and safety
        self.status = UAVStatus.IDLE
        self.fuel_level = 100.0  # Percentage
        self.battery_level = 100.0  # Percentage (for electric UAVs)
        self.emergency_landing = False
        
        # Communication
        self.last_update_time = 0.0
        self.communication_range = 1000.0  # meters
        
    def set_mission(self, waypoints: List[Tuple[float, float, float]]):
        """
        Set mission waypoints for the UAV.
        
        Args:
            waypoints: List of (x, y, altitude) positions to visit
        """
        self.waypoints = [np.array(wp, dtype=float) for wp in waypoints]
        self.current_waypoint_index = 0
        self.mission_complete = False
        self.status = UAVStatus.MISSION
        
    def get_current_target(self) -> Optional[np.ndarray]:
        """Get the current waypoint the UAV is heading towards."""
        if self.current_waypoint_index < len(self.waypoints):
            return self.waypoints[self.current_waypoint_index]
        return None
        
    def update_position(self, dt: float):
        """
        Update UAV position based on current velocity and time step.
        
        Args:
            dt: Time step in seconds
        """
        if self.status == UAVStatus.MISSION and not self.emergency_landing:
            # Move towards current waypoint
            target = self.get_current_target()
            if target is not None:
                # Calculate direction to target
                direction = target - self.position
                distance_to_target = np.linalg.norm(direction)
                
                if distance_to_target > 1.0:  # If not at waypoint yet
                    # Normalize direction and apply speed
                    direction_normalized = direction / distance_to_target
                    speed = min(self.max_speed, distance_to_target / dt)
                    self.velocity = direction_normalized * speed
                else:
                    # Reached waypoint, move to next one
                    self.current_waypoint_index += 1
                    if self.current_waypoint_index >= len(self.waypoints):
                        self.mission_complete = True
                        self.status = UAVStatus.IDLE
                        self.velocity = np.array([0.0, 0.0, 0.0])
        
        # Update position
        self.position += self.velocity * dt
        
        # Update heading based on velocity
        if np.linalg.norm(self.velocity[:2]) > 0.1:  # If moving horizontally
            self.heading = np.degrees(np.arctan2(self.velocity[1], self.velocity[0]))
            
    def get_predicted_position(self, time_ahead: float) -> np.ndarray:
        """
        Predict where the UAV will be after a given time.
        
        Args:
            time_ahead: Time in seconds to predict ahead
            
        Returns:
            Predicted position as numpy array
        """
        return self.position + self.velocity * time_ahead
        
    def distance_to(self, other_uav: 'UAV') -> float:
        """
        Calculate distance to another UAV.
        
        Args:
            other_uav: Another UAV instance
            
        Returns:
            Distance in meters
        """
        return np.linalg.norm(self.position - other_uav.position)
        
    def is_conflict_with(self, other_uav: 'UAV', time_horizon: float = 30.0) -> bool:
        """
        Check if this UAV will conflict with another UAV in the near future.
        
        Args:
            other_uav: Another UAV to check against
            time_horizon: How far ahead to check (seconds)
            
        Returns:
            True if conflict is predicted
        """
        # Check current distance
        current_distance = self.distance_to(other_uav)
        required_separation = max(self.min_separation, other_uav.min_separation)
        
        if current_distance < required_separation:
            return True
            
        # Check predicted positions
        for t in np.arange(1.0, time_horizon, 1.0):
            my_future_pos = self.get_predicted_position(t)
            other_future_pos = other_uav.get_predicted_position(t)
            future_distance = np.linalg.norm(my_future_pos - other_future_pos)
            
            if future_distance < required_separation:
                return True
                
        return False
        
    def emergency_stop(self):
        """Emergency stop - halt all movement."""
        self.velocity = np.array([0.0, 0.0, 0.0])
        self.status = UAVStatus.EMERGENCY
        self.emergency_landing = True
        
    def get_info(self) -> dict:
        """
        Get current UAV information as a dictionary.
        
        Returns:
            Dictionary with UAV status and properties
        """
        return {
            'id': self.id,
            'type': self.type.value,
            'position': self.position.tolist(),
            'velocity': self.velocity.tolist(),
            'heading': self.heading,
            'status': self.status.value,
            'priority': self.priority,
            'fuel_level': self.fuel_level,
            'battery_level': self.battery_level,
            'mission_complete': self.mission_complete,
            'emergency_landing': self.emergency_landing,
            'current_waypoint': self.current_waypoint_index,
            'total_waypoints': len(self.waypoints)
        }
        
    def __str__(self) -> str:
        """String representation of the UAV."""
        return (f"UAV-{self.id} ({self.type.value}) at "
                f"({self.position[0]:.1f}, {self.position[1]:.1f}, {self.position[2]:.1f}) "
                f"- Status: {self.status.value}")
