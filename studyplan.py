from flask import Flask, request, jsonify
from flask_cors import CORS
import spacy
import pandas as pd
import google.generativeai as genai
import re

app = Flask(__name__)
CORS(app)

# Load Spacy model
nlp = spacy.load("en_core_web_sm")

def format_text(text):
    # Regex pattern to match bullet points and sub-bullet points
    bullet_pattern = re.compile(r'(\s*-\s|\s*\*\s|\d+\.\s)')
    
    # Split text into lines
    lines = text.split('- ')
    
    formatted_lines = []
    for line in lines:
        # Further split by sub-bullet points and numbers
        sub_lines = re.split(r'(\s*\*\s|\d+\.\s)', line)
        sub_lines = [s for s in sub_lines if s]  # Remove empty strings
        
        # Add hyphen for main bullets and proper indentation for sub-bullets
        for i, sub_line in enumerate(sub_lines):
            if re.match(r'(\s*\*\s|\d+\.\s)', sub_line):
                formatted_lines[-1] += sub_line.strip()  # Append to the previous line
            else:
                formatted_lines.append('- ' + sub_line.strip())
    
    return "\n".join(formatted_lines)

def generate_study_recommendations(student_id, study_preferences, topics=None):
    # Configure Generative AI API
    api_key = "AIzaSyCnkGOxJyoE4pXQBfC4ihowmYP-1ZWzEZg"  # Replace with your actual API key
    genai.configure(api_key=api_key)
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )
    chat_session = model.start_chat(history=[])
    
    # Generate recommendations
    recommendations = {}
    timetable = generate_timetable(study_preferences, topics)
    
    for subject, subject_topics in topics.items():
        response = chat_session.send_message(
            f"I want to study {subject} next. Topics: {', '.join(subject_topics)}. Here are my study preferences: {study_preferences}"
        )
        formatted_response = format_text(response.text.strip().replace("**", ""))  # Format the recommendations using format_text
        recommendations[subject] = formatted_response
    
    return recommendations, timetable

def generate_timetable(study_preferences, topics):
    # Extract preferred times
    preferred_times = study_preferences.get('Preferred time of study', '').split(',')
    time_blocks = [
        "8:00 AM - 9:00 AM", "9:00 AM - 10:00 AM", "10:00 AM - 11:00 AM", "11:00 AM - 12:00 PM",
        "1:00 PM - 2:00 PM", "2:00 PM - 3:00 PM", "3:00 PM - 4:00 PM", "4:00 PM - 5:00 PM",
        "6:00 PM - 7:00 PM", "7:00 PM - 8:00 PM"
    ]
    
    # Initialize timetable data
    timetable_data = {"Time": [], "Subject": [], "Topic": [], "Pomodoro Session": []}
    pomodoro_sessions = "4 Pomodoro sessions: 25 minutes study, 5 minutes break"
    block_index = 0

    # Fill timetable with subjects and topics
    for time in preferred_times:
        for subject, subject_topics in topics.items():
            if block_index >= len(time_blocks):
                break
            for topic in subject_topics:
                if block_index >= len(time_blocks):
                    break
                timetable_data["Time"].append(time_blocks[block_index])
                timetable_data["Subject"].append(subject)
                timetable_data["Topic"].append(topic)
                timetable_data["Pomodoro Session"].append(pomodoro_sessions)
                block_index += 1

    # Convert timetable data to DataFrame
    timetable_df = pd.DataFrame(timetable_data)
    return timetable_df

@app.route('/generate_recommendations', methods=['POST'])
def generate_recommendations():
    data = request.json
    student_id = data.get('student_id')
    study_preferences = data.get('study_preferences', {})
    topics = data.get('topics', {})
    
    study_recommendations, timetable = generate_study_recommendations(student_id, study_preferences, topics)
    
    # Convert recommendations to list format
    recommendations_list = [{subject: recommendation.split('\n')} for subject, recommendation in study_recommendations.items()]
    
    response = {
        "study_recommendations": recommendations_list,
        "timetable": timetable.to_dict(orient='records')
    }
    
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, port=5002)
