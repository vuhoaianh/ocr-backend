from flask import Flask, session, request
from flask_restful import Api, Resource
from flask_session import Session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'

# Initialize Flask-Session
Session(app)

api = Api(app)

# Example resource that retrieves and sets session data
class SessionResource(Resource):
    def get(self):
        # Retrieve user_id from session
        user_id = session['key']
        app.logger.info('GET Request: Session data - %s', session)
        app.logger.info('GET Request: User ID - %s', user_id)
        return {'user_id': user_id}, 200

    def post(self):
        # Set user_id in session
        data = request.get_json()
        user_id = data.get('user_id')
        session['user_id'] = user_id
        app.logger.info('POST Request: Session data - %s', session)
        app.logger.info('POST Request: User ID - %s', user_id)
        return {'message': 'Session updated'}, 200

# Add the resource to the API
api.add_resource(SessionResource, '/session')

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True)
