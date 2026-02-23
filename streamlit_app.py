# -----------------------------
# Add Sale (progressive items)
# -----------------------------
st.header("Add Sale")

def sale_row(row_num: int):
    c1, c2 = st.columns([2, 3])
    with c1:
        st.number_input(
            f"Revenue ($)",
            min_value=0.0,
            step=1.0,
            key=f"rev_{row_num}",
        )
    with c2:
        st.multiselect(
            f"Category Tags",
            ["Health/Wearables", "CarFi", "Other"],
            key=f"tags_{row_num}",
        )

# Item 1
sale_row(1)

# Smaller "+" button under Item 1
st.markdown("""
<style>
div.stButton > button.small-plus {
    font-size: 14px;
    padding: 2px 8px;
    height: 28px;
    width: 40px;
}
</style>
""", unsafe_allow_html=True)

col_plus, _ = st.columns([1, 5])
with col_plus:
    if st.button("➕", key="plus_btn"):
        if st.session_state.item_count < MAX_ITEMS:
            st.session_state.item_count += 1
            st.rerun()

# Additional Items (only if added)
if st.session_state.item_count >= 2:
    sale_row(2)

if st.session_state.item_count >= 3:
    sale_row(3)

btn1, btn2 = st.columns([2, 2])

with btn1:
    if st.button("Add Sale"):
        count = add_basket()
        if count > 0:
            st.success(f"Added {count} item(s).")
            clear_inputs()
            st.rerun()
        else:
            st.warning("Enter revenue > $0")

with btn2:
    if st.button("Clear"):
        clear_inputs()
        st.rerun()
