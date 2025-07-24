"""
Lightweight demo for UAV Deconfliction System.
Optimized for systems with limited resources (8GB RAM).
"""

import sys
import os
import time

# Add the parent directory to path so imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from uav.uav import UAV, UAVType, UAVStatus
from uav.fleet import FleetManager
from deconfliction.priority_manager import PriorityManager, MissionType


def simple_demo():
    """
    Simple demonstration without heavy visualization or complex simulation.
    """
    print("🚁 UAV Deconfliction System - Lightweight Demo")
    print("=" * 50)
    
    # Create fleet manager
    print("\n1. Creating Fleet Manager...")
    fleet = FleetManager((-500, 500, -500, 500))
    
    # Create priority manager
    priority_mgr = PriorityManager()
    
    # Create a few UAVs
    print("\n2. Adding UAVs to fleet...")
    
    # UAV 1 - Emergency mission (high priority)
    uav1 = UAV("RESCUE-1", UAVType.QUADCOPTER, (0, 0, 100))
    priority_mgr.assign_mission_priority(uav1, MissionType.EMERGENCY_RESPONSE)
    uav1.set_mission([(400, 400, 100), (400, -400, 100)])
    fleet.add_uav(uav1)
    print(f"   Added {uav1.id} - Priority: {uav1.priority} (Emergency)")
    
    # UAV 2 - Cargo delivery (medium priority)
    uav2 = UAV("CARGO-1", UAVType.FIXED_WING, (0, 0, 120))
    priority_mgr.assign_mission_priority(uav2, MissionType.CARGO_DELIVERY)
    uav2.set_mission([(-400, 400, 120), (-400, -400, 120)])
    fleet.add_uav(uav2)
    print(f"   Added {uav2.id} - Priority: {uav2.priority} (Cargo)")
    
    # UAV 3 - Training mission (low priority)
    uav3 = UAV("TRAIN-1", UAVType.QUADCOPTER, (100, 100, 80))
    priority_mgr.assign_mission_priority(uav3, MissionType.TRAINING)
    uav3.set_mission([(300, 300, 80), (-300, -300, 80)])
    fleet.add_uav(uav3)
    print(f"   Added {uav3.id} - Priority: {uav3.priority} (Training)")
    
    print(f"\n3. Fleet Status:")
    print(f"   Total UAVs: {len(fleet.uavs)}")
    print(f"   Active UAVs: {len(fleet.get_active_uavs())}")
    
    # Run simulation for a short time
    print("\n4. Running simulation...")
    print("   Time | UAV Positions | Conflicts")
    print("   " + "-" * 45)
    
    for step in range(20):  # Only 20 steps instead of hundreds
        # Update fleet
        fleet.update_fleet(1.0)
        
        # Print status every few steps
        if step % 4 == 0:
            conflicts = len(fleet.conflicts)
            positions = []
            for uav in fleet.uavs.values():
                x, y = uav.position[0], uav.position[1]
                positions.append(f"{uav.id}:({x:.0f},{y:.0f})")
            
            pos_str = " | ".join(positions[:2])  # Only show first 2 UAVs
            print(f"   {step:4d}s | {pos_str:25s} | {conflicts}")
            
        time.sleep(0.1)  # Small delay for readability
    
    # Final status
    print(f"\n5. Final Results:")
    status = fleet.get_fleet_status()
    print(f"   Total conflicts detected: {status['total_conflicts_detected']}")
    print(f"   Conflicts resolved: {status['total_conflicts_resolved']}")
    
    # Show individual UAV status
    print(f"\n6. Individual UAV Status:")
    for uav in fleet.uavs.values():
        info = uav.get_info()
        print(f"   {info['id']}: {info['status']} at ({info['position'][0]:.0f}, {info['position'][1]:.0f}, {info['position'][2]:.0f})")
        if info['mission_complete']:
            print(f"      ✅ Mission completed!")
        else:
            print(f"      🎯 Waypoint {info['current_waypoint']}/{info['total_waypoints']}")


def test_conflict_detection():
    """
    Test conflict detection with two UAVs on collision course.
    """
    print("\n" + "=" * 50)
    print("🚨 CONFLICT DETECTION TEST")
    print("=" * 50)
    
    # Create two UAVs on collision course
    uav_alpha = UAV("ALPHA", UAVType.QUADCOPTER, (-100, 0, 100))
    uav_beta = UAV("BETA", UAVType.QUADCOPTER, (100, 0, 100))
    
    # Set them on collision course
    uav_alpha.set_mission([(100, 0, 100)])  # Moving right
    uav_beta.set_mission([(-100, 0, 100)])   # Moving left
    
    print(f"ALPHA starts at: ({uav_alpha.position[0]:.0f}, {uav_alpha.position[1]:.0f})")
    print(f"BETA starts at:  ({uav_beta.position[0]:.0f}, {uav_beta.position[1]:.0f})")
    print(f"Both heading toward center - CONFLICT EXPECTED!")
    
    # Create fleet and add UAVs
    fleet = FleetManager()
    fleet.add_uav(uav_alpha)
    fleet.add_uav(uav_beta)
    
    print(f"\nSimulating collision course:")
    print("Time | ALPHA Pos | BETA Pos  | Distance | Conflict?")
    print("-" * 55)
    
    for step in range(15):
        # Update positions
        fleet.update_fleet(1.0)
        
        # Calculate distance between UAVs
        distance = uav_alpha.distance_to(uav_beta)
        conflict = "🚨 YES" if fleet.conflicts else "   No"
        
        print(f"{step:4d} | ({uav_alpha.position[0]:6.0f},{uav_alpha.position[1]:3.0f}) | ({uav_beta.position[0]:6.0f},{uav_beta.position[1]:3.0f}) | {distance:6.1f}m | {conflict}")
        
        # If conflict was resolved, show how
        if fleet.conflicts:
            for conflict_info in fleet.conflicts:
                print(f"     ⚠️  {conflict_info.severity} conflict detected!")
                print(f"     📍 Minimum distance will be: {conflict_info.min_distance:.1f}m")
                print(f"     ⏰ Time to conflict: {conflict_info.time_to_conflict:.1f}s")
        
        time.sleep(0.1)
    
    print(f"\nFinal distance: {uav_alpha.distance_to(uav_beta):.1f}m")
    print(f"Total conflicts handled: {fleet.total_conflicts_resolved}")


def memory_efficient_test():
    """
    Very lightweight test for low-memory systems.
    """
    print("\n" + "=" * 50)
    print("💾 MEMORY-EFFICIENT TEST")
    print("=" * 50)
    
    # Just test basic UAV creation and movement
    print("Creating single UAV...")
    uav = UAV("TEST-1", UAVType.QUADCOPTER, (0, 0, 100))
    uav.set_mission([(100, 100, 100), (200, 200, 100)])
    
    print(f"Initial position: {uav.position}")
    print(f"Mission waypoints: {len(uav.waypoints)}")
    
    print("\nSimulating 10 movement steps:")
    for i in range(10):
        uav.update_position(1.0)
        target = uav.get_current_target()
        target_str = f"({target[0]:.0f},{target[1]:.0f})" if target is not None else "None"
        print(f"Step {i+1}: Pos({uav.position[0]:.0f},{uav.position[1]:.0f}) -> Target{target_str}")
        
        if uav.mission_complete:
            print("✅ Mission completed!")
            break
    
    print(f"Final status: {uav.status.value}")


if __name__ == "__main__":
    try:
        print("UAV Deconfliction System - Lightweight Demo")
        print("Optimized for 8GB RAM systems")
        print()
        
        # Run simple demo
        simple_demo()
        
        # Test conflict detection
        test_conflict_detection()
        
        # Memory efficient test
        memory_efficient_test()
        
        print("\n" + "=" * 50)
        print("✅ Demo completed successfully!")
        print("💡 For full visualization, install more RAM or use cloud computing")
        
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
