import streamlit as st

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def card_container(key=None):
    """
    Creates a container that looks like a card.
    Usage:
        with card_container():
            st.write("Inside card")
    """
    # Streamlit doesn't strictly allow wrapping arbitrary content in a custom div easily 
    # while keeping python context manager syntax for standard widgets without extra plugins.
    # However, we can simulate it or just use st.container() and styling.
    # For now, we'll try to use a styled container. 
    # Since we can't easily inject a class to a st.container, we might rely on the CSS 
    # targeting specific container indices if the structure is rigid, OR we just use markdown for headers/text.
    
    # A cleaner way in pure Streamlit for visual grouping is st.container with a border (added in recent versions)
    # But for our custom "Platinum" look with shadows, we might need a workaround or just apply global styles.
    
    # Let's use st.container(border=True) as a base and override its style via CSS if possible,
    # or just use standard st.container() but insert a starting and ending HTML div for the card style.
    # But inserting HTML divs breaks the stream of Streamlit widgets if those widgets are Python objects.
    
    # BEST APPROACH for Streamlit: Use st.container(border=True) and style standard elements.
    # OR, assume the user accepts that "Cards" might just be visually distinct sections.
    
    return st.container(border=True)

def display_header(title, subtitle=None):
    st.markdown(f'<h1 class="section-header">{title}</h1>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<p class="subtitle">{subtitle}</p>', unsafe_allow_html=True)

def display_metric_card(label, value, delta=None):
    st.metric(label=label, value=value, delta=delta)

