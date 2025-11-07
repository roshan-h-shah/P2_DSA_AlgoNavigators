"""
Streamlit-based interactive pathfinding application.
Allows clicking on any nodes to select start/end and dynamically recalculates paths.
"""
import streamlit as st
import osmnx as ox
import networkx as nx
import folium
from folium import plugins
from streamlit_folium import st_folium
from pathfinding import dijkstra, astar, find_nearest_node
import pandas as pd
import time

# Page configuration
st.set_page_config(
    page_title="Pathfinding: Dijkstra & A*",
    page_icon="🗺️",
    layout="wide"
)

# Initialize session state
if 'graph' not in st.session_state:
    with st.spinner("Loading road network graph..."):
        st.session_state.graph = ox.graph_from_xml("map.osm", simplify=True)
        st.session_state.nodes_gdf, st.session_state.edges_gdf = ox.graph_to_gdfs(st.session_state.graph)
        st.success(f"Graph loaded: {len(st.session_state.graph.nodes())} nodes, {len(st.session_state.graph.edges())} edges")

if 'start_coords' not in st.session_state:
    st.session_state.start_coords = None
if 'end_coords' not in st.session_state:
    st.session_state.end_coords = None
if 'last_click' not in st.session_state:
    st.session_state.last_click = None
if 'path_results' not in st.session_state:
    st.session_state.path_results = None

# Title and description
st.title("🗺️ Interactive Pathfinding: Dijkstra & A*")
st.markdown("""
Click anywhere on the map to select start and end points. The path will be calculated automatically using both algorithms.
""")

# Sidebar controls
with st.sidebar:
    st.header("Controls")
    
    # Algorithm selection
    algorithm = st.radio(
        "Select Algorithm(s):",
        ["Both", "Dijkstra Only", "A* Only"],
        index=0
    )
    
    # Show graph overlay
    show_graph = st.checkbox("Show Road Network", value=True)
    
    # Sample size for graph overlay
    sample_size = st.slider("Graph Sample Size", 100, 2000, 1000, 100)
    
    # Clear selection button
    if st.button("Clear Selection", type="secondary"):
        st.session_state.start_coords = None
        st.session_state.end_coords = None
        st.session_state.path_results = None
        st.session_state.last_click = None
        st.rerun()
    
    # Manual coordinate input
    st.header("Manual Input")
    st.markdown("Or enter coordinates manually:")
    
    with st.form("manual_coords"):
        start_lat = st.number_input("Start Latitude", value=29.6426, format="%.6f")
        start_lon = st.number_input("Start Longitude", value=-82.3357, format="%.6f")
        end_lat = st.number_input("End Latitude", value=29.6500, format="%.6f")
        end_lon = st.number_input("End Longitude", value=-82.3400, format="%.6f")
        
        if st.form_submit_button("Set Coordinates"):
            st.session_state.start_coords = (start_lat, start_lon)
            st.session_state.end_coords = (end_lat, end_lon)
            st.session_state.path_results = None
            st.rerun()

# Get graph
G = st.session_state.graph
nodes_gdf = st.session_state.nodes_gdf

# Calculate map center
if st.session_state.start_coords and st.session_state.end_coords:
    center_lat = (st.session_state.start_coords[0] + st.session_state.end_coords[0]) / 2
    center_lon = (st.session_state.start_coords[1] + st.session_state.end_coords[1]) / 2
elif st.session_state.start_coords:
    center_lat, center_lon = st.session_state.start_coords
elif len(nodes_gdf) > 0:
    center_lat = nodes_gdf['y'].mean()
    center_lon = nodes_gdf['x'].mean()
else:
    center_lat, center_lon = 29.6426, -82.3357

# Create map
m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=14,
    tiles='OpenStreetMap'
)

# Add fullscreen and measure controls
plugins.Fullscreen().add_to(m)
plugins.MeasureControl().add_to(m)

# Add graph overlay
if show_graph:
    sample_nodes = nodes_gdf.sample(min(sample_size, len(nodes_gdf)))
    for idx, row in sample_nodes.iterrows():
        folium.CircleMarker(
            location=[row['y'], row['x']],
            radius=1,
            color='lightblue',
            fill=True,
            fillColor='lightblue',
            fillOpacity=0.2,
            weight=0
        ).add_to(m)

# Handle path calculation
path_results = None
if st.session_state.start_coords and st.session_state.end_coords:
    # Find nearest nodes
    start_node = find_nearest_node(G, st.session_state.start_coords[0], st.session_state.start_coords[1])
    end_node = find_nearest_node(G, st.session_state.end_coords[0], st.session_state.end_coords[1])
    
    if start_node is None or end_node is None:
        st.error("Could not find nearest nodes to selected coordinates")
    elif start_node == end_node:
        st.warning("Start and end points are the same!")
    else:
        # Calculate paths
        path_results = {}
        
        if algorithm in ["Both", "Dijkstra Only"]:
            with st.spinner("Running Dijkstra's algorithm..."):
                dijkstra_path, dijkstra_dist, dijkstra_stats = dijkstra(
                    G, start_node, end_node, weight='length'
                )
                path_results['dijkstra'] = {
                    'path': dijkstra_path,
                    'distance': dijkstra_dist,
                    'stats': dijkstra_stats,
                    'start_node': start_node,
                    'end_node': end_node
                }
        
        if algorithm in ["Both", "A* Only"]:
            with st.spinner("Running A* algorithm..."):
                astar_path, astar_dist, astar_stats = astar(
                    G, start_node, end_node, weight='length'
                )
                path_results['astar'] = {
                    'path': astar_path,
                    'distance': astar_dist,
                    'stats': astar_stats,
                    'start_node': start_node,
                    'end_node': end_node
                }
        
        st.session_state.path_results = path_results

# Visualize paths
if path_results:
    # Offset function for A* path
    def offset_path(path_coords, offset_meters=3):
        import math
        R = 6371000
        if len(path_coords) < 2:
            return path_coords
        
        offset_coords = []
        for i in range(len(path_coords)):
            if i == 0 or i == len(path_coords) - 1:
                offset_coords.append(path_coords[i])
            else:
                prev_lat, prev_lon = path_coords[i-1]
                curr_lat, curr_lon = path_coords[i]
                next_lat, next_lon = path_coords[i+1]
                
                dlat = next_lat - prev_lat
                dlon = next_lon - prev_lon
                
                perp_dlat = -dlon * math.cos(math.radians(curr_lat))
                perp_dlon = dlat / math.cos(math.radians(curr_lat))
                
                length = math.sqrt(perp_dlat**2 + perp_dlon**2)
                if length > 0:
                    perp_dlat /= length
                    perp_dlon /= length
                
                offset_lat = curr_lat + (offset_meters / R) * perp_dlat * (180 / math.pi)
                offset_lon = curr_lon + (offset_meters / R) * perp_dlon * (180 / math.pi)
                
                offset_coords.append([offset_lat, offset_lon])
        
        return offset_coords
    
    # Visualize Dijkstra path
    if 'dijkstra' in path_results and path_results['dijkstra']['path']:
        dijkstra_path = path_results['dijkstra']['path']
        dijkstra_dist = path_results['dijkstra']['distance']
        dijkstra_stats = path_results['dijkstra']['stats']
        
        path_coords = []
        for node_id in dijkstra_path:
            node_data = G.nodes[node_id]
            lat = node_data.get('y')
            lon = node_data.get('x')
            if lat is not None and lon is not None:
                path_coords.append([lat, lon])
        
        if len(path_coords) >= 2:
            exec_time = dijkstra_stats.get('execution_time', 0) * 1000
            folium.PolyLine(
                locations=path_coords,
                color='red',
                weight=6,
                opacity=0.9,
                popup=folium.Popup(
                    f"<b>Dijkstra Path</b><br>"
                    f"Distance: {dijkstra_dist:.2f} m<br>"
                    f"Execution time: {exec_time:.2f} ms<br>"
                    f"Nodes in path: {len(dijkstra_path)}<br>"
                    f"Nodes explored: {dijkstra_stats['nodes_explored']}<br>"
                    f"Nodes visited: {dijkstra_stats['nodes_visited']}",
                    max_width=300
                )
            ).add_to(m)
    
    # Visualize A* path
    if 'astar' in path_results and path_results['astar']['path']:
        astar_path = path_results['astar']['path']
        astar_dist = path_results['astar']['distance']
        astar_stats = path_results['astar']['stats']
        
        path_coords = []
        for node_id in astar_path:
            node_data = G.nodes[node_id]
            lat = node_data.get('y')
            lon = node_data.get('x')
            if lat is not None and lon is not None:
                path_coords.append([lat, lon])
        
        if len(path_coords) >= 2:
            exec_time = astar_stats.get('execution_time', 0) * 1000
            # Offset A* path
            offset_coords = offset_path(path_coords, offset_meters=3)
            
            folium.PolyLine(
                locations=offset_coords,
                color='blue',
                weight=6,
                opacity=0.9,
                dashArray='10, 5',
                popup=folium.Popup(
                    f"<b>A* Path</b><br>"
                    f"Distance: {astar_dist:.2f} m<br>"
                    f"Execution time: {exec_time:.2f} ms<br>"
                    f"Nodes in path: {len(astar_path)}<br>"
                    f"Nodes explored: {astar_stats['nodes_explored']}<br>"
                    f"Nodes visited: {astar_stats['nodes_visited']}",
                    max_width=300
                )
            ).add_to(m)
    
    # Add path nodes as clickable markers
    all_path_nodes = set()
    if 'dijkstra' in path_results:
        all_path_nodes.update(path_results['dijkstra']['path'])
    if 'astar' in path_results:
        all_path_nodes.update(path_results['astar']['path'])
    
    for node_id in all_path_nodes:
        node_data = G.nodes[node_id]
        lat = node_data.get('y')
        lon = node_data.get('x')
        
        if lat is not None and lon is not None:
            folium.CircleMarker(
                location=[lat, lon],
                radius=4,
                color='purple',
                fill=True,
                fillColor='purple',
                fillOpacity=0.7,
                weight=2,
                popup=folium.Popup(
                    f"<b>Path Node</b><br>Node ID: {node_id}<br>"
                    f"Lat: {lat:.6f}<br>Lon: {lon:.6f}",
                    max_width=200
                )
            ).add_to(m)

# Add start and end markers
if st.session_state.start_coords:
    folium.Marker(
        location=st.session_state.start_coords,
        popup=folium.Popup(
            f"<b>Start Point</b><br>"
            f"Lat: {st.session_state.start_coords[0]:.6f}<br>"
            f"Lon: {st.session_state.start_coords[1]:.6f}",
            max_width=200
        ),
        icon=folium.Icon(color='green', icon='info-sign')
    ).add_to(m)

if st.session_state.end_coords:
    folium.Marker(
        location=st.session_state.end_coords,
        popup=folium.Popup(
            f"<b>End Point</b><br>"
            f"Lat: {st.session_state.end_coords[0]:.6f}<br>"
            f"Lon: {st.session_state.end_coords[1]:.6f}",
            max_width=200
        ),
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)

# Add legend
legend_html = '''
<div style="position: fixed; 
            bottom: 50px; right: 10px; width: 200px; 
            background-color: white; border:2px solid grey; z-index:9999; 
            font-size:13px; padding: 10px">
<h4 style="margin-top:0; margin-bottom:8px;">Legend</h4>
<p style="margin:3px 0;"><span style="color:green; font-weight:bold">●</span> Start Point</p>
<p style="margin:3px 0;"><span style="color:red; font-weight:bold">●</span> End Point</p>
<p style="margin:3px 0;"><span style="color:red; font-weight:bold">━</span> Dijkstra Path</p>
<p style="margin:3px 0;"><span style="color:blue; font-weight:bold">━</span> A* Path (dashed)</p>
<p style="margin:3px 0;"><span style="color:purple; font-weight:bold">●</span> Path Nodes</p>
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# Display map and handle clicks
map_data = st_folium(m, width=None, height=600, returned_objects=["last_clicked"])

# Handle map clicks
if map_data["last_clicked"] is not None:
    clicked_lat = map_data["last_clicked"]["lat"]
    clicked_lon = map_data["last_clicked"]["lng"]
    
    # If we don't have a start point, set it
    if st.session_state.start_coords is None:
        st.session_state.start_coords = (clicked_lat, clicked_lon)
        st.session_state.path_results = None
        st.rerun()
    # If we have start but no end, set end
    elif st.session_state.end_coords is None:
        st.session_state.end_coords = (clicked_lat, clicked_lon)
        st.session_state.path_results = None
        st.rerun()
    # If we have both, update start (allow clicking to change)
    else:
        # Toggle: click to set new start
        st.session_state.start_coords = (clicked_lat, clicked_lon)
        st.session_state.end_coords = None  # Reset end so user can click again
        st.session_state.path_results = None
        st.rerun()

# Display results
if path_results:
    st.header("📊 Algorithm Performance")
    
    col1, col2 = st.columns(2)
    
    if 'dijkstra' in path_results and path_results['dijkstra']['path']:
        with col1:
            dijkstra_stats = path_results['dijkstra']['stats']
            dijkstra_dist = path_results['dijkstra']['distance']
            dijkstra_time = dijkstra_stats.get('execution_time', 0) * 1000
            
            st.markdown("### 🔴 Dijkstra's Algorithm")
            st.metric("Distance", f"{dijkstra_dist:.2f} m")
            st.metric("Execution Time", f"{dijkstra_time:.2f} ms")
            st.metric("Nodes Explored", f"{dijkstra_stats['nodes_explored']:,}")
            st.metric("Nodes Visited", f"{dijkstra_stats['nodes_visited']:,}")
            st.metric("Path Length", f"{dijkstra_stats['path_length']} nodes")
    
    if 'astar' in path_results and path_results['astar']['path']:
        with col2:
            astar_stats = path_results['astar']['stats']
            astar_dist = path_results['astar']['distance']
            astar_time = astar_stats.get('execution_time', 0) * 1000
            
            st.markdown("### 🔵 A* Algorithm")
            st.metric("Distance", f"{astar_dist:.2f} m")
            st.metric("Execution Time", f"{astar_time:.2f} ms")
            st.metric("Nodes Explored", f"{astar_stats['nodes_explored']:,}")
            st.metric("Nodes Visited", f"{astar_stats['nodes_visited']:,}")
            st.metric("Path Length", f"{astar_stats['path_length']} nodes")
    
    # Comparison
    if 'dijkstra' in path_results and 'astar' in path_results:
        if path_results['dijkstra']['path'] and path_results['astar']['path']:
            st.markdown("---")
            st.subheader("📈 Comparison")
            
            dijkstra_time = path_results['dijkstra']['stats'].get('execution_time', 0) * 1000
            astar_time = path_results['astar']['stats'].get('execution_time', 0) * 1000
            time_diff = abs(dijkstra_time - astar_time)
            speed_improvement = ((dijkstra_time - astar_time) / dijkstra_time * 100) if dijkstra_time > 0 else 0
            
            dist_diff = abs(path_results['dijkstra']['distance'] - path_results['astar']['distance'])
            
            comp_col1, comp_col2, comp_col3 = st.columns(3)
            with comp_col1:
                st.metric("Time Difference", f"{time_diff:.2f} ms")
            with comp_col2:
                if speed_improvement > 0:
                    st.metric("Speed Improvement", f"{speed_improvement:.1f}%", f"A* is faster")
                else:
                    st.metric("Speed Improvement", f"{abs(speed_improvement):.1f}%", f"Dijkstra is faster")
            with comp_col3:
                st.metric("Distance Difference", f"{dist_diff:.2f} m")
            
            # Efficiency comparison
            dijkstra_explored = path_results['dijkstra']['stats']['nodes_explored']
            astar_explored = path_results['astar']['stats']['nodes_explored']
            efficiency_improvement = ((dijkstra_explored - astar_explored) / dijkstra_explored * 100) if dijkstra_explored > 0 else 0
            
            if efficiency_improvement > 0:
                st.success(f"✅ A* explored {efficiency_improvement:.1f}% fewer nodes ({astar_explored:,} vs {dijkstra_explored:,})")
            else:
                st.info(f"ℹ️ Dijkstra explored {abs(efficiency_improvement):.1f}% fewer nodes ({dijkstra_explored:,} vs {astar_explored:,})")
    
    # Instructions
    st.info("💡 **Tip**: Click anywhere on the map to select a new start point. The end point will reset, then click again for the end point.")

else:
    if st.session_state.start_coords is None:
        st.info("👆 **Click anywhere on the map to select the start point**")
    elif st.session_state.end_coords is None:
        st.info("👆 **Click anywhere on the map to select the end point**")

