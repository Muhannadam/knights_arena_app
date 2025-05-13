# ============================================================
# Course: EMAI611 - Advanced Programming for AI
# Project Title: Knight's Arena (Tactical AI Battle Game)
# ============================================================

import streamlit as st
from simpleai.search import SearchProblem, astar
import random

GRID_SIZE = 6

# 📜 Game Rules text
game_rules = """
### 📜 Game Rules:
- Move the player using arrow buttons (⬆️⬇️⬅️➡️).
- Attack the AI using "Light Hit" (🖐) or "Sword Attack" (🗡️).
- Sword Attack requires 2 turns to recharge after use.
- Power-Ups (💊) appear every 5 turns, granting +2 HP when collected.
- AI will intelligently attack, retreat, or move towards Power-Ups.
- Walls (🧱) are randomly placed and block movement.
- Goal: Defeat the AI before your HP reaches zero!
- A full Battle Report is generated after the game ends.
"""

# 🧩 Check adjacency
def is_adjacent(pos1, pos2):
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1]) == 1

# 🎨 Render the game grid
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

# 🤖 AI Pathfinding with A*
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

    def is_goal(self, state): return state == self.goal
    def cost(self, s1, a, s2): return 1
    def heuristic(self, state): return abs(state[0] - self.goal[0]) + abs(state[1] - self.goal[1])

# 💊 Manage Power-Ups
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

# 🤖 AI behavior
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
        except:
            pass

    try:
        result = astar(AStarMoveProblem(tuple(ai_pos), tuple(player_pos)))
        path = result.path()
        if path and len(path) > 1:
            st.session_state["ai_pos"] = list(path[1][1])
            st.session_state["messages"].append(f"🤖 AI moved to {path[1][1]} using A*.")
    except:
        pass

# 🧍 Player movement
def move_player(direction):
    if st.session_state["game_over"]: return
    x, y = st.session_state["player_pos"]
    nx, ny = x, y
    if direction == "Up" and x > 0: nx -= 1
    elif direction == "Down" and x < GRID_SIZE - 1: nx += 1
    elif direction == "Left" and y > 0: ny -= 1
    elif direction == "Right" and y < GRID_SIZE - 1: ny += 1
    if (nx, ny) not in st.session_state["blocked_tiles"]:
        st.session_state["player_pos"] = [nx, ny]
        st.session_state["messages"].append(f"🧍 Player moved {direction}")
    else:
        st.session_state["messages"].append("🚫 Move blocked by wall!")
    manage_powerup()
    ai_turn()
    check_win()
    st.session_state["turn"] += 1

# ⚔️ Player attack
def attack(type="light"):
    if st.session_state["game_over"]: return
    damage = 1 if type == "light" else 2
    label = "🖐 Light Hit" if type == "light" else "🗡️ Sword Attack"
    if is_adjacent(st.session_state["player_pos"], st.session_state["ai_pos"]):
        st.session_state["ai_hp"] -= damage
        st.session_state["messages"].append(f"{label}: You dealt {damage} damage.")
    else:
        st.session_state["messages"].append("⚠️ No enemy in range.")
    manage_powerup()
    ai_turn()
    check_win()
    st.session_state["turn"] += 1

# 🏆 Check winning conditions
def check_win():
    player_hp = st.session_state["player_hp"]
    ai_hp = st.session_state["ai_hp"]
    if player_hp <= 0 and ai_hp <= 0:
        result = "⚖️ It's a draw!"
    elif ai_hp <= 0:
        result = "🎉 You win!"
    elif player_hp <= 0:
        result = "💀 AI wins!"
    else:
        return
    st.session_state["game_over"] = True
    st.session_state["messages"].append(result)

# 🔄 Reset game state
def reset_game():
    blocked = set()
    while len(blocked) < 5:
        x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
        if [x, y] not in [[0, 0], [GRID_SIZE-1, GRID_SIZE-1]]:
            blocked.add((x, y))
    st.session_state.update({
        "player_pos": [0, 0],
        "ai_pos": [GRID_SIZE - 1, GRID_SIZE - 1],
        "player_hp": 10,
        "ai_hp": 10,
        "messages": [],
        "turn": 1,
        "game_over": False,
        "powerup_pos": None,
        "powerup_turn": None,
        "blocked_tiles": list(blocked),
    })

# Initialize game
if "player_pos" not in st.session_state:
    reset_game()

# Layout
st.title("🛡️ Knight's Arena")

col1, col2, col3 = st.columns([2.2, 1.2, 1.6])

with col1:
    if st.session_state["game_over"]:
        st.markdown(f"### {st.session_state['messages'][-1]}")
    render_grid()
    st.markdown(f"**Turn {st.session_state['turn']}** | 🧍 HP: {st.session_state['player_hp']} | 🤖 HP: {st.session_state['ai_hp']}")

with col2:
    st.markdown("### 🎮 Movement")
    st.button("⬆️", on_click=move_player, args=("Up",), use_container_width=True)
    row = st.columns(3)
    with row[0]: st.button("⬅️", on_click=move_player, args=("Left",), use_container_width=True)
    with row[1]: st.button("⬇️", on_click=move_player, args=("Down",), use_container_width=True)
    with row[2]: st.button("➡️", on_click=move_player, args=("Right",), use_container_width=True)
    st.markdown("### ⚔️ Attacks")
    st.button("🖐 Light Hit", on_click=attack, kwargs={"type": "light"}, use_container_width=True)
    st.button("🗡️ Sword Attack", on_click=attack, kwargs={"type": "sword"}, use_container_width=True)
    st.button("🔄 Restart", on_click=reset_game, use_container_width=True)
    if st.button("📜 View Game Rules", use_container_width=True):
        st.markdown(game_rules)

with col3:
    st.markdown("### 📜 History")
    st.markdown("<div style='max-height:450px; overflow:auto;'>", unsafe_allow_html=True)
    for msg in reversed(st.session_state["messages"][-20:]):
        st.markdown(f"- {msg}")
    st.markdown("</div>", unsafe_allow_html=True)
