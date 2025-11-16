import json
from process_map_data import MapGraph
def get_directions(start: str, end: str):
    """
    Find the navigation path between two map nodes in the Pokémon world.

    This tool loads the prebuilt map graph from disk and computes the path
    between the given start and end map names. The path is determined using
    the underlying MapGraph's pathfinding logic (typically BFS/A*, depending
    on its implementation).

    Parameters
    ----------
    start : str
        The name/label of the starting map (e.g., "PALLET_TOWN", "VIRIDIAN_CITY").
    end : str
        The name/label of the destination map.

    Returns
    -------
    list[str]
        An ordered list of map names representing the path from `start` to `end`.
        The first element is `start`, the last is `end`. Returns `None` if no path
        exists or either map is invalid.

    Notes
    -----
    - This function reads the map graph from
      `src/pokemon_agent/utils/ref_data/maps/map_graph.json`.
    - The function does not validate whether the map names exist; invalid names
      may result in `None` or an exception depending on the MapGraph implementation.
    - Designed for use as a tool in an LLM agent: provide clear, valid map names
      when calling.
    """
    with open("src/pokemon_agent/utils/ref_data/maps/map_graph.json") as f:
        MAP_GRAPH = json.load(f)
    g = MapGraph.from_dict(MAP_GRAPH)

    return g.find_path(start, end)

