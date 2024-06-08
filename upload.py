from flask import Flask, request, render_template
from flask_cors import CORS
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String

app = Flask(__name__)
CORS(app)

# Database credentials
db_credentials = {
    'dbname': 'bang_lore',
    'user': 'bang_lore_user',
    'password': 'GB9o29yszCItLrOGGBj5WgauI3E4ckfu',
    'host': 'dpg-cpest0v79t8c73bdet8g-a.singapore-postgres.render.com',
    'port': '5432'
}

def create_or_update_table(table_name, df):
    # Create PostgreSQL database engine
    engine = create_engine(f'postgresql://{db_credentials["user"]}:{db_credentials["password"]}@{db_credentials["host"]}:{db_credentials["port"]}/{db_credentials["dbname"]}', echo=True)
    conn = engine.connect()
    meta = MetaData()

    # Define table schema
    table = Table(
        table_name, meta,
        Column('id', Integer),
        Column('student_id', Integer),
        Column('subject', String(50)),
        Column('marks', Integer),
        Column('test_no', Integer),
        Column('study_hours', Integer),
        Column('Attendance', String(10)),
        
    )

    # Create the table if it does not exist
    meta.create_all(engine)

    # Convert all columns to appropriate types
    df = df.astype({
        'id': int,
        'student_id': int,
        'subject': str,
        'marks': int,
        'test_no': int,
        'study_hours': int,
        'Attendance': str
    })

    # Insert data into the table
    df.to_sql(table_name, con=engine, if_exists='append', index=False)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        table_name = request.form['table_name']
        file = request.files['file']
        if file and table_name:
            # Read CSV file
            df = pd.read_csv(file)
            # Create or update table
            try:
                create_or_update_table(table_name, df)
                return 'File uploaded successfully and data added to table: ' + table_name
            except Exception as e:
                return f'Error uploading data: {e}'
        else:
            return 'Table name and file are required.'
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
