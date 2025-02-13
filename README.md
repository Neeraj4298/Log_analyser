# Log_analyser

This project is a Flask-based web application that processes and stores logs in a MySQL database. It provides a web interface to search logs based on response codes and displays common errors over time.

## Features

- Parses logs from `log.txt` (JSON or Common Log Format)
- Stores logs in MySQL database
- Web interface for searching logs by response code
- Supports Docker deployment

## Prerequisites

Ensure you have the following installed:

- Python 3.x
- Flask
- MySQL Server
- Docker & Docker Compose (if using containers)

## Setup and Installation

### **1. Clone the Repository**

```bash
git clone https://github.com/Neeraj4298/Log_analyser.git
cd Log_analyser
```

### **2. Create and Activate a Virtual Environment**

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### **3. Install Dependencies**

```bash
pip install -r requirements.txt
```

### **4. Configure Environment Variables**

Create a `.env` file with:

```env
MYSQL_HOST=mysql
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_DATABASE=logs_db
```

### **5. Initialize the Database**

Run the following command to create the database and table:

```bash
python app.py
```

### **6. Run the Flask Application**

```bash
python app.py
```

Access it in the browser at `http://localhost:5000`.

## **Running with Docker**

### **1. Build and Start the Containers**

```bash
docker-compose up --build
```

### **2. Access the App**

Visit `http://localhost:5000` in your web browser.

## **API Endpoints**

- `/` - Homepage with response code selection
- `/search` - Search logs by response code

## **Contributing**

Feel free to fork the repository, make enhancements, and submit pull requests!

## **License**

This project is open-source and available under the MIT License.

