"""
Standalone animation demo for UAV deconfliction system.
This script focuses specifically on creating high-quality animations for demonstration.
"""

import sys
import os
import time
import numpy as np

# Add the parent directory to path so imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from uav.uav import UAV, UAVType
from uav.fleet import FleetManager
from deconfliction.priority_manager import PriorityManager, MissionType
from simulation.environment import SimulationEnvironment, WeatherCondition, AirspaceZone
from simulation.visualizer import UAVVisualizer


def create_showcase_scenario():
    """Create a visually impressive scenario for demonstration."""
    print("🎨 Creating showcase scenario for animation...")
    
    # Create larger environment for dramatic effect
    sim_env = SimulationEnvironment(
        bounds=(-800, 800, -800, 800),
        altitude_limits=(50, 250),
        time_step=0.8
    )
    
    # Add multiple airspace zones for visual interest
    sim_env.add_airspace_zone(
        "AIRPORT_NFZ", 
        AirspaceZone.NO_FLY,
        (-150, 150, -150, 150),
        (0, 250)
    )
    
    sim_env.add_airspace_zone(
        "RESTRICTED_MILITARY",
        AirspaceZone.RESTRICTED,
        (300, 600, 300, 600),
        (50, 200)
    )
    
    sim_env.add_airspace_zone(
        "CONTROLLED_AIRSPACE",
        AirspaceZone.CONTROLLED,
        (-600, -300, 400, 700),
        (100, 180)
    )
    
    # Set dynamic weather
    sim_env.set_weather(WeatherCondition.LIGHT_WIND, wind_speed=4.0, wind_direction=135.0)
    
    # Create complex UAV scenario with multiple conflict points
    uav_configs = [
        # Emergency response crossing the center
        {
            'id': 'RESCUE-01',
            'type': UAVType.HELICOPTER,
            'position': (-700, 0, 120),
            'mission': MissionType.EMERGENCY_RESPONSE,
            'waypoints': [(700, 0, 120), (700, 400, 120)]
        },
        
        # Medical delivery with priority
        {
            'id': 'MEDICAL-01',
            'type': UAVType.QUADCOPTER,
            'position': (0, -700, 80),
            'mission': MissionType.MEDICAL_DELIVERY,
            'waypoints': [(0, 700, 80), (-400, 700, 80)]
        },
        
        # Cargo delivery intersecting paths
        {
            'id': 'CARGO-01',
            'type': UAVType.FIXED_WING,
            'position': (600, 600, 160),
            'mission': MissionType.CARGO_DELIVERY,
            'waypoints': [(-600, -600, 160)]
        },
        
        # Patrol drone with circular path
        {
            'id': 'PATROL-01',
            'type': UAVType.QUADCOPTER,
            'position': (-400, -400, 100),
            'mission': MissionType.PATROL,
            'waypoints': [(400, -400, 100), (400, 400, 100), (-400, 400, 100), (-400, -400, 100)]
        },
        
        # Training mission
        {
            'id': 'TRAINING-01',
            'type': UAVType.VTOL,
            'position': (500, -500, 140),
            'mission': MissionType.TRAINING,
            'waypoints': [(-500, 500, 140), (0, 0, 140)]
        },
        
        # Additional cargo for complexity
        {
            'id': 'CARGO-02',
            'type': UAVType.FIXED_WING,
            'position': (-600, 600, 180),
            'mission': MissionType.CARGO_DELIVERY,
            'waypoints': [(600, -600, 180), (0, -600, 180)]
        },
        
        # Surveillance drone
        {
            'id': 'SURVEY-01',
            'type': UAVType.HELICOPTER,
            'position': (200, 200, 90),
            'mission': MissionType.PATROL,
            'waypoints': [(-200, 200, 90), (-200, -200, 90), (200, -200, 90), (200, 200, 90)]
        }
    ]
    
    # Add all UAVs to simulation
    for config in uav_configs:
        success = sim_env.add_uav_to_simulation(
            config['id'],
            config['type'],
            config['position'],
            config['mission'],
            config['waypoints']
        )
        if success:
            print(f"  ✓ Added {config['id']} ({config['mission'].value})")
    
    return sim_env


def create_conflict_focused_scenario():
    """Create a scenario specifically designed to show conflict resolution."""
    print("🎯 Creating conflict-focused scenario...")
    
    sim_env = SimulationEnvironment(
        bounds=(-400, 400, -400, 400),
        altitude_limits=(60, 180),
        time_step=0.5
    )
    
    # Add central no-fly zone to force conflicts
    sim_env.add_airspace_zone(
        "CENTRAL_NFZ", 
        AirspaceZone.NO_FLY,
        (-50, 50, -50, 50),
        (0, 200)
    )
    
    # Create UAVs that will definitely conflict
    conflict_configs = [
        # Two UAVs on collision course
        {
            'id': 'ALPHA',
            'type': UAVType.QUADCOPTER,
            'position': (-350, 0, 100),
            'mission': MissionType.EMERGENCY_RESPONSE,
            'waypoints': [(350, 0, 100)]
        },
        {
            'id': 'BETA',
            'type': UAVType.QUADCOPTER,
            'position': (350, 0, 100),
            'mission': MissionType.MEDICAL_DELIVERY,
            'waypoints': [(-350, 0, 100)]
        },
        
        # Crossing paths
        {
            'id': 'GAMMA',
            'type': UAVType.HELICOPTER,
            'position': (0, -350, 120),
            'mission': MissionType.CARGO_DELIVERY,
            'waypoints': [(0, 350, 120)]
        },
        {
            'id': 'DELTA',
            'type': UAVType.FIXED_WING,
            'position': (0, 350, 120),
            'mission': MissionType.PATROL,
            'waypoints': [(0, -350, 120)]
        },
        
        # Diagonal conflicts
        {
            'id': 'EPSILON',
            'type': UAVType.VTOL,
            'position': (-300, -300, 140),
            'mission': MissionType.TRAINING,
            'waypoints': [(300, 300, 140)]
        },
        {
            'id': 'ZETA',
            'type': UAVType.QUADCOPTER,
            'position': (300, -300, 140),
            'mission': MissionType.CARGO_DELIVERY,
            'waypoints': [(-300, 300, 140)]
        }
    ]
    
    for config in conflict_configs:
        sim_env.add_uav_to_simulation(
            config['id'],
            config['type'],
            config['position'],
            config['mission'],
            config['waypoints']
        )
    
    return sim_env


def run_animation_demo(scenario_name: str, sim_env: SimulationEnvironment, 
                      duration: float = 60.0, view_mode: str = '2d'):
    """Run a single animation demo."""
    print(f"\n🎬 Running animation demo: {scenario_name}")
    
    # Setup visualizer
    output_dir = f'animations/demos/{scenario_name}'
    visualizer = UAVVisualizer(sim_env)
    visualizer.setup_animation_recording(view_mode=view_mode, output_dir=output_dir)
    
    # Run simulation
    step_count = 0
    conflict_events = []
    
    while sim_env.current_time < duration:
        # Update simulation
        sim_env._simulation_step()
        step_count += 1
        
        # Capture frame
        visualizer.capture_frame()
        
        # Track conflict events
        current_conflicts = len(sim_env.fleet_manager.conflicts)
        if current_conflicts > 0:
            conflict_events.append({
                'time': sim_env.current_time,
                'count': current_conflicts
            })
        
        # Progress indicator
        if step_count % 50 == 0:
            progress = (sim_env.current_time / duration) * 100
            print(f"   Progress: {progress:.1f}% | Time: {sim_env.current_time:.1f}s | "
                  f"Conflicts: {current_conflicts} | Frames: {len(visualizer.frame_data)}")
    
    # Get final results
    results = sim_env._calculate_final_metrics()
    
    print(f"✅ Simulation complete for {scenario_name}")
    print(f"   - Duration: {duration}s")
    print(f"   - Frames captured: {len(visualizer.frame_data)}")
    print(f"   - Total conflicts: {results['total_conflicts']}")
    print(f"   - Conflicts resolved: {results['resolved_conflicts']}")
    
    # Generate animations
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # High quality GIF
    gif_filename = f"{scenario_name}_demo_{timestamp}.gif"
    visualizer.save_animation(gif_filename, fps=10)
    
    # Create summary
    visualizer.create_summary_plot(results)
    
    return results, visualizer


def main():
    """Main animation demo function."""
    print("=" * 60)
    print("🎬 UAV DECONFLICTION ANIMATION DEMO")
    print("   High-Quality Animation Generation")
    print("=" * 60)
    
    try:
        # Demo 1: Showcase scenario with multiple UAVs
        showcase_env = create_showcase_scenario()
        showcase_results, showcase_viz = run_animation_demo(
            "showcase", showcase_env, duration=90.0, view_mode='2d'
        )
        
        # Demo 2: Conflict-focused scenario
        conflict_env = create_conflict_focused_scenario()
        conflict_results, conflict_viz = run_animation_demo(
            "conflicts", conflict_env, duration=60.0, view_mode='2d'
        )
        
        # Demo 3: 3D visualization of showcase
        print("\n🌐 Creating 3D animation...")
        showcase_env_3d = create_showcase_scenario()
        showcase_3d_results, showcase_3d_viz = run_animation_demo(
            "showcase_3d", showcase_env_3d, duration=75.0, view_mode='3d'
        )
        
        # Demo 4: Multi-view dashboard
        print("\n📊 Creating multi-view dashboard animation...")
        dashboard_env = create_conflict_focused_scenario()
        dashboard_results, dashboard_viz = run_animation_demo(
            "dashboard", dashboard_env, duration=45.0, view_mode='multi'
        )
        
        # Summary
        print("\n🎉 All animation demos completed successfully!")
        print("\nGenerated Animations:")
        print("  ✅ Showcase scenario (2D) - Complex multi-UAV operations")
        print("  ✅ Conflict resolution (2D) - Focused conflict scenarios")
        print("  ✅ 3D visualization - Spatial conflict analysis")
        print("  ✅ Multi-view dashboard - Comprehensive monitoring")
        
        print(f"\n📁 All animations saved in 'animations/demos/' directory")
        print("📊 Summary plots and data exports included")
        
        # Performance summary
        total_conflicts = (showcase_results['total_conflicts'] + 
                          conflict_results['total_conflicts'] + 
                          showcase_3d_results['total_conflicts'] + 
                          dashboard_results['total_conflicts'])
        
        total_resolved = (showcase_results['resolved_conflicts'] + 
                         conflict_results['resolved_conflicts'] + 
                         showcase_3d_results['resolved_conflicts'] + 
                         dashboard_results['resolved_conflicts'])
        
        print(f"\n📈 Overall Performance:")
        print(f"   • Total conflicts across all demos: {total_conflicts}")
        print(f"   • Total conflicts resolved: {total_resolved}")
        print(f"   • Overall resolution rate: {(total_resolved/total_conflicts*100):.1f}%")
        
    except KeyboardInterrupt:
        print("\n⚠️  Animation demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Animation demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
