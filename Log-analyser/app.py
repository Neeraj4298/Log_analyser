# app.py
from flask import Flask, render_template, request
import mysql.connector
import json
from datetime import datetime
import os
import time
import sys



app = Flask(__name__)

app.config['TEMPLATES_AUTO_RELOAD'] = True

def wait_for_db(max_retries=30, delay=2):
    """Wait for database to be ready"""
    print("Waiting for database to be ready...")
    for attempt in range(max_retries):
        try:
            conn = mysql.connector.connect(
                host=os.getenv('MYSQL_HOST', 'mysql'),
                user=os.getenv('MYSQL_USER', 'root'),
                password=os.getenv('MYSQL_PASSWORD', 'password')
            )
            conn.close()
            print("Database is ready!")
            return True
        except mysql.connector.Error as err:
            print(f"Attempt {attempt + 1}/{max_retries}: Database not ready yet... ({err})")
            time.sleep(delay)
    return False

def get_db_connection():
    """Get database connection"""
    try:
        return mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'mysql'),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', 'password'),
            database=os.getenv('MYSQL_DATABASE', 'logs_db')
        )
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        raise

def init_db():
    """Initialize database"""
    if not wait_for_db():
        print("Could not connect to database after maximum retries")
        sys.exit(1)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create database if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME,
                remote_ip VARCHAR(50),
                remote_user VARCHAR(50),
                request TEXT,
                response INT,
                bytes INT,
                referrer TEXT,
                agent TEXT
            )
        """)
        conn.commit()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def load_logs():
    """Load logs into database with improved error handling and format detection"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if logs are already loaded
        cursor.execute("SELECT COUNT(*) FROM logs")
        if cursor.fetchone()[0] > 0:
            print("Logs already loaded, skipping...")
            return

        print("Loading logs from file...")
        with open('log.txt', 'r') as file:
            for line_number, line in enumerate(file, 1):
                try:
                    # Skip empty lines
                    if not line.strip():
                        continue
                    
                    # Try parsing as JSON
                    try:
                        log = json.loads(line.strip())
                    except json.JSONDecodeError:
                        # If JSON parsing fails, try parsing as Common Log Format
                        # Example: 127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326
                        import re
                        pattern = r'([^ ]*) ([^ ]*) ([^ ]*) \[(.*?)\] "(.*?)" ([^ ]*) ([^ ]*)'
                        match = re.match(pattern, line.strip())
                        
                        if match:
                            remote_ip, _, remote_user, time_str, request, response, bytes_sent = match.groups()
                            try:
                                timestamp = datetime.strptime(time_str, '%d/%b/%Y:%H:%M:%S %z')
                            except ValueError:
                                timestamp = datetime.now()  # Fallback if date parsing fails
                            
                            log = {
                                'remote_ip': remote_ip,
                                'remote_user': remote_user,
                                'time': timestamp.strftime('%d/%b/%Y:%H:%M:%S %z'),
                                'request': request,
                                'response': int(response) if response.isdigit() else 0,
                                'bytes': int(bytes_sent) if bytes_sent.isdigit() else 0,
                                'referrer': '-',
                                'agent': '-'
                            }
                        else:
                            print(f"Warning: Skipping malformed line {line_number}: {line.strip()}")
                            continue

                    # Extract timestamp
                    if isinstance(log.get('time'), str):
                        try:
                            timestamp = datetime.strptime(log['time'], '%d/%b/%Y:%H:%M:%S %z')
                        except ValueError:
                            timestamp = datetime.now()
                    else:
                        timestamp = datetime.now()

                    # Insert into database with proper error handling
                    cursor.execute("""
                        INSERT INTO logs (timestamp, remote_ip, remote_user, request, 
                                        response, bytes, referrer, agent)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        timestamp,
                        log.get('remote_ip', '-'),
                        log.get('remote_user', '-'),
                        log.get('request', '-'),
                        int(log.get('response', 0)),
                        int(log.get('bytes', 0)),
                        log.get('referrer', '-'),
                        log.get('agent', '-')
                    ))

                    # Commit every 1000 records to avoid memory issues
                    if line_number % 1000 == 0:
                        conn.commit()
                        print(f"Processed {line_number} lines...")

                except Exception as e:
                    print(f"Warning: Error processing line {line_number}: {str(e)}")
                    continue

        conn.commit()
        print("Logs loaded successfully!")
    except Exception as e:
        print(f"Error loading logs: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

@app.route('/')
def index():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT response FROM logs")
        response_codes = [row[0] for row in cursor.fetchall()]

        return render_template('index.html', response_codes=response_codes)
    except Exception as e:
        print(f"Error fetching response codes: {e}")
        return f"An error occurred: {str(e)}", 500
    finally:
        cursor.close()
        conn.close()


@app.route('/search', methods=['POST'])
def search():
    try:
        response_code = request.form.get('response_code')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM logs 
            WHERE response = %s
        """, (response_code,))
        count = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT * 
            FROM logs 
            WHERE response = %s
        """, (response_code,))
        logs = cursor.fetchall()
        
        return render_template('results.html', 
                             response_code=response_code,
                             count=count,
                             logs=logs)
    except Exception as e:
        print(f"Error in search: {e}")
        return f"An error occurred: {str(e)}", 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    print("Starting application...")
    init_db()
    load_logs()
    print("Application ready!")
    app.run(host='0.0.0.0', port=5000, debug=True)