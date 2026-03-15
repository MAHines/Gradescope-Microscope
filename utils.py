import streamlit as st
import pandas as pd
import os

    
def shared_sidebar():
    image_path = os.path.join(os.path.dirname(__file__), 'assets', 'Hobbes_glasses.png')
    #unique_image_path = f"{image_path}?{time.time()}"
    st.sidebar.image(image_path)
    st.sidebar.write("Melissa.Hines@cornell.edu")

