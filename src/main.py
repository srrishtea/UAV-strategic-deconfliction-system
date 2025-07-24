"""
Main entry point for the UAV Deconfliction System.
This script demonstrates the complete system functionality.
"""

import sys
import os
import time
import argparse
from typing import List, Tuple

# Add the parent directory to path so imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our modules
try:
    from uav.uav import UAV, UAVType
    from uav.fleet import FleetManager
    from deconfliction.algorithm import DeconflictionAlgorithm, DeconflictionStrategy
    from deconfliction.priority_manager import PriorityManager, MissionType
    from simulation.environment import SimulationEnvironment, WeatherCondition, AirspaceZone
    from simulation.visualizer import UAVVisualizer
    from utils.config import ConfigManager
except ImportError as e:
    print(f"Import error: {e}")
    print("Please make sure you're running from the src directory")
    sys.exit(1)


def create_sample_scenario() -> SimulationEnvironment:
    """
    Create a sample scenario with multiple UAVs and potential conflicts.
    
    Returns:
        Configured simulation environment
    """
    print("🚁 Creating sample UAV deconfliction scenario...")
    
    # Create simulation environment
    sim_env = SimulationEnvironment(
        bounds=(-1000, 1000, -1000, 1000),
        altitude_limits=(50, 300),
        time_step=1.0
    )
    
    # Add some airspace restrictions
    sim_env.add_airspace_zone(
        "NO_FLY_ZONE_1", 
        AirspaceZone.NO_FLY,
        (-200, 200, -200, 200),
        (0, 500)
    )
    
    sim_env.add_airspace_zone(
        "CONTROLLED_ZONE",
        AirspaceZone.CONTROLLED, 
        (-500, 500, 300, 800),
        (100, 200)
    )
    
    # Set weather conditions
    sim_env.set_weather(WeatherCondition.LIGHT_WIND, wind_speed=5.0, wind_direction=45.0)
    
    # Add UAVs with missions that will create conflicts
    uav_scenarios = [
        {
            'id': 'MEDICAL-1',
            'type': UAVType.QUADCOPTER,
            'position': (-800, -800, 100),
            'mission': MissionType.MEDICAL_DELIVERY,
            'waypoints': [(0, 0, 100), (800, 800, 100)]
        },
        {
            'id': 'CARGO-1', 
            'type': UAVType.FIXED_WING,
            'position': (800, -800, 120),
            'mission': MissionType.CARGO_DELIVERY,
            'waypoints': [(0, 0, 120), (-800, 800, 120)]
        },
        {
            'id': 'PATROL-1',
            'type': UAVType.HELICOPTER,
            'position': (-400, 0, 150),
            'mission': MissionType.PATROL,
            'waypoints': [(400, 0, 150), (400, 400, 150), (-400, 400, 150), (-400, 0, 150)]
        },
        {
            'id': 'EMERGENCY-1',
            'type': UAVType.VTOL,
            'position': (0, -900, 80),
            'mission': MissionType.EMERGENCY_RESPONSE,
            'waypoints': [(0, 0, 80), (0, 900, 80)]
        },
        {
            'id': 'TRAINING-1',
            'type': UAVType.QUADCOPTER,
            'position': (-600, -600, 200),
            'mission': MissionType.TRAINING,
            'waypoints': [(600, 600, 200), (600, -600, 200), (-600, -600, 200)]
        }
    ]
    
    # Add all UAVs to simulation
    for scenario in uav_scenarios:
        success = sim_env.add_uav_to_simulation(
            scenario['id'],
            scenario['type'],
            scenario['position'],
            scenario['mission'],
            scenario['waypoints']
        )
        if success:
            print(f"  ✓ Added {scenario['id']} ({scenario['mission'].value})")
        else:
            print(f"  ✗ Failed to add {scenario['id']}")
    
    print(f"📊 Scenario created with {len(sim_env.fleet_manager.uavs)} UAVs")
    return sim_env


def run_simulation_demo(sim_env: SimulationEnvironment, duration: float = 120.0, 
                       show_visualization: bool = True):
    """
    Run a demonstration of the deconfliction system.
    
    Args:
        sim_env: Simulation environment
        duration: Simulation duration in seconds
        show_visualization: Whether to show real-time visualization
    """
    print(f"🎬 Starting simulation demo (duration: {duration}s)...")
    
    # Setup visualization if requested
    if show_visualization:
        try:
            visualizer = UAVVisualizer(sim_env)
            visualizer.setup_real_time_display('multi')
            print("📊 Visualization enabled")
        except Exception as e:
            print(f"⚠️  Visualization setup failed: {e}")
            print("   Continuing without visualization...")
            show_visualization = False
    
    # Run simulation
    start_time = time.time()
    step_count = 0
    
    print("\n🚀 Simulation running...")
    print("=" * 60)
    
    while sim_env.current_time < duration:
        # Update simulation
        old_time = sim_env.current_time
        sim_env._simulation_step()
        step_count += 1
        
        # Update visualization
        if show_visualization and step_count % 5 == 0:  # Update every 5 steps
            try:
                visualizer.update_display()
            except Exception as e:
                print(f"Visualization update failed: {e}")
        
        # Print status every 10 seconds
        if int(sim_env.current_time) % 10 == 0 and int(old_time) != int(sim_env.current_time):
            status = sim_env.get_fleet_status()
            conflicts = sim_env.fleet_manager.conflicts
            
            print(f"⏱️  Time: {sim_env.current_time:.0f}s | "
                  f"Active UAVs: {status['active_uavs']} | "
                  f"Conflicts: {len(conflicts)} | "
                  f"Resolved: {status['total_conflicts_resolved']}")
            
            if conflicts:
                for conflict in conflicts:
                    print(f"   🔥 CONFLICT: {conflict.uav1.id} ↔ {conflict.uav2.id} "
                          f"({conflict.severity}, {conflict.time_to_conflict:.1f}s)")
        
        # Small delay for real-time effect
        time.sleep(0.1)
    
    # Simulation complete
    elapsed_time = time.time() - start_time
    results = sim_env._calculate_final_metrics()
    
    print("=" * 60)
    print("🏁 Simulation Complete!")
    print(f"📈 Results Summary:")
    print(f"   • Simulation Duration: {duration}s")
    print(f"   • Real Time Elapsed: {elapsed_time:.1f}s")
    print(f"   • Total Conflicts Detected: {results['total_conflicts']}")
    print(f"   • Conflicts Resolved: {results['resolved_conflicts']}")
    print(f"   • Resolution Success Rate: {results.get('conflict_resolution_rate', 0):.1%}")
    print(f"   • Mission Completion Rate: {results['mission_completion_rate']:.1%}")
    print(f"   • Safety Violations: {results['safety_violations']}")
    print(f"   • Total Distance Flown: {results['total_distance_flown']:.0f}m")
    
    # Show final UAV states
    print(f"\n🚁 Final UAV States:")
    for uav in sim_env.fleet_manager.uavs.values():
        info = uav.get_info()
        print(f"   • {info['id']}: {info['status']} at "
              f"({info['position'][0]:.0f}, {info['position'][1]:.0f}, {info['position'][2]:.0f})")
    
    # Generate summary visualization
    if show_visualization:
        try:
            print("\n📊 Generating summary plots...")
            visualizer.create_summary_plot(results)
        except Exception as e:
            print(f"Summary plot generation failed: {e}")
    
    return results


def run_batch_analysis():
    """Run batch analysis of different scenarios."""
    print("🔬 Running batch analysis of different scenarios...")
    
    scenarios = [
        {"name": "Light Traffic", "uav_count": 3, "duration": 60},
        {"name": "Medium Traffic", "uav_count": 5, "duration": 90},
        {"name": "Heavy Traffic", "uav_count": 8, "duration": 120},
    ]
    
    results_summary = []
    
    for scenario in scenarios:
        print(f"\n📋 Testing scenario: {scenario['name']}")
        
        # Create scenario (simplified for batch testing)
        sim_env = SimulationEnvironment()
        
        # Add UAVs in a pattern that will create conflicts
        for i in range(scenario['uav_count']):
            angle = (2 * 3.14159 * i) / scenario['uav_count']
            start_pos = (800 * cos(angle), 800 * sin(angle), 100 + i * 20)
            end_pos = (-start_pos[0], -start_pos[1], start_pos[2])
            
            sim_env.add_uav_to_simulation(
                f"UAV-{i+1}",
                UAVType.QUADCOPTER,
                start_pos,
                MissionType.CARGO_DELIVERY,
                [end_pos]
            )
        
        # Run simulation
        results = sim_env.run_simulation(scenario['duration'], real_time=False)
        results['scenario_name'] = scenario['name']
        results_summary.append(results)
        
        print(f"   ✓ Completed: {results['conflict_resolution_rate']:.1%} resolution rate")
    
    # Print batch summary
    print("\n📊 Batch Analysis Summary:")
    print("-" * 80)
    for result in results_summary:
        print(f"{result['scenario_name']:15} | "
              f"Conflicts: {result['total_conflicts']:3} | "
              f"Resolved: {result['resolved_conflicts']:3} | "
              f"Success: {result.get('conflict_resolution_rate', 0):6.1%} | "
              f"Violations: {result['safety_violations']:2}")


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description="UAV Deconfliction System Demo")
    parser.add_argument('--mode', choices=['demo', 'batch', 'config'], default='demo',
                       help='Run mode: demo (interactive), batch (analysis), or config (generate config)')
    parser.add_argument('--duration', type=float, default=120.0,
                       help='Simulation duration in seconds (default: 120)')
    parser.add_argument('--no-viz', action='store_true',
                       help='Disable visualization')
    parser.add_argument('--config', type=str,
                       help='Path to configuration file')
    parser.add_argument('--export', type=str,
                       help='Export results to file')
    
    args = parser.parse_args()
    
    # Header
    print("=" * 60)
    print("🚁 UAV STRATEGIC DECONFLICTION SYSTEM")
    print("   FlytBase Robotics Assignment 2025")
    print("=" * 60)
    
    try:
        if args.mode == 'config':
            # Generate sample configuration
            config_manager = ConfigManager()
            output_path = args.config or 'config.json'
            config_manager.create_sample_config(output_path)
            print(f"✓ Sample configuration created: {output_path}")
            
        elif args.mode == 'batch':
            # Run batch analysis
            run_batch_analysis()
            
        else:
            # Run interactive demo
            sim_env = create_sample_scenario()
            results = run_simulation_demo(
                sim_env, 
                duration=args.duration,
                show_visualization=not args.no_viz
            )
            
            # Export results if requested
            if args.export:
                sim_env.export_results(args.export)
                print(f"📁 Results exported to: {args.export}")
        
        print("\n✅ Program completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Program interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


# Helper functions for batch analysis
def cos(x):
    """Cosine function (simplified for demo)."""
    import math
    return math.cos(x)

def sin(x):
    """Sine function (simplified for demo)."""
    import math
    return math.sin(x)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
