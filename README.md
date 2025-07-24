# UAV Strategic Deconfliction System

A comprehensive UAV (Unmanned Aerial Vehicle) deconfliction system that provides strategic conflict resolution in shared airspace with advanced visualization and animation capabilities.

## Features

- **Strategic Deconfliction**: Real-time conflict detection and resolution for multiple UAVs
- **4D Simulation**: 3D spatial coordinates + time dimension for comprehensive analysis
- **Advanced Visualization**: 2D, 3D, and multi-view dashboard visualizations
- **Animation Export**: High-quality GIF and MP4 animation generation
- **Multiple UAV Types**: Support for quadcopters, fixed-wing, helicopters, and VTOL aircraft
- **Airspace Management**: No-fly zones, restricted areas, and controlled airspace
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

3. For MP4 export (optional):
```bash
# Install ffmpeg for MP4 animation export
# On Ubuntu/Debian:
sudo apt-get install ffmpeg

# On macOS:
brew install ffmpeg

# On Windows:
# Download from https://ffmpeg.org/download.html
```

## Quick Start

### Basic Demo with Animation Export
```bash
cd src
python main.py --duration 60 --view 2d
```

### Lightweight Demo (Memory Efficient)
```bash
cd src
python lightweight_demo.py
```

### High-Quality Animation Demo
```bash
cd src
python animation_demo.py
```

### Real-World Scenarios Demo
```bash
cd src
python real_world_demo.py
```

## Available Scripts

1. **main.py**: Main system with configurable parameters and animation export
2. **lightweight_demo.py**: Memory-efficient demo suitable for low-spec systems
3. **animation_demo.py**: Comprehensive animation generation with multiple scenarios
4. **real_world_demo.py**: Real-world use case demonstrations
5. **advanced_test_suite.py**: Advanced testing scenarios

## Command Line Options (main.py)

- `--duration`: Simulation duration in seconds (default: 120)
- `--view`: Visualization mode (`2d`, `3d`, `multi`)
- `--mode`: Run mode (`demo`, `quick`)
- `--output`: Output directory for animations (default: `animations`)

## System Status

✅ **Fully Operational**: All core components are working and tested
- ✅ Conflict detection and resolution
- ✅ Animation generation (GIF format)
- ✅ Multiple visualization modes (2D, 3D, multi-view)
- ✅ Real-world scenario demonstrations
- ✅ Memory-efficient operations for various hardware specs
- ✅ Comprehensive test coverage

## Output Files

The system generates several types of output:

### Animations
- **GIF files**: High-quality animated visualizations
- **Frame data**: JSON exports of simulation states

### Reports
- **Summary plots**: Comprehensive performance analysis charts
- **Simulation data**: Detailed JSON exports for further analysis
- **Performance metrics**: Conflict resolution statistics and mission completion rates

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

The system generates several types of animations:

### 2D Top-Down View
- Clear visualization of UAV positions and movements
- Conflict highlighting with red lines
- Airspace zones displayed as colored rectangles
- UAV trails showing historical paths

### 3D Spatial View
- Full 3D representation of airspace
- Altitude-based conflict analysis
- Realistic spatial relationships

### Multi-View Dashboard
- Combined 2D view with metrics panels
- Real-time performance indicators
- Conflict timeline visualization
- Altitude distribution charts

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
