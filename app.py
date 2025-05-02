import streamlit as st
import numpy as np
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

    # ✅ استخدم <br> للفصل بين الأسطر
    html = "<div style='font-size:32px; line-height:1.5;'>"
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
        actions = []
        if x > 0: actions.append('Up')
        if x < GRID_SIZE - 1: actions.append('Down')
        if y > 0: actions.append('Left')
        if y < GRID_SIZE - 1: actions.append('Right')
        return actions

    def result(self, state, action):
        x, y = state
        if action == 'Up': return (x - 1, y)
        if action == 'Down': return (x + 1, y)
        if action == 'Left': return (x, y - 1)
        if action == 'Right': return (x, y + 1)

    def is_goal(self, state):
        return state == self.goal

    def cost(self, state1, action, state2):
        return 1

    def heuristic(self, state):
        return abs(state[0] - self.goal[0]) + abs(state[1] - self.goal[1])

def ai_turn():
    if is_adjacent(st.session_state["ai_pos"], st.session_state["player_pos"]):
        st.session_state["player_hp"] -= 1
        st.session_state["messages"].append("🤖 AI attacked you!")
    else:
        try:
            problem = AStarMoveProblem(tuple(st.session_state["ai_pos"]), tuple(st.session_state["player_pos"]))
            result = astar(problem)
            path = result.path()
            if path and len(path) > 1:
                next_move = path[1][1]
                st.session_state["ai_pos"] = list(next_move)
                st.session_state["messages"].append(f"🤖 AI moved to {next_move} using A*.")
        except Exception as e:
            st.session_state["messages"].append(f"Error in AI move: {e}")

def move_player(direction):
    if st.session_state["game_over"]:
        return

    x, y = st.session_state["player_pos"]
    if direction == "Up" and x > 0: x -= 1
    elif direction == "Down" and x < GRID_SIZE - 1: x += 1
    elif direction == "Left" and y > 0: y -= 1
    elif direction == "Right" and y < GRID_SIZE - 1: y += 1
    st.session_state["player_pos"] = [x, y]
    st.session_state["messages"].append(f"🧍 Player moved {direction}")

    check_win()
    if not st.session_state["game_over"]:
        ai_turn()
        check_win()
    st.session_state["turn"] += 1

def attack():
    if st.session_state["game_over"]:
        return

    if is_adjacent(st.session_state["player_pos"], st.session_state["ai_pos"]):
        st.session_state["ai_hp"] -= 1
        st.session_state["messages"].append("🗡️ You attacked the AI!")
    else:
        st.session_state["messages"].append("No enemy in range.")

    check_win()
    if not st.session_state["game_over"]:
        ai_turn()
        check_win()
    st.session_state["turn"] += 1

def check_win():
    if st.session_state["ai_hp"] <= 0:
        st.session_state["messages"].append("🎉 You win!")
        st.session_state["game_over"] = True
    elif st.session_state["player_hp"] <= 0:
        st.session_state["messages"].append("💀 AI wins!")
        st.session_state["game_over"] = True

def reset_game():
    st.session_state["player_pos"] = [0, 0]
    st.session_state["ai_pos"] = [GRID_SIZE - 1, GRID_SIZE - 1]
    st.session_state["player_hp"] = 10
    st.session_state["ai_hp"] = 10
    st.session_state["messages"] = []
    st.session_state["turn"] = 1
    st.session_state["game_over"] = False

# Initialize session
if "player_pos" not in st.session_state:
    reset_game()

# UI
st.title("🛡️ Knight's Arena - Streamlit Edition")
render_grid()
st.markdown(f"**Turn:** {st.session_state['turn']} | 🧍 Player HP: {st.session_state['player_hp']} | 🤖 AI HP: {st.session_state['ai_hp']}")

col1, col2, col3 = st.columns(3)
with col2:
    st.button("⬆️ Up", on_click=move_player, args=("Up",))
col1, col2, col3 = st.columns(3)
with col1:
    st.button("⬅️ Left", on_click=move_player, args=("Left",))
with col2:
    st.button("⚔️ Attack", on_click=attack)
with col3:
    st.button("➡️ Right", on_click=move_player, args=("Right",))
col1, col2, col3 = st.columns(3)
with col2:
    st.button("⬇️ Down", on_click=move_player, args=("Down",))

st.button("🔄 Start New Game", on_click=reset_game)

st.markdown("---")
st.markdown("### 📜 Action History:")
for msg in st.session_state["messages"]:
    st.markdown(f"- {msg}")
