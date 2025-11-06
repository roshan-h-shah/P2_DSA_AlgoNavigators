# Pathfinding Application

A complete pathfinding application using OSMnx and Folium that visualizes shortest paths on a road network using Dijkstra's algorithm and A* algorithm.

## Features

- **Dijkstra's Algorithm**: Classic shortest path algorithm that explores all possible paths
- **A* Algorithm**: Heuristic-based algorithm that uses straight-line distance to guide search
- **Interactive Folium Maps**: Beautiful, interactive maps with path visualization
- **Path Comparison**: Compare both algorithms side-by-side
- **Statistics**: View detailed statistics about nodes explored, visited, and path distance

## Project Structure

```
P2/
map.osm                    # OpenStreetMap data file
pathfinding.py             # Core pathfinding algorithms
streamlit_app.py           # Streamlit UI - simple but working
README.md                  # This file
```

## Requirements

Install required packages using VENV is recommended:

```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install osmnx networkx folium streamlit streamlit-folium
```

## Usage

###  Streamlit Interactive App

```bash
streamlit run streamlit_app.py
```

Features:

Automatic path recalculation
Real-time performance metrics
Side-by-side algorithm comparison
Interactive controls and settings




## Algorithms Explained

### Dijkstra's Algorithm
**How it works**: Explores nodes in order of distance from start
**Guarantee**: Always finds the shortest path
**Performance**: Explores more nodes, especially in large graphs
**Use case**: When you need guaranteed shortest path

### A* Algorithm
**How it works**: Uses heuristic (straight-line distance) to guide search toward goal
**Guarantee**: Finds shortest path if heuristic is admissible**Performance**: Typically explores fewer nodes than Dijkstra
**Use case**: When you want faster computation with good path quality

## Output

The application generates an interactive HTML map with:
**Red line**: Dijkstra's path
**Blue line**: A* path
**Green marker**: Start point
**Red marker**: End point



##  Statistics

Each algorithm provides:
**Nodes explored**: Total nodes added to the priority queue
**Nodes visited**: Nodes actually processed (removed from queue)
**Path length**: Number of nodes in the final path
**Total distance**: Path distance in meters

### Please let us know if u encounter any issues!
