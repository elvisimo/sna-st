from flask import Flask, request, render_template, session, redirect, abort, flash, jsonify
from flask import render_template
from instagram.client import InstagramAPI
import os
import json
import time

app = Flask(__name__)
app.secret_key = 'Orion123'


# configure Instagram API
instaConfig = {
	'client_id': 'b168bdd5f96a4dc79f57414acba2afc6',#os.environ.get('CLIENT_ID'),
	'client_secret': 'b3d700d43d2a4461a3bc7d5a97f312a0', #os.environ.get('CLIENT_SECRET'),
	'redirect_uri' : 'http://185.99.8.195:5000/instagram_callback'#os.environ.get('REDIRECT_URI')
}
api = InstagramAPI(**instaConfig)


@app.route('/')

def user_self():
	if 'instagram_access_token' in session and 'instagram_user' in session:
		userAPI = InstagramAPI(access_token=session['instagram_access_token'])
		userSelf = userAPI.user(user_id=session['instagram_user'].get('id'))
		return '''Welcome ''' + userSelf.full_name
        else:

                return redirect('/connect')


# Redirect users to Instagram for login
@app.route('/connect')
def main():

	url = api.get_authorize_url(scope=["likes","comments"])
	return redirect(url)

# Instagram will redirect users back to this route after successfully logging in
@app.route('/instagram_callback')
def instagram_callback():

	code = request.args.get('code')

	if code:

		access_token, user = api.exchange_code_for_access_token(code)
		if not access_token:
			return 'Could not get access token'

		app.logger.debug('got an access token')
		app.logger.debug(access_token)

		# Sessions are used to keep this data 
		session['instagram_access_token'] = access_token
		session['instagram_user'] = user

		return redirect('/') # redirect back to main page
		
	else:
		return "Uhoh no code provided"


	
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


# This is a jinja custom filter
@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    pyDate = time.strptime(date,'%a %b %d %H:%M:%S +0000 %Y') # convert instagram date string into python date/time
    return time.strftime('%Y-%m-%d %h:%M:%S', pyDate) # return the formatted date.
    

if __name__ == "__main__":
	app.debug = True
	app.run(host='10.0.0.28', port=5000)
