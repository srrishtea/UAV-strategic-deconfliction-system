"""
Simulation environment for UAV deconfliction system.
Provides a realistic environment to test and visualize UAV operations.
"""

import numpy as np
import time
from typing import List, Dict, Tuple, Optional, Any
from enum import Enum
import json
import random

# Import from the same package level
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uav.uav import UAV, UAVStatus, UAVType
from uav.fleet import FleetManager, ConflictInfo
from deconfliction.algorithm import DeconflictionAlgorithm, DeconflictionStrategy
from deconfliction.priority_manager import PriorityManager, MissionType


class WeatherCondition(Enum):
    """Weather conditions affecting UAV operations."""
    CLEAR = "clear"
    LIGHT_WIND = "light_wind"
    MODERATE_WIND = "moderate_wind"
    HEAVY_WIND = "heavy_wind"
    RAIN = "rain"
    STORM = "storm"


class AirspaceZone(Enum):
    """Different airspace zones with varying restrictions."""
    UNRESTRICTED = "unrestricted"
    CONTROLLED = "controlled"
    RESTRICTED = "restricted"
    NO_FLY = "no_fly"
    EMERGENCY = "emergency"


class SimulationEnvironment:
    """
    Optimized simulation environment for UAV deconfliction testing.
    
    Features:
    - Fast physics simulation
    - Efficient conflict detection
    - Performance metrics collection
    - Real-time monitoring
    """
    
    def __init__(self, 
                 bounds: Tuple[float, float, float, float] = (-1000, 1000, -1000, 1000),
                 altitude_limits: Tuple[float, float] = (50, 300),
                 time_step: float = 1.0):
        """
        Initialize the simulation environment.
        
        Args:
            bounds: (min_x, max_x, min_y, max_y) in meters
            altitude_limits: (min_altitude, max_altitude) in meters
            time_step: Simulation time step in seconds
        """
        self.bounds = bounds
        self.altitude_limits = altitude_limits
        self.time_step = time_step
        
        # Core components
        self.fleet_manager = FleetManager(bounds)
        self.deconfliction_algorithm = DeconflictionAlgorithm()
        self.priority_manager = PriorityManager()
        
        # Environment state
        self.current_time = 0.0
        self.weather = WeatherCondition.CLEAR
        self.wind_vector = np.array([0.0, 0.0, 0.0])  # Wind velocity (m/s)
        self.airspace_zones = {}  # Zone definitions
        
        # Simulation metrics
        self.metrics = {
            'total_conflicts': 0,
            'resolved_conflicts': 0,
            'failed_resolutions': 0,
            'total_distance_flown': 0.0,
            'fuel_consumed': 0.0,
            'mission_completion_rate': 0.0,
            'average_resolution_time': 0.0,
            'safety_violations': 0
        }
        
        # Event logging (simplified for performance)
        self.event_log = []
        self.running = False
        
        # Performance optimizations
        self.max_log_entries = 100  # Limit log size
        
    def add_airspace_zone(self, zone_id: str, zone_type: AirspaceZone, 
                         bounds: Tuple[float, float, float, float],
                         altitude_range: Tuple[float, float]):
        """
        Add an airspace zone with restrictions.
        
        Args:
            zone_id: Unique identifier for the zone
            zone_type: Type of airspace zone
            bounds: (min_x, max_x, min_y, max_y)
            altitude_range: (min_alt, max_alt)
        """
        self.airspace_zones[zone_id] = {
            'type': zone_type,
            'bounds': bounds,
            'altitude_range': altitude_range,
            'violations': 0
        }
        
    def set_weather(self, weather: WeatherCondition, wind_speed: float = 0.0, 
                   wind_direction: float = 0.0):
        """
        Set weather conditions for the simulation.
        
        Args:
            weather: Weather condition
            wind_speed: Wind speed in m/s
            wind_direction: Wind direction in degrees (0 = North, 90 = East)
        """
        self.weather = weather
        
        # Convert wind to vector
        wind_rad = np.radians(wind_direction)
        self.wind_vector = np.array([
            wind_speed * np.sin(wind_rad),  # East component
            wind_speed * np.cos(wind_rad),  # North component
            0.0  # Vertical component
        ])
        
        self._log_event("weather_change", {
            'weather': weather.value,
            'wind_speed': wind_speed,
            'wind_direction': wind_direction
        })
        
    def add_uav_to_simulation(self, uav_id: str, uav_type: UAVType, 
                             position: Tuple[float, float, float],
                             mission_type: MissionType,
                             waypoints: List[Tuple[float, float, float]]) -> bool:
        """
        Add a UAV to the simulation with a mission.
        
        Args:
            uav_id: Unique UAV identifier
            uav_type: Type of UAV
            position: Starting position
            mission_type: Type of mission for priority assignment
            waypoints: Mission waypoints
            
        Returns:
            True if successfully added
        """
        # Create UAV
        uav = UAV(uav_id, uav_type, position)
        
        # Assign priority based on mission
        self.priority_manager.assign_mission_priority(uav, mission_type)
        
        # Set mission waypoints
        uav.set_mission(waypoints)
        
        # Add to fleet
        success = self.fleet_manager.add_uav(uav)
        
        if success:
            self._log_event("uav_added", {
                'uav_id': uav_id,
                'type': uav_type.value,
                'position': position,
                'mission_type': mission_type.value,
                'priority': uav.priority,
                'waypoints': len(waypoints)
            })
            
        return success
        
    def get_fleet_status(self) -> Dict:
        """
        Get current fleet status information.
        
        Returns:
            Dictionary containing fleet status metrics
        """
        active_uavs = len([uav for uav in self.fleet_manager.uavs.values() 
                          if uav.status in [UAVStatus.ACTIVE, UAVStatus.MISSION]])
        
        total_uavs = len(self.fleet_manager.uavs)
        
        completed_missions = len([uav for uav in self.fleet_manager.uavs.values() 
                                 if uav.mission_complete])
        
        return {
            'total_uavs': total_uavs,
            'active_uavs': active_uavs,
            'idle_uavs': total_uavs - active_uavs,
            'completed_missions': completed_missions,
            'current_conflicts': len(self.fleet_manager.conflicts),
            'total_conflicts_detected': self.fleet_manager.total_conflicts_detected,
            'total_conflicts_resolved': self.metrics['resolved_conflicts'],
            'safety_violations': self.metrics['safety_violations']
        }
        
    def run_simulation(self, duration: float, real_time: bool = False) -> Dict:
        """
        Run the simulation for a specified duration.
        
        Args:
            duration: Simulation duration in seconds
            real_time: If True, run in real-time (slow)
            
        Returns:
            Simulation results and metrics
        """
        self.running = True
        start_time = time.time()
        end_time = self.current_time + duration
        
        self._log_event("simulation_start", {
            'duration': duration,
            'uav_count': len(self.fleet_manager.uavs),
            'real_time': real_time
        })
        
        while self.running and self.current_time < end_time:
            # Update simulation step
            self._simulation_step()
            
            # Real-time delay if requested
            if real_time:
                time.sleep(self.time_step)
                
        # Calculate final metrics
        results = self._calculate_final_metrics()
        results['simulation_time'] = time.time() - start_time
        results['simulated_duration'] = duration
        
        self._log_event("simulation_end", results)
        self.running = False
        
        return results
        
    def _simulation_step(self):
        """Execute one optimized simulation time step."""
        # Check and enforce airspace restrictions BEFORE movement
        self._enforce_airspace_restrictions()
        
        # Apply environmental effects (simplified)
        self._apply_environmental_effects()
        
        # Update fleet (includes conflict detection and resolution)
        self.fleet_manager.update_fleet(self.time_step)
        
        # Handle conflicts with PROPER algorithms (not simplified)
        self._handle_conflicts_properly()
        
        # Update metrics
        self._update_metrics()
        
        # Advance time
        self.current_time += self.time_step
        
    def _apply_environmental_effects(self):
        """Apply simplified environmental effects to UAVs."""
        if self.weather == WeatherCondition.CLEAR:
            return  # No effects for clear weather
            
        for uav in self.fleet_manager.uavs.values():
            if uav.status in [UAVStatus.ACTIVE, UAVStatus.MISSION]:
                # Simplified wind effects
                if self.weather in [WeatherCondition.LIGHT_WIND, WeatherCondition.MODERATE_WIND]:
                    wind_effect = self.wind_vector * 0.05  # Reduced wind effect
                    uav.velocity += wind_effect
                elif self.weather in [WeatherCondition.HEAVY_WIND, WeatherCondition.STORM]:
                    uav.velocity *= 0.9  # 10% speed reduction
                        
    def _handle_conflicts_properly(self):
        """Handle conflicts using PROPER algorithms (not simplified)."""
        conflicts = self.fleet_manager.conflicts
        
        for conflict in conflicts:
            # Use the REAL deconfliction algorithms we wrote
            if conflict.severity == "CRITICAL":
                strategy = DeconflictionStrategy.EMERGENCY_AVOIDANCE
            elif conflict.time_to_conflict < 10.0:
                strategy = DeconflictionStrategy.ALTITUDE_LAYERING
            else:
                strategy = DeconflictionStrategy.GEOMETRIC_SEPARATION
                
            # Apply REAL conflict resolution
            resolution = self.deconfliction_algorithm.resolve_conflict(conflict, strategy)
            
            # Update metrics
            if resolution['success']:
                self.metrics['resolved_conflicts'] += 1
                print(f"Resolved {conflict.severity} conflict between {conflict.uav1.id} and {conflict.uav2.id}")
            else:
                self.metrics['failed_resolutions'] += 1
                print(f"FAILED to resolve conflict between {conflict.uav1.id} and {conflict.uav2.id}")
                
    def _enforce_airspace_restrictions(self):
        """PREVENT UAVs from entering restricted airspace."""
        for uav in self.fleet_manager.uavs.values():
            for zone_id, zone in self.airspace_zones.items():
                # Check if UAV will violate airspace in next step
                future_position = uav.position + uav.velocity * self.time_step
                
                if self._is_position_in_zone(future_position, zone):
                    if zone['type'] in [AirspaceZone.RESTRICTED, AirspaceZone.NO_FLY]:
                        # STOP the UAV from entering
                        print(f"⚠️ PREVENTING {uav.id} from entering {zone['type'].value} zone")
                        
                        # Calculate avoidance direction
                        zone_center = np.array([
                            (zone['bounds'][0] + zone['bounds'][1]) / 2,
                            (zone['bounds'][2] + zone['bounds'][3]) / 2,
                            (zone['altitude_range'][0] + zone['altitude_range'][1]) / 2
                        ])
                        
                        # Move UAV away from zone center
                        avoidance_direction = uav.position - zone_center
                        if np.linalg.norm(avoidance_direction) > 0:
                            avoidance_direction = avoidance_direction / np.linalg.norm(avoidance_direction)
                            # Strong avoidance velocity
                            uav.velocity = avoidance_direction * uav.max_speed * 0.8
                        
                        self.metrics['safety_violations'] += 1
                        
    def _is_position_in_zone(self, position: np.ndarray, zone: Dict) -> bool:
        """Check if position is inside a zone."""
        bounds = zone['bounds']
        alt_range = zone['altitude_range']
        
        return (bounds[0] <= position[0] <= bounds[1] and
                bounds[2] <= position[1] <= bounds[3] and
                alt_range[0] <= position[2] <= alt_range[1])
                
    def _check_airspace_violations(self):
        """Check for airspace violations (for logging only - prevention happens in _enforce_airspace_restrictions)."""
        for uav in self.fleet_manager.uavs.values():
            for zone_id, zone in self.airspace_zones.items():
                if self._is_position_in_zone(uav.position, zone):
                    if zone['type'] in [AirspaceZone.RESTRICTED, AirspaceZone.NO_FLY]:
                        zone['violations'] += 1
                        print(f"❌ VIOLATION: {uav.id} is in {zone['type'].value} zone!")
                        
    def _is_uav_in_zone(self, uav: UAV, zone: Dict) -> bool:
        """Check if UAV is in zone (kept for compatibility)."""
        return self._is_position_in_zone(uav.position, zone)
                
    def _update_metrics(self):
        """Update simulation metrics efficiently."""
        # Count total conflicts
        self.metrics['total_conflicts'] = self.fleet_manager.total_conflicts_detected
        
        # Calculate total distance flown (simplified)
        if int(self.current_time) % 10 == 0:  # Update every 10 seconds
            total_distance = 0.0
            for uav in self.fleet_manager.uavs.values():
                speed = np.linalg.norm(uav.velocity)
                total_distance += speed * self.time_step * 10  # Approximate for 10 seconds
            self.metrics['total_distance_flown'] += total_distance
        
        # Calculate mission completion rate
        completed_missions = sum(1 for uav in self.fleet_manager.uavs.values() 
                               if uav.mission_complete)
        total_missions = len([uav for uav in self.fleet_manager.uavs.values() 
                            if uav.waypoints])
        if total_missions > 0:
            self.metrics['mission_completion_rate'] = completed_missions / total_missions
            
    def _log_event(self, event_type: str, data: Dict):
        """Optimized event logging with size limits."""
        if len(self.event_log) >= self.max_log_entries:
            self.event_log.pop(0)  # Remove oldest entry
            
        self.event_log.append({
            'timestamp': self.current_time,
            'type': event_type,
            'data': data
        })
        
    def _calculate_final_metrics(self) -> Dict:
        """Calculate final simulation metrics."""
        results = self.metrics.copy()
        
        # Add fleet status
        results['fleet_status'] = self.get_fleet_status()
        
        # Add environmental summary
        results['environment'] = {
            'weather': self.weather.value,
            'wind_vector': self.wind_vector.tolist(),
            'airspace_zones': len(self.airspace_zones),
            'total_violations': sum(zone['violations'] for zone in self.airspace_zones.values())
        }
        
        # Calculate efficiency metrics
        if results['total_conflicts'] > 0:
            results['conflict_resolution_rate'] = (
                results['resolved_conflicts'] / results['total_conflicts']
            )
        else:
            results['conflict_resolution_rate'] = 1.0
            
        # Add UAV final states
        results['uav_final_states'] = []
        for uav in self.fleet_manager.uavs.values():
            results['uav_final_states'].append(uav.get_info())
            
        return results
        
    def get_simulation_state(self) -> Dict:
        """Get current simulation state for monitoring."""
        return {
            'time': self.current_time,
            'running': self.running,
            'uav_count': len(self.fleet_manager.uavs),
            'active_uavs': len([uav for uav in self.fleet_manager.uavs.values() 
                               if uav.status in [UAVStatus.ACTIVE, UAVStatus.MISSION]]),
            'current_conflicts': len(self.fleet_manager.conflicts),
            'weather': self.weather.value,
            'wind': self.wind_vector.tolist(),
            'metrics': self.metrics.copy()
        }
        
    def export_results(self, filename: str):
        """Export simulation results to JSON file."""
        results = {
            'simulation_config': {
                'bounds': self.bounds,
                'altitude_limits': self.altitude_limits,
                'time_step': self.time_step,
                'total_time': self.current_time
            },
            'final_metrics': self._calculate_final_metrics(),
            'event_log': self.event_log[-50:],  # Only last 50 events
            'uav_final_states': [uav.get_info() for uav in self.fleet_manager.uavs.values()]
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
            
    def stop_simulation(self):
        """Stop the simulation."""
        self.running = False
        
    def reset_simulation(self):
        """Reset simulation to initial state."""
        self.current_time = 0.0
        self.running = False
        self.weather = WeatherCondition.CLEAR
        self.wind_vector = np.array([0.0, 0.0, 0.0])
        
        # Reset metrics
        self.metrics = {
            'total_conflicts': 0,
            'resolved_conflicts': 0,
            'failed_resolutions': 0,
            'total_distance_flown': 0.0,
            'fuel_consumed': 0.0,
            'mission_completion_rate': 0.0,
            'average_resolution_time': 0.0,
            'safety_violations': 0
        }
        
        # Clear logs
        self.event_log.clear()
        
        # Reset fleet
        self.fleet_manager = FleetManager(self.bounds)
        
    def __str__(self) -> str:
        """String representation of the simulation."""
        return (f"UAV Simulation: {len(self.fleet_manager.uavs)} UAVs, "
                f"Time: {self.current_time:.1f}s, "
                f"Weather: {self.weather.value}")
