# app.py
# Run:
#   pip install streamlit pandas
#   streamlit run app.py

import streamlit as st
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Any
import webbrowser

st.set_page_config(page_title="COD-like Game Finder", page_icon="🎮", layout="wide")

# ----------------------------
# Data model + small curated dataset
# (You can extend this list easily)
# ----------------------------
@dataclass
class Game:
    title: str
    platforms: List[str]
    modes: List[str]  # e.g., ["MP", "BR", "COOP", "SP"]
    tags: List[str]   # descriptors used for matching
    pace: str         # "Slow", "Medium", "Fast"
    realism: str      # "Arcade", "Hybrid", "Tactical"
    tiktok: bool      # "snappy clips" vibe (just a fun label)
    price_model: str  # "F2P", "Paid", "Sub"
    crossplay: bool
    notes: str
    link: str         # trailer / store / official page

GAMES: List[Game] = [
    Game(
        title="Battlefield 2042",
        platforms=["PC", "PS5", "Xbox Series", "PS4", "Xbox One"],
        modes=["MP"],
        tags=["modern", "large-scale", "vehicles", "classes", "objective", "teamplay"],
        pace="Fast",
        realism="Hybrid",
        tiktok=True,
        price_model="Paid",
        crossplay=True,
        notes="Big maps, vehicles, squad play. More chaotic sandbox than COD.",
        link="https://www.ea.com/games/battlefield/battlefield-2042",
    ),
    Game(
        title="XDefiant",
        platforms=["PC", "PS5", "Xbox Series"],
        modes=["MP"],
        tags=["arena", "objective", "fast-ttk", "abilities", "modern", "competitive"],
        pace="Fast",
        realism="Arcade",
        tiktok=True,
        price_model="F2P",
        crossplay=True,
        notes="Arcade FPS with factions/abilities; closest 'COD-like' pacing for many players.",
        link="https://www.ubisoft.com/en-us/game/xdefiant",
    ),
    Game(
        title="Rainbow Six Siege",
        platforms=["PC", "PS5", "Xbox Series", "PS4", "Xbox One"],
        modes=["MP"],
        tags=["tactical", "abilities", "destruction", "5v5", "slow-peek", "teamplay"],
        pace="Slow",
        realism="Tactical",
        tiktok=False,
        price_model="Paid",
        crossplay=True,
        notes="Very tactical and round-based; not COD pacing, but strong gunplay/team utility.",
        link="https://www.ubisoft.com/en-us/game/rainbow-six/siege",
    ),
    Game(
        title="Apex Legends",
        platforms=["PC", "PS5", "Xbox Series", "PS4", "Xbox One", "Switch"],
        modes=["BR"],
        tags=["battle-royale", "movement", "abilities", "squad", "fast", "hero"],
        pace="Fast",
        realism="Arcade",
        tiktok=True,
        price_model="F2P",
        crossplay=True,
        notes="Fast movement BR; if you like Warzone movement/abilities style, this hits.",
        link="https://www.ea.com/games/apex-legends",
    ),
    Game(
        title="Fortnite (Zero Build)",
        platforms=["PC", "PS5", "Xbox Series", "PS4", "Xbox One", "Switch", "Mobile"],
        modes=["BR"],
        tags=["battle-royale", "zero-build", "third-person", "fast", "crossovers"],
        pace="Fast",
        realism="Arcade",
        tiktok=True,
        price_model="F2P",
        crossplay=True,
        notes="Zero Build is a strong Warzone alternative with huge playerbase and crossplay.",
        link="https://www.fortnite.com/",
    ),
    Game(
        title="Insurgency: Sandstorm",
        platforms=["PC", "PS5", "Xbox Series", "PS4", "Xbox One"],
        modes=["MP", "COOP"],
        tags=["tactical", "hardcore", "realistic", "objective", "low-hud"],
        pace="Medium",
        realism="Tactical",
        tiktok=False,
        price_model="Paid",
        crossplay=False,
        notes="More realism, lower HUD, slower than COD but still accessible.",
        link="https://www.insurgency-sandstorm.com/",
    ),
    Game(
        title="Hell Let Loose",
        platforms=["PC", "PS5", "Xbox Series"],
        modes=["MP"],
        tags=["ww2", "large-scale", "tactical", "squad", "realistic", "objective"],
        pace="Medium",
        realism="Tactical",
        tiktok=False,
        price_model="Paid",
        crossplay=True,
        notes="WW2 mil-sim leaning; comms and objectives matter a lot.",
        link="https://www.hellletloose.com/",
    ),
    Game(
        title="The Finals",
        platforms=["PC", "PS5", "Xbox Series"],
        modes=["MP"],
        tags=["arena", "destruction", "objective", "fast", "creative", "teamplay"],
        pace="Fast",
        realism="Arcade",
        tiktok=True,
        price_model="F2P",
        crossplay=True,
        notes="High destruction + objective play; very 'highlight reel' friendly.",
        link="https://www.reachthefinals.com/",
    ),
    Game(
        title="Destiny 2 (Crucible)",
        platforms=["PC", "PS5", "Xbox Series", "PS4", "Xbox One"],
        modes=["MP", "COOP"],
        tags=["arena", "abilities", "loot", "sci-fi", "fast", "builds"],
        pace="Fast",
        realism="Arcade",
        tiktok=True,
        price_model="F2P",
        crossplay=True,
        notes="Shooter feel + abilities; MP is solid if you like build-based gunfights.",
        link="https://www.destinythegame.com/",
    ),
    Game(
        title="Escape from Tarkov",
        platforms=["PC"],
        modes=["MP"],
        tags=["extraction", "hardcore", "loot", "tactical", "high-stakes"],
        pace="Slow",
        realism="Tactical",
        tiktok=False,
        price_model="Paid",
        crossplay=False,
        notes="Hardcore extraction shooter; not COD, but scratches tactical/high-stakes itch.",
        link="https://www.escapefromtarkov.com/",
    ),
]

def to_df(games: List[Game]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for g in games:
        rows.append({
            "Title": g.title,
            "Platforms": ", ".join(g.platforms),
            "Modes": ", ".join(g.modes),
            "Pace": g.pace,
            "Style": g.realism,
            "Price": g.price_model,
            "Crossplay": "Yes" if g.crossplay else "No",
            "Tags": ", ".join(g.tags),
            "Notes": g.notes,
            "Link": g.link,
        })
    return pd.DataFrame(rows)

DF = to_df(GAMES)

# ----------------------------
# Scoring (simple content-based match)
# ----------------------------
def score_game(game: Game, prefs: Dict[str, Any]) -> float:
    score = 0.0

    # Platform match
    if prefs["platform"] != "Any":
        if prefs["platform"] in game.platforms:
            score += 3.0
        else:
            score -= 2.0

    # Mode match
    wanted_modes = prefs["modes"]
    if wanted_modes:
        overlap = set(wanted_modes).intersection(set(game.modes))
        score += 2.5 * len(overlap)
        if not overlap:
            score -= 1.5

    # Pace preference
    if prefs["pace"] != "Any":
        score += 2.0 if game.pace == prefs["pace"] else -0.5

    # Realism/style preference
    if prefs["style"] != "Any":
        score += 2.0 if game.realism == prefs["style"] else -0.5

    # Price model
    if prefs["price_model"] != "Any":
        score += 1.5 if game.price_model == prefs["price_model"] else -0.3

    # Crossplay
    if prefs["crossplay_only"]:
        score += 1.0 if game.crossplay else -3.0

    # Tags / vibes
    wanted_tags = prefs["tags"]
    if wanted_tags:
        overlap = set(wanted_tags).intersection(set(game.tags))
        score += 1.2 * len(overlap)

    # "COD-like" boost heuristics
    cod_like = {"modern", "arena", "objective", "competitive", "fast-ttk", "fast"}
    score += 0.4 * len(cod_like.intersection(set(game.tags)))

    return score

# ----------------------------
# UI
# ----------------------------
st.title("🎮 COD-like Game Finder (Streamlit)")
st.caption("Pick your vibe and get ranked recommendations for games similar to Call of Duty.")

left, right = st.columns([1, 2], gap="large")

with left:
    st.subheader("Your Preferences")

    platform = st.selectbox(
        "Platform",
        ["Any", "PC", "PS5", "Xbox Series", "PS4", "Xbox One", "Switch", "Mobile"],
        index=0,
    )

    modes = st.multiselect("Modes you want", ["MP", "BR", "COOP", "SP"], default=["MP"])

    pace = st.selectbox("Pace", ["Any", "Fast", "Medium", "Slow"], index=1)

    style = st.selectbox("Style", ["Any", "Arcade", "Hybrid", "Tactical"], index=0)

    price_model = st.selectbox("Price Model", ["Any", "F2P", "Paid", "Sub"], index=0)

    crossplay_only = st.checkbox("Crossplay only", value=True)

    tag_options = sorted({t for g in GAMES for t in g.tags})
    tags = st.multiselect(
        "Extra tags (optional)",
        tag_options,
        default=["modern", "objective", "competitive"] if "modern" in tag_options else [],
    )

    top_n = st.slider("How many results?", 3, 10, 6)

    st.divider()
    st.markdown("**Tip:** Add tags like `battle-royale`, `arena`, `tactical`, `movement`, `vehicles`.")

prefs = {
    "platform": platform,
    "modes": modes,
    "pace": pace,
    "style": style,
    "price_model": price_model,
    "crossplay_only": crossplay_only,
    "tags": tags,
}

scored = []
for g in GAMES:
    scored.append((score_game(g, prefs), g))

scored.sort(key=lambda x: x[0], reverse=True)
top = scored[:top_n]

with right:
    st.subheader("Ranked Recommendations")

    if not top:
        st.info("No matches found. Try loosening filters.")
    else:
        for rank, (s, g) in enumerate(top, start=1):
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"### {rank}. {g.title}")
                    st.write(
                        f"**Platforms:** {', '.join(g.platforms)}  \n"
                        f"**Modes:** {', '.join(g.modes)}  \n"
                        f"**Pace:** {g.pace}  \n"
                        f"**Style:** {g.realism}  \n"
                        f"**Price:** {g.price_model}  \n"
                        f"**Crossplay:** {'Yes' if g.crossplay else 'No'}"
                    )
                    st.write(f"**Tags:** {', '.join(g.tags)}")
                    st.write(g.notes)

                with c2:
                    st.metric("Match score", f"{s:.1f}")
                    if st.button("Open link", key=f"open_{g.title}"):
                        # Streamlit runs on server side; this opens in server environment.
                        # Still useful for local runs.
                        webbrowser.open_new_tab(g.link)

        st.divider()
        st.subheader("Browse the full list")
        st.dataframe(DF, use_container_width=True, hide_index=True)

st.divider()
with st.expander("How to customize the game list"):
    st.markdown(
        """
- Add games by appending a new `Game(...)` object in the `GAMES` list.
- Make matching smarter by editing `score_game()` (e.g., weight BR higher if you like Warzone).
- If you want, I can swap the hardcoded list for:
  - a CSV you maintain, or
  - an API-based database (IGDB/RAWG), so it auto-updates.
"""
    )
