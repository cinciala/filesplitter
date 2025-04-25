import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from werkzeug.utils import secure_filename
import tempfile
import uuid
from text_splitter import process_excel_file

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-dev-secret")

# Configure upload settings
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
TEMP_FOLDER = tempfile.gettempdir()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if a file was uploaded
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    
    file = request.files['file']
    
    # Check if the file was selected
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # Secure the filename and create a unique name
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        input_path = os.path.join(TEMP_FOLDER, f"input_{unique_id}_{filename}")
        output_path = os.path.join(TEMP_FOLDER, f"output_{unique_id}_{filename}")
        
        # Save the uploaded file
        file.save(input_path)
        logging.debug(f"File saved at: {input_path}")
        
        # Get column names if provided
        source_col = request.form.get('source_column', 'en-US')
        target_col = request.form.get('target_column', 'cs-CZ')
        check_alignment = 'check_alignment' in request.form
        
        logging.debug(f"Alignment check enabled: {check_alignment}")
        
        # Process the file
        try:
            result = process_excel_file(
                input_path, 
                output_path, 
                source_column=source_col, 
                target_column=target_col,
                check_alignment=check_alignment
            )
            
            # Store the result paths in session
            session['output_path'] = output_path
            session['filename'] = filename
            session['stats'] = result
            
            return redirect(url_for('results'))
            
        except Exception as e:
            flash(f"Error processing file: {str(e)}", 'danger')
            logging.error(f"Error processing file: {str(e)}")
            return redirect(url_for('index'))
    else:
        flash('File type not allowed. Please upload an Excel file (.xlsx, .xls)', 'danger')
        return redirect(url_for('index'))

@app.route('/results')
def results():
    if 'output_path' not in session or 'stats' not in session:
        flash('No processed file available', 'warning')
        return redirect(url_for('index'))
    
    return render_template('results.html', stats=session['stats'])

@app.route('/download')
def download():
    if 'output_path' not in session or 'filename' not in session:
        flash('No processed file available', 'warning')
        return redirect(url_for('index'))
    
    output_path = session['output_path']
    original_filename = session['filename']
    download_name = f"split_sentences_{original_filename}"
    
    return send_file(
        output_path,
        as_attachment=True,
        download_name=download_name,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.route('/new')
def new_process():
    # Clear session data
    if 'output_path' in session:
        try:
            os.remove(session['output_path'])
        except:
            pass
    session.pop('output_path', None)
    session.pop('filename', None)
    session.pop('stats', None)
    return redirect(url_for('index'))

# We'll handle cleanup through the new_process route instead of using teardown handlers
# which can cause session context issues with Gunicorn
