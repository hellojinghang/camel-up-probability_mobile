import streamlit as st
import pandas as pd
from itertools import permutations, product
from collections import defaultdict

# -----------------------------
# Camel movement logic
# -----------------------------
def update_positions(base_positions, moves, spectator_tiles):
    camels = list(base_positions.keys())
    stacks = {tile: [] for tile in range(17)}

    # Initialize stacks
    for camel in camels:
        tile, stack = base_positions[camel]
        stacks[tile].append((stack, camel))

    for tile in stacks:
        stacks[tile].sort()

    for camel, steps in moves:
        for tile, stack in stacks.items():
            for i, (_, c) in enumerate(stack):
                if c == camel:
                    if tile == 0:
                        camel_stack = [(0, camel)]
                        stacks[tile] = [x for x in stack if x[1] != camel]
                    else:
                        camel_stack = stack[i:]
                        stacks[tile] = stack[:i]

                    raw_dest_tile = tile + steps
                    final_dest_tile = raw_dest_tile

                    if raw_dest_tile in spectator_tiles:
                        effect = spectator_tiles[raw_dest_tile]
                        if effect == "oasis":
                            final_dest_tile = min(16, raw_dest_tile + 1)
                            stacks[final_dest_tile] = camel_stack + stacks[final_dest_tile]
                        elif effect == "mirage":
                            final_dest_tile = max(0, raw_dest_tile - 1)
                            stacks[final_dest_tile] = (
                                [(0, camel_stack[0][1])] +
                                [(idx + 1, cam) for idx, (_, cam) in enumerate(camel_stack[1:])] +
                                stacks[final_dest_tile]
                            )
                        else:
                            stacks[final_dest_tile] = camel_stack + stacks[final_dest_tile]
                        break
                    else:
                        stacks[raw_dest_tile] = camel_stack + stacks[raw_dest_tile]
                    break
            else:
                continue
            break

    final_positions = {}
    for tile, stack in stacks.items():
        for idx, (_, camel) in enumerate(stack):
            final_positions[camel] = (tile, idx)

    return final_positions


def rank_camels(positions):
    return [camel for camel, _ in sorted(positions.items(), key=lambda x: (x[1][0], -x[1][1]), reverse=True)]


def simulate_combinations(initial_positions, remaining_camels, spectator_tiles):
    dice_faces = [1, 2, 3]
    roll_combos = list(product(dice_faces, repeat=len(remaining_camels)))
    order_perms = list(permutations(remaining_camels))
    results = []

    for rolls in roll_combos:
        for order in order_perms:
            moves = list(zip(order, rolls))
            final_pos = update_positions(initial_positions, moves, spectator_tiles)
            rank = rank_camels(final_pos)
            results.append(rank)
    return results


def summarize_results(results):
    total = len(results)
    camel_rank_summary = defaultdict(lambda: [0] * 5)

    for rank in results:
        for i, camel in enumerate(rank):
            camel_rank_summary[camel][i] += 1

    df_camel_summary = pd.DataFrame([
        {
            "Camel": camel,
            **{f"{i+1}st (%)": round(count / total * 100, 2) for i, count in enumerate(ranks)},
            **{f"{i+1}st Count": count for i, count in enumerate(ranks)}
        }
        for camel, ranks in camel_rank_summary.items()
    ])

    return df_camel_summary.sort_values("1st (%)", ascending=False)

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Camel Up Probability Simulator", layout="wide")
st.title("🐫 Camel Up: Probability Simulator")

st.markdown("""
Configure camel positions and spectator tiles below.  
Results show **per-camel exact probabilities** of finishing in each position.
""")

camel_colors = ["Red", "Blue", "Yellow", "Orange", "Green"]

# -----------------------------
# Camel Positions (table input)
# -----------------------------
st.subheader("Camel Positions (Row by Row)")
df_positions = pd.DataFrame({
    "Camel": camel_colors,
    "Tile": [0] * len(camel_colors),
    "Stack": [0] * len(camel_colors),
})

edited_positions = st.data_editor(
    df_positions,
    hide_index=True,
    disabled=["Camel"],  # lock Camel column
    column_config={
        "Tile": st.column_config.NumberColumn("Tile (0–16)", min_value=0, max_value=16, step=1),
        "Stack": st.column_config.NumberColumn("Stack (0=bottom)", min_value=0, max_value=4, step=1),
    },
    use_container_width=True
)

# Convert back to dict for simulation
initial_positions = {row["Camel"]: (row["Tile"], row["Stack"]) for _, row in edited_positions.iterrows()}

# -----------------------------
# Remaining Camels to Roll
# -----------------------------
st.subheader("Remaining Camels to Roll")
cols = st.columns(3)
remaining_camels = []
for i, camel in enumerate(camel_colors):
    with cols[i % 3]:
        if st.checkbox(camel, key=f"rem_{camel}"):
            remaining_camels.append(camel)

# -----------------------------
# Spectator Tiles
# -----------------------------
st.subheader("Spectator Tiles")
spectator_tiles = {}
selected_tiles = st.multiselect("Select tile(s) for spectator effect", options=list(range(17)), key="spectator_tiles")

for tile in selected_tiles:
    effect = st.selectbox(f"Effect for tile {tile}", ["oasis", "mirage"], key=f"spectator_effect_{tile}")
    spectator_tiles[tile] = effect

# -----------------------------
# Run Simulation
# -----------------------------
if st.button("Run Simulation"):
    try:
        results = simulate_combinations(initial_positions, remaining_camels, spectator_tiles)
        df_summary = summarize_results(results)

        st.subheader("📊 Per-Camel Probability Distribution")
        st.dataframe(df_summary, use_container_width=True)

    except Exception as e:
        st.error(f"Error in simulation: {e}")
