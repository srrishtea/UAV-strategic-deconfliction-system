"""
Advanced UAV Visualization System with Animation Export
Provides comprehensive visualization capabilities for UAV deconfliction scenarios.
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Circle, Rectangle, Polygon
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import json
import os
import time
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict, deque

# Import UAV system components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uav.uav import UAV, UAVStatus, UAVType
from simulation.environment import SimulationEnvironment, AirspaceZone


class UAVVisualizer:
    """
    Advanced UAV visualization system with animation export capabilities.
    
    Features:
    - Real-time 2D/3D visualization
    - Conflict detection highlighting
    - UAV trail tracking
    - Airspace zone visualization
    - Performance metrics display
    - Animation export (GIF)
    - Summary plot generation
    """
    
    def __init__(self, simulation_env: SimulationEnvironment):
        """
        Initialize the UAV visualizer.
        
        Args:
            simulation_env: The simulation environment to visualize
        """
        self.sim_env = simulation_env
        self.bounds = simulation_env.bounds
        
        # Visualization settings
        self.figure_size = (12, 8)
        self.dpi = 100
        self.trail_length = 20  # Number of trail points to keep
        
        # Color schemes - only use UAVType values that actually exist
        self.uav_colors = {
            UAVType.QUADCOPTER: '#FF6B6B',      # Red
            UAVType.FIXED_WING: '#4ECDC4',      # Teal
            UAVType.HELICOPTER: '#45B7D1',      # Blue
            UAVType.VTOL: '#96CEB4'             # Green
        }
        
        self.status_colors = {
            UAVStatus.IDLE: '#95A5A6',          # Gray
            UAVStatus.ACTIVE: '#2ECC71',        # Green
            UAVStatus.MISSION: '#3498DB',       # Blue
            UAVStatus.EMERGENCY: '#E74C3C',     # Red
            UAVStatus.MAINTENANCE: '#F39C12'    # Orange
        }
        
        self.conflict_colors = {
            'LOW': '#F1C40F',                   # Yellow
            'MEDIUM': '#E67E22',                # Orange
            'HIGH': '#E74C3C',                  # Red
            'CRITICAL': '#8E44AD'               # Purple
        }
        
        # Data storage for animation
        self.frame_data = []
        self.uav_trails = defaultdict(lambda: deque(maxlen=self.trail_length))
        
        # Animation settings
        self.animation_fps = 8
        self.max_frames = 180  # Limit frames for reasonable file sizes
        
        # Figure and axes
        self.fig = None
        self.ax = None
        self.ax3d = None
        
        # Animation recording
        self.recording = False
        self.output_dir = 'animations'
        
        # Set matplotlib to non-interactive mode
        plt.ioff()
        
    def setup_animation_recording(self, view_mode: str = '2d', output_dir: str = 'animations'):
        """
        Setup the visualizer for animation recording.
        
        Args:
            view_mode: Visualization mode ('2d', '3d', 'multi')
            output_dir: Directory to save animations
        """
        self.view_mode = view_mode
        self.output_dir = output_dir
        self.recording = True
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize figure based on view mode
        if view_mode == '3d':
            self.fig = plt.figure(figsize=self.figure_size, dpi=self.dpi)
            self.ax3d = self.fig.add_subplot(111, projection='3d')
            self._setup_3d_plot()
        elif view_mode == 'multi':
            self.fig, axes = plt.subplots(2, 2, figsize=(16, 12), dpi=self.dpi)
            self.ax = axes[0, 0]
            self.ax_metrics = axes[0, 1]
            self.ax3d = self.fig.add_subplot(223, projection='3d')
            self.ax_status = axes[1, 1]
            self._setup_multi_plot()
        else:  # 2d mode
            self.fig, self.ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
            self._setup_2d_plot()
        
        # Set dark theme
        self.fig.patch.set_facecolor('#1a1a1a')
        
        print(f"✅ Animation recording setup complete: {view_mode} mode")
        
    def _setup_2d_plot(self):
        """Setup 2D plot styling."""
        self.ax.set_xlim(self.bounds[0], self.bounds[1])
        self.ax.set_ylim(self.bounds[2], self.bounds[3])
        self.ax.set_aspect('equal')
        self.ax.grid(True, alpha=0.3, color='white')
        self.ax.set_facecolor('#0a0a0a')
        self.ax.set_xlabel('X Position (m)', color='white', fontsize=11)
        self.ax.set_ylabel('Y Position (m)', color='white', fontsize=11)
        self.ax.tick_params(colors='white')
        
    def _setup_3d_plot(self):
        """Setup 3D plot styling."""
        self.ax3d.set_xlim(self.bounds[0], self.bounds[1])
        self.ax3d.set_ylim(self.bounds[2], self.bounds[3])
        self.ax3d.set_zlim(self.sim_env.altitude_limits[0], self.sim_env.altitude_limits[1])
        self.ax3d.set_xlabel('X Position (m)', color='white', fontsize=11)
        self.ax3d.set_ylabel('Y Position (m)', color='white', fontsize=11)
        self.ax3d.set_zlabel('Altitude (m)', color='white', fontsize=11)
        self.ax3d.xaxis.pane.fill = False
        self.ax3d.yaxis.pane.fill = False
        self.ax3d.zaxis.pane.fill = False
        
    def _setup_multi_plot(self):
        """Setup multi-view plot styling."""
        # Main 2D view
        self._setup_2d_plot()
        
        # Metrics view
        self.ax_metrics.set_facecolor('#0a0a0a')
        self.ax_metrics.set_title('Performance Metrics', color='white', fontsize=10)
        
        # 3D view
        self._setup_3d_plot()
        
        # Status view
        self.ax_status.set_facecolor('#0a0a0a')
        self.ax_status.set_title('UAV Status', color='white', fontsize=10)
        
    def capture_frame(self):
        """Capture current simulation state for animation."""
        if not self.recording:
            return
            
        # Limit total frames
        if len(self.frame_data) >= self.max_frames:
            return
            
        # Get current simulation state
        frame_data = {
            'timestamp': self.sim_env.current_time,
            'uavs': {},
            'conflicts': [],
            'airspace_zones': self.sim_env.airspace_zones.copy(),
            'metrics': self.sim_env.metrics.copy(),
            'weather': self.sim_env.weather.value
        }
        
        # Capture UAV states
        for uav_id, uav in self.sim_env.fleet_manager.uavs.items():
            uav_data = {
                'id': uav.id,
                'position': uav.position.copy(),
                'velocity': uav.velocity.copy(),
                'type': uav.type,
                'status': uav.status,
                'priority': uav.priority,
                'fuel_level': uav.fuel_level,
                'battery_level': uav.battery_level,
                'mission_complete': uav.mission_complete
            }
            frame_data['uavs'][uav_id] = uav_data
            
            # Update trails
            self.uav_trails[uav_id].append(uav.position.copy())
        
        # Capture conflicts
        for conflict in self.sim_env.fleet_manager.conflicts:
            conflict_data = {
                'uav1_id': conflict.uav1.id,
                'uav2_id': conflict.uav2.id,
                'severity': conflict.severity,
                'distance': conflict.min_distance,
                'time_to_conflict': conflict.time_to_conflict
            }
            frame_data['conflicts'].append(conflict_data)
        
        self.frame_data.append(frame_data)
        
    def render_frame(self, frame_data: Dict):
        """Render a single frame of the animation."""
        if self.view_mode == '2d':
            self._render_2d_frame(frame_data)
        elif self.view_mode == '3d':
            self._render_3d_frame(frame_data)
        elif self.view_mode == 'multi':
            self._render_multi_frame(frame_data)
            
    def _render_2d_frame(self, frame_data: Dict):
        """Render 2D visualization frame."""
        self.ax.clear()
        self._setup_2d_plot()
        
        # Draw airspace zones
        self._draw_airspace_zones_2d(frame_data['airspace_zones'])
        
        # Draw UAV trails
        self._draw_uav_trails_2d(frame_data['uavs'])
        
        # Draw UAVs
        self._draw_uavs_2d(frame_data['uavs'])
        
        # Draw conflicts
        self._draw_conflicts_2d(frame_data['conflicts'], frame_data['uavs'])
        
        # Add title and info
        title = f"UAV Deconfliction System - Time: {frame_data['timestamp']:.1f}s"
        self.ax.set_title(title, fontsize=14, color='white', pad=20)
        
        # Add legend
        self._add_legend_2d()
        
        # Add metrics text
        self._add_metrics_text_2d(frame_data['metrics'])
        
    def _render_3d_frame(self, frame_data: Dict):
        """Render 3D visualization frame."""
        self.ax3d.clear()
        self._setup_3d_plot()
        
        # Draw airspace zones in 3D
        self._draw_airspace_zones_3d(frame_data['airspace_zones'])
        
        # Draw UAV trails in 3D
        self._draw_uav_trails_3d(frame_data['uavs'])
        
        # Draw UAVs in 3D
        self._draw_uavs_3d(frame_data['uavs'])
        
        # Draw conflicts in 3D
        self._draw_conflicts_3d(frame_data['conflicts'], frame_data['uavs'])
        
        # Add title
        title = f"UAV Deconfliction 3D - Time: {frame_data['timestamp']:.1f}s"
        self.ax3d.set_title(title, fontsize=14, color='white')
        
    def _render_multi_frame(self, frame_data: Dict):
        """Render multi-view frame."""
        # Clear all axes
        self.ax.clear()
        self.ax_metrics.clear()
        self.ax3d.clear()
        self.ax_status.clear()
        
        # Setup plots
        self._setup_2d_plot()
        self._setup_3d_plot()
        
        # Render 2D view
        self._draw_airspace_zones_2d(frame_data['airspace_zones'])
        self._draw_uav_trails_2d(frame_data['uavs'])
        self._draw_uavs_2d(frame_data['uavs'])
        self._draw_conflicts_2d(frame_data['conflicts'], frame_data['uavs'])
        
        # Render 3D view
        self._draw_uavs_3d(frame_data['uavs'])
        self._draw_conflicts_3d(frame_data['conflicts'], frame_data['uavs'])
        
        # Render metrics
        self._render_metrics_panel(frame_data['metrics'])
        
        # Render status
        self._render_status_panel(frame_data['uavs'])
        
    def _draw_airspace_zones_2d(self, zones: Dict):
        """Draw airspace zones in 2D."""
        for zone_id, zone in zones.items():
            bounds = zone['bounds']
            zone_type = zone['type']
            
            # Create rectangle for zone
            width = bounds[1] - bounds[0]
            height = bounds[3] - bounds[2]
            
            if zone_type == AirspaceZone.NO_FLY:
                color = '#FF4444'
                alpha = 0.3
            elif zone_type == AirspaceZone.RESTRICTED:
                color = '#FF8800'
                alpha = 0.2
            elif zone_type == AirspaceZone.CONTROLLED:
                color = '#4488FF'
                alpha = 0.1
            else:
                color = '#888888'
                alpha = 0.1
                
            rect = Rectangle((bounds[0], bounds[2]), width, height,
                           facecolor=color, alpha=alpha, edgecolor=color, linewidth=2)
            self.ax.add_patch(rect)
            
            # Add zone label
            center_x = (bounds[0] + bounds[1]) / 2
            center_y = (bounds[2] + bounds[3]) / 2
            self.ax.text(center_x, center_y, zone_type.value.upper(),
                        ha='center', va='center', fontsize=8, color='white', weight='bold')
    
    def _draw_airspace_zones_3d(self, zones: Dict):
        """Draw airspace zones in 3D."""
        for zone_id, zone in zones.items():
            bounds = zone['bounds']
            alt_range = zone['altitude_range']
            zone_type = zone['type']
            
            if zone_type == AirspaceZone.NO_FLY:
                color = '#FF4444'
                alpha = 0.2
            elif zone_type == AirspaceZone.RESTRICTED:
                color = '#FF8800'
                alpha = 0.15
            else:
                continue  # Skip other zones in 3D for clarity
                
            # Create 3D box for zone
            x = [bounds[0], bounds[1], bounds[1], bounds[0], bounds[0]]
            y = [bounds[2], bounds[2], bounds[3], bounds[3], bounds[2]]
            
            # Draw bottom and top faces
            for z in [alt_range[0], alt_range[1]]:
                self.ax3d.plot(x, y, [z]*5, color=color, alpha=alpha*2, linewidth=2)
            
            # Draw vertical edges
            for xi, yi in [(bounds[0], bounds[2]), (bounds[1], bounds[2]), 
                          (bounds[1], bounds[3]), (bounds[0], bounds[3])]:
                self.ax3d.plot([xi, xi], [yi, yi], alt_range, color=color, alpha=alpha*2, linewidth=1)
    
    def _draw_uav_trails_2d(self, uavs: Dict):
        """Draw UAV movement trails in 2D."""
        for uav_id, uav_data in uavs.items():
            if uav_id in self.uav_trails and len(self.uav_trails[uav_id]) > 1:
                trail = list(self.uav_trails[uav_id])
                x_coords = [pos[0] for pos in trail]
                y_coords = [pos[1] for pos in trail]
                
                # Get UAV color
                color = self.uav_colors.get(uav_data['type'], '#FFFFFF')
                
                # Draw trail with fading effect
                for i in range(len(trail) - 1):
                    alpha = (i + 1) / len(trail) * 0.5  # Fading trail
                    self.ax.plot(x_coords[i:i+2], y_coords[i:i+2], 
                               color=color, alpha=alpha, linewidth=1)
    
    def _draw_uav_trails_3d(self, uavs: Dict):
        """Draw UAV movement trails in 3D."""
        for uav_id, uav_data in uavs.items():
            if uav_id in self.uav_trails and len(self.uav_trails[uav_id]) > 1:
                trail = list(self.uav_trails[uav_id])
                x_coords = [pos[0] for pos in trail]
                y_coords = [pos[1] for pos in trail]
                z_coords = [pos[2] for pos in trail]
                
                # Get UAV color
                color = self.uav_colors.get(uav_data['type'], '#FFFFFF')
                
                # Draw 3D trail
                self.ax3d.plot(x_coords, y_coords, z_coords, 
                             color=color, alpha=0.6, linewidth=2)
    
    def _draw_uavs_2d(self, uavs: Dict):
        """Draw UAVs in 2D."""
        for uav_id, uav_data in uavs.items():
            pos = uav_data['position']
            uav_type = uav_data['type']
            status = uav_data['status']
            
            # Get colors
            base_color = self.uav_colors.get(uav_type, '#FFFFFF')
            status_color = self.status_colors.get(status, '#FFFFFF')
            
            # Draw UAV as circle
            circle = Circle((pos[0], pos[1]), 30, facecolor=base_color, 
                          edgecolor=status_color, linewidth=3, alpha=0.8)
            self.ax.add_patch(circle)
            
            # Add UAV ID label
            self.ax.text(pos[0], pos[1], uav_id, ha='center', va='center',
                        fontsize=8, color='black', weight='bold')
            
            # Add velocity vector
            vel = uav_data['velocity']
            if np.linalg.norm(vel) > 1:  # Only show if moving
                scale = 5  # Scale factor for velocity vector
                self.ax.arrow(pos[0], pos[1], vel[0]*scale, vel[1]*scale,
                            head_width=20, head_length=30, fc=base_color, ec=base_color, alpha=0.7)
    
    def _draw_uavs_3d(self, uavs: Dict):
        """Draw UAVs in 3D."""
        for uav_id, uav_data in uavs.items():
            pos = uav_data['position']
            uav_type = uav_data['type']
            
            # Get color
            color = self.uav_colors.get(uav_type, '#FFFFFF')
            
            # Draw UAV as sphere
            self.ax3d.scatter(pos[0], pos[1], pos[2], c=color, s=200, alpha=0.8)
            
            # Add UAV ID label
            self.ax3d.text(pos[0], pos[1], pos[2] + 20, uav_id, 
                         fontsize=8, color='white')
    
    def _draw_conflicts_2d(self, conflicts: List, uavs: Dict):
        """Draw conflict indicators in 2D."""
        for conflict in conflicts:
            uav1_id = conflict['uav1_id']
            uav2_id = conflict['uav2_id']
            severity = conflict['severity']
            
            if uav1_id in uavs and uav2_id in uavs:
                pos1 = uavs[uav1_id]['position']
                pos2 = uavs[uav2_id]['position']
                
                # Get conflict color
                color = self.conflict_colors.get(severity, '#FFFFFF')
                
                # Draw conflict line
                self.ax.plot([pos1[0], pos2[0]], [pos1[1], pos2[1]], 
                           color=color, linewidth=4, alpha=0.8, linestyle='--')
                
                # Add conflict warning
                mid_x = (pos1[0] + pos2[0]) / 2
                mid_y = (pos1[1] + pos2[1]) / 2
                self.ax.text(mid_x, mid_y, f"⚠️ {severity}", ha='center', va='center',
                           fontsize=10, color=color, weight='bold',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor='black', alpha=0.7))
    
    def _draw_conflicts_3d(self, conflicts: List, uavs: Dict):
        """Draw conflict indicators in 3D."""
        for conflict in conflicts:
            uav1_id = conflict['uav1_id']
            uav2_id = conflict['uav2_id']
            severity = conflict['severity']
            
            if uav1_id in uavs and uav2_id in uavs:
                pos1 = uavs[uav1_id]['position']
                pos2 = uavs[uav2_id]['position']
                
                # Get conflict color
                color = self.conflict_colors.get(severity, '#FFFFFF')
                
                # Draw conflict line in 3D
                self.ax3d.plot([pos1[0], pos2[0]], [pos1[1], pos2[1]], [pos1[2], pos2[2]],
                             color=color, linewidth=4, alpha=0.8, linestyle='--')
    
    def _add_legend_2d(self):
        """Add legend to 2D plot."""
        legend_elements = []
        
        # UAV types
        for uav_type, color in self.uav_colors.items():
            legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                            markerfacecolor=color, markersize=10, 
                                            label=uav_type.value.replace('_', ' ').title()))
        
        self.ax.legend(handles=legend_elements, loc='upper right', 
                      bbox_to_anchor=(1.15, 1), fontsize=8, 
                      facecolor='black', edgecolor='white', labelcolor='white')
    
    def _add_metrics_text_2d(self, metrics: Dict):
        """Add metrics text to 2D plot."""
        metrics_text = f"""Conflicts: {metrics.get('total_conflicts', 0)}
Resolved: {metrics.get('resolved_conflicts', 0)}
Violations: {metrics.get('safety_violations', 0)}
Distance: {metrics.get('total_distance_flown', 0):.0f}m"""
        
        self.ax.text(0.02, 0.98, metrics_text, transform=self.ax.transAxes,
                    fontsize=10, color='white', verticalalignment='top',
                    bbox=dict(boxstyle="round,pad=0.5", facecolor='black', alpha=0.7))
    
    def _render_metrics_panel(self, metrics: Dict):
        """Render metrics panel for multi-view."""
        self.ax_metrics.clear()
        self.ax_metrics.set_facecolor('#0a0a0a')
        self.ax_metrics.set_title('Performance Metrics', color='white', fontsize=10)
        
        metrics_text = [
            f"Total Conflicts: {metrics.get('total_conflicts', 0)}",
            f"Resolved: {metrics.get('resolved_conflicts', 0)}",
            f"Failed: {metrics.get('failed_resolutions', 0)}",
            f"Safety Violations: {metrics.get('safety_violations', 0)}",
            f"Distance Flown: {metrics.get('total_distance_flown', 0):.0f}m",
            f"Mission Rate: {metrics.get('mission_completion_rate', 0):.1%}"
        ]
        
        for i, text in enumerate(metrics_text):
            self.ax_metrics.text(0.05, 0.9 - i * 0.15, text, transform=self.ax_metrics.transAxes,
                               fontsize=9, color='white', verticalalignment='top')
        
        self.ax_metrics.set_xlim(0, 1)
        self.ax_metrics.set_ylim(0, 1)
        self.ax_metrics.axis('off')
    
    def _render_status_panel(self, uavs: Dict):
        """Render UAV status panel for multi-view."""
        self.ax_status.clear()
        self.ax_status.set_facecolor('#0a0a0a')
        self.ax_status.set_title('UAV Status', color='white', fontsize=10)
        
        status_counts = {}
        for uav_data in uavs.values():
            status = uav_data['status'].value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        if status_counts:
            labels = list(status_counts.keys())
            sizes = list(status_counts.values())
            colors = [self.status_colors.get(UAVStatus(status), '#FFFFFF') for status in labels]
            
            self.ax_status.pie(sizes, labels=labels, colors=colors, autopct='%1.0f', 
                             startangle=90, textprops={'color': 'white', 'fontsize': 8})
        
    def save_animation(self, filename: str, fps: int = 8, duration: float = None):
        """
        Save captured frames as GIF animation.
        
        Args:
            filename: Output filename
            fps: Frames per second
            duration: Maximum duration in seconds (None for all frames)
        """
        if not self.frame_data:
            print("❌ No frames captured for animation")
            return None
            
        print(f"🎬 Creating animation with {len(self.frame_data)} frames...")
        
        # Limit frames if duration specified
        if duration:
            max_frames = int(duration * fps)
            frames_to_use = self.frame_data[:max_frames]
        else:
            frames_to_use = self.frame_data
        
        # Create animation function
        def animate(frame_idx):
            if frame_idx < len(frames_to_use):
                self.render_frame(frames_to_use[frame_idx])
            return []
        
        # Create animation
        anim = animation.FuncAnimation(
            self.fig, animate, frames=len(frames_to_use),
            interval=int(1000/fps), blit=False, repeat=True
        )
        
        # Save as GIF
        output_path = os.path.join(self.output_dir, filename)
        if not filename.endswith('.gif'):
            output_path += '.gif'
            
        try:
            print(f"💾 Saving GIF animation to: {output_path}")
            anim.save(output_path, writer='pillow', fps=fps, dpi=80)
            
            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            print(f"✅ Animation saved successfully!")
            print(f"📁 File size: {file_size:.1f} MB")
            return output_path
            
        except Exception as e:
            print(f"❌ Error saving animation: {e}")
            print("💡 Make sure you have pillow installed: pip install pillow")
            return None
        
    def create_summary_plot(self, results: Dict):
        """Create summary visualization of simulation results."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('UAV Deconfliction System - Simulation Summary', fontsize=16, color='white')
        fig.patch.set_facecolor('#1a1a1a')
        
        # Plot 1: Conflict Resolution
        conflicts_data = [
            results.get('resolved_conflicts', 0),
            results.get('failed_resolutions', 0)
        ]
        labels = ['Resolved', 'Failed']
        colors = ['#2ECC71', '#E74C3C']
        
        if sum(conflicts_data) > 0:
            ax1.pie(conflicts_data, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax1.set_title('Conflict Resolution Rate', color='white')
        ax1.set_facecolor('#0a0a0a')
        
        # Plot 2: UAV Status Distribution
        fleet_status = results.get('fleet_status', {})
        status_data = [
            fleet_status.get('active_uavs', 0),
            fleet_status.get('idle_uavs', 0),
            fleet_status.get('completed_missions', 0)
        ]
        status_labels = ['Active', 'Idle', 'Completed']
        status_colors = ['#3498DB', '#95A5A6', '#2ECC71']
        
        if sum(status_data) > 0:
            ax2.pie(status_data, labels=status_labels, colors=status_colors, autopct='%1.1f%%', startangle=90)
        ax2.set_title('UAV Status Distribution', color='white')
        ax2.set_facecolor('#0a0a0a')
        
        # Plot 3: Performance Metrics
        metrics_names = ['Total Conflicts', 'Safety Violations', 'Distance (km)']
        metrics_values = [
            results.get('total_conflicts', 0),
            results.get('safety_violations', 0),
            results.get('total_distance_flown', 0) / 1000
        ]
        
        bars = ax3.bar(metrics_names, metrics_values, color=['#E74C3C', '#F39C12', '#3498DB'])
        ax3.set_title('Performance Metrics', color='white')
        ax3.set_facecolor('#0a0a0a')
        ax3.tick_params(colors='white')
        
        # Add value labels on bars
        for bar, value in zip(bars, metrics_values):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'{value:.1f}', ha='center', va='bottom', color='white')
        
        # Plot 4: Timeline (if we have frame data)
        if self.frame_data:
            times = [frame['timestamp'] for frame in self.frame_data]
            conflict_counts = [len(frame['conflicts']) for frame in self.frame_data]
            
            ax4.plot(times, conflict_counts, color='#E74C3C', linewidth=2, label='Active Conflicts')
            ax4.fill_between(times, conflict_counts, alpha=0.3, color='#E74C3C')
            ax4.set_xlabel('Time (s)', color='white')
            ax4.set_ylabel('Active Conflicts', color='white')
            ax4.set_title('Conflicts Over Time', color='white')
            ax4.set_facecolor('#0a0a0a')
            ax4.tick_params(colors='white')
            ax4.grid(True, alpha=0.3)
        
        # Style all subplots
        for ax in [ax1, ax2, ax3, ax4]:
            ax.set_facecolor('#0a0a0a')
        
        plt.tight_layout()
        
        # Save summary plot
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        summary_filename = f"simulation_summary_{timestamp}.png"
        summary_path = os.path.join(self.output_dir, summary_filename)
        plt.savefig(summary_path, dpi=150, bbox_inches='tight', 
                   facecolor='#1a1a1a', edgecolor='none')
        
        print(f"📊 Summary plot saved: {summary_path}")
        plt.close(fig)
        
    def export_visualization_data(self, filename: str):
        """Export visualization data to JSON file."""
        export_data = {
            'frame_count': len(self.frame_data),
            'simulation_bounds': self.bounds,
            'animation_settings': {
                'fps': self.animation_fps,
                'trail_length': self.trail_length,
                'max_frames': self.max_frames
            },
            'color_schemes': {
                'uav_colors': {k.value: v for k, v in self.uav_colors.items()},
                'status_colors': {k.value: v for k, v in self.status_colors.items()},
                'conflict_colors': self.conflict_colors
            },
            'metadata': {
                'export_time': time.strftime("%Y-%m-%d %H:%M:%S"),
                'total_frames_captured': len(self.frame_data)
            }
        }
        
        output_path = os.path.join(self.output_dir, filename)
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
            
        print(f"📁 Visualization data exported: {output_path}")
        
    def __str__(self) -> str:
        """String representation of the visualizer."""
        return (f"UAVVisualizer: {len(self.frame_data)} frames captured, "
                f"Recording: {'Active' if self.recording else 'Inactive'}, "
                f"Mode: {getattr(self, 'view_mode', 'Not set')}")
