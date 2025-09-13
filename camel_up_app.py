import streamlit as st
import pandas as pd

st.set_page_config(page_title="Camel Up Probability", layout="wide")

st.title("🐪 Camel Up Probability Calculator")

# -----------------------------
# Camel position input (spreadsheet style)
# -----------------------------
camel_colors = ["Blue", "Green", "Orange", "Yellow", "White"]

st.subheader("Camel Positions (Row by Row)")

# Initial dataframe
df_positions = pd.DataFrame({
    "Camel": camel_colors,
    "Tile": [0] * len(camel_colors),
    "Stack": [0] * len(camel_colors),
})

# Editable table
edited_positions = st.data_editor(
    df_positions,
    hide_index=True,
    disabled=["Camel"],  # lock Camel column
    column_config={
        "Tile": st.column_config.NumberColumn(
            "Tile (0–16)", min_value=0, max_value=16, step=1
        ),
        "Stack": st.column_config.NumberColumn(
            "Stack (0=bottom)", min_value=0, max_value=4, step=1
        ),
    },
    use_container_width=True
)

st.write("✅ Current Camel Positions")
st.dataframe(edited_positions, use_container_width=True)

# -----------------------------
# Remaining Camels (checkbox grid)
# -----------------------------
st.subheader("Remaining Camels to Roll")
cols = st.columns(3)
remaining_camels = []
for i, camel in enumerate(camel_colors):
    with cols[i % 3]:
        if st.checkbox(camel, key=f"rem_{camel}"):
            remaining_camels.append(camel)

# -----------------------------
# Spectator Tiles (dropdown + add button style recommended)
# -----------------------------
st.subheader("Spectator Tiles")
# Example placeholder — can expand later
spectator_tiles = st.multiselect("Select spectator tiles", camel_colors)

# -----------------------------
# Probability Calculation Button
# -----------------------------
if st.button("Calculate Probabilities"):
    st.success("🔮 Probability calculation goes here... (to be integrated with your model)")
    # Example output placeholder
    st.write("Rank Orders (Top 10)")
    st.dataframe(pd.DataFrame({
        "Rank": range(1, 6),
        "Camel": ["Blue", "Orange", "Green", "Yellow", "White"]
    }), use_container_width=True)
