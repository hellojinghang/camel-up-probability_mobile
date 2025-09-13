import streamlit as st
import pandas as pd
from itertools import permutations, product
from collections import defaultdict

# ==============================
# Camel Up Logic
# ==============================

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
                        elif effect == "mirage":
                            final_dest_tile = max(0, raw_dest_tile - 1)

                    stacks[final_dest_tile] = camel_stack + stacks[final_dest_tile]
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
    if not remaining_camels:
        return [rank_camels(initial_positions)]

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
    rank_counter = defaultdict(int)
    total = len(results)

    for rank in results:
        rank_counter[tuple(rank)] += 1

    df_rank = pd.DataFrame([
        {
            "Rank Order": " > ".join(r),
            "Count": c,
            "Probability (%)": c / total * 100
        }
        for r, c in sorted(rank_counter.items(), key=lambda x: -x[1])
    ])

    camel_rank_summary = defaultdict(lambda: [0] * 5)
    for rank in results:
        for i, camel in enumerate(rank):
            camel_rank_summary[camel][i] += 1

    df_camel_summary = pd.DataFrame([
        {
            "Camel": camel,
            **{f"{i+1}st": count / total * 100 for i, count in enumerate(ranks)},
            **{f"{i+1}st Count": count for i, count in enumerate(ranks)}
        }
        for camel, ranks in camel_rank_summary.items()
    ])
    return df_rank, df_camel_summary.sort_values("1st", ascending=False)


# ==============================
# Streamlit UI (Mobile First)
# ==============================

st.set_page_config(layout="wide")

st.title("🐫 Camel Up: Probability Simulator")

st.markdown("Designed with **mobile-friendly controls**: number inputs, checkboxes, and tabs.")

camel_colors = ["Red", "Blue", "Yellow", "Orange", "Green"]

with st.form("input_form"):
    # -----------------
    # Camel Positions
    # -----------------
    with st.expander("🐪 Camel Positions"):
        st.write("Set starting tile (0–16) and stack (0=bottom).")
        initial_positions = {}
        all_positions = set()

        cols = st.columns(2)  # two per row
        for i, camel in enumerate(camel_colors):
            with cols[i % 2]:
                st.markdown(f"**{camel}**")
                tile = st.number_input("Tile", 0, 16, 1, key=f"{camel}_tile")
                stack_pos = st.number_input("Stack", 0, 4, 0, key=f"{camel}_stack")
                if (tile, stack_pos) in all_positions:
                    st.error(f"Duplicate: {camel} at tile {tile}, stack {stack_pos}")
                all_positions.add((tile, stack_pos))
                initial_positions[camel] = (tile, stack_pos)

    # -----------------
    # Remaining Camels
    # -----------------
    with st.expander("🎲 Remaining Camels to Roll"):
        st.write("Tick the camels that still need to roll.")
        cols = st.columns(3)
        remaining_camels = []
        for i, camel in enumerate(camel_colors):
            with cols[i % 3]:
                if st.checkbox(camel, key=f"rem_{camel}"):
                    remaining_camels.append(camel)

    # -----------------
    # Spectator Tiles
    # -----------------
    with st.expander("👥 Spectator Tiles"):
        st.write("Add spectator tiles one by one (no adjacency allowed).")

        spectator_tiles = {}
        valid_spectator_tiles = st.session_state.get("spectator_tiles", [])

        col1, col2, col3 = st.columns([1,1,2])
        with col1:
            new_tile = st.number_input("Tile", 0, 16, 0, key="new_spec_tile")
        with col2:
            new_effect = st.selectbox("Effect", ["oasis", "mirage"], key="new_spec_effect")
        with col3:
            if st.form_submit_button("➕ Add Tile", use_container_width=True):
                if new_tile in valid_spectator_tiles:
                    st.warning(f"Tile {new_tile} already used.")
                elif any(abs(new_tile - t) == 1 for t in valid_spectator_tiles):
                    st.warning(f"Tile {new_tile} is adjacent to another spectator tile.")
                else:
                    valid_spectator_tiles.append(new_tile)
                    st.session_state["spectator_tiles"] = valid_spectator_tiles
                    st.session_state[f"effect_{new_tile}"] = new_effect

        # Display current spectator tiles
        if valid_spectator_tiles:
            st.write("Current spectator tiles:")
            for t in valid_spectator_tiles:
                eff = st.session_state.get(f"effect_{t}", "oasis")
                st.write(f"• Tile {t}: {eff}")
                if st.form_submit_button(f"❌ Remove {t}"):
                    valid_spectator_tiles.remove(t)
                    st.session_state["spectator_tiles"] = valid_spectator_tiles

        for t in valid_spectator_tiles:
            spectator_tiles[t] = st.session_state.get(f"effect_{t}", "oasis")

    simulate = st.form_submit_button("Run Simulation", use_container_width=True)

# -----------------
# Results
# -----------------
if simulate:
    if len(all_positions) < len(camel_colors):
        st.error("Invalid configuration: Duplicate camel positions detected.")
    else:
        try:
            results = simulate_combinations(initial_positions, remaining_camels, spectator_tiles)
            df_rank, df_summary = summarize_results(results)

            tab1, tab2 = st.tabs(["🔢 Rank Orders", "📊 Camel Summary"])
            with tab1:
                st.dataframe(df_rank.head(10), use_container_width=True)
            with tab2:
                st.dataframe(df_summary, use_container_width=True)

        except Exception as e:
            st.error(f"Error in simulation: {e}")
