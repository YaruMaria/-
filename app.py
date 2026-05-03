from flask import Flask, render_template
import random

app = Flask(__name__)

# Справочник длительностей
DURATIONS = [
    {'id': 'whole', 'name': 'Целая', 'val': 1.0},
    {'id': 'half', 'name': 'Половинная', 'val': 0.5},
    {'id': 'quarter', 'name': 'Четвертная', 'val': 0.25},
    {'id': 'eighth', 'name': 'Восьмая', 'val': 0.125}
]

@app.route('/')
def index():
    return render_template('index.html', durations=DURATIONS)

if __name__ == '__main__':
    app.run(debug=True)
