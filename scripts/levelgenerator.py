import random

MAX_JUMP_HEIGHT = 3
MAX_JUMP_WIDTH = 4 
SPAWNER_VARIANTS = [0,1]

def place_tile(tilemap, x, y, tile_type="grass", variant=0):
    tilemap[f"{x};{y}"] = {
        "type": tile_type,
        "variant": variant,
        "pos": [x, y]
    }

def generate_additional_islands(tilemap, islands, offgrid, max_islands=2, level_width=60, level_height=20):
    attempts = 0
    added = 0
    enemies_placed = 0

    while added < max_islands and attempts < 50:
        attempts += 1

        # Choose a random existing island to build from
        base_island = random.choice(islands)
        bx_min, bx_max, by_top, by_ground = base_island

        # Randomly decide placement: above or to the right
        if random.random() < 0.5:
            # Place above
            x_start = random.randint(bx_min, bx_max)
            y_ground = by_top - random.randint(1, MAX_JUMP_HEIGHT)
        else:
            # Place to the right
            x_start = bx_max + random.randint(1, MAX_JUMP_WIDTH)
            y_ground = random.randint(max(0, by_ground - MAX_JUMP_HEIGHT), min(level_height - 2, by_ground + MAX_JUMP_HEIGHT))

        # Generate island size
        width = random.randint(3, 7)
        height = random.randint(2, 4)
        new_island = (x_start, x_start + width - 1, y_ground - height + 1, y_ground)

        # Check placement rules
        if new_island[2] < 0:  # Can't spawn above top of level
            continue
        if not can_place_island(new_island, islands, buffer=2):
            continue

        # Place tiles
        for x in range(new_island[0], new_island[1] + 1):
            col_height = height
            if random.random() < 0.3:
                col_height = max(2, height + random.choice([-1,0,1]))
            col_top = new_island[3] - col_height + 1
            for y in range(col_top, new_island[3] + 1):
                place_tile(tilemap, x, y)

        # Place enemies
        num_enemies = random.randint(0,3)
        if num_enemies > 0:
            enemies_placed += num_enemies
        x_min, x_max, y_min, y_max = new_island
        for _ in range(num_enemies):
            enemy_x = random.randint(x_min, x_max)
            enemy_y = y_min
            offgrid.append({
                "type": "spawners",
                "variant": 1, 
                "pos": [enemy_x*16 + 0.5, enemy_y*16 + 0.5]
            })

        islands.append(new_island)
        added += 1

    # If no enemies were placed, force one on a random island
    if enemies_placed == 0 and islands:
        island = random.choice(islands[1:] or islands)  # Prefer non-starter islands
        x_min, x_max, y_min, y_max = island
        enemy_x = random.randint(x_min, x_max)
        enemy_y = y_min
        offgrid.append({
            "type": "spawners",
            "variant": 1,
            "pos": [enemy_x*16 + 0.5, enemy_y*16 + 0.5]
        })

def place_spawner(offgrid, island_bounds, variant=0):
    x_min, x_max, y_min, y_max = island_bounds
    spawner_x = (x_min + x_max) // 2
    spawner_y = y_min
    offgrid.append({
        "type": "spawners",
        "variant": variant,
        "pos": [spawner_x*16 + 0.5, spawner_y*16 + 0.5]
    })

def place_enemies(offgrid, island_bounds):
    num_enemies = random.randint(0,3)
    x_min, x_max, y_min, y_max = island_bounds
    for _ in range(num_enemies):
        enemy_x = random.randint(x_min, x_max)
        enemy_y = y_min
        offgrid.append({
            "type": "spawners",
            "variant": 1,
            "pos": [enemy_x*16 + 0.5, enemy_y*16 + 0.5]
        })

def can_place_island(new_island, existing_islands, buffer=2):
    """Check that new island doesn’t touch existing ones"""
    nx_min, nx_max, ny_min, ny_max = new_island
    for ix_min, ix_max, iy_min, iy_max in existing_islands:
        # Check horizontal buffer
        if nx_max + buffer >= ix_min and nx_min - buffer <= ix_max:
            # Check vertical buffer
            if ny_max + buffer >= iy_min and ny_min - buffer <= iy_max:
                return False
    return True
def generate_starter_island(tilemap, level_width, level_height, min_width=3, min_height=2, max_width=7, max_height=4):
    """
    Generates the starter island at the bottom-middle of the level.
    Returns the island bounds and spawn position.
    """
    # Middle of the level horizontally
    center_x = level_width // 2
    # Bottom of the level minus some padding
    y_ground = level_height - 2

    # Random island size
    width = random.randint(min_width, max_width)
    height = random.randint(min_height, max_height)

    x_start = center_x - width // 2
    y_top = y_ground - height + 1

    # Create irregular island shape
    for x in range(x_start, x_start + width):
        # Randomly vary column height to avoid perfect rectangle
        col_height = height
        if random.random() < 0.4:
            col_height = max(2, height + random.choice([-1, 0, 1]))
        col_top = y_ground - col_height + 1

        for y in range(col_top, y_ground + 1):
            place_tile(tilemap, x, y)

    # Middle of the island for spawn
    spawn_x = (x_start + x_start + width - 1) // 2
    spawn_y = y_ground

    # Return island bounds for reference: (x_start, x_end, y_top, y_ground)
    return (x_start, x_start + width - 1, y_top, y_ground)

def generate_level(tilemap, width=60, height=20):
    tilemap.clear()
    offgrid = []
    islands = []

    # 1. Starter island
    starter_x = 2
    starter_y = height - 5
    starter_island = generate_starter_island(tilemap, starter_x, starter_y)
    islands.append(starter_island)
    place_spawner(offgrid, starter_island, variant=0)
    spawn_x = (starter_island[0] + starter_island[1]) // 2
    spawn_y = starter_island[3]

    # 2. Generate additional islands
    generate_additional_islands(tilemap, islands, offgrid, max_islands=2, level_width=width, level_height=height)

    return spawn_x, spawn_y, offgrid
