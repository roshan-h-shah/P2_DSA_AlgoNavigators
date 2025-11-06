"""
Pathfinding algorithms for road network graph.
Implements Dijkstra's algorithm and A* algorithm.
"""
import heapq
import math
import time
from typing import Dict, List, Tuple, Optional, Set


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth using the Haversine formula.
    Returns distance in meters.
    """
    # Earth's radius in meters
    R = 6371000
    
    # Convert latitude and longitude from degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance


def dijkstra(graph, source, target, weight='length') -> Tuple[List, float, Dict]:
    """
    Dijkstra's algorithm for finding shortest path.
    
    Args:
        graph: NetworkX graph
        source: Starting node ID
        target: Target node ID
        weight: Edge weight attribute (default: 'length')
    
    Returns:
        Tuple of (path, distance, stats) where:
        - path: List of node IDs from source to target
        - distance: Total path distance
        - stats: Dictionary with algorithm statistics
    """
    # Initialize distances: all nodes start at infinity
    distances = {node: float('inf') for node in graph.nodes()}
    distances[source] = 0
    
    # Previous nodes for path reconstruction
    previous = {node: None for node in graph.nodes()}
    
    # Priority queue: (distance, node)
    pq = [(0, source)]
    heapq.heapify(pq)
    
    # Track visited nodes
    visited = set()
    
    # Statistics
    nodes_explored = 0
    nodes_visited = 0
    
    # Start timing
    start_time = time.time()
    
    while pq:
        current_dist, current = heapq.heappop(pq)
        
        # Skip if we've already processed this node with a shorter path
        if current in visited:
            continue
        
        visited.add(current)
        nodes_visited += 1
        
        # If we reached the target, reconstruct path
        if current == target:
            path = []
            node = target
            while node is not None:
                path.append(node)
                node = previous[node]
            path.reverse()
            
            elapsed_time = time.time() - start_time
            stats = {
                'nodes_explored': nodes_explored,
                'nodes_visited': nodes_visited,
                'path_length': len(path),
                'total_distance': current_dist,
                'execution_time': elapsed_time
            }
            return path, current_dist, stats
        
        # Explore neighbors
        for neighbor in graph.neighbors(current):
            if neighbor in visited:
                continue
            
            # Get edge data (handle MultiDiGraph)
            edge_data = graph.get_edge_data(current, neighbor)
            if edge_data is None:
                continue
            
            # Get the minimum weight edge (in case of multiple edges)
            min_weight = float('inf')
            for key, data in edge_data.items():
                edge_weight = data.get(weight, float('inf'))
                if edge_weight < min_weight:
                    min_weight = edge_weight
            
            if min_weight == float('inf'):
                continue
            
            # Calculate new distance
            new_dist = current_dist + min_weight
            
            # Update if we found a shorter path
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                previous[neighbor] = current
                heapq.heappush(pq, (new_dist, neighbor))
                nodes_explored += 1
    
    # No path found
    elapsed_time = time.time() - start_time
    stats = {
        'nodes_explored': nodes_explored,
        'nodes_visited': nodes_visited,
        'path_length': 0,
        'total_distance': float('inf'),
        'execution_time': elapsed_time
    }
    return [], float('inf'), stats


def astar(graph, source, target, weight='length') -> Tuple[List, float, Dict]:
    """
    A* algorithm for finding shortest path using heuristic.
    
    Args:
        graph: NetworkX graph
        source: Starting node ID
        target: Target node ID
        weight: Edge weight attribute (default: 'length')
    
    Returns:
        Tuple of (path, distance, stats) where:
        - path: List of node IDs from source to target
        - distance: Total path distance
        - stats: Dictionary with algorithm statistics
    """
    # Get node coordinates for heuristic
    source_data = graph.nodes[source]
    target_data = graph.nodes[target]
    
    source_lat, source_lon = source_data.get('y'), source_data.get('x')
    target_lat, target_lon = target_data.get('y'), target_data.get('x')
    
    # Heuristic function (straight-line distance to target)
    def heuristic(node):
        node_data = graph.nodes[node]
        node_lat, node_lon = node_data.get('y'), node_data.get('x')
        if node_lat is None or node_lon is None:
            return float('inf')
        return haversine_distance(node_lat, node_lon, target_lat, target_lon)
    
    # Initialize distances: all nodes start at infinity
    g_score = {node: float('inf') for node in graph.nodes()}
    g_score[source] = 0
    
    # f_score = g_score + heuristic
    f_score = {node: float('inf') for node in graph.nodes()}
    f_score[source] = heuristic(source)
    
    # Previous nodes for path reconstruction
    previous = {node: None for node in graph.nodes()}
    
    # Priority queue: (f_score, node)
    pq = [(f_score[source], source)]
    heapq.heapify(pq)
    
    # Track visited nodes
    visited = set()
    
    # Statistics
    nodes_explored = 0
    nodes_visited = 0
    
    # Start timing
    start_time = time.time()
    
    while pq:
        current_f, current = heapq.heappop(pq)
        
        # Skip if we've already processed this node with a better f_score
        if current in visited:
            continue
        
        visited.add(current)
        nodes_visited += 1
        
        # If we reached the target, reconstruct path
        if current == target:
            path = []
            node = target
            while node is not None:
                path.append(node)
                node = previous[node]
            path.reverse()
            
            elapsed_time = time.time() - start_time
            stats = {
                'nodes_explored': nodes_explored,
                'nodes_visited': nodes_visited,
                'path_length': len(path),
                'total_distance': g_score[target],
                'execution_time': elapsed_time
            }
            return path, g_score[target], stats
        
        # Explore neighbors
        for neighbor in graph.neighbors(current):
            if neighbor in visited:
                continue
            
            # Get edge data (handle MultiDiGraph)
            edge_data = graph.get_edge_data(current, neighbor)
            if edge_data is None:
                continue
            
            # Get the minimum weight edge (in case of multiple edges)
            min_weight = float('inf')
            for key, data in edge_data.items():
                edge_weight = data.get(weight, float('inf'))
                if edge_weight < min_weight:
                    min_weight = edge_weight
            
            if min_weight == float('inf'):
                continue
            
            # Calculate tentative g_score
            tentative_g_score = g_score[current] + min_weight
            
            # Update if we found a shorter path
            if tentative_g_score < g_score[neighbor]:
                previous[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor)
                heapq.heappush(pq, (f_score[neighbor], neighbor))
                nodes_explored += 1
    
    # No path found
    elapsed_time = time.time() - start_time
    stats = {
        'nodes_explored': nodes_explored,
        'nodes_visited': nodes_visited,
        'path_length': 0,
        'total_distance': float('inf'),
        'execution_time': elapsed_time
    }
    return [], float('inf'), stats


def find_nearest_node(graph, lat: float, lon: float) -> Optional[int]:
    """
    Find the nearest node in the graph to given coordinates.
    
    Args:
        graph: NetworkX graph
        lat: Latitude
        lon: Longitude
    
    Returns:
        Node ID of nearest node, or None if graph is empty
    """
    if len(graph.nodes()) == 0:
        return None
    
    min_distance = float('inf')
    nearest_node = None
    
    for node in graph.nodes():
        node_data = graph.nodes[node]
        node_lat = node_data.get('y')
        node_lon = node_data.get('x')
        
        if node_lat is None or node_lon is None:
            continue
        
        distance = haversine_distance(lat, lon, node_lat, node_lon)
        if distance < min_distance:
            min_distance = distance
            nearest_node = node
    
    return nearest_node

