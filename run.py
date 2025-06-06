
from flask_food import create_app,db
from flask_food.models import User, Post

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
