import streamlit as st
import pandas as pd
import io
import base64
import numpy as np

# Function to parse uploaded CSV data
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Read the CSV file with encoding='latin1'
            df = pd.read_csv(io.StringIO(decoded.decode('latin1')))
        else:
            return None, None, None
    except Exception as e:
        return None, None, None

    # Rename the columns as needed
    df.rename(columns={
        'Where did you find our job post?': 'job_source',
        'Where are you currently located?': 'current_location',
        'What is your ideal start date for teaching?': 'ideal_startdate',
        'If you selected (Other), please specify:':'Other_source',
        'What was your major/specialization?': 'major/specialization',
        'Do you hold a passport from any of the following countries?\nUS, UK, Canada, Australia, New Zealand, Ireland or South Africa': 'native_speaker',
        'What is your age?': 'age',
        'Which subject would you like to teach?': 'expect_subject',
        'Do you have a TEFL/TESOL/CELTA?': 'Pass_engtest',
        'Text/Messaging Platform': 'contact_via',
        'Username or Phone Number for Messaging Platform (i.e. Skype ID, iMessage #, Line ID, WeChat ID)': 'ID/Phone',
        "Bachelor's Degree from College and/or University (Original Copy Required upon arrival in Thailand) **Please ONLY upload your Bachelor's degree**": "Graduated",
        "If Selected (Other...) Indicate your Passport Country of Issue.": "other_country",
        "Do you have a University/College Bachelor's degree?": "Bachelor_degree",
        'You only need to complete our application form once. Let us know other positions you are interested in.':'interested_position',
        'Completed Date':'Completed_Date',
        'What is your ideal teaching location in Thailand?':'Ideal_location',
        'pass_university_accredited.':'pass_accredited',
        'Which grade level would you like to teach?':'expected_grade',
        'Passport Country of Issue':'Passport_issue'
    }, inplace=True)

    # Create a full name column
    df['Full_Name'] = df['First Name'] + ' ' + df['Last Name']

    # Select only the necessary columns
    new_df = df[['Full_Name', 'Completed_Date', 'job_source', 'current_location', 'ideal_startdate',
                 'Ideal_location', 'expected_grade', 'expect_subject', 'Pass_engtest', 'contact_via',
                 'ID/Phone', 'Bachelor_degree', 'Graduated', 'major/specialization',
                 'pass_accredited', 'native_speaker', 'Passport_issue',
                 'other_country', 'age', 'interested_position']]

    # Calculate country counts
    country_counts = new_df['Passport_issue'].value_counts().reset_index()
    country_counts.columns = ['Passport_issue', 'Counts']

    # Define native countries
    native = ['USA', 'UK', 'Canada', 'Australia', 'New Zealand', 'Ireland', 'South Africa']
    country_counts['Native'] = country_counts['Passport_issue'].apply(lambda country: 'yes' if country in native else 'no')

    # Create a column to mark native/non-native
    new_df['Native'] = new_df['Passport_issue'].apply(lambda country: 'Native' if country in native else 'Non-Native')

    # Group by job source and native/non-native
    source = new_df.groupby(['job_source', 'Native']).size().unstack(fill_value=0).reset_index()

    # Group by job source and country
    source2 = new_df.groupby(['job_source', 'Passport_issue']).size().unstack(fill_value=0).reset_index()

    # Group by age range
    def categorize_agerange(age):
        if age < 25:
            return '<25'
        elif 25 <= age < 40:
            return '25-40'
        elif 40 <= age < 60:
            return '40-60'
        else:
            return '>60'

    new_df['age_range'] = new_df['age'].apply(categorize_agerange)
    grouped_counts = new_df.groupby(['job_source', 'age_range']).size().unstack(fill_value=0).reset_index()

    return source, source2, grouped_counts


# Streamlit App Layout
st.title("👩‍💻BFITS HR Analysis")
# Subtitle instructions for file preparation before import
st.subheader("❗Please do this every time before importing the file:")
st.markdown("""
1. **Remove the first 3 header rows**.
2. **Change the column header**:
   - 'What was your major/specialization?' to 'pass_university_accredited.'
""")
st.write("Upload a CSV file to analyze the data.")

# File uploader
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    # Read file contents and parse
    content_string = uploaded_file.getvalue().decode('latin1')
    encoded_string = base64.b64encode(content_string.encode()).decode('utf-8')
    contents = f"data:application/csv;base64,{encoded_string}"
    source, source2, grouped_counts = parse_contents(contents, uploaded_file.name)

    # Data selection dropdown
    selected_data = st.selectbox(
        "Select a table to view or export:",
        ["Job Source by Native", "Job Source by Country", "Job Source by Age"]
    )

    # Display the selected table
    if selected_data == "Job Source by Native":
        st.dataframe(source)
        df_to_export = source
        filename = "job_source_by_native.csv"
    elif selected_data == "Job Source by Country":
        st.dataframe(source2)
        df_to_export = source2
        filename = "job_source_by_country.csv"
    elif selected_data == "Job Source by Age":
        st.dataframe(grouped_counts)
        df_to_export = grouped_counts
        filename = "job_source_by_age.csv"

    # Export button
    csv = df_to_export.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Export Data",
        data=csv,
        file_name=filename,
        mime='text/csv'
    )

