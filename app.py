import streamlit as st
import random
from simpleai.search import SearchProblem, astar

GRID_SIZE = 6
ITEM_TYPES = ["❤️", "💣", "🗡️"]

# Initialize game state
if "player_pos" not in st.session_state:
    st.session_state.player_pos = [0, 0]
    st.session_state.ai_pos = [GRID_SIZE - 1, GRID_SIZE - 1]
    st.session_state.player_hp = 10
    st.session_state.ai_hp = 10
    st.session_state.turn = 1
    st.session_state.messages = []
    st.session_state.game_over = False
    st.session_state.items = {}

# Ensure items is always defined
if "items" not in st.session_state or not isinstance(st.session_state.items, dict):
    st.session_state.items = {}

def spawn_items():
    items = {}
    for _ in range(3):
        x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
        if [x, y] not in [st.session_state.player_pos, st.session_state.ai_pos]:
            items[(x, y)] = random.choice(ITEM_TYPES)
    return items

def reset_game():
    st.session_state.player_pos = [0, 0]
    st.session_state.ai_pos = [GRID_SIZE - 1, GRID_SIZE - 1]
    st.session_state.player_hp = 10
    st.session_state.ai_hp = 10
    st.session_state.turn = 1
    st.session_state.messages = []
    st.session_state.game_over = False
    st.session_state.items = spawn_items()

def is_adjacent(p1, p2):
    return abs(p1[0]-p2[0]) + abs(p1[1]-p2[1]) == 1

def render_grid():
    # Safe check for items
    if "items" not in st.session_state or not isinstance(st.session_state.items, dict):
        st.session_state.items = {}
    grid = [["⬛" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    for (ix, iy), icon in st.session_state.items.items():
        grid[ix][iy] = icon
    px, py = st.session_state.player_pos
    ax, ay = st.session_state.ai_pos
    grid[px][py] = "🧍"
    grid[ax][ay] = "🤖" if not is_adjacent((px, py), (ax, ay)) else "🔥"
    return "<div style='font-size:28px'>" + "<br>".join(" ".join(row) for row in grid) + "</div>"

def collect_item(pos):
    item = st.session_state.items.pop(tuple(pos), None)
    if item == "❤️":
        st.session_state.player_hp += 2
        st.session_state.messages.append("Collected ❤️ +2 HP")
    elif item == "💣":
        st.session_state.player_hp -= 2
        st.session_state.messages.append("Hit 💣 -2 HP")
    elif item == "🗡️":
        st.session_state.player_hp += 1
        st.session_state.messages.append("Picked up 🗡️ +1 attack")

def move_player(direction):
    x, y = st.session_state.player_pos
    if direction == "Up" and x > 0: x -= 1
    elif direction == "Down" and x < GRID_SIZE - 1: x += 1
    elif direction == "Left" and y > 0: y -= 1
    elif direction == "Right" and y < GRID_SIZE - 1: y += 1
    st.session_state.player_pos = [x, y]
    collect_item([x, y])
    st.session_state.messages.append(f"You moved {direction}")

def attack():
    if is_adjacent(st.session_state.player_pos, st.session_state.ai_pos):
        dmg = 1
        if "Picked up 🗡️ +1 attack" in st.session_state.messages[-1:]: dmg += 1
        st.session_state.ai_hp -= dmg
        st.session_state.messages.append(f"You attacked AI! (-{dmg})")
    else:
        st.session_state.messages.append("AI not in range.")

class AIPath(SearchProblem):
    def actions(self, state):
        x, y = state
        return [d for d, dx, dy in [("Up",-1,0),("Down",1,0),("Left",0,-1),("Right",0,1)]
                if 0 <= x+dx < GRID_SIZE and 0 <= y+dy < GRID_SIZE]

    def result(self, state, action):
        x, y = state
        return {"Up":(x-1,y), "Down":(x+1,y), "Left":(x,y-1), "Right":(x,y+1)}[action]

    def is_goal(self, state):
        return is_adjacent(state, tuple(st.session_state.player_pos))

    def cost(self, s1, a, s2): return 1
    def heuristic(self, state):
        px, py = st.session_state.player_pos
        return abs(state[0] - px) + abs(state[1] - py)

def ai_turn():
    if is_adjacent(st.session_state.ai_pos, st.session_state.player_pos):
        st.session_state.player_hp -= 1
        st.session_state.messages.append("AI attacked you! (-1)")
    else:
        path = astar(AIPath(tuple(st.session_state.ai_pos)))
        if len(path) > 1:
            st.session_state.ai_pos = list(path[1])
            st.session_state.messages.append("AI moved.")

def check_end():
    if st.session_state.player_hp <= 0 and st.session_state.ai_hp <= 0:
        st.session_state.messages.append("🤝 It's a draw!")
        st.session_state.game_over = True
    elif st.session_state.ai_hp <= 0:
        st.session_state.messages.append("🏆 You win!")
        st.session_state.game_over = True
    elif st.session_state.player_hp <= 0:
        st.session_state.messages.append("💀 You lost!")
        st.session_state.game_over = True

# UI
st.title("🛡️ Knight's Arena – with Random Items")
st.markdown(render_grid(), unsafe_allow_html=True)
st.write(f"Turn {st.session_state.turn} | 🧍 HP: {st.session_state.player_hp} | 🤖 HP: {st.session_state.ai_hp}")
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
