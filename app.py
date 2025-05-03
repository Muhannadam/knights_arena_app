import streamlit as st
import random

# Title
st.set_page_config(page_title="Knight's Arena – Challenge Mode", layout="centered")
st.title("⚔️ Knight's Arena – Challenge Mode")

# Constants
GRID_SIZE = 6
MAX_ATTACKS = 3

# Initialize session state
if "player_pos" not in st.session_state:
    st.session_state.player_pos = [0, 0]
    st.session_state.ai_pos = [GRID_SIZE - 1, GRID_SIZE - 1]
    st.session_state.player_hp = 3
    st.session_state.ai_hp = 3
    st.session_state.turn = 1
    st.session_state.history = []
    st.session_state.attacks_left = MAX_ATTACKS
    st.session_state.winner = ""

def render_grid():
    grid_html = ""
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            cell = "⬛"
            if [i, j] == st.session_state.player_pos:
                cell = "🧍"
            elif [i, j] == st.session_state.ai_pos:
                cell = "🤖"
            grid_html += f"{cell} "
        grid_html += "<br>"
    return grid_html

def are_adjacent(pos1, pos2):
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1]) == 1

def move_player(direction):
    if st.session_state.winner:
        return
    x, y = st.session_state.player_pos
    if direction == "Up" and x > 0:
        x -= 1
    elif direction == "Down" and x < GRID_SIZE - 1:
        x += 1
    elif direction == "Left" and y > 0:
        y -= 1
    elif direction == "Right" and y < GRID_SIZE - 1:
        y += 1
    st.session_state.player_pos = [x, y]
    st.session_state.history.append(f"🧍 moved {direction}")
    process_ai_turn()

def attack():
    if st.session_state.winner or st.session_state.attacks_left <= 0:
        return
    if are_adjacent(st.session_state.player_pos, st.session_state.ai_pos):
        st.session_state.ai_hp -= 1
        st.session_state.attacks_left -= 1
        st.session_state.history.append("🧍 attacked 🤖!")
        if st.session_state.ai_hp <= 0:
            st.session_state.winner = "You win! 🎉"
    else:
        st.session_state.history.append("🧍 missed!")
        st.session_state.attacks_left -= 1
    process_ai_turn()

def process_ai_turn():
    if st.session_state.winner:
        return
    px, py = st.session_state.player_pos
    ax, ay = st.session_state.ai_pos
    dx = 1 if px > ax else -1 if px < ax else 0
    dy = 1 if py > ay else -1 if py < ay else 0
    if abs(px - ax) > abs(py - ay):
        ax += dx
    else:
        ay += dy
    st.session_state.ai_pos = [ax, ay]
    st.session_state.history.append("🤖 moved")
    # AI attack if adjacent
    if are_adjacent(st.session_state.player_pos, st.session_state.ai_pos):
        st.session_state.player_hp -= 1
        st.session_state.history.append("🤖 attacked 🧍!")
        if st.session_state.player_hp <= 0:
            st.session_state.winner = "You lost 😢"
    # Check for draw
    if st.session_state.attacks_left == 0 and st.session_state.ai_hp > 0 and not st.session_state.winner:
        st.session_state.winner = "Draw 🤝"

def restart():
    for key in list(st.session_state.keys()):
        del st.session_state[key]

# Layout
st.markdown(render_grid(), unsafe_allow_html=True)

# Game status
st.markdown(f"**Turn:** {st.session_state.turn} | 🧍 HP: {st.session_state.player_hp} | 🤖 HP: {st.session_state.ai_hp} | 🪓 Attacks Left: {st.session_state.attacks_left}")

if st.session_state.winner:
    st.success(st.session_state.winner)

# Controls
col1, col2, col3 = st.columns(3)
with col2:
    st.button("⬆️", on_click=move_player, args=("Up",))
with col1:
    st.button("⬅️", on_click=move_player, args=("Left",))
    st.button("⬇️", on_click=move_player, args=("Down",))
with col3:
    st.button("➡️", on_click=move_player, args=("Right",))

st.button("🗡️ Attack", on_click=attack)
st.button("🔄 Restart", on_click=restart)

# History
st.subheader("📄 History")
for log in reversed(st.session_state.history[-10:]):
    st.write(log)
