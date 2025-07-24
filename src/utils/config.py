"""
Configuration management for UAV deconfliction system.
Handles system settings, parameters, and configuration files.
"""

import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


@dataclass
class SimulationConfig:
    """Configuration for simulation parameters."""
    # Simulation area
    area_bounds: tuple = (-2000, 2000, -2000, 2000)  # (min_x, max_x, min_y, max_y)
    altitude_limits: tuple = (50, 500)  # (min_alt, max_alt)
    time_step: float = 1.0  # seconds
    
    # Safety parameters
    default_separation: float = 50.0  # meters
    emergency_separation: float = 30.0  # meters
    conflict_detection_horizon: float = 60.0  # seconds
    
    # Performance parameters
    max_uav_speed: float = 15.0  # m/s
    fuel_consumption_rate: float = 1.0  # %/minute
    battery_consumption_rate: float = 1.5  # %/minute


@dataclass
class DeconflictionConfig:
    """Configuration for deconfliction algorithms."""
    # Strategy selection
    enable_priority_based: bool = True
    enable_altitude_layering: bool = True
    enable_geometric_separation: bool = True
    enable_velocity_adjustment: bool = True
    enable_cooperative_pathfinding: bool = True
    
    # Algorithm parameters
    safety_margin_multiplier: float = 1.5
    max_altitude_change: float = 100.0  # meters
    max_speed_reduction: float = 0.5  # fraction
    loiter_radius: float = 30.0  # meters
    
    # Emergency parameters
    critical_time_threshold: float = 5.0  # seconds
    emergency_stop_distance: float = 20.0  # meters


@dataclass
class VisualizationConfig:
    """Configuration for visualization system."""
    # Display settings
    update_interval: int = 100  # milliseconds
    trail_length: int = 50  # number of points
    figure_size: tuple = (12, 10)  # (width, height)
    
    # Feature toggles
    show_paths: bool = True
    show_conflicts: bool = True
    show_zones: bool = True
    show_metrics: bool = True
    
    # Colors and styling
    uav_marker_size: int = 100
    conflict_line_width: int = 2
    trail_alpha: float = 0.5


class ConfigManager:
    """
    Manages configuration for the UAV deconfliction system.
    
    Handles loading, saving, and validation of configuration files.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file (YAML or JSON)
        """
        self.config_path = config_path
        self.simulation = SimulationConfig()
        self.deconfliction = DeconflictionConfig()
        self.visualization = VisualizationConfig()
        
        if config_path and Path(config_path).exists():
            self.load_config(config_path)
            
    def load_config(self, config_path: str):
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file
        """
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
        # Determine file format
        if config_file.suffix.lower() in ['.yaml', '.yml']:
            if not YAML_AVAILABLE:
                raise ImportError("PyYAML is required for YAML configuration files. Install with: pip install pyyaml")
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
        elif config_file.suffix.lower() == '.json':
            with open(config_file, 'r') as f:
                config_data = json.load(f)
        else:
            raise ValueError("Configuration file must be YAML or JSON format")
            
        # Update configuration objects
        if 'simulation' in config_data:
            self._update_config(self.simulation, config_data['simulation'])
        if 'deconfliction' in config_data:
            self._update_config(self.deconfliction, config_data['deconfliction'])
        if 'visualization' in config_data:
            self._update_config(self.visualization, config_data['visualization'])
            
    def save_config(self, config_path: str, format: str = 'yaml'):
        """
        Save current configuration to file.
        
        Args:
            config_path: Path to save configuration
            format: File format ('yaml' or 'json')
        """
        config_data = {
            'simulation': asdict(self.simulation),
            'deconfliction': asdict(self.deconfliction),
            'visualization': asdict(self.visualization)
        }
        
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() in ['yaml', 'yml']:
            if not YAML_AVAILABLE:
                raise ImportError("PyYAML is required for YAML output. Install with: pip install pyyaml")
            with open(config_file, 'w') as f:
                yaml.safe_dump(config_data, f, default_flow_style=False, indent=2)
        elif format.lower() == 'json':
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        else:
            raise ValueError("Format must be 'yaml' or 'json'")
            
    def _update_config(self, config_obj, new_values: Dict[str, Any]):
        """Update configuration object with new values."""
        for key, value in new_values.items():
            if hasattr(config_obj, key):
                setattr(config_obj, key, value)
            else:
                print(f"Warning: Unknown configuration parameter: {key}")
                
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration as dictionary."""
        return {
            'simulation': asdict(self.simulation),
            'deconfliction': asdict(self.deconfliction),
            'visualization': asdict(self.visualization)
        }
        
    def validate_config(self) -> List[str]:
        """
        Validate current configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate simulation config
        if self.simulation.time_step <= 0:
            errors.append("Simulation time_step must be positive")
        if self.simulation.default_separation <= 0:
            errors.append("Default separation must be positive")
        if self.simulation.max_uav_speed <= 0:
            errors.append("Max UAV speed must be positive")
            
        # Validate deconfliction config
        if self.deconfliction.safety_margin_multiplier < 1.0:
            errors.append("Safety margin multiplier must be >= 1.0")
        if self.deconfliction.max_speed_reduction < 0 or self.deconfliction.max_speed_reduction > 1:
            errors.append("Max speed reduction must be between 0 and 1")
            
        # Validate visualization config
        if self.visualization.update_interval <= 0:
            errors.append("Visualization update interval must be positive")
        if self.visualization.trail_length < 0:
            errors.append("Trail length must be non-negative")
            
        return errors
        
    def create_sample_config(self, output_path: str):
        """
        Create a sample configuration file with documentation.
        
        Args:
            output_path: Path to save sample configuration
        """
        sample_config = {
            'simulation': {
                # Simulation area boundaries in meters
                'area_bounds': [-2000, 2000, -2000, 2000],
                'altitude_limits': [50, 500],
                'time_step': 1.0,  # Simulation time step in seconds
                
                # Safety parameters
                'default_separation': 50.0,  # Minimum separation distance in meters
                'emergency_separation': 30.0,  # Emergency separation distance
                'conflict_detection_horizon': 60.0,  # How far ahead to look for conflicts
                
                # Performance parameters
                'max_uav_speed': 15.0,  # Maximum UAV speed in m/s
                'fuel_consumption_rate': 1.0,  # Fuel consumption rate in %/minute
                'battery_consumption_rate': 1.5  # Battery consumption rate in %/minute
            },
            'deconfliction': {
                # Enable/disable different resolution strategies
                'enable_priority_based': True,
                'enable_altitude_layering': True,
                'enable_geometric_separation': True,
                'enable_velocity_adjustment': True,
                'enable_cooperative_pathfinding': True,
                
                # Algorithm parameters
                'safety_margin_multiplier': 1.5,  # Safety margin multiplier
                'max_altitude_change': 100.0,  # Maximum altitude change in meters
                'max_speed_reduction': 0.5,  # Maximum speed reduction (0.0-1.0)
                'loiter_radius': 30.0,  # Loiter pattern radius in meters
                
                # Emergency parameters
                'critical_time_threshold': 5.0,  # Time threshold for critical conflicts
                'emergency_stop_distance': 20.0  # Distance for emergency stops
            },
            'visualization': {
                # Display settings
                'update_interval': 100,  # Update interval in milliseconds
                'trail_length': 50,  # Number of trail points to display
                'figure_size': [12, 10],  # Figure size (width, height)
                
                # Feature toggles
                'show_paths': True,  # Show UAV movement trails
                'show_conflicts': True,  # Show conflict indicators
                'show_zones': True,  # Show airspace zones
                'show_metrics': True,  # Show performance metrics
                
                # Visual styling
                'uav_marker_size': 100,  # Size of UAV markers
                'conflict_line_width': 2,  # Width of conflict lines
                'trail_alpha': 0.5  # Transparency of trails (0.0-1.0)
            }
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            if YAML_AVAILABLE:
                yaml.safe_dump(sample_config, f, default_flow_style=False, indent=2)
            else:
                json.dump(sample_config, f, indent=2)
            
        print(f"Sample configuration saved to: {output_path}")
        
    def __str__(self) -> str:
        """String representation of the configuration manager."""
        return f"ConfigManager: {self.config_path or 'Default configuration'}"
