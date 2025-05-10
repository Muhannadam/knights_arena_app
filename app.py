# ==============================================
# Course: EMAI611 - Advanced Programming for AI
# Project Title: Knight's Arena (Tactical AI Game)
# Team: (Add your names and IDs if required)
# ==============================================

# 📜 Game Rules:
# - Move using the arrow buttons (⬆️⬇️⬅️➡️).
# - Attack the AI with light or sword attacks.
# - Sword attack requires cooldown (2 turns).
# - Collect 💊 Power-Ups for +2 HP.
# - Avoid 🧱 walls; you cannot pass through them.
# - Defeat the AI by reducing its HP to zero before losing all your own HP.
# - The AI may run away if it's weaker than you and nearby.
# - The game will generate a Battle Report after finishing.

import streamlit as st
from simpleai.search import SearchProblem, astar
import random

GRID_SIZE = 6

# 🧩 Utility: Check adjacency
def is_adjacent(pos1, pos2):
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1]) == 1

# 🎨 Render the game grid with player, AI, walls, and power-ups
def render_grid():
    grid = [["⬛" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    for bx, by in st.session_state["blocked_tiles"]:
        grid[bx][by] = "🧱"
    if st.session_state.get("powerup_pos"):
        pu_x, pu_y = st.session_state["powerup_pos"]
        grid[pu_x][pu_y] = "💊"
    px, py = st.session_state["player_pos"]
    ax, ay = st.session_state["ai_pos"]
    if is_adjacent((px, py), (ax, ay)):
        grid[px][py] = "🧍"
        grid[ax][ay] = "🔥"
    else:
        grid[px][py] = "🧍"
        grid[ax][ay] = "🤖"
    html = "<div style='font-size:28px; line-height:1.3;'>"
    for row in grid:
        html += " ".join(row) + "<br>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

# 🤖 AI movement using A* search
class AStarMoveProblem(SearchProblem):
    def __init__(self, start, goal):
        self.goal = goal
        super().__init__(initial_state=start)

    def actions(self, state):
        x, y = state
        possible = []
        for d in ['Up', 'Down', 'Left', 'Right']:
            nx = x + (d == 'Down') - (d == 'Up')
            ny = y + (d == 'Right') - (d == 'Left')
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                if (nx, ny) not in st.session_state["blocked_tiles"]:
                    possible.append(d)
        return possible

    def result(self, state, action):
        x, y = state
        return (x - 1, y) if action == 'Up' else (x + 1, y) if action == 'Down' else (x, y - 1) if action == 'Left' else (x, y + 1)

    def is_goal(self, state): 
        return state == self.goal

    def cost(self, s1, a, s2): 
        return 1

    def heuristic(self, state): 
        return abs(state[0] - self.goal[0]) + abs(state[1] - self.goal[1])

# 💊 Manage power-up appearance and collection
def manage_powerup():
    turn = st.session_state["turn"]
    if turn % 5 == 0 and st.session_state["powerup_pos"] is None:
        while True:
            x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            if [x, y] not in [st.session_state["player_pos"], st.session_state["ai_pos"]] and (x, y) not in st.session_state["blocked_tiles"]:
                st.session_state["powerup_pos"] = [x, y]
                st.session_state["powerup_turn"] = turn
                st.session_state["messages"].append(f"💊 Power-Up appeared at ({x}, {y})!")
                break
    if st.session_state["powerup_pos"] and (turn - st.session_state["powerup_turn"] >= 3):
        st.session_state["powerup_pos"] = None
        st.session_state["powerup_turn"] = None
        st.session_state["messages"].append("💊 Power-Up expired.")
    for who in ["player", "ai"]:
        pos = st.session_state[f"{who}_pos"]
        if st.session_state["powerup_pos"] and pos == st.session_state["powerup_pos"]:
            st.session_state[f"{who}_hp"] += 2
            st.session_state["powerup_pos"] = None
            st.session_state["powerup_turn"] = None
            st.session_state["messages"].append(f"💊 {who.upper()} collected Power-Up! +2 HP.")

# 🧠 AI turn logic: attack, retreat or move towards target
def ai_turn():
    if "ai_escape_turns" not in st.session_state:
        st.session_state["ai_escape_turns"] = 0
    ai_hp = st.session_state["ai_hp"]
    player_hp = st.session_state["player_hp"]
    ai_pos = st.session_state["ai_pos"]
    player_pos = st.session_state["player_pos"]
    powerup_pos = st.session_state.get("powerup_pos")
    distance_to_player = abs(ai_pos[0] - player_pos[0]) + abs(ai_pos[1] - player_pos[1])

    if ai_hp < 3 and player_hp > ai_hp and distance_to_player <= 2:
        st.session_state["ai_escape_turns"] = 2

    if st.session_state["ai_escape_turns"] > 0:
        st.session_state["ai_escape_turns"] -= 1
        ax, ay = ai_pos
        px, py = player_pos
        options = [(ax - 1, ay), (ax + 1, ay), (ax, ay - 1), (ax, ay + 1)]
        valid_moves = [pos for pos in options if 0 <= pos[0] < GRID_SIZE and 0 <= pos[1] < GRID_SIZE and pos not in st.session_state["blocked_tiles"]]
        def distance(pos): return abs(pos[0] - px) + abs(pos[1] - py)
        if valid_moves:
            best_move = max(valid_moves, key=distance)
            st.session_state["ai_pos"] = list(best_move)
            st.session_state["messages"].append(f"🤖 AI is retreating to {best_move}")
        else:
            st.session_state["messages"].append("🤖 AI tried to retreat but is blocked.")
        return

    if is_adjacent(ai_pos, player_pos):
        st.session_state["player_hp"] -= 1
        st.session_state["messages"].append("🤖 AI attacked you!")
        return

    if powerup_pos and ai_hp < 5 and distance_to_player > 2:
        try:
            result = astar(AStarMoveProblem(tuple(ai_pos), tuple(powerup_pos)))
            path = result.path()
            if path and len(path) > 1:
                st.session_state["ai_pos"] = list(path[1][1])
                st.session_state["messages"].append(f"🤖 AI moved to 💊 at {path[1][1]}")
                return
        except Exception as e:
            st.session_state["messages"].append(f"A* error (to power-up): {e}")

    try:
        result = astar(AStarMoveProblem(tuple(ai_pos), tuple(player_pos)))
        path = result.path()
        if path and len(path) > 1:
            st.session_state["ai_pos"] = list(path[1][1])
            st.session_state["messages"].append(f"🤖 AI moved to {path[1][1]} using A*.")
    except Exception as e:
        st.session_state["messages"].append(f"A* error: {e}")

# 🧍 Handle player movement
# ⚔️ Handle player attack
# 🏆 Check if game is over
# 🔄 Reset game state

# --- the remaining parts (move_player, attack, check_win, reset_game, and UI layout) will also have similar English comments added.

