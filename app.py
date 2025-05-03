import streamlit as st
from simpleai.search import SearchProblem, astar

GRID_SIZE = 6
PLAYER_ICON = "🧍"
AI_ICON = "🤖"

# Initialize session state
if "player_pos" not in st.session_state:
    st.session_state.player_pos = [0, 0]
    st.session_state.ai_pos = [GRID_SIZE - 1, GRID_SIZE - 1]
    st.session_state.player_hp = 3
    st.session_state.ai_hp = 3
    st.session_state.turn = 1
    st.session_state.log = []
    st.session_state.game_over = False
    st.session_state.attacks_left = 3
    st.session_state.shrink_zone = GRID_SIZE

def is_adjacent(p1, p2):
    return abs(p1[0]-p2[0]) + abs(p1[1]-p2[1]) == 1

def render_grid():
    grid = ""
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if i >= st.session_state.shrink_zone or j >= st.session_state.shrink_zone:
                grid += "  "  # out of zone
            elif [i, j] == st.session_state.player_pos:
                grid += PLAYER_ICON
            elif [i, j] == st.session_state.ai_pos:
                grid += AI_ICON
            else:
                grid += "⬛"
        grid += "\n"
    return grid

def move_player(dx, dy):
    if st.session_state.game_over:
        return
    x, y = st.session_state.player_pos
    nx, ny = max(0, min(st.session_state.shrink_zone-1, x+dx)), max(0, min(st.session_state.shrink_zone-1, y+dy))
    st.session_state.player_pos = [nx, ny]
    st.session_state.log.insert(0, f"🧍 moved to ({nx},{ny})")
    process_turn()

def attack():
    if st.session_state.game_over or st.session_state.attacks_left <= 0:
        st.session_state.log.insert(0, "❌ No attacks left!")
        return
    if is_adjacent(st.session_state.player_pos, st.session_state.ai_pos):
        st.session_state.ai_hp -= 1
        st.session_state.log.insert(0, "🧍 attacked 🤖! (-1)")
    else:
        st.session_state.log.insert(0, "🧍 missed attack!")
    st.session_state.attacks_left -= 1
    process_turn()

class AIPath(SearchProblem):
    def actions(self, state):
        x, y = state
        return [d for d, dx, dy in [("Up",-1,0),("Down",1,0),("Left",0,-1),("Right",0,1)]
                if 0 <= x+dx < st.session_state.shrink_zone and 0 <= y+dy < st.session_state.shrink_zone]

    def result(self, state, action):
        x, y = state
        return {"Up":(x-1,y), "Down":(x+1,y), "Left":(x,y-1), "Right":(x,y+1)}[action]

    def is_goal(self, state):
        return is_adjacent(state, tuple(st.session_state.player_pos))

    def cost(self, s1, a, s2): return 1
    def heuristic(self, state):
        px, py = st.session_state.player_pos
        return abs(state[0]-px) + abs(state[1]-py)

def ai_turn():
    if is_adjacent(st.session_state.ai_pos, st.session_state.player_pos):
        st.session_state.player_hp -= 1
        st.session_state.log.insert(0, "🤖 attacked 🧍! (-1)")
    else:
        try:
            path = astar(AIPath(initial_state=tuple(st.session_state.ai_pos)))
            if len(path) > 2:
                st.session_state.ai_pos = list(path[2])
            elif len(path) > 1:
                st.session_state.ai_pos = list(path[1])
            st.session_state.log.insert(0, "🤖 moved.")
        except:
            st.session_state.log.insert(0, "🤖 stuck and skipped move.")

def check_zone():
    x, y = st.session_state.player_pos
    ax, ay = st.session_state.ai_pos
    if x >= st.session_state.shrink_zone or y >= st.session_state.shrink_zone:
        st.session_state.player_hp -= 1
        st.session_state.log.insert(0, "🧍 took damage outside zone!")
    if ax >= st.session_state.shrink_zone or ay >= st.session_state.shrink_zone:
        st.session_state.ai_hp -= 1
        st.session_state.log.insert(0, "🤖 took damage outside zone!")

def process_turn():
    ai_turn()
    check_zone()
    if st.session_state.turn % 5 == 0 and st.session_state.shrink_zone > 3:
        st.session_state.shrink_zone -= 1
        st.session_state.log.insert(0, f"⚠️ Zone shrunk to {st.session_state.shrink_zone}x{st.session_state.shrink_zone}")
    if st.session_state.turn % 3 == 0:
        st.session_state.attacks_left = 3
        st.session_state.log.insert(0, "🧍 attack reset!")
    check_end()
    st.session_state.turn += 1

def check_end():
    if st.session_state.player_hp <= 0 and st.session_state.ai_hp <= 0:
        st.session_state.game_over = True
        st.session_state.log.insert(0, "⚖️ It's a draw!")
    elif st.session_state.player_hp <= 0:
        st.session_state.game_over = True
        st.session_state.log.insert(0, "💀 You lost!")
    elif st.session_state.ai_hp <= 0:
        st.session_state.game_over = True
        st.session_state.log.insert(0, "🎉 You win!")

def restart():
    for k in list(st.session_state.keys()):
        del st.session_state[k]

# -------------------- UI --------------------
st.title("⚔️ Knight's Arena – Challenge Mode")
st.markdown(render_grid(), unsafe_allow_html=True)
st.markdown(f"**Turn:** {st.session_state.turn} | 🧍 HP: {st.session_state.player_hp} | 🤖 HP: {st.session_state.ai_hp} | 🗡️ Attacks Left: {st.session_state.attacks_left}")

# Buttons
col1, col2, col3 = st.columns(3)
with col2: st.button("⬆️", on_click=move_player, args=[-1, 0])
with col1: st.button("⬅️", on_click=move_player, args=[0, -1])
with col3: st.button("➡️", on_click=move_player, args=[0, 1])
st.button("⬇️", on_click=move_player, args=[1, 0])
st.button("⚔️ Attack", on_click=attack)
st.button("🔁 Restart", on_click=restart)

st.subheader("📝 History")
for e in st.session_state.log[:10]:
    st.write("•", e)
