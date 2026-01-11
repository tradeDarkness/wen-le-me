import streamlit as st
import os
import time
import random
from utils import ContentEngine, StateManager

# Page Config
st.set_page_config(
    page_title="问了吗? (Wen Le Me)",
    page_icon="🐱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize Logic
if "engine" not in st.session_state:
    st.session_state.engine = ContentEngine()

# Load User Data
if "user_data" not in st.session_state:
    st.session_state.user_data = StateManager.load_data()
    if "pet_emoji" not in st.session_state.user_data:
        st.session_state.user_data["pet_emoji"] = "🐱"

data = st.session_state.user_data

# --- SIDEBAR (HISTORY TIMELINE) ---
with st.sidebar:
    st.title("⏳ 提问时光机")
    st.caption("Review your curiosity journey")
    
    if not data["history"]:
        st.info("还没有提问记录。")
    
    for item in data["history"]:
        score_color = "#6366f1" if item['score'] > 80 else "#888"
        
        st.markdown(f"""
        <div class="timeline-item" style="border-left-color: {score_color}">
            <div class="timeline-date">{item['time']}</div>
            <div style="font-weight: 500; margin-bottom: 5px;">{item['question']}</div>
            <div style="font-size: 0.8em; color: {score_color}">
                {item['score']} pts <span style="color:#666">•</span> {item['comment']}
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- MAIN LAYOUT ---
# Left: 2 (Pet/Input), Right: 1 (Examples)
main_col, ex_col = st.columns([2, 1])

with main_col:
    st.title("问了吗?")
    st.caption("好奇心是活着的证明")

    # Layout: Left = Pet Avatar, Right = Stats + Input Form
    col_pet, col_interaction = st.columns([1, 2.5])
    
    with col_pet:
        st.markdown('<div class="pet-container">', unsafe_allow_html=True)
        # Display current emoji - Static as requested
        st.markdown(f'<div class="pet-emoji">{data["pet_emoji"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_interaction:
        # 1. Stats Row
        health = data["pet_health"]
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:5px;">
            <div>
                <span style="font-size: 0.9em; color:#666;">Curiosity Health</span>
                <div style="font-size: 2.5em; font-weight:800; line-height:1; color: #111;">{health}%</div>
            </div>
            <div style="text-align:right; font-size:0.9em; color:#888;">
                {data['questions_today']}/10 Questions
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(health / 100)
        
        # 2. Input Form
        st.write("") # Spacer

        with st.form("question_form", clear_on_submit=True):
            question = st.text_input("向 AI 提问", placeholder="为什么猫会发出呼噜声?...", key="q_input", label_visibility="collapsed")
            submitted = st.form_submit_button("喂食 (Feed)")

            if submitted and question:
                with st.spinner("AI 正在品鉴..."):
                    rating = st.session_state.engine.rate_question(question)
                    st.session_state.user_data = StateManager.add_question(data, question, rating)
                    
                    # Show Result - LIGHT MODE Style
                    score = rating['score']
                    score_color = "#6366f1" if score > 80 else "#111"
                    
                    st.markdown(f"""
                    <div style="background:#f8f9fa; border-radius:12px; padding:20px; text-align:left; margin-top:20px; border:1px solid #eee; box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
                        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #eee; padding-bottom:10px; margin-bottom:10px;">
                            <div style="color:#666; font-size:0.9rem;">AI 评价</div>
                            <div style="font-size:1.5rem; font-weight:800; color:{score_color}">{score} pts</div>
                        </div>
                        <div style="font-style:italic; color:#666; margin-bottom:15px;">"{rating['comment']}"</div>
                        <div style="font-size:1rem; line-height:1.6; color:#333;">
                            <strong>AI 回答：</strong><br>
                            {rating.get('answer', '')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # No auto-rerun immediately so user can read the answer. 
                    # State is saved, so sidebar will update on next interaction.

with ex_col:
    st.markdown("### 💡 灵感 (Inspiration)")
    st.caption("点击问题自动填入：")
    
    # Large pool of examples for randomization
    all_examples = [
        "如果时间静止了，光还会移动吗？",
        "为什么我们可以想象不存在的颜色？",
        "梦境里的逻辑是自洽的吗？",
        "数学是发明的还是发现的？",
        "如果你把自己复制一份，那是你吗？",
        "为什么热水比冷水结冰快？",
        "镜子里的你和真实的你是一样的吗？",
        "为什么宇宙是黑色的？",
        "既视感（Déjà vu）是怎么产生的？",
        "如果没有语言，我们还能思考吗？",
        "为什么星期一感觉比星期五更长？",
        "意识可以被上传到电脑吗？",
        "为什么我们喜欢听悲伤的音乐？",
        "如果全人类同时跳跃，地球会震动吗？",
        "我们看到的是同一个红色吗？"
    ]
    
    # Initialize random examples in session state ONLY ONCE (to avoid jitter on input typing)
    if "random_examples" not in st.session_state:
        st.session_state.random_examples = random.sample(all_examples, 5)
        
    current_examples = st.session_state.random_examples

    # Function to update input safely
    def fill_input(text):
        st.session_state.q_input = text

    st.markdown('<div class="example-btn-row">', unsafe_allow_html=True)
    for ex in current_examples:
        st.button(ex, key=ex, use_container_width=True, on_click=fill_input, args=(ex,))
    
    # Shuffle button
    if st.button("🎲 换一批", type="secondary"):
        del st.session_state.random_examples
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)
