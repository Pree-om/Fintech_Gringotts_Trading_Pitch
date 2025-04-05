import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import time
from datetime import datetime, timedelta
import random
import base64
from io import BytesIO
import json

st.set_page_config(page_title="Quidditch Finance", page_icon="⚡", layout="wide")


st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@700&display=swap');
    
    .title-font {
        font-family: 'Cinzel Decorative', cursive;
        color: #D4AF37;
        text-shadow: 2px 2px 4px #000000;
    }
    
    .sidebar .sidebar-content {
        background-image: linear-gradient(#0E1A40,#2A623D);
        color: white;
    }
    
    .stProgress > div > div > div {
        background-image: linear-gradient(to right, #AE0001, #FFDB00);
    }
    
    .bludger-alert {
        animation: bludgerShake 0.5s;
        animation-iteration-count: 2;
    }
    
    .vr-container {
        border: 2px solid #D4AF37;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        background: rgba(0,0,0,0.3);
    }
    
    @keyframes bludgerShake {
        0% { transform: translate(1px, 1px) rotate(0deg); }
        20% { transform: translate(-1px, -2px) rotate(-1deg); }
        40% { transform: translate(-3px, 0px) rotate(1deg); }
        60% { transform: translate(3px, 2px) rotate(0deg); }
        80% { transform: translate(1px, -1px) rotate(1deg); }
        100% { transform: translate(-1px, 2px) rotate(-1deg); }
    }
    
    # Add this CSS to your existing style block (inside the <style> tags)
    .vr-viewport {
        border: 2px solid #D4AF37;
        border-radius: 10px;
        margin: 20px 0;
    }

    .vr-controls {
        background: rgba(0,0,0,0.5);
        padding: 15px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

HOUSES = {
    "Gryffindor": {
        "color": "#AE0001", 
        "volatility": 0.3,
        "mascot": "🦁",
        "traits": "Bravery, Nerve, Courage"
    },
    "Slytherin": {
        "color": "#2A623D", 
        "volatility": 0.4,
        "mascot": "🐍",
        "traits": "Ambition, Cunning, Resourcefulness"
    },
    "Ravenclaw": {
        "color": "#0E1A40", 
        "volatility": 0.25,
        "mascot": "🦅",
        "traits": "Intelligence, Wisdom, Creativity"
    },
    "Hufflepuff": {
        "color": "#FFDB00", 
        "volatility": 0.2,
        "mascot": "🦡",
        "traits": "Loyalty, Patience, Fair Play"
    }
}


if 'game' not in st.session_state:
    st.session_state.game = {
        'active': False,
        'scores': {house: 10 for house in HOUSES},
        'prices': {house: [100] for house in HOUSES},
        'positions': {house: (0,0) for house in HOUSES},
        'snitch': False,
        'snitch_position': (0, 0),
        'start_time': None,
        'history': [],
        'events': [],
        'vr_mode': False
    }


def generate_price(house):
    """Magical price generator with house characteristics"""
    last_price = st.session_state.game['prices'][house][-1]
    base_change = HOUSES[house]['volatility'] * random.uniform(-0.1, 0.1)
    
    # House-specific behaviors
    if house == "Slytherin" and random.random() < 0.1:
        base_change = abs(base_change)  # Slytherin sometimes manipulates the market
    elif house == "Hufflepuff":
        base_change *= 0.8  # More stable
        
    new_price = max(50, last_price * (1 + base_change))
    return round(new_price, 2)

def update_positions():
    """Update seeker positions with house tendencies"""
    for house in HOUSES:
        x, y = st.session_state.game['positions'][house]
        
        # House-specific movement patterns
        if house == "Gryffindor":
            x += random.uniform(-0.3, 0.5)  # Bold moves
            y += random.uniform(-0.3, 0.5)
        elif house == "Ravenclaw":
            x += random.uniform(-0.2, 0.2)  # Calculated moves
            y += random.uniform(-0.2, 0.2)
        else:
            x += random.uniform(-0.25, 0.25)
            y += random.uniform(-0.25, 0.25)
            
        # Keep within bounds
        x = max(-1, min(1, x))
        y = max(-1, min(1, y))
        st.session_state.game['positions'][house] = (x, y)
    
    # Update snitch position if it's active
    if st.session_state.game['snitch']:
        sx, sy = st.session_state.game['snitch_position']
        st.session_state.game['snitch_position'] = (
            max(-1.5, min(1.5, sx + random.uniform(-0.4, 0.4))),
            max(-1.5, min(1.5, sy + random.uniform(-0.4, 0.4)))
        )
    elif not st.session_state.game['snitch'] and st.session_state.game['active']:
        elapsed = datetime.now() - st.session_state.game['start_time']
        if elapsed.seconds > 120:  # Snitch appears after 2 minutes
            st.session_state.game['snitch'] = True
            st.session_state.game['snitch_position'] = (
                random.uniform(-1, 1),
                random.uniform(-1, 1))
            st.session_state.game['events'].append("✨ The Golden Snitch has appeared!")

def simulate_events():
    """Magical events during the match"""
    events = []
    
    # Bludger attacks
    if random.random() < 0.15:
        house = random.choice(list(HOUSES.keys()))
        damage = random.randint(1, 5)
        st.session_state.game['scores'][house] = max(0, st.session_state.game['scores'][house] - damage)
        events.append(f"💥 Bludger hit {HOUSES[house]['mascot']} {house}! (-{damage} points)")
    
    # Random quaffle goals
    if random.random() < 0.2:
        scorer = random.choice(list(HOUSES.keys()))
        st.session_state.game['scores'][scorer] += 10
        events.append(f"⚽ {HOUSES[scorer]['mascot']} {scorer} scored with the Quaffle! (+10 points)")
    
    # Check for snitch catch
    if st.session_state.game['snitch']:
        for house in HOUSES:
            hx, hy = st.session_state.game['positions'][house]
            sx, sy = st.session_state.game['snitch_position']
            distance = ((hx - sx)*2 + (hy - sy)*2)*0.5
            if distance < 0.2 and random.random() < 0.3:  # 30% chance to catch when close
                st.session_state.game['scores'][house] += 150
                st.session_state.game['snitch'] = False
                events.append(f"✨ {HOUSES[house]['mascot']} {house} caught the Golden Snitch! +150 points!")
                st.session_state.game['events'].extend(events)
                st.balloons()
                break
    
    return events




# ========== VR FUNCTIONS ==========
def show_vr_mode():
    """Launch VR mode in a new tab with proper WebXR handling"""
    house_data = [{
        "name": house,
        "color": HOUSES[house]['color'],
        "position": list(st.session_state.game['positions'][house])
    } for house in HOUSES]

    snitch_data = {
        "active": st.session_state.game['snitch'],
        "position": list(st.session_state.game['snitch_position']) if st.session_state.game['snitch'] else [0, 0]
    }

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Quidditch VR</title>
        <style>
            body {{ 
                margin: 0; 
                overflow: hidden; 
                background: black;
                font-family: Arial, sans-serif;
            }}
            canvas {{ display: block; }}
            #status {{
                position: absolute;
                top: 10px;
                left: 10px;
                color: white;
                background: rgba(0,0,0,0.7);
                padding: 5px 10px;
                border-radius: 5px;
                z-index: 100;
            }}
            #vr-button {{
                position: absolute;
                bottom: 20px;
                left: 20px;
                padding: 10px 20px;
                background: #D4AF37;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                cursor: pointer;
                z-index: 100;
            }}
        </style>
    </head>
    <body>
        <div id="status">Initializing VR...</div>
        <button id="vr-button" disabled>ENTER VR</button>

        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/jsm/webxr/VRButton.js"></script>

        <script>
            // Configuration
            const houseData = {json.dumps(house_data)};
            const snitchData = {json.dumps(snitch_data)};
            
            // Core variables
            let scene, camera, renderer, controls;
            let vrSession = null;
            
            // DOM elements
            const statusEl = document.getElementById('status');
            const vrButton = document.getElementById('vr-button');
            
            function init() {{
                try {{
                    // 1. Initialize scene
                    scene = new THREE.Scene();
                    camera = new THREE.PerspectiveCamera(
                        75, 
                        window.innerWidth / window.innerHeight, 
                        0.1, 
                        1000
                    );
                    
                    // 2. Set up renderer
                    renderer = new THREE.WebGLRenderer({{ antialias: true }});
                    renderer.setPixelRatio(window.devicePixelRatio);
                    renderer.setSize(window.innerWidth, window.innerHeight);
                    renderer.xr.enabled = true;
                    document.body.appendChild(renderer.domElement);
                    
                    // 3. Add lighting
                    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
                    scene.add(ambientLight);
                    
                    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
                    directionalLight.position.set(0, 10, 10);
                    scene.add(directionalLight);
                    
                    // 4. Create pitch
                    const pitch = new THREE.Mesh(
                        new THREE.PlaneGeometry(100, 70),
                        new THREE.MeshStandardMaterial({{ 
                            color: 0x2a623d,
                            roughness: 0.8 
                        }})
                    );
                    pitch.rotation.x = -Math.PI / 2;
                    scene.add(pitch);
                    
                    // 5. Add hoops
                    const hoopGeometry = new THREE.TorusGeometry(3, 0.5, 16, 32);
                    const hoopMaterial = new THREE.MeshBasicMaterial({{ color: 0xD4AF37 }});
                    [-40, 0, 40].forEach(x => {{
                        const hoop = new THREE.Mesh(hoopGeometry, hoopMaterial);
                        hoop.position.set(x, 8, -30);
                        hoop.rotation.x = Math.PI / 2;
                        scene.add(hoop);
                    }});
                    
                    // 6. Add seekers
                    houseData.forEach(house => {{
                        const geometry = new THREE.SphereGeometry(1.5, 32, 32);
                        const material = new THREE.MeshPhongMaterial({{
                            color: parseInt(house.color.substring(1), 16),
                            emissive: parseInt(house.color.substring(1), 16)
                        }});
                        const seeker = new THREE.Mesh(geometry, material);
                        seeker.position.set(
                            house.position[0] * 20, 
                            3, 
                            house.position[1] * 20
                        );
                        scene.add(seeker);
                    }});
                    
                    // 7. Add snitch if active
                    if (snitchData.active) {{
                        const geometry = new THREE.SphereGeometry(0.8, 32, 32);
                        const material = new THREE.MeshStandardMaterial({{
                            color: 0xD4AF37,
                            metalness: 0.9,
                            roughness: 0.1
                        }});
                        const snitch = new THREE.Mesh(geometry, material);
                        snitch.position.set(
                            snitchData.position[0] * 25,
                            10,
                            snitchData.position[1] * 25
                        );
                        scene.add(snitch);
                    }}
                    
                    // 8. Position camera
                    camera.position.set(0, 30, 50);
                    camera.lookAt(0, 0, 0);
                    
                    // 9. Set up controls
                    controls = new THREE.OrbitControls(camera, renderer.domElement);
                    controls.enableDamping = true;
                    controls.dampingFactor = 0.05;
                    
                    // 10. Set up VR button
                    setupVRButton();
                    
                    // 11. Start animation
                    animate();
                    
                    statusEl.textContent = "Ready! Click ENTER VR";
                    
                }} catch (error) {{
                    handleError(error);
                }}
            }}
            
            function setupVRButton() {{
                vrButton.disabled = false;
                
                vrButton.addEventListener('click', async () => {{
                    if (!navigator.xr) {{
                        statusEl.textContent = "WebXR not supported in your browser";
                        return;
                    }}
                    
                    try {{
                        if (!vrSession) {{
                            vrSession = await navigator.xr.requestSession('immersive-vr');
                            renderer.xr.setSession(vrSession);
                            
                            vrButton.textContent = "EXIT VR";
                            statusEl.textContent = "VR mode active";
                            
                            vrSession.addEventListener('end', () => {{
                                vrSession = null;
                                vrButton.textContent = "ENTER VR";
                                statusEl.textContent = "VR session ended";
                            }});
                        }} else {{
                            await vrSession.end();
                        }}
                    }} catch (error) {{
                        handleError(error);
                    }}
                }});
            }}
            
            function animate() {{
                renderer.setAnimationLoop(() => {{
                    if (!vrSession) {{
                        controls.update();
                    }}
                    renderer.render(scene, camera);
                }});
            }}
            
            function handleError(error) {{
                console.error("VR Error:", error);
                statusEl.textContent = `Error: ${{error.message}}`;
                statusEl.style.color = "#ff4444";
                vrButton.disabled = true;
            }}
            
            // Handle window resize
            window.addEventListener('resize', () => {{
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            }});
            
            // Start initialization when DOM is ready
            document.addEventListener('DOMContentLoaded', init);
        </script>
    </body>
    </html>
    """

    # Display in Streamlit
    st.markdown("## 🧙‍♂️ Immersive Quidditch VR")
    st.markdown("""
    <div style="background: rgba(0,0,0,0.1); padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <p>For the best experience:</p>
        <ol>
            <li>Use Chrome or Edge on desktop</li>
            <li>Enable WebXR in browser flags if needed</li>
            <li>VR headset recommended for full immersion</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    # Create download link that opens in new tab
    b64 = base64.b64encode(html_content.encode()).decode()
    payload_url = f"data:text/html;base64,{b64}"
    
    st.markdown(f"""
    <a href="{payload_url}" target="_blank">
        <button style='
            padding: 12px 24px;
            background: linear-gradient(#D4AF37, #F0E68C);
            color: #000;
            font-weight: bold;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            width: 100%;
        '>
            🕶️ Launch VR Experience
        </button>
    </a>
    """, unsafe_allow_html=True)


# ========== ENCHANTED VISUALIZATION ==========
def draw_pitch():
    """Magical pitch visualization"""
    df = pd.DataFrame([
        {
            "House": house, 
            "X": pos[0], 
            "Y": pos[1], 
            "Color": HOUSES[house]['color'],
            "Mascot": HOUSES[house]['mascot'],
            "Size": 30 if house == max(st.session_state.game['scores'].items(), key=lambda x: x[1])[0] else 20
        }
        for house, pos in st.session_state.game['positions'].items()
    ])
    
    # Add golden snitch if it appears
    if st.session_state.game['snitch']:
        sx, sy = st.session_state.game['snitch_position']
        snitch_df = pd.DataFrame([{
            "House": "Golden Snitch", 
            "X": sx, "Y": sy, 
            "Color": "#D4AF37",
            "Mascot": "✨",
            "Size": 15
        }])
        df = pd.concat([df, snitch_df], ignore_index=True)
    
    fig = px.scatter(
        df, x="X", y="Y", color="House", text="Mascot",
        color_discrete_map={h: HOUSES[h]['color'] for h in HOUSES},
        range_x=[-1.5,1.5], range_y=[-1.5,1.5],
        title="<b>Quidditch Pitch - Seeker Positions</b>",
        size="Size", size_max=45,
        hover_data={"House": True, "Mascot": False, "Size": False}
    )
    
    # Customize appearance
    fig.update_traces(
        marker=dict(line=dict(width=2, color='DarkSlateGrey')),
        textfont=dict(size=18),
        textposition='middle center'
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(173, 216, 230, 0.1)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        title_x=0.5,
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False, zeroline=False),
        height=500
    )
    
    # Add quidditch pitch markings
    fig.add_shape(type="circle", xref="x", yref="y",
                  x0=-1.5, y0=-1.5, x1=1.5, y1=1.5,
                  line=dict(color="#D4AF37", width=2, dash="dot"))
    
    st.plotly_chart(fig, use_container_width=True)

def draw_performance():
    """House stock performance"""
    df = pd.DataFrame(st.session_state.game['prices'])
    
    fig = px.line(
        df, 
        title="<b>House Stock Performance</b>",
        labels={"value": "Stock Value (Galleons)", "index": "Time"},
        color_discrete_map={h: HOUSES[h]['color'] for h in HOUSES}
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0.1)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        title_x=0.5,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_final_results():
    """Display comprehensive results after match"""
    st.markdown("## 🏆 Match Results")
    
    # Final scores
    final_scores = st.session_state.game['scores']
    winner = max(final_scores.items(), key=lambda x: x[1])[0]
    
    cols = st.columns(4)
    for i, (house, score) in enumerate(final_scores.items()):
        with cols[i]:
            st.metric(
                label=f"{HOUSES[house]['mascot']} {house}", 
                value=score,
                delta=f"🏆 Winner!" if house == winner else None,
                delta_color="normal" if house == winner else "off"
            )
    
    # Historical price data
    st.markdown("## 📜 Historical Stock Data")
    history_df = pd.DataFrame(st.session_state.game['prices'])
    st.dataframe(history_df.style.background_gradient(axis=0), use_container_width=True)
    
    # Performance charts
    st.markdown("## 📊 Performance Analysis")
    
    # Price change percentage
    price_changes = {
        house: ((history_df[house].iloc[-1] - history_df[house].iloc[0]) / history_df[house].iloc[0]) * 100
        for house in HOUSES
    }
    
    fig1 = px.bar(
        x=list(price_changes.keys()),
        y=list(price_changes.values()),
        color=list(price_changes.keys()),
        color_discrete_map={h: HOUSES[h]['color'] for h in HOUSES},
        title="Percentage Change in Stock Values",
        labels={"x": "House", "y": "Percentage Change"},
        text=[f"{v:.1f}%" for v in price_changes.values()]
    )
    fig1.update_traces(textposition='outside')
    fig1.update_layout(showlegend=False)
    
    # Volatility analysis
    volatilities = {
        house: history_df[house].pct_change().std() * 100
        for house in HOUSES
    }
    
    fig2 = px.bar(
        x=list(volatilities.keys()),
        y=list(volatilities.values()),
        color=list(volatilities.keys()),
        color_discrete_map={h: HOUSES[h]['color'] for h in HOUSES},
        title="Stock Volatility During Match",
        labels={"x": "House", "y": "Volatility (σ)"},
        text=[f"{v:.1f}%" for v in volatilities.values()]
    )
    fig2.update_traces(textposition='outside')
    fig2.update_layout(showlegend=False)
    
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        st.plotly_chart(fig2, use_container_width=True)
    
    # Event log
    if st.session_state.game['events']:
        st.markdown("## 📜 Match Event Log")
        for event in st.session_state.game['events']:
            st.write(f"- {event}")

# ========== STREAMLIT UI ==========
st.markdown("<h1 class='title-font'>🏆 Quidditch Finance Simulator</h1>", unsafe_allow_html=True)
st.caption("A magical fusion of wizard banking and quidditch strategy")

# Control Panel
with st.sidebar:
    st.markdown("<h2 style='color:#D4AF37'>⚡ Match Controls</h2>", unsafe_allow_html=True)
    
    if st.button("Start Match ✨", disabled=st.session_state.game['active'], 
                help="Begin the quidditch match and market simulation"):
        st.session_state.game['active'] = True
        st.session_state.game['start_time'] = datetime.now()
        st.session_state.game['events'] = []
        st.session_state.game['snitch'] = False
        st.rerun()
        
    if st.button("Stop Match 🏁", disabled=not st.session_state.game['active'],
                help="End the current match"):
        st.session_state.game['active'] = False
        st.rerun()
    
    # VR mode toggle
    st.markdown("<h2 style='color:#D4AF37'>🕶 VR Mode</h2>", unsafe_allow_html=True)
    st.session_state.game['vr_mode'] = st.toggle("Enable VR", value=False, 
                                               help="Experimental VR mode for immersive experience")
    
    st.markdown("<h2 style='color:#D4AF37'>🏰 House Information</h2>", unsafe_allow_html=True)
    for house, data in HOUSES.items():
        st.markdown(f"""
        <div style='background-color:{data["color"]}20; padding:10px; border-radius:10px; margin-bottom:10px;'>
            <h4>{data['mascot']} {house}</h4>
            <p><small>{data.get('traits', '')}</small></p>
            <p>Volatility: {data['volatility']*100:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<h2 style='color:#D4AF37'>📊 Current Scores</h2>", unsafe_allow_html=True)
    for house, score in st.session_state.game['scores'].items():
        st.metric(
            label=f"{HOUSES[house]['mascot']} {house}", 
            value=score,
            delta_color="off"
        )

# Main Game Area
tab1, tab2, tab3, tab4 = st.tabs(["🏟 Pitch View", "📈 Market Data", "🏆 Results", "🕶 VR Experience"])

with tab1:
    if st.session_state.game['active']:
        draw_pitch()
        
        # Match status
        elapsed = datetime.now() - st.session_state.game['start_time']
        remaining = max(180 - elapsed.seconds, 0)
        st.progress(min(elapsed.seconds / 180, 1.0), 
                   f"⏳ Match Time: {str(elapsed).split('.')[0]} | Snitch appears in: {max(120 - elapsed.seconds, 0)}s")
        
        # Magical events
        new_events = simulate_events()
        if new_events:
            st.session_state.game['events'].extend(new_events)
            for event in new_events:
                st.markdown(f'<div class="bludger-alert">{event}</div>', unsafe_allow_html=True)
    else:
        st.info("🚀 Press 'Start Match' to begin the magical simulation!")
        st.markdown("""
        <div style="text-align: center;">
            <h3>Welcome to Quidditch Finance!</h3>
            <p>Experience the magical world of wizard banking combined with the excitement of quidditch</p>
            <p>✨🦁🐍🦅🦡✨</p>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    if st.session_state.game['active']:
        # Update prices less frequently for performance
        if time.time() % 5 < 0.5:  # Update every ~5 seconds
            for house in HOUSES:
                st.session_state.game['prices'][house].append(generate_price(house))
                if len(st.session_state.game['prices'][house]) > 50:
                    st.session_state.game['prices'][house].pop(0)
            update_positions()
        
        draw_performance()
        
        # Current price table
        st.markdown("### Current Stock Values")
        current_prices = {
            house: st.session_state.game['prices'][house][-1]
            for house in HOUSES
        }
        st.table(pd.DataFrame.from_dict(current_prices, orient='index', columns=['Price (Galleons)'])
                .style.format("{:.2f}")
                .background_gradient(axis=0))
    else:
        st.write("📊 Market data will appear during matches")

with tab3:
    if not st.session_state.game['active'] and st.session_state.game['start_time'] is not None:
        show_final_results()
    else:
        st.info("🏁 Complete a match to see detailed results and analysis")

with tab4:
    if st.session_state.game['vr_mode']:
        show_vr_mode()
    else:
        st.info("Enable VR Mode in the sidebar to experience the magical world in 3D!")
    
    # Show VR instructions
    st.markdown("""
    <div style="background: rgba(0,0,0,0.1); padding: 15px; border-radius: 10px; margin-top: 20px;">
        <h3>VR Mode Instructions</h3>
        <ol>
            <li>Enable VR Mode in the sidebar</li>
            <li>Use a VR headset or mobile device</li>
            <li>Click "Enter VR Mode" button</li>
            <li>Look around by moving your head/device</li>
        </ol>
        <p><small>Note: This is a simulated VR experience. For full immersion, use with a WebXR-compatible browser and device.</small></p>
    </div>
    """, unsafe_allow_html=True)

# Run the match loop without threads
if st.session_state.game['active']:
    time.sleep(1)  # Prevent excessive reruns
    st.rerun()
