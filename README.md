# UAV Strategic Deconfliction System

A comprehensive UAV (Unmanned Aerial Vehicle) deconfliction system that provides strategic conflict resolution in shared airspace with advanced visualization and animation capabilities.

## Features

- **Strategic Deconfliction**: Real-time conflict detection and resolution for multiple UAVs
- **4D Simulation**: 3D spatial coordinates + time dimension for comprehensive analysis
- **Advanced Visualization**: 2D and 3D animation visualizations
- **Animation Export**: High-quality GIF animation generation
- **Multiple UAV Types**: Support for quadcopters, fixed-wing, helicopters, and VTOL aircraft
- **Airspace Management**: No-fly zones, restricted areas, and controlled airspace enforcement
- **Priority-based Resolution**: Mission-type based priority system for conflict resolution
- **Performance Metrics**: Comprehensive simulation analytics and reporting

## Installation

1. Clone the repository:
```bash
git clone https://github.com/srrishtea/UAV-strategic-deconfliction-system.git
cd UAV-strategic-deconfliction-system
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

### Generate Showcase Animations (Recommended)

**2D Showcase Animation** - Comprehensive multi-UAV scenario with conflict resolution:
```bash
cd src
python animation_demo.py
```
This generates:
- `animations/demos/showcase/showcase_demo_*.gif` - 2D visualization with multiple UAVs, conflicts, and airspace zones
- `animations/demos/showcase/simulation_summary_*.png` - Performance analysis charts

**3D Showcase Animation** - Same scenario in 3D perspective:
```bash
cd src
python animation_demo.py
```
This generates:
- `animations/demos/showcase_3d/showcase_3d_demo_*.gif` - 3D visualization showing altitude separation
- `animations/demos/showcase_3d/simulation_summary_*.png` - 3D performance metrics

### Other Demos

**Basic System Demo**:
```bash
cd src
python main.py --duration 60 --view 2d
```

**Real-World Scenarios Demo**:
```bash
cd src
python real_world_demo.py
```

## Available Scripts

1. **animation_demo.py**: 🎬 **Primary Demo** - Generates high-quality showcase animations in both 2D and 3D
2. **main.py**: Basic system with configurable parameters and animation export
3. **real_world_demo.py**: Real-world use case demonstrations (terminal output only)
4. **advanced_test_suite.py**: Advanced testing scenarios

## Command Line Options (main.py)

- `--duration`: Simulation duration in seconds (default: 120)
- `--view`: Visualization mode (`2d`, `3d`)
- `--mode`: Run mode (optional for different scenarios)

## System Status

✅ **Fully Operational**: All core components are working and tested
- ✅ Conflict detection and resolution
- ✅ Animation generation (GIF format)
- ✅ Multiple visualization modes (2D and 3D)
- ✅ Real-world scenario demonstrations
- ✅ Airspace enforcement and no-fly zone management
- ✅ Comprehensive test coverage

## Output Files

The system generates several types of output:

### Animations
- **GIF files**: High-quality animated visualizations showing UAV deconfliction in action
  - `animations/demos/showcase/showcase_demo_*.gif` - 2D comprehensive scenario
  - `animations/demos/showcase_3d/showcase_3d_demo_*.gif` - 3D perspective view
- **Frame data**: JSON exports of simulation states

### Reports
- **Summary plots**: Comprehensive performance analysis charts with conflict resolution metrics
- **Simulation data**: Detailed exports showing UAV trajectories, conflicts detected/resolved, and mission completion rates

## System Architecture

### Core Components

1. **UAV Management** (`src/uav/`)
   - Individual UAV behavior and state management
   - Fleet coordination and communication
   - Mission planning and execution

2. **Deconfliction Engine** (`src/deconfliction/`)
   - Conflict detection algorithms
   - Priority-based resolution strategies
   - Real-time path adjustment

3. **Simulation Environment** (`src/simulation/`)
   - 4D space-time simulation
   - Weather and environmental factors
   - Airspace zone management

4. **Visualization System** (`src/simulation/visualizer.py`)
   - Animation recording and export
   - Multi-view dashboard capabilities
   - 2D, 3D, and multi-panel visualizations

## Animation Examples

The system generates high-quality showcase animations that demonstrate:

### 2D Showcase Animation (`animations/demos/showcase/`)
- ✅ **Multi-UAV Operations**: 7 UAVs with different mission types and priorities
- ✅ **Conflict Resolution**: Real-time altitude separation and geometric avoidance
- ✅ **Airspace Management**: No-fly zones and restricted areas with enforcement
- ✅ **Mission Execution**: UAVs navigating to waypoints while avoiding conflicts
- ✅ **Visual Clarity**: Clear representation of UAV positions, trails, conflicts, and zones

### 3D Showcase Animation (`animations/demos/showcase_3d/`)
- ✅ **3D Spatial View**: Full 3D representation showing altitude-based conflict resolution
- ✅ **Realistic Perspective**: True spatial relationships between UAVs
- ✅ **Altitude Layering**: Visual demonstration of vertical separation strategies
- ✅ **Performance Metrics**: Real-time statistics and conflict resolution indicators

Both animations show the same complex scenario with:
- **Emergency Response UAV** (highest priority)
- **Medical Delivery UAVs** (high priority) 
- **Cargo Delivery UAVs** (medium priority)
- **Patrol UAVs** (medium priority)
- **Training UAVs** (lowest priority)

The animations demonstrate automatic conflict detection, priority-based resolution, and successful mission completion without collisions.

## Conflict Resolution Strategies

The system implements multiple deconfliction strategies:

1. **Altitude Separation**: Vertical spacing between UAVs
2. **Temporal Separation**: Time-based conflict avoidance
3. **Path Deviation**: Route modification around conflicts
4. **Speed Adjustment**: Velocity changes to avoid collisions
5. **Priority Override**: Emergency and medical missions take precedence

## Mission Types and Priorities

1. **Emergency Response** (Highest Priority)
2. **Medical Delivery** (High Priority)
3. **Cargo Delivery** (Medium Priority)
4. **Patrol Operations** (Medium Priority)
5. **Training Missions** (Lowest Priority)

## Performance Metrics

The system tracks comprehensive performance indicators:

- **Conflict Detection Rate**: Percentage of potential conflicts identified
- **Resolution Success Rate**: Conflicts successfully resolved without violations
- **Mission Completion Rate**: Percentage of missions completed successfully
- **Safety Violations**: Number of minimum separation breaches
- **Total Distance Flown**: Cumulative flight distance across all UAVs
- **Average Resolution Time**: Time taken to resolve conflicts

## Scalability Considerations

For real-world deployment with thousands of UAVs:

### Architectural Enhancements
- **Distributed Computing**: Microservices architecture for horizontal scaling
- **Real-time Data Pipelines**: Apache Kafka or similar for high-throughput data ingestion
- **Database Optimization**: Time-series databases for trajectory data
- **Load Balancing**: Geographic distribution of processing nodes

### Algorithm Optimizations
- **Spatial Indexing**: R-trees or similar for efficient spatial queries
- **Predictive Analytics**: Machine learning for conflict prediction
- **Hierarchical Resolution**: Multi-level conflict resolution strategies
- **Caching Mechanisms**: Pre-computed conflict matrices for common scenarios

## Testing and Validation

### Test Scenarios
- Head-on collision scenarios
- Multi-UAV convergence points
- Complex crossing patterns
- Emergency override situations
- Weather impact simulations

### Quality Assurance
- Automated test suites for all conflict scenarios
- Performance benchmarking under various loads
- Safety validation with minimum separation requirements
- Edge case handling verification

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with comprehensive tests
4. Submit a pull request with detailed description

## License

This project is developed for educational and research purposes as part of the FlytBase Robotics Assignment 2025.

## Support

For questions or issues:
1. Check the documentation in the `docs/` directory
2. Review existing issues in the repository
3. Create a new issue with detailed description and reproduction steps

---

**Note**: This system is designed for simulation and educational purposes. Real-world deployment would require additional safety certifications, regulatory compliance, and extensive testing.
