"""
Visualization system for UAV deconfliction simulation.
Provides real-time and post-analysis visualization capabilities.
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Circle, Rectangle
import numpy as np
from typing import List, Dict, Tuple, Optional
import json
from datetime import datetime

# Import from the same package level
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.environment import SimulationEnvironment, AirspaceZone
from uav.uav import UAV, UAVStatus, UAVType


class UAVVisualizer:
    """
    Advanced visualization system for UAV deconfliction simulation.
    
    Features:
    - Real-time 2D/3D visualization
    - Conflict highlighting
    - Path tracking
    - Performance metrics display
    - Export capabilities
    """
    
    def __init__(self, simulation_env: SimulationEnvironment):
        """
        Initialize the visualizer.
        
        Args:
            simulation_env: Simulation environment to visualize
        """
        self.sim_env = simulation_env
        self.fig = None
        self.axes = {}
        self.artists = {}
        self.animation = None
        
        # Visualization settings
        self.show_paths = True
        self.show_conflicts = True
        self.show_zones = True
        self.show_metrics = True
        self.trail_length = 50  # Number of position points to keep in trail
        
        # Color schemes
        self.uav_colors = {
            UAVType.QUADCOPTER: 'blue',
            UAVType.FIXED_WING: 'green',
            UAVType.HELICOPTER: 'red',
            UAVType.VTOL: 'purple'
        }
        
        self.status_colors = {
            UAVStatus.IDLE: 'gray',
            UAVStatus.ACTIVE: 'green',
            UAVStatus.MISSION: 'blue',
            UAVStatus.EMERGENCY: 'red',
            UAVStatus.MAINTENANCE: 'orange'
        }
        
        # Data storage for visualization
        self.uav_trails = {}  # Historical positions
        self.conflict_history = []
        self.metrics_history = []
        
    def setup_real_time_display(self, view_mode: str = '2d') -> None:
        """
        Setup real-time visualization display.
        
        Args:
            view_mode: '2d', '3d', or 'multi' for multiple views
        """
        if view_mode == '2d':
            self._setup_2d_display()
        elif view_mode == '3d':
            self._setup_3d_display()
        elif view_mode == 'multi':
            self._setup_multi_display()
        else:
            raise ValueError("view_mode must be '2d', '3d', or 'multi'")
            
    def _setup_2d_display(self):
        """Setup 2D top-down view."""
        self.fig, self.axes['main'] = plt.subplots(figsize=(12, 10))
        
        # Set up main plot area
        bounds = self.sim_env.bounds
        self.axes['main'].set_xlim(bounds[0], bounds[1])
        self.axes['main'].set_ylim(bounds[2], bounds[3])
        self.axes['main'].set_xlabel('X Position (m)')
        self.axes['main'].set_ylabel('Y Position (m)')
        self.axes['main'].set_title('UAV Deconfliction System - Real-time View')
        self.axes['main'].grid(True, alpha=0.3)
        self.axes['main'].set_aspect('equal')
        
        # Initialize empty artists for UAVs
        self.artists['uavs'] = {}
        self.artists['trails'] = {}
        self.artists['conflicts'] = []
        self.artists['zones'] = []
        
    def _setup_3d_display(self):
        """Setup 3D perspective view."""
        self.fig = plt.figure(figsize=(14, 10))
        self.axes['main'] = self.fig.add_subplot(111, projection='3d')
        
        # Set up 3D plot area
        bounds = self.sim_env.bounds
        alt_limits = self.sim_env.altitude_limits
        
        self.axes['main'].set_xlim(bounds[0], bounds[1])
        self.axes['main'].set_ylim(bounds[2], bounds[3])
        self.axes['main'].set_zlim(alt_limits[0], alt_limits[1])
        self.axes['main'].set_xlabel('X Position (m)')
        self.axes['main'].set_ylabel('Y Position (m)')
        self.axes['main'].set_zlabel('Altitude (m)')
        self.axes['main'].set_title('UAV Deconfliction System - 3D View')
        
        # Initialize empty artists
        self.artists['uavs'] = {}
        self.artists['trails'] = {}
        self.artists['conflicts'] = []
        
    def _setup_multi_display(self):
        """Setup multiple view dashboard."""
        self.fig = plt.figure(figsize=(16, 12))
        
        # Create subplots
        gs = self.fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # Main 2D view
        self.axes['main'] = self.fig.add_subplot(gs[0:2, 0:2])
        bounds = self.sim_env.bounds
        self.axes['main'].set_xlim(bounds[0], bounds[1])
        self.axes['main'].set_ylim(bounds[2], bounds[3])
        self.axes['main'].set_title('Top-Down View')
        self.axes['main'].grid(True, alpha=0.3)
        self.axes['main'].set_aspect('equal')
        
        # Altitude view
        self.axes['altitude'] = self.fig.add_subplot(gs[0, 2])
        self.axes['altitude'].set_title('Altitude Distribution')
        self.axes['altitude'].set_xlabel('UAV Count')
        self.axes['altitude'].set_ylabel('Altitude (m)')
        
        # Metrics view
        self.axes['metrics'] = self.fig.add_subplot(gs[1, 2])
        self.axes['metrics'].set_title('Performance Metrics')
        
        # Timeline view
        self.axes['timeline'] = self.fig.add_subplot(gs[2, :])
        self.axes['timeline'].set_title('Conflicts Over Time')
        self.axes['timeline'].set_xlabel('Time (s)')
        self.axes['timeline'].set_ylabel('Conflict Count')
        
        # Initialize artists
        self.artists['uavs'] = {}
        self.artists['trails'] = {}
        self.artists['conflicts'] = []
        
    def update_display(self):
        """Update the visualization with current simulation state."""
        # Clear previous artists
        self._clear_dynamic_artists()
        
        # Draw UAVs
        self._draw_uavs()
        
        # Draw trails if enabled
        if self.show_paths:
            self._draw_trails()
            
        # Draw conflicts if enabled
        if self.show_conflicts:
            self._draw_conflicts()
            
        # Draw airspace zones if enabled
        if self.show_zones:
            self._draw_airspace_zones()
            
        # Update metrics if available
        if 'metrics' in self.axes and self.show_metrics:
            self._update_metrics_display()
            
        # Update timeline if available
        if 'timeline' in self.axes:
            self._update_timeline()
            
        # Refresh the display
        plt.draw()
        plt.pause(0.01)
        
    def _clear_dynamic_artists(self):
        """Clear artists that change each frame."""
        for artist_list in [self.artists['conflicts']]:
            for artist in artist_list:
                if artist in self.axes['main'].collections:
                    artist.remove()
            artist_list.clear()
            
    def _draw_uavs(self):
        """Draw UAVs on the display."""
        ax = self.axes['main']
        
        for uav in self.sim_env.fleet_manager.uavs.values():
            # Get UAV position
            pos = uav.position
            
            # Choose color based on status and type
            base_color = self.uav_colors.get(uav.type, 'black')
            status_color = self.status_colors.get(uav.status, 'gray')
            
            # Create or update UAV marker
            if uav.id not in self.artists['uavs']:
                if len(ax.axes.name) == '3d':  # 3D plot
                    self.artists['uavs'][uav.id] = ax.scatter(
                        pos[0], pos[1], pos[2], 
                        c=base_color, s=100, alpha=0.8
                    )
                else:  # 2D plot
                    self.artists['uavs'][uav.id] = ax.scatter(
                        pos[0], pos[1], 
                        c=base_color, s=100, alpha=0.8,
                        edgecolors=status_color, linewidth=2
                    )
            else:
                # Update existing marker
                if len(ax.axes.name) == '3d':
                    self.artists['uavs'][uav.id]._offsets3d = ([pos[0]], [pos[1]], [pos[2]])
                else:
                    self.artists['uavs'][uav.id].set_offsets([[pos[0], pos[1]]])
                    
            # Add UAV label
            if len(ax.axes.name) == '3d':
                ax.text(pos[0], pos[1], pos[2] + 10, uav.id, fontsize=8)
            else:
                ax.annotate(uav.id, (pos[0], pos[1]), xytext=(5, 5), 
                           textcoords='offset points', fontsize=8)
                
            # Update trail data
            if uav.id not in self.uav_trails:
                self.uav_trails[uav.id] = []
            self.uav_trails[uav.id].append(pos.copy())
            
            # Limit trail length
            if len(self.uav_trails[uav.id]) > self.trail_length:
                self.uav_trails[uav.id].pop(0)
                
    def _draw_trails(self):
        """Draw UAV movement trails."""
        ax = self.axes['main']
        
        for uav_id, trail in self.uav_trails.items():
            if len(trail) > 1:
                trail_array = np.array(trail)
                
                if uav_id not in self.artists['trails']:
                    if len(ax.axes.name) == '3d':
                        self.artists['trails'][uav_id], = ax.plot(
                            trail_array[:, 0], trail_array[:, 1], trail_array[:, 2],
                            alpha=0.5, linewidth=1
                        )
                    else:
                        self.artists['trails'][uav_id], = ax.plot(
                            trail_array[:, 0], trail_array[:, 1],
                            alpha=0.5, linewidth=1
                        )
                else:
                    # Update existing trail
                    if len(ax.axes.name) == '3d':
                        self.artists['trails'][uav_id].set_data_3d(
                            trail_array[:, 0], trail_array[:, 1], trail_array[:, 2]
                        )
                    else:
                        self.artists['trails'][uav_id].set_data(
                            trail_array[:, 0], trail_array[:, 1]
                        )
                        
    def _draw_conflicts(self):
        """Draw current conflicts."""
        ax = self.axes['main']
        
        for conflict in self.sim_env.fleet_manager.conflicts:
            uav1_pos = conflict.uav1.position
            uav2_pos = conflict.uav2.position
            
            # Draw line between conflicting UAVs
            if len(ax.axes.name) == '3d':
                line = ax.plot([uav1_pos[0], uav2_pos[0]], 
                              [uav1_pos[1], uav2_pos[1]], 
                              [uav1_pos[2], uav2_pos[2]], 
                              'r--', alpha=0.7, linewidth=2)[0]
            else:
                line = ax.plot([uav1_pos[0], uav2_pos[0]], 
                              [uav1_pos[1], uav2_pos[1]], 
                              'r--', alpha=0.7, linewidth=2)[0]
            
            self.artists['conflicts'].append(line)
            
            # Add conflict severity label
            mid_point = (uav1_pos + uav2_pos) / 2
            if len(ax.axes.name) == '3d':
                ax.text(mid_point[0], mid_point[1], mid_point[2], 
                       conflict.severity, color='red', fontweight='bold')
            else:
                ax.text(mid_point[0], mid_point[1], conflict.severity, 
                       color='red', fontweight='bold')
                       
    def _draw_airspace_zones(self):
        """Draw airspace restriction zones."""
        ax = self.axes['main']
        
        for zone_id, zone in self.sim_env.airspace_zones.items():
            bounds = zone['bounds']
            zone_type = zone['type']
            
            # Choose color based on zone type
            if zone_type == AirspaceZone.NO_FLY:
                color = 'red'
                alpha = 0.3
            elif zone_type == AirspaceZone.RESTRICTED:
                color = 'orange'
                alpha = 0.2
            elif zone_type == AirspaceZone.CONTROLLED:
                color = 'yellow'
                alpha = 0.1
            else:
                color = 'gray'
                alpha = 0.05
                
            # Draw rectangle for zone
            if zone_id not in self.artists['zones']:
                rect = Rectangle(
                    (bounds[0], bounds[2]), 
                    bounds[1] - bounds[0], 
                    bounds[3] - bounds[2],
                    facecolor=color, alpha=alpha, edgecolor=color
                )
                ax.add_patch(rect)
                self.artists['zones'].append(rect)
                
                # Add zone label
                ax.text(bounds[0] + 10, bounds[3] - 10, zone_id, 
                       fontsize=8, color=color, fontweight='bold')
                       
    def _update_metrics_display(self):
        """Update metrics display panel."""
        ax = self.axes['metrics']
        ax.clear()
        
        # Get current metrics
        metrics = self.sim_env.metrics
        
        # Create metrics text
        metrics_text = [
            f"Total Conflicts: {metrics['total_conflicts']}",
            f"Resolved: {metrics['resolved_conflicts']}",
            f"Failed: {metrics['failed_resolutions']}",
            f"Distance: {metrics['total_distance_flown']:.1f}m",
            f"Violations: {metrics['safety_violations']}",
            f"Completion: {metrics['mission_completion_rate']:.1%}"
        ]
        
        for i, text in enumerate(metrics_text):
            ax.text(0.05, 0.9 - i * 0.15, text, transform=ax.transAxes,
                   fontsize=10, verticalalignment='top')
                   
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_title('Performance Metrics')
        ax.axis('off')
        
    def _update_timeline(self):
        """Update conflict timeline."""
        ax = self.axes['timeline']
        
        # Store current conflict count
        current_conflicts = len(self.sim_env.fleet_manager.conflicts)
        self.conflict_history.append({
            'time': self.sim_env.current_time,
            'conflicts': current_conflicts
        })
        
        # Limit history length
        if len(self.conflict_history) > 100:
            self.conflict_history.pop(0)
            
        # Plot timeline
        if len(self.conflict_history) > 1:
            times = [h['time'] for h in self.conflict_history]
            conflicts = [h['conflicts'] for h in self.conflict_history]
            
            ax.clear()
            ax.plot(times, conflicts, 'b-', linewidth=2)
            ax.fill_between(times, conflicts, alpha=0.3)
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Active Conflicts')
            ax.set_title('Conflicts Over Time')
            ax.grid(True, alpha=0.3)
            
    def create_summary_plot(self, results: Dict, save_path: Optional[str] = None):
        """
        Create a comprehensive summary plot of simulation results.
        
        Args:
            results: Simulation results dictionary
            save_path: Optional path to save the plot
        """
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('UAV Deconfliction Simulation Summary', fontsize=16)
        
        # Plot 1: Final UAV positions
        ax = axes[0, 0]
        for uav_info in results['uav_final_states']:
            pos = uav_info['position']
            status = uav_info['status']
            color = self.status_colors.get(UAVStatus(status), 'gray')
            ax.scatter(pos[0], pos[1], c=color, s=100, alpha=0.7)
            ax.annotate(uav_info['id'], (pos[0], pos[1]), xytext=(5, 5),
                       textcoords='offset points', fontsize=8)
        ax.set_title('Final UAV Positions')
        ax.set_xlabel('X Position (m)')
        ax.set_ylabel('Y Position (m)')
        ax.grid(True, alpha=0.3)
        
        # Plot 2: Conflict resolution statistics
        ax = axes[0, 1]
        categories = ['Total', 'Resolved', 'Failed']
        values = [
            results['total_conflicts'],
            results['resolved_conflicts'], 
            results['failed_resolutions']
        ]
        colors = ['blue', 'green', 'red']
        bars = ax.bar(categories, values, color=colors, alpha=0.7)
        ax.set_title('Conflict Resolution Statistics')
        ax.set_ylabel('Count')
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{value}', ha='center', va='bottom')
                   
        # Plot 3: Mission completion status
        ax = axes[0, 2]
        completed = sum(1 for uav in results['uav_final_states'] if uav['mission_complete'])
        total = len(results['uav_final_states'])
        incomplete = total - completed
        
        labels = ['Completed', 'Incomplete']
        sizes = [completed, incomplete]
        colors = ['green', 'orange']
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.set_title('Mission Completion Status')
        
        # Plot 4: Distance flown by UAV
        ax = axes[1, 0]
        uav_ids = [uav['id'] for uav in results['uav_final_states']]
        # Note: This would need distance tracking per UAV in the actual implementation
        ax.bar(uav_ids, [100] * len(uav_ids))  # Placeholder values
        ax.set_title('Distance Flown by UAV')
        ax.set_xlabel('UAV ID')
        ax.set_ylabel('Distance (m)')
        plt.setp(ax.get_xticklabels(), rotation=45)
        
        # Plot 5: Safety violations
        ax = axes[1, 1]
        violation_types = ['Airspace', 'Separation', 'Other']
        violation_counts = [results['safety_violations'], 0, 0]  # Placeholder
        ax.bar(violation_types, violation_counts, color='red', alpha=0.7)
        ax.set_title('Safety Violations')
        ax.set_ylabel('Count')
        
        # Plot 6: Performance metrics summary
        ax = axes[1, 2]
        metrics_text = [
            f"Total Simulation Time: {results.get('simulated_duration', 0):.1f}s",
            f"Conflict Resolution Rate: {results.get('conflict_resolution_rate', 0):.1%}",
            f"Mission Completion Rate: {results['mission_completion_rate']:.1%}",
            f"Total Distance: {results['total_distance_flown']:.1f}m",
            f"Safety Violations: {results['safety_violations']}",
            f"Weather: {results['environment']['weather']}"
        ]
        
        for i, text in enumerate(metrics_text):
            ax.text(0.05, 0.9 - i * 0.15, text, transform=ax.transAxes,
                   fontsize=10, verticalalignment='top')
                   
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_title('Performance Summary')
        ax.axis('off')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            
        plt.show()
        
    def start_real_time_animation(self, interval: int = 100):
        """
        Start real-time animation of the simulation.
        
        Args:
            interval: Update interval in milliseconds
        """
        def animate(frame):
            self.update_display()
            return []
            
        self.animation = animation.FuncAnimation(
            self.fig, animate, interval=interval, blit=False
        )
        
    def stop_animation(self):
        """Stop the real-time animation."""
        if self.animation:
            self.animation.event_source.stop()
            
    def save_animation(self, filename: str, duration: float, fps: int = 10):
        """
        Save simulation animation as video file.
        
        Args:
            filename: Output filename (should end with .mp4 or .gif)
            duration: Duration of animation in seconds
            fps: Frames per second
        """
        # This would require additional setup for video export
        # Implementation would depend on available codecs
        print(f"Animation export not implemented. Would save to {filename}")
        
    def export_visualization_data(self, filename: str):
        """
        Export visualization data for external analysis.
        
        Args:
            filename: Output JSON filename
        """
        viz_data = {
            'uav_trails': {k: [pos.tolist() for pos in trail] 
                          for k, trail in self.uav_trails.items()},
            'conflict_history': self.conflict_history,
            'metrics_history': self.metrics_history,
            'settings': {
                'show_paths': self.show_paths,
                'show_conflicts': self.show_conflicts,
                'show_zones': self.show_zones,
                'trail_length': self.trail_length
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(viz_data, f, indent=2)
            
    def __str__(self) -> str:
        """String representation of the visualizer."""
        return (f"UAV Visualizer: {len(self.uav_trails)} UAV trails tracked, "
                f"Animation: {'Active' if self.animation else 'Inactive'}")
