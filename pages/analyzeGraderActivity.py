import streamlit as st
import pandas as pd
import numpy as np
import utils
from datetime import datetime
from streamlit import session_state as ss

# After analyzing the statistics under different assumptions, I assume that graders,
#   on average, spend 4 min reading before they make their first entry in GS. It appears this
#   is actually too large for most graders.
MIN_BEFORE_FIRST_ENTRY = 4.0

def handle_graderActivity_upload_change():
    """Callback function to update session state when canvas file is uploaded."""
    if st.session_state['graderActivity_uploader_key'] is not None:
        grader_df = pd.read_csv(st.session_state['graderActivity_uploader_key']
                                 )
        grader_df.rename(columns={'Graded time': 'Time'}, inplace=True)
        current_year = datetime.now().year - 1
        time_part = grader_df['Time'].str.extract(r'^(.*?)\s*\(')[0].str.strip()
        full_datetime_str = str(current_year) + ' ' + time_part.str.replace(" at ", " ")
        grader_df['Time'] = full_datetime_str
        grader_df['Time'] = pd.to_datetime(full_datetime_str, format='%Y %b %d %I:%M%p')
        grader_df.rename(columns={'Last graded by': 'Grader'}, inplace=True)
        
        grader_df = grader_df.sort_values(by=['Grader', 'Time'])

        # Get list of unique graders
        ss.graders = grader_df['Grader'].unique().tolist()

        ss['grader_df'] = grader_df
    
def handle_grader_change():
    selected_grader = ss.selected_grader
    analyze_grader(selected_grader)

def analyze_grader(grader):
    ss.grader_df['start'] = ss.grader_df['Time'] - pd.Timedelta(minutes = MIN_BEFORE_FIRST_ENTRY)
    ss.grader_df['end'] = ss.grader_df['Time']

    one_grader_df = ss.grader_df[ss.grader_df['Grader'] == grader].copy()
    
    one_grader_df['max_end'] = one_grader_df['end'].cummax().shift().fillna(one_grader_df['start'].min())
    one_grader_df['new_group'] = one_grader_df['start'] > one_grader_df['max_end']
    one_grader_df['group_id'] = one_grader_df['new_group'].cumsum()
    
    merged_df = one_grader_df.groupby('group_id').agg(
        merged_start=('start', 'min'),
        merged_end=('end', 'max')
    )
    
    # Calculate duration and sum
    merged_df['duration'] = merged_df['merged_end'] - merged_df['merged_start']
    merged_df['break'] = merged_df['merged_end'].diff() - merged_df['duration']
    total_time = merged_df['duration'].sum().total_seconds()/3600
    numStudents =  one_grader_df['Student\'s name'].nunique()
    
    cols_to_drop = ['start', 'end', 'max_end', 'new_group', 'group_id']
    one_grader_df = one_grader_df.drop(columns = cols_to_drop)
    
    ss.one_grader_df = one_grader_df
    ss.merged_df = merged_df
    
    return total_time, numStudents

def calculate_statistics():
    output_df = pd.DataFrame(ss.graders, columns=['Grader'])
    
    output_df['numGraded'] = np.nan
    output_df['Time grading (hr)'] = np.nan
    output_df['Time/student (min)'] = np.nan    

    for grader in ss.graders:
        total_time, numStudents = analyze_grader(grader)
        output_df.loc[output_df['Grader'] == grader, 'numGraded'] = numStudents
        output_df.loc[output_df['Grader'] == grader, 'Time grading (hr)'] = round(total_time, 2)
        output_df.loc[output_df['Grader'] == grader, 'Time/student (min)'] = round(60 * total_time/numStudents, 1)

    ss.output_df = output_df

def reset_uploader():
    """Function to clear the uploaded files and show the uploader again."""
    ss['grader_df'] = None

if 'grader_df' not in st.session_state:
    ss['grader_df'] = None
if 'output_df' not in ss:
    ss.output_df = pd.DataFrame()
if 'one_grader_df' not in ss:
    ss.one_grader_df = pd.DataFrame()
if 'merged_df' not in ss:
    ss.merged_df = pd.DataFrame()

st.title('Analyze Grader Activity')

st.button("Reset or work on a different course.", 
            on_click=reset_uploader,
            type = 'primary')

if st.session_state['grader_df'] is None:
    # Display the uploader only if no file has been uploaded yet
    st.file_uploader(
        "Upload Grader Activity csv here:",
        type=['csv'],
        accept_multiple_files=False,
        key = 'graderActivity_uploader_key',
        on_change = handle_graderActivity_upload_change
    )
else:
    st.write('#### :gray[Grader activity already uploaded.]')    
    
    if st.button("Calculate statistics", type = 'primary'):
        calculate_statistics()               
    
    st.dataframe(ss.output_df)
    if len(ss.output_df) > 1:
        median_hrs = ss.output_df['Time grading (hr)'].median()
        median_min = ss.output_df['Time/student (min)'].median()
        st.write(f"Median grading time was {median_hrs} hrs or {median_min} min/student.")

    st.selectbox(
        'Select a grader', # Label for the dropdown
        options = ss.graders, # The options to display
        index = None,
        key = 'selected_grader',                # Always start at none selected
        on_change = handle_grader_change
    )

    if ss.selected_grader is not None:
        st.write('### All grader activity')
        st.dataframe(ss.one_grader_df)
        
        st.write('### All grader grading sessions')    
        st.dataframe(ss.merged_df)

utils.shared_sidebar()
