"""
Simple testcases 4 us to verify the algorithms work properly - made by Krish + Sriniketh
Couldve done pytest but this was simpkle for prototyping rn
"""
import osmnx as ox
import networkx as nx
from pathfinding import dijkstra, astar, find_nearest_node

def test_pathfinding():
    "Test the pathfinding algorithms. - very very imprtant - make sure this works"
    print("=" * 60)
    print("Testing Pathfinding Algorithms")
    print("=" * 60)
    
    # Load the graph from oms file
  
    try:
        G = ox.graph_from_xml("map.osm", simplify=True)
        print(f"Graph  loaded: {len(G.nodes())} nodes, {len(G.edges())} edges")
    except Exception as e:
        print(f"Error {e}")
        return False
    
    # Get testing nodes
    nodes_list = list(G.nodes())
    if len(nodes_list) < 2:
        print("Not enough nodes  inG")
        return False
    
    source = nodes_list[0]
    target = nodes_list[min(1000, len(nodes_list) - 1)]  # Use closer nodes fto test - faster
    
    print(f"Testing with nodes:")
    print(f" Source: {source}")
    print(f" Target: {target}")
    
    # Test Dijkstra

    print("Testing Dijkstra's Algorithm")

    try:
        path, distance, stats = dijkstra(G, source, target, weight='length')
        if path:
            print(f"Path found!")
            print(f"  Path length: {len(path)} nodes")
            print(f" Distance: {distance:.2f} meters")
            print(f" Nodes explored: {stats['nodes_explored']}")
            print(f" Nodes visited {stats['nodes_visited']}")
        else:
            #should we returbn error here?
            return False
    except Exception as e:
        print(f" Failed - Error in Dijkstra: {e}") #this is happening too much - graph disconnected need to fix soon!!
        import traceback
        traceback.print_exc()
        return False
    
    # Test A*

    print("Testing A Algorithm")
 


    try:
        path, distance, stats = astar(G, source, target, weight='length')
        if path:
            print(f"Path found!")
            print(f"Path length: {len(path)} nodes")
            print(f"Distance: {distance:.2f} meters")

        else:
            print("✗ No path found")
            return False
    except Exception as e:
        print(f"✗ Error in A*: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test find_nearest_node

    print("Testing find_nearest_node fn")

    try:
        source_data = G.nodes[source]
        test_lat = source_data.get('y')
        test_lon = source_data.get('x')
        
        if test_lat is None or test_lon is None:
            print("Source node missing coordinates")
            return False
        
        nearest = find_nearest_node(G, test_lat, test_lon)
        if nearest == source:
            print(f"Found correct nearest node: {nearest}")
        else:
            print(f"Nearest node {nearest} differs from source {source}")

    except Exception as e:
        print(f" Error : {e}")
        return False
    
    
    # Compare results of everyhing

    print("Comparison! - Dijkstra vs A")

    dijkstra_path, dijkstra_dist, dijkstra_stats = dijkstra(G, source, target, weight='length')
    astar_path, astar_dist, astar_stats = astar(G, source, target, weight='length')
    
    if dijkstra_path and  astar_path:

        diff = abs(dijkstra_dist - astar_dist)
        print(f"Dijkstra distance: {dijkstra_dist} m")
        print(f"A* distance:       {astar_dist} m")
        print(f"Difference:        {diff} m")
        
        if diff < 0.01:  # Very small difference (essentially same)
            print("✓ Both algorithms found essentially the same path!") #this bc so many nodes in the graph - so many possible paths
        else:
            print(" Paths differ")
        
        print(f"Dijkstra explored: {dijkstra_stats['nodes_explored']} nodes")
        print(f"A* explored:       {astar_stats['nodes_explored']} nodes")
        
        if astar_stats['nodes_explored'] < dijkstra_stats['nodes_explored']:
            improvement = ((dijkstra_stats['nodes_explored'] - astar_stats['nodes_explored']) / 
                          dijkstra_stats['nodes_explored'] * 100)
            print(f"✓ A* was  X {improvement}% more efficient")
        elif dijkstra_stats['nodes_explored'] < astar_stats['nodes_explored']:
            print("Dijkstra explored fewer nodes (unusual for A*)") #make sure this rarely happens-
        else:
            print(" Both algorithms explored similar number of nodes")
    

    print("All tests passed!!")

    return True

if __name__ == "__main__":
    success = test_pathfinding()
    exit(0 if success else 1)


