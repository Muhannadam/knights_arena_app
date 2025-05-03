import random
import streamlit as st
from simpleai.search import SearchProblem, astar

# Constants
GRID_SIZE = 6
ITEM_TYPES = ["❤️", "💣", "🗡️"]

# Initialize session state (safe)
if "player_pos" not in st.session_state:
    st.session_state.player_pos = [0, 0]
    st.session_state.ai_pos = [GRID_SIZE - 1, GRID_SIZE - 1]
    st.session_state.player_hp = 10
    st.session_state.ai_hp = 10
    st.session_state.turn = 1
    st.session_state.messages = []
    st.session_state.game_over = False
    st.session_state.items = {}  # ✅ prevent AttributeError

if "items" not in st.session_state:
    st.session_state.items = {}

def spawn_items():
    items = {}
    for _ in range(3):
        x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
        if [x, y] not in [st.session_state.player_pos, st.session_state.ai_pos]:
            items[(x, y)] = random.choice(ITEM_TYPES)
    return items

def is_adjacent(pos1, pos2):
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1]) == 1

def reset_game():
    st.session_state.player_pos = [0, 0]
    st.session_state.ai_pos = [GRID_SIZE - 1, GRID_SIZE - 1]
    st.session_state.player_hp = 10
    st.session_state.ai_hp = 10
    st.session_state.turn = 1
    st.session_state.messages = []
    st.session_state.game_over = False
    st.session_state.items = spawn_items()

def render_grid():
    grid = [["⬛" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    px, py = st.session_state.player_pos
    ax, ay = st.session_state.ai_pos

    for (ix, iy), icon in st.session_state.items.items():
        grid[ix][iy] = icon

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
    return html

def collect_item(pos):
    item = st.session_state.items.pop(tuple(pos), None)
    if item == "❤️":
        st.session_state.player_hp += 2
        st.session_state.messages.append("🩸 Collected Health +2")
    elif item == "💣":
        st.session_state.player_hp -= 2
        st.session_state.messages.append("💥 Stepped on Trap -2")
    elif item == "🗡️":
        st.session_state.player_hp += 1
        st.session_state.messages.append("⚔️ Power-up! +1 damage next hit")

def move_player(direction):
    x, y = st.session_state.player_pos
    if direction == "Up" and x > 0: x -= 1
    elif direction == "Down" and x < GRID_SIZE - 1: x += 1
    elif direction == "Left" and y > 0: y -= 1
    elif direction == "Right" and y < GRID_SIZE - 1: y += 1
    st.session_state.player_pos = [x, y]
    collect_item([x, y])
    st.session_state.messages.append(f"Moved {direction}")

def attack():
    if is_adjacent(st.session_state.player_pos, st.session_state.ai_pos):
        damage = 1
        if "⚔️ Power-up! +1 damage next hit" in st.session_state.messages[-1:]:
            damage += 1
        st.session_state.ai_hp -= damage
        st.session_state.messages.append(f"You attacked AI! (-{damage})")
    else:
        st.session_state.messages.append("No enemy in range.")

class AIProblem(SearchProblem):
    def actions(self, state):
        x, y = state
        return [d for d, dx, dy in [("Up",-1,0),("Down",1,0),("Left",0,-1),("Right",0,1)]
                if 0 <= x+dx < GRID_SIZE and 0 <= y+dy < GRID_SIZE]

    def result(self, state, action):
        x, y = state
        return {
            "Up": (x - 1, y), "Down": (x + 1, y),
            "Left": (x, y - 1), "Right": (x, y + 1)
        }[action]

    def is_goal(self, state):
        return is_adjacent(state, tuple(st.session_state.player_pos))

    def cost(self, s1, a, s2): return 1
    def heuristic(self, state):
        px, py = st.session_state.player_pos
        return abs(state[0] - px) + abs(state[1] - py)

def ai_turn():
    if is_adjacent(st.session_state.ai_pos, st.session_state.player_pos):
        st.session_state.player_hp -= 1
        st.session_state.messages.append("🤖 AI attacked you! (-1)")
    else:
        path = astar(AIProblem(initial_state=tuple(st.session_state.ai_pos)))
        if len(path) > 1:
            st.session_state.ai_pos = list(path[1])
        st.session_state.messages.append("🤖 AI moved.")

def check_end():
    if st.session_state.player_hp <= 0 and st.session_state.ai_hp <= 0:
        st.session_state.messages.append("⚖️ It's a draw!")
        st.session_state.game_over = True
    elif st.session_state.ai_hp <= 0:
        st.session_state.messages.append("🎉 You win!")
        st.session_state.game_over = True
    elif st.session_state.player_hp <= 0:
        st.session_state.messages.append("💀 AI wins!")
        st.session_state.game_over = True

# UI layout
st.title("🛡️ Knight's Arena – with Random Items")

st.markdown(render_grid(), unsafe_allow_html=True)
st.write(f"Turn: {st.session_state.turn} | 🧍 HP: {st.session_state.player_hp} | 🤖 HP: {st.session_state.ai_hp}")
st.write("**History:**")
for msg in reversed(st.session_state.messages[-5:]):
    st.markdown(f"- {msg}")

if not st.session_state.game_over:
    col1, col2, col3 = st.columns(3)
    with col2:
        if st.button("⬆️ Up"): move_player("Up")
    with col1:
        if st.button("⬅️ Left"): move_player("Left")
    with col3:
        if st.button("➡️ Right"): move_player("Right")
    if st.button("⬇️ Down"): move_player("Down")
    if st.button("⚔️ Attack"): attack()
    ai_turn()
    check_end()
    st.session_state.turn += 1
else:
    if st.button("🔄 Restart"):
        reset_game()
