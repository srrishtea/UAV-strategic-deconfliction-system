"""
Main entry point for the UAV Deconfliction System.
This script demonstrates the complete system functionality with animation export.
"""

import sys
import os
import time
import argparse
import math
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
    
    # Create simulation environment with optimized settings
    sim_env = SimulationEnvironment(
        bounds=(-800, 800, -800, 800),  # Smaller area for faster processing
        altitude_limits=(50, 200),
        time_step=2.0  # Larger time step for faster simulation
    )
    
    # Add fewer airspace restrictions for faster processing
    sim_env.add_airspace_zone(
        "NO_FLY_ZONE", 
        AirspaceZone.NO_FLY,
        (-150, 150, -150, 150),
        (0, 300)
    )
    
    # Set weather conditions
    sim_env.set_weather(WeatherCondition.CLEAR, wind_speed=2.0, wind_direction=45.0)
    
    # Simplified UAV scenarios for faster processing
    uav_scenarios = [
        {
            'id': 'UAV-1',
            'type': UAVType.QUADCOPTER,
            'position': (-600, -600, 100),
            'mission': MissionType.MEDICAL_DELIVERY,
            'waypoints': [(600, 600, 100)]
        },
        {
            'id': 'UAV-2', 
            'type': UAVType.FIXED_WING,
            'position': (600, -600, 120),
            'mission': MissionType.CARGO_DELIVERY,
            'waypoints': [(-600, 600, 120)]
        },
        {
            'id': 'UAV-3',
            'type': UAVType.HELICOPTER,
            'position': (0, -700, 150),
            'mission': MissionType.EMERGENCY_RESPONSE,
            'waypoints': [(0, 700, 150)]
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


def run_simulation_with_animation(sim_env: SimulationEnvironment, duration: float = 60.0, 
                                view_mode: str = '2d', output_dir: str = 'animations'):
    """
    Run simulation and create animation export with optimized performance.
    
    Args:
        sim_env: Simulation environment
        duration: Simulation duration in seconds
        view_mode: Visualization mode ('2d', '3d', 'multi')
        output_dir: Directory to save animations
    """
    print(f"🎬 Starting optimized simulation (duration: {duration}s)...")
    
    # Setup visualizer for animation recording
    visualizer = UAVVisualizer(sim_env)
    visualizer.setup_animation_recording(view_mode=view_mode, output_dir=output_dir)
    
    # Optimize frame capture frequency
    frame_capture_interval = max(1, int(5 / sim_env.time_step))  # Capture every ~5 seconds
    
    # Run simulation with progress tracking
    start_time = time.time()
    step_count = 0
    last_progress_time = 0
    
    print("\n🚀 Simulation running...")
    print("=" * 50)
    
    while sim_env.current_time < duration:
        # Update simulation
        old_time = sim_env.current_time
        sim_env._simulation_step()
        step_count += 1
        
        # Capture frame less frequently to improve performance
        if step_count % frame_capture_interval == 0:
            visualizer.capture_frame()
        
        # Print progress every 5 seconds of real time
        current_real_time = time.time()
        if current_real_time - last_progress_time >= 5.0:
            status = sim_env.get_fleet_status()
            conflicts = sim_env.fleet_manager.conflicts
            progress = (sim_env.current_time / duration) * 100
            
            print(f"⏱️  Progress: {progress:.1f}% | "
                  f"Sim Time: {sim_env.current_time:.0f}s | "
                  f"Active UAVs: {status['active_uavs']} | "
                  f"Conflicts: {len(conflicts)} | "
                  f"Frames: {len(visualizer.frame_data)}")
            
            # Show current conflicts briefly
            if conflicts and len(conflicts) <= 3:  # Only show if not too many
                for conflict in conflicts[:2]:  # Show max 2 conflicts
                    print(f"   🔥 {conflict.uav1.id} ↔ {conflict.uav2.id} ({conflict.severity})")
            
            last_progress_time = current_real_time
        
        # Remove the sleep to speed up processing
        # time.sleep(0.05)  # Commented out for faster processing
    
    # Simulation complete
    elapsed_time = time.time() - start_time
    results = sim_env._calculate_final_metrics()
    
    print("=" * 50)
    print("🏁 Simulation Complete!")
    print(f"📈 Results Summary:")
    print(f"   • Simulation Duration: {duration}s")
    print(f"   • Real Time Elapsed: {elapsed_time:.1f}s")
    print(f"   • Speed Factor: {duration/elapsed_time:.1f}x")
    print(f"   • Total Conflicts: {results['total_conflicts']}")
    print(f"   • Conflicts Resolved: {results['resolved_conflicts']}")
    print(f"   • Resolution Rate: {results.get('conflict_resolution_rate', 0):.1%}")
    print(f"   • Animation Frames: {len(visualizer.frame_data)}")
    
    # Generate animations and summary quickly
    print(f"\n🎨 Generating visualizations...")
    
    # Save animation with optimized settings
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    animation_filename = f"uav_demo_{view_mode}_{timestamp}.gif"
    
    # Limit animation duration for faster processing
    max_anim_duration = min(30, duration)  # Max 30 seconds for GIF
    visualizer.save_animation(animation_filename, fps=6, duration=max_anim_duration)
    
    # Create summary plot
    visualizer.create_summary_plot(results)
    
    return results, visualizer


def create_quick_demo_scenarios():
    """Create quick demonstration scenarios for faster processing."""
    scenarios = []
    
    # Scenario 1: Simple head-on collision
    print("\n📋 Creating Quick Demo 1: Head-on Collision")
    sim_env1 = SimulationEnvironment(
        bounds=(-300, 300, -300, 300),
        time_step=2.0  # Faster time step
    )
    sim_env1.add_uav_to_simulation('UAV-A', UAVType.QUADCOPTER, (-250, 0, 100), 
                                  MissionType.MEDICAL_DELIVERY, [(250, 0, 100)])
    sim_env1.add_uav_to_simulation('UAV-B', UAVType.QUADCOPTER, (250, 0, 100), 
                                  MissionType.CARGO_DELIVERY, [(-250, 0, 100)])
    scenarios.append(('head_on', sim_env1))
    
    # Scenario 2: Crossing paths
    print("📋 Creating Quick Demo 2: Crossing Paths")
    sim_env2 = SimulationEnvironment(
        bounds=(-300, 300, -300, 300),
        time_step=2.0
    )
    sim_env2.add_uav_to_simulation('UAV-X', UAVType.HELICOPTER, (-250, -250, 120), 
                                  MissionType.EMERGENCY_RESPONSE, [(250, 250, 120)])
    sim_env2.add_uav_to_simulation('UAV-Y', UAVType.FIXED_WING, (-250, 250, 120), 
                                  MissionType.PATROL, [(250, -250, 120)])
    scenarios.append(('crossing', sim_env2))
    
    return scenarios


def run_quick_batch_demos():
    """Generate quick animations for demonstration scenarios."""
    print("🎬 Running quick batch animation generation...")
    
    scenarios = create_quick_demo_scenarios()
    
    for scenario_name, sim_env in scenarios:
        print(f"\n🎯 Processing scenario: {scenario_name}")
        
        # Run simulation with animation (shorter duration)
        results, visualizer = run_simulation_with_animation(
            sim_env, 
            duration=20.0,  # Much shorter duration
            view_mode='2d',
            output_dir=f'animations/{scenario_name}'
        )
        
        print(f"✅ Scenario '{scenario_name}' completed")
        print(f"   - Conflicts: {results['total_conflicts']}")
        print(f"   - Resolution rate: {results.get('conflict_resolution_rate', 0):.1%}")
    
    print("\n🎉 All quick demos completed!")


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description="UAV Deconfliction System - Optimized Animation Export")
    parser.add_argument('--mode', choices=['demo', 'quick', 'scenarios'], default='demo',
                       help='Run mode: demo (single), quick (fast batch), or scenarios (quick demos)')
    parser.add_argument('--duration', type=float, default=30.0,
                       help='Simulation duration in seconds (default: 30)')
    parser.add_argument('--view', choices=['2d', '3d', 'multi'], default='2d',
                       help='Visualization mode (default: 2d)')
    parser.add_argument('--output', type=str, default='animations',
                       help='Output directory for animations (default: animations)')
    
    args = parser.parse_args()
    
    # Header
    print("=" * 60)
    print("🚁 UAV STRATEGIC DECONFLICTION SYSTEM")
    print("   Optimized Animation Export - FlytBase 2025")
    print("=" * 60)
    
    try:
        if args.mode == 'scenarios':
            # Run quick demonstration scenarios
            run_quick_batch_demos()
            
        elif args.mode == 'quick':
            # Run single quick demo
            print("⚡ Running quick demo mode...")
            
            # Create simple scenario
            sim_env = SimulationEnvironment(
                bounds=(-400, 400, -400, 400),
                time_step=3.0  # Very fast time step
            )
            
            # Add just 2 UAVs for quick demo
            sim_env.add_uav_to_simulation('ALPHA', UAVType.QUADCOPTER, (-300, 0, 100),
                                        MissionType.MEDICAL_DELIVERY, [(300, 0, 100)])
            sim_env.add_uav_to_simulation('BETA', UAVType.QUADCOPTER, (300, 0, 100),
                                        MissionType.CARGO_DELIVERY, [(-300, 0, 100)])
            
            results, visualizer = run_simulation_with_animation(
                sim_env, 
                duration=15.0,  # Very short duration
                view_mode=args.view,
                output_dir=args.output
            )
            
        else:
            # Run standard demo with optimizations
            sim_env = create_sample_scenario()
            results, visualizer = run_simulation_with_animation(
                sim_env, 
                duration=args.duration,
                view_mode=args.view,
                output_dir=args.output
            )
        
        print("\n✅ Program completed successfully!")
        print(f"📁 Check the '{args.output}' directory for generated animations")
        print("💡 Tip: Use --mode quick for faster testing")
        
    except KeyboardInterrupt:
        print("\n⚠️  Program interrupted by user")
        print("💡 Try using --mode quick for faster processing")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
