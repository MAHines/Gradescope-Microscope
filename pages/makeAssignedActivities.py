import streamlit as st
import pandas as pd
import plotly.express as px
import utils
import ast
from datetime import datetime, timedelta, date
from streamlit import session_state as ss
from pathlib import Path

def add_holiday():
    ss.holidays.append(ss.selected_holiday)
    
def clear_holidays():  
    ss.holidays = []
      
def add_lab_holiday():
    ss.lab_holidays.append(ss.lab_holiday)
    
def clear_lab_holidays():  
    ss.lab_holidays = []
      
def add_staffMtg_holiday():
    ss.staffMtg_holidays.append(ss.staffMtg_holiday) 
    
def clear_staffMtg_holidays():  
    ss.staffMtg_holidays = []
      
def add_prelim():
    ss.prelims.append(ss.prelim_day) 
    
def clear_prelims():  
    ss.prelims = []
      
def add_final():
    ss.finals.append(ss.final_day) 
    
def clear_finals():  
    ss.finals = []
      
def convert_days(day_code):
    # Mapping of characters to desired weekday abbreviations
    mapping = {
        'M': 'Mon',
        'T': 'Tue',
        'W': 'Wed',
        'R': 'Thu',
        'F': 'Fri'
    }
    # List comprehension to convert chars, handling potential key errors
    return " ".join([mapping[day] for day in day_code if day in mapping])

def update_lecture_days():

    allowed = set('MTWRF')
    if set(ss.lecture_days_input.upper()).issubset(allowed):
        ss.weekmask = convert_days(ss.lecture_days_input.upper())
    else:
        st.error('Invalid days entered.')
        ss.weekmask = ''        
        
def calculate_lectures():
    
    dates = pd.bdate_range(start=ss.first_class_day, end=ss.last_class_day, freq='C', weekmask=ss.weekmask)
    ss.lectures_df = pd.DataFrame({'Day': dates})
    
    # Remove holidays
    for holiday in ss.holidays:
        ss.lectures_df = ss.lectures_df[~ss.lectures_df['Day'].between(pd.to_datetime(holiday[0]), pd.to_datetime(holiday[1]))]
    
    ss.lectures_df['duration_min'] = ss.class_duration
    ss.lectures_df['Activity'] = 'Lecture'

def calculate_OHs():

    dates = pd.bdate_range(start=ss.first_OH_day, end=ss.last_OH_day, freq='C', weekmask='Wed')
    ss.OHs_df = pd.DataFrame({'Day': dates})
    
    # Remove holidays
    for holiday in ss.holidays:
        ss.OHs_df = ss.OHs_df[~ss.OHs_df['Day'].between(pd.to_datetime(holiday[0]), pd.to_datetime(holiday[1]))]
    
    ss.OHs_df['duration_min'] = ss.OH_duration
    ss.OHs_df['Activity'] = 'OH'
    
def calculate_labs():

    dates = pd.bdate_range(start=ss.first_lab_day, end=ss.last_lab_day, freq='C', weekmask='Wed')
    ss.labs_df = pd.DataFrame({'Day': dates})
    
    # Remove holidays
    for holiday in ss.holidays:
        ss.labs_df = ss.labs_df[~ss.labs_df['Day'].between(pd.to_datetime(holiday[0]), pd.to_datetime(holiday[1]))]
    for holiday in ss.lab_holidays:
        ss.labs_df = ss.labs_df[~ss.labs_df['Day'].between(pd.to_datetime(holiday[0]), pd.to_datetime(holiday[1]))]
    
    ss.labs_df['duration_min'] = ss.lab_duration
    if ss.short_first_last:
        ss.labs_df.loc[ss.labs_df['Day'].idxmin(), 'duration_min'] = ss.lab_duration/2
        ss.labs_df.loc[ss.labs_df['Day'].idxmax(), 'duration_min'] = ss.lab_duration/2
    ss.labs_df['Activity'] = 'Lab'
        
def calculate_staffMtgs():

    dates = pd.bdate_range(start=ss.first_staffMtg_day, end=ss.last_staffMtg_day, freq='C', weekmask='Fri')
    ss.staffMtgs_df = pd.DataFrame({'Day': dates})
    
    # Remove holidays
    for holiday in ss.staffMtg_holidays:
        ss.staffMtgs_df = ss.staffMtgs_df[~ss.staffMtgs_df['Day'].between(pd.to_datetime(holiday[0]), pd.to_datetime(holiday[1]))]
    
    ss.staffMtgs_df['duration_min'] = ss.staffMtg_duration
    ss.staffMtgs_df['Activity'] = 'Staff Mtg'
    
def calculate_proctoring():

    ss.proctor_df = pd.DataFrame({'Day': ss.prelims})
    ss.proctor_df['Day'] = pd.to_datetime(ss.proctor_df['Day'])
    ss.proctor_df['duration_min'] = ss.prelim_duration
    ss.proctor_df['Activity'] = 'Proctor Prelim'
    if len(ss.finals) > 0:
        new_row_df = pd.DataFrame([{'Day':ss.finals[0], 'duration_min':ss.final_duration, 'Activity':'Proctor Final'}])
        new_row_df['Day'] = pd.to_datetime(new_row_df['Day'])
        ss.proctor_df = pd.concat([ss.proctor_df, new_row_df], ignore_index=True)

def combine_activities():

    df_list = [ss.lectures_df, ss.OHs_df, ss.labs_df, ss.staffMtgs_df, ss.proctor_df]
    valid_dfs = [df for df in df_list if df is not None and not df.empty]
    ss.assigned_activity_df = pd.concat(valid_dfs, ignore_index = True)

@st.cache_data
def convert_to_csv(df):
    return df.to_csv(index = False, header = True).encode('utf-8')
    
def reset_sheet_generator():
    ss.clear()
    ss.needs_reset = True
 
keys = ['first_class_day', 'last_class_day', 'class_duration',
        'first_OH_day', 'last_OH_day', 'OH_duration',
        'first_lab_day', 'last_lab_day', 'lab_duration', 'short_first_last',
        'first_staffMtg_day', 'last_staffMtg_day', 'staffMtg_duration',
        'prelim_day', 'prelim_duration', 'final_day', 'final_duration',
        'lectures_df', 'OHs_df', 'labs_df', 'staffMtgs_df', 'proctor_df', 'assigned_activity_df']

for key in keys:
    ss.setdefault(key, None)

if 'weekmask' not in ss:
    ss.weekmask = ''
if 'holidays' not in ss:
    ss.holidays = []
if 'lab_holidays' not in ss:
    ss.lab_holidays = []
if 'staffMtg_holidays' not in ss:
    ss.staffMtg_holidays = []
if 'prelims' not in ss:
    ss.prelims = []
if 'finals' not in ss:
    ss.finals = []
if 'needs_reset' not in ss:
    ss.needs_reset = False

st.title('Make Assigned Activities Sheet')

text_str = 'This module is used to make a csvt that contains all of the '
text_str += 'activities assigned to a TA and their duration (not including grading). '
text_str += 'These data are needed for the \'Combine Daily Grading Reports\' script. '
text_str += 'The actual day of the week assigned to each activity is irrelevant, because '
text_str += 'we track time on a weekly basis. '
st.write(text_str)

text_str = 'Complete each section below in order. When a section is complete, you will be presented '
text_str += 'with a bar graph representing the assigned activity for that section. If you screw up, '
text_str += 'just complete the section again. After all sections are complete, you will combine them '
text_str += 'to make the final csv.'
st.write(text_str)

text_str = 'After downloading the csv to your Downloads folder, you need to move it to the appropriate '
text_str += 'folder in your Microscope Archive. The location of your archive is set in Settings. '
text_str += 'On a Mac, the root folder of your Microscope archive is likely ~/Documents/Microscope/. '
text_str += 'Each course will be stored in subfolders whose names are derived from your Gradescope '
text_str += 'course, e.g., ~/Documents/Microscope/Chem2070/2026Spring/.'
st.write(text_str)

st.button("Reset or work on a different course.", 
        on_click=reset_sheet_generator,
        type = 'primary')

if ss.needs_reset:
    ss.needs_reset = False
    st.rerun()

st.write('#### Holidays')
text_str = 'Add all holidays before proceeding further. Holidays are entered as a range, NOT as single days. '
text_str += 'Holidays affect lectures and office hours only. '
st.write(text_str)
ss.selected_holiday = st.date_input(
                        "Select a date range",
                        key = 'holiday_input',
                        value=(date.today(), date.today() + timedelta(days=1))
)
col1, col2 = st.columns(2)
with col1:
    st.button("Add holiday", 
            on_click = add_holiday,
            type = 'primary')

with col2:
    st.button('Clear holidays',
            on_click = clear_holidays,
            type = 'primary')
st.write(f'Current holidays: {ss.holidays}')

st.write('#### Lectures')
col1, col2 = st.columns(2)
with col1:
    ss.first_class_day = st.date_input('First day of classes (e.g., 2026-01-20)',
                                        format="YYYY-MM-DD",
                                        value = None) 

    ss.class_duration = st.number_input('Duration of each lecture in min (e.g., 50)',
                                            min_value = 0,
                                            max_value = 360)
                                            
with col2:
    ss.last_class_day = st.date_input('Last day of classes (e.g., 2026-05-05)',
                                        format="YYYY-MM-DD",
                                        value = None) 

    st.text_input('Lecture days (e.g., MWF, TR, MTWRF)',
                    key = 'lecture_days_input',
                    on_change = update_lecture_days) 
       
required_fields = [ss.first_class_day, ss.class_duration, ss.last_class_day]
if len(ss.weekmask) > 1 and all(field is not None for field in required_fields):
    st.button("Calculate lecture times", 
            on_click=calculate_lectures,
            type = 'primary')
                        
if ss.lectures_df is not None:
    st.bar_chart(ss.lectures_df, x = 'Day', y = 'duration_min') 

st.write('#### Office Hours')
text_str = 'For simplicity, we assume office hours are held once a week on Wednesdays. If TAs hold '
text_str += 'multiple OHs per week, just increase their duration. Office hours are canceled for '
text_str += 'Thanksgiving and Spring Break, but not Fall and Februray Break. You can tweak the '
text_str += 'final csv if you would like to do things differently.'
st.write(text_str)
col1, col2 = st.columns(2)
with col1:
    ss.first_OH_day = st.date_input('First week of office hours (e.g., Monday 2026-02-02)',
                                     format="YYYY-MM-DD",
                                     value = None) 
    
    
    ss.OH_duration = st.number_input('Duration of office hours in min (e.g., 60)',
                                        min_value = 0,
                                        max_value = 360)
with col2:
    ss.last_OH_day = st.date_input('Last week of office hours (e.g., Friday 2026-05-08)',
                                     format="YYYY-MM-DD",
                                     value = None) 
required_fields = [ss.first_OH_day, ss.last_OH_day, ss.OH_duration]
if all(field is not None for field in required_fields):
    st.button("Calculate office hours", 
            on_click=calculate_OHs,
            type = 'primary')
                        
if ss.OHs_df is not None:
    st.bar_chart(ss.OHs_df, x = 'Day', y = 'duration_min') 

st.write('#### Labs')
text_str = 'For simplicity, we assume labs are held once a week on Wednesdays. If TAs teach '
text_str += 'multiple lab sections per week, just increase their duration (e.g., 360 min). Labs are '
text_str += 'automatically cancelled the weeks of Thanksgiving and Spring Break. You have the option '
text_str += 'of cancelling additional weeks. There is also the option of making the first and last labs '
text_str += 'half their usual duration for check-in and check-out.'
st.write(text_str)
col1, col2 = st.columns(2)
with col1:
    ss.first_lab_day = st.date_input('First week of labs (e.g., Monday 2026-01-26)',
                                     format="YYYY-MM-DD",
                                     value = None) 
    
    
    ss.lab_duration = st.number_input('Duration of labs in min (e.g., 360)',
                                        min_value = 0,
                                        max_value = 540)
with col2:
    ss.last_lab_day = st.date_input('Last week of labs (e.g., Friday 2026-05-01)',
                                     format="YYYY-MM-DD",
                                     value = None)
    
    ss.short_first_last = st.checkbox("First and last labs have half duration.")

text_str = 'If you need to cancel a week of labs, use the interface below.'
st.write(text_str)
ss.lab_holiday = st.date_input(
                        "Select a date range",
                        key = 'lab_holiday_input',
                        value=(date.today(), date.today() + timedelta(days=1))
)
col1, col2 = st.columns(2)
with col1:
    st.button("Add lab holiday", 
            on_click = add_lab_holiday,
            type = 'primary')

with col2:
    st.button('Clear lab holidays',
            on_click = clear_lab_holidays,
            type = 'primary')
st.write(f'Current lab holidays: {ss.lab_holidays}')

lab_required_fields = [ss.first_lab_day, ss.last_lab_day, ss.lab_duration, ss.short_first_last]
if all(field is not None for field in lab_required_fields):
    st.button("Calculate lab hours", 
            on_click=calculate_labs,
            type = 'primary')
                        
if ss.labs_df is not None:
    st.bar_chart(ss.labs_df, x = 'Day', y = 'duration_min') 

st.write('#### Staff Meetings')
text_str = 'For simplicity, we assume staff meetings are held once a week on Fridays. Staff meetings '
text_str += 'are not canceled for holidays. You must manually cancel them using the interface below.'
st.write(text_str)
col1, col2 = st.columns(2)
with col1:
    ss.first_staffMtg_day = st.date_input('First week of staff meetings (e.g., Friday 2026-01-23)',
                                     format="YYYY-MM-DD",
                                     value = None) 
    
    
    ss.staffMtg_duration = st.number_input('Duration of staff meetings in min (e.g., 120)',
                                        min_value = 0,
                                        max_value = 240)
with col2:
    ss.last_staffMtg_day = st.date_input('Last week of staff meetigs (e.g., Friday 2026-04-24)',
                                     format="YYYY-MM-DD",
                                     value = None)
    
text_str = 'If you need to cancel a week of staff meetings, use the interface below.'
st.write(text_str)
ss.staffMtg_holiday = st.date_input(
                        "Select a date range",
                        key = 'staffMtg_holiday_input',
                        value=(date.today(), date.today() + timedelta(days=1))
)
col1, col2 = st.columns(2)
with col1:
    st.button("Add staff meeting holiday", 
            on_click = add_staffMtg_holiday,
            type = 'primary')

with col2:
    st.button('Clear staff meeting holidays',
            on_click = clear_staffMtg_holidays,
            type = 'primary')
st.write(f'Current staff meeting holidays: {ss.staffMtg_holidays}')

required_fields = [ss.first_staffMtg_day, ss.last_staffMtg_day, ss.staffMtg_duration]
if all(field is not None for field in required_fields):
    st.button("Calculate staff meeting hours", 
            on_click=calculate_staffMtgs,
            type = 'primary')
                        
if ss.staffMtgs_df is not None:
    st.bar_chart(ss.staffMtgs_df, x = 'Day', y = 'duration_min') 

st.write('#### Exam Proctoring')
col1, col2 = st.columns(2)
with col1:
    ss.prelim_day = st.date_input('Day of Prelim (e.g., Monday 2026-01-26)',
                                     format="YYYY-MM-DD",
                                     value = None) 
    
with col2:
    ss.prelim_duration = st.number_input('Duration of prelim proctoring in min (e.g., 150)',
                                        min_value = 0,
                                        max_value = 300)

col1, col2 = st.columns(2)
with col1:
    st.button("Add Prelim", 
            on_click = add_prelim,
            type = 'primary')

with col2:
    st.button('Clear Prelims',
            on_click = clear_prelims,
            type = 'primary')
st.write(f'Current prelims: {ss.prelims}')

col1, col2 = st.columns(2)
with col1:
    ss.final_day = st.date_input('Day of Final, if any (e.g., Sunday 2026-05-10)',
                                     format="YYYY-MM-DD",
                                     value = None) 
    
with col2:
    ss.final_duration = st.number_input('Duration of final proctoring in min (e.g., 210)',
                                        min_value = 0,
                                        max_value = 420)

col1, col2 = st.columns(2)
with col1:
    st.button("Add Final", 
            on_click = add_final,
            type = 'primary')

with col2:
    st.button('Clear final',
            on_click = clear_finals,
            type = 'primary')
st.write(f'Current finals: {ss.finals}')

required_fields = [ss.prelim_day, ss.prelim_duration]
if len(ss.prelims) > 0 and all(field is not None for field in required_fields):
    st.button("Calculate proctoring hours", 
            on_click=calculate_proctoring,
            type = 'primary')
                        
if ss.proctor_df is not None:
    st.bar_chart(ss.proctor_df, x = 'Day', y = 'duration_min') 

st.write('#### Make Assigned Activities Sheet')
text_str = 'When you are ready, use the button below to combine all of the previous sections.'
st.write(text_str)
st.button("Combine All Activities", 
        on_click=combine_activities,
        type = 'primary')

if ss.assigned_activity_df is not None:
    weeklyActivity_df = ss.assigned_activity_df.resample('W-MON', on = 'Day')['duration_min'].sum().reset_index()
    weeklyActivity_df = weeklyActivity_df.rename(columns = {'Day': 'Week'})
    weeklyActivity_df['duration_hr'] = weeklyActivity_df['duration_min']/60
    st.bar_chart(weeklyActivity_df, x = 'Week', y = 'duration_hr') 
    
    text_str = 'The button below will download the csv to your Downloads folder. Move it to '
    text_str += 'the appropriate archive (e.g., ~/Documents/Microscope/Chem2070/2026Spring/).'
    st.write(text_str)
    assigned_activity_csv = convert_to_csv(ss.assigned_activity_df)
    st.download_button(label = 'Download Assigned Activity CSV',
                    data = assigned_activity_csv,
                    file_name = 'assignedActivity.csv',
                    mime = 'text/csv',
                    type = 'primary')

    
utils.shared_sidebar()