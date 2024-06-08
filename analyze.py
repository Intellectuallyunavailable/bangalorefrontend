from flask import Flask, jsonify
from flask_cors import CORS
import psycopg2
import numpy as np
import pandas as pd

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# PostgreSQL database credentials
db_credentials = {
    'dbname': 'bang_lore',
    'user': 'bang_lore_user',
    'password': 'GB9o29yszCItLrOGGBj5WgauI3E4ckfu',
    'host': 'dpg-cpest0v79t8c73bdet8g-a.singapore-postgres.render.com',
    'port': '5432'
}

# Function to execute SQL queries
def execute_query(query):
    conn = psycopg2.connect(**db_credentials)
    cur = conn.cursor()
    cur.execute(query)
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result

# API endpoint to fetch tables in the database
@app.route('/tables', methods=['GET'])
def get_tables():
    query = "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    tables = execute_query(query)
    return jsonify(tables)

# API endpoint to fetch unique student IDs for a specific table
@app.route('/student_ids/<table_name>', methods=['GET'])
def get_student_ids(table_name):
    query = f"SELECT DISTINCT student_id FROM {table_name}"
    student_ids = execute_query(query)
    return jsonify(student_ids)

# API endpoint to fetch unique subjects for a specific student ID
@app.route('/subjects/<table_name>/<student_id>', methods=['GET'])
def get_subjects(table_name, student_id):
    query = f"SELECT DISTINCT subject FROM {table_name} WHERE student_id='{student_id}'"
    subjects = execute_query(query)
    return jsonify(subjects)

# API endpoint to fetch all test data for a specific student and subject, including marks and attendance
@app.route('/test_data/<table_name>/<student_id>/<subject>', methods=['GET'])
def get_test_data(table_name, student_id, subject):
    query = f"SELECT test_no, marks, study_hours, attendance FROM {table_name} WHERE student_id='{student_id}' AND subject='{subject}'"
    test_data = execute_query(query)
    return jsonify(test_data)

# API endpoint to analyze test data for a specific student and subject
@app.route('/analyze/<table_name>/<student_id>/<subject>', methods=['GET'])
def analyze_student_performance(table_name, student_id, subject):
    query = f"SELECT test_no, marks, study_hours, attendance FROM {table_name} WHERE student_id='{student_id}' AND subject='{subject}'"
    test_data = execute_query(query)
    
    if not test_data:
        return jsonify({"error": "No data found for the specified student and subject."}), 404
    
    # Convert test data to a DataFrame
    columns = ['test_no', 'marks', 'study_hours', 'attendance']
    df = pd.DataFrame(test_data, columns=columns)
    
    # Remove '%' symbol from attendance column and convert to numeric
    df['attendance'] = df['attendance'].str.replace('%', '').astype(float)
    
    # Convert other columns to numeric types
    df['marks'] = pd.to_numeric(df['marks'])
    df['study_hours'] = pd.to_numeric(df['study_hours'])
    
    # Calculate consistency
    marks_consistency = round(df['marks'].std(), 2)
    study_hours_consistency = round(df['study_hours'].std(), 2)
    
    # Performance trend
    trend = np.polyfit(df['test_no'], df['marks'], 1)
    performance_trend = 'Improving' if trend[0] > 0 else 'Declining'
    
    # Study efficiency
    study_efficiency = round(np.corrcoef(df['study_hours'], df['marks'])[0, 1], 2)
    
    # Attendance impact
    attendance_impact = round(np.corrcoef(df['attendance'], df['marks'])[0, 1], 2)
    
    # Improvement rate
    improvement_rate = round((df['marks'].iloc[-1] - df['marks'].iloc[0]) / len(df), 2)
    
    # Prepare insights
    insights = {
        "average_study_hours": round(df['study_hours'].mean(), 2),
        "average_attendance": round(df['attendance'].mean(), 2),
        "average_marks": round(df['marks'].mean(), 2),
        "marks_consistency": marks_consistency,
        "study_hours_consistency": study_hours_consistency,
        "performance_trend": performance_trend,
        "study_efficiency": study_efficiency,
        "attendance_impact": attendance_impact,
        "improvement_rate": improvement_rate,
        "marks_data": {"x": df['test_no'].tolist(), "y": df['marks'].tolist()},
        "study_hours_data": {"x": df['test_no'].tolist(), "y": df['study_hours'].tolist()},
        "attendance_data": {"x": df['test_no'].tolist(), "y": df['attendance'].tolist()}
    }
    
    return jsonify(insights)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
