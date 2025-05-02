import streamlit as st
from simpleai.search import SearchProblem, astar

GRID_SIZE = 6

def is_adjacent(pos1, pos2):
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1]) == 1

def render_grid():
    grid = [["⬛" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
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
        return [d for d in ['Up', 'Down', 'Left', 'Right']
                if 0 <= (state[0] + (d == 'Down') - (d == 'Up')) < GRID_SIZE and
                   0 <= (state[1] + (d == 'Right') - (d == 'Left')) < GRID_SIZE]
    def result(self, state, action):
        x, y = state
        return (x - 1, y) if action == 'Up' else (x + 1, y) if action == 'Down' else (x, y - 1) if action == 'Left' else (x, y + 1)
    def is_goal(self, state): return state == self.goal
    def cost(self, s1, a, s2): return 1
    def heuristic(self, state): return abs(state[0] - self.goal[0]) + abs(state[1] - self.goal[1])

def ai_turn():
    if is_adjacent(st.session_state["ai_pos"], st.session_state["player_pos"]):
        st.session_state["player_hp"] -= 1
        st.session_state["messages"].append("🤖 AI attacked you!")
    else:
        try:
            result = astar(AStarMoveProblem(tuple(st.session_state["ai_pos"]), tuple(st.session_state["player_pos"])))
            path = result.path()
            if path and len(path) > 1:
                st.session_state["ai_pos"] = list(path[1][1])
                st.session_state["messages"].append(f"🤖 AI moved to {path[1][1]} using A*.")
        except Exception as e:
            st.session_state["messages"].append(f"A* error: {e}")

def move_player(direction):
    if st.session_state["game_over"]: return
    x, y = st.session_state["player_pos"]
    if direction == "Up" and x > 0: x -= 1
    elif direction == "Down" and x < GRID_SIZE - 1: x += 1
    elif direction == "Left" and y > 0: y -= 1
    elif direction == "Right" and y < GRID_SIZE - 1: y += 1
    st.session_state["player_pos"] = [x, y]
    st.session_state["messages"].append(f"🧍 Player moved {direction}")
    check_win()
    if not st.session_state["game_over"]: ai_turn(); check_win()
    st.session_state["turn"] += 1

def attack(type="light"):
    if st.session_state["game_over"]: return
    if is_adjacent(st.session_state["player_pos"], st.session_state["ai_pos"]):
        damage = 1 if type == "light" else 2
        label = "Light Hit" if type == "light" else "Sword Attack"
        st.session_state["ai_hp"] -= damage
        st.session_state["messages"].append(f"{label}! You dealt {damage} damage.")
    else:
        st.session_state["messages"].append("No enemy in range.")
    check_win()
    if not st.session_state["game_over"]: ai_turn(); check_win()
    st.session_state["turn"] += 1

def check_win():
    if st.session_state["ai_hp"] <= 0:
        st.session_state["messages"].append("🎉 You win!")
        st.session_state["game_over"] = True
    elif st.session_state["player_hp"] <= 0:
        st.session_state["messages"].append("💀 AI wins!")
        st.session_state["game_over"] = True

def reset_game():
    st.session_state.update({
        "player_pos": [0, 0], "ai_pos": [GRID_SIZE - 1, GRID_SIZE - 1],
        "player_hp": 10, "ai_hp": 10, "messages": [],
        "turn": 1, "game_over": False
    })

if "player_pos" not in st.session_state: reset_game()

st.markdown("<h2 style='margin-bottom:0'>🛡️ Knight's Arena</h2>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([2.2, 1.2, 1.8])

with col1:
    if st.session_state["game_over"]:
        msg = "🎉 You win!" if st.session_state["ai_hp"] <= 0 else "💀 AI wins!"
        st.markdown(f"<h4>{msg}</h4>", unsafe_allow_html=True)
    render_grid()
    st.markdown(f"**Turn {st.session_state['turn']}** | 🧍 HP: {st.session_state['player_hp']} | 🤖 HP: {st.session_state['ai_hp']}")

with col2:
    st.markdown("### 🎮 Move")
    st.button("⬆️", on_click=move_player, args=("Up",), use_container_width=True)
    row = st.columns(3)
    with row[0]: st.button("⬅️", on_click=move_player, args=("Left",), use_container_width=True)
    with row[1]: st.button("⚔️ Light Hit", on_click=attack, kwargs={"type": "light"}, use_container_width=True)
    with row[2]: st.button("➡️", on_click=move_player, args=("Right",), use_container_width=True)
    st.button("⬇️", on_click=move_player, args=("Down",), use_container_width=True)
    st.button("🗡️ Sword Attack", on_click=attack, kwargs={"type": "sword"}, use_container_width=True)
    st.button("🔄 Start New Game", on_click=reset_game, use_container_width=True)

with col3:
    st.markdown("### 📜 History")
    st.markdown("<div style='max-height:450px; overflow:auto;'>", unsafe_allow_html=True)
    for msg in reversed(st.session_state["messages"][-30:]):
        st.markdown(f"- {msg}")
    st.markdown("</div>", unsafe_allow_html=True)
