import streamlit as st
from simpleai.search import SearchProblem, astar
import random

GRID_SIZE = 6

def is_adjacent(pos1, pos2):
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1]) == 1

def render_grid():
    grid = [["⬛" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    for bx, by in st.session_state["blocked_tiles"]:
        grid[bx][by] = "🧱"
    if st.session_state.get("bomb_tile"):
        bx, by = st.session_state["bomb_tile"]["pos"]
        grid[bx][by] = "💣"
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
        return (x - 1, y) if action == 'Up' else (x + 1, y) if action == 'Down' else \
               (x, y - 1) if action == 'Left' else (x, y + 1)
    def is_goal(self, state): return state == self.goal
    def cost(self, s1, a, s2): return 1
    def heuristic(self, state): return abs(state[0] - self.goal[0]) + abs(state[1] - self.goal[1])

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

def manage_bomb():
    if "bomb_tile" in st.session_state and st.session_state["bomb_tile"]:
        st.session_state["bomb_tile"]["timer"] -= 1
        if st.session_state["bomb_tile"]["timer"] <= 0:
            bx, by = st.session_state["bomb_tile"]["pos"]
            for who in ["player", "ai"]:
                x, y = st.session_state[f"{who}_pos"]
                if (x, y) == (bx, by) or is_adjacent((x, y), (bx, by)):
                    st.session_state[f"{who}_hp"] -= 3
                    st.session_state["messages"].append(f"💥 Bomb exploded! {who.upper()} took 3 damage.")
            st.session_state["bomb_tile"] = None
    elif st.session_state["turn"] % 7 == 0:
        while True:
            x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            if (x, y) not in st.session_state["blocked_tiles"] and [x, y] not in [st.session_state["player_pos"], st.session_state["ai_pos"]]:
                st.session_state["bomb_tile"] = {"pos": (x, y), "timer": 2}
                st.session_state["messages"].append(f"💣 Bomb appeared at ({x}, {y})! Explodes in 2 turns.")
                break

def update_dynamic_walls():
    if st.session_state["turn"] % 10 == 0:
        blocked = set()
        while len(blocked) < 5:
            x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            if (x, y) not in [tuple(st.session_state["player_pos"]), tuple(st.session_state["ai_pos"])]:
                if st.session_state.get("powerup_pos") and (x, y) == tuple(st.session_state["powerup_pos"]): continue
                if st.session_state.get("bomb_tile") and (x, y) == st.session_state["bomb_tile"]["pos"]: continue
                blocked.add((x, y))
        st.session_state["blocked_tiles"] = list(blocked)
        st.session_state["messages"].append("🧱 Map changed! New walls generated.")

def ai_turn():
    if st.session_state["ai_hp"] <= 0: return
    ai_pos = st.session_state["ai_pos"]
    player_pos = st.session_state["player_pos"]
    if is_adjacent(ai_pos, player_pos):
        st.session_state["player_hp"] -= 1
        st.session_state["messages"].append("🤖 AI attacked you!")
    else:
        try:
            result = astar(AStarMoveProblem(tuple(ai_pos), tuple(player_pos)))
            path = result.path()
            if path and len(path) > 1:
                st.session_state["ai_pos"] = list(path[1][1])
                st.session_state["messages"].append(f"🤖 AI moved to {path[1][1]}")
        except:
            pass

def move_player(direction):
    if st.session_state["game_over"] or st.session_state["stamina"] <= 0:
        st.session_state["messages"].append("⚠️ Not enough stamina!") if st.session_state["stamina"] <= 0 else None
        return
    x, y = st.session_state["player_pos"]
    nx, ny = x, y
    if direction == "Up" and x > 0: nx -= 1
    elif direction == "Down" and x < GRID_SIZE - 1: nx += 1
    elif direction == "Left" and y > 0: ny -= 1
    elif direction == "Right" and y < GRID_SIZE - 1: ny += 1
    if (nx, ny) not in st.session_state["blocked_tiles"]:
        st.session_state["player_pos"] = [nx, ny]
        st.session_state["messages"].append(f"🧍 Player moved {direction}")
        st.session_state["stamina"] -= 1
    else:
        st.session_state["messages"].append("🚫 Move blocked!")
    run_turn()

def attack(type="light"):
    if st.session_state["game_over"] or st.session_state["stamina"] <= 0:
        st.session_state["messages"].append("⚠️ Not enough stamina!") if st.session_state["stamina"] <= 0 else None
        return
    dmg = 1 if type == "light" else 2
    name = "🖐 Light Hit" if type == "light" else "🗡️ Sword"
    if type == "special":
        if st.session_state["turn"] % 7 != 0:
            st.session_state["messages"].append("❌ Special not ready!")
            return
        dmg = 4
        name = "💥 SPECIAL ATTACK"
    if is_adjacent(st.session_state["player_pos"], st.session_state["ai_pos"]):
        st.session_state["ai_hp"] -= dmg
        st.session_state["messages"].append(f"{name}: {dmg} damage!")
    else:
        st.session_state["messages"].append("⚠️ No enemy in range.")
    st.session_state["stamina"] -= 1
    run_turn()

def run_turn():
    st.session_state["turn"] += 1
    st.session_state["stamina"] = min(st.session_state["stamina"] + 1, 5)
    manage_powerup()
    manage_bomb()
    update_dynamic_walls()
    ai_turn()
    check_win()

def check_win():
    p, a = st.session_state["player_hp"], st.session_state["ai_hp"]
    if p <= 0 and a <= 0:
        msg = "⚖️ Draw!"
    elif a <= 0:
        msg = "🎉 You win!"
    elif p <= 0:
        msg = "💀 AI wins!"
    else:
        return
    st.session_state["game_over"] = True
    st.session_state["messages"].append(msg)

def reset_game():
    st.session_state.update({
        "player_pos": [0, 0], "ai_pos": [GRID_SIZE - 1, GRID_SIZE - 1],
        "player_hp": 10, "ai_hp": 10, "stamina": 5, "turn": 1, "game_over": False,
        "messages": [], "powerup_pos": None, "powerup_turn": None,
        "blocked_tiles": [], "bomb_tile": None
    })
    update_dynamic_walls()

if "player_pos" not in st.session_state:
    reset_game()

st.title("🛡️ Knight's Arena")
col1, col2, col3 = st.columns([2.2, 1.2, 1.6])
with col1:
    if st.session_state["game_over"]:
        st.markdown(f"### {st.session_state['messages'][-1]}")
    render_grid()
    st.markdown(f"**Turn {st.session_state['turn']}** | 🧍 HP: {st.session_state['player_hp']} | 🤖 HP: {st.session_state['ai_hp']} | ⚡ Stamina: {st.session_state['stamina']}/5")
with col2:
    st.markdown("### 🎮 Move")
    st.button("⬆️", on_click=move_player, args=("Up",), use_container_width=True)
    row = st.columns(3)
    with row[0]: st.button("⬅️", on_click=move_player, args=("Left",), use_container_width=True)
    with row[1]: st.button("⬇️", on_click=move_player, args=("Down",), use_container_width=True)
    with row[2]: st.button("➡️", on_click=move_player, args=("Right",), use_container_width=True)
    st.markdown("### ⚔️ Attack")
    st.button("🖐 Light", on_click=attack, kwargs={"type": "light"}, use_container_width=True)
    st.button("🗡️ Sword", on_click=attack, kwargs={"type": "sword"}, use_container_width=True)
    if st.session_state["turn"] % 7 == 0:
        st.button("💥 Special", on_click=attack, kwargs={"type": "special"}, use_container_width=True)
    st.button("🔄 Restart", on_click=reset_game, use_container_width=True)
with col3:
    st.markdown("### 📜 Log")
    for m in reversed(st.session_state["messages"][-20:]):
        st.markdown(f"- {m}")
