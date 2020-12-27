from flask import Flask, request, render_template
from reader import Reader

app = Flask(__name__)

@app.route('/')
def my_form():
    return render_template('my-form.html')

@app.route('/', methods=['POST'])
def my_form_post():
    text = request.form['text']
    reader = Reader()
    result = reader.get_result(text)
    result = result.replace('\n\n', '<br><br>')
    return result