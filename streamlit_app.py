import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import io
import base64
import google.generativeai as genai

# Function to parse uploaded CSV data
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('latin1')), skiprows=3)
        else:
            st.error("Unsupported file type. Please upload a CSV file.")
            return None
    except Exception as e:
        st.error(f"Error parsing file: {e}")
        return None

    # Rename columns
    df.rename(columns={
        'Where did you find our job post?': 'job_source',
        'Where are you currently located?': 'current_location',
        'What is your ideal start date for teaching?': 'ideal_startdate',
        'If you selected (Other), please specify:': 'Other_source',
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
        'You only need to complete our application form once. Let us know other positions you are interested in.': 'interested_position',
        'Completed Date': 'Completed_Date',
        'What is your ideal teaching location in Thailand?': 'Ideal_location',
        'Which grade level would you like to teach?': 'expected_grade',
        'To ensure that we can process a legal work permit for you, kindly verify that your university is accredited.\n\nUSA\nhttps://www.chea.org/  \n\nUK\nhttps://hedd.ac.uk/ \nhttps://onlinescr.co.uk/ \nhttps://www.gov.uk/government/collections/qualified-teacher-status-qts \n\nPhilippines\nhttps://ched.gov.ph/': 'pass_accredited',
        'Passport Country of Issue': 'Passport_issue'
    }, inplace=True)

    # Create a full name column
    df['Full_Name'] = df['First Name'] + ' ' + df['Last Name']

    # Select relevant columns
    new_df = df[['Full_Name', 'Completed_Date', 'job_source', 'current_location', 
                 'ideal_startdate', 'Ideal_location', 'expected_grade', 
                 'expect_subject', 'Pass_engtest', 'contact_via', 
                 'ID/Phone', 'Bachelor_degree', 'Graduated', 
                 'major/specialization', 'pass_accredited', 
                 'native_speaker', 'Passport_issue', 
                 'other_country', 'age', 
                 'interested_position']]
    
    native_speaker_countries = ['USA', 'UK', 'Canada', 'Australia', 'New Zealand', 'Ireland', 'South Africa']
    new_df['native_speaker'] = new_df['Passport_issue'].apply(lambda x: 'yes' if x in native_speaker_countries else 'no')
    new_df.reset_index(drop=True, inplace=True)
    
    return new_df
    

color_palette = ['#0143FA', '#7AFADD', '#7AC5FA', '#DC6DFA']
# Streamlit App Layout
st.sidebar.title("👩‍💻 BFITS HR Analysis")
st.sidebar.write("Upload a CSV file to analyze the data.")

# File uploader on the sidebar
uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    # Read file contents and parse
    content_string = uploaded_file.getvalue().decode('latin1')
    encoded_string = base64.b64encode(content_string.encode()).decode('utf-8')
    contents = f"data:application/csv;base64,{encoded_string}"
    new_df = parse_contents(contents, uploaded_file.name)

    if new_df is not None:

        tables = {
            'df1': new_df.groupby(['job_source', 'Passport_issue']).size().unstack(fill_value=0),
            'df2': new_df.groupby(['job_source', 'native_speaker']).size().unstack(fill_value=0),
            'age_counts': new_df[new_df['native_speaker'] == 'yes'].groupby(['job_source', pd.cut(new_df['age'], bins=[0, 25, 40, 60, 100], labels=['<25', '25-40', '40-60', '>60'])]).size().unstack(fill_value=0).reset_index()
        }

        # Data selection dropdown for tables and charts
        selected_data = st.selectbox(
            "Select a data visualization:",
            ["Job Source by Country", "Job Source by Native", "Job Source by Age"]
        )

        if selected_data == "Job Source by Country":
            st.subheader("Job Source by Country Table")
            st.dataframe(tables['df1'], use_container_width=True)
            
            # Job Source by Country Heatmap
            fig, ax = plt.subplots(figsize=(20, 12))  # Increase figure size for full scale
            sns.heatmap(
                tables['df1'],
                annot=True,
                fmt='d',
                cmap='YlGnBu',
                cbar_kws={'label': 'Counts'},
                linewidths=.5,
                ax=ax
            )
            ax.set_title('Job Sources by Passport Issue (Heatmap)', fontsize=20)
            ax.set_xlabel('Passport Issue', fontsize=16)
            ax.set_ylabel('Job Source', fontsize=16)
            st.pyplot(fig)

        elif selected_data == "Job Source by Native":
            st.subheader("Job Source by Native Table")
            st.dataframe(tables['df2'], use_container_width=True)

            # Job Source by Native Stacked Bar Chart
            fig, ax = plt.subplots(figsize=(14, 8))  # Increase figure size for full scale
            tables['df2'].plot(
                kind='bar',
                stacked=True,
                color=color_palette[:2],
                alpha=0.9,
                ax=ax
            )
            ax.set_title('Native vs Non-Native Applicants by Job Source', fontsize=20)
            ax.set_xlabel('Job Source', fontsize=16)
            ax.set_ylabel('Count', fontsize=16)
            ax.legend(title='Native', fontsize=14)
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            st.pyplot(fig)

        elif selected_data == "Job Source by Age":
            st.subheader("Job Source by Age Table")
            st.dataframe(tables['age_counts'], use_container_width=True)

            # Job Source by Age Horizontal Stacked Bar Chart
            fig, ax = plt.subplots(figsize=(16, 10))  # Increase figure size for full scale
            tables['age_counts'].set_index('job_source').plot(
                kind='barh',
                stacked=True,
                color=color_palette[:4],
                ax=ax
            )
            ax.set_title('Job Source by Age Group (Native Applicants)', fontsize=20)
            ax.set_xlabel('Count', fontsize=16)
            ax.set_ylabel('Job Source', fontsize=16)
            ax.legend(title='Age Group', fontsize=14)
            st.pyplot(fig)

else:
    st.info("Please upload a CSV file to begin.")